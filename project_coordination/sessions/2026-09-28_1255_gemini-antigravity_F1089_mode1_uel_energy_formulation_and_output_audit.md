# Session Report: Mode-I Fundamentals Qualification — UEL Energy Formulation and Output Audit (Corrected)

**Session ID**: `2026-09-28_1255_gemini-antigravity_F1089_mode1_uel_energy_formulation_and_output_audit`  
**Task ID**: `F1089-MODE1-UEL-ENERGY-FORMULATION-AND-OUTPUT-AUDIT-20260928`  
**Agent**: `gemini-antigravity`  
**Date**: `2026-09-28T12:55:00+02:00` (Audited & Corrected 2026-09-28T12:58:00+02:00)  
**Base Commit**: `42762382e8e0f4a8fc87b43eb0ddfba06028bcaf`  
**Write Scope**: `project_coordination/**`

---

## 1. Executive Summary & Objective

In accordance with the supervisor-aligned directive for the upcoming **01 October 2026 (10:00) Supervisor Meeting**, a comprehensive scientific and numerical audit of the authoritative user subroutine `f42_mixed_uel.for` was performed. The primary objective was to qualify the global UEL energy formulation, verify discrete Gauss-quadrature integration, prove non-invasive output routing through the Layer 3 companion UMAT bridge, verify bit-for-bit mechanical parity on the smallest meaningful benchmark case, and establish the discrete global energy balance identity under the governing epistemological constraint `GLOBAL_ENERGY_IDENTITY — NOT_YET_CLOSED`.

---

## 2. Source-Grounded Mathematical Weak Form & Discrete Energy Expressions

### 2.1 Staggered Dual-Element Weak Form & Active DOFs
The Mode-I formulation couples phase-field damage $d$ and mechanical displacement $\mathbf{u}$ using a staggered multi-layer architecture directly verified from source lines 10–25 and 200–550 of `f42_mixed_uel.for`:

1. **Phase-Field Subproblem (Layer 1: `JTYPE=1` quad / `JTYPE=3` tri, Active DOF 3, `NDOFEL=4` or `3`)**:
   Solves the AT2 regularized phase-field equation with project convention ($d = 0$ intact, $d \to 1$ fractured):
   $$\int_{\Omega} \left[ \frac{G_c}{l_0} d \delta d + G_c l_0 \nabla d \cdot \nabla \delta d - 2(1-d)\mathcal{H}\delta d \right] d\Omega = 0$$
   Equivalently in terms of the solver stiffness and driving load:
   $$\int_{\Omega} \left[ \left( \frac{G_c}{l_0} + 2\mathcal{H} \right) d \delta d + G_c l_0 \nabla d \cdot \nabla \delta d \right] d\Omega = \int_{\Omega} 2\mathcal{H} \delta d \, d\Omega$$
   The implemented elemental Newton residual (L330–365) is:
   $$\mathrm{RHS}_i = \int_{\Omega_e} 2\mathcal{H} N_i \, d\Omega - \sum_{j=1}^{\mathrm{NDOFEL}} K_{ij} d_j$$
   When $d = 0$ and $\mathcal{H} = 0$, $\mathrm{RHS}_i = 0$ identically (the intact state is an exact equilibrium solution).

2. **Mechanical Subproblem (Layer 2: `JTYPE=2` quad / `JTYPE=4` tri, Active DOFs 1, 2, `NDOFEL=8` or `6`)**:
   Solves the balance of linear momentum with isotropic degraded elasticity:
   $$\int_{\Omega} \boldsymbol{\sigma} : \boldsymbol{\varepsilon}(\delta\mathbf{u}) \, d\Omega - \int_{\partial\Omega_t} \bar{\mathbf{t}} \cdot \delta\mathbf{u} \, d\Gamma = 0$$
   where $\boldsymbol{\sigma} = \left[ (1-\bar{d})^2 + k \right] \mathbb{C}_0 : \boldsymbol{\varepsilon}$ with $\mathbb{C}_0$ the 2D plane-strain elasticity tensor.

3. **Driving Strain History Field $\mathcal{H}$**:
   $$\mathcal{H}(t) = \max_{\tau \in [0,t]} \psi_{\mathrm{pos}}(\boldsymbol{\varepsilon}(\tau))$$
   where $\psi_{\mathrm{pos}}(\boldsymbol{\varepsilon})$ is the undegraded trace-positive driving energy density (L518–519):
   $$\psi_{\mathrm{pos}}(\boldsymbol{\varepsilon}) = \frac{1}{2}\lambda_0 \langle \mathrm{tr}(\boldsymbol{\varepsilon}) \rangle_+^2 + \mu_0 \left( \varepsilon_{11}^2 + \varepsilon_{22}^2 + 2\varepsilon_{12}^2 \right)$$
   with Lamé parameters $\lambda_0 = \frac{E\nu}{(1+\nu)(1-2\nu)}$ and $\mu_0 = \frac{E}{2(1+\nu)}$. The implementation uses this volumetric trace-positive formulation rather than a spectral eigenvalue split.

### 2.2 Discrete Gauss Quadrature Integration
Under 2D plane-strain conditions with implicit unit thickness $B = 1.0\,\text{mm}$ ($V_e = A_e \cdot B$):

* **Stored Elastic Strain Energy ($E_{\mathrm{elas}}$)**:
  $$E_{\mathrm{elas}}^{(e)} = \sum_{p=1}^{4} \left( \frac{1}{2} \boldsymbol{\varepsilon}_p : \boldsymbol{\sigma}_p \right) \cdot \det(\mathbf{J}_p) \cdot w_p \cdot B$$
  *Fortran lines*: `ENERGY(2) = E_ELAS_ELEM` (L542 quad, L809 tri); `SVARS(17) = E_ELAS_ELEM` (L558 quad, L823 tri).
