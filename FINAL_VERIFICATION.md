# Final Research Verification Report

## G4: Bayesian Optimisation of PostgreSQL Configuration

**Verification date:** 19 November 2026

**Project:** Can Bayesian Optimisation Beat PostgreSQL Defaults? An Empirical Study of Knob Tuning on pgbench

**Database:** PostgreSQL 18.7

**Operating system:** Windows 11

**Status:** Exploratory experiments completed; independent validation pending.

---

## 1. Experimental Completion Status

The following experiments were performed on the local PostgreSQL instance.

| Experiment | Planned runs | Completed runs | Status |
|---|---:|---:|---|
| Baseline | 5 | 5 | Completed |
| Grid search | 9 | 9 | Completed |
| Bayesian Optimisation | 25 | 25 | Completed |
| Independent validation | 10 | 0 | Not performed |
| Supplementary experiments | 15 | 0 | Not performed |
| **Total** | **64** | **39** | **Partially completed** |

Additional smoke tests and diagnostic benchmarks were conducted but are not included in the 39 formal measurements.

The experimental data are stored in:

```text
results/baseline.json
results/grid.json
results/bo.json
```

---

## 2. Baseline Verification

The baseline configuration was evaluated five times.

### Configuration

| Parameter | Value |
|---|---|
| shared_buffers | 128 MB |
| work_mem | 4 MB |
| max_wal_size | 1 GB |
| wal_buffers | 4 MB |
| checkpoint_completion_target | 0.9 |
| synchronous_commit | on |

### Measured throughput

| Trial | TPS |
|---|---:|
| 1 | 4151.340896 |
| 2 | 4964.642105 |
| 3 | 5086.236164 |
| 4 | 4858.951917 |
| 5 | 4533.722390 |

**Mean throughput:** 4718.98 TPS

**Sample standard deviation:** 377.94 TPS

**Coefficient of variation:** Approximately 8.01%

All five baseline measurements reported zero failed transactions.

### Verification result

PASS — Five baseline measurements were completed.

CAUTION — The baseline is an explicitly specified configuration and should not automatically be described as PostgreSQL's untouched factory defaults.

---

## 3. Grid Search Verification

Grid search evaluated nine combinations of `shared_buffers` and `work_mem`.

| shared_buffers | 4 MB | 16 MB | 64 MB |
|---|---:|---:|---:|
| 128 MB | 4304.84 | 3658.87 | 4640.93 |
| 256 MB | 4828.77 | 4623.13 | 4900.11 |
| 512 MB | 4789.30 | 4878.36 | 4880.82 |

### Best configuration

```text
shared_buffers = 256MB
work_mem = 64MB
```

**Best observed throughput:** 4900.11 TPS.

**Observed difference from baseline mean:** +3.84%.

### Verification result

PASS — Nine grid-search measurements were completed.

CAUTION — Each grid-search configuration was evaluated once. The best result has not been independently validated.

---

## 4. Bayesian Optimisation Verification

Bayesian Optimisation evaluated 25 PostgreSQL configurations.

The optimisation procedure used:

- Gaussian Process regression.
- Expected Improvement acquisition.
- Configuration search over five PostgreSQL parameters.
- pgbench throughput as the optimisation objective.

### Best observed configuration

| Parameter | Value |
|---|---|
| shared_buffers | 1009 MB |
| work_mem | 7 MB |
| max_wal_size | 3143 MB |
| wal_buffers | 11 MB |
| checkpoint_completion_target | 0.7619 |

**Best trial:** 11

**Best observed throughput:** 5246.900436 TPS

### Performance comparison

| Comparison | Observed difference |
|---|---:|
| Best BO vs baseline mean | +11.19% |
| Best grid search vs baseline mean | +3.84% |
| Best BO vs best grid search | +7.08% |

### Verification result

PASS — Twenty-five BO measurements were completed.

CAUTION — The best BO observation is a selected maximum from the search process, not an independently validated estimate of tuned performance.

