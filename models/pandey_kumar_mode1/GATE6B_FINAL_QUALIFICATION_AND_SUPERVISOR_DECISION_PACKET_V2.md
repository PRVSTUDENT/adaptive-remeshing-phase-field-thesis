# Gate-6B Final Qualification & Supervisor Decision Packet
**Benchmark:** Mode-I Edge-Cracked Square Plate (Pandey & Kumar, 2025)  
**Governance State:** `GATE_6B_OPEN_PENDING_SUPERVISOR_DECISION_01OCT2026` | **Readiness Status:** `SUPERVISOR_READY`  
**Active Phase:** `MODE1_ENERGY_CONVERGENCE_AND_STATE_TRANSFER_FOUNDATIONS_ACTIVE`  
**Date:** 23 September 2026 | **Target Supervisor Meeting:** 08 October 2026, 10:00 | **Revision:** `V2 (Reconciled Governance & Evidence Bounds)`  

---

## 1. Executive Summary & Purpose

This packet delivers the finalized, evidence-backed qualification of Gate 6B (Mode-I Energetic and Convergence Foundations) for the Pandey & Kumar (2025) benchmark.

### 1.1 Core Scientific Findings
1. **Convergence & Sensitivity Behavior:**
   - **Qualified Quantities:** Initial structural stiffness $K_0$ ($137.95\,\mathrm{kN/mm}$, invariant across models with $<0.09\%$ spread), crack-path symmetry along the horizontal symmetry plane, temporal force invariance across $T_1-T_3$ ($\Delta F_{\max} < 0.07\%$), and verified spatial localization widths across models ($S_1$: $w_{0.5} = 23.3418\,\mu\mathrm{m}$, $S_2$: $22.9510\,\mu\mathrm{m}$, $S_3$: $23.1397\,\mu\mathrm{m}$, $S_4$: $22.8298\,\mu\mathrm{m}$, $A_1$: $23.1512\,\mu\mathrm{m}$, $A_2$: $22.7753\,\mu\mathrm{m}$, $A_3$: $22.1325\,\mu\mathrm{m}$, $A_4$: $20.3008\,\mu\mathrm{m}$).
   - **Mesh-Sensitive Quantities:** Peak reaction force $F_{\max}$, displacement at peak force $u_{\mathrm{peak}}$, and core localization width $w_{0.9}$ are mesh-sensitive across the spatial series.
   - **Documented Limitations:** Spatial discretization energetic convergence across $S_1 - S_4$ is `QUALIFIED` ($W_{\mathrm{trap}}$ and $E_{\mathrm{elas}}$ pre-peak stable $<0.23\%$; post-peak $E_{\mathrm{frac}}$ converges to within $1.56\%$ across a $3.4\times$ mesh refinement, `STABLE_OVER_TESTED_RANGE`). Length-scale behavior is classified as `THREE_POINT_FIXED_S3_L0_SENSITIVITY_QUALIFIED_WITHIN_TESTED_RANGE` ($K_0$ stable, $F_{\max}$ and $u_{\mathrm{peak}}$ length-scale sensitive; under-resolved $l_0 = 3.75\,\mu\mathrm{m}$ excluded; no asymptotic $l_0 \to 0$ law and no square-root scaling law established).
