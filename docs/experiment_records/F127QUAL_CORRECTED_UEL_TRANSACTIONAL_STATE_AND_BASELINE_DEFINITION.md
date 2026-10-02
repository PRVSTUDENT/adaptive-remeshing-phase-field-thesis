# Qualification Report: F127QUAL Transactional UEL & Baseline Definition

- **Task ID**: `F127QUAL-M2-CORRECTED-UEL-TRANSACTIONAL-STATE-AND-BASELINE-DEFINITION1`
- **Date**: 2026-08-15
- **Agent**: `gemini-antigravity`
- **New Candidate UEL**: [`models/generated/mode_ii/production_control_batch/f42_mixed_uel_transactional.for`](file:///D:/Master%20thesis/Adaptive%20remeshing/models/generated/mode_ii/production_control_batch/f42_mixed_uel_transactional.for)
- **New Candidate SHA256**: `e3b373253069f9b36085ee426568ce002a7f195a4d5356c6c6a5549c97767138`
- **Superceded Candidate**: `f42_mixed_uel_corrected.for` (`6e4745484aa405374be2ef64d7df3f486518bc25ef14dca21e25e3d74c0c1b7e`)

---

## 1. Line-by-Line Implementation Verification of F126 Candidate

| Feature | F126 Status | F127 Transactional Candidate Status |
| :--- | :--- | :--- |
| **Undegraded $\psi_+$ Calculation** | `IMPLEMENTED` | `IMPLEMENTED` |
| **Degraded Stress / Tangent** | `IMPLEMENTED` | `IMPLEMENTED` |
| **Committed / Trial History Storage** | `NOT_IMPLEMENTED` | **`IMPLEMENTED`** (`SV_H_COMMITTED` / `SV_H_TRIAL`) |
| **Committed / Trial Phase Storage** | `NOT_IMPLEMENTED` | **`IMPLEMENTED`** (`SV_PHASE_COMMITTED` / `SV_PHASE_TRIAL`) |
| **Increment-Start Synchronization** | `NOT_IMPLEMENTED` | **`IMPLEMENTED`** (`UEXTERNALDB` `LOP=1`) |
| **Increment-Accept Commit** | `NOT_IMPLEMENTED` | **`IMPLEMENTED`** (`UEXTERNALDB` `LOP=2`) |
| **Cutback / Rejection Rollback** | `NOT_IMPLEMENTED` | **`IMPLEMENTED`** (`UEXTERNALDB` `LOP=1` auto-restore) |
| **`UEXTERNALDB` Abaqus Callback** | `NOT_IMPLEMENTED` | **`IMPLEMENTED`** |
| **Call-Order Independent Comm.** | `TEST_ONLY` | **`IMPLEMENTED`** |

---

## 2. Abaqus 2023 Qualification Run (`QUAL_TINY_4ELEM`)

A tiny 4-element non-production qualification package was built and executed in Abaqus 2023 on the cluster:

- `abaqus_compile` = **`PASS`** (Compiled with `ifort` and linked cleanly with 0 errors).
- `abaqus_datacheck` = **`PASS`** (Input file processor and datacheck passed with 0 errors).
- `tiny_execution` = **`PASS`** (`Abaqus JOB QUAL_TINY_4ELEM COMPLETED` cleanly).
- `call_order_independence_runtime` = **`PASS`**.
- `rollback_recovery_runtime` = **`PASS`** (Increment trial-restore verified via `UEXTERNALDB` `LOP=1`).

---

## 3. Verified Mesh Identities & Element Count Correction

| Model / Deck | Topology | Physical Element Count | Status / Correction |
| :--- | :--- | :--- | :--- |
| **H1 Full (`1389351`)** | H1 Uniform Reference | **12,064** | Verified |
| **H2 Full (`1389352`)** | H2 Uniform Reference | **33,852** | **Corrected from errant 9,612** |
| **PK10R1 (`1389677`)** | PK10R1 Control | **9,612** | Verified |

---

## 4. Proposed Next Virgin Production Batch Specifications (Unsubmitted)

### Job 1: `M2CORR_H2_FULL_U050`
- **Topology**: Exact H2 Uniform Reference (`M2REF_H2_FULL_U050`, 33,852 physical elements)
- **Initial State**: Virgin state ($d=0, H=0$)
- **Displacement**: $U_1: 0 \to 0.050000\text{ mm}$
- **UEL Subroutine**: `f42_mixed_uel_transactional.for` (`e3b373253069f9b36085ee426568ce002a7f195a4d5356c6c6a5549c97767138`)
- **Resources**: `1 CPU / 16 GB / 24:00:00 / entry_imfdfkmq`
- **Dependencies**: None.

### Job 2: `M2CORR_PK10R1_CONTINUOUS_U050`
- **Topology**: Exact PK10R1 Control Topology (`PK10R1_CONTINUOUS_U050`, 9,612 physical elements)
- **Initial State**: Virgin state ($d=0, H=0$)
- **Displacement**: $U_1: 0 \to 0.050000\text{ mm}$
- **UEL Subroutine**: `f42_mixed_uel_transactional.for` (`e3b373253069f9b36085ee426568ce002a7f195a4d5356c6c6a5549c97767138`)
- **Resources**: `1 CPU / 16 GB / 24:00:00 / entry_imfdfkmq`
- **Dependencies**: None.
