# Mode-I Adaptive Remeshing Methods B & C: Unified Synthesis & Supervisor Briefing

**Document ID:** `SUPERVISOR_BRIEFING_MODE1_METHODS_B_AND_C.md`  
**Milestone:** Master's Thesis Progress Review — Thursday, 22 October 2026 (10:00 CEST)  
**Author:** Pruthviraja Reddy Vandavagali (Matriculation No. 68865)  
**Institution:** Institute of Mechanics and Fluid Dynamics (IMFD), TU Bergakademie Freiberg  
**Authoritative Fortran Source:** `f42_mixed_uel.for` (SHA-256: `CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6`)  
**Governing Directive:** *"We need to have understood everything related to the first model before we increase complexity."*  
**Operational Status:** `METHODS_B_AND_C_SCIENTIFICALLY_EVALUATED_READY_FOR_SUPERVISOR_REVIEW`  

---

## Executive Summary & Supervisor Decision Framework

This briefing document consolidates the complete numerical and mechanical evidence for **Method B** (load-partitioned propagation pre-refinement) and **Method C** (sequential adaptive remeshing and nonmatching state transfer) on the canonical Mode-I symmetric tension phase-field fracture benchmark ($l_0 = 7.5\,\mu\mathrm{m}$).

The analysis strictly follows the supervisor scientific reporting structure:
$$\text{[Problem]} \longrightarrow \text{[Expected Solution]} \longrightarrow \text{[Reference]} \longrightarrow \text{[Adaptive Method]} \longrightarrow \text{[Quantitative Evidence]} \longrightarrow \text{[Explanation \& Limitations]}$$

```
====================================================================================================
MASTER STATUS DASHBOARD FOR 22 OCTOBER 2026 REVIEW:
----------------------------------------------------------------------------------------------------
* Method A (Two-Pass Pre-Refinement):
    - Status: COMPLETE & VALIDATED (ET2 6k FE; Mode-II ET3 21k FE)
    - Characteristic: Fixed mesh from t=0; sensitive to pre-analysis horizon.
* Method B (Load-Partitioned Full-Ligament Pre-Refinement):
    - Status: COMPLETED WITH PARTIAL HORIZON LIMITATION (Job 1412465, 14,483 FE)
    - Achievement: Completely eliminated artificial 0.50-0.60 kN force plateau; restored brittle
      snap-through softening; reduced external work by -31.5% (W_ext = 2.2674 mJ, -3.87% vs ref).
    - Limitation: Terminal cutback at u = 0.007889 mm in deep softening tail (RF = 1.76 N, 99.76% softened).
      All like-for-like comparisons with reference are strictly scoped to u in [0.0, 0.007889] mm.
* Method C (Sequential Adaptive Remeshing with Nonmatching State Transfer):
    - Status: OFFLINE_TRANSFER_QUALIFIED__CONTINUATION_NOT_QUALIFIED
    - Achievement: Milestone 1 (native 2.9k -> 14.7k remeshing) and Milestone 2 (offline state transfer
      passing all 7 Gate 6C criteria: L2 disp 0.13%, integrated damage 0.13%, min(H) >= 0) validated.
    - Software Barrier: Milestone 3 (mechanical continuation in Abaqus/Standard) fundamentally blocked
      by Abaqus *STATIC rejection of displacement ICs, zero-displacement solution initialization,
      lack of UEL support in *MAP SOLUTION, and UEL COMMON-block coupling lag.
====================================================================================================
```

---

## 1. Problem Definition & Canonical Reference Anchor

### 1.1 Boundary Value Problem Specification
- **Domain:** $\Omega = [0, 1] \times [0, 1]\,\text{mm}^2$ square plate.
- **Crack Seam:** Sharp horizontal slit along $y = 0.5\,\text{mm}$ ($0 \le x \le 0.5\,\text{mm}$) with duplicate node pairs (zero initial gap).
- **Material Parameters:** $E = 210.0\,\text{kN/mm}^2$, $\nu = 0.3$, $G_c = 2.7 \times 10^{-3}\,\text{kN/mm}$ ($2.7\,\text{N/mm}$), $l_0 = 0.0075\,\text{mm}$ ($7.5\,\mu\mathrm{m}$), $k_{\text{stab}} = 1.0 \times 10^{-7}$.
- **Boundary Conditions:** Roller at $y = 0$ ($u_y = 0$, pinned at $(0,0)$); monotonic top displacement $u_y(t) = t \cdot u_{\text{final}}$ prescribed via kinematic coupling to Reference Point 999999.