---

## 5. Bayesian Optimisation Stability

The optimisation trace exhibited a substantial throughput decline after trial 11.

Representative observations:

| Trial | TPS |
|---|---:|
| 9 | 5062.75 |
| 11 | 5246.90 |
| 12 | 2467.13 |
| 16 | 2077.71 |
| 19 | 1958.03 |
| 24 | 2108.28 |

The decline persisted across multiple configurations.

Possible contributing factors include:

- Database-state changes.
- WAL and checkpoint activity.
- Background operating-system activity.
- Hardware or storage variability.
- Poorly performing configurations.
- Gaussian Process modelling limitations.

The available evidence does not establish one definitive cause.

### Verification result

PASS — The optimisation trace was preserved.

CAUTION — Benchmark drift and measurement variability limit causal interpretation of the results.

---

## 6. Post-Experiment Diagnostics

Additional diagnostic benchmarks were conducted using the restored baseline configuration.

### Baseline diagnostic throughput

| Measurement | TPS |
|---|---:|
| Initial post-BO check | 3752.14 |
| Post-maintenance check 1 | 3749.26 |
| Post-maintenance check 2 | 3713.41 |
| Post-maintenance check 3 | 2057.93 |

The diagnostic results demonstrated that throughput could vary substantially even without deliberate changes to the selected PostgreSQL configuration.

### PostgreSQL diagnostics

The following observations were recorded:

- Approximately 19 GB of cumulative WAL generation.
- More than 4.2 million committed transactions.
- Zero recorded deadlocks.
- Approximately 154,625 estimated dead tuples in `pgbench_accounts` during an earlier inspection.
- Occasional WAL write, data-file write, and transaction-lock waits.

### System monitoring

During diagnostic monitoring:

- Overall CPU utilisation was approximately 27–40%.
- Physical disk busy time was approximately 14–23%.
- Reported average disk write latency was low.
- No sustained system-wide CPU or disk saturation was evident in the sampled intervals.

These observations did not establish the cause of the throughput decline.

### Verification result

PASS — Additional diagnostic measurements were collected.

CAUTION — These diagnostic measurements are not part of the original formal baseline dataset.

---

## 7. Generated Figures

The following figures were generated from the experimental results:

```text
figures/bo.pdf
figures/bo.png
figures/grid.pdf
figures/grid.png
```

### Figure 1: Bayesian Optimisation Convergence

Includes:

- Individual trial throughput.
- Best-so-far throughput.
- Baseline mean reference.

### Figure 2: Grid Search Heatmap

Includes:

- Nine tested configurations.
- `shared_buffers` values.
- `work_mem` values.
- Measured throughput.

### Verification result

PASS — Both figures were generated from the experimental measurements.

---

## 8. Statistical Verification

The baseline sample mean and sample standard deviation were calculated from five independent benchmark invocations.

The grid-search and BO results represent single measurements per candidate configuration.

Because independent validation was not performed:

- No validated tuned-configuration mean is available.
- No validated tuned-configuration standard deviation is available.
- No reliable confidence interval for the tuned-versus-baseline difference is available.
- No statistically supported claim of BO superiority can be made.

A Welch's t-test comparing independently repeated baseline and tuned measurements was not performed.

### Verification result

PARTIAL — Descriptive statistics are available.

NOT COMPLETED — Independent validation and inferential comparison.

---

## 9. Missing Experiments

### Independent validation

The planned validation experiment consisted of:

- Five baseline measurements.
- Five measurements using the selected BO configuration.

This experiment was not performed.

Expected output:

```text
results/validation.json
```

### Supplementary experiment

The planned supplementary experiment consisted of:

- Five baseline measurements.
- Five deliberately misconfigured measurements.
- Five measurements with `synchronous_commit=off`.

This experiment was not performed.

Expected output:

```text
results/supp.json
```

Neither experiment should be described as completed in the research article.

---

## 10. Bibliography Audit

An earlier manuscript contained 21 numbered references.

