# Session Report: `F96SUB-M2-INSTRUMENTED-RESTART1-R1R11-PRODUCTION-SUBMISSION1`

- **Task ID**: `F96SUB-M2-INSTRUMENTED-RESTART1-R1R11-PRODUCTION-SUBMISSION1`
- **Active Agent**: `gemini-antigravity`
- **Candidate Name**: `M2STATE_FRACFIX_RESTART1R1R11`
- **PBS Job ID**: `1389278.mmaster02`
- **Target Queue**: `entry_imfdfkmq` (1 CPU, 16 GB, 24:00:00 walltime)
- **Execution Date**: 14 August 2026
- **Status Verdict**: `SUBMITTED_RUNNING_IN_QUEUE`
- **Governance**: Single authorized HPC submission executed (`qsub_call_count = 1`, `max_permitted_submissions = 1`, `authorization_consumed = true`, `automatic_retry = false`).

---

## 1. Submission Trace & Verification

1. **Preflight Verification**:
   - Guarded wrapper `./submit_m2state_fracfix_restart1r1r11.sh --execute` executed on `mlogin01`.
   - Verified sealed package manifest (`c3d0d249988b453a79f0aa204d147d9f6bb3af8969b02cb9323db58ff8030e84`): 100% PASS.
   - Job submitted to PBS: `1389278.mmaster02`.
   - Submission notification issued via `notify_submitted`.

2. **Policy Compliance**:
   - Exactly one submission performed (`qsub_call_count = 1`).
   - Zero unauthorized retries (`automatic_retry = false`).
   - Zero polling loops performed on scheduler.
   - Candidate `M2STATE_FRACFIX_RESTART2R10` remains completely untouched.

---

## 2. Invariants & Submission Summary

```text
source_job = 1386469.mmaster02
candidate = M2STATE_FRACFIX_RESTART1R1R11
job_id = 1389278.mmaster02
submission_time = 2026-08-14T10:17:35Z
queue = entry_imfdfkmq
resources = select=1:ncpus=1:mpiprocs=1:mem=16gb,walltime=24:00:00
manifest_hash = c3d0d249988b453a79f0aa204d147d9f6bb3af8969b02cb9323db58ff8030e84
single_authorized_submission_executed = true
authorization_consumed = true
max_permitted_submissions = 1
qsub_call_count = 1
automatic_retry = false
qdel_called = false
qmove_called = false
M2STATE_FRACFIX_RESTART2R10_modified = false
status = SUBMITTED_RUNNING_IN_QUEUE
```
