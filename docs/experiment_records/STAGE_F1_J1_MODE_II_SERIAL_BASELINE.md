# Stage F1-J1 Mode-II H0 Serial Baseline Record

- **Task ID**: `F1-J1`
- **Stage**: Stage F (Mode-II mixed-mode benchmark)
- **Classification**: `stage_f_mode_ii_h0_serial_fail`
- **Operational Submission Revision**: `5b092853419e8e8829d7f4c024ce3ea78d131740`
- **Authorization Revision**: `44d928a00f77c3e6b0515c3d045b1be2ab4bb9a9`
- **Scientific Freeze Revision**: `17240f646cf1e382396006ab635976fa22a67890`
- **Datacheck Job ID**: `1378911.mmaster02` (datacheck passed)
- **Solver Job ID**: `1378919.mmaster02` (PBS exit 7; staging fail)
- **Solver Submissions Used**: 1 / 1 (consumed)
- **Automatic Retry Authorized**: `false` (prohibited)
- **Status**: `failed_execution_blocked`

## Execution Summary

1. **Submission**:
   - Job `1378919.mmaster02` was submitted to queue `entry_imfdfkmq` and routed to `normal_imfdfkmq` on host `mnode098/0`.
   - Resource allocation: 1 CPU, 16 GB RAM, 04:00:00 walltime limit.

2. **Failure Analysis**:
   - The job exited with PBS `Exit_status = 7` before Abaqus solver execution.
   - Root Cause: In `02_mode_ii_h0_serial.pbs`, the input file was copied to `${SCRATCH_RUN}/${JOB_NAME}.inp` (`mode_ii_h0_serial.inp`). `DECK_SHA` was then computed using `sha256sum ModeII_H0_serial.inp`, which failed because the original filename no longer existed in scratch.
   - `MODE_II_H0_RUNTIME_MANIFEST.json` recorded `deck_sha256: ""`, resulting in a runtime staging mismatch (`stage_f_mode_ii_h0_serial_staging_fail`).

3. **Boundary Assertions & Next Actions**:
   - One-shot solver authorization is 100% consumed (`solver_submissions_used: 1`).
   - No automatic retry or replacement job is permitted (`automatic_retry_authorized: false`).
   - Downstream Stage F tasks (F2 and beyond) remain **blocked**.
   - Recorded in `docs/project/MISTAKES_AND_FIXES_LOG.md` under entry `M-090`.
