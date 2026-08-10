# Project Current State

# Current Project State - Stage C Reference Baseline Verification

**Active Task**: `F43MODEREF11-PAIR2-ANCHORRECOVERY1`
**Date**: 2026-08-10
**Active Agent**: `gemini-antigravity`
**Task Status**: `complete_pass`

---

## 1. Recovered Immutable Lineage & Qualified Pair-2 Jobs (M2REF_H1_FRACFIX & M2REF_H2_FRACFIX)

- **Preparation Tag P**: `P43MODEREF11-FINAL1` (`9f3d66afbe30af00685590f31f4f6ec5792e35d6`)
- **Qualification Tag Q**: `Q43MODEREF11-FINAL1` (`abd9ab5a651e38ffeb925c53bba1b861a51eff1a`)
- **Historical Governance Deviations Recorded**:
  - `P43MODEREF10_FINAL1_authorization_anchor_valid`: `false` (moved via `git tag -f` after creation)
  - `Q43MODEREF10_FINAL1_authorization_anchor_valid`: `false` (certified non-immutable preparation SHA)
  - `protocol_deviation_preparation_tag_moved_and_force_pushed`: `true`
  - `previous_final_P_exact_qualification_proven`: `false`
  - `previous_qualification_cleanup_commands_used`: `true`
- **Current P11/Q11 Qualification Status**:
  - `fresh_isolated_worktree`: `true` (`/home/pr21vyci/projects/qual_worktree_p11_final1`)
  - `pretest_status_empty`: `true`
  - `authoritative_unit_tests`: 624/624 `PASS` (0 failures, 0 errors, 0 skips)
  - `natural_status_empty`: `true`
  - `qualification_cleanup_commands_used`: `false`
  - `H1_execution_bytes_unchanged_P_to_Q`: `true`
  - `H2_execution_bytes_unchanged_P_to_Q`: `true`
- **Preflight Classification**:
  - `pair2_package_preflight_without_authorization`: `PASS`
  - `pair2_submission_preflight`: `BLOCKED_no_direct_human_authorization`
- **Prepared Jobs**:
  1. `M2REF_H1_FRACFIX`: NPHYS = 12064, 1 CPU, 8 GB, 02:00:00 walltime, queue `entry_imfdfkmq`
  2. `M2REF_H2_FRACFIX`: NPHYS = 33852, 1 CPU, 8 GB, 04:00:00 walltime, queue `entry_imfdfkmq`
- **Notification Contract**: Explicit `#PBS -m abe` and exact 2 approved recipients
- **Readiness Flags**:
  - `H0_scoped_scientific_result`: `provisional_PASS_on_available_H0_reproduction_gates`
  - `scientifically_ready_for_pair2`: `true`
  - `authorization_ready_for_pair2`: `true`
  - `execution_authorized`: `false`
  - `submission_approved`: `false`
  - `maximum_jobs_now`: `0`
  - `HPC_submissions`: `0`
- **Execution Hashes**:
  - Input: `e86ad4b439fb93d2a43d3100e19911ed0f2df3ac25dcbe584a3b549830069268`
  - UEL: `0bc4378179a35acd9954d20d3e07517f8e1c356ae07a23c40e7715cd7b56dce8`
  - PBS: `a1af3bc73828e0184fdb272ff2d50985bc00593bb0d905835e81e609e6a5e49b`
  - Wrapper: `f54d9261b7087c16f25533a324d3f4e58e61c4a81700b4bc1fafd947a692e331`
  - Manifest: `44fadd1c882a15a60facffa20202cdb35bca7b316434a6a582d3810b7ad70fdb`

---

## 2. Current Authority Boundary

- `execution_authorized = false` (Submitted job `1386372.mmaster02` in progress; authority consumed)
- `submission_approved = false`
- `maximum_jobs_now = 0`
- `qsub_called = true` (1 submission consumed)
- `HPC_submissions = 1`
- `H1_status = blocked_pending_corrected_H0_scientific_PASS`
- `H2_status = blocked_pending_corrected_H0_scientific_PASS`
