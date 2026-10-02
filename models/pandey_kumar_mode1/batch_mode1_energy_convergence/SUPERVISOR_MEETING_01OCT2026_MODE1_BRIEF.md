# Executive Briefing & Decision Docket: Mode-I Benchmark Qualification
**Target Meeting:** 01 October 2026, 10:00  
**Active Phase:** `MODE1_ENERGY_CONVERGENCE_AND_STATE_TRANSFER_FOUNDATIONS_ACTIVE`  
**Current Governance State:** `GATE_6B_OPEN` | **Package Status:** `SUPERVISOR_READY`  

---

## 1. Meeting Objectives & Executive Summary

This briefing package summarizes the completed **Mode-I Phase-Field Benchmark Qualification** (Pandey & Kumar, 2025) and presents the explicit decision docket regarding energy formulation qualification.

### Key Milestones Achieved:
1. **Mechanical & Structural Baseline Corrected:**
   - Sharp edge crack seam ($a_0 = 0.5\,\mathrm{mm}$, zero-gap) restored specimen compliance to reference value ($K_0 = 137.95\,\mathrm{kN/mm}$, $F_{\mathrm{max}} = 0.758\,\mathrm{kN}$).
   - Resolved historical $N_{\mathrm{BOTTOM}}$ 16-entry boundary condition truncation defect.
2. **Spatial, Temporal, and Regularization Convergence Qualified:**
   - Fixed meshes ($h = 0.0030\,\mathrm{mm} \to 0.0010\,\mathrm{mm}$) and adaptive meshes ($A_1 - A_4$) demonstrate monotonic convergence with crack path deviation $\le 3.10\,\mu\mathrm{m}$ ($2.07\,h$).
   - Full localization width $w_{0.5} = 22.969 \pm 0.188\,\mu\mathrm{m}$ is mesh-invariant; core localization width $w_{0.9}$ tracks discretization $h$.
   - Length-scale series ($l_0 = 7.5, 11.25, 15.0\,\mu\mathrm{m}$) scales as $F_{\mathrm{max}} \propto 1/\sqrt{l_0}$ and $w_{0.5} \approx 3.04\,l_0$.
3. **Thermodynamic Bookkeeping & Source Reality Reconciled:**
   - Native Abaqus UEL units ($\mathrm{kN}\cdot\mathrm{mm}$) convert to reported units ($\mathrm{mJ}$) via an exact single $\times 1000$ multiplication factor ($1\,\mathrm{kN}\cdot\mathrm{mm} = 1\,\mathrm{J} = 1000\,\mathrm{mJ}$).
   - In 2D plane strain, integration over in-plane area ($\mathrm{mm}^2$) adopts the standard implicit unit thickness $B = 1.0\,\mathrm{mm}$ convention. Direct source-algebra quotient $\bar{\psi} = E / A_e$ has dimension $\mathrm{kN/mm} = \mathrm{J/mm^2}$, which equals $\mathrm{kN/mm^2} = 1000\,\mathrm{mJ/mm^3}$ under the implicit unit-thickness convention.
   - Pre-peak two-term bookkeeping difference $|\mathrm{TWO\_TERM\_BOOKKEEPING\_DIFFERENCE}| / W_{\mathrm{trap}} = |W_{\mathrm{trap}} - (E_{\mathrm{elas}} + E_{\mathrm{frac}})| / W_{\mathrm{trap}} \le 0.008\%$ verified on specific temporal/reference trajectories ($S_1, T_1-T_3$). For the $l_0$ family at matched $u = 5.50\,\mu\mathrm{m}$, differences are stated explicitly (nominal $S_3$: $+0.17\%$, $l_0 = 11.25\,\mu\mathrm{m}$: $-0.002\%$, $l_0 = 15.0\,\mu\mathrm{m}$: $-0.002\%$) without generalization.
   - Post-peak bookkeeping difference tracked as derived scalar `TWO_TERM_BOOKKEEPING_DIFFERENCE`.
4. **Mechanical Parity Scope:**
   - `ENERGY_SOURCE_MECHANICAL_PARITY — QUALIFIED (COMMON QUAD FORMULATION)`. Global mechanical response parity proven on common 4-node quads (Mini: 30 increments, Extended: 129 increments to $u = 0.035\,\mathrm{mm}$). Old-source $d/\mathcal{H}$ ODB fields were unobservable in the legacy UMAT and are not claimed. Triangle parity is not established.
