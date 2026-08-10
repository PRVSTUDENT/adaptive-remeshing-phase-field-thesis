# Current Project State - Stage C Reference Baseline Verification

**Active Task**: `F43MODEREF8-QUALRECOVERY2`
**Date**: 2026-08-10
**Active Agent**: `gemini-antigravity`
**Task Status**: `lineage_prepared_and_qualified_awaiting_human_authorization`

---

## 1. Lineage & Qualification Status

- **Preparation Tag P**: `P43MODEREF8-FINAL2` at commit `097c930263673f8a42fdb70aa3eeb5f2fca25e24`
  - Tag Object SHA: `8e5721d3e811c798ce8cbdbbeffef5aed1a24d55`
  - Remote Tag Object SHA: `8e5721d3e811c798ce8cbdbbeffef5aed1a24d55`
- **Qualification Tag Q**: `Q43MODEREF8-FINAL2` (to be tagged at qualification closeout commit)
- **Qualification Environment**:
  - Fresh isolated worktree: `/home/pr21vyci/projects/qual_worktree_p8_final2`
  - Pre-test status: 100% EMPTY (`pretest_status_empty = true`)
  - Toolchain: `gcc/11.4.0`, `intel/2024.2.0`, `abaqus/2023`, `python/gcc/11.4.0/3.11.7` (`Python 3.11.7`)
  - Full Unit Suite: 621 tests ran, 0 errors, 0 failures (`full_test_rc = 0`).
  - Focused NPHYS Contract Validator: PASS (`corrected_H0_mapping_validator = PASS`, `H1 = PASS`, `H2 = PASS`).
  - Natural Cleanliness: 100% EMPTY (`natural_status_empty = true`, `git_diff_exit_code = 0`, `git_diff_cached_exit_code = 0`).
  - Qualification cleanup commands used: `false`.

---

## 2. Governance Deviation & Lineage Records

- **P8/Q8 FINAL1 Historical Status**:
  - `P43MODEREF8_FINAL1_execution_preparation_valid = true`
  - `P43MODEREF8_FINAL1_authoritative_exact_P_qualification_valid = false` (qualification runner was modified post-P)
  - `Q43MODEREF8_FINAL1_authoritative_qualification_anchor_valid = false` (Q tag created prior to qualification completion)
  - Historical tags `P43MODEREF8-FINAL1` and `Q43MODEREF8-FINAL1` preserved unchanged.
- **Repository Cleanup Deviation Recorded**:
  - `protocol_deviation_repository_cleanup_during_qualification_workflow` recorded for prior workflow invocation of `git checkout -- models/generated/mode_ii/` and `git checkout -- .`.

---

## 3. Execution Hashes Verification

All corrected H0/H1/H2 execution bytes match frozen targets 100%:
- **H0**: input `e86ad4b439fb93d2a43d3100e19911ed0f2df3ac25dcbe584a3b549830069268`, UEL `0bc4378179a35acd9954d20d3e07517f8e1c356ae07a23c40e7715cd7b56dce8`, PBS `a1af3bc73828e0184fdb272ff2d50985bc00593bb0d905835e81e609e6a5e49b`, wrapper `f54d9261b7087c16f25533a324d3f4e58e61c4a81700b4bc1fafd947a692e331`, manifest `44fadd1c882a15a60facffa20202cdb35bca7b316434a6a582d3810b7ad70fdb`.
- **H1**: input `94fda0134500b6ebadd7ae869f2c8909454b4112c6951b930c89ca02da907281`, UEL `0bc4378179a35acd9954d20d3e07517f8e1c356ae07a23c40e7715cd7b56dce8`, PBS `273e06fbff87d6a521fb9aeab87f120070040d85109624171c7fa7cac01b5fd5`, wrapper `9a39efa92a3de74d24381beab3cad3fb1125b2f7db50a6a52db59bc413ca9f80`, manifest `4b6e81203909a2837031de39c5a882019dce8e04336c0a7650acb5d4e9c3b27c`.
- **H2**: input `c3119217eb57662289971ad814c1f6c0020b15a4c10da170da91d990e774586a`, UEL `0bc4378179a35acd9954d20d3e07517f8e1c356ae07a23c40e7715cd7b56dce8`, PBS `bed6926f473d185c2dfe9d55c57c4a7d0d7cb2ef1e9a8a9ff220508f4bd2e879`, wrapper `b7592b020b4758ec1c68f07674b1980af392493c6d297eace9fcd1cfd7a5143b`, manifest `4b6e81203909a2837031de39c5a882019dce8e04336c0a7650acb5d4e9c3b27c`.

---

## 4. Current Authority & Next Scientific Job

- `authorization_ready_for_corrected_H0 = true`
- `future_verification_jobs = ["M2REF_H0_NPHYSFIX_REPRO"]`
- `planned_future_submissions = 1`
- `maximum_running_jobs = 2`
- `H1_status = blocked_pending_corrected_H0_scientific_PASS`
- `H2_status = blocked_pending_corrected_H0_scientific_PASS`
- `execution_authorized = false`
- `submission_approved = false`
- `maximum_jobs_now = 0`
- `qsub_called = false` (No Abaqus/PBS submissions permitted without fresh explicit human authorization)
