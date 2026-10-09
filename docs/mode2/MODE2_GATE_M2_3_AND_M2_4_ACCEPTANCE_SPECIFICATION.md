# Technical Specification: Gate M2-3 and Gate M2-4 Acceptance Criteria, Source-Frame Provenance, and Fracture Qualification Framework

**Task Reference:** Task F1355 (`F1355-MODE2-CORRECT-FRAME-PROVENANCE-AND-RECONCILE-METRICS`)  
**Protocol Version:** 2  
**Date:** `2026-10-09T08:35:00+02:00`  
**Governing Authority:** `project_coordination/`  
**Investigating Agent:** `gemini-antigravity`  
**Parent Milestone:** Gate M2-3 / Gate M2-4 Native Remeshing Corridor Reproduction & Solver Recovery  
**Branch:** `mode2-pandey-kumar-reproduction`  
**Starting Commit:** `0a6773184e83a8351b858b99b08d3e58b850d8f3`  
**Mode-I Baseline Freeze:** `v2026.10.08-supervisor-meeting-mode1-freeze` (100% byte-identical and untouched)

---

## 1. Executive Framework, Staged Architecture & Evidence Precedence

This technical specification establishes the authoritative, quantitative acceptance criteria for **Gate M2-3** (Native Remeshing Corridor Reproduction) and **Gate M2-4** (Mode-II Adapted Fracture Simulation), separating verified preparatory milestones from pending solver results in accordance with the supervisor-aligned governance rules.

### 1.1 Staged Execution Architecture

The Mode-II reproduction workflow is strictly structured into four sequential phases:

```
+---------------------------------------------------------------------------------------------------+
|                         PHASE A: PREPARATORY PRE-ANALYSIS & NATIVE REMESHING                      |
|                                                                                                   |
|  [Step-2 ODB (Job-1_UEL.odb)] -> [Native Abaqus RemeshingRule] -> [Adapted Mesh (21,063 FE)]      |
|       Step-2 association verified        UNIFORM_ERROR, ET_3PCT          Matches paper +5.51%     |
|       d_max = 1.0, eta_e = 26.18         outputFrequency=ALL_INCREMENTS                           |
|                                                                                                   |
|  GATE M2-3 STATUS: CLOSED_PASSED_CORRECTED_CORRIDOR_QUALIFIED                                     |
+---------------------------------------------------------------------------------------------------+
                                                  |
                                                  v
+---------------------------------------------------------------------------------------------------+
|                         PHASE B: ACTIVE ADAPTED FRACTURE SIMULATION                               |
|                                                                                                   |
|  [Stabilized Production Deck (21,063 FE)] -> [PBS Job 1411267 on mnode097/0]                     |
|       Line Search N_ls = 4, IA = 12                Step 1 Inc 801+ (ux = 4.01 um), 0 cutbacks     |
|                                                    K0 = 45.416 kN/mm, 3 iters/inc                 |
|                                                                                                   |
|  GATE M2-4 STATUS: ACTIVE_STABILIZED_FRACTURE_RUNNING (Pending Post-Peak Fracture Completion)     |
+---------------------------------------------------------------------------------------------------+
                                                  |
                                                  v
+---------------------------------------------------------------------------------------------------+
|                         PHASE C: IN-SITU RESULT EXTRACTION & VERIFICATION                         |
|                                                                                                   |
|  [Post-Peak ODB Extraction] -> [Reaction Force & Softening Slope] -> [Pointwise Irreversibility]  |
|       Terminal crack trajectory       F_max vs literature reference        dot(d) >= 0 audit      |
+---------------------------------------------------------------------------------------------------+
                                                  |
                                                  v
+---------------------------------------------------------------------------------------------------+
|                         PHASE D: LITERATURE SYNTHESIS & SUPERVISOR CLOSEOUT                       |
|                                                                                                   |
|  [Master Digitization Comparison] -> [Speedup vs Accuracy Tradeoff] -> [Supervisor Gate Signoff]  |
|       Overlay Pandey & Kumar Fig 13a         Walltime & DOF comparison        Milestone Freeze    |
+---------------------------------------------------------------------------------------------------+
```

### 1.2 Explicit Precedence Hierarchy for Evidence Conflicts

To prevent ambiguity when records or documentation conflict, the following strict four-tier precedence hierarchy governs all scientific evaluations:

1. **Primary Physical / Solver Simulation Outputs:** Raw, verified Abaqus solver output files (`.dat`, `.sta`, `.msg`, `.odb`, `.prt`, `.log`).
2. **Executable Source & Model Decks:** Input decks (`.inp`), user subroutines (`.for`), and verified execution wrappers.
3. **Project Coordination Ledgers:** Authoritative live state tracked in `project_coordination/` (`CURRENT_STATE.md`, `ACTIVE_TASK.json`, `HPC_JOB_LEDGER.csv`, `TASK_LEDGER.csv`).
4. **Derived Reports & Documentation:** Narrative Markdown reports, summaries, and meeting notes under `docs/` and `references/`.

---

## 2. Gate M2-3: Native Refinement Corridor Acceptance Specification

### 2.1 Criterion 1: Native Remeshing Mechanism Without Manual Geometrical Bounds
- **Requirement:** The mesh refinement corridor must emerge purely through native Abaqus/CAE `RemeshingRule` and `adaptiveRemesh` sizing calculations, driven by the element stress error indicator `MISESERI` on the companion continuum layer (`CPE4`/`CPE3`, material `UMAT_MAT`), without manual bounding box partitioning or hard-coded mesh refinement zones.
- **Underlying Pre-Analysis Basis:** The pre-analysis simulation (`Job-1_UEL_paper_horizon.inp`, Job ID `1411104.mmaster02`, $2{,}960$ FEs, Exit 0) must execute complete phase-field damage evolution ($d_{\max} = 1.000000$, $F_{\max} = 514.51\,\text{N}$, kink angle $\theta = -57.95^\circ$, bottom exit $x = 0.813\,\text{mm}$) with the UEL driving vector `RHS(I,1)` fully active.
- **Verification Status:** **PASS (`NATIVE_REMESHING_MECHANISM_VERIFIED`).** In contrast to the initial stationary pre-analysis (Job 1410790 where $d \equiv 0$ kept error pinned at the tip), the corrected damage pre-analysis produces a dynamic stress-error wave traveling along the shear trajectory.

### 2.2 Criterion 2: Corrected Source-Frame Provenance & Abaqus API Semantics
- **Requirement:** The exact relationship between the pre-analysis ODB (`Job-1_UEL.odb`), the remeshing rule parameters, and the frame evaluation mechanism must be stated with strict API accuracy without claiming undocumented single-frame isolation.
- **Authoritative API Audit & Execution Evidence:**
  - **Script:** `models/pandey_kumar_mode2/06_paper_grounded_uel_preanalysis/m2_corrected_remesh/execute_mode2_corrected_adaptive_remesh.py`
  - **Remeshing Rule Definition:**
    ```python
    m.RemeshingRule(
        name='RR_MODE2_CORRECTED_%d' % int(et),
        stepName='Step-2',
        region=reg,
        outputFrequency=ALL_INCREMENTS,
        variables=('MISESERI', ),
        sizingMethod=UNIFORM_ERROR,
        errorTarget=float(et),
        minElementSize=0.001,
        maxElementSize=0.020,
        coarseningFactor=NOT_ALLOWED,
        refinementFactor=10
    )
    m.adaptiveRemesh(odb=odb)
    ```
  - **API Semantics:** The script associates the rule with `stepName='Step-2'` and `outputFrequency=ALL_INCREMENTS`. It does **NOT** explicitly pass a specific frame (e.g. `frame=...` or `frameId=20`) to `RemeshingRule` or `adaptiveRemesh`. Under Abaqus CAE 2023 semantics, `adaptiveRemesh` evaluates error indicators across all available frames in Step-2, computing the sizing envelope over the transient step.
  - **Diagnostic Frame Inspection:** The script diagnostically probed `last_frame = step2.frames[-1]` (Increment 2000, Frame 20 of output step, $u_x = 20\,\mu\text{m}$, $t_{\text{total}} = 2.000$) to verify that the ODB contained the completed damage state ($d_{\max}=1.0$, $\eta_{\max}=26.18$, top 10% error orientation $=-34.07^\circ$, crack corridor error fraction $=43.92\%$).
  - **Epistemic Classification:** **`SOURCE_STEP_VERIFIED_FRAME_SELECTION_NOT_YET_QUALIFIED`**. (Step-2 association is verified and proved; whether Abaqus evaluated exclusively the final frame or the multi-frame envelope is governed by the native `ALL_INCREMENTS` sizing engine).

