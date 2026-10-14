# Mode-I Method C Gate 6C: Sequential Adaptive Remeshing & Nonmatching State Transfer Architecture

**Protocol Version:** 2  
**Date:** 2026-10-14  
**Author:** Gemini Antigravity  
**Task ID:** `F1446-MODE1-METHOD-C-INITIATION-AND-TRANSFER-FRAMEWORK`  
**Classification:** `METHOD_C_GATE6C_STATE_TRANSFER_FRAMEWORK_QUALIFIED`  
**Status:** `ACTIVE_DESIGN_AND_VERIFICATION`  

---

## 1. Problem Definition & State-Preservation Requirements

### A. Core Scientific Question
In the numerical simulation of brittle fracture using continuous phase-field models, localized mesh refinement is essential to resolve steep damage gradients ($\nabla d$) across the physical regularization scale $l_0$. Method B addressed this challenge via **offline error-guided pre-refinement**, where a fixed non-uniform discretization was generated before the fracture simulation using error indicator information from a coarse antecedent pre-analysis.

**Method C (Sequential Adaptive Remeshing)** extends this methodology into a sequential, multi-stage adaptive workflow:
$$\text{Solve Stage } k \longrightarrow \text{Evaluate Error / Damage Indicator} \longrightarrow \text{Generate Nonmatching Mesh } k+1 \longrightarrow \text{Transfer State Variables} \longrightarrow \text{Restart \& Continue}$$

The primary scientific question governing Method C is:
> *Can an Abaqus native remeshing cycle be performed during Mode-I crack evolution while preserving the mechanically and energetically relevant solution state on a new, nonmatching mesh, without introducing unphysical energy dissipation, artificial damage growth, or boundary force discontinuities?*

### B. Benchmark Boundary Value Problem
The framework is formulated exclusively on the qualified Pandey–Kumar (2025) Mode-I benchmark:
- **Geometry:** Square plate $\Omega = [0, 1]\,\text{mm} \times [0, 1]\,\text{mm}$ ($L = 1.0\,\text{mm}$, $W = 1.0\,\text{mm}$).
- **Pre-Existing Crack:** Sharp horizontal crack seam $a_0 = 0.5\,\text{mm}$ along $y = 0.5\,\text{mm}$, $0 \le x \le 0.5\,\text{mm}$ modeled as a zero-gap duplicate-node seam (54 duplicate node pairs, 108 flank nodes).
- **Boundary Conditions:**
  - Bottom edge ($y = 0$): Roller support ($u_y = 0$), pinned at origin ($(0, 0)$ with $u_x = 0$).
  - Top edge ($y = 1$): Monotonic displacement-controlled tension ($u_y$ prescribed via kinematic coupling to reference node 999999).
- **Material & Phase-Field Properties:**
  - Young's modulus: $E = 210.0\,\text{kN/mm}^2$ ($210\,\text{GPa}$)
  - Poisson's ratio: $\nu = 0.30$
  - Critical fracture energy release rate: $G_c = 2.7 \times 10^{-3}\,\text{kN/mm}$ ($2.7\,\text{N/mm}$)
  - Regularization length scale: $l_0 = 0.0075\,\text{mm}$ ($7.5\,\mu\text{m}$)
  - Numerical residual stiffness: $k_{\text{stab}} = 1.0 \times 10^{-7}$
- **Element Architecture:** 3-layer co-located finite element structure:
  - Layer 1: Phase-field UEL (JTYPE=1 quad, JTYPE=3 tri; active DOF 3)
  - Layer 2: Mechanical displacement UEL (JTYPE=2 quad, JTYPE=4 tri; active DOFs 1, 2)
  - Layer 3: Companion visualization UMAT (CPE4 quad, CPE3 tri; stress/strain and state recovery)

---

## 2. Fixed-Mesh Reference Anchor & Method B Baseline Comparison

To ensure quantitative rigor, all Method C transfer candidates are judged strictly against the established project anchors:

