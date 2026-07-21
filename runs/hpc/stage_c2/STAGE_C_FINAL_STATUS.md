# Stage C final status (C2F-v3 freeze)

```text
Stage C: supported for elastic, pre-peak and peak RF–U
Production mesh: uniform H1
Refined demonstration mesh: C2C-v3 (notch-corrected)
Post-peak validation: limited
Crack-path validation: pending formal matched-state assessment
classification: stage_c_refined_response_supported
```

## Classification (scoped)

> The corrected locally refined model reproduces the uniform H1 elastic, pre-peak, and peak-load response. Residual post-peak differences remain and crack-path convergence has not yet been formally assessed.

## Pass / open matrix

| Item | Status |
| --- | --- |
| pipeline execution | pass |
| automated refined-mesh generation | pass |
| four-thread UEL qualification (H0) | pass |
| elastic equivalence | pass |
| peak/pre-peak RF–U equivalence | pass |
| post-peak equivalence | **limited** (NRMSE ≈ 24.3%) |
| crack-path equivalence | **pending** |

## Metrics (C2F-v3 vs serial H1)

| Metric | H1 | C2F-v3 | Diff |
| --- | ---: | ---: | ---: |
| Peak RF | 0.6996 | 0.6979 | **0.24%** |
| Initial stiffness (kN/mm) | 134.33 | 134.25 | **0.061%** |
| Pre-peak NRMSE | — | — | **0.089%** |
| Peak U (mm) | 0.0058 | 0.0058 | identical |
| Full-curve NRMSE | — | — | 9.0% (report) |
| Post-peak NRMSE | — | — | 24.3% (report) |
| Physical elements | 12064 | 10290 | **14.7% fewer** |
| Layered elements | — | 30870 | — |

## Jobs

| Stage | Job ID | Note |
| --- | --- | --- |
| C2F-v3 | **1376480.mmaster02** | scientific result (this freeze) |
| D1 elastic probe | 1376464.mmaster02 | K error 0.083% |
| D3 phase/SDV | 1376467.mmaster02 | SDV15 spatial |
| C2F-v2 failed | 1376444.mmaster02 | missing notch — preserve |
| H1 4-thread baseline | *to be filled* | fair walltime |

## Paths

```text
Deck:  models/generated/molnar_gravouil_2017/unified_preprocessing/H0_refined_layered_v3_notchfix/
ODB:   /scratch/.../molnar_c2f_v3_refined_final_threads4_1376480.mmaster02/
RF-U:  runs/hpc/stage_c2/recovery/c2f_v3_vs_h1/
Status: runs/hpc/stage_c2/recovery/c2f_v3_vs_h1/STAGE_C_FINAL_CLASSIFICATION.json
```

## v2 failure → v3 correction (thesis narrative)

1. Missing exact `y=0` → no notch free faces → continuous plate → K +72%, no softening.  
2. Geometry audit → force `y=0` → doubled notch faces → D1 pass → D3 spatial SDV15 → C2F-v3 peak/pre-peak agreement.

## Fair efficiency note

Do not compare C2F-v3 walltime (4 threads) to serial H1 walltime. Run `12_h1_threads4_baseline.pbs` first.

## Mail notifications

Jobs must use `#PBS -m abe`, `#PBS -M` (student + mailserver), `qsub -M` with the same list, and `scripts/hpc/pbs_job_mail_notify.sh` as mailx fallback.