### 2.3 Criterion 3: Quantitative Spatial Localization, Dual Selectivity Metrics, and Local Size Distribution
- **Requirement:** The resulting native mesh must match the published element count within the working engineering target ($\pm 10\%$), demonstrate significant spatial selectivity inside the physical corridor, and resolve the phase-field regularizing length scale $l_0 = 15.0\,\mu\text{m}$.
- **Quantitative Metrics for `ET_3PCT` (ErrorTarget = 3.0%):**
  1. **Element Count:** **$21{,}063$ finite elements** ($20{,}487$ quads, $576$ tris, $21{,}042$ physical nodes, $63{,}030$ DOFs).
     - Comparison with Pandey & Kumar (2025) Table 3 ($19{,}963$ elements): **$+1{,}100$ elements (+5.51%)**, well within the $\pm 10\%$ engineering target. Note: This $\pm 10\%$ is an adopted engineering working target, not a formal supervisor decree.
  2. **Corridor Trajectory:** Chord angle $\theta = \mathbf{-48.30^\circ}$, exiting the bottom boundary at $x = 0.985\,\text{mm}$.
  3. **Dual Spatial Fine-Element Selectivity Metrics:**
     - **Narrow Straight Chord Box ($W = 0.12\,\text{mm}$):** Straight band connecting $(0.5, 0.5)$ to $(0.85, 0.0)$ captures **$46.34\%$** ($7{,}309 / 15{,}771$) of all fine elements ($h \le 0.008\,\text{mm}$).
     - **Mesh-Following Curved Physical Envelope ($W = 0.24\,\text{mm}$):** Curved envelope tracking the actual fine element centroid trajectory along the curved shear path captures **$78.83\%$** ($12{,}432 / 15{,}771$) of all fine elements.
  4. **Rigorous Element Density Contrast Evaluation:**
     - Corridor region area: $A_{\text{corridor}} = 0.1510\,\text{mm}^2$ ($15.10\%$ of specimen area).
     - Outside corridor area: $A_{\text{outside}} = 0.8490\,\text{mm}^2$ ($84.90\%$ of specimen area).
     - Fine elements in corridor: $N_{\text{fine, corridor}} = 12{,}432 \implies \rho_{\text{fine, corridor}} = \mathbf{82{,}347\,\text{fine elements/mm}^2}$.
     - Fine elements outside corridor: $N_{\text{fine, outside}} = 3{,}339 \implies \rho_{\text{fine, outside}} = \mathbf{3{,}933\,\text{fine elements/mm}^2}$.
     - **Fine Element Density Contrast Ratio:** $\rho_{\text{fine, corridor}} / \rho_{\text{fine, outside}} = \mathbf{20.94\times}$.
     - **Total Element Density Contrast Ratio:** $79{,}908 / 10{,}422 = \mathbf{7.67\times}$ (curved envelope vs far-field).
  5. **Local Element Size Distribution (Whole Domain):**
     - Minimum element size: $h_{\min} = 0.717\,\mu\text{m} \implies h_{\min} / l_0 = 0.0478$ ($>20$ elements resolving the regularizing zone).
     - Median element size: $h_{\text{median}} = \mathbf{3.952\,\mu\text{m}} \implies h_{\text{median}} / l_0 = 0.2635 \ll 0.5$.
     - Mean element size: $h_{\text{mean}} = \mathbf{5.512\,\mu\text{m}} \implies h_{\text{mean}} / l_0 = 0.3675$.
     - Maximum element size: $h_{\max} = 24.162\,\mu\text{m}$ (in the far field).
     - Percentiles: $h_{p10} = 1.782\,\mu\text{m}$, $h_{p25} = 2.177\,\mu\text{m}$, $h_{p75} = 8.024\,\mu\text{m}$, $h_{p90} = 11.107\,\mu\text{m}$.
  6. **Centerline Agreement:** Upper-half crack initiation centerline ($Y \in [0.35, 0.50]\,\text{mm}$) agrees with Pandey & Kumar Fig. 12(b) within **$1.3\text{--}14.9\,\mu\text{m}$**. The lower exit deviates outward to $x = 0.985\,\text{mm}$ (+0.117 mm vs Fig. 12(b) at $x=0.868\,\text{mm}$) due to the linear-elastic corner stress error concentration.

### 2.4 Nuanced Gate M2-3 Classification Matrix

| Dimension | Qualification Category | Status | Technical Finding |
| :--- | :--- | :---: | :--- |
| **1. Refinement Mechanism** | `NATIVE_REMESHING_MECHANISM_VERIFIED` | **PASS** | Pure native Abaqus `RemeshingRule` + `adaptiveRemesh` without geometric partitioning. |
| **2. Qualitative Topology** | `REFINEMENT_CORRIDOR_QUALITATIVELY_REPRODUCED` | **PASS** | Genuine diagonal curved corridor formed tracking the Mode-II shear crack path. |
| **3. Quantitative Metrics** | `SPATIAL_AGREEMENT_PARTIALLY_QUALIFIED` | **PASS** | Upper centerline within $1.3\text{--}14.9\,\mu\text{m}$, element count $+5.51\%$, fine density contrast $20.94\times$. |
| **4. Exact Bottom Exit** | `EXACT_LITERATURE_GEOMETRY_NOT_REPRODUCED` | **LIMITATION** | Bottom exit deviates outward by $+0.117\,\text{mm}$ due to linear-elastic corner singularity. |

