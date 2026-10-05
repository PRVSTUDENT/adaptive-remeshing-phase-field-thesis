# Session Report: F1243 Mode-I UEL Energy Output Mechanical Parity Qualification & Gate-6B Promotion

- **Task ID**: `F1243-MODE1-UEL-ENERGY-MECHANICAL-PARITY-QUALIFICATION`
- **Agent**: `gemini-antigravity`
- **Date**: 2026-10-05T16:25:00+02:00
- **Base Commit**: `1de44c27`
- **Status**: `COMPLETED`
- **Governing Status Promotion**: `UEL_ENERGY_OUTPUT_NOT_YET_QUALIFIED` $\to$ `UEL_ENERGY_OUTPUT_QUALIFIED_MECHANICALLY_NONINVASIVE`
- **Governing Gate Verdict**: `STAGE14_UEL_ENERGY_FORMULATION_AND_MECHANICAL_PARITY_QUALIFIED`

---

## 1. Executive Summary & Objectives

This task executed a rigorous, defensible full-solve mechanical parity and source invariance audit between the pre-energy-instrumentation authoritative Mode-I fixed-reference solve and the energy-instrumented fixed-reference solve to formally decide and promote the UEL energy output qualification status within Gate-6B.

### 1.1 Provenance of Audited Solves
Both models share 100% identical geometry ($1\times 1\,\text{mm}$ plate), mesh ($15{,}192$ underlying finite elements, $15{,}521$ nodes), zero-gap sharp seam ($a_0 = 0.5\,\text{mm}$), material parameters ($E = 210\,\text{GPa}, \nu = 0.3$), phase-field parameters ($G_c = 2.7\,\text{N/mm}, l_0 = 0.0075\,\text{mm}, k_{\text{res}} = 10^{-7}$), boundary conditions, incrementation schedules, and solver controls:
1. **Pre-Instrumentation Baseline Solve**:
   - Model Path: `models/pandey_kumar_mode1/01_standard_pfm_reference/`
   - Input Deck: `PK_MODE1_STANDARD_PFM.inp` (`SHA256: C1773707D2F12FB8BFE1324AC6BE47D28D1FD6B06C4C3780CD98E9527FA7EF82`)
   - Fortran Subroutine: `f42_mixed_uel.for` (`SHA256: ED1586D6427A4B1A01D99F7E219891EC7BE9FE911E066D9360724942E7D27720`)
   - Completed Increments: $7{,}000$
2. **Energy-Instrumented Reference Solve**:
   - Model Path: `models/pandey_kumar_mode1/16_energy_qualification_reference_15k/`
   - Job ID: `1409734.mmaster02` (`PK_M1_REF15K_ENERGY`, compute node `mnode097`)
   - Input Deck: `PK_MODE1_REF15K_ENERGY.inp` (`SHA256: EC560A4C265730647B43DAB125D166EBC57CAC285D574D38222A498A967535D9`)
   - Fortran Subroutine: `f42_mixed_uel.for` (`SHA256: CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6`)
   - Completed Increments: $7{,}000$

---

## 2. Quantitative Mechanical Parity Audit Results

A point-by-point audit across all $7{,}000$ increments established complete mechanical identity:

| Metric / Quantity | Pre-Instrumentation (`ED1586D6`) | Post-Instrumentation (`CE8D5EDC`) | Absolute Difference | Relative Difference | Verdict |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Initial Stiffness $K_0$** | $137.945519645084\,\text{kN/mm}$ | $137.945519645084\,\text{kN/mm}$ | $0.000000\,\text{kN/mm}$ | **$0.000000\%$** | **BITWISE MATCH** |
| **Linear Fit $R^2$ ($N=400$)** | $0.99999960$ | $0.99999960$ | $0.000000$ | $0.000000\%$ | **BITWISE MATCH** |
| **Linear Intercept $b$** | $4.472368\times 10^{-5}\,\text{kN}$ | $4.472368\times 10^{-5}\,\text{kN}$ | $0.000000\,\text{kN}$ | $0.000000\%$ | **BITWISE MATCH** |
| **Peak Force $F_{\max}$** | $0.75777849\,\text{kN}$ | $0.75777849\,\text{kN}$ | $0.000000\,\text{kN}$ | **$0.000000\%$** | **BITWISE MATCH** |
| **Displacement at Peak $u(F_{\max})$** | $0.005857\,\text{mm}$ | $0.005857\,\text{mm}$ | $0.000000\,\text{mm}$ | **$0.000000\%$** | **BITWISE MATCH** |
| **Final Force $F(u=0.010\,\text{mm})$** | $2.32162170\times 10^{-4}\,\text{kN}$ | $2.32162150\times 10^{-4}\,\text{kN}$ | $2.0\times 10^{-11}\,\text{kN}$ | $8.61\times 10^{-6}\%$ | **ROUNDOFF PARITY** |
| **External Work $W_{\text{ext}}$** | $2.359328927990\,\text{mJ}$ | $2.359328927919\,\text{mJ}$ | $7.12\times 10^{-11}\,\text{mJ}$ | **$3.02\times 10^{-9}\%$** | **ROUNDOFF PARITY** |
| **Pointwise Max $\|\Delta u\|$** | — | — | $0.000000\,\text{mm}$ | $0.000000\%$ | **BITWISE MATCH** |
| **Pointwise Max $\|\Delta F\|$** | — | — | $1.0\times 10^{-9}\,\text{kN}$ | $1.29\times 10^{-5}\%$ | **ROUNDOFF PARITY** |
| **Total Completed Increments** | $7{,}000$ | $7{,}000$ | $0$ | $0.0\%$ | **EXACT MATCH** |
| **Total Newton Iterations** | $21{,}120$ | $21{,}120$ | $0$ | $0.0\%$ | **EXACT MATCH** |
| **Cutbacks / Severe Discon.** | $0 / 0$ | $0 / 0$ | $0 / 0$ | $0.0\%$ | **EXACT MATCH** |

