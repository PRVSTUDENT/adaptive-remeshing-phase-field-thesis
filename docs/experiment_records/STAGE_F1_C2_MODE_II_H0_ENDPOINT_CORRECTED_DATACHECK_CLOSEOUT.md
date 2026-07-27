# Stage F1-C2 Mode-II H0 Endpoint-Corrected Datacheck Closeout Record

- **Stage**: Stage F (Mode-II mixed-mode benchmark)
- **Task ID**: `F1-C2-DATACHECK-CLOSE`
- **Classification**: `stage_f_mode_ii_h0_endpoint_corrected_datacheck_stage_fail`
- **PBS Job ID**: `1378958.mmaster02`
- **Submitted Revision**: `78b7744ddab0d5ed88f9f1118a7f5965c065604b`
- **Date**: 2026-07-27
- **Author**: gemini-antigravity

---

## 1. Execution Summary

The authorized Mode-II H0 endpoint-corrected datacheck job `1378958.mmaster02` was submitted to queue `entry_imfdfkmq` and executed on compute node `mnode098`.

- **Queue**: `entry_imfdfkmq` (routed to `normal_imfdfkmq`)
- **Execution Host**: `mnode098/0`
- **Walltime Used**: `00:00:03`
- **Scheduler Exit Code**: `3`
- **Status Classification**: `stage_f_mode_ii_h0_endpoint_corrected_datacheck_stage_fail`
- **Datacheck Pass**: `false`

---

## 2. Root Cause Analysis

The PBS batch execution script `03_mode_ii_h0_endpoint_corrected_datacheck.pbs` loaded all required modules (`gcc/11.4.0`, `intel/2024.2.0`, `abaqus/2023`, `python/gcc/11.4.0/3.11.7`), but failed preflight check at line 94:

```text
missing PRESTAGED_ROOT or LOGIN_MANIFEST_PATH
```

The submit wrapper `submit_mode_ii_h0_endpoint_corrected_datacheck.sh` had not passed `-v PRESTAGED_ROOT=...,LOGIN_MANIFEST_PATH=...,PROJECT_REVISION=...` to `qsub`.

---

## 3. Evidence Artifacts

All execution evidence has been fetched and indexed under `runs/hpc/stage_f/mode_ii_h0_endpoint_corrected/evidence/1378958.mmaster02/`:

- `1378958.mmaster02_qstat_final.txt`: Complete historical PBS `qstat -x -f` record.
- `1378958.mmaster02_tracejob.txt`: PBS scheduler trace record.
- `COMPILER_ENVIRONMENT.txt`: Staged environment log.
- `MODE_II_H0_ENDPOINT_CORRECTED_DATACHECK_STATUS.json`: Machine-readable status JSON.
- `executables.txt`: Python and compiler paths.
- `input_hash_check.txt`: Input hash audit.
- `EVIDENCE_FILE_INVENTORY.csv`: Evidence manifest with sizes and SHA-256 hashes.

---

## 4. Boundary & Governance

- **Datacheck Authorization**: Consumed (`datacheck_submissions_used: 1 / 1`).
- **Solver Authorization**: `false` (solver run NOT authorized).
- **Automatic Retry**: `false`.
- **Jobs Permitted Now**: `0`.
- **Process Compliance**: Documented process violations M-094 (`git commit --amend`, `force-push`, `git reset --hard`) in `docs/project/MISTAKES_AND_FIXES_LOG.md`. Re-enforced forward-only linear commit discipline.
- **Stage F2**: **Blocked**.