| Model Discretization | FE Count | Initial Stiffness $K_0$ [kN/mm] | Peak Force $F_{\max}$ [kN] | Peak Disp. $u_{\text{peak}}$ [mm] | Work $W_{\text{ext}}$ [mJ] | Plateau ($0.5-0.6\,\text{kN}$) | Status |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Canonical Reference (Job 1398090)** | $15{,}192$ | $137.9455$ | $0.757778$ | $0.005857$ | $2.3587$ | None | Canonical Anchor |
| **Original Method B (Job 1411934)** | $14{,}677$ | $137.8919$ ($-0.039\%$) | $0.743015$ ($-1.95\%$) | $0.005700$ | $3.3319$ ($+41.2\%$) | Severe ($u \in [0.006, 0.0085]$) | Coarse Ligament Defect |
| **Corrected Method B (Job 1412465)** | $14{,}483$ | $137.9096$ ($-0.026\%$) | $0.743701$ ($-1.86\%$) | $0.005733$ | $2.2674$ ($-3.87\%$) | Eliminated ($F < 0.0021\,\text{kN}$) | Frozen Method B Target |

---

## 3. Forensic Audit of Existing Method C Gate C1 V2 (Job 1412464)

### A. Execution & Mechanical Summary
In Task F1435–F1436, Method C Gate C1 V2 was executed on cluster node `mnode097/0` under PBS Job ID `1412464.mmaster02` (`submit_M1_RECIP_2906_CONTINUATION_V2.pbs`):
- **Recipient Mesh:** $2{,}906$ finite elements ($2{,}818$ quads, $88$ triangles, $43{,}449$ co-located records).
- **Execution Trajectory:** Completed $5{,}058$ total increments ($10$ increments in Step 1 reload, $5{,}048$ increments in Step 2 continuation) in $01:03:25$ walltime with Abaqus Exit 0.
- **Step 1 Boundary:** Displacement ramped from $0.0$ to $u_y = 0.0050\,\text{mm}$, achieving $RF = 0.652467\,\text{kN}$ and stiffness $K_0 = 130.49\,\text{kN/mm}$.
- **Step Boundary Force Discontinuity:** Jump $\Delta RF = 9.25 \times 10^{-5}\,\text{kN} = 0.0925\,\text{N}$, passing the strict $0.005\,\text{kN}$ continuity threshold by a factor of $54\times$.
- **Step 2 Softening:** The model progressed past peak to complete post-peak softening with terminal residual force $RF_{\text{final}} = 0.0277\,\text{kN}$.

### B. Scientific Classification: Quasi-Static Reload vs. True Continuation
Job 1412464 demonstrated that history variable transfer via `*INITIAL CONDITIONS, TYPE=SOLUTION` successfully prevents premature damage accumulation during reloading. However, it revealed critical limitations:
1. **Unadapted Recipient Mesh:** The recipient mesh was the unrefined $2{,}906$-element coarse mesh ($h \approx 20\,\mu\text{m}$ to $3.75\,\mu\text{m}$). Consequently, in Step 2, delayed localization occurred, driving peak load up to $F_{\max} = 1.0868\,\text{kN}$ at $u_y = 0.009234\,\text{mm}$ ($+43.4\%$ above the reference $0.7578\,\text{kN}$).
2. **Reload Architecture (Not Seamless Continuation):** Step 1 did not continue from an existing non-zero displacement/stress state. Instead, it reloaded from $u_y = 0.0$ to $u_y = 0.0050\,\text{mm}$ over 10 artificial increments. While the boundary force matched, this is technically a **Quasi-Static Reload with Transferred History**, not genuine continuation from an in-flight solver checkpoint.
3. **Verdict:** Job `1412464.mmaster02` is permanently classified as `QUASI_STATIC_RELOAD_WITH_TRANSFERRED_HISTORY`. It validates the history transfer interface, but leaves genuine nonmatching adaptive continuation to be demonstrated.

---

## 4. Donor–Recipient Architecture & Nonmatching Mesh Generation

