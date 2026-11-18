# Bayesian Optimisation of PostgreSQL Configuration

### An Empirical Study of Database Knob Tuning Using Gaussian Processes and pgbench

This repository contains the implementation, experimental results, and analysis for a DBMS research project investigating whether Bayesian Optimisation (BO) can identify PostgreSQL configurations that outperform a specified baseline.

The study compares three approaches:

1. A fixed PostgreSQL baseline configuration.
2. Grid search over selected memory parameters.
3. Gaussian Process-based Bayesian Optimisation using Expected Improvement.

Experiments were conducted using PostgreSQL 18.7 and the built-in `pgbench` benchmark on Windows 11.

## 1. Research Objective

**Research question:** Can Bayesian Optimisation discover PostgreSQL configurations that deliver higher transaction throughput than a fixed baseline and conventional grid search?

The study evaluates:

- Transaction throughput (TPS).
- Average transaction latency.
- Performance improvements relative to the baseline.
- Bayesian Optimisation convergence.
- Variability and stability of benchmark measurements.

The objective is to investigate the effectiveness of automated database configuration tuning while documenting experimental limitations.

## 2. Experimental Environment

| Component | Specification |
|---|---|
| Operating system | Windows 11 |
| Database | PostgreSQL 18.7 |
| Benchmark | pgbench 18.7 |
| Programming language | Python |
| Optimisation model | Gaussian Process |
| Acquisition function | Expected Improvement |
| Machine | Lenovo LOQ |
| Processor | Intel Core i5-13450HX |
| RAM | 24 GB |
| Storage | SSD |
| Benchmark scale | 30 |
| Clients | 8 |
| Threads | 1 |
| Measured duration | 20 seconds |
| Warmup duration | 5 seconds |

The benchmark uses pgbench's built-in TPC-B-like transaction workload.

The benchmark database was initialised with approximately 3 million accounts.

## 3. PostgreSQL Configuration Parameters

Five PostgreSQL parameters were included in the Bayesian Optimisation search space:

| Parameter | Description |
|---|---|
| `shared_buffers` | Memory allocated to PostgreSQL's shared buffer cache |
| `work_mem` | Memory available for individual query operations |
| `max_wal_size` | WAL size threshold influencing checkpoint frequency |
| `wal_buffers` | Shared memory used for WAL buffering |
| `checkpoint_completion_target` | Target fraction of the checkpoint interval used to spread checkpoint I/O |

The baseline configuration was:

| Parameter | Baseline value |
|---|---|
| `shared_buffers` | 128 MB |
| `work_mem` | 4 MB |
| `max_wal_size` | 1 GB |
| `wal_buffers` | 4 MB |
| `checkpoint_completion_target` | 0.9 |
| `synchronous_commit` | on |

**Important:** This is the explicitly configured experimental baseline, not necessarily the unmodified default configuration of PostgreSQL 18.7.

## 4. Methodology

### 4.1 Baseline Evaluation

The baseline configuration was evaluated five times.

Each measurement used:

- 8 clients.
- 1 benchmark thread.
- 5 seconds of warmup.
- 20 seconds of measured execution.

The baseline mean and sample standard deviation were calculated from the five throughput measurements.

### 4.2 Grid Search

Grid search evaluated nine configurations using:

`shared_buffers`:

- 128 MB
- 256 MB
- 512 MB

`work_mem`:

- 4 MB
- 16 MB
- 64 MB

The remaining parameters were held at their baseline values.

Each grid-search configuration was evaluated once.

### 4.3 Bayesian Optimisation

Bayesian Optimisation used a Gaussian Process surrogate model and an Expected Improvement acquisition function.

The optimiser evaluated 25 configurations.

Each candidate was applied to PostgreSQL and evaluated using pgbench.

The highest observed throughput was retained as the best configuration.

The initial search included randomly sampled configurations, followed by model-guided candidate selection.

### 4.4 Experimental Limitations

The original experiments exhibited substantial performance variability.

Later BO trials experienced a pronounced throughput decline, and subsequent baseline checks also produced lower throughput than the original baseline measurements.

Consequently, the highest observed BO throughput cannot be interpreted as a statistically validated improvement.

Independent validation and supplementary experiments were not completed.

## 5. Experimental Results

### 5.1 Baseline Results

| Trial | Throughput (TPS) |
|---|---:|
| 1 | 4151.34 |
| 2 | 4964.64 |
| 3 | 5086.24 |
| 4 | 4858.95 |
| 5 | 4533.72 |

**Baseline mean:** 4718.98 TPS

**Sample standard deviation:** 377.94 TPS

### 5.2 Grid Search Results

| shared_buffers | work_mem = 4 MB | work_mem = 16 MB | work_mem = 64 MB |
|---|---:|---:|---:|
| 128 MB | 4304.84 | 3658.87 | 4640.93 |
| 256 MB | 4828.77 | 4623.13 | **4900.11** |
| 512 MB | 4789.30 | 4878.36 | 4880.82 |

The best grid-search configuration was:

- `shared_buffers = 256MB`
- `work_mem = 64MB`

**Best observed throughput:** 4900.11 TPS.

### 5.3 Bayesian Optimisation Results

The highest observed BO throughput occurred during trial 11.

| Parameter | Value |
|---|---|
| `shared_buffers` | 1009 MB |
| `work_mem` | 7 MB |
| `max_wal_size` | 3143 MB |
| `wal_buffers` | 11 MB |
| `checkpoint_completion_target` | 0.7619 |

**Best observed throughput:** 5246.90 TPS.

### 5.4 Performance Comparison

