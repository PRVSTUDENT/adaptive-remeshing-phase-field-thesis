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
* Method B (Load-Partitioned Pre-Refinement):
    - Definition & Scope: Configurable 1-, 2-, or 4-step loading partitions, followed by ONE
      remeshing operation and a fresh simulation from t = 0. The number of loading steps (1, 2, or 4)
      is NOT the number of adaptive remeshing cycles.
    - Status: COMPLETED WITH PARTIAL HORIZON LIMITATION (Job 1412465, 14,483 FE).
    - Achievement: Completely eliminated artificial 0.50-0.60 kN force plateau; restored brittle
      snap-through softening; reduced external work by 31.4896% (from 3.309642 mJ to 2.267448 mJ
      over matched horizon u <= 0.007889 mm, within -3.87% of canonical reference 2.3586 mJ).
    - Limitation: Terminal cutback at u = 0.007889 mm in deep softening tail (RF = 1.76 N, 99.76% softened).
      All like-for-like comparisons with reference are strictly scoped to u in [0.0, 0.007889] mm.
* Method C (Sequential Adaptive Remeshing during Crack Propagation):
    - Intended Research Objective: The user's intended research objective remains genuine sequential
      adaptive remeshing during Mode-I crack propagation (Solve -> evaluate error -> remesh ->
      transfer state -> continue, repeated when scientifically justified), rather than merely
      successful offline pre-refinement.
    - Status: OFFLINE_TRANSFER_QUALIFIED__CONTINUATION_NOT_QUALIFIED.
    - Actual Documented Milestone Status: One authentic coarse-to-fine refinement candidate
      (2,906 -> 14,677 FEs) and offline transfer have been verified (Milestone 1 and Milestone 2).
      However, ZERO complete sequential remeshing-and-continuation cycles have been qualified in the
      solver. Two-cycle and four-cycle Method C experiments have NOT been demonstrated.
    - Commercial Software Barrier: In-analysis continuation (Milestone 3) is fundamentally blocked
      by commercial Abaqus/Standard limitations: fatal rejection of displacement ICs in *STATIC,
      zero displacement DOFs under *INITIAL CONDITIONS, TYPE=SOLUTION, lack of UEL support in
      *MAP SOLUTION, and staggered UEL COMMON-block coupling lag.
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
- Terminal external work reached $W_{\text{ext}} = 3.3320\,\text{mJ}$ over the full displacement horizon $u = 0.0100\,\text{mm}$ ($+41.3\%$ excess work; and $W_{\text{ext}} = 3.3096\,\text{mJ}$ over the matched horizon $u \le 0.007889\,\text{mm}$).

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
| **Work $W_{\text{ext}}$ (matched $u \le 0.0079\,\text{mm}$)** | $2.3586\,\text{mJ}$ | $3.3096\,\text{mJ}$ | $\mathbf{2.2674\,\text{mJ}}^*$ | $\mathbf{-3.87\%}$ ($-31.49\%$ vs Orig B matched) |
| **Terminal Work $W_{\text{ext}}$ ($u = 0.0100\,\text{mm}$)** | $2.3587\,\text{mJ}$ | $3.3320\,\text{mJ}$ | \emph{N/A}$^\dagger$ | --- (Full-horizon baseline; cross-horizon comparison invalid) |
| **Fracture Energy $E_{\text{frac}}$**| $2.3512\,\text{mJ}$ | $3.0320\,\text{mJ}$ | $2.2855\,\text{mJ}^*$ | $-2.79\%$ |
| **Energy Residual $\Delta E$** | $0.0072\,\text{mJ}$ | $0.2848\,\text{mJ}$ | $0.0250\,\text{mJ}^*$ | $\mathbf{1.10\%}$ (Relative Error) |
| **Verified Endpoint** | $u = 0.0100\,\text{mm}$ | $u = 0.0100\,\text{mm}$ | $u = 0.007889\,\text{mm}$ | Post-fracture ($99.76\%$) |

$^*$Evaluated at terminal state $u = 0.007889\,\text{mm}$ ($RF = 1.76\,\text{N}$, $99.76\%$ softened).  
$^\dagger$Solver cutback at $u = 0.007889\,\text{mm}$; nominal $0.0100\,\text{mm}$ horizon was not reached.

