"""G4: PostgreSQL knob tuning experiment. LOCAL, DISPOSABLE PostgreSQL ONLY.
Requires PostgreSQL/pgbench installed and a role permitted to ALTER SYSTEM.
Every record comes from real pgbench output; nothing is invented.

Fixes vs the first version:
  * pgbench options are now placed BEFORE the database name (required on Windows).
  * set_config() first runs ALTER SYSTEM RESET ALL, so no setting (e.g. synchronous_commit) leaks between trials.
  * pgbench is run WITHOUT -n so tables are vacuumed before every run (avoids bloat drift over 60+ trials).
  * All four memory knobs are log-scaled (as the paper states); EI uses no exploration offset (as the paper's formula).
  * After a restart the script waits until the server accepts connections.
"""
import argparse, json, os, re, shlex, subprocess, time
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
import psycopg
from psycopg import sql
from scipy.stats import norm
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import ConstantKernel, Matern, WhiteKernel

KNOBS = {   # name: (low, high, unit, log-scale)
    'shared_buffers': (64, 1024, 'MB', True),
    'work_mem': (1, 64, 'MB', True),
    'max_wal_size': (256, 4096, 'MB', True),
    'wal_buffers': (1, 64, 'MB', True),
    'checkpoint_completion_target': (0.5, 0.95, '', False),
}
DEFAULTS = {'shared_buffers':'128MB','work_mem':'4MB','max_wal_size':'1GB',
            'wal_buffers':'4MB','checkpoint_completion_target':'0.9'}
ALLOWED = set(KNOBS) | {'synchronous_commit'}

def sh(command, timeout=300):
    p = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=timeout)
    if p.returncode: raise RuntimeError(f'Command failed: {command}\n{p.stderr}\n{p.stdout}')
    return p.stdout

def connect(dsn):
    return psycopg.connect(dsn, autocommit=True)

def wait_ready(dsn, tries=120):
    last = None
    for _ in range(tries):
        try:
            with connect(dsn) as con: con.execute('SELECT 1'); return
        except Exception as e:
            last = e; time.sleep(0.5)
    raise RuntimeError(f'Server did not accept connections after restart: {last}')

def current_settings(dsn):
    with connect(dsn) as con, con.cursor() as cur:
        out = {}
        for k in list(KNOBS) + ['synchronous_commit']:
            out[k] = list(cur.execute('SELECT setting, unit, pending_restart FROM pg_settings WHERE name=%s', (k,)).fetchone())
        return out

def set_config(dsn, config, restart_cmd):
    with connect(dsn) as con, con.cursor() as cur:
        cur.execute('ALTER SYSTEM RESET ALL')          # clear anything left from earlier trials
        for key, val in config.items():
            if key not in ALLOWED: raise ValueError(key)
            cur.execute(sql.SQL('ALTER SYSTEM SET {} = {}').format(sql.Identifier(key), sql.Literal(str(val))))
        cur.execute('SELECT pg_reload_conf()')
    sh(restart_cmd)
    time.sleep(2)
    wait_ready(dsn)
    settings = current_settings(dsn)
    for key in config:
        if settings[key][2]:
            raise RuntimeError(f'{key} still has pending_restart=True; check --restart-cmd')
    return settings

def benchmark(pgbench_cmd, seconds, warmup, clients, jobs):
    """pgbench_cmd = 'pgbench -h localhost -U postgres testdb' (database LAST). Options are inserted before the database."""
    tokens = shlex.split(pgbench_cmd, posix=(os.name != 'nt'))
    base, db = tokens[:-1], tokens[-1]
    def run(t):
        cmd = base + ['-c', str(clients), '-j', str(jobs), '-T', str(t), db]
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=t + 600)
        if p.returncode: raise RuntimeError(f'pgbench failed: {cmd}\n{p.stderr}\n{p.stdout}')
        return p.stdout
    if warmup: run(warmup)
    output = run(seconds)
    m = re.search(r'tps\s*=\s*([\d.]+)', output, re.I)
    if not m: raise RuntimeError(f'Could not parse pgbench TPS:\n{output}')
    return float(m.group(1)), output