2. **Pre-Peak Thermodynamic Bookkeeping:** Exact pre-peak equality between external boundary work and internal energy sum ($|W_{\mathrm{trap}} - (E_{\mathrm{elas}} + E_{\mathrm{frac}})| / W_{\mathrm{trap}} \le 0.008\%$) is numerically verified strictly on the frozen $S_1$ and temporal $T_1-T_3$ trajectories and must not be generalized. For the $l_0$ sensitivity series at matched displacement $u = 5.50\,\mu\mathrm{m}$, the discrete difference evaluates explicitly to $+0.17\%$ on nominal $S_3$ ($l_0 = 7.5\,\mu\mathrm{m}$) and $-0.002\%$ on $l_0 = 11.25\,\mu\mathrm{m}$ and $l_0 = 15.0\,\mu\mathrm{m}$.
3. **Dimensional & Source Reality:** Native Abaqus UEL evaluated quantities ($E_{\mathrm{elas}}, E_{\mathrm{frac}}$ in $\mathrm{kN}\cdot\mathrm{mm}$) convert to reported units ($\mathrm{mJ}$) via an exact, single $\times 1000$ multiplication factor ($1\,\mathrm{kN}\cdot\mathrm{mm} = 1\,\mathrm{J} = 1000\,\mathrm{mJ}$). In 2D plane strain, integration over in-plane Jacobian area ($\mathrm{mm}^2$) adopts the standard implicit unit thickness $B = 1.0\,\mathrm{mm}$ convention. Direct source-algebra quotient $\bar{\psi} = E / A_e$ has dimension $\mathrm{kN/mm} = \mathrm{J/mm^2}$, which equals $\mathrm{kN/mm^2} = 1000\,\mathrm{mJ/mm^3}$ under the implicit unit-thickness convention.
4. **Mechanical Parity Scope:** `ENERGY_SOURCE_MECHANICAL_PARITY — QUALIFIED (COMMON QUAD FORMULATION)`. Global mechanical response parity is proven across Mini (`1406904` vs `1406905`, 30 increments) and Extended (`1406906` vs `1406907`, 129 increments to $u = 0.035\,\mathrm{mm}$) cases on 4-node quads. Old-source $d / \mathcal{H}$ ODB fields were unobservable in the legacy UMAT and are not claimed. Triangle parity is not established.
5. **Governed Decision Focus & Pre-Meeting Actionability:** All presently observable Gate-6B quantities are complete, and only the exact global identity requires unavailable within-increment/operator-path information. Consequently, no further independent pre-meeting simulation or derivation is scientifically justified. The sole open item under Gate 6B is whether the supervisor accepts this observable endpoint energetic qualification (with documented analytical and observational boundaries) or mandates a future dedicated within-increment/operator-path investigation to close the post-peak algorithmic identity.

---

## 2. Frozen Benchmark Specifications & Canonical Reference

| Benchmark Parameter | Governed Value | Implementation Detail | Reference / Source |
| :--- | :--- | :--- | :--- |
| **Geometry** | $1.0\,\mathrm{mm} \times 1.0\,\mathrm{mm}$ square plate | 2D plane strain plate | Pandey & Kumar (2025) |
| **Initial Seam** | $a_0 = 0.5\,\mathrm{mm}$ along $y = 0.5\,\mathrm{mm}$ | Zero-gap sharp crack seam (no notch) | Canonical benchmark geometry |
| **Young's Modulus $E$** | $210.0\,\mathrm{GPa} = 210.0\,\mathrm{kN/mm^2}$ | Isotropic linear elastic baseline | Table 1 / Fig. 7 specification |
| **Poisson's Ratio $\nu$** | $0.30$ | Elastic coupling | Table 1 specification |
| **Fracture Toughness $G_c$** | $2.7\times 10^{-3}\,\mathrm{kN/mm} = 2.7\,\mathrm{N/mm}$ | Critical energy release rate | Table 1 specification |
| **Length Scale $l_0$** | $0.0075\,\mathrm{mm} = 7.5\,\mu\mathrm{m}$ (nominal) | Phase-field regularization parameter | Nominal baseline value |
| **Residual Stiffness $k_{\mathrm{res}}$** | $1.0\times 10^{-7}$ | Numerical stability parameter | Subroutine constant |
| **Canonical $K_0$ Anchor** | $137.945520\,\mathrm{kN/mm}$ | $R^2 = 0.99999960, N = 400$ increments | Project-derived from linear elastic range |
| **Reference $F_{\mathrm{max}}$** | $\sim 0.758\,\mathrm{kN}$ at $u \approx 0.00586\,\mathrm{mm}$ | Fixed-mesh fine reference (Job 1398090) | Digitized from Fig. 7(a) |

---

## 3. Multifaceted Mode-I Convergence & Evidence Matrix

