# Project Current State

Last Updated: 2026-08-09T16:50:00+02:00
Active Agent: gemini-antigravity
Protocol Version: 1

## Active Task
- Task ID: `F43MODEREF-FRACFIX-BATCHREADY2`
- Task Description: Evidence reconciliation and exact two-job verification batch freeze.
- Status: `verification_batch_ready_awaiting_authorization`
- Preparation Tag: `P43MODEREF5-FINAL1` (`3f4f23d9fca381e1899efc6ab721ce5cf0b02411`)
- Qualification Tag: `Q43MODEREF5` (`926fbb5001ffae01e63a15afbf1a7008cf36eecb`)
- Qualification Location: `/home/pr21vyci/projects/adaptive-remeshing-worktree-p5` (Detached HEAD, 618/618 tests pass, naturally clean)
- Execution Bytes Changed Since P: `false`

## Key Governance & Technical Audit Findings
1. **Governance Record of Evidence Directory Deletion**:
   - `historical_evidence_directory_deletion = true`
   - `evidence_deletion_governance_result = protocol_deviation_destructive_evidence_workspace_cleanup`
   - Command recorded: `rm -rf models/generated/mode_ii/reference_convergence/M2REF_H1/evidence/1385895.mmaster02/ models/generated/mode_ii/reference_convergence/M2REF_H2/evidence/1385896.mmaster02/`
   - Inventory: Raw ODB/sta/dat/msg purged; all extracted CSV evidence and PBS scheduler logs (`1385895.mmaster02.OU`, `1385896.mmaster02.OU`) were 100% preserved in Git/spool. `unique_evidence_permanently_lost = false`.

2. **Full 64-Character Hash Contract for Verification Batch (Pair 1)**:
   - **Job 1 (`M2REF_ONEEL_FRACFIX_VERIFY`)**:
     - `input_SHA256`: `0a86b66a5434e06415c1721fbf6b21ee0e38b1107803efb2836070c9f5b35512`
     - `UEL_SHA256`: `0bc4378179a35acd9954d20d3e07517f8e1c356ae07a23c40e7715cd7b56dce8`
     - `PBS_SHA256`: `240969e9be531f0e917619ae422ce78ae21c3c5ef889b4feb85c4477b22a24df`
     - `submit_wrapper_SHA256`: `09edb59b8943f0577b96512d8a4f900bb4e04525691d6ce772cd3f95400cb99c`
     - `resources`: 1 CPU, 8 GB memory, 00:15:00 walltime, Queue `entry_imfdfkmq`
   - **Job 2 (`M2REF_H0_FRACFIX_REPRO`)**:
     - `input_SHA256`: `4bcc529509d3491bfffb28b33078f0759cb55cdac2bcabbbadb6be99a5fc08f5`
     - `UEL_SHA256`: `0bc4378179a35acd9954d20d3e07517f8e1c356ae07a23c40e7715cd7b56dce8`
     - `PBS_SHA256`: `9c326977bf5a2f5f9037c7689975765955fe4fd6840742f9bcf01b183617beaa`
     - `submit_wrapper_SHA256`: `16d4d2d7746b3144bdf6a5de2c858e44c33ede0fc7b951f96f879507c16b4d9a`
     - `resources`: 1 CPU, 8 GB memory, 01:00:00 walltime, Queue `entry_imfdfkmq`

3. **Two-Job Staged Batch Strategy**:
   - **Verification Batch (Pair 1)**: `M2REF_ONEEL_FRACFIX_VERIFY`, `M2REF_H0_FRACFIX_REPRO`
   - **Production Batch (Pair 2)**: `M2REF_H1_FRACFIX`, `M2REF_H2_FRACFIX`
   - Maximum concurrent running jobs: 2

## Current HPC Authority Boundary
- `authorization_ready_for_verification_batch = true`
- `execution_authorized = false`
- `submission_approved = false`
- `maximum_jobs_now = 0`
- `qsub_called = false`
- `HPC_submissions = 0`