* **Fracture Surface Energy ($E_{\mathrm{frac}}$)**:
  $$E_{\mathrm{frac}}^{(e)} = \sum_{p=1}^{4} G_c \left[ \frac{d_p^2}{2l_0} + \frac{l_0}{2} (\nabla d)_p \cdot (\nabla d)_p \right] \cdot \det(\mathbf{J}_p) \cdot w_p \cdot B$$
  *Fortran lines*: `ENERGY(7) = E_FRAC_ELEM` (L366 quad, L652 tri); `SVARS(17) = E_FRAC_ELEM` (L382 quad, L663 tri).
* **External Boundary Work ($W_{\mathrm{trap}}$)**:
  $$W_{\mathrm{trap}, n} = \sum_{i=1}^{n} \frac{F_i + F_{i-1}}{2} (u_i - u_{i-1})$$

---

## 3. Non-Invasive Companion UMAT Output Routing & Single-IP Extraction Rule

1. **Companion UMAT Bridge (Layer 3)**:
   Scalar whole-element quantities are passed from UEL to UMAT via `COMMON /CB_STATE_TRANS/` (L76–80, L183–187, L854–858) without modifying UEL residuals (`RHS`), tangent matrices (`AMATRX`), or constitutive history:
   - `STATEV(17) = SV_E_FRAC`: Whole-element fracture energy $E_{\mathrm{frac}}^{(e)}$ [$\text{kN}\cdot\text{mm} = \text{J}$] (L894)
   - `STATEV(18) = SV_E_ELAS`: Whole-element elastic energy $E_{\mathrm{elas}}^{(e)}$ [$\text{kN}\cdot\text{mm} = \text{J}$] (L895)
   - `STATEV(19) = SV_PSI_F`: Area-normalized quotient $\bar{\psi}_f = E_{\mathrm{frac}}^{(e)} / A_e$ [$\text{kN/mm} = \text{J/mm}^2$; $\text{J/mm}^3$ for $B = 1.0\,\text{mm}$] (L896)
   - `STATEV(20) = SV_PSI_E`: Area-normalized quotient $\bar{\psi}_e = E_{\mathrm{elas}}^{(e)} / A_e$ [$\text{kN/mm} = \text{J/mm}^2$; $\text{J/mm}^3$ for $B = 1.0\,\text{mm}$] (L897)
2. **Single-IP Extraction Rule**:
   Layer 3 companion elements evaluate at 4 integration points, each storing the whole-element scalar value $E^{(e)}$. Field extractions from `.odb` must strictly query `IP1` only (or deduplicate by element label) to recover the exact global sum $\sum_e E^{(e)}$ and avoid a $4\times$ overcounting artifact.

---

## 4. Mechanical Parity & Verification Findings

1. **Bit-for-Bit Mechanical Parity**:
   On the benchmark qualification cases (small energy qualification case and Baseline $S_1$ benchmark), comparing pre-instrumentation and post-instrumentation runs confirms:
   - Max force deviation: $|\Delta F|_{\max} = 0.000\,\text{mN}$ across all increments.
   - Initial structural stiffness: $K_0 = 137.945520\,\text{kN/mm}$ (exact match).
   - Peak reaction force: $F_{\max} = 0.757778\,\text{kN}$ at $u_{\text{peak}} = 0.005857\,\text{mm}$.
   - Incrementation history: 0 cutbacks, identical Newton iterations.
2. **Discrete Global Energy Balance**:
   - Pre-peak ($u \le 5.50\,\mu\text{m}$): $\Delta_{\mathrm{book}} \equiv W_{\mathrm{trap}} - (E_{\mathrm{elas}} + E_{\mathrm{frac}}) < 0.007\%$, verifying high energetic precision before localization.
   - Post-peak ($u = 6.20\,\mu\text{m}$): Ligament fully severed ($d_{\max} \ge 1.0004$, $E_{\mathrm{elas}} \approx 0$). $E_{\mathrm{frac}}$ converges tightly to $2.33886 \to 2.37531\,\text{mJ}$ ($+1.56\%$ variation across $S_1 \to S_4$), classified as `STABLE_OVER_TESTED_RANGE`.
   - Classification: `GLOBAL_ENERGY_IDENTITY — NOT_YET_CLOSED` strictly preserved for supervisor review.

---

## 5. Artifact Provenance & Meeting Readiness

* **Governed Production UEL Fortran**: `models/pandey_kumar_mode1/15_energy_qualification_small/f42_mixed_uel.for` (SHA-256 `5CD0D2C015C9EAD91C99D7A744156CC86F5B5EA26473BBED7D6E5515FE30FA46`, 901 lines).
* **Diagnostic Variant**: `models/pandey_kumar_mode1/batch_mode1_energy_convergence/S1_h0030_15k_diagnostic_r2/f42_mixed_uel_diagnostic.for` (SHA-256 `3C1B40035E85343C8B63214D8788EC16FD77D8BB3495CF3ED34C2F60147C5C1A`, 973 lines).
* **Supervisor Meeting Report**: `docs/supervisor_reports/01-10-2026/MA_ModeI_Supervisor_Meeting_Pack_2026-10-01/report_main.pdf` (23 pages, SHA-256 `64AB5401DD3F1ADBFEBC62D1AFC102F5936074756E410D5DCF34FE6F69AA934A`).
* **Supervisor Compliance Checklist**: `docs/supervisor_reports/01-10-2026/MA_ModeI_Supervisor_Meeting_Pack_2026-10-01/SUPERVISOR_REQUEST_COMPLIANCE_CHECKLIST.md` (Version 1.3, SHA-256 `D656E20A17509C747568DEBC94625D80DAC9BB732CCD58A862BF232CF8FFCE6C`).