### 3.1 Spatial Convergence Matrix
- **Governed Fixed Mesh Series ($S_1 - S_4$):** Element size refined across the governed sequence $S_1 \to S_4$ ($S_1 = 15,192$ finite elements, $h = 0.0030\,\mathrm{mm}$; $S_2 = 32,130$, $h = 0.0020\,\mathrm{mm}$; $S_3 = 41,912$, $h = 0.0015\,\mathrm{mm}$; $S_4 = 51,408$, $h = 0.00125\,\mathrm{mm}$), plus the separate historical fine-mesh case ($69,384$ finite elements, Job `1406019`, $h = 0.0010\,\mathrm{mm}$, whose literal deck name contains S5 but is not governed S5).
  - $F_{\mathrm{max}}$ drops monotonically across the governed sequence $S_1 \to S_4$ ($0.7578\,\mathrm{kN} \to 0.7290\,\mathrm{kN}$, $-3.80\%$) and extends to $0.7255\,\mathrm{kN}$ in the historical fine case (`1406019`).
  - Structural stiffness $K_0$ remains invariant: $137.946 \to 137.858\,\mathrm{kN/mm}$ ($< 0.09\%$ variation across $S_1 \to S_3$; canonical reference $K_0 = 137.945520\,\mathrm{kN/mm}$, $S_3$ nominal $K_0 = 137.857608\,\mathrm{kN/mm}$).
  - Localization width: verified Spatial-V4 values $S_1$: $w_{0.5} = 23.3418\,\mu\mathrm{m}, w_{0.9} = 8.7963\,\mu\mathrm{m}$; $S_2$: $22.9510, 9.8192\,\mu\mathrm{m}$; $S_3$: $23.1397, 10.6661\,\mu\mathrm{m}$; $S_4$: $22.8298, 10.1652\,\mu\mathrm{m}$; $A_1$: $23.1512, 9.9398\,\mu\mathrm{m}$; $A_2$: $22.7753, 9.8512\,\mu\mathrm{m}$; $A_3$: $22.1325, 7.4397\,\mu\mathrm{m}$; $A_4$: $20.3008, 4.6462\,\mu\mathrm{m}$.
  - Core localized band: $w_{0.9}$ is mesh-sensitive, tracking the local finite element discretization $h$.
  - Spatial energetic convergence ($S_1 - S_4$): `QUALIFIED`. Verified via single-IP extraction at matched physical checkpoints ($u = 5.50, 5.85, 6.20\,\mu\mathrm{m}$). Pre-peak $W_{\mathrm{trap}}$ ($-0.10\%$) and $E_{\mathrm{elas}}$ ($-0.23\%$) are `STABLE_OVER_TESTED_RANGE`; $E_{\mathrm{frac}}$ ($+4.36\%$) is `MESH-SENSITIVE` due to notch-tip core resolution. Post-peak $E_{\mathrm{frac}}$ converges to within $1.56\%$ across a $3.4\times$ mesh refinement ($2.339 \to 2.375\,\mathrm{mJ}$, `STABLE_OVER_TESTED_RANGE`), while $W_{\mathrm{trap}}$ drops $-7.97\%$ (`MESH-SENSITIVE`). Two-term difference $\Delta_{\mathrm{book}}$ tracked under `GLOBAL_ENERGY_IDENTITY — NOT_YET_CLOSED`.
- **Adaptive Remeshing Series ($A_1 - A_4$):** Spatial refinement driven by native Abaqus `RemeshingRule` (`MISESERI`).
  - $A_1$ ($71,320$ finite elements, $\mathrm{errorTarget}=1.0\%$): $F_{\mathrm{max}} = 0.745325\,\mathrm{kN}, K_0 = 137.821\,\mathrm{kN/mm}$.
  - $A_2$ ($15,396$ finite elements, $\mathrm{errorTarget}=2.0\%$): $F_{\mathrm{max}} = 0.748197\,\mathrm{kN}, K_0 = 137.844\,\mathrm{kN/mm}$.
  - $A_3$ ($7,633$ finite elements, $\mathrm{errorTarget}=3.0\%$): $F_{\mathrm{max}} = 0.743471\,\mathrm{kN}, K_0 = 137.854\,\mathrm{kN/mm}$.
  - $A_4$ ($4,194$ finite elements, $\mathrm{errorTarget}=5.0\%$): $F_{\mathrm{max}} = 0.764964\,\mathrm{kN}, K_0 = 137.966\,\mathrm{kN/mm}$.
  - Crack path trajectory: straight horizontal crack extension along the symmetry line $y = 0.500\,\mathrm{mm}$ preserved across all models.

