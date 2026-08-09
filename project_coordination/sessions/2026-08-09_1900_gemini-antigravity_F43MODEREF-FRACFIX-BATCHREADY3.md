# Session Report: F43MODEREF-FRACFIX-BATCHREADY3

**Date**: 2026-08-09 19:00:00 +02:00  
**Agent**: gemini-antigravity  
**Task ID**: `F43MODEREF-FRACFIX-BATCHREADY3`  
**Preparation Tag**: `P43MODEREF5-FINAL1` (`3f4f23d9fca381e1899efc6ab721ce5cf0b02411`)  
**Qualification Tag**: `Q43MODEREF5` (`926fbb5001ffae01e63a15afbf1a7008cf36eecb`)  
**Qualification Location**: `/home/pr21vyci/projects/adaptive-remeshing-worktree-p5` (Detached HEAD on `tu_freiberg`)

---

## 1. Governance & Session Claim
- `ACTIVE_SESSION.json` successfully claimed before editing (`active: true`, task `F43MODEREF-FRACFIX-BATCHREADY3`).
- Strictly enforced `execution_authorized = false`, `submission_approved = false`, `maximum_jobs_now = 0`, `qsub_called = false`. No solver jobs executed.

---

## 2. Evidence Loss Provenance Correction
- **Explicit Distinction**:
  - `unique_raw_solver_evidence_permanently_lost = true` (raw ODB/sta/dat/msg purged on HPC during workspace cleanup)
  - `derived_extracted_evidence_preserved = true` (all 10 extracted JSON/CSV files preserved in Git)
  - `pbs_scheduler_logs_preserved = true` (`1385895.mmaster02.OU` and `1385896.mmaster02.OU` preserved in home spool)
- **Governance Classification**:
  - Preserved `protocol_deviation_destructive_evidence_workspace_cleanup`.
- **Historical Jobs Classification**:
  - `1385895.mmaster02`: `scheduler_result = PASS`, `technical_result = PASS`, `scientific_result = HOLD_phase_field_result_inconsistent_with_historical_reference`
  - `1385896.mmaster02`: Same HOLD classification.

---

## 3. Final Two-Job Authorization Contract (Pair 1 Verification Batch)

### JOB 1: `M2REF_ONEEL_FRACFIX_VERIFY`
- `input_SHA256`: `0a86b66a5434e06415c1721fbf6b21ee0e38b1107803efb2836070c9f5b35512`
- `UEL_SHA256`: `0bc4378179a35acd9954d20d3e07517f8e1c356ae07a23c40e7715cd7b56dce8`
- `PBS_SHA256`: `240969e9be531f0e917619ae422ce78ae21c3c5ef889b4feb85c4477b22a24df`
- `submit_wrapper_SHA256`: `09edb59b8943f0577b96512d8a4f900bb4e04525691d6ce772cd3f95400cb99c`
- `queue`: `entry_imfdfkmq` | `ncpus`: 1 | `memory`: 8 GB | `walltime`: `00:15:00`

### JOB 2: `M2REF_H0_FRACFIX_REPRO`
- `input_SHA256`: `4bcc529509d3491bfffb28b33078f0759cb55cdac2bcabbbadb6be99a5fc08f5`
- `UEL_SHA256`: `0bc4378179a35acd9954d20d3e07517f8e1c356ae07a23c40e7715cd7b56dce8`
- `PBS_SHA256`: `9c326977bf9a9100811062b6bc367e442b83086103efe8f66d6e405fc025db65`
- `submit_wrapper_SHA256`: `16d4d2d7746b3144bdf6a5de2c858e44c33ede0fc7b951f96f879507c16b4d9a`
- `queue`: `entry_imfdfkmq` | `ncpus`: 1 | `memory`: 8 GB | `walltime`: `01:00:00`

### Notification Contract
- `notification_mail_points`: `abe` (`#PBS -m abe`)
- `notification_recipient_configuration_present`: `true`

---

## 4. Common Submission & Scientific Gate Procedure
- Fail-closed common preflight procedure frozen for Pair 1 verification batch (`M2REF_ONEEL_FRACFIX_VERIFY` and `M2REF_H0_FRACFIX_REPRO`).
- Production Pair 2 (`M2REF_H1_FRACFIX` and `M2REF_H2_FRACFIX`) remains blocked until Pair 1 passes scientifically.