### A. Donor State Selection
To establish a rigorous, physically meaningful validation case, the donor state must satisfy:
1. **Linear-Elastic with Pre-Peak Incipient Damage:** The state must precede unstable crack propagation ($u_y \le 0.0055\,\text{mm}$) to avoid the chaotic dynamics of post-peak crack bifurcation or deep cutbacks.
2. **Standard Handoff Point:** Prescribed displacement $u_y = 0.0050\,\text{mm}$ (Increment 500 of Step 1 in $2{,}906$-FE coarse pre-analysis, or Increment 2000 of Step 1 in $14{,}677$-FE donor).
3. **Observable State Quantities:** At $u_y = 0.0050\,\text{mm}$, reaction force is $RF \approx 0.6531-0.6616\,\text{kN}$, peak phase-field damage is $d_{\max} \approx 0.3195$, crack extension is $\Delta a = 0.0\,\text{mm}$, and fracture energy is $E_{\text{frac}} \approx 0.0075\,\text{mJ}$.

### B. Native Nonmatching Mesh Generation
The recipient mesh must be generated strictly using Abaqus native tools without hardcoding the crack path:
1. Coarse pre-analysis calculates the linear-elastic continuum stress field.
2. Abaqus recovery-based error estimator evaluates the stress discretization indicator:
   $$\text{MISESERI} = \|\boldsymbol{\sigma}^* - \boldsymbol{\sigma}_h\|_{L_2}$$
3. Abaqus `RemeshingRule` calculates local sizing $h(x, y)$ under `UNIFORM_ERROR`.
4. `adaptiveRemesh` generates the new unstructured recipient mesh $\mathcal{M}_{\text{recip}}$.
5. The 3-layer co-located UEL structure is generated deterministically on $\mathcal{M}_{\text{recip}}$ with exact duplicate nodes along the crack slit.

---

## 5. Field-by-Field Transfer Mappings & Irreversibility Enforcement

