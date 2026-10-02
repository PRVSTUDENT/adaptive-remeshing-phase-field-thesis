# Master Thesis Mode-I Final Convergence & Energy Audit Brief (08 October 2026)

**Candidate:** Pruthviraja Reddy Vandavagali (Matr. Nr. 68865)  
**Supervisors:** Prof. Dipl.-Ing. Björn Kiefer, Ph.D., Dr.-Ing. Stephan Roth (IMFD, TU Bergakademie Freiberg)  
**Governing Directive:** *"We need to have understood everything related to the first model before we increase complexity."*  
**Active Scientific Phase:** `MODE1_ENERGY_CONVERGENCE_AND_STATE_TRANSFER_FOUNDATIONS_ACTIVE`  
**Active Milestone Gate:** **Gate 6B: Mode-I Energetic & Multi-Quantity Convergence** (`ACTIVE -- HIGHEST PRIORITY`)  
**Associated Job Series:** `PK_M1_S1` through `PK_M1_S4`, `PK_M1_T1` through `PK_M1_T3`, `PK_M1_A1` through `PK_M1_A4`, `PK_M1_S3_L01125`, `PK_M1_S3_L01500`  
**Authoritative Subroutine Hash (`f42_mixed_uel.for`):** `SHA256: 5cd0d2c015c9ead91c99d7a744156cc86f5b5ea26473bbed7d6e5515fe30fa46`

---

## 1. Executive Summary & Purpose

This briefing document consolidates the complete numerical, mechanical, and energetic evidence for the Mode-I phase-field fracture benchmark ahead of the supervisory review on **08 October 2026 (10:00)**. 

### Core Scientific Milestones Completed:
1. **Mechanical Anomaly Resolution (Gate 6A):** `RESOLVED_AND_CLOSED`. The 71,320-element initial stiffness defect was proven to arise from an Abaqus keyword preprocessing line limit ($\le 16$ nodes per line in `*NSET` without `GENERATE`), silently omitting 134 of 150 boundary nodes. Wrapping the data lines restored all constraints and achieved reference-consistent structural stiffness recovery (within $0.09\%$, $K_0 = 137.820804\,\mathrm{kN/mm}$ in full fracture Job `1404933`, $\Delta K_0 = -0.09\%$, $\Delta F_{\mathrm{max}} = -1.64\%$).
2. **Native Remeshing Reproduction (Gate 5):** `SUPERVISOR_ACCEPTED_REPRODUCTION_LIMITATION_CLOSED`. The supervisor accepted that publication details do not expose enough information to reproduce every reported element count exactly. Parametric sensitivity trends are preserved and strictly disambiguated between offline preliminary sizing ($1.0\% \to 71{,}320$; $2.0\% \to 17{,}687$; $3.0\% \to 8{,}120$; $5.0\% \to 4{,}356$) and the audited production batch meshes ($1.0\% \to 71{,}320$; $2.0\% \to 15{,}396$; $3.0\% \to 7{,}633$; $5.0\% \to 4{,}194$ finite elements).
3. **UEL Energy Formulation & Accounting (Priority 1):**
   - Implemented stored elastic strain energy $E_{\mathrm{elas}}$ (`ENERGY(2)`) and regularized fracture surface energy $E_{\mathrm{frac}}$ (`ENERGY(7)`).
   - Proven mathematically decoupled from residual vector (`RHS`) and stiffness (`AMATRX`).
   - Single-IP extraction rule enforces unambiguous recovery of once-per-element global integrals without $4\times$ visualizer overcounting artifacts.
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
- **Canonical Reference Values (Fine Mesh Job 1406015, 15,192 elements):**
  - Initial structural stiffness $K_0 = 137.945520\,\mathrm{kN/mm}$ ($R^2 = 0.99999960, N = 400$ increments).
  - Peak reaction force $F_{\mathrm{max}} = 0.757778\,\mathrm{kN}$ at $u = 0.005857\,\mathrm{mm}$ (digitized reference: $F_{\mathrm{max}} \approx 0.758\,\mathrm{kN}$ at $u \approx 0.00586\,\mathrm{mm}$).

