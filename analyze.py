"""Generate ALL numbers, figures and tables for the paper ONLY from the measured JSON logs.
Outputs: results/summary.json, results/tables.txt, figures/{grid,bo,validation,supp}.{png,pdf}"""
import argparse, json, re
from pathlib import Path
import numpy as np
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy import stats

def read(p):
    p = Path(p); return json.loads(p.read_text()) if p.exists() else []
def tps(rows, label): return np.array([r['tps'] for r in rows if r['label'] == label])
def num(s): return float(re.sub(r'[A-Za-z]+', '', str(s)))
def save(fig, name):
    fig.tight_layout(); fig.savefig(f'figures/{name}.png', dpi=200); fig.savefig(f'figures/{name}.pdf'); plt.close(fig)

def main():
    ap = argparse.ArgumentParser()
    for k in ('baseline', 'grid', 'bo', 'validation', 'supp'): ap.add_argument(f'--{k}', default=f'results/{k}.json')
    a = ap.parse_args(); Path('figures').mkdir(exist_ok=True)
    base, grid, bo, val, supp = (read(getattr(a, k)) for k in ('baseline', 'grid', 'bo', 'validation', 'supp'))
    plt.rcParams.update({'font.family': 'serif', 'font.size': 8})
    S, T = {}, []
    if base:
        d = tps(base, 'baseline'); S.update(default_mean=d.mean(), default_sd=d.std(ddof=1), default_cv_pct=100*d.std(ddof=1)/d.mean(), default_n=len(d))
        print(f'Baseline: {d.mean():.1f} +- {d.std(ddof=1):.1f} TPS (n={len(d)}, CV {S["default_cv_pct"]:.1f}%)')
    if grid:
        sb, wm = [128, 256, 512], [4, 16, 64]; M = np.full((3, 3), np.nan)
        for r in grid:
            i, j = map(int, str(r['trial']).split('-')); M[sb.index(i), wm.index(j)] = r['tps']
        fig, ax = plt.subplots(figsize=(3.2, 2.1)); im = ax.imshow(M, cmap='Blues')
        ax.set_xticks(range(3), [f'{x} MB' for x in wm]); ax.set_yticks(range(3), [f'{x} MB' for x in sb])
        ax.set_xlabel('work_mem'); ax.set_ylabel('shared_buffers'); fig.colorbar(im, ax=ax, label='TPS')
        for i in range(3):
            for j in range(3):
                if np.isfinite(M[i, j]): ax.text(j, i, f'{M[i,j]:.0f}', ha='center', va='center', fontsize=7)
        save(fig, 'grid'); S.update(grid_best=float(np.nanmax(M)), grid_worst=float(np.nanmin(M)), grid_range_pct=float(100*(np.nanmax(M)/np.nanmin(M)-1)))
        if base: S['grid_best_vs_default_pct'] = float(100*(np.nanmax(M)/S['default_mean']-1))
    if bo:
        y = np.array([r['tps'] for r in bo]); best = np.maximum.accumulate(y); nr = 6
        fig, ax = plt.subplots(figsize=(3.4, 2.3)); x = range(1, len(y)+1)
        ax.plot(x, y, 'o', ms=3, label='BO trial'); ax.plot(x, best, '-', label='Best so far')
        if base: ax.axhline(S['default_mean'], ls='--', c='gray', label='Default (mean)')
        ax.axvline(nr+0.5, ls=':', c='k', lw=.6); ax.set_xlabel('Trial'); ax.set_ylabel('Throughput (TPS)'); ax.legend(fontsize=6, loc='lower right')
        save(fig, 'bo')
        S.update(bo_best=float(y.max()), bo_min=float(y.min()), bo_median=float(np.median(y)), bo_sd=float(y.std(ddof=1)), bo_trials=len(y),
                 bo_random_mean=float(y[:nr].mean()), bo_ei_mean=float(y[nr:].mean()) if len(y) > nr else None)
        if base: S['bo_best_vs_default_pct'] = float(100*(y.max()/S['default_mean']-1))
        rho = []
        for k in ('shared_buffers', 'work_mem', 'max_wal_size', 'wal_buffers', 'checkpoint_completion_target'):
            v = np.array([num(r['requested'][k]) for r in bo]); rr, p = stats.spearmanr(v, y); rho.append((k, rr, p))
        T.append('Spearman correlation (knob vs TPS):\n' + '\n'.join(f'  {k:32s} rho={r:+.2f}  p={p:.3f}' for k, r, p in rho))
        order = np.argsort(-y); rows = lambda idx: '\n'.join(
            f'  trial {i:2d} | sb {num(bo[i]["requested"]["shared_buffers"]):5.0f} | wm {num(bo[i]["requested"]["work_mem"]):3.0f} | wal {num(bo[i]["requested"]["max_wal_size"]):5.0f} | wbuf {num(bo[i]["requested"]["wal_buffers"]):3.0f} | ckpt {num(bo[i]["requested"]["checkpoint_completion_target"]):.2f} | {y[i]:.0f}' for i in idx)
        T.append('Best 4 BO trials:\n' + rows(order[:4]) + '\nWorst 4 BO trials:\n' + rows(order[-4:]))
        S['bo_winner_config'] = bo[int(np.argmax(y))]['requested']
    if val:
        d, b = tps(val, 'validation_default'), tps(val, 'validation_bo')
        if len(d) > 1 and len(b) > 1:
            t, p = stats.ttest_ind(b, d, equal_var=False)
            S.update(val_default_mean=d.mean(), val_default_sd=d.std(ddof=1), val_bo_mean=b.mean(), val_bo_sd=b.std(ddof=1),
                     val_gain_pct=100*(b.mean()/d.mean()-1), val_welch_t=t, val_welch_p=p)
            print(f'Validation: default {d.mean():.1f}+-{d.std(ddof=1):.1f} | BO {b.mean():.1f}+-{b.std(ddof=1):.1f} | gain {S["val_gain_pct"]:+.2f}% | Welch p={p:.4g}')
            fig, ax = plt.subplots(figsize=(3.2, 2.1)); lab = ['Default', 'BO best']; m = [d.mean(), b.mean()]
            ax.bar(lab, m, yerr=[d.std(ddof=1), b.std(ddof=1)], capsize=3, color=['#999', '#2a5599'])
            for i, v in enumerate(m): ax.text(i, v*1.02, f'{v:.0f}', ha='center', fontsize=7)
            ax.set_ylabel('Throughput (TPS)'); ax.set_ylim(0, max(m)*1.2); save(fig, 'validation')
    if supp:
        g = {k: tps(supp, k) for k in ('supp_default', 'supp_bad', 'supp_sync_off')}
        if all(len(v) > 1 for v in g.values()):
            for k, v in g.items(): S[k+'_mean'] = v.mean(); S[k+'_sd'] = v.std(ddof=1)
            for k in ('supp_bad', 'supp_sync_off'):
                t, p = stats.ttest_ind(g[k], g['supp_default'], equal_var=False)
                S[k+'_vs_default_pct'] = 100*(g[k].mean()/g['supp_default'].mean()-1); S[k+'_p'] = p
                print(f'{k}: {g[k].mean():.1f} vs default {g["supp_default"].mean():.1f} -> {S[k+"_vs_default_pct"]:+.1f}% (p={p:.3g})')
            fig, ax = plt.subplots(figsize=(3.2, 2.1)); names = ['Default', 'Misconfigured', 'sync_commit\n=off']
            ax.bar(names, [v.mean() for v in g.values()], yerr=[v.std(ddof=1) for v in g.values()], capsize=3, color=['#999', '#cc6666', '#339966'])
            for i, v in enumerate(g.values()): ax.plot([i]*len(v), v, 'k.', ms=3)
            ax.set_ylabel('Throughput (TPS)'); save(fig, 'supp')
    Path('results').mkdir(exist_ok=True)
    Path('results/summary.json').write_text(json.dumps(S, indent=1, default=float)); Path('results/tables.txt').write_text('\n\n'.join(T))
    print('\n'.join(T)); print('Wrote results/summary.json, results/tables.txt, figures/')
if __name__ == '__main__': main()
