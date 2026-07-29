# Current project state

Updated: 2026-07-29
Protocol version: 1
Classification: `stage_f3_submitted`

## Git

| Item | Value |
|---|---|
| Active job IDs | `1379576.mmaster02`, `1379577.mmaster02` |
| Active agent | `gemini-antigravity` (session claimed) |
| Active task | **F3-STAGE-F3-SUBMIT** (`submitted`) |

## Submission boundary (critical)

```text
Current task: F3-STAGE-F3-SUBMIT
Status: submitted
Classification: stage_f3_submitted
active_job_ids: ["1379576.mmaster02", "1379577.mmaster02"]
completed_job_ids: ["1379481.mmaster02", "1379482.mmaster02", "1379483.mmaster02", "1379484.mmaster02"]
execution_authorized: true
submission_approved: true
maximum_batch_submissions: 2
submissions_used: 2
maximum_running_jobs: 2
maximum_jobs_now: 2
automatic_retry_authorized: false
```

## Summary of Active Jobs & Submitted Configuration

1. **Candidate Job A (Mode-II H2 Uniform Reference Serial):**
   - **PBS Job ID:** `1379576.mmaster02`
   - **Queue:** `entry_imfdfkmq` (1 CPU, 16 GB RAM, 12:00:00 walltime)
   - **Purpose:** Full non-linear phase-field shear fracture simulation at frozen reference displacement endpoint $U_1 = 0.020\text{ mm}$ ($33,852$ physical elements, true notch topology).
   - **Deck SHA-256:** `559e060988224874fd18328ef2eb7eac2aab23f1adebcbeac3c6664787e209d6`
   - **Fortran SHA-256:** `49c9054ab5faec9e069e0a9149af5058e6f1e11ab164c2a0e318f60282309b37`

2. **Candidate Job B (Pandey-Kumar MISESERI Pre-Analysis):**
   - **PBS Job ID:** `1379577.mmaster02`
   - **Queue:** `entry_imfdfkmq` (1 CPU, 16 GB RAM, 01:00:00 walltime)
   - **Purpose:** Linear elastic pre-analysis at load level $U_1 = 0.001\text{ mm}$ ($3,930$ `CPE4` plane-strain elements, 15 coincident node pairs along true slit).
   - **Deck SHA-256:** `484edd39e6930758346764e5e183b5fd050577bdb6b11ede5cba49b955307fe9`

## Next Action

Monitor active HPC jobs `1379576.mmaster02` and `1379577.mmaster02` to completion and close out lightweight evidence.
