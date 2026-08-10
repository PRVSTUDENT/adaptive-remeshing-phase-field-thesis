# Project Current State

# Current Project State - Stage C Reference Baseline Verification

**Active Task**: `F43MODEREF10-PAIR2-PREP1`
**Date**: 2026-08-10
**Active Agent**: `gemini-antigravity`
**Task Status**: `complete_pass`

---

## 1. Prepared & Qualified Pair-2 Jobs (M2REF_H1_FRACFIX & M2REF_H2_FRACFIX)

- **Preparation Tag P**: `P43MODEREF10-FINAL1` (`888a780bbd978a3c8e4ce2ee2e5ddb015112fa52`)
- **Qualification Tag Q**: `Q43MODEREF10-FINAL1` (`ffdb59a06a3666ac3270a6fc97b7ef106c9d67b6`)
- **Prepared Jobs**:
  1. `M2REF_H1_FRACFIX`: NPHYS = 12064, 1 CPU, 8 GB, 02:00:00 walltime, queue `entry_imfdfkmq`
  2. `M2REF_H2_FRACFIX`: NPHYS = 33852, 1 CPU, 8 GB, 04:00:00 walltime, queue `entry_imfdfkmq`
- **Notification Contract**: Explicit `#PBS -m abe` and exact 2 approved recipients (`Pruthviraja.Reddy-Vandavagali@student.tu-freiberg.de`, `pr21vyci@mailserver.tu-freiberg.de`)
- **Raw Execution Hashes**:
  - `M2REF_H1_FRACFIX`: INP `407f88694d...`, UEL `0bc4378179...`, PBS `80c1a509a6...`, SH `2d354ec6e0...`
  - `M2REF_H2_FRACFIX`: INP `c9a3f496cf...`, UEL `0bc4378179...`, PBS `f7040080f6...`, SH `dd3f85dcc6...`
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
