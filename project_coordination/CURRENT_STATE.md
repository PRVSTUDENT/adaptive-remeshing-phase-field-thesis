# Current project state

Updated: 2026-07-28
Protocol version: 1
Classification: `stage_f_mode_ii_h1_endpoint_sweep_authorized`

## Git

| Item | Value |
|---|---|
| Active job ID | none (batch submission pending) |
| Active agent | gemini-antigravity |
| Active task | **F2-H1-ENDPOINT-SWEEP-BATCH** (authorized, 4 jobs) |

## Submission boundary (critical)

```text
Current task: F2-H1-ENDPOINT-SWEEP-BATCH
Status: prepared_and_authorized
Classification: stage_f_mode_ii_h1_endpoint_sweep_authorized
active_job_ids: []
execution_authorized: true
submission_approved: true
maximum_batch_submissions: 4
submissions_used: 0
maximum_running_jobs: 2
maximum_jobs_now: 4
automatic_retry_authorized: false
```

Four Stage F Mode-II H1 endpoint sweep packages (`u015`, `u020`, `u030`, `u040`) have been deterministically generated, statically validated, and authorized for batch submission.
- **Formulation:** Accepted Molnar staggered UEL/UMAT formulation ($h_1 = 0.0025\text{ mm}$, 12,064 physical elements, 12,382 nodes). Redundant tension BCs (`topl`, `bottoml`) removed.
- **Resource Request:** 1 CPU, 16 GB RAM, 06:00:00 walltime per job.
- **Guarded Wrapper:** `scripts/hpc/stage_f/mode_ii_h1_endpoint_sweep/submit_mode_ii_h1_endpoint_sweep_batch.sh`.

## Next Action

Fast-forward cluster clone, run preflight checks, execute guarded batch submission wrapper once in submission mode (`MODE_II_H1_ENDPOINT_SWEEP_SUBMIT=1`).