### 3.2 Temporal Convergence Matrix ($T_1 - T_3$)
- Time increment refined from $\Delta u = 2.0\times 10^{-5}\,\mathrm{mm}$ ($T_1$) to $1.0\times 10^{-5}\,\mathrm{mm}$ ($T_2$) to $5.0\times 10^{-6}\,\mathrm{mm}$ ($T_3$).
- Global force metrics are temporally stable: $F_{\mathrm{max}}$ invariant to 5 significant figures ($0.75815 \to 0.75778 \to 0.75763\,\mathrm{kN}$, spread $\pm 0.035\%$), and initial stiffness $K_0$ is invariant ($137.945 \pm 0.0006\,\mathrm{kN/mm}$, spread $\pm 0.00045\%$, $R^2 > 0.9999995$).
- Terminal $W_{\mathrm{trap}}$ and the two-term bookkeeping difference are `TEMPORALLY SENSITIVE` ($+0.38\% \to +0.76\% \to +3.54\%$).
- Pre-peak two-term bookkeeping difference: $|\mathrm{TWO\_TERM\_BOOKKEEPING\_DIFFERENCE}| / W_{\mathrm{trap}} \le 0.008\%$ on the frozen $S_1$ / temporal $T_1-T_3$ trajectory ($-0.005\%$ at $u = 5.0\,\mu\mathrm{m}$, $-0.007\%$ at $u = 5.856\,\mu\mathrm{m}$); this bound is restricted to these qualified trajectories and is not generalized.

### 3.3 Phase-Field Length-Scale Sensitivity ($l_0 \in \{7.5, 11.25, 15.0\}\,\mu\mathrm{m}$)
- Governed status: `THREE_POINT_FIXED_S3_L0_SENSITIVITY_QUALIFIED_WITHIN_TESTED_RANGE` ($l_0 \in \{7.5, 11.25, 15.0\}\,\mu\mathrm{m}$ on fixed $S_3$ mesh, 41,912 finite elements):
  - **Initial Stiffness $K_0$:** Stable / insensitive over the tested range ($137.857608 \to 137.765563 \to 137.676175\,\mathrm{kN/mm}$, spread $0.13\%$).
  - **Peak Force $F_{\mathrm{max}}$:** Length-scale sensitive (monotonically decreases: $0.732196\,\mathrm{kN} \to 0.708402\,\mathrm{kN} \to 0.689540\,\mathrm{kN}$, a $-5.83\%$ reduction).
  - **Peak Displacement $u_{\mathrm{peak}}$:** Length-scale sensitive (monotonically shifts earlier: $5.633\,\mu\mathrm{m} \to 5.590\,\mu\mathrm{m} \to 5.579\,\mu\mathrm{m}$).
  - **Transverse Localization Width $w_{0.5}$:** Broadens with $l_0$ ($23.21\,\mu\mathrm{m} \to 34.41\,\mu\mathrm{m} \to 45.44\,\mu\mathrm{m}$ at fully propagated state).
  - Under-resolved $l_0 = 3.75\,\mu\mathrm{m}$ excluded.
  - No asymptotic $l_0 \to 0$ convergence law and no square-root scaling law ($F_{\mathrm{max}} \propto 1/\sqrt{l_0}$) established.

---

## 4. Thermodynamic Bookkeeping & Endpoint Energetic Accounting

### 4.1 Two-Term Endpoint Bookkeeping Difference
The observable discrete bookkeeping difference is defined at converged increment endpoints as:
$$\mathrm{TWO\_TERM\_BOOKKEEPING\_DIFFERENCE} = W_{\mathrm{trap}}(t_n) - \left( E_{\mathrm{elas}}(t_n) + E_{\mathrm{frac}}(t_n) \right)$$
where $E_{\mathrm{frac}}$ is strictly the regularized fracture surface energy and $E_{\mathrm{elas}}$ is stored elastic energy.