---

## 3. Spatial, Temporal, and Regularization Convergence Summary

### 3.1 Spatial Mesh Convergence
| Mesh Case | Element Count | $h_{\mathrm{ref}}$ (mm) | $F_{\mathrm{max}}$ (kN) | $u(F_{\mathrm{max}})$ (mm) | $K_0$ (kN/mm) | $w_{0.5}$ ($\mu$m) | $w_{0.9}$ ($\mu$m) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **$S_1$** (Coarse Fixed) | 15,192 | 0.00300 | 0.757778 | 0.005857 | 137.946 | 23.342 | 8.796 |
| **$S_2$** (Medium Fixed) | 32,258 | 0.00200 | 0.742398 | 0.005721 | 137.892 | 22.969 | 9.819 |
| **$S_3$** (Fine Fixed) | 41,912 | 0.00150 | 0.732196 | 0.005633 | 137.858 | 23.140 | 10.666 |
| **$S_4$** (Very Fine Fixed) | 51,200 | 0.00125 | 0.727142 | 0.005584 | 137.904 | 22.984 | 10.165 |
| **$A_1$** (Adaptive 1%) | 71,320 | 0.00085 | 0.734795 | 0.005650 | 138.006 | 22.969 | 9.940 |
| **$A_2$** (Adaptive 2%) | 15,396 | 0.00185 | 0.748197 | 0.005775 | 137.844 | 22.775 | 9.851 |
| **$A_3$** (Adaptive 3%) | 7,633 | 0.00260 | 0.743471 | 0.005733 | 137.854 | 22.133 | 7.440 |
| **$A_4$** (Adaptive 5%) | 4,194 | 0.00350 | 0.764964 | 0.007060 | 137.966 | 20.301 | 4.646 |

*(Note: Governed fixed series is $S_1 - S_4$. The 69,384-element $h \approx 1.0\,\mu\mathrm{m}$ case is a separate historical fine run with $F_{\mathrm{max}} = 0.7255\,\mathrm{kN}, u_{\mathrm{peak}} = 5.575\,\mu\mathrm{m}$, not a governed $S_5$. Spatial peak force and peak displacement are classified as `MESH-SENSITIVE` over the full range).*

### 3.2 Temporal Convergence ($T_1 - T_3$)
- Pre-peak $F_{\mathrm{max}}$ is stable within $<0.07\%$: $T_1$ ($0.758153\,\mathrm{kN}$), $T_2$ ($0.757778\,\mathrm{kN}$), $T_3$ ($0.757630\,\mathrm{kN}$); total variation $0.0690\%$.
- Pre-peak two-term bookkeeping difference: $|\mathrm{TWO\_TERM\_BOOKKEEPING\_DIFFERENCE}| / W_{\mathrm{trap}} \le 0.008\%$ on frozen $S_1$ / temporal $T_1-T_3$ trajectory ($-0.005\%$ at $u = 5.0\,\mu\mathrm{m}$, $-0.007\%$ at $u = 5.856\,\mu\mathrm{m}$).
- Terminal work $W_{\mathrm{trap}}$ ($\sim 3.24\%$ variation) and post-peak normalized bookkeeping difference ($+0.38\%$ to $+3.54\%$) are classified as `TEMPORALLY SENSITIVE`.

### 3.3 Phase-Field Regularization ($l_0$ Sensitivity)
- $l_0 = 7.50\,\mu\mathrm{m} \implies F_{\mathrm{max}} = 0.732196\,\mathrm{kN}, u_{\mathrm{peak}} = 5.633\,\mu\mathrm{m}, K_0 = 137.857608\,\mathrm{kN/mm}$
- $l_0 = 11.25\,\mu\mathrm{m} \implies F_{\mathrm{max}} = 0.708402\,\mathrm{kN}, u_{\mathrm{peak}} = 5.590\,\mu\mathrm{m}, K_0 = 137.765563\,\mathrm{kN/mm}$
- $l_0 = 15.00\,\mu\mathrm{m} \implies F_{\mathrm{max}} = 0.689540\,\mathrm{kN}, u_{\mathrm{peak}} = 5.579\,\mu\mathrm{m}, K_0 = 137.676175\,\mathrm{kN/mm}$
- $F_{\mathrm{max}}$ and $u_{\mathrm{peak}}$ are classified as `LENGTH-SCALE SENSITIVE` ($-5.83\%$ peak force reduction across series); $K_0$ is classified as `INSENSITIVE / STABLE OVER TESTED RANGE` ($<0.14\%$). Unproven $F_{\mathrm{max}} \propto 1/\sqrt{l_0}$ and $w_{0.5} \approx 3.04\,l_0$ claims are strictly excluded.