The earlier audit identified nine references dated 2022–2026, representing approximately 42.9% of the bibliography.

The assignment requires:

- 15–25 references.
- At least 60% published within the required recent-year window.

### Verification requirements

Before final submission:

1. Confirm the final bibliography contains 15–25 references.
2. Verify that at least 60% satisfy the publication-year requirement.
3. Check the existence and publication metadata of each reference.
4. Ensure in-text citations match the bibliography.
5. Ensure the literature matrix reflects the final bibliography.
6. Distinguish peer-reviewed papers from preprints.

### Verification result

PENDING — The final bibliography has not been independently audited in this report.

---

## 11. Reproducibility and Safety

The experimental scripts modify PostgreSQL server configuration.

Some operations include:

```sql
ALTER SYSTEM RESET ALL;
```

These operations can remove custom settings from `postgresql.auto.conf`.

The scripts also restart PostgreSQL.

The supplementary experiment may temporarily change:

```sql
synchronous_commit = off;
```

### Required precautions

- Run experiments only on a disposable PostgreSQL instance.
- Back up `postgresql.auto.conf`.
- Avoid shared or production database instances.
- Do not store database passwords in source code.
- Do not commit credentials or private configuration files.
- Verify server configuration after experiments.
- Preserve original raw results.

A PostgreSQL restart does not guarantee that the operating-system filesystem cache has been cleared.

Therefore, the study must not claim that every trial started with a fully cold operating-system cache.

---

## 12. Repository Verification

### Available source files

```text
tune.py
supp.py
analyze.py
verify_results.py
db_connection.py
requirements.txt
README.md
FINAL_VERIFICATION.md
```

### Available experimental evidence

```text
results/baseline.json
results/grid.json
results/bo.json
results/summary.json
results/tables.txt
```

### Available figures

```text
figures/bo.pdf
figures/bo.png
figures/grid.pdf
figures/grid.png
```

### Automated verification

The repository includes:

```powershell
python verify_results.py
```

The complete audit expects validation and supplementary experiment files.

Because these experiments were not performed, the complete audit may fail.

Such a failure must not be reported as a successful full verification.

---

## 13. Research Article Verification

The final article should satisfy the following requirements:

| Requirement | Status |
|---|---|
| Baseline measurements | Completed |
| Grid-search measurements | Completed |
| Bayesian Optimisation measurements | Completed |
| Experimental graphs | Generated |
| Descriptive statistics | Available |
| Independent validation | Not completed |
| Statistical significance testing | Not completed |
| Benchmark limitations disclosed | Required |
| Final bibliography audit | Pending |
| Literature matrix consistency | Pending |
| Author information | Must be checked |
| Final IEEE page count | Must be checked |
| Plagiarism/similarity report | Not verified |

No plagiarism percentage, similarity percentage, or external authenticity certification is claimed.

---

## 14. Final Research Conclusion

The experiment successfully evaluated a fixed PostgreSQL baseline, nine grid-search configurations, and 25 Bayesian Optimisation configurations.

Bayesian Optimisation identified the highest single observed throughput of 5246.90 TPS.

This was approximately 11.19% above the original baseline mean and 7.08% above the best grid-search observation.

However, substantial benchmark variability and the absence of independent validation prevent a statistically supported conclusion that Bayesian Optimisation consistently outperforms the baseline or grid search.

The study should therefore be presented as an exploratory empirical investigation rather than a definitive demonstration of BO superiority.

---

## 15. Final Status

**Completed:**

- Baseline benchmarking.
- Grid search.
- Bayesian Optimisation.
- Descriptive performance analysis.
- BO convergence graph.
- Grid-search heatmap.
- Initial PostgreSQL performance diagnostics.

**Not completed:**

- Independent validation.
- Supplementary experiments.
- Inferential statistical testing.
- Independent bibliography verification.
- Institutional plagiarism verification.

**Overall status: Experimental implementation and exploratory analysis completed; full research verification remains incomplete.**