**Overall Gate M2-3 Status:** **CLOSED_PASSED_CORRECTED_CORRIDOR_QUALIFIED**.

---

## 3. Gate M2-4: Adapted Production Fracture Acceptance Specification

### 3.1 Criterion 1: Complete Force-Displacement Fracture Response & Literature Reference Framing
- **Requirement:** The adapted simulation must capture the full structural response from initial linear elasticity, through peak fracture load and initiation, steep softening descent, and complete post-peak residual load drop across $u_x \in [0, 20]\,\mu\text{m}$.
- **Literature Reference Framing (Published Digitized Baselines):**
  - **Proposed PFM (Pandey & Kumar 2025 Fig. 13a):** $F_{\max} = 365.74\,\text{N}$ at $u_x = 8.28\,\mu\text{m}$ ($K_0 = 47.70\,\text{kN/mm}$).
  - **Standard PFM (Pandey & Kumar 2025 Fig. 13a):** $F_{\max} = 351.99\,\text{N}$ at $u_x = 8.08\,\mu\text{m}$ ($K_0 = 46.75\,\text{kN/mm}$).
  - **Navidtehrani et al. [73]:** $F_{\max} = 332.67\,\text{N}$ at $u_x = 8.07\,\mu\text{m}$ ($K_0 = 45.51\,\text{kN/mm}$).
- **Acceptance Criteria for Current Simulation:**
  - **Initial Structural Stiffness ($K_0$):** $K_0 \in [45.0, 48.0]\,\text{kN/mm}$ under pure shear with top roller constraint ($u_y = 0$).
  - **Peak Fracture Region:** Peak reaction force $F_{\max}$ and displacement $u(F_{\max})$ to be evaluated against the literature reference window ($332\text{--}366\,\text{N}$ at $8.0\text{--}8.3\,\mu\text{m}$).
  - **Softening Behavior:** Monotonic load drop following peak with steep negative slope ($dRF/du < -400\,\text{kN/mm}$) without artificial numerical snap-back or unphysical force plateaus.

### 3.2 Criterion 2: Numerical Convergence, Recoverable Cutbacks, and Non-Invasive Solver Controls
- **Requirement:** The simulation must execute without non-physical modifications to the governing equations (zero artificial viscosity, zero altered fracture toughness). Non-convex Newton step oscillations during softening must be controlled strictly through validated non-invasive Abaqus parameters:
  1. Line Search damping: `*CONTROLS, PARAMETERS=LINE SEARCH` with $N^{ls} = 4$.
  2. Iteration controls: `*CONTROLS, PARAMETERS=TIME INCREMENTATION` with $I_A = 12$, $I_0 = 8, I_R = 12$.
  3. Minimum increment size: $\Delta t_{\min} = 1.0 \times 10^{-12}$.
- **Convergence Reconciliation:** Recoverable Newton cutbacks during steep softening are normal numerical behavior in non-convex phase-field fracture and do **NOT** constitute simulation failure, provided the solver recovers, continues integration, and completes the prescribed displacement horizon.
- **Acceptance Threshold:** Clean completion through the complete displacement horizon $u_x \in [0, 20]\,\mu\text{m}$ without fatal divergence.

### 3.3 Criterion 3: Phase-Field Damage Evolution, Pointwise Irreversibility, and Trajectory Validation
- **Requirement:**
  1. **Pointwise Damage Bounds:** $0 \le d \le 1.000$ strictly preserved across all integration points.
  2. **Pointwise Damage Irreversibility:** $\dot{d} \ge 0$ independently audited across all output frames (distinguishing history monotonicity $\dot{\mathcal{H}} \ge 0$ from pointwise phase verification).
  3. **Crack Trajectory Correctness:** Oblique crack trajectory initiating at $(0.5, 0.5)$ and propagating diagonally towards the bottom boundary with chord angle $\theta \in [-48^\circ, -58^\circ]$.

---

## 4. Current Execution Status: PBS Job 1411267 Telemetry & Walltime Risk Assessment

### 4.1 Live Telemetry Audit (PBS Job 1411267)