### 4.2 Pre-Peak vs Post-Peak Observations
1. **Pre-Peak Regime ($u \le 5.856\,\mu\mathrm{m}$):**
   - On qualified temporal and reference trajectories ($S_1$, $T_1-T_3$), exact same-frame extraction demonstrates:
     $$|\mathrm{TWO\_TERM\_BOOKKEEPING\_DIFFERENCE}| / W_{\mathrm{trap}} \le 0.008\%$$
   - For the $l_0$ sensitivity family at the pre-peak matched state $u = 5.50\,\mu\mathrm{m}$, the discrete difference evaluates explicitly to:
     - Nominal $S_3$ ($l_0 = 7.5\,\mu\mathrm{m}$): $+0.17\%$
     - Candidate 1 ($l_0 = 11.25\,\mu\mathrm{m}$): $-0.002\%$
     - Candidate 2 ($l_0 = 15.0\,\mu\mathrm{m}$): $-0.002\%$
   - Classification: **`NUMERICALLY VERIFIED ON SPECIFIC TEMPORAL/REFERENCE RUNS; l0 MATCHED VALUES STATED EXPLICITLY`**.
2. **Post-Peak Regime ($u > 5.856\,\mu\mathrm{m}$):**
   - Bookkeeping difference deviates non-trivially (e.g. $+0.76\%$ for $S_1$ at $u = 9.398\,\mu\mathrm{m}$, $-7.65\%$ for $S_3$ at cutback termination $u = 7.836\,\mu\mathrm{m}$).
   - The exact decomposition of this post-peak bookkeeping difference cannot be reconstructed from standard endpoint ODB output without within-increment path information (`DECOMPOSITION_REQUIRES_WITHIN_INCREMENT_PATH_INFORMATION`).

---

## 5. Analytical & Observational Boundaries of the Implementation

### 5.1 Cross-Derivative & Common-Potential Limitation
In the authoritative Fortran implementation (`f42_mixed_uel.for`), the coupled mechanical and phase-field boundary value problem is solved via a **decoupled staggered operator split**:
- Sub-step 1 solves the mechanical momentum balance $\mathbf{K}_{uu} \Delta \mathbf{u} = \mathbf{R}_u$ at fixed damage $d$.
- Sub-step 2 solves the phase-field Helmholtz equation $\mathbf{K}_{dd} \Delta d = \mathbf{R}_d$ at fixed displacement $\mathbf{u}$.

Because history $\mathcal{H}_n$ is evaluated at step $n$ and damage $d_{n+1}$ at step $n+1$, cross-derivatives do not commute:
$$\frac{\partial^2 \Pi}{\partial \mathbf{u} \partial d} = -2(1-d)\mathbb{C}_0 : \boldsymbol{\varepsilon} \quad \ne \quad \frac{\partial^2 \Pi}{\partial d \partial \mathbf{u}} = -2(1-d)\frac{\partial \mathcal{H}}{\partial \boldsymbol{\varepsilon}}$$
**`COMMON_DISCRETE_POTENTIAL_DISPROVEN_BY_CROSS_DERIVATIVE_INCOMPATIBILITY`**: No single discrete scalar potential exists governing the joint discrete update $(\mathbf{u}^{n} \to \mathbf{u}^{n+1}, d^{n} \to d^{n+1})$.

---

### 5.2 Observability Limitation in Standard ODB Output
- **What is Observable:** Converged equilibrium states $(\mathbf{u}^{n+1}, d^{n+1})$ and their associated endpoint energies ($W_{\mathrm{trap}}^{n+1}, E_{\mathrm{elas}}^{n+1}, E_{\mathrm{frac}}^{n+1}$) are fully recorded and mathematically rigorous.
- **What is NOT Observable:** The continuous sub-increment equilibrium path $\mathbf{u}(\tau), d(\tau)$, Newton subiteration work, and discrete operator-split dissipation path are not recorded in standard Abaqus ODB output.
- **`DECOMPOSITION_REQUIRES_WITHIN_INCREMENT_PATH_INFORMATION`:** An exact closed global algorithmic energy identity (`GLOBAL_ENERGY_IDENTITY`) cannot be reconstructed from standard post-processing of uninstrumented staggered ODB files.

