# C2C 1376305 Failure Analysis

## Job identity

| Field | Value |
| --- | --- |
| Job ID | `1376305.mmaster02` |
| Job name | `c2c_rebuild_val` |
| Submission record | `C2_RESUME_FROM_C2B_SUBMISSION_RECORD.txt` |
| Project revision at submit | `4ecf73e0bfadab45642740a88133b8ddfb2811c4` |
| Exit status | `12` |
| Walltime used | `00:00:02` |
| Exec host | `mnode104` |
| Abaqus executed | **No** (`solver_executed=false`; no `.odb`, 2 s runtime) |

## Paths from `qstat -xf`

| Field | Path |
| --- | --- |
| Output_Path | `/scratch/pr21vyci/adaptive-remeshing/pbs_output/stage_c2b_20260721T093329+0200_4ecf73e0bfad/c2c.out` (empty) |
| Error_Path | `/scratch/pr21vyci/adaptive-remeshing/prestage/stage_c2b_20260721T093329+0200_4ecf73e0bfad/c2c_rebuild_val.e1376305` (empty) |
| PBS_O_WORKDIR / prestage | `/scratch/pr21vyci/adaptive-remeshing/prestage/stage_c2b_20260721T093329+0200_4ecf73e0bfad` |
| Scratch run dir | `/scratch/pr21vyci/adaptive-remeshing/runs/c2c_rebuild_validate_1376305.mmaster02` |
| Light evidence | `/home/pr21vyci/projects/adaptive-remeshing/runs/hpc/stage_c2/c2c_rebuild_validate/evidence/1376305.mmaster02` |

## Environment

From `python_version.txt` in the run directory:

- Module Python 3.11.7 (gcc 11.4.0 stack) selected successfully
- `yaml` import succeeded
- Failure occurred **after** Python environment setup

## Exact failing command

```bash
python3 scripts/preprocessing/build_molnar_unified_deck.py \
  --config configs/preprocessing/molnar_h0_h1_unified.yaml \
  --role-name H0_refined \
  --output-profile fracture_baseline \
  --from-nodes-csv <C2B refined CSVs> \
  --from-elems-csv <C2B refined CSVs> \
  --out <H0_refined_layered>
```

## Root cause (exact)

`FileNotFoundError` while hashing the preserved Molnar supplementary source:

```text
.../models/baseline_original/molnar_gravouil_2017/02_Single_Notch_Tension/SingleNotch.inp
```

The `git archive` prestage for the C2B→C2C recovery submission **did not include**
`models/baseline_original/...`. The deck builder requires that file (and
`SingleNotch.for`) to:

1. verify preserved-source integrity (SHA-256);
2. generate Fortran with the correct `N_ELEM` from the supplementary template.

PBS exit code `12` was the generic C2C controlled failure exit; the evidence class
was `rebuild_failure` (generic at that revision — no structured `C2C_STATUS.json`
with `failed_check` yet).

## Why C2B was valid while C2C failed

| Stage | Needed products | Status |
| --- | --- | --- |
| C2B | C2A continuum ODB + export/remesh Python (self-contained) | Present; gate passed; refined mesh written |
| C2C | C2B refined CSVs **plus** baseline `SingleNotch.inp/.for` in prestage | CSVs present; **baseline missing from prestage** |

C2B does not read the baseline layered Molnar sources. C2C rebuilds the **layered
UEL/UMAT deck** from the refined physical mesh and therefore must prestage the
author supplementary sources.

## Downstream impact

C2D–C2F (`1376306–1376308`) used `afterok` on C2C. After C2C failed, PBS deleted
those dependents without execution (no `stime`, no resource usage). They are
finished-historical (`F`) but **did not run**.

## Corrections implemented

1. Include `models/baseline_original/.../SingleNotch.*` in C2 prestage path lists.
2. C2C PBS: fallback copy from `$PROJECT_HOME` if prestage baseline missing.
3. LF-normalized + dual (CRLF/LF) preserved-hash acceptance (Windows vs HPC).
4. Lazy study-YAML load when rebuilding from external refined CSVs.
5. Safe `path_under_root` for `/scratch` vs `/scratchN` aliases.
6. Validator role `H0_refined` (do not apply author H0 corridor checks).
7. Structured `C2C_STATUS.json` / `C2C_FAILURE_REPORT.md` with `failed_check`.
8. Recovery chain: `afterany` + markers `C2C.ok`…`C2F.ok` (visible skip records).

## Confirmation

- No Abaqus analysis ran in C2C 1376305 (2 s wall, no ODB, rebuild only).
- C2A `1376298` and C2B `1376304` remain frozen and are reused.
- Remeshing parameters were not changed.