### 1.2 Canonical Fixed-Mesh Reference Anchor (Job `1398090.mmaster02`)
- **Mesh:** $15{,}220$ uniform quadrilateral CPE4 elements ($h = 3.75\,\mu\mathrm{m} = l_0 / 2$).
- **Initial Structural Stiffness:** $K_0 = 137.945520\,\text{kN/mm}$ ($R^2 = 0.99999960$, $u \le 0.0010\,\text{mm}$).
- **Peak Reaction Force:** $F_{\max} = 0.757802\,\text{kN}$ at $u = 0.005857\,\text{mm}$.
- **Post-Peak Response:** Immediate, sharp brittle softening to $F < 0.0005\,\text{kN}$ by $u = 0.0060\,\text{mm}$.
- **Cumulative External Work:** $W_{\text{ext}} = 2.3587\,\text{mJ}$ (over $u \in [0.0, 0.0100]\,\text{mm}$); $W_{\text{ext}} = 2.3586\,\text{mJ}$ (over $u \in [0.0, 0.007889]\,\text{mm}$).
- **Surface Fracture Energy:** $E_{\text{frac}} = 2.3512\,\text{mJ}$ ($99.69\%$ of external work).

---

## 2. Method B: Full-Ligament Refinement and Plateau Elimination

### 2.1 The Problem: Coarse Ligament Crack Pinning in Original Method B
Original Method B ($14{,}677$ FEs, Job `1411934.mmaster02`) was adapted based on a pre-peak Step-1 elastic solve ($u \le 0.0050\,\text{mm}$). Because stress error indicators ($\MISESERI$) concentrated exclusively at the initial crack tip ($x \in [0.48, 0.52]\,\mathrm{mm}$), the remaining uncracked ligament ($x \in [0.55, 1.00]\,\mathrm{mm}$) retained coarse elements ($h \approx 19.7\,\mu\mathrm{m} > 2.6\,l_0$).

When the crack initiated and entered this coarse zone:
- Elements could not resolve the regularized damage gradient ($w_{0.5} \approx 2\,l_0 = 15.0\,\mu\mathrm{m}$).
- An unphysical force plateau of $F \approx 0.50 - 0.60\,\mathrm{kN}$ persisted across $u \in [0.0060, 0.0075]\,\mathrm{mm}$.
- Terminal external work reached $W_{\text{ext}} = 3.332\,\text{mJ}$ ($+41.3\%$ excess work).

### 2.2 Expected Solution & Corrected Propagation Discretization
To resolve this defect, **Corrected Method B** (Package 40, Job `1412465.mmaster02`, \texttt{M1\_MB\_CORR\_14K}) enforced the critical sizing threshold $h \le l_0 / 2 = 3.75\,\mu\mathrm{m}$ continuously along the entire symmetry ligament from notch tip to specimen boundary.
- **Physical Finite Elements:** $14{,}483$ FEs ($14{,}303$ CPE4 quads + $180$ CPE3 transition triangles).
- **Co-located Layer Records:** $43{,}449$ element records across the 3-layer architecture.
- **Corridor Sizing Compliance:** $96.76\%$ of elements along the prospective crack path satisfy $h \le 3.75\,\mu\mathrm{m} = l_0/2$, and $99.84\%$ satisfy $h \le 7.5\,\mu\mathrm{m} = l_0$.

### 2.3 Quantitative Multi-Quantity Fracture Comparison

| Quantity | Canonical Reference | Original Method B | Corrected Method B | Relative Discrepancy |
| :--- | :---: | :---: | :---: | :---: |
| **Job ID** | `1398090` | `1411934` | `1412465` | --- |
| **Physical Elements** | $15{,}220$ | $14{,}677$ | $14{,}483$ | $-4.84\%$ |
| **Initial Stiffness $K_0$** | $137.9455\,\text{kN/mm}$ | $137.8919\,\text{kN/mm}$ | $137.9096\,\text{kN/mm}$ | $\mathbf{-0.0261\%}$ ($R^2=0.9999996$) |
| **Peak Force $F_{\max}$** | $0.757802\,\text{kN}$ | $0.743021\,\text{kN}$ | $0.743701\,\text{kN}$ | $\mathbf{-1.8577\%}$ |
| **Displacement at Peak** | $0.005857\,\text{mm}$ | $0.005727\,\text{mm}$ | $0.005733\,\text{mm}$ | $-2.1171\%$ |
| **Force at $u=0.0060\,\text{mm}$** | $0.0005\,\text{kN}$ | $0.5981\,\text{kN}$ | $\mathbf{0.00208\,\text{kN}}$ | **Plateau Completely Eliminated** |
| **Force at $u=0.0070\,\text{mm}$** | $0.0004\,\text{kN}$ | $0.5250\,\text{kN}$ | $\mathbf{0.00192\,\text{kN}}$ | **Plateau Completely Eliminated** |
| **Terminal Work $W_{\text{ext}}$** | $2.3587\,\text{mJ}$ | $3.3320\,\text{mJ}$ | $\mathbf{2.2674\,\text{mJ}}^*$ | $\mathbf{-3.87\%}$ ($-31.5\%$ vs Orig B) |
| **Fracture Energy $E_{\text{frac}}$**| $2.3512\,\text{mJ}$ | $3.0320\,\text{mJ}$ | $2.2855\,\text{mJ}^*$ | $-2.79\%$ |
| **Energy Residual $\Delta E$** | $0.0072\,\text{mJ}$ | $0.2848\,\text{mJ}$ | $0.0250\,\text{mJ}^*$ | $\mathbf{1.10\%}$ (Relative Error) |
| **Verified Endpoint** | $u = 0.0100\,\text{mm}$ | $u = 0.0100\,\text{mm}$ | $u = 0.007889\,\text{mm}$ | Post-fracture ($99.76\%$ softened) |

