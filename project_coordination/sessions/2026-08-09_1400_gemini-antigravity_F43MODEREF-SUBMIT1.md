# Session Report: F43MODEREF-SUBMIT1

- **Task ID**: `F43MODEREF-SUBMIT1`
- **Agent**: `gemini-antigravity`
- **Date**: `2026-08-09`
- **Starting Commit**: `42444682054ff46b9a896d8e063853155702ddf8`
- **Preparation Commit**: `417e3b8dbb74e36bb6942250e56b6c0ac9427475` (`P43MODEREF3`)
- **Qualification Commit**: `42444682054ff46b9a896d8e063853155702ddf8` (`Q43MODEREF3-FINAL3`)
- **Classification**: `guarded_replacement_reference_batch_submitted`

## Human Authorization & Execution Evidence Summary

1. **Explicit Human Chat Authorization**:
   - `authorization_received`: `true`
   - `authorization_sentence`: `"I authorize exactly two guarded HPC submissions for the repaired Mode-II uniform phase-field reference convergence batch using preparation commit 417e3b8dbb74e36bb6942250e56b6c0ac9427475 (P43MODEREF3) and qualification commit 42444682054ff46b9a896d8e063853155702ddf8 (Q43MODEREF3-FINAL3). I authorize exactly these two independent jobs: M2REF_H1_REPAIR using input deck SHA256 4ac37c50a26d67106e5c1e6083937f9b0716c3646c90ad87c51a8ef9b172808e, 1 CPU, 16 GB memory, and 06:00:00 walltime; and M2REF_H2_REPAIR using input deck SHA256 a651cef82999d333bd9062cc4d743a98908178535623dd8ca8ed7993dfe23de0, 1 CPU, 32 GB memory, and 18:00:00 walltime. Both jobs shall use user subroutine SHA256 5dc005383773a2923b943024b97dc15590a4f220e319fd289c891b15c30844f3, Abaqus 2023, gcc/11.4.0, intel/2024.2.0, and queue entry_imfdfkmq. MAX_SUBMISSIONS=2 and both jobs may run concurrently. Historical Mode-II H0 job 1378942.mmaster02 remains the accepted coarse convergence point and is not authorized for resubmission. Failed jobs 1385728.mmaster02 and 1385729.mmaster02 are historical only and are not authorized for retry. No automatic retries, replacement submissions beyond these two jobs, qmove, qdel, MM or PK5 production run, additional uniform-reference job, or downstream job are authorized."`
   - `maximum_jobs_authorized`: `2`

2. **Submitted PBS Jobs on `tu_freiberg`**:
   - `Job 1`: `M2REF_H1_REPAIR`
     - `PBS_JOB_ID`: `1385895.mmaster02`
     - `Queue`: `entry_imfdfkmq` (`normal_imfdfkmq`)
     - `Status`: `Q` (Queued)
     - `Input SHA256`: `4ac37c50a26d67106e5c1e6083937f9b0716c3646c90ad87c51a8ef9b172808e`
     - `Resources`: 1 CPU, 16 GB memory, 06:00:00 walltime
   - `Job 2`: `M2REF_H2_REPAIR`
     - `PBS_JOB_ID`: `1385896.mmaster02`
     - `Queue`: `entry_imfdfkmq` (`normal_imfdfkmq`)
     - `Status`: `Q` (Queued)
     - `Input SHA256`: `a651cef82999d333bd9062cc4d743a98908178535623dd8ca8ed7993dfe23de0`
     - `Resources`: 1 CPU, 32 GB memory, 18:00:00 walltime

3. **Authority Consumption**:
   - `execution_authorized`: `true`
   - `submission_approved`: `true`
   - `maximum_jobs_authorized`: `2`
   - `actual_submissions_made`: `2`
   - `qsub_called`: `true`
   - `consumed_authorization_jobs`: `["1385895.mmaster02", "1385896.mmaster02"]`
   - `remaining_authorized_submissions`: `0`
