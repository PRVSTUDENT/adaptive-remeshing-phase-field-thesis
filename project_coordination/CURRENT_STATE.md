# Project Current State

Last Updated: 2026-08-09T17:15:00+02:00
Active Agent: gemini-antigravity
Protocol Version: 1

## Active Task
- Task ID: `F43MODEREF-VERIFY-SUBMIT1`
- Task Description: Preflight and execution of authorized Mode-II FRACFIX verification batch (M2REF_ONEEL_FRACFIX_VERIFY and M2REF_H0_FRACFIX_REPRO).
- Status: `authorized_submitting_verification_batch`
- Preparation Tag: `P43MODEREF5-FINAL1` (`3f4f23d9fca381e1899efc6ab721ce5cf0b02411`)
- Qualification Tag: `Q43MODEREF5` (`926fbb5001ffae01e63a15afbf1a7008cf36eecb`)
- Qualification Location: `/home/pr21vyci/projects/adaptive-remeshing-worktree-p5` (Detached HEAD, 618/618 tests pass, naturally clean)

## Authorized Verification Batch (Pair 1)
1. **`M2REF_ONEEL_FRACFIX_VERIFY`**:
   - `input_SHA256`: `0a86b66a5434e06415c1721fbf6b21ee0e38b1107803efb2836070c9f5b35512`
   - `UEL_SHA256`: `0bc4378179a35acd9954d20d3e07517f8e1c356ae07a23c40e7715cd7b56dce8`
   - `PBS_SHA256`: `ab099bddfe035f37df9b034b56eb38756019f5012ca590a279efc75b48c6bd26`
   - `submit_wrapper_SHA256`: `09edb59b8943f0577b96512d8a4f900bb4e04525691d6ce772cd3f95400cb99c`
   - Resources: 1 CPU, 8 GB memory, 00:15:00 walltime, Queue `entry_imfdfkmq`

2. **`M2REF_H0_FRACFIX_REPRO`**:
   - `input_SHA256`: `4bcc529509d3491bfffb28b33078f0759cb55cdac2bcabbbadb6be99a5fc08f5`
   - `UEL_SHA256`: `0bc4378179a35acd9954d20d3e07517f8e1c356ae07a23c40e7715cd7b56dce8`
   - `PBS_SHA256`: `fe146489d62fe6cca6cdcf6584c3637687229878bcc9508f7f676bc26d52d064`
   - `submit_wrapper_SHA256`: `16d4d2d7746b3144bdf6a5de2c858e44c33ede0fc7b951f96f879507c16b4d9a`
   - Resources: 1 CPU, 8 GB memory, 01:00:00 walltime, Queue `entry_imfdfkmq`

## Current HPC Authority Boundary
- `authorization_ready_for_verification_batch = true`
- `execution_authorized = true`
- `submission_approved = true`
- `maximum_jobs_authorized = 2`
- `actual_submissions_made = 0`
- `qsub_called = false`
