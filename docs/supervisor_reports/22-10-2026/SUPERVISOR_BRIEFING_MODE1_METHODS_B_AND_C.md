# Mode-I Adaptive Remeshing Methods B & C: Unified Synthesis & Supervisor Briefing

**Document ID:** `SUPERVISOR_BRIEFING_MODE1_METHODS_B_AND_C.md`  
**Milestone:** Master's Thesis Progress Review — Thursday, 22 October 2026 (10:00 CEST)  
**Author:** Pruthviraja Reddy Vandavagali (Matriculation No. 68865)  
**Institution:** Institute of Mechanics and Fluid Dynamics (IMFD), TU Bergakademie Freiberg  
**Authoritative Fortran Source:** `f42_mixed_uel.for` (SHA-256: `CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6`)  
**Governing Directive:** *"We need to have understood everything related to the first model before we increase complexity."*  
**Operational Status:** `METHODS_B_AND_C_SCIENTIFICALLY_EVALUATED_READY_FOR_SUPERVISOR_REVIEW`  

---

## Executive Summary & Scientific Sequence Overview

This briefing consolidates the complete numerical and mechanical evidence for **Method B** (load-partitioned propagation pre-refinement) and **Method C** (sequential adaptive remeshing and state transfer) on the canonical Mode-I symmetric tension phase-field fracture benchmark ($l_0 = 7.5\,\mu\mathrm{m}$).

The analysis strictly adheres to the supervisor-mandated scientific sequence:
$$\text{[Problem Definition]} \longrightarrow \text{[Expected Solution]} \longrightarrow \text{[Fixed-Mesh Reference Anchor]} \longrightarrow \text{[Method A/B Results]} \longrightarrow \text{[Method C1 Feasibility]} \longrightarrow \text{[Method C2 Alternatives]} \longrightarrow \text{[Unresolved Limitations]} \longrightarrow \text{[Specific Supervisor Decisions]}$$

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
    - Intended Research Objective: Genuine sequential adaptive remeshing during Mode-I crack
      propagation (Solve -> evaluate error -> remesh -> transfer state -> continue), rather than
      merely offline pre-refinement.
    - Status: OFFLINE_TRANSFER_QUALIFIED__CONTINUATION_NOT_QUALIFIED.
    - Actual Documented Milestone Status: One authentic coarse-to-fine refinement candidate
      (2,906 -> 14,677 FEs) and offline transfer verified. ZERO complete sequential remeshing-
      and-continuation cycles qualified in the solver. Multi-cycle experiments un-demonstrated.
    - Commercial Software Barrier: In-analysis continuation is fundamentally blocked in commercial
      Abaqus/Standard: fatal rejection of displacement ICs in *STATIC (Error 144), zero displacement
      DOFs under *INITIAL CONDITIONS, TYPE=SOLUTION, lack of UEL support in *MAP SOLUTION, and
      staggered UEL COMMON-block coupling lag.
