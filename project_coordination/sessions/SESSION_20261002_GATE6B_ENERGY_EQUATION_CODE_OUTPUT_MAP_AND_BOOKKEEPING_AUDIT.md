# Session Report: Gate-6B Energy Equation-to-Code-to-Output Map, Bookkeeping Audit & Unit Test Regression

**Session Date:** 02 October 2026, 08:45 CEST  
**Agent Identity:** Gemini Antigravity  
**Task ID:** `F1142-GATE6B-ENERGY-EQUATION-CODE-OUTPUT-MAP-AND-BOOKKEEPING-AUDIT-20261002`  
**Parent Commit:** `42762382e8e0f4a8fc87b43eb0ddfba06028bcaf`  
**Active Phase:** `MODE1_GATE6B_ENERGY_CONVERGENCE_AND_STEP2_RECONCILIATION_ACTIVE`  
**Classification:** `GATE6B_ENERGY_SPECIFICATION_AND_REGRESSION_QUALIFIED`

---

## 1. Executive Overview

This session executed a comprehensive final audit of Gate-6B energy definitions, state-variable storage mappings, ODB/CSV data channels, unit systems, and reduction rules across the entire Mode-I toolchain (`f42_mixed_uel.for`, `extract_authoritative_mode1_energy_complete.py`, `UEXTERNALDB`, `handle_job_1409705_terminal_qualification.py`, reproduction package, and supervisor pack).