| Method | Throughput (TPS) | Difference relative to baseline mean |
|---|---:|---:|
| Baseline mean | 4718.98 | — |
| Best grid-search observation | 4900.11 | +3.84% |
| Best BO observation | **5246.90** | **+11.19%** |

The best BO observation was approximately 7.08% higher than the best grid-search observation.

These percentages describe observed differences. They do not establish statistically significant improvements.

## 6. Generated Figures

The repository includes:

**Bayesian Optimisation Convergence**

`figures/bo.pdf`

`figures/bo.png`

This figure displays:

- Individual BO trial throughput.
- Best-observed throughput so far.
- Baseline mean throughput.

**Grid Search Heatmap**

`figures/grid.pdf`

`figures/grid.png`

This figure visualises throughput across the nine grid-search configurations.

## 7. Repository Structure

```text
bayesian_opt/
├── figures/
│   ├── bo.pdf
│   ├── bo.png
│   ├── grid.pdf
│   └── grid.png
│
├── results/
│   ├── baseline.json
│   ├── grid.json
│   ├── bo.json
│   ├── smoke.json
│   ├── summary.json
│   └── tables.txt
│
├── analyze.py
├── db_connection.py
├── tune.py
├── supp.py
├── verify_results.py
├── requirements.txt
├── README.md
├── FINAL_VERIFICATION.md
└── .gitignore
```

The `smoke.json` file contains a preliminary functionality test and must not be included in the formal experimental analysis.

## 8. Installation

### Requirements

- Python
- PostgreSQL 18
- PostgreSQL command-line utilities
- pip
- PowerShell
- Administrator privileges for PostgreSQL service restarts

Clone the repository:

```powershell
git clone <YOUR_REPOSITORY_URL>
cd bayesian_opt
```

Create a virtual environment:

```powershell
python -m venv .venv
```

Activate it:

```powershell
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
pip install -r requirements.txt
```

Ensure the PostgreSQL binaries are available:

```powershell
$env:Path = "C:\Program Files\PostgreSQL\18\bin;$env:Path"
```

## 9. Database Authentication

Do not hardcode database passwords in Python scripts or commit credentials to GitHub.

For local execution:

```powershell
$env:PGPASSWORD = Read-Host "Enter PostgreSQL password"
```

Connection settings can be supplied using a PostgreSQL DSN:

```powershell
$D = "dbname=testdb user=postgres host=localhost port=5432"
```

## 10. Reproducing the Experiments

**WARNING: Use only a dedicated, disposable PostgreSQL instance.**

The tuning scripts execute PostgreSQL configuration commands, including:

```sql
ALTER SYSTEM RESET ALL;
```

This resets settings stored in `postgresql.auto.conf`.

The scripts also restart PostgreSQL and may overwrite custom server configuration.

Back up the PostgreSQL configuration before running any experiment.

Example configuration:

```powershell
$D = "dbname=testdb user=postgres host=localhost port=5432"
$P = "pgbench -h localhost -U postgres testdb"
$R = "net stop postgresql-x64-18 && net start postgresql-x64-18"
```

Run the baseline experiment:

```powershell
python tune.py --dsn "$D" --pgbench "$P" --restart-cmd "$R" --mode baseline --duration 20 --warmup 5 --clients 8 --jobs 1 --repeats 5 --output results/baseline.json
```

Run grid search:

```powershell
python tune.py --dsn "$D" --pgbench "$P" --restart-cmd "$R" --mode grid --duration 20 --warmup 5 --clients 8 --jobs 1 --output results/grid.json
```

Run Bayesian Optimisation:

```powershell
python tune.py --dsn "$D" --pgbench "$P" --restart-cmd "$R" --mode bo --trials 25 --n-random 5 --duration 20 --warmup 5 --clients 8 --jobs 1 --seed 42 --output results/bo.json
```

These commands are provided for reproducibility. Running them again is not necessary to inspect the existing results.

## 11. Generating Results and Figures

To regenerate the analysis from the existing experimental data:

```powershell
python analyze.py --baseline results/baseline.json --grid results/grid.json --bo results/bo.json
```

The analysis script generates summary statistics, tables, and figures.

The main output files are:

```text
results/summary.json
results/tables.txt
figures/bo.pdf
figures/bo.png
figures/grid.pdf
figures/grid.png
```

## 12. Verification

The repository contains:

```text
verify_results.py
```

This script checks the expected experimental evidence and generated outputs.

The original verification workflow expects additional validation and supplementary results.

Because those experiments were not completed, the full verification audit may report missing files.

Do not interpret a missing-file failure as evidence that the completed baseline, grid-search, or BO results are invalid.

## 13. Limitations

The study has several limitations:

1. Experiments were conducted on a single Windows laptop.
2. The benchmark used one workload and one client-concurrency level.
3. Grid-search and BO candidate configurations were evaluated only once.
4. Throughput varied substantially during the experiment.
5. Independent validation was not completed.
6. No statistically supported claim of BO superiority can be made.
7. Results may differ across PostgreSQL versions, workloads, hardware, and operating systems.

## 14. Conclusion

Bayesian Optimisation identified the highest single-trial throughput among the configurations tested.

The best BO observation reached 5246.90 TPS, compared with a baseline mean of 4718.98 TPS and a best grid-search observation of 4900.11 TPS.

However, substantial benchmark variability prevents these results from establishing a reliable performance advantage.

The experiment demonstrates both the potential of automated PostgreSQL configuration tuning and the importance of reproducible benchmarking, repeated validation, and controlling system-level variability.

## 15. Academic Use

This repository accompanies a DBMS research study on PostgreSQL configuration tuning.

Experimental results are provided for academic analysis and reproducibility.

No benchmark values should be interpreted as independently validated performance improvements unless supported by additional controlled experiments.