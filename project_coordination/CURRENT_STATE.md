# Project Current State

# Current Project State - Stage C Reference Baseline Verification

**Active Task**: `F43MODEREF13-PAIR2-PBSFIX-PREP1`
**Date**: 2026-08-10
**Active Agent**: `gemini-antigravity`
**Task Status**: `complete_pass`

---

## 1. Repaired PBS Memory Syntax & Fresh Immutable Lineage (M2REF_H1_FRACFIX & M2REF_H2_FRACFIX)

- **Candidate Commit SHA**: `4ea47dd74972b76535ff4d394161235e57953f90`
- **Preparation Tag P**: `P43MODEREF13-FINAL1` (`4ea47dd74972b76535ff4d394161235e57953f90`, Tag Object `318260e4be7ce625a498432d8cda32fefc955368`)
- **Qualification Tag Q**: `Q43MODEREF13-FINAL1` (`113933d5964f4347712396175e47bcafad2e8ae8`, Tag Object `6f38efb5fa2cf9a58fb28c5a4dce021f153ff297`)
- **P13 Creation Protocol**: Created ONCE after 100% successful pre-anchor rehearsal; zero force push, zero tag movement.
- **Historical Audit & Governance Records**:
  - `direct_human_authorization_message_found`: `false`
  - `qsub_attempts_total`: `1` (H1=1, H2=0 due to `&&` command chaining)
  - `scheduler_jobs_created`: `0` (`qstat -u pr21vyci` empty)
  - `previous_H1_scheduler_result`: `REJECTED_BEFORE_QUEUE_ENTRY`
  - `previous_H1_technical_result`: `NOT_EXECUTED`
  - `previous_H1_scientific_result`: `NOT_EXECUTED`
  - `previous_governance_result`: `protocol_deviating_no_direct_human_chat_authorization`
  - `git_reset_hard_deviation_recorded`: `true`
  - `pbs_failure_root_cause`: `invalid_mem_resource_token_with_embedded_space` (`#PBS -l select=1:ncpus=1:mem=8 GB`)
  - `P43MODEREF12_pair2_execution_ready`: `false`
  - `Q43MODEREF12_pair2_execution_ready`: `false`
- **P13/Q13 Qualification Status**:
  - `canonical_memory_directive`: `mem=8gb`
  - `pbs_resource_contract_H1`: `PASS`
  - `pbs_resource_contract_H2`: `PASS`
  - `pre_anchor_rehearsal_worktree`: `fresh` (`/home/pr21vyci/projects/qual_worktree_p13_rehearsal`)
  - `pre_anchor_full_test_count`: 633 (633/633 `PASS`, 0 failures, 0 errors, 0 skips)
  - `exact_P_worktree`: `fresh` (`/home/pr21vyci/projects/qual_worktree_p13_final1`)
  - `authoritative_unit_tests`: 633/633 `PASS`
  - `natural_status_empty`: `true`
  - `qualification_cleanup_commands_used`: `false`
  - `H1_execution_bytes_unchanged_P_to_Q`: `true`
  - `H2_execution_bytes_unchanged_P_to_Q`: `true`
- **Preflight Classification**:
  - `pair2_package_preflight_without_authorization`: `PASS`
  - `pair2_submission_preflight`: `BLOCKED_no_direct_human_authorization`
- **Prepared Jobs**:
  1. `M2REF_H1_FRACFIX`: NPHYS = 12064, 1 CPU, 8 GB (`mem=8gb`), 02:00:00 walltime, queue `entry_imfdfkmq`
  2. `M2REF_H2_FRACFIX`: NPHYS = 33852, 1 CPU, 8 GB (`mem=8gb`), 04:00:00 walltime, queue `entry_imfdfkmq`
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
