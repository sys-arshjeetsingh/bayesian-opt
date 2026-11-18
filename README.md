# G4: Bayesian optimisation of PostgreSQL configuration (corrected scripts)

Run ONLY on a disposable local PostgreSQL. Scripts call `ALTER SYSTEM RESET ALL` (this wipes ALL your custom
postgresql.auto.conf settings), restart the service, and the supplementary test temporarily sets `synchronous_commit=off`.
Back up `C:\Program Files\PostgreSQL\18\data\postgresql.auto.conf` first.

## What was fixed in your uploaded version
1. pgbench options were placed after the database name (fails on Windows) -> options now come first.
2. `synchronous_commit=off` leaked into later "default"/"bad" runs of supp.py -> `ALTER SYSTEM RESET ALL` before every trial.
3. pgbench `-n` (no vacuum) removed -> tables are vacuumed each run, avoiding bloat drift across ~60 trials.
4. work_mem and max_wal_size are now log-scaled (the paper says memory knobs are log-scaled); EI has no extra offset (matches the paper's formula).
5. After restart the script waits until the server accepts connections; `--restart-cmd` is mandatory.
6. analyze.py now creates every number/table the paper needs: results/summary.json, results/tables.txt, figures/*.pdf.

## Steps (Windows, ~1-1.5 hours total)
Open **PowerShell as Administrator** (right-click -> Run as administrator), then:
```powershell
cd "C:\Users\Arshjeet singh\Documents\DBMS\Project\bayesian_opt"
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:PGPASSWORD = "YOUR_POSTGRES_PASSWORD"
$D = "dbname=testdb user=postgres host=localhost"
$P = "pgbench -h localhost -U postgres testdb"
$R = "net stop postgresql-x64-18 && net start postgresql-x64-18"

# 0. warm the cache once (result is thrown away); close other programs, plug in the laptop, disable sleep
pgbench -h localhost -U postgres -c 8 -j 1 -T 30 testdb

# 1. SMOKE TEST (2 min) - confirm restart + pgbench work before the long run
python tune.py --dsn $D --pgbench $P --restart-cmd $R --duration 3 --warmup 1 --repeats 1 --mode baseline --output results/smoke.json

# 2. REAL RUN (do not touch the laptop while it runs)
python tune.py --dsn $D --pgbench $P --restart-cmd $R --mode baseline --output results/baseline.json
python tune.py --dsn $D --pgbench $P --restart-cmd $R --mode grid     --output results/grid.json
python tune.py --dsn $D --pgbench $P --restart-cmd $R --mode bo       --output results/bo.json
python tune.py --dsn $D --pgbench $P --restart-cmd $R --mode validate --winner-file results/bo.json --output results/validation.json
python supp.py --dsn $D --pgbench $P --restart-cmd $R

# 3. Analysis
python analyze.py
```
Delete `results/smoke.json` before step 2 is analysed. Do not mix smoke-test data with real data.

## Collect hardware details for the paper (PowerShell)
```powershell
Get-CimInstance Win32_Processor | Select Name,NumberOfCores,NumberOfLogicalProcessors,MaxClockSpeed
Get-CimInstance Win32_ComputerSystem | Select @{n="RAM_GB";e={[math]::Round($_.TotalPhysicalMemory/1GB,1)}}
Get-PhysicalDisk | Select FriendlyName,MediaType,Size
(Get-CimInstance Win32_OperatingSystem).Caption
psql -h localhost -U postgres -c "select version()"
```
