# Stage C five-job campaign

Status: `job2_scientific_gate_fail_stop`  
Updated: 2026-07-21

## Queue policy (validated)

```text
submit through entry_imfdfkmq
→ scheduler may route to normal_imfdfkmq
→ Job 2 wait ≈ 1 s (immediate start)
```

## Job status

| Job | ID | Wait | Result |
|---|---|---|---|
| 1 smoke | `1376292` | ≈11.6 min | technical + field availability **PASS** |
| 2 pre-analysis | `1376296` | ≈1 s | technical **PASS**; scientific **FAIL** (`miseseri_output_available_but_scientifically_inactive`) |
| 3 remesh | — | — | **NOT RELEASED** |
| 4–5 | — | — | blocked |

## Job 2 scientific stop

```text
max(MISESERI) ≈ 8.9e-14
max(von Mises on umatelem) ≈ 3.2e-13
errorTarget=0.05 marks 0 elements
```

Root cause: MISESERI/S recovered from residual-stiffness CPS4 UMAT facsimile, not from load-bearing U2 UEL.

Evidence package:

```text
runs/hpc/stage_c_miseseri/molnar_h0_miseseri_preanalysis/evidence/1376296.mmaster02/
  JOB2_GATE_REPORT.md
  JOB2_FIELD_SUMMARY.json
  JOB2_TECHNICAL_SUMMARY.json
  JOB2_MISESERI_ELEMENT_DATA.csv
  figures/01..05_*.png
```

No automatic Job 2 retry. No Job 3 `qsub`.
