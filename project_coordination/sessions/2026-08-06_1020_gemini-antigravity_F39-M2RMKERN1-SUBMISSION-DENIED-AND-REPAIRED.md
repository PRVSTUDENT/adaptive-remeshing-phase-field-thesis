# Session Report: F39 M2RMKERN1 Submission Denial & PBS Queue Repair

- **Date**: 2026-08-06
- **Agent**: gemini-antigravity
- **Task ID**: `F39-M2RMKERN1-AUTHORIZED-SUBMISSION`
- **Qualification Revision (Q)**: `33b2fc6f14dcf0e2b657badc800e4a4b0f107f69`
- **Repair Preparation Revision (P2)**: `ae8441d945bc3a2d6b176d37de6500a070d1268e`
- **Classification**: `f39_m2rmkern1_submission_denied_pbs_queue_policy`

---

## 1. Summary of Events

1. **Submission Attempt**:
   - Explicit human authorization was received for submitting `M2RMKERN1` from qualification commit `33b2fc6f14dcf0e2b657badc800e4a4b0f107f69`.
   - Cluster clone `/scratch9/pr21vyci/f21_exec_83cbfe0` was fast-forwarded to `33b2fc6f14dcf0e2b657badc800e4a4b0f107f69`.
   - Execution wrapper `submit_stage_f39_cae_kernel_diagnostic.sh` was invoked with `F39_ALLOW_SUBMISSION=true` and `F39_AUTHORIZE_M2RMKERN1=true`.
   - Scheduler output:
     ```text
     qsub: Access to queue is denied
     ```
   - **Root Cause Analysis**: `M2RMKERN1.pbs` used `#PBS -q normal_imfdfkmq` and `#PBS -l nodes=1:ppn=1`. The PBS routing queue configuration requires student submissions to target `#PBS -q entry_imfdfkmq` and specify resources as `#PBS -l select=1:ncpus=1:mpiprocs=1:ompthreads=1:mem=8gb`.
   - **Authority & Job ID**: Submission was denied by PBS before any job ID was assigned. Zero authority was consumed and no job executed.

2. **Offline Package Repair P2 (`ae8441d945bc3a2d6b176d37de6500a070d1268e`)**:
   - Repaired `M2RMKERN1.pbs` headers:
     - `#PBS -q entry_imfdfkmq`
     - `#PBS -l select=1:ncpus=1:mpiprocs=1:ompthreads=1:mem=8gb`
   - Recalculated and froze package SHA-256 manifests (`SHA256SUMS`, `F39_SHA256SUMS`, `PACKAGE_MANIFEST.json`).

3. **Detached Clean-Linux Qualification**:
   - Qualification worktree `/tmp/f39_clean_qual_ae8441d` created from commit `ae8441d945bc3a2d6b176d37de6500a070d1268e`.
   - Verified 12/12 unit tests, static validator (0 failures), bash syntax, Python compilation, and manifest checksums.

---

## 2. Consumed & Remaining Authority

- `execution_authorized`: `false`
- `submission_approved`: `false`
- `maximum_jobs_now`: `0`
- `maximum_future_submissions`: `0`
- `retry_authorized`: `false`
- `replacement_authorized`: `false`
- `automatic_retry`: `false`