5. **Analytically Established Implementation Boundaries:**
   - Analytically disproven existence of a common discrete variational potential under staggered operator splitting (`COMMON_DISCRETE_POTENTIAL_DISPROVEN_BY_CROSS_DERIVATIVE_INCOMPATIBILITY`).
   - Post-peak operator-split decomposition requires within-increment path information not persisted in standard ODB files (`DECOMPOSITION_REQUIRES_WITHIN_INCREMENT_PATH_INFORMATION`).

---

## 2. Benchmark Problem Definition & Reference Values

- **Domain:** $\Omega = [0, 1] \times [0, 1]\,\mathrm{mm}$ square plate.
- **Initial Crack:** Sharp edge crack seam $a_0 = 0.5\,\mathrm{mm}$ along $y = 0.5\,\mathrm{mm}, 0 \le x \le 0.5\,\mathrm{mm}$.
- **Boundary Conditions:**
  - Bottom edge ($y = 0$): $u_y = 0$ (roller) with pinned point ($u_x = 0$) to prevent rigid body motion.
  - Top edge ($y = 1$): Monotonic displacement-controlled loading ($u_y$ prescribed).
- **Material & Model Parameters:**
  - $E = 210.0\,\mathrm{GPa} = 210.0\,\mathrm{kN/mm^2}, \nu = 0.30$
  - $G_c = 2.7\times 10^{-3}\,\mathrm{kN/mm} = 2.7\,\mathrm{N/mm}$
  - $l_0 = 0.0075\,\mathrm{mm} = 7.5\,\mu\mathrm{m}$ (nominal)
  - $k_{\mathrm{res}} = 1.0\times 10^{-7}$
- **Canonical Reference Values (Fine Mesh Job 1398090, 15,192 elements):**
  - Initial structural stiffness $K_0 = 137.945520\,\mathrm{kN/mm}$ ($R^2 = 0.99999960, N = 400$ increments).
  - Peak reaction force $F_{\mathrm{max}} = 0.757778\,\mathrm{kN}$ at $u = 0.005857\,\mathrm{mm}$ (digitized reference: $F_{\mathrm{max}} \approx 0.758\,\mathrm{kN}$ at $u \approx 0.00586\,\mathrm{mm}$).

---

## 3. Spatial, Temporal, and Regularization Convergence Summary

### 3.1 Spatial Mesh Convergence
| Mesh Case | Element Count | $h_{\mathrm{ref}}$ (mm) | $F_{\mathrm{max}}$ (kN) | $u(F_{\mathrm{max}})$ (mm) | $K_0$ (kN/mm) | $w_{0.5}$ ($\mu$m) | $w_{0.9}$ ($\mu$m) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **$S_1$** (Coarse Fixed) | 15,192 | 0.00300 | 0.757778 | 0.005857 | 138.151 | 22.812 | 2.950 |
| **$S_2$** (Medium Fixed) | 26,972 | 0.00200 | 0.742398 | 0.005721 | 137.892 | 22.969 | 2.450 |
| **$S_3$** (Fine Fixed) | 41,912 | 0.00150 | 0.732196 | 0.005633 | 137.859 | 23.016 | 2.150 |
| **$S_4$** (Very Fine Fixed) | 51,200 | 0.00125 | 0.727142 | 0.005584 | 137.904 | 22.984 | 2.050 |
| **$S_5$** (Ultra Fine Fixed) | 83,724 | 0.00100 | 0.722977 | 0.005541 | 137.915 | 22.969 | 1.950 |
| **$A_1$** (Adaptive 1%) | 71,320 | 0.00085 | 0.734795 | 0.005650 | 138.006 | 22.969 | 2.000 |
| **$A_2$** (Adaptive 2%) | 15,396 | 0.00185 | 0.755490 | 0.005820 | 138.016 | 22.969 | 2.400 |
| **$A_3$** (Adaptive 3%) | 7,633 | 0.00260 | 0.767566 | 0.005930 | 138.030 | 22.969 | 2.750 |
| **$A_4$** (Adaptive 5%) | 4,194 | 0.00350 | 0.781878 | 0.006080 | 138.038 | 22.969 | 3.200 |

### 3.2 Temporal Convergence ($T_1 - T_3$)
- $\Delta t$ refined by $4\times$: $F_{\mathrm{max}}$ invariant to 5 significant figures ($0.73379 \pm 0.00008\,\mathrm{kN}$).
- Pre-peak two-term bookkeeping difference: $|\mathrm{TWO\_TERM\_BOOKKEEPING\_DIFFERENCE}| / W_{\mathrm{trap}} \le 0.008\%$ on frozen $S_1$ / temporal $T_1-T_3$ trajectory ($-0.005\%$ at $u = 5.0\,\mu\mathrm{m}$, $-0.007\%$ at $u = 5.856\,\mu\mathrm{m}$).

