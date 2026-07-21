# Stage C Five-Job Executable Manifests (Frozen)

Status: `frozen_for_execution`  
Authorization: `docs/decisions/STAGE_C_EXECUTION_AUTHORIZATION.md`  
Date: 2026-07-21

Exactly **one** submission of each job is authorized. No automatic retries.

## Common

| Field | Value |
|---|---|
| Preferred small-job queue | `entry_imfdfkmq` (route; do **not** hard-code `normal_imfdfkmq`) |
| Job 5 full fracture queue | `normal_imfdfkmq` unless another eligible queue is faster |
| Serial | `ncpus=1` |
| Mail | `#PBS -m abe`; recipient via `qsub -M` |
| Modules | `gcc/11.4.0`, `intel/2024.2.0`, `abaqus/2023` |
| Prestaging | immutable `git archive` snapshot + `PROJECT_REVISION` |
| Heavy outputs | scratch only |
| Live check | `qstat -Qf entry_imfdfkmq` + `qstat -q` before each submit |

## Job 1 — MISESERI smoke

| Field | Value |
|---|---|
| PBS | `scripts/hpc/molnar_h0_miseseri_smoke.pbs` |
| Submit | `scripts/hpc/submit_stage_c_job1_smoke.sh` |
| Class | solver |
| Mem / wall | 8gb / 01:00:00 |
| Deck | `.../H0_fullgen_elastic_preanalysis_smoke/` |
| U | smoke 0.001 mm |
| Outputs | MISESERI, MISESAVG, S, EVOL, U, RF, SDV |

## Job 2 — H0 elastic pre-analysis

| Field | Value |
|---|---|
| PBS | `scripts/hpc/molnar_h0_miseseri_preanalysis.pbs` |
| Class | solver |
| Mem / wall | 16gb / 02:00:00 |
| Deck | `.../H0_fullgen_elastic_preanalysis/` |
| U_pre | **0.00464 mm** (= 0.8 × 0.0058) |
| Outputs | MISESERI, MISESAVG, S, EVOL, U, RF, SDV |

## Job 3 — CAE remesh export

| Field | Value |
|---|---|
| PBS | `scripts/hpc/molnar_h0_miseseri_remesh.pbs` |
| Class | CAE + system-python remesh (no Standard solve) |
| Mem / wall | 16gb / 01:00:00 |
| Extract | `scripts/remeshing/extract_miseseri_from_odb.py` |
| Remesh | `scripts/remeshing/build_refined_mesh_from_miseseri.py` |
| Rule | `configs/remeshing/miseseri_h0_to_h1_initial.json` |
| Env | `PREANALYSIS_ODB`, plus MISESERI_* in extract |

## Job 4 — Refined integrity

| Field | Value |
|---|---|
| PBS | `scripts/hpc/molnar_h0_refined_integrity.pbs` |
| Class | solver |
| Mem / wall | 16gb / 02:00:00 |
| Deck | rebuilt `H0_refined_layered` after Job 3 |

## Job 5 — Refined fracture

| Field | Value |
|---|---|
| PBS | `scripts/hpc/molnar_miseseri_refined_final.pbs` |
| Class | solver |
| Mem / wall | 32gb / 06:00:00 |
| Reference | uniform H1 |
| Crack path | exploratory only |

## Remeshing rule freeze

```text
errorTarget=0.05
refinementFactor=2.0
minElementSize=0.0025 mm
maxElementSize=0.025 mm
passes=1
coarsening=disabled
```
