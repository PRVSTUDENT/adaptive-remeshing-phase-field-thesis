# Current project state

Updated: 2026-07-28
Protocol version: 1
Classification: `stage_f_mode_ii_h1_endpoint_sweep_submitted`

## Git

| Item | Value |
|---|---|
| Active job IDs | `1379481.mmaster02`, `1379482.mmaster02`, `1379483.mmaster02`, `1379484.mmaster02` |
| Active agent | none (session released) |
| Active task | **F2-H1-ENDPOINT-SWEEP-BATCH** (`batch_submitted_pending_results`) |

## Submission boundary (critical)

```text
Current task: F2-H1-ENDPOINT-SWEEP-BATCH
Status: batch_submitted_pending_results
Classification: stage_f_mode_ii_h1_endpoint_sweep_submitted
active_job_ids: ["1379481.mmaster02", "1379482.mmaster02", "1379483.mmaster02", "1379484.mmaster02"]
execution_authorized: false (consumed)
submission_approved: false (consumed)
maximum_batch_submissions: 4
submissions_used: 4
maximum_running_jobs: 2
maximum_jobs_now: 0
automatic_retry_authorized: false
```

The four Stage F Mode-II H1 endpoint sweep jobs have been submitted to the HPC scheduler:
- `u015` ($U_1 = 0.015\text{ mm}$): Job ID `1379481.mmaster02`
- `u020` ($U_1 = 0.020\text{ mm}$): Job ID `1379482.mmaster02`
- `u030` ($U_1 = 0.030\text{ mm}$): Job ID `1379483.mmaster02`
- `u040` ($U_1 = 0.040\text{ mm}$): Job ID `1379484.mmaster02`

## Next Action

Wait until all 4 jobs reach terminal scheduler states (`F`), then collect lightweight evidence and perform combined closeout in task `F2-H1-ENDPOINT-SWEEP-BATCH-CLOSE`. All submission flags are consumed (`maximum_jobs_now = 0`).