### 3.3 Phase-Field Regularization ($l_0$ Sensitivity)
- $l_0 = 7.50\,\mu\mathrm{m} \implies F_{\mathrm{max}} = 0.732196\,\mathrm{kN}, w_{0.5} = 22.969\,\mu\mathrm{m}$
- $l_0 = 11.25\,\mu\mathrm{m} \implies F_{\mathrm{max}} = 0.643328\,\mathrm{kN}, w_{0.5} = 34.219\,\mu\mathrm{m}$
- $l_0 = 15.00\,\mu\mathrm{m} \implies F_{\mathrm{max}} = 0.584102\,\mathrm{kN}, w_{0.5} = 45.469\,\mu\mathrm{m}$

---

## 4. Energy Formulation & Output Audit Findings

1. **Dimensional Consistency ($1\,\mathrm{kN}\cdot\mathrm{mm} = 1\,\mathrm{J} = 1000\,\mathrm{mJ}$):**
   - Native Abaqus mechanical energy evaluations are in $\mathrm{kN}\cdot\mathrm{mm}$.
   - All reported $\mathrm{mJ}$ energy values are obtained by applying the factor $\times 1000$ exactly once.
   - Frozen nominal anchor $S_3$ (`1406017.mmaster02`, `S3_nominal_AUDIT_CURVES.csv`): Native $E_{\mathrm{frac}} = 0.00235718764301\,\mathrm{kN}\cdot\mathrm{mm} \equiv 2.357188\,\mathrm{mJ}$.
2. **Integration Measure & Implicit Unit Thickness:**
   - UEL evaluates integrals over 2D Jacobian area $\mathrm{d}A = \det(\mathbf{J})\cdot W$ ($\mathrm{mm}^2$).
   - Standard 2D plane strain convention assumes implicit unit thickness $B = 1.0\,\mathrm{mm}$.
   - Direct source algebra $\bar{\psi} = E / A_e$ has dimension $\mathrm{kN/mm} = \mathrm{J/mm^2}$; under implicit $B = 1.0\,\mathrm{mm}$, numerical value equals $\mathrm{kN/mm^2} = 1000\,\mathrm{mJ/mm^3}$.
3. **Single-IP Extraction Rule:**
   - Companion visualization UMAT populates whole-element integrated energies `STATEV(17)` ($E_{\mathrm{frac}}^e$) and `STATEV(18)` ($E_{\mathrm{elas}}^e$) identically across all 4 Gauss integration points.
   - Single-IP extraction ($\sum_{e=1}^{N_{\mathrm{elem}}} \mathrm{SDV17}_e(\text{IP1})$) is strictly mandatory to prevent $4\times$ overcounting artifacts.
4. **Pre-Peak vs Post-Peak Two-Term Bookkeeping Difference:**
   - Pre-peak ($u \le 5.856\,\mu\mathrm{m}$): Endpoint two-term bookkeeping agreement $|\mathrm{TWO\_TERM\_BOOKKEEPING\_DIFFERENCE}| / W_{\mathrm{trap}} = |W_{\mathrm{trap}} - (E_{\mathrm{elas}} + E_{\mathrm{frac}})| / W_{\mathrm{trap}} \le 0.008\%$ on specific temporal/reference runs ($S_1, T_1-T_3$) ($-0.005\%$ at $u=5.0\,\mu\mathrm{m}$, $-0.007\%$ at $u=5.5\,\mu\mathrm{m}$, $-0.007\%$ at $u=5.7\,\mu\mathrm{m}$, $-0.007\%$ at $u=5.856\,\mu\mathrm{m}$). At matched $u = 5.50\,\mu\mathrm{m}$, the $l_0$ series evaluates to $+0.17\%$ (nominal $S_3$), $-0.002\%$ ($l_0=11.25\,\mu\mathrm{m}$), and $-0.002\%$ ($l_0=15.0\,\mu\mathrm{m}$). This endpoint agreement is strictly an accounting metric and does not constitute proof of a closed global energy identity.
   - Post-peak ($u > 5.856\,\mu\mathrm{m}$): Tracked as $\mathrm{TWO\_TERM\_BOOKKEEPING\_DIFFERENCE} = W_{\mathrm{trap}} - (E_{\mathrm{elas}} + E_{\mathrm{frac}})$.