Because Abaqus built-in `*MAP SOLUTION` is explicitly incompatible with User Elements (`*USER ELEMENT`), all solution mapping is performed by the dedicated, verified projection engine ([`scripts/state_transfer/mode1_state_transfer_engine.py`](file:///D:/Master%20thesis/Adaptive%20remeshing/scripts/state_transfer/mode1_state_transfer_engine.py)).

```
+-----------------------------------------------------------------------------------------+
|                               STATE TRANSFER ARCHITECTURE                               |
+-----------------------------------------------------------------------------------------+
|   Donor Mesh M_A (FE_A elements)            Recipient Mesh M_B (FE_B elements)         |
|   ==============================            ==================================         |
|   Nodes: Coordinates (X, Y)_A               Nodes: Coordinates (X, Y)_B                |
|     DOFs: u_x, u_y (Mech), d (Phase)   -->    DOFs: Initialized via Shape Functions   |
|                                                                                         |
|   Topology Guard: Split Slit Flanks         Topology Guard: Split Slit Flanks           |
|     y = 0.5, x <= 0.5 mm                      y = 0.5, x <= 0.5 mm                      |
|     UPPER nodes (y > 0.5)              -->    UPPER recipient nodes only                |
|     LOWER nodes (y < 0.5)              -->    LOWER recipient nodes only                |
|     LIGAMENT nodes (x > 0.5)           -->    Full intact ligament search               |
|                                                                                         |
|   Gauss Points: (x_g, y_g)_A                Gauss Points: (x_g, y_g)_B                  |
|     History H_A = max(psi_0^+, H_prior) -->   History H_B = HOST_NEAREST_GP(H_A)       |
|                                               Enforce H_B >= 0.0                        |
|                                                                                         |
|   State Variable Reconstruction             Input Deck Assembly                         |
|     SVARS(1..4)   = Strain eps_11             *INITIAL CONDITIONS, TYPE=DISPLACEMENT    |
|     SVARS(5..8)   = Stress sigma_11           *INITIAL CONDITIONS, TYPE=SOLUTION        |
|     SVARS(9..12)  = Transferred H_B           Wrapped N_BOTTOM / N_TOP boundary cards   |
|     SVARS(13..15) = Re-evaluated g(d), d      Seamless step ramping u_handoff -> u_end  |
+-----------------------------------------------------------------------------------------+
```

### A. Topological Slit Flank Guard
The crack seam at $y = 0.5\,\text{mm}$ for $x \in [0.0, 0.5]\,\text{mm}$ forms a physical displacement and phase discontinuity. If an upper recipient node were interpolated from lower donor elements, severe unphysical artificial crack-bridging stresses would result:
- **Element Centroid Partition:** Elements with centroid $y_c \ge 0.5\,\text{mm}$ are classified as `UPPER`; elements with $y_c < 0.5\,\text{mm}$ are `LOWER`.
- **Node Classification:**
  - Nodes with $x > 0.5 + 10^{-6}\,\text{mm}$ are `LIGAMENT` (intact material).
  - Nodes with $x \le 0.5 + 10^{-6}\,\text{mm}$ and $y > 0.5 + 10^{-6}\,\text{mm}$ are `UPPER`.
  - Nodes with $x \le 0.5 + 10^{-6}\,\text{mm}$ and $y < 0.5 - 10^{-6}\,\text{mm}$ are `LOWER`.
  - Nodes on the flank surfaces ($y = 0.5\,\text{mm}$, $x \le 0.5\,\text{mm}$) are partitioned strictly based on the flank of their connected elements.
- **Search Rule:** Upper recipient nodes search only upper donor elements; lower recipient nodes search only lower donor elements.

### B. Nodal Degree of Freedom Mapping ($u_x, u_y, d$)
For any recipient node $P = (x_B, y_B)$ belonging to flank $\mathcal{F}$:
1. Identify host donor element $e_A \in \mathcal{M}_{\text{donor}}$ of flank $\mathcal{F}$ such that $P \in \Omega_{e_A}$.
2. Invert physical coordinates $(x_B, y_B)$ to natural coordinates $(\xi, \eta)$ using Newton–Raphson iteration on:
   $$x_B = \sum_{i=1}^4 N_i(\xi, \eta) X_i^A, \quad y_B = \sum_{i=1}^4 N_i(\xi, \eta) Y_i^A$$
3. Interpolate primary nodal fields:
   $$u_x(P) = \sum_{i=1}^{N_{\text{nodes}}} N_i(\xi, \eta) u_{x,i}^A, \quad u_y(P) = \sum_{i=1}^{N_{\text{nodes}}} N_i(\xi, \eta) u_{y,i}^A, \quad d(P) = \sum_{i=1}^{N_{\text{nodes}}} N_i(\xi, \eta) d_i^A$$
4. **Physical Bounding:** Enforce $0.0 \le d(P) \le 1.0$.

### C. Integration-Point History Variable Mapping ($H$)
In the Miehe/Bourdin AT2 formulation, damage irreversibility is strictly enforced through the maximum historical undegraded elastic strain energy density:
$$H(t) = \max_{\tau \le t} \psi_0^+(\boldsymbol{\varepsilon}(\tau))$$
- In `f42_mixed_uel.for`, Phase elements (JTYPE=1, 3) read `SV_H_COMMITTED(PHYSIDX, KPT) = SVARS(8+KPT)` on Increment 1.
- For each recipient integration point $Q_B = (x_{g,B}, y_{g,B})$:
  1. Identify host donor element $e_A$.
  2. Map history variable using the qualified **Host Nearest Gauss Point Operator (`HOST_NEAREST_GP`)**:
     $$H(Q_B) = H(Q_A^*), \quad Q_A^* = \arg\min_{Q_A \in e_A} \|Q_B - Q_A\|$$
  3. **Non-Negativity Constraint:** Enforce $H(Q_B) \ge 0.0$.
  4. **Damage Irreversibility:** Ensure that on the recipient mesh:
     $$H(Q_B) \ge \psi_0^+(\boldsymbol{\varepsilon}(Q_B))$$
     guaranteeing that $\Delta H = 0$ during equilibrium iterations at $u_{\text{handoff}}$, preventing spurious artificial damage growth.

### D. Subroutine COMMON-Block Initialization State
Forensic source analysis of `f42_mixed_uel.for` confirms:
- At `LOP = 0` (Start of Analysis), subroutine `UEXTERNALDB` initializes all arrays in `COMMON /CB_STATE_TRANS/` (`SV_PHASE_COMMITTED`, `SV_PHASE_TRIAL`, `SV_H_COMMITTED`, `SV_H_TRIAL`, `SV_E_FRAC`, `SV_E_ELAS`) to ZERO.
- At `LOP = 1` (Start of Increment 1), `SV_H_COMMITTED` is populated from `SVARS(9..12)` (quad) or `SVARS(7..9)` (tri).
- **Critical Finding:** Nodal phase-field damage $d$ is NOT read from `SVARS` into the COMMON block; rather, $d$ is solved as an active degree of freedom (DOF 3) from the Helmholtz weak form at each Newton iteration:
  $$((G_c/l_0 + 2H) d - G_c l_0 \nabla^2 d = 2H)$$
- Consequently, providing both `*INITIAL CONDITIONS, TYPE=DISPLACEMENT` (for initial trial $d$ and kinematic displacement $u$) and `*INITIAL CONDITIONS, TYPE=SOLUTION` (for internal history $H$) is necessary to establish full numerical equilibrium without convergence failure.

---

## 6. Quantitative Acceptance Criteria for Method C (Gate 6C)

To prevent arbitrary qualification, Method C state transfer must satisfy seven pre-declared quantitative acceptance thresholds:

```
+----------------------------------------------------------------------------------------------------------+
|                                    GATE 6C ACCEPTANCE THRESHOLDS MATRIX                                  |
+----------------------------------------------------------------------------------------------------------+
| Metric                              Extraction Formulation                            Acceptance Bound   |
+----------------------------------------------------------------------------------------------------------+
| 1. Displacement Field L2 Error      ||u_recip - u_donor||_L2 / ||u_donor||_L2         <= 1.0 %           |
| 2. Peak Phase-Field Damage Error    |max(d_recip) - max(d_donor)|                     <= 0.020 (2.0%)    |
| 3. Integrated Damage Error          |int d_recip dOmega - int d_donor dOmega| / I_d   <= 5.0 %           |
| 4. History Non-Negativity           min(H_recip(x_g))                                 >= 0.0 (Strict)    |
| 5. Step Boundary Force Continuity   |RF_start(Step 2) - RF_end(Step 1)|               <= 0.005 kN (5.0 N)|
| 6. Global Energy Difference         |E_total,recip - E_total,donor| / E_total,donor   <= 5.0 %           |
| 7. Initial Elastic Stiffness        |K_0,recip - K_0,ref| / K_0,ref                   <= 1.0 %           |
+----------------------------------------------------------------------------------------------------------+
```

### Detailed Rationale for Tolerances:
1. **Displacement $L_2 \le 1.0\%$:** Standard finite element shape function projection between smooth compatible fields maintains $>99\%$ $L_2$ norm fidelity.
2. **Peak Damage $\le 0.02$ ($2\%$):** At $u_y = 0.0050\,\text{mm}$, peak damage is $d_{\max} \approx 0.3195$. A change of $\pm 0.02$ preserves the pre-peak physical state without triggering premature localization.
3. **Integrated Damage $\le 5.0\%$:** Due to convex chordal interpolation across unstructured elements with varying size $h$, discrete integration of $d$ exhibits a known small coarsening/refinement bias ($\Delta I \approx \frac{h^2}{6 l_0} d_{\max}$); a $5.0\%$ threshold accommodates this geometric artifact.
4. **Boundary Force Continuity $\le 0.005\,\text{kN}$ ($5.0\,\text{N}$):** At $RF \approx 0.65\,\text{kN}$, a force jump $< 5\,\text{N}$ ($<0.77\%$) ensures $C^0$ load continuity without solver shock.

---

## 7. Distinguishing Genuine Continuation from Quasi-Static Reload

To maintain scientific integrity in the Master's thesis, the distinction between a reload and true sequential continuation must be rigorously enforced:

| Characteristic | Quasi-Static Reload (Gate C1 V2) | Genuine Adaptive Continuation (Target Method C) |
| :--- | :--- | :--- |
| **Initial Kinematic State** | $u_y = 0.0$, $\boldsymbol{\varepsilon} = 0$, $\boldsymbol{\sigma} = 0$ at $t = 0$ | $u_y = u_{\text{handoff}}$, $\boldsymbol{\varepsilon} = \boldsymbol{\varepsilon}_{\text{handoff}}$, $\boldsymbol{\sigma} = \boldsymbol{\sigma}_{\text{handoff}}$ |
| **Step 1 Function** | Ramps displacement from $0$ to $u_{\text{handoff}}$ | Single static equilibrium / initial check increment |
| **External Work $W_{\text{ext}}$** | Re-accumulates from $0.0\,\text{mJ}$ during Step 1 | Inherits $W_{\text{ext,donor}} = \int_0^{u_{\text{handoff}}} F \, du$ |
| **Phase-Field Evolution** | Re-solves $d$ from $0 \to d_{\text{donor}}$ under frozen $H$ | Starts directly from mapped $d(x, y)$ |
| **Computational Overhead** | Incurs cost of re-solving elastic ramp | Continues directly into fracture propagation |
| **Scientific Claim** | `RELOAD_WITH_COMMITTED_HISTORY` | `SEQUENTIAL_ADAPTIVE_CONTINUATION` |

If solver limitations (e.g. Abaqus user element displacement initial condition handling) require a rapid reload step to achieve equilibrium, that step must be explicitly documented as a *re-equilibration phase*, rather than disguised as seamless runtime continuation.

---

## 8. Implementation Verification & Unit Test Coverage

The Method C architecture is verified by the dedicated test suite:
[`tests/unit/test_mode1_f1446_method_c_transfer_framework.py`](file:///D:/Master%20thesis/Adaptive%20remeshing/tests/unit/test_mode1_f1446_method_c_transfer_framework.py)

### Tested Verifications:
1. `test_f1446_method_b_completion_and_freeze_record`: Confirms Method B is classified as `METHOD_B_SCIENTIFIC_OBJECTIVE_COMPLETED_WITH_PARTIAL_HORIZON_LIMITATION` and protected from modifications.
2. `test_f1446_human_authorization_recorded`: Verifies the explicit human authorization of 14 October 2026 is recorded separately from pending supervisor Gate 6B sign-off.
3. `test_f1446_gate_c1_v2_audit_and_reload_classification`: Audits Job 1412464 evidence and confirms classification as `QUASI_STATIC_RELOAD_WITH_TRANSFERRED_HISTORY`.
4. `test_f1446_transfer_engine_integrity_and_hash`: Confirms `mode1_state_transfer_engine.py` exists, parses 3-layer co-located decks, and enforces slit topology.
5. `test_f1446_frozen_uel_source_hash`: Verifies authoritative UEL hash `CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6`.
6. `test_f1446_acceptance_thresholds_definition`: Verifies mathematical definition of the 7 quantitative acceptance criteria.

---

## 9. Summary & Next Steps

1. **Method B Status:** Scientifically closed and frozen with partial-horizon limitation. Plateau elimination and external work reduction are formally established.
2. **Method C Framework:** State transfer architecture, slit-flank topological guards, field mapping operators, and quantitative acceptance thresholds are fully defined.
3. **Next Recommended Task (`F1447`):** Execute a lightweight offline state-projection benchmark using `mode1_state_transfer_engine.py` mapping donor state at $u_y = 0.0050\,\text{mm}$ onto a refined native recipient mesh, evaluate field differences against the acceptance criteria, and perform a cluster datacheck prior to production solve.
