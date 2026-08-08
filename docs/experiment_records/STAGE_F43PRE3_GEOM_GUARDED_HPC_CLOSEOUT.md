# Stage C F43PRE3_GEOM Guarded HPC Job 1385460 Terminal Closeout Record

Protocol version: 1
Task ID: `F43PRE3_GEOM_SUBMISSION`
Status: `complete_failed` (`f43pre3_geom_pbs_workdir_input_deck_not_found`)
Job ID: `1385460.mmaster02`
Queue: `entry_imfdfkmq` (routed to `normal_imfdfkmq`)
Submit Host: `mlogin01.cluster`
Execution Node: `mnode098/0`
Submit Timestamp: 2026-08-08 05:14:41 CEST

## Submission Context & Hashes

- **Authorization Commit**: `b9386f47a1f468e5037e7185009df0ceae92ac8a`
- **Preparation Commit ($P$)**: `400c8ae9d538719ffd2cd6d43c1bc5d0fd81e43f`
- **Qualification Commit ($Q$)**: `40ff9617b40ad060ecf636030f32c18877984b6d`
- **Input Deck**: `models/generated/mode_ii/f43_stage_c_bridge/F43PRE3_GEOM.inp` (SHA256: `10d4fb75cc97d92fbb1491361624e92f4cc4269ed40e4420164af28ed15207ee`)
- **Source CAE**: `/home/pr21vyci/projects/adaptive-remeshing-artifacts/f43pre3/ModeII_Geometry_Source_Abaqus2023.cae` (SHA256: `0d5b32fe48b70ed0817e8b9c439bfdb39165dee5e8d157fcb6d0b3075efe1baa`)
- **Submission Wrapper**: `models/generated/mode_ii/f43_stage_c_bridge/submit_f43pre3_geom.sh`

## Terminal Execution Result

- **qsub Exit Code**: 0 (Submitted as `1385460.mmaster02`)
- **Scheduler Exit Code**: 1
- **Execution Log**: `models/generated/mode_ii/f43_stage_c_bridge/evidence/1385460.mmaster02/execution.log`
- **Log Error Excerpt**:
  ```text
  [F43PRE3_GEOM] Starting Abaqus 2023 preanalysis job at Sa 8. Aug 05:14:41 CEST 2026
  [F43PRE3_GEOM] PBS_JOBID: 1385460.mmaster02
  [F43PRE3_GEOM] Workdir: /home/pr21vyci/projects/adaptive-remeshing
  ...
  [F43PRE3_GEOM] FATAL ERROR: F43PRE3_GEOM.inp input deck missing!
  ```

## Root-Cause Analysis

1. `submit_f43pre3_geom.sh` called `qsub "${SCRIPT_DIR}/F43PRE3_GEOM.pbs"` from the repository root directory `/home/pr21vyci/projects/adaptive-remeshing`.
2. PBS automatically assigned `PBS_O_WORKDIR` to `/home/pr21vyci/projects/adaptive-remeshing`.
3. `F43PRE3_GEOM.pbs` navigated to `${PBS_O_WORKDIR}` and expected `F43PRE3_GEOM.inp` in the repository root rather than inside `models/generated/mode_ii/f43_stage_c_bridge/`.
4. `F43PRE3_GEOM.pbs` failed the file presence check and exited cleanly with status 1 before invoking Abaqus/Standard.

## Deterministic Local/Offline Repair Applied

1. Updated `submit_f43pre3_geom.sh` to explicitly `cd "${SCRIPT_DIR}"` before calling `qsub`.
2. Updated `F43PRE3_GEOM.pbs` to resolve `SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"`, change directory to `${SCRIPT_DIR}`, and invoke `collect_f43pre3_geom_evidence.sh "${PBS_JOBID:-local}"` automatically on completion.

## Governance & Next Action

- The single authorized submission (`MAX_SUBMISSIONS=1`) was consumed by job `1385460.mmaster02`.
- Automatic retries or replacement submissions without explicit user authorization are strictly prohibited.
- `F43PRE3_GEOM` remains qualified; a fresh human authorization is required for exactly one replacement submission of `F43PRE3_GEOM`.
