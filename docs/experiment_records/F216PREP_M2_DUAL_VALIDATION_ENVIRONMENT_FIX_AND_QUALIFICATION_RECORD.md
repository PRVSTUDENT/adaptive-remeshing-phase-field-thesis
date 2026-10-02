# Mode-II Dual Validation Environment Fix & Qualification Record

**Task ID**: `F216PREP-M2-DUAL-VALIDATION-ENVIRONMENT-FIX-AND-QUALIFICATION1`  
**Date**: 17 August 2026  
**Status**: `LAUNCHERS CORRECTED / COMPILATION QUALIFIED (EXIT 0) / ZERO SCIENTIFIC BYTES CHANGED / READY FOR FRESH AUTHORIZATION / GATES PRESERVED`  
**Active Agent**: `gemini-antigravity`  

---

## 1. Executive Summary

Following the infrastructure compiler failure observed in PBS jobs `1390037.mmaster02` and `1390038.mmaster02` (`MODULE_COMPILER_FAILURE`), technically corrected replacement packages were prepared without submitting any jobs.

### Key Actions & Results
1. **Root Cause Isolation**:
   - Intel 2024 Fortran compiler (`ifort` classic) on the HPC compute nodes requires `gcc` in `$PATH` to resolve GNU C runtime/linker header paths.
   - Identified that `module load gcc/11.4.0` directly satisfies this prerequisite.
2. **Offline Qualification Smoke Test (Exit Code 0)**:
   - Evaluated `abaqus make library=...` under `module load gcc/11.4.0 intel/2024.2.0 abaqus/2023` on the cluster.
   - Both `f44_mixed_uel_restart_stateinit.for` (R7) and `f42_mixed_uel.for` (PK10R2) compiled and linked cleanly into shared objects `libstandardU.so` without error.
3. **Scientific Package Invariance**:
   - Zero scientific bytes were altered: INPs, UEL source code, include boundary cards, and binary state files have 100% identical SHA256 hashes.
   - Only batch launcher scripts (`submit_job.sh` / `submit_job.pbs`) were modified.
4. **Readiness**:
   - Both replacement candidates are **`READY_FOR_FRESH_AUTHORIZATION`**.

---

## 2. Artifact Comparison & Cryptographic Hash Audit

### Job 1: Same-Mesh Restart Validation (Revision R7)
- **Replacement Job Name**: `M2CORR_PK10R1_SAMEMESH_RESTART_VALIDATION_R7`
- **Failed Predecessor ID**: `1390037.mmaster02` (`MODULE_COMPILER_FAILURE`)
- **Status**: `READY_FOR_FRESH_AUTHORIZATION`

| Artifact | File Path | Status | SHA256 Hash |
| :--- | :--- | :--- | :--- |
| **Input Deck** | `.../M2CORR_PK10R1_SAMEMESH_RESTART_VALIDATION_R7.inp` | **Unchanged** | `d20edf3a13f024b4ccb981dd86ec82fd7e91ba611451694b9cf313d0affcf750` |
| **UEL Subroutine** | `.../f44_mixed_uel_restart_stateinit.for` | **Unchanged** | `de8326dfd28e66a82ba38496ee63869b86b5959e2cc35b010ebb28ae1dec6438` |
| **State Include** | `.../PK10R1_INC29_PRIMARY_STATE_BOUNDARY.inp` | **Unchanged** | `9bd16f9a27cf7c7aa398af31f7e3c754bfab5e9ecf2825fd835dbd1340bd51e5` |
| **U3 Include** | `.../PK10R1_INC29_U3_ONLY_BOUNDARY.inp` | **Unchanged** | `f54e4fefb92308ec302322cf4183cfa62ae5f89eeb37f1d8727034ea1ce167b8` |
| **Reconstructed Binary** | `.../PK10R1_INC29_COMMITTED_STATE_REPLAY_RECONSTRUCTED.bin` | **Unchanged** | `9ad133d73332fa24e4c35eab9d49505d30232d30ff5b9f49372d361f833cccea` |
| **Old Launcher** | `.../submit_job.sh` (Failed) | Superseded | `36e5f0080dc8b947f384bb793f2a2251fb102c1b53cabf2cc22cb4601f89b827` |
| **New Launcher** | `.../submit_job.sh` (Corrected) | **Updated** | `ba75bbe2a4f3b6ced22f872d3264e8750eae8304b8d9852b164ac1c300944440` |

### Job 2: Corrected Topology Validation (Revision R2)
- **Replacement Job Name**: `M2CORR_PK10R2_TOPOLOGY_CORRECTED`
- **Failed Predecessor ID**: `1390038.mmaster02` (`MODULE_COMPILER_FAILURE`)
- **Status**: `READY_FOR_FRESH_AUTHORIZATION`

| Artifact | File Path | Status | SHA256 Hash |
| :--- | :--- | :--- | :--- |
| **Input Deck** | `.../M2CORR_PK10R2_TOPOLOGY_CORRECTED.inp` | **Unchanged** | `667897fc42ee134be434cb5bc543796ce47ffd2024ec4d6c01d20e0abbd987be` |
| **UEL Subroutine** | `.../f42_mixed_uel.for` | **Unchanged** | `e0865b5eba43c14d21a733e72717e157d65c778319e6556e5eca8ab222364e58` |
| **Old Launcher** | `.../submit_job.sh` (Failed) | Superseded | `3532540a3c56c5e2a1baaf43d46c33ec71fc31f76dffde5eb9c7602291bffea4` |
| **New Launcher** | `.../submit_job.sh` (Corrected) | **Updated** | `c0dc769e9a21488e8dd9b6e315ac7a5b9b1ba0ee684dd32a4633798940c14ed3` |

---

## 3. Preserved Execution Configuration

- **Requested Resources**: 1 CPU (`nodes=1:ppn=1`), 16 GB RAM (`mem=16gb`), 24:00:00 walltime
- **Target Queue**: `entry_imfdfkmq`
- **PBS Email Notifications**: `#PBS -m abe` and `#PBS -M Pruthviraja.Reddy-Vandavagali@student.tu-freiberg.de,pr21vyci@mailserver.tu-freiberg.de`
- **Telegram Webhook**: Maintained in cluster notification wrappers.

---

## 4. Scientific Governance & Preserved Invariants

- `same_mesh_restart_validation` = `PARTIALLY_VALIDATED`
- `history_transfer_rule_resolved` = `false`
- `selected_production_history_operator` = `UNRESOLVED`
- `nonmatching_transfer_algorithm_scientifically_unblocked` = `false`
- `production_adaptive_accuracy_validation_scientifically_unblocked` = `false`
- `PK10R1_topology_repair_required` = `true`
- `fresh_human_authorization_required` = `true`
- `new_submission_authorized` = `false`
- `qsub_called` = `false`, `qdel_called` = `false`, `qmove_called` = `false`
- `git_commit_called` = `false`, `git_push_called` = `false`
