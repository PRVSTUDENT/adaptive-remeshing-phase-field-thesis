# Scientific Formulation & Qualification Audit Report: Task F126FIX

- **Task ID**: `F126FIX-M2-UEL-UNDEGRADED-DRIVING-ENERGY-AND-ROLLBACK-SAFE-STATE-QUAL1`
- **Date**: 2026-08-15
- **Agent**: `gemini-antigravity`
- **Candidate Corrected UEL**: [`models/generated/mode_ii/production_control_batch/f42_mixed_uel_corrected.for`](file:///D:/Master%20thesis/Adaptive%20remeshing/models/generated/mode_ii/production_control_batch/f42_mixed_uel_corrected.for)
- **Candidate Corrected UEL SHA256**: `6e4745484aa405374be2ef64d7df3f486518bc25ef14dca21e25e3d74c0c1b7e`

---

## 1. Executive Summary & Blast Radius Audit

A comprehensive audit of all historical Mode-II UEL subroutines across the project repository was performed.

### Scientific Lineage Classification

| Job / Candidate | UEL SHA256 | $POS_M$ Driving Energy Classification | Scientific Force & Damage Curve Status |
| :--- | :--- | :--- | :--- |
| **H1 Full Reference (`1389351`)** | `e0865b5eba43` | **`DEGRADED_G_TIMES_PSI_PLUS_BUG`** | `VALID_ONLY_AS_INTERNAL_NUMERICAL_COMPARISON` |
| **H2 Full Reference (`1389352`)** | `e0865b5eba43` | **`DEGRADED_G_TIMES_PSI_PLUS_BUG`** | `VALID_ONLY_AS_INTERNAL_NUMERICAL_COMPARISON` |
| **R2R13 State Transfer (`1389325`)**| `2da998a8823f` | **`DEGRADED_G_TIMES_PSI_PLUS_BUG`** | `INVALIDATED` |
| **R2R14 Continuation (`1389328`)** | `2da998a8823f` | **`DEGRADED_G_TIMES_PSI_PLUS_BUG`** | `INVALIDATED` |
| **PK10R1 Continuous (`1389677`)** | `43aeacbfdf7b` | **`DEGRADED_G_TIMES_PSI_PLUS_BUG`** | `VALID_ONLY_AS_INTERNAL_NUMERICAL_COMPARISON` |
| **PK10R1 Identity Restart (`1389678`)**| `43aeacbfdf7b` | **`DEGRADED_G_TIMES_PSI_PLUS_BUG`** | `INVALIDATED` |
| **PK10R1 Corrected Restart (`1389680`)**| `500afe096c5c` | **`DEGRADED_G_TIMES_PSI_PLUS_BUG`** | `INVALIDATED` |

### Blast Radius Reclassification

1. **`H1/H2 Force Convergence & Peak Statements`**: Reclassified as **`VALID_ONLY_AS_INTERNAL_NUMERICAL_COMPARISON`**. (The code converged reliably and solved the system defined, but the physical driving energy was degraded by $g(d)$).
2. **`R2R13 Transferred State & R2R14 Load Drop`**: Reclassified as **`INVALIDATED`**. (The post-restart drop was driven by stale history caused by $g(d)\psi_+$ energy suppression).
3. **`Adaptive-vs-Uniform Accuracy Comparison`**: Reclassified as **`INVALIDATED`**.

---

## 2. Corrected UEL Architecture

Created candidate subroutine `f42_mixed_uel_corrected.for`:
- **Separated Elastic Constants**:
  ```fortran
  C11_0 = E_MOD*(ONE - E_NU)/((ONE + E_NU)*(ONE - TWO*E_NU))
  C12_0 = E_MOD*E_NU/((ONE + E_NU)*(ONE - TWO*E_NU))
  C33_0 = E_MOD/(TWO*(ONE + E_NU))

  C12_MECH = C12_0 * DEG
  C33_MECH = C33_0 * DEG
  ```
- **Undegraded Strain Energy Density**:
  ```fortran
  POS_M = HALF*C12_0*(E_POS**2) + C33_0*(E11**2 + E22**2 + TWO*(E12**2))
  ```
- Mechanical stresses and tangents continue to use `C12_MECH` and `C33_MECH` (strictly degraded by `DEG`).

---

## 3. Recommended Next Production Batch Plan (Unsubmitted)

The minimum scientifically necessary next production batch consists of **2 independent virgin baseline jobs** using the corrected UEL formulation:

### Job 1: `M2CORR_H2_FULL_U050`
- **Purpose**: Establish a clean, un-degraded driving energy uniform H2 reference baseline ($h=0.0075\text{ mm}$, $9,612$ elements).
- **UEL**: `f42_mixed_uel_corrected.for` (`6e4745484aa405374be2ef64d7df3f486518bc25ef14dca21e25e3d74c0c1b7e`)
- **Resources**: `1 CPU / 16 GB / 24:00:00 / entry_imfdfkmq`
- **Dependencies**: None.

### Job 2: `M2CORR_PK10R1_CONTINUOUS_U050`
- **Purpose**: Establish a clean, un-degraded driving energy continuous control baseline on PK10R1 mesh topology ($9,612$ elements) from $U_1=0.000$ to $0.050\text{ mm}$ without restart or state transfer.
- **UEL**: `f42_mixed_uel_corrected.for` (`6e4745484aa405374be2ef64d7df3f486518bc25ef14dca21e25e3d74c0c1b7e`)
- **Resources**: `1 CPU / 16 GB / 24:00:00 / entry_imfdfkmq`
- **Dependencies**: None.
