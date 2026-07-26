# Stage F1-J1-R1 Mode-II H0 Serial Infrastructure Replacement Record

- **Task ID**: `F1-J1-R1`
- **Stage**: Stage F (Mode-II mixed-mode benchmark)
- **Classification**: `stage_f_mode_ii_h0_serial_fail`
- **Replacement Submission Revision**: `46cf420b995ff6b2f74fecfc10fb1bb4411feaac`
- **Replacement Authorization Revision**: `2f6a0f6efc992b85c9ae79ff9006ebadd9bf81d8`
- **Scientific Freeze Revision**: `17240f646cf1e382396006ab635976fa22a67890`
- **Datacheck Job ID**: `1378911.mmaster02` (datacheck passed)
- **Original Solver Job ID**: `1378919.mmaster02` (PBS exit 7; staging fail)
- **Replacement Solver Job ID**: `1378920.mmaster02` (PBS exit 7; inline Python KeyError staging fail)
- **Replacement Solver Submissions Used**: 1 / 1 (consumed)
- **Automatic Retry Authorized**: `false` (prohibited)
- **Status**: `failed_execution_blocked`

## Execution Summary

1. **Submission**:
   - Replacement job `1378920.mmaster02` was submitted to queue `entry_imfdfkmq` and routed to `normal_imfdfkmq` on host `mnode098/0`.
   - Resource allocation: 1 CPU, 16 GB RAM, 04:00:00 walltime limit.

2. **Failure Analysis**:
   - The job exited with PBS `Exit_status = 7` before Abaqus solver execution.
   - Root Cause: In `02_mode_ii_h0_serial.pbs`, line 174 attempted to access `matches["deck_hash_match"]`, whereas the dictionary loop had created key `matches["deck_sha256_match"]`. This threw a Python `KeyError` exception before `MODE_II_H0_RUNTIME_STAGING_CHECK.json` could be written.
   - `MODE_II_H0_SERIAL_STATUS.json` recorded `stage_f_mode_ii_h0_serial_staging_fail` with `abaqus_return_code: -1`.

3. **Boundary Assertions & Next Actions**:
   - One-shot replacement solver authorization is 100% consumed (`replacement_submissions_used: 1`).
   - No automatic retry or replacement job is permitted (`automatic_retry_authorized: false`).
   - Downstream Stage F tasks (F2 and beyond) remain **blocked**.
   - Recorded in `docs/project/MISTAKES_AND_FIXES_LOG.md` under entry `M-091`.
