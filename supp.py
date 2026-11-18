"""Supplementary experiments; synchronous_commit=off weakens durability. Disposable local database ONLY.
Fix: set_config() now does ALTER SYSTEM RESET ALL first, so synchronous_commit=off can no longer leak into later 'default'/'bad' runs."""
import argparse, json
from pathlib import Path
from tune import DEFAULTS, set_config, benchmark

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--dsn',required=True); p.add_argument('--pgbench',required=True); p.add_argument('--restart-cmd',required=True)
    p.add_argument('--repeats',type=int,default=5); p.add_argument('--duration',type=int,default=20); p.add_argument('--warmup',type=int,default=5)
    p.add_argument('--output',default='results/supp.json')
    a=p.parse_args()
    configs={'supp_default':DEFAULTS,
             'supp_bad':dict(DEFAULTS,shared_buffers='16MB',max_wal_size='64MB',wal_buffers='64kB',checkpoint_completion_target='0.1'),
             'supp_sync_off':dict(DEFAULTS,synchronous_commit='off')}
    rows=[]
    try:
        for i in range(a.repeats):
            for label,cfg in configs.items():
                settings=set_config(a.dsn,cfg,a.restart_cmd)
                tps,raw=benchmark(a.pgbench,a.duration,a.warmup,8,1)
                rows.append({'label':label,'trial':i,'tps':tps,'requested':cfg,'actual_settings':settings,'pgbench_output':raw})
                Path(a.output).parent.mkdir(parents=True,exist_ok=True)
                Path(a.output).write_text(json.dumps(rows,indent=2))
                print(label,i,tps,flush=True)
    finally:
        try: set_config(a.dsn,DEFAULTS,a.restart_cmd)
        except Exception as e: print('RESTORE SETTINGS MANUALLY:',e)
if __name__=='__main__':main()
