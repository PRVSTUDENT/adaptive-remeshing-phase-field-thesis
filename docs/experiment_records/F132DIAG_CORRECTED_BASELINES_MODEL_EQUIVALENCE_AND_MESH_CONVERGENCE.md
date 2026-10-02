# Diagnostic Report: F132DIAG Corrected Baselines Model-Equivalence & Mesh Convergence Audit

- **Task ID**: `F132DIAG-M2-CORRECTED-H2-VS-PK10R1-MODEL-EQUIVALENCE-AND-MESH-CONVERGENCE1`
- **Date**: 2026-08-15
- **Agent**: `gemini-antigravity`
- **Evaluated Baseline Jobs**:
  - `M2CORR_H2_FULL_U050` (`1389685.mmaster02`, H2 topology, 33,852 physical elements)
  - `M2CORR_PK10R1_CONTINUOUS_U050` (`1389684.mmaster02`, PK10R1 topology, 9,612 physical elements)

---

## 1. Executive Summary & Root Cause Findings

The diagnostic audit uncovered a **major structural model mismatch** between `M2CORR_H2_FULL_U050` (`1389685.mmaster02`) and `M2CORR_PK10R1_CONTINUOUS_U050` (`1389684.mmaster02`):

1. **Top Boundary Condition $U_2$ Mismatch**:
   - In H2 (`1389685.mmaster02`), `top_nodes, 2, 2` ($U_2 = 0.0$) is fixed under `*Boundary`, constraining vertical displacement on the top boundary and creating a fully constrained shear box.
   - In PK10R1 (`1389684.mmaster02`), $U_2$ on `N_TOP` is **unconstrained**, allowing the top edge to expand/contract vertically in $Y$.
   - **Pre-Damage Elastic Stiffness Mismatch**: This BC mismatch causes a **`65.21%` relative stiffness mismatch** in initial linear elastic response ($1839.10\text{ kN/mm}$ for H2 vs $639.80\text{ kN/mm}$ for PK10R1) BEFORE ANY DAMAGE OCCURS ($d=0$).
   - Therefore, the $51\%$ peak force difference between H2 ($0.7830\text{ kN}$) and PK10R1 ($0.3832\text{ kN}$) is **primarily driven by boundary condition mismatch**, NOT merely spatial mesh resolution!

2. **Resolution of Mesh Metrics & Historical Claims**:
   - **H2 Actual Mesh Metrics**: $h_{\min} = \mathbf{0.001000\text{ mm}}$ ($1.0\ \mu\text{m}$ at notch tip), notch region median $h = \mathbf{0.001000\text{ mm}}$ (1,476 elements within $1l_0$). Claims of H2 $h=0.0075\text{ mm}$ or $0.0025\text{ mm}$ are **`NOT_SUPPORTED`**.
   - **PK10R1 Actual Mesh Metrics**: $h_{\min} = \mathbf{0.005000\text{ mm}}$ ($5.0\ \mu\text{m}$ at notch tip), notch region median $h = \mathbf{0.012917\text{ mm}}$ (8 elements within $1l_0$). Claims of PK10R1 $h_{\min}=0.001\text{ mm}$ are **`NOT_SUPPORTED`**.
   - PK10R1 is non-uniform graded, though near the notch tip PK10R1 is $5\times$ coarser in $h_{\min}$ and has 8 elements vs H2's 1,476 elements.

3. **Inert Dummy UMAT Verification**:
   - `SUBROUTINE UMAT` returns zero stress and zero stiffness (`STRESS=0`, `DDSDDE=0`) for passive CPE4 elements. `passive_layer_RF1_fraction` = **`0.000000`**.

4. **Corrected H1 Baseline Requirement & Restart Status**:
   - `corrected_H1_required_for_uniform_convergence` = **`true`** (To establish true spatial mesh convergence under $POS_M = \psi_+$ on uniform meshes with aligned BCs).
   - `restart_validation_scientifically_unblocked` = **`false`** (Blocked until BC alignment).

---

## 2. Matched Region Mesh Table

| Region | H2 $h_{\min}$ (mm) | H2 $h_{\text{median}}$ (mm) | PK10 $h_{\min}$ (mm) | PK10 $h_{\text{median}}$ (mm) | H2 Elements | PK10 Elements |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **$1l_0$ ($r \le 0.015\text{ mm}$)** | **0.001000** | **0.001000** | **0.005000** | **0.012917** | 1,476 | 8 |
| **$2l_0$ ($r \le 0.030\text{ mm}$)** | **0.001000** | **0.001000** | **0.005000** | **0.012917** | 3,420 | 32 |
| **$5l_0$ ($r \le 0.075\text{ mm}$)** | **0.001000** | **0.001625** | **0.005000** | **0.012917** | 8,208 | 328 |
