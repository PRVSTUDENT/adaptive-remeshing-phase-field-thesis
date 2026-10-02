# CANONICAL ENERGY VARIABLE MAP & DIAGNOSTIC AUDIT
**Milestone:** `GATE_6B --- S1_DIAGNOSTIC_RECONCILED_AND_ENERGY_AUDIT_QUALIFIED`  
**Global Energy Identity Status:** `GLOBAL_ENERGY_IDENTITY --- NOT_YET_CLOSED`  
**Active Scientific Phase:** `MODE1_ENERGY_CONVERGENCE_AND_STATE_TRANSFER_FOUNDATIONS_ACTIVE`  
**Authoritative Diagnostic Source:** `f42_mixed_uel_diagnostic.for` (`SHA256: 3c1b40035e85343c8b63214d8788ec16fd77d8bb3495cf3ed34c2f60147c5c1a`)  
**Completed Diagnostic Run on Cluster:** Job `1406839.mmaster02` (`PK_M1_S1_DIAG_R2` on `mnode097`, `Exit_status=0`, 7000 accepted increments, terminal $u=0.010000\,\mathrm{mm}$) --- **RECONCILED & SCIENTIFICALLY ACCEPTED**  
**Canonical S1 Mesh Anchor:** Job `1406015.mmaster02` ($15{,}192$ cells/layer $\times$ 3 layers = $45{,}576$ elements)

---

## 1. Executive Summary & Companion-Gauss Mapping Qualification

### A. Companion-Gauss Mapping Provenance Audit
A rigorous source-code audit of `f42_mixed_uel_diagnostic.for` (lines 349–360, 495–506, and 1081–1096) resolves the Gauss-point mapping between co-located Phase UEL (`JTYPE=1`), Mechanical UEL (`JTYPE=2`), and companion visualizer UMAT (`CPE4`):
1. **Phase & Mechanical UEL Quadrature ($2 \times 2$ Gauss):**
   ```fortran
   XG4(1) = -0.577350269189626D0; YG4(1) = -0.577350269189626D0; W4(1) = 1.0D0  ! Point 1: (-1/sqrt(3), -1/sqrt(3)) [SW]
   XG4(2) =  0.577350269189626D0; YG4(2) = -0.577350269189626D0; W4(2) = 1.0D0  ! Point 2: (+1/sqrt(3), -1/sqrt(3)) [SE]
   XG4(3) =  0.577350269189626D0; YG4(3) =  0.577350269189626D0; W4(3) = 1.0D0  ! Point 3: (+1/sqrt(3), +1/sqrt(3)) [NE]
   XG4(4) = -0.577350269189626D0; YG4(4) =  0.577350269189626D0; W4(4) = 1.0D0  ! Point 4: (-1/sqrt(3), +1/sqrt(3)) [NW]
   ```
2. **Companion UMAT Integration Mapping:**
   ```fortran
   KPT_IDX = NPT
   IF (KPT_IDX .GT. 4) KPT_IDX = 4
   IF (KPT_IDX .LT. 1) KPT_IDX = 1
   IF (NSTATV .GE. 2)  STATEV(2)  = SV_H_TRIAL(PHYSIDX, KPT_IDX)
   IF (NSTATV .GE. 16) STATEV(16) = SV_H_TRIAL(PHYSIDX, KPT_IDX)
   ```
3. **Isoparametric Equivalence and Verification Governance:**
   - Companion `CPE4` elements share identical node connectivity and standard counter-clockwise Gauss point numbering ($1, 2, 3, 4$), mapping $\mathrm{NPT} = k \iff \mathrm{KPT} = k$.
   - **Classification:** **`ODB_H_GAUSS_MAPPING_CODE_INTENT_VERIFIED`**.

### B. Element-Average Damage Representation in ODB
- In UMAT, `STATEV(1)` and `STATEV(14)` receive strictly scalar element-average damage $\bar{d}_e = \frac{1}{4}\sum_{i=1}^4 U_i$, copied across all 4 companion integration points.
- **Classification:** **`ODB_PHASE_REPRESENTATION = COMPANION_ELEMENT_AVERAGED_D`**.

### C. Unique-Visualization-Element Energy Extraction Rule
- In ODB post-processing, `SDV17` ($E_{\mathrm{frac}}$) and `SDV18` ($E_{\mathrm{elas}}$) are summed by filtering strictly on the companion visualization element set `UMATELEM` (Labels $30{,}385 \dots 45{,}576$, exactly $15{,}192$ elements) and selecting `integrationPoint == 1` (or deduplicating by element label).
- Summing across all 4 Gauss points without deduplication artificially multiplies internal energy by $4\times$, which was previously corrected.

---

## 2. Definitive Variable Map & Energy Formulary