The definitive, authoritative specification [`MODE1_ENERGY_EQUATION_CODE_OUTPUT_MAP.md`](file:///D:/Master%20thesis/Adaptive%20remeshing/docs/supervisor_reports/08-10-2026/MA_ModeI_Supervisor_Meeting_Pack_2026-10-08/MODE1_ENERGY_EQUATION_CODE_OUTPUT_MAP.md) was created, verified, and integrated into both the supervisor meeting pack and the lightweight reproduction package. A dedicated unit test suite covering 7 offline regression checks was implemented in `tests/unit/test_mode1_energy_equation_code_map.py` and passed with 100% Exit 0 (7/7 tests passed; full Mode-I regression 63/63 passed).

---

## 2. Mathematical Formulations & Code Mapping Summary

| Mathematical Quantity | Mathematical Formulation | Subroutine & Line Numbers | Fortran Variable | State Array / Layer | ODB Field & Set | CSV Column (`uel_energy_balance.csv`) | Density vs Integrated | Native Unit & Conversion | Reduction / Deduplication Rule |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Fracture Surface Energy** ($E_{\text{frac}}$) | $\int_{\Omega_e} G_c \left[ \frac{d^2}{2l_0} + \frac{l_0}{2}\|\nabla d\|^2 \right] d\Omega$ | `f42_mixed_uel.for`<br>Lines 357–373 (Quad)<br>Lines 645–659 (Tri) | `E_FRAC_ELEM`<br>`SV_E_FRAC(PHYSIDX)` | Layer 3 Companion:<br>`STATEV(17)` | `SDV17` on `All_elem` (Layer 3) | `E_fracture_kNmm` | **Element-Integrated Scalar Energy** | $\text{kN}\cdot\text{mm} \equiv \text{J}$<br>($\times 1000 \to \text{mJ}$) | Single-IP1 or unique element deduplication ($\sum_{e=1}^{N_{\text{phys}}} E_{\text{frac}, e}$) |
| **Elastic Strain Energy** ($E_{\text{elas}}$) | $\int_{\Omega_e} \frac{1}{2} g(d) \boldsymbol{\varepsilon} : \mathbf{C} : \boldsymbol{\varepsilon} \, d\Omega$ | `f42_mixed_uel.for`<br>Lines 534–549 (Quad)<br>Lines 806–816 (Tri) | `E_ELAS_ELEM`<br>`SV_E_ELAS(PHYSIDX)` | Layer 3 Companion:<br>`STATEV(18)` | `SDV18` on `All_elem` (Layer 3) | `E_elastic_kNmm` | **Element-Integrated Scalar Energy** | $\text{kN}\cdot\text{mm} \equiv \text{J}$<br>($\times 1000 \to \text{mJ}$) | Single-IP1 or unique element deduplication ($\sum_{e=1}^{N_{\text{phys}}} E_{\text{elas}, e}$) |
| **Fracture Energy Density** ($\psi_f$) | $G_c \left[ \frac{d^2}{2l_0} + \frac{l_0}{2}\|\nabla d\|^2 \right]$ | `f42_mixed_uel.for`<br>Lines 375, 661 | `SV_PSI_F(PHYSIDX)` | Layer 3 Companion:<br>`STATEV(19)` | `SDV19` on `All_elem` (Layer 3) | *(Not in global CSV)* | **Local Energy Density** | $\text{kN/mm}^2 \equiv \text{MPa} \equiv \text{J/mm}^2$ | Pointwise field variable; **NEVER SUM DIRECTLY** |
| **Elastic Energy Density** ($\psi_e$) | $\frac{1}{2} g(d) \boldsymbol{\varepsilon} : \mathbf{C} : \boldsymbol{\varepsilon}$ | `f42_mixed_uel.for`<br>Lines 551, 818 | `SV_PSI_E(PHYSIDX)` | Layer 3 Companion:<br>`STATEV(20)` | `SDV20` on `All_elem` (Layer 3) | *(Not in global CSV)* | **Local Energy Density** | $\text{kN/mm}^2 \equiv \text{MPa} \equiv \text{J/mm}^2$ | Pointwise field variable; **NEVER SUM DIRECTLY** |
| **Total Internal Model Energy** ($E_{\text{model}}$) | $E_{\text{elas}} + E_{\text{frac}}$ | `UEXTERNALDB`<br>Line 137 | `TOT_E_INT` | Global Reduction | Derived: `SDV17 + SDV18` | `E_total_kNmm` | **Domain-Integrated Scalar Energy** | $\text{kN}\cdot\text{mm} \equiv \text{J}$<br>($\times 1000 \to \text{mJ}$) | Global sum over $1 \dots N_{\text{phys}}$ |
| **External Work** ($W_{\text{ext}}$) | $\int_0^u -\text{RF2}_{\text{RP}} \, du$ | Extractor script<br>Lines 124–130 | `w_cum` | ODB Assembly History | Derived from `U` & `RF` at RP node (999999) | *(Derived in postprocessing)* | **Cumulative Work** | $\text{kN}\cdot\text{mm} \equiv \text{J}$<br>($\times 1000 \to \text{mJ}$) | Composite trapezoidal integration over time history |
| **Bookkeeping Residual** ($\Delta_{\text{book}}$) | $E_{\text{model}} - W_{\text{ext}}$ | Extractor script<br>Line 167 | `delta_book` | Postprocessed Diagnostic | Derived: $E_{\text{model}} - W_{\text{ext}}$ | *(Diagnostic output)* | **Scalar Energy Discrepancy** | $\text{kN}\cdot\text{mm} \equiv \text{J}$<br>($\times 1000 \to \text{mJ}$) | Point-by-point subtraction along displacement path |

---

## 3. Key Findings & Epistemological Discipline

1. **Phase-Field Surface Energy vs. Dissipated Energy:**
   - $E_{\text{frac}}$ represents the *regularized crack surface energy functional* $\Gamma_d(d) = \int_\Omega G_c \left[ \frac{d^2}{2l_0} + \frac{l_0}{2} |\nabla d|^2 \right] d\Omega$. Under damage irreversibility ($\dot{d} \ge 0$), it acts as the phase-field proxy for accumulated surface energy. It is **not** called "dissipated fracture energy" in the authoritative documentation.
2. **Local Densities vs. Element-Integrated Energies:**
   - $\psi_f$ (`SDV19`) and $\psi_e$ (`SDV20`) are local densities ($\text{kN/mm}^2$).
   - $E_{\text{frac}}$ (`SDV17`) and $E_{\text{elas}}$ (`SDV18`) are element-integrated scalar energies ($\text{kN}\cdot\text{mm} \equiv \text{J}$).
   - Direct summation of $\psi_f$ or $\psi_e$ without multiplying by element area $A_e$ causes dimensional and numerical errors.
3. **Single-IP Extraction & Zero Overcounting:**
   - Layer-3 companion CPE4 elements duplicate scalar energies across all 4 integration points. Summing all 4 points inflates total energy by $4\times$. The extractor enforces single-value element deduplication (`seen_elems = set()`), guaranteeing exact domain integration.
4. **Zero Multi-Layer Double Counting:**
   - Fortran `UEXTERNALDB` sums `SV_E_ELAS(I)` and `SV_E_FRAC(I)` over $I = 1 \dots N_{\text{capacity}}$, indexing each physical element $1 \dots N_{\text{phys}}$ exactly once. Layer 1, Layer 2, and Layer 3 do not create duplicate slots.

---

## 4. Verification & Regression Results

1. **Reproduction Package Self-Check:**
   - Script: `models/pandey_kumar_mode1/reproduction_package_gate6b_energy/verify_reproduction_package.py`
   - Result: **17 / 17 checks passed (100.0% Exit 0)**.
2. **Unit Test Suite for Energy Map:**
   - Suite: `tests/unit/test_mode1_energy_equation_code_map.py`
   - Result: **7 / 7 passed in 0.26s (100% Exit 0)**.
3. **Full Mode-I Regression Suite:**
   - Test Discovery: 63 tests across 7 test files.
   - Result: **63 / 63 passed in 2.35s (100% Exit 0)**.
4. **Convergence Matrix Upgrade:**
   - File: `docs/supervisor_reports/08-10-2026/MA_ModeI_Supervisor_Meeting_Pack_2026-10-08/MODE1_CONVERGENCE_EXECUTION_MATRIX.md` (Revision 11, SHA-256 `5B49E0C9CC6B4E8D4A201341E383FB50D2EA32EC65CC4AE399EAFC5E012E4F4A`).

---

## 5. Active Governance State

- **Active Running Reference Job:** `1409734.mmaster02` (`PK_M1_REF15K_ENERGY`) is actively running on compute node `mnode097/0` in `normal_imfdfkmq` with live ODB and `uel_energy_balance.csv` updating. Preserved completely untouched / zero polling.
- **Candidate Packages $S_2$ and $S_3$:** Staged at `DATACHECK_PASSED_READY_AFTER_CORRECTED_S1_ENERGY_QUALIFICATION` (strictly unsubmitted, `authorized = false`).
- **Step-2 62k Adaptive Mesh:** Maintained frozen at `ROOT_CAUSE_CANDIDATE_NOT_YET_RECONCILED` (0 replacement jobs authorized).
- **Scope Restriction:** Mode-II and multi-step state transfer remain paused on **HOLD**.