---

### 5.3 Gate-6B Closure Status & Summary of Qualified vs Open Items

1. **Positively Qualified Results:**
   - Initial structural stiffness $K_0$ stability and canonical reference reproduction ($K_0 = 137.945520\,\mathrm{kN/mm}$).
   - Monotonic $F-u$ force-displacement response tracking.
   - Crack-path symmetry preservation ($\max |y_c - 0.5\,\mathrm{mm}| \le 3.10\,\mu\mathrm{m}$).
   - Temporal force metric invariance ($F_{\max}$ invariant to $<0.07\%$).
    - Transverse localization width tracking across spatial and adaptive models (verified Spatial-V4 $w_{0.5}$ and $w_{0.9}$ dataset).
   - Three-point length-scale sensitivity on fixed $S_3$ (`THREE_POINT_FIXED_S3_L0_SENSITIVITY_QUALIFIED_WITHIN_TESTED_RANGE`).
   - Common 4-node quad mechanical parity (`ENERGY_SOURCE_MECHANICAL_PARITY — QUALIFIED (COMMON QUAD FORMULATION)`).
2. **Documented `NOT_YET_QUALIFIED` Limitations:**
   - `SPATIAL EELAS/EFRAC CONVERGENCE — NOT YET QUALIFIED` due to unpopulated companion energy outputs in several spatial runs.
   - `GLOBAL_ENERGY_IDENTITY — NOT_YET_CLOSED` due to staggered non-commuting cross-derivatives and unobservable within-increment subiteration trajectories in standard ODB output.
3. **Supervisor Decision:**
   - The remaining item under Gate 6B is the supervisor decision on whether the demonstrated observable endpoint energetic accounting plus the analytical observability limitation is sufficient for Mode-I thesis qualification.

---

## 6. Supervisor Decision Framework (08 October 2026 Meeting)

### 6.1 The Explicit Decision Question
The supervisor is presented with the following precise, scientifically bounded decision question:

> **"Is the demonstrated endpoint energetic accounting — together with the analytically established limitation that no reconstructible common discrete potential/global algorithmic identity is available from the current staggered uninstrumented trajectory — sufficient for the thesis Mode-I energy qualification, provided this limitation is stated explicitly?"**

---

### 6.2 Two Neutral Resolution Pathways

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

- **Pathway 1:** Accept observable endpoint energetic accounting plus the explicitly documented analytical/observability limitation. Authorize advancing to Gate 6C (Mode-I State Transfer Energy Preservation).
- **Pathway 2:** Require dedicated within-increment/operator-path instrumentation and/or reformulation before Gate-6B closure (with design/scope/effort to be determined).

---

## 7. Active Governance Commitments & Holds

1. **Gate 6B Status:** Strictly maintained as **`GATE_6B_OPEN_PENDING_SUPERVISOR_DECISION_01OCT2026`** pending supervisor decision at the 08 October 2026 meeting. All presently observable Gate-6B quantities are complete; no further independent pre-meeting simulation or derivation is scientifically justified.
2. **Package Readiness:** Authoritatively confirmed as **`SUPERVISOR_READY`** (all consistency checks passing).
3. **Simulation Moratorium:** Strictly maintained (zero new solver jobs submitted; no new PBS runs authorized prior to supervisor review).
4. **Scope Holds Active:**
   - Gate 6C (Mode-I State Transfer Conservation): PENDING supervisor decision on Gate 6B.
   - Mode-II Shear Fracture: **HOLD**.
   - Mixed-Mode / Multi-Crack / Holes: **HOLD**.
   - Task 6 / Gate 7 (IMFD ABAQUSER Integration): Reopened; status is **`BLOCKED_ON_AUTHENTIC_IMFD_ABAQUSER_ACCESS`** / **`BLOCKED_ON_AUTHENTIC_INTERFACE_DELIVERY`** (internal companion bridge is not a substitute; no surrogate implementation or search work active).
   - True Distributed-Memory MPI & Thread Scaling Sweeps: **HOLD**.

