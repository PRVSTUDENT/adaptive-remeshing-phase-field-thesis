# Mode-II Final Dual Authorization Package Preparation Record (R7 / PK10R2)

**Task ID**: `F202PREP-M2-R7-PK10R2-FINAL-DUAL-AUTHORIZATION-PACKAGE1`  
**Date**: 16 August 2026  
**Status**: `PACKAGE PREPARED / FROZEN / READY_FOR_HUMAN_AUTHORIZATION / NO_JOBS_SUBMITTED`  
**Active Agent**: `gemini-antigravity`  

---

## 1. Executive Summary

This record completes the final offline human-authorization package `M2_DUAL_VALIDATION_BATCH_R7_PK10R2`, replacing superseded revision `R6` with qualified revision `R7`. All manifest, launcher, input deck, and subroutine hashes are frozen across both jobs. The jobs are proven to be scientifically independent and compliant with batch HPC policies.

---

## 2. Frozen Dual Batch Package Identity

### Batch Specification
- **Batch Name**: `M2_DUAL_VALIDATION_BATCH_R7_PK10R2`
- **Job 1**: `M2CORR_PK10R1_SAMEMESH_RESTART_VALIDATION_R7`
- **Job 2**: `M2CORR_PK10R2_TOPOLOGY_CORRECTED`
- **Jobs Scientifically Independent**: `true`
- **Batch Submission Scientifically Permissible**: `true`
- **Maximum Total Submissions**: 2
- **Maximum Simultaneous Running Jobs**: 2
- **Automatic Retry**: `false`

### Complete Frozen Hash Inventory
| Job | Component | Path | SHA256 |
| :--- | :--- | :--- | :--- |
| **R7** | Input Deck | `models/.../M2CORR_PK10R1_SAMEMESH_RESTART_VALIDATION_R7.inp` | `d20edf3a13f024b4ccb981dd86ec82fd7e91ba611451694b9cf313d0affcf750` |
| **R7** | UEL Subroutine | `models/.../f44_mixed_uel_restart_stateinit.for` | `de8326dfd28e66a82ba38496ee63869b86b5959e2cc35b010ebb28ae1dec6438` |
| **R7** | Primary Boundary | `models/.../PK10R1_INC29_PRIMARY_STATE_BOUNDARY.inp` | `9bd16f9a27cf7c7aa398af31f7e3c754bfab5e9ecf2825fd835dbd1340bd51e5` |
| **R7** | U3 Boundary | `models/.../PK10R1_INC29_U3_ONLY_BOUNDARY.inp` | `f54e4fefb92308ec302322cf4183cfa62ae5f89eeb37f1d8727034ea1ce167b8` |
| **R7** | Primary CSV | `models/.../PK10R1_INC29_PRIMARY_STATE_REPLAY_R1.csv` | `5a2313e1ed15834d933e7cd12808681bd554394ad64d58419ad85f6f2bf6cf69` |
| **R7** | Reconstructed Binary | `models/.../PK10R1_INC29_COMMITTED_STATE_REPLAY_RECONSTRUCTED.bin` | `9ad133d73332fa24e4c35eab9d49505d30232d30ff5b9f49372d361f833cccea` |
| **R7** | Launcher Script | `models/.../submit_job.sh` | `36e5f0080dc8b947f384bb793f2a2251fb102c1b53cabf2cc22cb4601f89b827` |
| **R7** | Manifest | `models/.../manifest.json` | `198a9a31c8e6f6d1c4ee6c32bbb8c01cd872352d81e1c40d7117853c3340bbf0` |
| **PK10R2** | Input Deck | `models/.../M2CORR_PK10R2_TOPOLOGY_CORRECTED.inp` | `667897fc42ee134be434cb5bc543796ce47ffd2024ec4d6c01d20e0abbd987be` |
| **PK10R2** | UEL Subroutine | `models/.../f42_mixed_uel.for` | `e0865b5eba43c14d21a733e72717e157d65c778319e6556e5eca8ab222364e58` |
| **PK10R2** | Launcher Script | `models/.../submit_job.sh` | `3532540a3c56c5e2a1baaf43d46c33ec71fc31f76dffde5eb9c7602291bffea4` |
| **PK10R2** | Manifest | `models/.../manifest.json` | `313a77015f83cf05e174216bff4e7a033173f0dc61b872e49a2d1e2cb303d043` |

---

## 3. Mandatory Notification Pre-Submission Gate

Both job packages have verified pre-submission notification gates:
- PBS Email: `#PBS -m abe`, `#PBS -M Pruthviraja.Reddy-Vandavagali@student.tu-freiberg.de,pr21vyci@mailserver.tu-freiberg.de`
- Telegram: `~/.config/adaptive-remeshing/notifications.env` verified on cluster.