### 2.4 Solver Termination Audit & Comparison Horizon Discipline
- **Termination Root Cause:** Job `1412465` executed $4{,}890$ increments and encountered Exit Code 1 at $u = 0.007889\,\text{mm}$ due to increment cutbacks below $dt_{\min} = 1.0 \times 10^{-12}$ in the post-fracture softening tail.
- **Physical State at Termination:** Reaction force had dropped to $RF = 1.76\,\text{N}$ ($99.76\%$ load reduction from peak). The specimen halves were macroscopically severed and undergoing rigid-body separation.
- **Strict Comparison Horizon:** All like-for-like comparisons with reference are strictly valid over $u \in [0.0, 0.007889]\,\text{mm}$. Within this window, the complete linear elastic, initiation, peak, and brittle softening regimes are fully captured.
- **Topological Crack Continuity:** BFS dual-graph search confirms that all $818$ elements with $d \ge 0.95$ form a single $100\%$ connected component traversing $99.9\%$ of the ligament with zero isolated clusters or spatial gaps, demonstrating continuous phase-field damage localization along the prospective path (characterized as damage band continuity rather than mathematical proof of discrete topological separation).
- **Damage Overshoot:** Peak damage reached $d_{\max} = 1.001123$ ($+0.11\%$). This is confirmed as an unconstrained continuous Galerkin Newton formulation property without active-set projection, fully stabilized by residual stiffness $k_{\text{stab}}$.
- **Epistemic Attribution:** Sizing parameters (\texttt{errorTarget}=2.5\% vs 1.0\%) and pre-analysis source step were adjusted simultaneously; plateau elimination is verified for the corrected mesh, but cannot be uniquely isolated to one parameter without further unconfounded testing.

---

## 3. Method C: Sequential Adaptive Remeshing Feasibility & State Transfer

### 3.1 User Objective and Method B vs. Method C Architectural Distinction
The user's intended research objective remains **genuine sequential adaptive remeshing during Mode-I crack propagation**, rather than merely successful offline pre-refinement.

It is essential to maintain clear architectural boundaries:
- **Method B:** Configurable 1-, 2-, or 4-step loading partitions, followed by **one** remeshing operation and a fresh simulation from $t = 0$. The number of loading steps is not the number of adaptive remeshing cycles.
- **Method C:** Solve $\to$ evaluate error $\to$ remesh $\to$ transfer state $\to$ continue, repeated sequentially during crack propagation when scientifically justified.

**Documented Status:** One authentic coarse-to-fine refinement candidate ($2{,}906 \to 14{,}677$ FEs) and offline transfer have been verified, but **zero complete sequential remeshing-and-continuation cycles have been qualified**. Two-cycle and four-cycle Method C experiments have not been demonstrated.

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
| **Criterion 6** | Offline Mesh Compliance Disparity | $\le 5.0\%$ | $\mathbf{1.6662\%}^\ddagger$ | **PASS** |
| **Criterion 7** | Continuation Energy Residual | $\le 10.0\%$ | \emph{Not Yet Evaluated}$^\dagger$ | **UN-RUN IN SOLVER** |

$^*$Evaluated at coincident notch tip node 129 ($x=0.5, y=0.5\,\text{mm}$).  
$^\dagger$Forward recipient mesh has never been solved in Abaqus. Reverse coarsening metrics (Job 1412809: $21.55\,\text{N}$ and $22.22\%$) are kept strictly decoupled.  
$^\ddagger$Criterion 6 evaluates the static compliance disparity between the independently solved coarse donor ($1.6634\,\text{mJ}$) and fine reference ($1.6911\,\text{mJ}$) equilibrium states at $u = 0.0050\,\text{mm}$; it reflects discretization compliance disparity and is not directly measured projection-induced energy loss.

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

## 4. Formal Decisions Submitted for Supervisor Consideration & Determination (22 October 2026)

During the upcoming meeting on Thursday, 22 October 2026 at 10:00 CEST, the following formal decisions and technical notes are submitted for the supervisor's review, consideration, and formal determination:

