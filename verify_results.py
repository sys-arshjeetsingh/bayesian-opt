"""Audit real pgbench JSON logs. Never creates or invents benchmark results."""
import json, math, sys
from pathlib import Path
from statistics import mean, stdev

EXPECTED = {'baseline':(5,{'baseline'}),'grid':(9,{'grid'}),'bo':(25,{'bo'}),'validation':(10,{'validation_default','validation_bo'}),'supp':(15,{'supp_default','supp_bad','supp_sync_off'})}
root=Path('results'); errors=[]; records={}
for name,(count,labels) in EXPECTED.items():
    path=root/f'{name}.json'
    if not path.exists():
        errors.append(f'MISSING: {path}');continue
    try: rows=json.loads(path.read_text(encoding='utf-8'))
    except Exception as e: errors.append(f'INVALID JSON {path}: {e}');continue
    if not isinstance(rows,list):errors.append(f'{path}: expected JSON list');continue
    records[name]=rows
    if len(rows)!=count:errors.append(f'{path}: expected {count} records, found {len(rows)}')
    actual={r.get('label') for r in rows if isinstance(r,dict)}
    if actual!=labels:errors.append(f'{path}: labels {actual}, expected {labels}')
    for i,r in enumerate(rows):
        if not isinstance(r,dict):errors.append(f'{path} row {i}: not object');continue
        t=r.get('tps')
        if not isinstance(t,(int,float)) or not math.isfinite(t) or t<=0:errors.append(f'{path} row {i}: invalid TPS {t!r}')
        if 'pgbench_output' not in r:errors.append(f'{path} row {i}: missing raw pgbench output')
        if 'requested' not in r:errors.append(f'{path} row {i}: missing knob configuration')
    print(f'{name}: {len(rows)}/{count} runs; labels={sorted(actual)}')
if 'validation' in records:
    groups={k:[r['tps'] for r in records['validation'] if r.get('label')==k and isinstance(r.get('tps'),(int,float))] for k in ('validation_default','validation_bo')}
    if any(len(v)!=5 for v in groups.values()):errors.append('validation: require exactly 5 default and 5 BO runs')
    if all(len(v)>1 for v in groups.values()):
        d,b=groups.values();print(f'VALIDATION default: {mean(d):.2f} ± {stdev(d):.2f} TPS');print(f'VALIDATION BO: {mean(b):.2f} ± {stdev(b):.2f} TPS');print(f'VALIDATION gain: {(mean(b)/mean(d)-1)*100:+.2f}%')
if 'bo' in records and len(records['bo'])>0:
    winner=max(records['bo'],key=lambda r:r.get('tps',float('-inf')))
    print('BO best observed trial:',winner.get('trial'),'TPS:',winner.get('tps'),'knobs:',winner.get('requested'))
for name in ('grid','bo','validation','supp'):
    for ext in ('png','pdf'):
        if not (Path('figures')/f'{name}.{ext}').exists():errors.append(f'MISSING figure: figures/{name}.{ext} (run python analyze.py)')
for path in (root/'summary.json',root/'tables.txt'):
    if not path.exists():errors.append(f'MISSING analysis: {path} (run python analyze.py)')
print('\n'+'\n'.join(errors) if errors else '\nPASS: logs have expected counts, labels, TPS, raw outputs and figures.')
sys.exit(1 if errors else 0)