def decode(x):
    result = {}
    for (key, (lo, hi, unit, logscale)), z in zip(KNOBS.items(), x):
        v = np.exp(np.log(lo)+z*(np.log(hi)-np.log(lo))) if logscale else lo+z*(hi-lo)
        result[key] = f'{v:.4f}' if key == 'checkpoint_completion_target' else f'{max(1,round(v))}{unit}'
    return result

def evaluate(label, config, args, records, trial=None):
    settings = set_config(args.dsn, config, args.restart_cmd)
    tps, raw = benchmark(args.pgbench, args.duration, args.warmup, args.clients, args.jobs)
    record = {'timestamp_utc': datetime.now(timezone.utc).isoformat(), 'label':label, 'trial':trial,
              'requested':config, 'actual_settings':settings, 'tps':tps, 'pgbench_output':raw,
              'duration_s':args.duration, 'warmup_s':args.warmup, 'clients':args.clients, 'jobs':args.jobs}
    records.append(record)
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(json.dumps(records, indent=2))
    print(f'{label} {trial if trial is not None else ""}: {tps:.2f} TPS', flush=True)
    return tps

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--dsn',default=os.getenv('PG_DSN','dbname=testdb user=postgres host=localhost'))
    ap.add_argument('--pgbench',default='pgbench -h localhost -U postgres testdb',help='pgbench command INCLUDING database name as the LAST word')
    ap.add_argument('--restart-cmd',required=True,help='Restart ONLY your disposable PostgreSQL instance')
    ap.add_argument('--duration',type=int,default=20)
    ap.add_argument('--warmup',type=int,default=5)
    ap.add_argument('--clients',type=int,default=8)
    ap.add_argument('--jobs',type=int,default=1)
    ap.add_argument('--seed',type=int,default=42)
    ap.add_argument('--trials',type=int,default=25)
    ap.add_argument('--n-random',type=int,default=6)
    ap.add_argument('--output',default='results/main.json')
    ap.add_argument('--mode',choices=['baseline','grid','bo','validate'],required=True)
    ap.add_argument('--repeats',type=int,default=5)
    ap.add_argument('--winner-file',default='results/bo.json')
    args=ap.parse_args()
    records=[]
    try:
        if args.mode=='baseline':
            for i in range(args.repeats): evaluate('baseline',DEFAULTS,args,records,i)
        elif args.mode=='grid':
            for a in (128,256,512):
                for b in (4,16,64):
                    evaluate('grid',dict(DEFAULTS,shared_buffers=f'{a}MB',work_mem=f'{b}MB'),args,records,f'{a}-{b}')
        elif args.mode=='bo':
            rng=np.random.default_rng(args.seed); X=[]; Y=[]
            for i in range(args.trials):
                if i<args.n_random:
                    x=rng.random(5)
                else:
                    kernel=ConstantKernel(1.0,(1e-3,1e3))*Matern(length_scale=np.ones(5),nu=2.5)+WhiteKernel(noise_level=0.01)
                    gp=GaussianProcessRegressor(kernel=kernel,normalize_y=True,n_restarts_optimizer=2,random_state=args.seed+i)
                    gp.fit(np.asarray(X),np.asarray(Y))
                    cand=rng.random((4000,5)); mu,sd=gp.predict(cand,return_std=True)
                    improvement=mu-max(Y)
                    z=np.divide(improvement,sd,out=np.zeros_like(sd),where=sd>0)
                    ei=improvement*norm.cdf(z)+sd*norm.pdf(z)
                    x=cand[np.argmax(ei)]
                y=evaluate('bo',decode(x),args,records,i)
                records[-1]['x_normalized']=x.tolist()
                Path(args.output).write_text(json.dumps(records,indent=2))
                X.append(x); Y.append(y)
        else:
            source=json.loads(Path(args.winner_file).read_text())
            bo=[r for r in source if r['label']=='bo']
            if not bo: raise RuntimeError('No BO trials in winner-file')
            winner=max(bo,key=lambda r:r['tps'])['requested']
            print('Validating BO winner:',winner)
            for i in range(args.repeats):
                evaluate('validation_default',DEFAULTS,args,records,i)
                evaluate('validation_bo',winner,args,records,i)
    finally:
        try:
            set_config(args.dsn,DEFAULTS,args.restart_cmd)
            print('Restored the paper baseline configuration (NOT necessarily your original server settings).')
        except Exception as e: print('WARNING: RESTORE MANUALLY:',e)

if __name__=='__main__': main()
