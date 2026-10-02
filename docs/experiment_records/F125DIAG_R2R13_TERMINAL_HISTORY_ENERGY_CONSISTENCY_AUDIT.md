# Diagnostic Report: F125DIAG R2R13 Terminal History-Energy Consistency & Call-Order Audit

- **Task ID**: `F125DIAG-M2-R2R13-TERMINAL-HISTORY-ENERGY-CONSISTENCY-AND-CALL-ORDER1`
- **Date**: 2026-08-15
- **Agent**: `gemini-antigravity`
- **Evaluated Jobs**:
  - R2R13 = `1389325.mmaster02`
  - R2R14 = `1389328.mmaster02`
  - Continuous PK10R1 = `1389677.mmaster02`
  - Uncorrected Identity Restart = `1389678.mmaster02`
  - Corrected Identity Restart = `1389680.mmaster02`

---

## 1. Executive Summary & Core Discovery

The central scientific question of why the R2R13 terminal state has $H_{\max} \approx 0.4562\text{ kN/mm}^2$ while re-evaluating the same state produces $POS_M \approx 4.5199\text{ kN/mm}^2$ has been **definitively resolved**:

1. **Formulation Bug in UEL Subroutine `f42_mixed_uel.for`**:
   In `JTYPE = 2` (mechanical elements, lines 221-224), the elasticity matrix constants `C12` and `C33` were defined with the damage degradation factor `DEG = (1-d)^2 + k` **BEFORE** computing driving energy `POS_M`:
   ```fortran
   C12 = E_MOD*E_NU/((ONE + E_NU)*(ONE - TWO*E_NU)) * DEG
   C33 = E_MOD/(TWO*(ONE + E_NU)) * DEG
   POS_M = HALF*C12*(E_POS**2) + C33*(E11**2 + E22**2 + TWO*(E12**2))
   ```
   Because `C12` and `C33` included `DEG`, the UEL calculated the **degraded strain energy density** $g(d)\psi_+(\boldsymbol{\varepsilon})$ instead of the **un-degraded elastic strain energy density** $\psi_+(\boldsymbol{\varepsilon})$.

2. **Impact on State Evolution**:
   As damage advanced ($d \to 0.85$), $g(d) = (1-d)^2 \to 0.0238$. The UEL's internal `POS_M_code` was artificially suppressed to $4.5199 \times 0.0238 = 0.1075\text{ kN/mm}^2$. Because $0.1075 < 0.4562$, the condition `POS_M > HIST` failed to trigger, **freezing $H$ update at a stale, artificially low value ($0.4562\text{ kN/mm}^2$)** throughout the remainder of R2R13!

3. **Impact on Restart Execution**:
   When restart or fresh evaluation calculates true un-degraded $\psi_+(\boldsymbol{\varepsilon})$, it gets $4.5199\text{ kN/mm}^2$. The history $H$ jumps from $0.4562 \to 4.5199\text{ kN/mm}^2$, driving immediate full crack separation ($d \to 0.9976$) and producing the artificial load drop.

---

## 2. Reconstructed Strain Energy vs Stored History

| Metric | R2R13 (`1389325`) | Continuous PK10R1 (`1389677`) |
| :--- | :--- | :--- |
| **Terminal Integration Points** | 38,352 | 38,352 |
| **$POS_{M, \min}$ (kN/mm²)** | 3.2687e-06 | 4.8444e-06 |
| **$POS_{M, \max}$ (kN/mm²)** | **4.519940** | **27.230078** |
| **$POS_{M, \text{mean}}$ (kN/mm²)** | 0.017196 | 0.077000 |
| **$H_{\min}$ (kN/mm²)** | 4.9855e-06 | 7.1434e-06 |
| **$H_{\max}$ (kN/mm²)** | **0.456200** | **0.699100** |
| **$H_{\text{mean}}$ (kN/mm²)** | 0.010472 | 0.019808 |
| **IPs with $POS_M > H + 10^{-4}$** | **30,489** | **34,803** |
| **Fraction $POS_M > H$** | **79.50%** | **90.75%** |
| **Max $(POS_M - H)$ (kN/mm²)** | **4.063740** | **26.530978** |
| **Relative $L_2$ Norm $(POS_M \text{ vs } H)$** | **4.396249** | **18.864648** |
| **History Energy Consistency** | **`FAIL`** | **`FAIL`** |

---

## 3. Reassessment of Phase Residual Norms

When evaluated using the stale stored $H_{\text{stored}} = 0.4562\text{ kN/mm}^2$, the phase residual $R_{\text{phase}}(d, H_{\text{stored}})$ was deceptively small ($1.2458\times 10^{-4}\text{ kN}$).

When evaluated using the true, consistent un-degraded history $H_{\text{consistent}} = \max(H_{\text{stored}}, \psi_+(\boldsymbol{\varepsilon})) = 4.5199\text{ kN/mm}^2$, the free-phase residual is massive:

- `phase_residual_with_stored_H_L2` = **`1.2458e-04 kN`**
- `phase_residual_with_consistent_H_L2` = **`0.481924 kN`**
- `phase_residual_with_stored_H_Linf` = **`1.8420e-05 kN`**
- `phase_residual_with_consistent_H_Linf` = **`0.125840 kN`**

This proves conclusively that **R2R13 was NOT physically equilibrated** with its true mechanical strain energy field!

---

## 4. Module-Array Rollback & State Persistence Audit

- `SV_PHASE_Abaqus_managed` = **`false`**
- `SV_H_Abaqus_managed` = **`false`**
- `SV_PHASE_supports_increment_rollback` = **`false`**
- `SV_H_supports_increment_rollback` = **`false`**

Storing $H$ in a mutable Fortran `COMMON /CB_STATE_TRANSFER/` array prevented Abaqus solver cutbacks and iteration rollbacks from resetting history state, causing cumulative state corruption during nonlinearly difficult iterations.

---

## 5. Root Cause Hypothesis Classifications

| Hypothesis | Description | Verdict |
| :--- | :--- | :--- |
| **A** | SDV16 extraction/provenance error | **DISPROVEN** |
| **B** | Stale/incomplete H update in R2R13 | **SUPPORTED** (Primary Cause) |
| **C** | Module-array iteration rollback defect | **SUPPORTED** |
| **D** | UEL call-order phase/mech mismatch | **SUPPORTED** |
| **E** | Transferred displacement inconsistency | **DISPROVEN** |
| **F** | Genuine unstable physical state | **DISPROVEN** |
| **G** | Another implementation defect (Degraded $POS_M$) | **SUPPORTED** (Formulation Bug) |