### Decision 1: Formal Closure of Gate 6B (Method B)
- **Submitted for Supervisor Determination:** Formal closure and sign-off of Gate 6B with the classification:
  `METHOD_B_SCIENTIFIC_OBJECTIVE_COMPLETED_WITH_PARTIAL_HORIZON_LIMITATION`
- **Technical Basis:** Corrected Method B completely resolved the central research question by eliminating the $0.50-0.60\,\text{kN}$ force plateau, restoring brittle snap-through softening, and reducing external work by $31.4896\%$ (from $3.309642\,\text{mJ}$ to $2.267448\,\text{mJ}$ over the matched horizon $u \le 0.007889\,\text{mm}$, within $-3.87\%$ of canonical reference $2.3586\,\text{mJ}$). All scientific claims are strictly scoped to the verified common displacement horizon $u \in [0.0, 0.007889]\,\text{mm}$ (capturing $>99.76\%$ softening).

### Decision 2: Formal Evaluation of Gate 6C (Method C)
- **Submitted for Supervisor Determination:** Formal classification of Gate 6C under the dual-matrix evaluation:
  `OFFLINE_TRANSFER_QUALIFIED__CONTINUATION_NOT_QUALIFIED`
- **Technical Basis:** Milestone 1 (native mesh refinement) and Milestone 2 (offline mathematical state transfer) are fully verified and meet all Gate 6C criteria ($L_2 = 0.13\%$, $\Delta d = 0.000000$, $\min(\Hist) \ge 0.0$, compliance disparity $1.67\%$). Milestone 3 (in-analysis mechanical continuation in Abaqus/Standard) cannot be achieved natively due to commercial Abaqus displacement initialization limitations (rejection of displacement ICs in `*STATIC`, zero DOFs in solution ICs) and lack of UEL support in `*MAP SOLUTION`. Zero complete sequential remeshing-and-continuation cycles have been qualified in the solver; multi-cycle experiments remain un-demonstrated.

### Decision 3: Strategic Thesis Path Forward
- **Submitted for Supervisor Consideration & Determination:** The strategic research direction for the thesis remains for determination between the user and supervisor. Two scientifically defensible options are submitted:
  - **Option A (Preserve & Report Baseline Methods):** Preserve and report Methods A and B as verified offline pre-refinement engineering workflows, alongside a rigorous documentation of the current commercial Abaqus/Standard Method C feasibility limitations and architectural software barriers, without further solver modifications.
  - **Option B (Investigate Separate Experimental Continuation Architecture):** Investigate a separate experimental, state-preserving UEL continuation architecture (e.g. exploring alternative state-initialization mechanisms or monolithic formulation) developed in an isolated development branch, keeping the authoritative, frozen baseline `f42_mixed_uel.for` (`CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6`) strictly unchanged and protected (technical feasibility and controlled single-cycle validation plan detailed in `docs/reports/MODE1_METHOD_C1_CONTINUATION_FEASIBILITY_AND_PLAN.md` and independent architectural validation and Method C2 wake coarsening audit in `docs/reports/MODE1_METHOD_C_CONTINUATION_ARCHITECTURE_VALIDATION.md`).
- **Epistemic Discipline:** The choice between Option A and Option B belongs strictly to the user and the supervisor. The controller/agent does not independently terminate Method C or resume Mode-II.

### 4.4 Technical Note: Mandatory Qualification Criteria for a Single Genuine Method C Remeshing Cycle

For supervisor consideration regarding Option B (or any future continuation investigation), a future single genuine Method C remeshing-and-continuation cycle ($\text{Solve} \to \text{Evaluate Error} \to \text{Remesh} \to \text{Transfer State} \to \text{Continue}$) must rigorously demonstrate the following six pre-declared verification criteria before multi-cycle execution can be considered:

1. **State-Preserving Nonzero-Displacement Initialization:**
   The solver must initialize directly at the transferred deformed equilibrium state ($\mathbf{u} = \mathbf{u}_{\text{handoff}} \ne \mathbf{0}$) on the recipient mesh without requiring an artificial quasi-static reload from $u = 0$, thereby preserving the active stress state and kinematic history.