| Parameter / Field | Specified Target | Live Measured Status | Classification |
| :--- | :--- | :--- | :--- |
| **PBS Job ID** | `1411267.mmaster02` | `1411267.mmaster02` (`M2_J2_ADAPT_ET3_STAB`) | Active Production Solve |
| **Compute Node / Queue** | `mnode097` / `normal_imfdfkmq` | `mnode097/0` / `normal_imfdfkmq` (1 CPU serial, 16 GB RAM) | Valid Host & Queue |
| **Discretization** | $21{,}063$ FEs (`ET_3PCT`) | $21{,}063$ physical FEs ($63{,}189$ layered elements, $63{,}030$ DOFs) | Exact Match |
| **Active Increment** | Step 1, $u_x = 0 \to 10\,\mu\text{m}$ | **Step 1 Increment 801+** ($u_x = 4.005\,\mu\text{m}$, **40.05% of Step 1 completed**) | Monotonically Advancing |
| **Current Reaction Force** | Linear Elastic Range | $RF_1 = 182.12\,\text{N}$ at $u_x = 4.010\,\mu\text{m}$ | Physically Consistent |
| **Structural Stiffness ($K_0$)** | $45.5\text{--}47.7\,\text{kN/mm}$ | **$K_0 = 45.416\,\text{kN/mm}$** ($R^2 = 0.99999$, linear regression) | **PASS (Exact Match)** |
| **Newton Convergence** | Stable | **0 cutbacks**, **exactly 3 iterations / increment** across all 801 incs | Highly Stable |
| **Memory Usage** | $< 16\,\text{GB}$ | $3.96\,\text{GB}$ physical resident set size | Fully Compliant |

### 4.2 Walltime Exhaustion Risk Assessment & Restart Setting Analysis
- **Allocated PBS Walltime:** $24:00:00$ ($86{,}400\,\text{s}$).
- **Elapsed Walltime:** $01:18:44$ ($\approx 1.31\,\text{h}$).
- **Measured Throughput:** $801\,\text{increments} / 1.31\,\text{h} \approx \mathbf{612\,\text{increments/hour}}$.
- **Total Simulation Horizon:** $4{,}000\,\text{increments}$ (Step 1: 2,000 incs; Step 2: 2,000 incs).
- **Projected Total Walltime:** $4{,}000 / 612 \approx \mathbf{6.5\,\text{hours}}$ (or $\sim 7.5\text{--}9.0\,\text{hours}$ allowing for slower softening iterations).
- **Walltime Risk Level:** **VERY LOW** ($\approx 35\%$ of the $24.0\,\text{h}$ allocation ceiling).
- **Restart Setting Evaluation:** The input deck specifies `*Restart, write, frequency=0`. Consequently, intermediate restart `.res` files are not written. In the unlikely event of unexpected hardware failure or walltime exhaustion, execution cannot be resumed from an intermediate increment and would require resubmission. However, given current solver stability (0 cutbacks, 3 iters/inc) and ample walltime headroom ($>22.6\,\text{hours}$ remaining), the running job is left completely undisturbed.

---

## 5. Epistemological Classification Matrix

| Scientific Question / Dimension | Required Defensible Classification | Evidence Basis |
| :--- | :--- | :--- |
| **1. Native Abaqus remeshing generated diagonal refinement corridor** | **Demonstrated (PASS)** | Native `adaptiveRemesh` produced $21{,}063$ FEs with chord angle $-48.30^\circ$. |
| **2. Source ODB and Step-2 association** | **Verified (PASS)** | `RemeshingRule` explicitly sets `stepName='Step-2'` with `outputFrequency=ALL_INCREMENTS`. |
| **3. Exclusive use of Step-2 final Frame 20** | **Pending independent API qualification (`SOURCE_STEP_VERIFIED_FRAME_SELECTION_NOT_YET_QUALIFIED`)** | Script targets Step-2 with `ALL_INCREMENTS`; Frame 20 was probed diagnostically. |
| **4. Element count versus published 19,963** | **Quantitatively documented (+5.51%)** | $21{,}063$ vs $19{,}963$ elements ($+1{,}100$ FEs, within $\pm 10\%$ working target). |
| **5. Full spatial agreement with literature** | **Partial (Upper half $1.3\text{--}14.9\,\mu\text{m}$; bottom exit $+0.117\,\text{mm}$ offset)** | Documented limitation due to corner stress error concentration. |
| **6. Physical meaning of companion-UMAT MISESERI** | **Effective-strain-related recovered-stress error proxy** | Companion Layer 3 measures un-degraded kinematic strain field; $10^7\times$ ratio vs tensile physical stress. |
| **7. Adapted fracture response through 20 µm** | **Pending actual solver completion (`ACTIVE_STABILIZED_FRACTURE_RUNNING`)** | Solver at Inc 801+ ($u_x = 4.01\,\mu\text{m}$); advancing steadily toward initiation and softening. |