### 2.1 10-State Matched Displacement Parity

| State Label | Step, Inc | Prescribed $u$ (mm) | Pre RF (kN) | Post RF (kN) | $\Delta \text{RF}$ (kN) | Rel Diff (\%) | Status |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **$u = 0.001000\,\text{mm}$** | $(1, 400)$ | $0.001000$ | $0.13792416$ | $0.13792416$ | $0.0000\,\text{e+}00$ | $0.000000\%$ | BITWISE MATCH |
| **$u = 0.003000\,\text{mm}$** | $(1, 1200)$ | $0.003000$ | $0.40841828$ | $0.40841828$ | $0.0000\,\text{e+}00$ | $0.000000\%$ | BITWISE MATCH |
| **$u = 0.005000\,\text{mm}$** | $(1, 2000)$ | $0.005000$ | $0.66205217$ | $0.66205217$ | $0.0000\,\text{e+}00$ | $0.000000\%$ | BITWISE MATCH |
| **$u = 0.005857\,\text{mm}$ (Peak)** | $(2, 857)$ | $0.005857$ | $0.75777849$ | $0.75777849$ | $0.0000\,\text{e+}00$ | $0.000000\%$ | BITWISE MATCH |
| **$u = 0.006000\,\text{mm}$** | $(2, 1000)$ | $0.006000$ | $0.00054637$ | $0.00054637$ | $1.0000\,\text{e-}11$ | $0.000002\%$ | ROUNDOFF MATCH |
| **$u = 0.006500\,\text{mm}$** | $(2, 1500)$ | $0.006500$ | $0.00048480$ | $0.00048480$ | $1.0000\,\text{e-}11$ | $0.000002\%$ | ROUNDOFF MATCH |
| **$u = 0.007000\,\text{mm}$** | $(2, 2000)$ | $0.007000$ | $0.00042986$ | $0.00042986$ | $1.0000\,\text{e-}11$ | $0.000002\%$ | ROUNDOFF MATCH |
| **$u = 0.008000\,\text{mm}$** | $(2, 3000)$ | $0.008000$ | $0.00033946$ | $0.00033946$ | $1.0000\,\text{e-}11$ | $0.000003\%$ | ROUNDOFF MATCH |
| **$u = 0.009000\,\text{mm}$** | $(2, 4000)$ | $0.009000$ | $0.00027648$ | $0.00027648$ | $2.0000\,\text{e-}11$ | $0.000007\%$ | ROUNDOFF MATCH |
| **$u = 0.010000\,\text{mm}$ (Final)** | $(2, 5000)$ | $0.010000$ | $0.00023216$ | $0.00023216$ | $2.0000\,\text{e-}11$ | $0.000009\%$ | ROUNDOFF MATCH |

---

## 3. Source Diff Analysis & Non-Invasiveness Invariants

The Fortran source diff between `ED1586D6...` and `CE8D5EDC...` proved:
1. **RHS Residual Vectors**: Zero alterations for 4-node quad elements.
2. **AMATRX Stiffness Matrices**: Zero alterations for 4-node quad elements.
3. **Degradation & History Evolution**: $g(d) = (1-d)^2 + k_{\text{res}}$ and $H(\mathbf{x}, t) = \max \psi_0^+$ are 100% bitwise invariant.
4. **State Variable Isolation**: Energy terms occupy dedicated auxiliary slots `SVARS(17..18)` and `STATEV(17..20)`, preserving baseline `SVARS(1..16)` bitwise.

---

## 4. Status Promotion & Gate-6B Remaining Items

- **Promoted Status**: `UEL_ENERGY_OUTPUT_QUALIFIED_MECHANICALLY_NONINVASIVE`
- **Closing Evidence**: Provenance-linked full-solve comparison between `01_standard_pfm_reference` (`ED1586D6...`) and `16_energy_qualification_reference_15k` (Job `1409734.mmaster02`, `CE8D5EDC...`).
- **Remaining Active Gate-6B Unresolved Items**:
  1. Spatial-resolution evaluation (Job `1410179.mmaster02`, 57,929 base elements);
  2. Convergence-control diagnostic (Job `1410180.mmaster02`, $C_n = 0.50$ relaxation);
  3. ErrorTarget fracture-response sensitivity (Jobs `1410357.mmaster02`, `1410358.mmaster02`, `1410359.mmaster02` for ET2, ET3, ET5);
  4. Multi-quantity convergence synthesis (spatial and temporal phase-field profiles awaiting these terminal solves).
- **Gate 6C Status**: Remains strictly `PENDING_GATE_6B` until the running convergence evidence is completed and evaluated.

---

## 5. Active Solvers & Verification

All 5 active scratch9 jobs remain running undisturbed:
- `1410180.mmaster02` (`PK_M1_14K_CONV_CTRL`, Step 2)
- `1410179.mmaster02` (`PK_M1_14AM_SOLVE`, Step 1)
- `1410357.mmaster02` (`PK_M1_14ET2_SOLVE`, Step 1)
- `1410358.mmaster02` (`PK_M1_14ET3_SOLVE`, Step 1)
- `1410359.mmaster02` (`PK_M1_14ET5_SOLVE`, Step 1)

- **Unit Test Suite**: 9/9 tests pass (100% OK in `tests/unit/test_stage14_uel_energy_formulation_audit.py`).
- **Supervisor Meeting Pack**: `report_main.pdf` compiled cleanly (30 pages, 0 errors).
- **Thesis**: Updated Chapter 2 with Section 2.4.2 mechanical parity table.