2. **Phase-Field and Strain-History Preservation:**
   Nodal damage values ($0 \le d \le 1$) and element history variables ($\Hist \ge 0$) must be transferred with high spatial fidelity without unphysical diffusion, negative values, or loss of localization ($L_2 \le 1.0\%$, $\Delta d_{\max} \le 0.02$).
3. **Reaction-Force Continuity Within Declared Tolerance:**
   The initial reaction force upon continuation on the recipient mesh must match the donor handoff reaction force within the declared tolerance of $|\Delta RF| \le 5.0\,\text{N}$, eliminating step-boundary discontinuities.
4. **Quantified Transfer-Induced Energy Discrepancy:**
   The energy discrepancy introduced purely by mesh-to-mesh state transfer must be rigorously bounded and tracked ($\Delta E_{\text{transfer}} / W_{\text{ext}} \le 5.0\%$), and global energy balance must be satisfied throughout subsequent continuation ($\Delta E \le 10.0\%$).
5. **Actual Forward-Recipient Fracture Response Against Fixed Reference:**
   Continuation must demonstrate physical crack propagation on the fine recipient mesh matching the canonical fixed-mesh reference in stiffness $K_0$, peak load $F_{\max}$, and brittle post-peak softening without crack pinning.
6. **Repeatability Before Extending to Multi-Cycle Execution:**
   A single remeshing cycle must be proven robust, deterministic, and repeatable before extending the workflow to two or more sequential remeshing cycles.

*Epistemic Guard:* Developing an experimental UEL modification or alternative initialization architecture is treated strictly as an engineering hypothesis requiring separate empirical verification; it must not be assumed or claimed that an experimental UEL modification will necessarily resolve these commercial solver constraints.

### 4.5 Technical Note: Defensible Progressive Progression from Gate C1 to Gate C2

To ensure scientific rigor, a two-stage sequential validation gate structure is established (detailed in `docs/reports/MODE1_METHOD_C_CONTINUATION_ARCHITECTURE_VALIDATION.md`):

1. **Gate C1 (Forward-Refinement Continuation Validation):**
   - Must demonstrate one genuine forward continuation ($2,906 \to 14,677$ FEs at $u = 0.0050\,\mathrm{mm}$).
   - Mandatory criteria: reaction-force continuity ($|\Delta RF| \le 5.0\,\mathrm{N}$), transfer energy error ($\le 5.0\%$), global balance residual ($\le 10.0\%$), damage irreversibility ($\Delta d \ge -10^{-6}$), reference fracture response parity ($|F_{\max} - F_{\max}^{\mathrm{ref}}| \le 3.0\%$, no crack pinning), and 0 pre-peak cutbacks.
   - Staged re-equilibration is treated as a provisional reload surrogate requiring proof of state equivalence at handoff, while kinematic-offset UEL is an experimental candidate.

2. **Gate C2 (Selective Crack-Wake Coarsening Validation):**
   - Activated **only after Gate C1 achieves PASS**.
   - Distinguishes coarsening in intact far-field material ($d = 0$, safe to coarsen to $20-50\,\mu\mathrm{m}$), active FPZ ($0 < d < 1$, strictly forbidden to coarsen), and fully fractured wake ($d \approx 1$, where coarsening risks altering arm compliance, COD, and fracture energy quadrature).
   - Applies the candidate mesh-resolution guideline $h_{\mathrm{wake}} \le l_0/2 = 3.75\,\mu\mathrm{m}$ across damaged zones ($d \ge 0.05$) as an engineering heuristic awaiting numerical validation, without hardcoding crack trajectories.
   - Requires demonstrating net computational efficiency ($\ge 15\%$ walltime reduction vs C1) without corrupting global fracture physics.

3. **Governance & Authorization Status:**
   - Gate 6B is ready for supervisor sign-off on 22 October 2026.
   - **Gate 6C remains ON HOLD PENDING SUPERVISOR REVIEW.** Passing unit tests or general PBS script presence do NOT constitute scientific gate clearance. Zero new solver jobs are submitted without explicit supervisor/user release.