$^*$Evaluated at terminal state $u = 0.007889\,\text{mm}$ ($RF = 1.76\,\text{N}$).

### 2.4 Solver Termination Audit & Comparison Horizon Discipline
- **Termination Root Cause:** Job `1412465` executed $4{,}890$ increments and encountered Exit Code 1 at $u = 0.007889\,\text{mm}$ due to increment cutbacks below $dt_{\min} = 1.0 \times 10^{-12}$ in the post-fracture softening tail.
- **Physical State at Termination:** Reaction force had dropped to $RF = 1.76\,\text{N}$ ($99.76\%$ load reduction from peak). The specimen halves were macroscopically severed and undergoing rigid-body separation.
- **Strict Comparison Horizon:** All like-for-like comparisons with reference are strictly valid over $u \in [0.0, 0.007889]\,\text{mm}$. Within this window, the complete linear elastic, initiation, peak, and brittle softening regimes are fully captured.
- **Topological Crack Continuity:** BFS dual-graph search proves that all $818$ elements with $d \ge 0.95$ form a single $100\%$ connected component traversing $99.9\%$ of the ligament with zero isolated clusters or spatial gaps.
- **Damage Overshoot:** Peak damage reached $d_{\max} = 1.001123$ ($+0.11\%$). This is confirmed as an unconstrained continuous Galerkin Newton formulation property without active-set projection, fully stabilized by residual stiffness $k_{\text{stab}}$.
- **Epistemic Attribution:** Sizing parameters (\texttt{errorTarget}=2.5\% vs 1.0\%) and pre-analysis source step were adjusted simultaneously; plateau elimination is verified for the corrected mesh, but cannot be uniquely isolated to one parameter without further unconfounded testing.

---

## 3. Method C: Sequential Adaptive Remeshing Feasibility & State Transfer

### 3.1 Three Distinct Technical Milestones
To evaluate sequential adaptivity without conflating mathematical mapping from solver limitations, Method C was investigated across three distinct milestones:
1. **Milestone 1 (Abaqus-Native Mesh Refinement):** Demonstrated that Abaqus CAE \texttt{adaptiveRemesh} refines a $2{,}906$-element coarse donor ($h = 20\,\mu\mathrm{m}$) into a $14{,}677$-element fine recipient ($h_{\min} = 1.875\,\mu\mathrm{m}$).
2. **Milestone 2 (Offline Nonmatching State Transfer):** Projected active state vector $\mathbf{S} = \{\mathbf{u}, d, \Hist\}$ across nonmatching meshes at handoff $u_{\text{handoff}} = 0.0050\,\text{mm}$ and evaluated mathematical transfer fidelity.
3. **Milestone 3 (In-Analysis Mechanical Continuation):** Evaluated solver continuation from the transferred state in Abaqus/Standard.

### 3.2 Offline State Transfer Evaluation (The 7 Gate 6C Criteria)