### 3.4 Spatial Energetic Convergence ($S_1 - S_4$)
Global energy components evaluated across meshes $S_1$ ($3.0\,\mu\mathrm{m}$, 15.2k elems), $S_2$ ($2.0\,\mu\mathrm{m}$, 32.1k elems), $S_3$ ($1.5\,\mu\mathrm{m}$, 41.9k elems), and $S_4$ ($1.25\,\mu\mathrm{m}$, 51.4k elems) via verified single-IP extraction from full ODBs at matched accepted displacements:
- **Pre-Peak ($u = 5.50\,\mu\mathrm{m}$):**
  - Boundary work $W_{\mathrm{trap}} = 2.03739 \to 2.03528\,\mathrm{mJ}$ ($-0.10\%$, `STABLE_OVER_TESTED_RANGE`).
  - Stored elastic energy $E_{\mathrm{elas}} = 1.98181 \to 1.97717\,\mathrm{mJ}$ ($-0.23\%$, `STABLE_OVER_TESTED_RANGE`).
  - Regularized fracture surface energy $E_{\mathrm{frac}} = 0.05572 \to 0.05815\,\mathrm{mJ}$ ($+4.36\%$, `MESH-SENSITIVE`, associated with sharper notch-tip damage core resolution, $d_{\max}$ rising $0.4105 \to 0.5073$).
  - Pre-peak two-term bookkeeping difference $|\Delta_{\mathrm{book}}| \le 0.00014\,\mathrm{mJ}$ ($<0.007\%$ of $W_{\mathrm{trap}}$).
- **Post-Peak Fully Fractured State ($u = 6.20\,\mu\mathrm{m}$):**
  - Severed ligament with $d_{\max} \ge 1.0004$ across all cases ($E_{\mathrm{elas}} < 0.0016\,\mathrm{mJ} \approx 0$).
  - Fracture surface energy evaluated across the meshes gives $E_{\mathrm{frac}} = 2.33886\,\mathrm{mJ}$ ($S_1$), $2.33022\,\mathrm{mJ}$ ($S_2$, $-0.37\%$), $2.35701\,\mathrm{mJ}$ ($S_3$, $+0.78\%$), and $2.37531\,\mathrm{mJ}$ ($S_4$, $+1.56\%$). Across the tested $S_1 - S_4$ range ($3.4\times$ mesh refinement), post-peak $E_{\mathrm{frac}}$ varies by **$1.56\%$** and is classified as `STABLE_OVER_TESTED_RANGE`.
  - Boundary work $W_{\mathrm{trap}} = 2.35801 \to 2.17004\,\mathrm{mJ}$ ($-7.97\%$, `MESH-SENSITIVE`, associated with earlier peak displacement $u_{\mathrm{peak}} = 5.857 \to 5.586\,\mu\mathrm{m}$ and reduced peak load).
  - Two-term bookkeeping difference $\Delta_{\mathrm{book}} \equiv W_{\mathrm{trap}} - (E_{\mathrm{elas}} + E_{\mathrm{frac}})$ is strictly designated as `TWO_TERM_BOOKKEEPING_DIFFERENCE` ($+0.01754\,\mathrm{mJ}$ [$+0.74\%$, $S_1$] to $-0.20585\,\mathrm{mJ}$ [$-9.49\%$, $S_4$]), and `GLOBAL_ENERGY_IDENTITY — NOT_YET_CLOSED` is preserved without asserting unverified within-increment dissipation mechanisms.

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

## 7. Supervisor Decision Framework (08 October 2026 Meeting)

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
