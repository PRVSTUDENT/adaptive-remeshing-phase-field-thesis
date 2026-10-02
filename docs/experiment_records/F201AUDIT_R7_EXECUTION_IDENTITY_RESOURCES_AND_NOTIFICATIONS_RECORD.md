# Mode-II R7 Execution Identity, Resources, and Notifications Audit Record

**Task ID**: `F201AUDIT-M2-R7-EXECUTION-IDENTITY-RESOURCES-AND-NOTIFICATIONS1`  
**Date**: 16 August 2026  
**Status**: `AUDIT COMPLETED / LAUNCHER REPAIRED / NOTIFICATION GATE VERIFIED / ZERO SCIENTIFIC DRIFT`  
**Active Agent**: `gemini-antigravity`  

---

## 1. Executive Summary

This record resolves the technical launcher drift between temporary defaults (4h/batch) and the governing project resource specification (24h/16GB/entry_imfdfkmq), audits PBS email and Telegram notification configurations, repairs `submit_job.sh` in the R7 package, and confirms machine-precision invariance of all scientific file hashes.

---

## 2. Resource Specification Audit & Launcher Drift Resolution

| Field | R6 Qualified Value | R7 Unrepaired Value | Governing Project Value | Difference Classification |
| :--- | :--- | :--- | :--- | :--- |
| **Requested Queue** | `entry_imfdfkmq` | `batch` | `entry_imfdfkmq` | **`TECHNICAL_LAUNCHER_DRIFT`** (Repaired) |
| **CPUs** | `nodes=1:ppn=1` | `nodes=1:ppn=1` | `nodes=1:ppn=1` | **`UNCHANGED`** |
| **Memory** | `16gb` | Unspecified | `16gb` | **`TECHNICAL_LAUNCHER_DRIFT`** (Repaired) |
| **Walltime** | `24:00:00` | `04:00:00` | `24:00:00` | **`TECHNICAL_LAUNCHER_DRIFT`** (Repaired) |
| **Email Directives** | `#PBS -m abe`, `#PBS -M ...` | None | `#PBS -m abe`, `#PBS -M ...` | **`TECHNICAL_LAUNCHER_DRIFT`** (Repaired) |
| **Abaqus Version** | `abaqus/2023` | `abaqus/2023` | `abaqus/2023` | **`UNCHANGED`** |
| **Compiler Module**| `intel/2024.2.0` | `intel/2024.2.0` | `intel/2024.2.0` | **`UNCHANGED`** |
| **Execution Mode** | Batch (Single Job) | Batch (Single Job) | Batch (Single Job) | **`UNCHANGED`** |

---

## 3. PBS Email & Telegram Notification Configuration Audit

- **PBS Email Notification**:
  - `pbs_email_notification_configured` = `true`
  - `pbs_email_events` = `abe` (Abort, Begin, End)
  - `pbs_email_recipient_configured` = `true` (`Pruthviraja.Reddy-Vandavagali@student.tu-freiberg.de,pr21vyci@mailserver.tu-freiberg.de`)
- **Telegram Notification Integration**:
  - `telegram_notification_mechanism_found` = `true` (`scripts/hpc/telegram_notify.py` / `scripts/hpc/notify_hpc_event.py`)
  - `telegram_notification_configured` = `true` (`~/.config/adaptive-remeshing/notifications.env` and `notifications.json` confirmed on cluster)
  - `notification_pre_submission_gate_ready` = `true`

---

## 4. Frozen Scientific & Launcher Hashes Post-Repair

- **Input Deck (`M2CORR_PK10R1_SAMEMESH_RESTART_VALIDATION_R7.inp`)**:
  `d20edf3a13f024b4ccb981dd86ec82fd7e91ba611451694b9cf313d0affcf750` (**100% UNCHANGED**)
- **User Subroutine (`f44_mixed_uel_restart_stateinit.for`)**:
  `de8326dfd28e66a82ba38496ee63869b86b5959e2cc35b010ebb28ae1dec6438` (**100% UNCHANGED**)
- **State-Install Boundary Include (`PK10R1_INC29_PRIMARY_STATE_BOUNDARY.inp`)**:
  `9bd16f9a27cf7c7aa398af31f7e3c754bfab5e9ecf2825fd835dbd1340bd51e5` (**100% UNCHANGED**)
- **U3-Only Boundary Include (`PK10R1_INC29_U3_ONLY_BOUNDARY.inp`)**:
  `f54e4fefb92308ec302322cf4183cfa62ae5f89eeb37f1d8727034ea1ce167b8` (**100% UNCHANGED**)
- **Canonical Primary CSV (`PK10R1_INC29_PRIMARY_STATE_REPLAY_R1.csv`)**:
  `5a2313e1ed15834d933e7cd12808681bd554394ad64d58419ad85f6f2bf6cf69` (**100% UNCHANGED**)
- **Reconstructed Committed Binary (`PK10R1_INC29_COMMITTED_STATE_REPLAY_RECONSTRUCTED.bin`)**:
  `9ad133d73332fa24e4c35eab9d49505d30232d30ff5b9f49372d361f833cccea` (**100% UNCHANGED**)
- **Repaired Launcher (`submit_job.sh`)**:
  `36e5f0080dc8b947f384bb793f2a2251fb102c1b53cabf2cc22cb4601f89b827` (Repaired to governing 24h/16GB/entry_imfdfkmq/abe)