====================================================================================================
```

---

## 1. Problem Definition, Expected Response & Canonical Reference Anchor

### 1.1 Boundary Value Problem Specification
- **Domain:** $\Omega = [0, 1] \times [0, 1]\,\text{mm}^2$ square plate.
- **Crack Representation:** Sharp horizontal seam along $y = 0.5\,\text{mm}$ ($0 \le x \le 0.5\,\text{mm}$) with duplicate coincident node pairs (zero initial gap).
- **Material & Phase-Field Parameters:** $E = 210.0\,\text{kN/mm}^2$, $\nu = 0.3$, $G_c = 2.7 \times 10^{-3}\,\text{kN/mm}$ ($2.7\,\text{N/mm}$), $l_0 = 0.0075\,\text{mm}$ ($7.5\,\mu\mathrm{m}$), $k_{\text{stab}} = 1.0 \times 10^{-7}$.
- **Boundary Conditions:** Roller support at $y = 0$ ($u_y = 0$, pinned at $(0,0)$); monotonic tensile top displacement $u_y(t) = t \cdot u_{\text{final}}$ prescribed via kinematic coupling to Reference Point 999999.

### 1.2 Expected Physical Response
1. Initial linear-elastic response with structural stiffness $K_0 \approx 138\,\text{kN/mm}$.
2. Crack-tip phase-field damage localization ($0 \le d \le 1$) within a regularized zone of width $w \approx 2 l_0 = 15\,\mu\mathrm{m}$.
3. Peak reaction force $F_{\max} \approx 0.758\,\text{kN}$ at $u \approx 0.00586\,\text{mm}$.
4. Immediate, sharp brittle softening tail with complete separation ($RF \to 0$) along the symmetry line $y = 0.5\,\text{mm}$.

### 1.3 Canonical Fixed-Mesh Reference Anchor (Job `1398090.mmaster02`)
The fixed-mesh reference solution is the quantitative anchor against which all adaptive methods are judged:
- **Mesh:** $15{,}220$ uniform quadrilateral CPE4 elements ($h = 3.75\,\mu\mathrm{m} = l_0 / 2$).
- **Initial Structural Stiffness:** $K_0 = 137.945520\,\text{kN/mm}$ ($R^2 = 0.99999960$, $u \le 0.0010\,\text{mm}$).
- **Peak Reaction Force:** $F_{\max} = 0.757802\,\text{kN}$ at $u = 0.005857\,\text{mm}$.
- **Post-Peak Response:** Immediate, sharp brittle softening to $F < 0.0005\,\text{kN}$ by $u = 0.0060\,\text{mm}$.
- **Cumulative External Work:** $W_{\text{ext}} = 2.3587\,\text{mJ}$ (over $u \in [0.0, 0.0100]\,\text{mm}$); $W_{\text{ext}} = 2.3586\,\text{mJ}$ (over $u \in [0.0, 0.007889]\,\text{mm}$).
- **Surface Fracture Energy:** $E_{\text{frac}} = 2.3512\,\text{mJ}$ ($99.69\%$ of external work).

---

## 2. Method B: Full-Ligament Refinement and Plateau Elimination

### 2.1 The Problem: Coarse Ligament Crack Pinning in Original Method B
Original Method B ($14{,}677$ FEs, Job `1411934.mmaster02`) was adapted based on an elastic Step-1 pre-analysis ($u \le 0.0050\,\text{mm}$). Because stress error indicators ($\MISESERI$) concentrated exclusively at the initial crack tip ($x \in [0.48, 0.52]\,\mathrm{mm}$), the remaining uncracked ligament ($x \in [0.55, 1.00]\,\mathrm{mm}$) retained coarse elements ($h \approx 19.7\,\mu\mathrm{m} > 2.6\,l_0$).
When the crack initiated into this coarse zone:
- Elements could not resolve the regularized damage gradient ($w_{0.5} \approx 2\,l_0 = 15.0\,\mu\mathrm{m}$).
- An unphysical force plateau of $F \approx 0.50 - 0.60\,\mathrm{kN}$ persisted across $u \in [0.0060, 0.0075]\,\mathrm{mm}$.
- Terminal external work reached $W_{\text{ext}} = 3.3320\,\text{mJ}$ ($+41.3\%$ excess work vs reference).

### 2.2 Expected Solution & Corrected Propagation Discretization
To resolve this defect, **Corrected Method B** (Package 40, Job `1412465.mmaster02`, `M1_MB_CORR_14K`) enforced the critical sizing threshold $h \le l_0 / 2 = 3.75\,\mu\mathrm{m}$ continuously along the entire symmetry ligament from notch tip to specimen boundary.
- **Finite Element Count:** $14{,}483$ FEs ($14{,}303$ CPE4 quads + $180$ CPE3 transition triangles).
- **Co-located Layer Records:** $43{,}449$ element records across the 3-layer architecture.
- **Corridor Sizing Compliance:** $96.76\%$ of elements along the prospective crack path satisfy $h \le 3.75\,\mu\mathrm{m} = l_0/2$, and $99.84\%$ satisfy $h \le 7.5\,\mu\mathrm{m} = l_0$.

### 2.3 Quantitative Multi-Quantity Fracture Comparison

| Quantity | Canonical Reference | Original Method B | Corrected Method B | Relative Discrepancy |
| :--- | :---: | :---: | :---: | :---: |
| **Job ID** | `1398090` | `1411934` | `1412465` | --- |
| **Finite Elements** | $15{,}220$ | $14{,}677$ | $14{,}483$ | $-4.84\%$ |
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
- **Termination Root Cause:** Job `1412465` executed $4{,}890$ increments and encountered Exit Code 1 at $u = 0.007889\,\text{mm}$ due to cutbacks below $dt_{\min} = 1.0 \times 10^{-12}$ in the deep post-fracture softening tail.
- **Physical State at Termination:** Reaction force had dropped to $RF = 1.76\,\text{N}$ ($99.76\%$ load reduction from peak). The specimen halves were macroscopically severed and undergoing rigid-body separation.
- **Strict Comparison Horizon:** All like-for-like comparisons with reference are strictly valid over $u \in [0.0, 0.007889]\,\text{mm}$. Within this window, the complete linear elastic, initiation, peak, and brittle softening regimes are fully captured.
- **Topological Crack Continuity:** BFS dual-graph search confirms that all $818$ elements with $d \ge 0.95$ form a single $100\%$ connected component traversing $99.9\%$ of the ligament with zero isolated clusters or spatial gaps.

---

## 3. Method C: Sequential Adaptive Remeshing Feasibility & State Transfer

### 3.1 Architectural Scope & Milestone Separation
- **Method B:** Configurable 1-, 2-, or 4-step loading partitions, followed by **one** remeshing operation and a fresh simulation from $t = 0$.
- **Method C:** Solve $\to$ evaluate error $\to$ remesh $\to$ transfer state $\to$ continue, repeated sequentially during crack propagation.
**Documented Status:** One authentic coarse-to-fine refinement candidate ($2{,}906 \to 14{,}677$ FEs) and offline transfer have been verified, but **zero complete sequential remeshing-and-continuation cycles have been qualified**. Two-cycle and four-cycle Method C experiments have not been demonstrated.

The state-transfer comparison across the three canonical physical fields at $u = 0.0050\,\text{mm}$ established:
- **Field 1 (Coarse Donor Solution, 2.9k FEs):** $d_{\max} = 0.094910$. Coarse mesh ($h = 20\,\mu\mathrm{m} > 2.6\,l_0$) pinned damage evolution, retarding crack initiation.
- **Field 2 (Coarse Solution Interpolated on Fine Mesh):** $d_{\max} = 0.094910$. Exact identity with Field 1 ($\Delta d = 0.000000$) at coincident notch tip node 129. Proves **mathematical transfer fidelity**.
- **Field 3 (Independently Solved Fine Reference, 14.7k FEs):** $d_{\max} = 0.319455$. Fine mesh ($h = 1.875\,\mu\mathrm{m} \le l_0/4$) resolved steep damage gradient from $t = 0$.

### 3.2 Offline State Transfer Evaluation (Gate 6C Criteria)

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
$^\ddagger$Criterion 6 evaluates the static compliance disparity between the independently solved coarse donor ($1.6634\,\text{mJ}$) and fine reference ($1.6911\,\text{mJ}$) equilibrium states at $u = 0.0050\,\text{mm}$.

### 3.3 Mathematical Tangent Disambiguation & Nonmatching Projection Residual
1. **Mechanical Tangent for Fixed Damage ($\mathbf{K}_{uu}$):**
   $$\mathbf{K}_{uu} = \int_{\Omega} \mathbf{B}^T g(d) \mathbf{C}_0 \mathbf{B} \, d\Omega$$
   Because $g(d) = (1-d)^2 + k_{\text{stab}} \ge 10^{-7} > 0$ everywhere, $\mathbf{K}_{uu}$ is **strictly symmetric and positive definite** for any fixed damage state. One must not infer loss of positive definiteness of $\mathbf{K}_{uu}$ solely from material degradation.
2. **Coupled Damage-Evolution Tangent ($\mathbf{K}_{\text{coupled}}$):**
   When damage evolves ($\dot{d} > 0$), the variation $-\frac{\partial g}{\partial d}\dot{d}\mathbf{C}_0:\boldsymbol{\varepsilon}$ introduces negative eigenvalues into the coupled system operator $\mathbf{K}_{\text{coupled}}$, which causes loss of positive definiteness during localized crack propagation.
3. **Nonmatching Projection Residual ($\mathbf{R}_{\text{internal}, 0}$):**
   For the candidate forward transfer ($2,906 \to 14,677$ FEs at $u = 0.0050\,\text{mm}$), the compliance disparity of $1.64\%$ produces an estimated internal un-equilibrated nodal residual norm of $\|\mathbf{R}_{\text{internal}, 0}\| \approx \mathcal{O}(10\,\text{N})$ across the $\sim 11,846$ newly created interior nodes.
4. **Three Zero Quantities Disambiguated:**
   - $\Delta \mathbf{U}_{\text{prescribed}} = \mathbf{0}$ (prescribed boundary condition increment)
   - $\mathbf{R}_{\text{internal}, 0} = \mathbf{0}$ (discrete internal equilibrium residual, which is strictly non-zero: $\boldsymbol{\rho}_{\text{transfer}} \ne \mathbf{0}$)
   - $\Delta RF = 0$ (boundary reaction force discontinuity)
   Prescribing zero incremental displacement does NOT ensure internal equilibrium or force continuity.

---

## 4. Formal Decisions Submitted for Supervisor Consideration & Determination (22 October 2026)

During the upcoming meeting on Thursday, 22 October 2026 at 10:00 CEST, the following formal decisions and technical notes are submitted for the supervisor's review, consideration, and formal determination:

### 4.1 Decision 1: Formal Closure of Gate 6B (Method B)
- **Submitted for Supervisor Determination:** Formal closure and sign-off of Gate 6B with the classification:
  `METHOD_B_SCIENTIFIC_OBJECTIVE_COMPLETED_WITH_PARTIAL_HORIZON_LIMITATION`
- **Technical Basis:** Corrected Method B completely resolved the central research question by eliminating the $0.50-0.60\,\text{kN}$ force plateau, restoring brittle snap-through softening, and reducing external work by $31.4896\%$ (from $3.309642\,\text{mJ}$ to $2.267448\,\text{mJ}$ over the matched horizon $u \le 0.007889\,\text{mm}$, within $-3.87\%$ of canonical reference $2.3586\,\text{mJ}$). All scientific claims are strictly scoped to the verified common displacement horizon $u \in [0.0, 0.007889]\,\text{mm}$ (capturing $>99.76\%$ softening).

### 4.2 Decision 2: Formal Evaluation of Gate 6C (Method C)
- **Submitted for Supervisor Determination:** Formal classification of Gate 6C under the dual-matrix evaluation:
  `OFFLINE_TRANSFER_QUALIFIED__CONTINUATION_NOT_QUALIFIED`
- **Technical Basis:** Milestone 1 (native mesh refinement) and Milestone 2 (offline mathematical state transfer) are fully verified and meet all Gate 6C criteria ($L_2 = 0.13\%$, $\Delta d = 0.000000$, $\min(\Hist) \ge 0.0$, compliance disparity $1.67\%$). Milestone 3 (in-analysis mechanical continuation in Abaqus/Standard) cannot be achieved natively due to commercial Abaqus displacement initialization limitations (rejection of displacement ICs in `*STATIC`, zero DOFs in solution ICs) and lack of UEL support in `*MAP SOLUTION`. Zero complete sequential remeshing-and-continuation cycles have been qualified in the solver; multi-cycle experiments remain un-demonstrated.

### 4.3 Decision 3: Strategic Thesis Path Forward
- **Submitted for Supervisor Consideration & Determination:** The strategic research direction for the thesis remains for determination between the user and supervisor. Two scientifically defensible options are submitted:
  - **Option A (Preserve & Report Baseline Methods):** Preserve and report Methods A and B as verified offline pre-refinement engineering workflows, alongside a rigorous documentation of the current commercial Abaqus/Standard Method C feasibility limitations and architectural software barriers, without further solver modifications.
  - **Option B (Investigate Separate Experimental Continuation Architecture):** Authorize implementing and evaluating the smallest isolated experimental C1 continuation prototype on a dedicated development branch (`f42_experimental_offset_uel.for`), keeping the authoritative, frozen baseline `f42_mixed_uel.for` (`CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6`) strictly unchanged and protected (technical feasibility and controlled single-cycle validation plan detailed in `docs/reports/MODE1_METHOD_C1_CONTINUATION_FEASIBILITY_AND_PLAN.md` and independent architectural validation and Method C2 wake coarsening audit in `docs/reports/MODE1_METHOD_C_CONTINUATION_ARCHITECTURE_VALIDATION.md`).
- **Epistemic Discipline:** The choice between Option A and Option B belongs strictly to the user and the supervisor. The controller/agent does not independently terminate Method C or resume Mode-II. General PBS permission does NOT authorize C1 solver execution without explicit supervisor review.

### 4.4 Technical Note: Mandatory Qualification Criteria for a Single Genuine Method C Remeshing Cycle

For supervisor consideration regarding Option B (or any future continuation investigation detailed in `docs/reports/MODE1_METHOD_C1_CONTINUATION_FEASIBILITY_AND_PLAN.md`), a future single genuine Method C remeshing-and-continuation cycle ($\text{Solve} \to \text{Evaluate Error} \to \text{Remesh} \to \text{Transfer State} \to \text{Continue}$) must rigorously demonstrate the following six pre-declared verification criteria before multi-cycle execution can be considered:

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

---

## 5. Traceable Epistemic Evidence Matrix

The complete evidence base is classified under the formal schema (`Evidence_ID`, `Epistemic_Tier`, `Claim_Statement`, `Governing_Metric`, `Pass_Threshold`, `Measured_Value`, `Evaluation_Status`):

```
+=======================================================================================================================================================+
|                                                      TRACEABLE EPISTEMIC EVIDENCE MATRIX                                                              |
+============+========================+====================================+======================+================+==================+=================+
| Evidence ID| Epistemic Tier         | Claim Statement                    | Governing Metric     | Pass Threshold | Measured Value   | Status          |
+============+========================+====================================+======================+================+==================+=================+
| EVD-M1-001 | [SOURCE CODE AUDIT]    | UEXTERNALDB zeroing loop prevents  | Code presence in     | Exact syntax   | Verified lines   | VERIFIED_PASS   |
|            |                        | Fortran state carryover            | f42_mixed_uel.for    | LOP=0 loop     | 88-101           |                 |
+------------+------------------------+------------------------------------+----------------------+----------------+------------------+-----------------+
| EVD-M1-002 | [SOURCE CODE AUDIT]    | SVARS(8+KPT) ingests history H     | SV_H_COMMITTED assign| Exact syntax   | Verified lines   | VERIFIED_PASS   |
|            |                        | from *INITIAL CONDITIONS, TYPE=SOL | from SVARS(8+KPT)    | in Step 1 Inc 1| 248-262          |                 |
+------------+------------------------+------------------------------------+----------------------+----------------+------------------+-----------------+
| EVD-M1-003 | [MATHEMATICAL DERIV.]  | Fixed-damage tangent Kuu is        | Eigenvalues of Kuu   | min(lambda)>0  | lambda > 0       | VERIFIED_PASS   |
|            |                        | strictly positive-definite         | for g(d) >= k_stab   | for all d      | analytically     |                 |
+------------+------------------------+------------------------------------+----------------------+----------------+------------------+-----------------+
| EVD-M1-004 | [MATHEMATICAL DERIV.]  | Coupled tangent K_coupled loses    | Eigenvalues of       | lambda <= 0    | lambda < 0       | VERIFIED_PASS   |
|            |                        | definiteness during softening      | K_coupled with soft. | during crack   | during localized |                 |
|            |                        |                                    |                      | propagation    | softening        |                 |
+------------+------------------------+------------------------------------+----------------------+----------------+------------------+-----------------+
| EVD-M1-005 | [MATHEMATICAL DERIV.]  | Reference update X*=X+u0 is        | F = d(x)/d(X*)       | F != I         | F = I, eps = 0,  | VERIFIED_FAIL   |
|            |                        | physically invalid                 | Strain and stress    | sigma != 0     | sigma = 0        | (DISQUALIFIED)  |
+------------+------------------------+------------------------------------+----------------------+----------------+------------------+-----------------+
| EVD-M1-006 | [MATHEMATICAL DERIV.]  | 1D chordal error formula produces  | eps(xi) =            | Illustrative   | +53.25% for      | PROPOSED_       |
|            |                        | +53.25% for coarse elements        | xi*coth(xi) - 1      | analytical     | h/l0 = 2.67      | GUIDELINE       |
+------------+------------------------+------------------------------------+----------------------+----------------+------------------+-----------------+
| EVD-M1-007 | [OFFLINE NUM. PROJ.]   | Forward transfer displacement error| ||u_recip - u_donor||| <= 1.0%        | 0.1347%          | VERIFIED_PASS   |
|            |                        | on 2,906 -> 14,677 FEs             | / ||u_donor|| (L2)   |                |                  |                 |
+------------+------------------------+------------------------------------+----------------------+----------------+------------------+-----------------+
| EVD-M1-008 | [OFFLINE NUM. PROJ.]   | Forward transfer peak damage error | |d_max^recip -       | <= 0.02        | 0.000000         | VERIFIED_PASS   |
|            |                        | at coincident notch tip node 129   | d_max^donor|         |                |                  |                 |
+------------+------------------------+------------------------------------+----------------------+----------------+------------------+-----------------+
| EVD-M1-009 | [OFFLINE NUM. PROJ.]   | Forward transfer damage integral   | |int d_recip -       | <= 5.0%        | 0.1322%          | VERIFIED_PASS   |
|            |                        | discrepancy across 2D domain       | int d_donor| / int d |                |                  |                 |
+------------+------------------------+------------------------------------+----------------------+----------------+------------------+-----------------+
| EVD-M1-010 | [OFFLINE NUM. PROJ.]   | Forward transfer history variable  | min(H_recip)         | >= 0.0         | 1.579e-9 kN/mm^2 | VERIFIED_PASS   |
|            |                        | non-negativity                     | across all GPs       | (0 negative)   | (0 negative GPs) |                 |
+------------+------------------------+------------------------------------+----------------------+----------------+------------------+-----------------+
| EVD-M1-011 | [OFFLINE NUM. PROJ.]   | Forward transfer internal node     | ||R_internal,0|| /   | <= 2.0%        | ~1.5 - 2.0%      | PROPOSED_       |
|            |                        | projection residual estimate       | ||F_ext,0||          |                | (~10 - 15 N)     | GUIDELINE       |
+------------+------------------------+------------------------------------+----------------------+----------------+------------------+-----------------+
| EVD-M1-012 | [ABAQUS DATACHECK]     | Native 14,677 FE recipient deck    | Abaqus datacheck     | Exit 0         | Exit 0 on        | VERIFIED_PASS   |
|            |                        | syntax and card wrapping validity  | preflight exit       |                | Job-2_UEL.inp    |                 |
+------------+------------------------+------------------------------------+----------------------+----------------+------------------+-----------------+
| EVD-M1-013 | [SOLVER RUNTIME VERIF.]| Abaqus fatal error on displacement | Solver execution of  | Rejection      | Exit 1 with      | VERIFIED_PASS   |
|            |                        | IC in general static step          | *INITIAL COND., DISP | recorded       | Error 144        | (LIMITATION)    |
+------------+------------------------+------------------------------------+----------------------+----------------+------------------+-----------------+
| EVD-M1-014 | [SOLVER RUNTIME VERIF.]| Single-increment coarsening force  | |RF_step2_inc1 -     | <= 5.0 N       | 21.55 N          | VERIFIED_FAIL   |
|            |                        | jump in Job 1412809                | RF_step1_end|        |                |                  | (DISCONTINUITY) |
+------------+------------------------+------------------------------------+----------------------+----------------+------------------+-----------------+
| EVD-M1-015 | [SOLVER RUNTIME VERIF.]| Coarse mesh crack pinning in       | F_max vs reference   | <= 0.78 kN     | 1085.41 N        | VERIFIED_FAIL   |
|            |                        | Job 1412809                        | (0.758 kN)           | (+3.0%)        | (+43.2%)         | (PINNING)       |
+------------+------------------------+------------------------------------+----------------------+----------------+------------------+-----------------+
| EVD-M1-016 | [SOLVER RUNTIME VERIF.]| Corrected Method B plateau         | RF at u >= 0.0060 mm | <= 0.005 kN    | 0.00208 kN       | VERIFIED_PASS   |
|            |                        | elimination (Job 1412465)          |                      | (plateau gone) | (plateau gone)   |                 |
+------------+------------------------+------------------------------------+----------------------+----------------+------------------+-----------------+
| EVD-M1-017 | [SOLVER RUNTIME VERIF.]| Corrected Method B matched work    | W_ext(u <= 0.0079 mm)| <= 2.45 mJ     | 2.2674 mJ        | VERIFIED_PASS   |
|            |                        | reduction vs reference             | vs Ref (2.3586 mJ)   | (within 5.0%)  | (-3.87% vs ref)  |                 |
+============+========================+====================================+======================+================+==================+=================+
```

---

## 6. Smallest C1 Experiment Specification & Execution Sequence

To establish an actionable, controlled experimental roadmap (pending explicit supervisor authorization), the smallest C1 experiment is specified:
- **Donor State:** Existing Mode-I donor state at $u = 0.0050\,\text{mm}$ (Job 1411891 / 1411924, $2,906$ FEs, $2,988$ nodes, $RF = 653.09\,\text{N}$, $E_{\text{elas}} = 1.6634\,\text{mJ}$).
- **Recipient Mesh:** Native $14,677$ FE recipient mesh (`M1_MB_NATIVE_14K` / `Job-2_UEL.inp`, $14,834$ nodes, corridor $h = 1.875\,\mu\text{m} = l_0/4$).
- **Comparison of Approaches:**
  * *Path 1 (Staged Reload):* Kept with production UEL frozen; reloads from $u=0$ over 500 increments; evaluates whether state equivalence holds at $u = 0.0050\,\text{mm}$.
  * *Path 2 (Experimental Kinematic Offset):* Modifies UEL on an isolated branch (`f42_experimental_offset_uel.for`); ingests $\mathbf{u}_0$; evaluates direct continuation without reload.
- **Controlled 4-Step Verification Sequence:**
  1. *Step 1: Offline Transfer Verification:* Run Python mapping script, verifying coordinate alignment, field interpolation, and computing the exact discrete residual norm $\|\mathbf{R}_{\text{internal}, 0}\|$.
  2. *Step 2: Abaqus Datacheck:* Execute `abaqus datacheck` on recipient deck (`M1_MC_C1_FORWARD_14K.inp`) to verify keyword syntax, card wrapping, and memory allocation.
  3. *Step 3: Single-Increment Equilibrium Solve:* Execute 1 increment at $\Delta u = 0$ to measure initial Newton convergence iterations, relaxation displacement $\|\delta \mathbf{u}\|$, and entry reaction force $RF_{\text{recip}}$.
  4. *Step 4: Short Forward Solve:* Advance 50 increments ($u \in [0.0050, 0.0055]\,\text{mm}$) to verify numerical stability before any full fracture solve.
- **Governance Guard:** None of these solver steps are executed without explicit supervisor authorization. General PBS permission does NOT authorize C1 solver execution.