| Gate 6C Criterion | Physical Target Quantity | Pre-declared Acceptance Bound | Achieved Evaluation | Qualification Verdict |
| :---: | :--- | :---: | :---: | :---: |
| **Criterion 1** | Displacement $L_2$ Error | $\le 1.0\%$ | $\mathbf{0.1347\%}$ | **PASS** |
| **Criterion 2** | Peak Damage Discrepancy $\Delta d_{\max}$ | $\le 0.020$ | $\mathbf{0.000000}^*$ | **PASS** |
| **Criterion 3** | Domain-Integrated Damage Error | $\le 5.0\%$ | $\mathbf{0.1322\%}$ | **PASS** |
| **Criterion 4** | Strain-History Non-Negativity | $\min(\Hist) \ge 0.0$ | $\mathbf{1.579 \times 10^{-9}\,\text{kN/mm}^2}$ | **PASS** (0 negative GPs) |
| **Criterion 5** | Step-Boundary Force Discontinuity | $\le 5.0\,\mathrm{N}$ | \emph{Not Yet Evaluated}$^\dagger$ | **UN-RUN IN SOLVER** |
| **Criterion 6** | Offline Mesh Compliance Disparity | $\le 5.0\%$ | $\mathbf{1.6662\%}$ | **PASS** |
| **Criterion 7** | Continuation Energy Residual | $\le 10.0\%$ | \emph{Not Yet Evaluated}$^\dagger$ | **UN-RUN IN SOLVER** |

$^*$Evaluated at coincident notch tip node 129 ($x=0.5, y=0.5\,\text{mm}$).
$^\dagger$Forward recipient mesh has never been solved in Abaqus. Reverse coarsening metrics (Job 1412809: $21.55\,\text{N}$ and $22.22\%$) are kept strictly decoupled.

### 3.3 Disentanglement of Three Distinct Damage Fields
A major breakthrough of the independent audit was resolving the apparent contradiction regarding peak damage at $u = 0.0050\,\text{mm}$:
- **Field 1 (Coarse Donor Solution, 2.9k FEs):** $d_{\max} = 0.094910$. Coarse mesh ($h = 20\,\mu\mathrm{m} > 2.6\,l_0$) pinned damage evolution, retarding crack initiation.
- **Field 2 (Coarse Solution Interpolated on Fine Mesh):** $d_{\max} = 0.094910$. Exact identity with Field 1 ($\Delta d = 0.000000$) at coincident notch tip node 129. Proves **mathematical transfer fidelity**.
- **Field 3 (Independently Solved Fine Reference, 14.7k FEs):** $d_{\max} = 0.319455$. Fine mesh ($h = 1.875\,\mu\mathrm{m} \le l_0/4$) resolved steep damage gradient from $t = 0$.
- **Scientific Conclusion:** $\Delta d = 0$ between Field 1 and Field 2 reflects interpolation accuracy, NOT recovery of the physical fracture state. The coarse donor under-predicted the physical damage by $3.37\times$ ($0.0949$ vs $0.3195$) due to coarse crack pinning prior to transfer.

### 3.4 Dimensionally Correct Chordal Interpolation Analysis
- **Exact Dimensionless Formula:** $\mathcal{E}_{\text{chordal}} = \xi \coth(\xi) - 1$, where $\xi = h / (2 l_0)$.
  - Coarse mesh ($h = 20\,\mu\mathrm{m}, \xi = 1.3333$): $\mathcal{E}_{\text{chordal}} = 53.25\%$.
  - Fine mesh ($h = 1.875\,\mu\mathrm{m}, \xi = 0.1250$): $\mathcal{E}_{\text{chordal}} = 0.5203\%$.
  - Theoretical reduction ratio: $102.34\times$ (asymptotic $(20 / 1.875)^2 = 113.78\times$).
- **Dimensional Rectification:** The expression $\frac{h^2}{6 l_0} d_{\max} = 7.415 \times 10^{-6}\,\text{mm}$ carries units of length, not percentage.
- **Historical Origin of "$0.0039\%$":** Traced to decimal fraction $0.003906 = \xi_{\text{fine}}^2 / 4$ ($= 0.39\%$) mislabeled as a percentage.
- **Empirical 2D Result:** The actual 2D non-uniform FE quadrature error is $0.1322\%$, fully satisfying Criterion 3 ($\le 5.0\%$).

### 3.5 The In-Analysis Mechanical Continuation Blocker in Abaqus/Standard
Exhaustive experimental and technical investigation revealed fundamental architectural limitations in commercial Abaqus/Standard:
1. **Fatal Rejection of Displacement Initial Conditions:** `*INITIAL CONDITIONS, TYPE=DISPLACEMENT` is rejected in `*STATIC` procedures (Error 144; allowed only in dynamic/velocity analyses).
2. **Zero Displacement Initialization with Solution ICs:** `*INITIAL CONDITIONS, TYPE=SOLUTION` initializes element state variables ($\mathrm{SDVs}$ including $d$ and $\Hist$), but leaves nodal displacement DOFs identically zero at $t = 0$. The solver must artificially reload from $u = 0$ to $u_{\text{handoff}}$, traversing a virgin-to-damaged secant path that distorts reaction force continuity.
3. **Incompatibility with User Elements:** Native Abaqus state mapping (`*MAP SOLUTION` and `*IMPORT`) does not support user-defined elements (`UEL`). Topology changes prevent standard restart (`*RESTART`).
4. **Staggered COMMON-Block Coupling Lag:** Staggered coupling between mechanical and phase-field layers via Fortran `COMMON` blocks introduces a single-increment lag upon step transition, contributing to the observed $21.55\,\text{N}$ step-boundary force jump.