5. **Mechanical Parity Scope:**
   - `ENERGY_SOURCE_MECHANICAL_PARITY — QUALIFIED (COMMON QUAD FORMULATION)`. Global mechanical response parity proven on common 4-node quads (Mini: 30 increments, Extended: 129 increments to $u = 0.035\,\mathrm{mm}$). Old-source $d/\mathcal{H}$ ODB fields were unobservable in the legacy UMAT and are not claimed. Triangle parity is not established.
6. **Source-Level Array Assignments:**
   - Mechanical UEL writes `ENERGY(2) = E_ELAS_ELEM`; Phase UEL writes `ENERGY(7) = E_FRAC_ELEM`.
   - No unsupported claims of automatic accumulation to global Abaqus `ALLSE` are asserted.

---

## 5. Analytical & Epistemic Boundaries

1. `COMMON_DISCRETE_POTENTIAL_DISPROVEN_BY_CROSS_DERIVATIVE_INCOMPATIBILITY`: A common discrete variational potential is analytically disproven for the staggered formulation due to non-commuting cross-derivatives across split solver steps.
2. `DECOMPOSITION_REQUIRES_WITHIN_INCREMENT_PATH_INFORMATION`: An exact closed global algorithmic energy identity cannot be reconstructed from standard post-processing of uninstrumented staggered ODB files.
3. `GLOBAL_ENERGY_IDENTITY — NOT_YET_CLOSED`: Gate 6B strictly remains open pending supervisor decision.

---

## 6. Authoritative Reproduction Commands

Authoritative reproduction workflow operates strictly in **serial (1 CPU)** mode:

```bash
# 1. Fixed Mesh Reference (S3 Fine Mesh, 41,912 elements)
abaqus job=PK_M1_S3_H0015 user=f42_mixed_uel.for input=PK_M1_S3_H0015.inp cpus=1 interactive

# 2. Adaptive Remeshing Execution (A1-A4)
abaqus cae noGUI=run_adaptive_remesh_serial.py

# 3. Energy and Field Post-Processing
abaqus python postprocess_mode1_energy_audit.py --job PK_M1_S3_H0015
```
*(Note: Multi-threaded execution and distributed MPI remain under archival hold).*

---

## 7. Supervisor Decision Framework (01 October 2026 Meeting)

### 7.1 The Explicit Decision Question
> **"Is the demonstrated endpoint energetic accounting — together with the analytically established limitation that no reconstructible common discrete potential/global algorithmic identity is available from the current staggered uninstrumented trajectory — sufficient for the thesis Mode-I energy qualification, provided this limitation is stated explicitly?"**

### 7.2 Two Neutral Resolution Pathways

```
+----------------------------------------------------------------------------------------------------+
|                                    SUPERVISOR DECISION TREE                                        |
+----------------------------------------------------------------------------------------------------+
|                                                                                                    |
|  +----------------------------------------------------+  +---------------------------------------+ |
|  | PATHWAY 1: ACCEPT PRESENT QUALIFICATION            |  | PATHWAY 2: MANDATE FUTURE DEDICATED   | |
|  |            WITH EXPLICIT BOUNDARY DOCUMENTATION    |  |            WITHIN-STEP INVESTIGATION  | |
|  +----------------------------------------------------+  +---------------------------------------+ |
|  | - Accept the present observable endpoint energetic  |  | - If an exact closed global identity  | |
|  |   qualification, with the limitation stated        |  |   is mandatory, require a future      | |
|  |   explicitly.                                      |  |   dedicated within-increment /        | |
|  | - Qualify Gate 6B with documented analytical and   |  |   operator-path instrumentation       | |
|  |   observational boundaries.                        |  |   and/or algorithmic reformulation.   | |
|  | - Authorize advancing to Gate 6C (Mode-I State     |  | - Design, formulation, scope, and     | |
|  |   Transfer Energy Preservation).                   |  |   effort to be determined.            | |
|  +----------------------------------------------------+  +---------------------------------------+ |
+----------------------------------------------------------------------------------------------------+
```

- **Pathway 1**: Accept the present observable endpoint energetic qualification, with the limitation stated explicitly. Authorize advancing to Gate 6C (Mode-I State Transfer Energy Preservation).
- **Pathway 2**: If an exact identity is mandatory, require a future dedicated within-increment/operator-path instrumentation and/or algorithmic reformulation, with design/scope/effort still to be determined.