| Category | Mathematical Symbol | Subroutine Variable | Units | Storage Location | Physical Meaning & Extraction Rule |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **External Work** | $W_{\mathrm{ext}}(u)$ | `W_ext_trap` | $\mathrm{kN\cdot mm}$ | Integrated from DAT / N_RP RF2 | $\int_0^u F(\tilde{u})\,\mathrm{d}\tilde{u}$ via trapezoidal rule on N_RP nodal reaction force. |
| **Elastic Energy** | $E_{\mathrm{elas}}$ | `SV_E_ELAS(PHYSIDX)` | $\mathrm{kN\cdot mm}$ | `SDV18` (IP1) on `UMATELEM` | $\sum_{e} \int_{\Omega_e} g(d)\,\psi_0^+(\boldsymbol{\varepsilon})\,\mathrm{d}\Omega + \psi_0^-(\boldsymbol{\varepsilon})\,\mathrm{d}\Omega$. |
| **Fracture Energy** | $E_{\mathrm{frac}}$ | `SV_E_FRAC(PHYSIDX)` | $\mathrm{kN\cdot mm}$ | `SDV17` (IP1) on `UMATELEM` | $\sum_{e} \int_{\Omega_e} G_c \left[ \frac{d^2}{2 l_0} + \frac{l_0}{2} |\nabla d|^2 \right] \mathrm{d}\Omega$. |
| **Total Internal Energy**| $E_{\mathrm{int}}$ | `TOT_E_INT` | $\mathrm{kN\cdot mm}$ | Unit 105 / sum(`SDV17`+`SDV18`) | $E_{\mathrm{elas}} + E_{\mathrm{frac}}$. |
| **Two-Term Bookkeeping Difference** | $R_{\mathrm{bookkeeping}}$ | `R_bookkeeping` | $\mathrm{kN\cdot mm}$ | Computed scalar | $R_{\mathrm{bookkeeping}} = W_{\mathrm{trap}} - (E_{\mathrm{elas}} + E_{\mathrm{frac}})$. |
| **Normalized Difference** | $\Delta_{\mathrm{rel}}$ | `rel_diff_pct` | $\%$ | Computed scalar | $(R_{\mathrm{bookkeeping}} / W_{\mathrm{trap}}) \times 100\%$. |
| **Incremental History Coupling** | $\Delta T_{\mathrm{hist}}$ | `TOT_INC_T_HIST` | $\mathrm{kN\cdot mm}$ | Unit 106 Col 8 | $\sum_e \int_{\Omega_e} (g(d_{n+1}) - g(d_n)) H_n\,\mathrm{d}\Omega$. |
| **Incremental Avg Coupling** | $\Delta T_{\mathrm{avg}}$ | `TOT_INC_T_AVG` | $\mathrm{kN\cdot mm}$ | Unit 106 Col 9 | Discrete coupling due to element-average vs Gauss-point field evaluation. |
| **Incremental Strain Split** | $\Delta T_{\mathrm{split}}$ | `TOT_INC_T_SPLIT` | $\mathrm{kN\cdot mm}$ | Unit 106 Col 10 | Spectral split transition term. |
| **Cumulative Diagnostic Sum** | $\sum T_{\mathrm{sum}}$ | `CUM_T_SUM` | $\mathrm{kN\cdot mm}$ | Unit 106 Col 14 | $\sum (\Delta T_{\mathrm{hist}} + \Delta T_{\mathrm{avg}} + \Delta T_{\mathrm{split}})$. |

---

## 3. Mathematical Principles & Epistemological Commitments

1. **`TWO_TERM_BOOKKEEPING_DIFFERENCE`**:
   The quantity $R_{\mathrm{bookkeeping}} = W_{\mathrm{trap}} - (E_{\mathrm{elas}} + E_{\mathrm{frac}}) = 0.7607\%$ is an endpoint bookkeeping difference between external boundary work and two-term volume internal energy.
2. **`GLOBAL_ENERGY_IDENTITY --- NOT_YET_CLOSED`**:
   The global discrete energy identity is not closed as a single path-independent potential identity because the staggered UEL formulation evaluates $H$ at step $n$ and $d$ at step $n+1$.
3. **`COMMON_DISCRETE_POTENTIAL_DISPROVEN_BY_CROSS_DERIVATIVE_INCOMPATIBILITY`**:
   Because $\frac{\partial^2 \Pi}{\partial \boldsymbol{u}\,\partial d} \ne \frac{\partial^2 \Pi}{\partial d\,\partial \boldsymbol{u}}$ in staggered execution, finite-increment energy balance requires path-dependent increment terms.
4. **`DECOMPOSITION_REQUIRES_WITHIN_INCREMENT_PATH_INFORMATION`**:
   Exact decomposition of the discrete residual into constitutive dissipation versus numerical discretization requires continuous within-increment subiteration trajectories.

---

## 4. Reconciled Evidence Summary: Job 1406839 vs Job 1406015

```
Job 1406839.mmaster02 Terminal State (u = 0.010000 mm):
  Exit Status:                    0 (Clean Abaqus exit)
  Total Increments in DAT / ODB:  7000 (Step 1: 2000, Step 2: 5000)
  Mechanical Parity vs 1406015:   EXACT_BIT_PARITY (|Delta K0|=0.0%, |Delta Fmax|=0.0%)
  W_left:                         0.0023588327 kN*mm
  W_trap:                         0.0023593294 kN*mm
  W_right:                        0.0023598260 kN*mm
  E_elas (SDV18 at IP1):          1.16081078e-06 kN*mm
  E_frac (SDV17 at IP1):          2.34022000e-03 kN*mm
  E_elas + E_frac:                2.34138082e-03 kN*mm
  R_bookkeeping:                  1.79485350e-05 kN*mm (0.7607 %)
  Unit 105 / 106 Persisted Rows:  6994 rows (Missing 6 increments due to 22s buffer flush cutoff)
  Unit 107 Persisted Call Trace:  393,386 events (Alternating JTYPE 1 -> 2 order verified)
```