### 3.6 Dual-Matrix Governance Evaluation for Method C

```
====================================================================================================
DUAL-MATRIX ACCEPTANCE EVALUATION:
----------------------------------------------------------------------------------------------------
Matrix A: Mathematical Offline Forward State Transfer (2.9k -> 14.7k at u = 0.0050 mm)
  * Displacement L2 Error:               0.1347% <= 1.0%     --> QUALIFIED (PASS)
  * Peak Damage Interpolation Error:     Delta d = 0.000000  --> QUALIFIED (PASS)
  * Domain-Integrated Damage Error:      0.1322% <= 5.0%     --> QUALIFIED (PASS)
  * History Non-Negativity:              min(H) >= 0.0 (0 neg)--> QUALIFIED (PASS)
  * Offline Mesh Compliance Disparity:   1.6662% <= 5.0%     --> QUALIFIED (PASS)
  Verdict: MATHEMATICAL STATE TRANSFER FULLY QUALIFIED

Matrix B: In-Analysis Mechanical Continuation in Abaqus/Standard
  * Displacement Initial Conditions:     Rejected (Error 144)--> UNSUPPORTED BY ABAQUS
  * User Element Mapping (*MAP SOLUTION):Not supported       --> UNSUPPORTED BY ABAQUS
  * Forward Step-Boundary Force Jump:    Un-run in solver    --> NOT YET EVALUATED
  * Forward Continuation Energy Residual:Un-run in solver    --> NOT YET EVALUATED
  * Reverse Coarsening Force Jump:       21.55 N > 5.0 N     --> FAIL (DISCONTINUITY)
  * Reverse Coarsening Energy Residual:  22.22% > 10.0%      --> FAIL (ENERGY CONSERVATION)
  Verdict: CONTINUATION IN ABAQUS/STANDARD NOT QUALIFIED WITHOUT INTRUSIVE UEL RE-ARCHITECTING
====================================================================================================
```

---

## 4. Formal Decisions Requiring Supervisor Approval (22 October 2026)

During the upcoming meeting on Thursday, 22 October 2026 at 10:00 CEST, the following three formal decisions are submitted for supervisor endorsement:

### Decision 1: Formal Closure of Gate 6B (Method B)
- **Recommendation:** Formally close Gate 6B with classification:
  `METHOD_B_SCIENTIFIC_OBJECTIVE_COMPLETED_WITH_PARTIAL_HORIZON_LIMITATION`
- **Justification:** Corrected Method B completely resolved the central research question by eliminating the $0.50-0.60\,\text{kN}$ force plateau, restoring brittle snap-through softening, and reducing external work by $31.5\%$ (within $-3.87\%$ of reference). All scientific claims are strictly scoped to the verified common displacement horizon $u \in [0.0, 0.007889]\,\text{mm}$ (capturing $>99.76\%$ softening).

### Decision 2: Formal Evaluation of Gate 6C (Method C)
- **Recommendation:** Formally classify Gate 6C with classification:
  `OFFLINE_TRANSFER_QUALIFIED__CONTINUATION_NOT_QUALIFIED`
- **Justification:** Milestone 1 (native mesh refinement) and Milestone 2 (offline mathematical state transfer) are fully verified and meet all Gate 6C criteria. Milestone 3 (mechanical continuation in Abaqus/Standard) cannot be achieved natively due to Abaqus displacement initialization limitations and lack of UEL support in `*MAP SOLUTION`.

### Decision 3: Strategic Thesis Path Forward
- **Recommendation:** Conclude numerical simulation campaigns for Mode-I and focus remaining thesis effort on:
  1. Authoring final synthesis chapters consolidating Methods A and B as verified pre-refinement engineering workflows.
  2. Documenting Method C as a rigorous feasibility and software-limitation case study, articulating the exact commercial FE architectural barriers.
  3. Recommending future research directions (monolithic UEL formulation with internal displacement mapping or external Python orchestration) without undertaking high-risk UEL redesign that would breach the frozen baseline Fortran contract (`CE8D5EDC...`).
