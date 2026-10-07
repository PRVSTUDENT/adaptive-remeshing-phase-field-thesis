# Mode-II Gate M2-2 Predeclared Acceptance Criteria & Evaluation Protocol

**Benchmark:** Pandey & Kumar (2025) Section 4.2 Mode-II Pre-Analysis  
**Job Identifier:** `M2_J1_MIEHE_HORIZON` (PBS Job ID `1410790.mmaster02`)  
**Input Deck:** `Job-1_UEL_paper_horizon.inp` (SHA-256 `BCFC850EDD07B9DC0BEC36FA8A795A5A0F55EFA4CA75A584784862F41D3F04F5`)  
**Constitutive Subroutine:** `f42_mixed_uel_mode2_miehe.for` (SHA-256 `75029EF77CAA1677D2B1557CFF5B1DE61725B17FC380B9B27D37AED3EFCF4D9A`)  
**Mesh Discretization:** 2,960 finite elements (2,860 CPE4 + 100 CPE3), 3 co-located layers (8,880 total cards), 3,036 FE nodes.  
**Governing Phase:** `MODE2_REPRODUCTION_ACTIVE_HUMAN_AUTHORIZED_PREMEETING`  

---

## 1. Predeclared Acceptance Checks (Codified Prior to Terminal State)

To ensure zero post-hoc scientific adjustment or confirmation bias, the following 8 acceptance criteria are declared prior to solver completion:

| Check # | Evaluation Criterion | Governing Threshold / Rule | Falsification Condition |
| :---: | :--- | :--- | :--- |
| **AC-1** | **Displacement History & Boundary Conditions** | Step 1: $u_x \in [0.0, 0.0100]\,\text{mm}$ (2000 incs, $\Delta u_1 = 5.0\,\text{nm}$).<br>Step 2: $u_x \in [0.0100, 0.0200]\,\text{mm}$ (2000 incs, $\Delta u_2 = 5.0\,\text{nm}$).<br>Bottom pinned/roller ($u_x=u_y=0$), Top roller ($u_y=0, u_x = \text{prescribed}$). | Any deviation from uniform $5.0\,\text{nm/inc}$ or improper constraint. |
| **AC-2** | **Constitutive Formulation & Hash Immutability** | `f42_mixed_uel_mode2_miehe.for` SHA-256 `75029EF7...` identical across cluster worktree and scratch.<br>Protected Mode-I UEL hash `CE8D5EDC...` 100% untouched. | Any hash discrepancy or unintended modification of constitutive equations. |
| **AC-3** | **Displacement Horizon Attainment** | Solver successfully executes all 4,000 increments to terminal $u_x = 0.0200\,\text{mm}$ ($20.0\,\mu\text{m}$), fully covering Pandey & Kumar Figs. 12 and 13(a). | Job aborts prematurely or walltime expires before $u_x = 0.0200\,\text{mm}$. |
| **AC-4** | **Convergence Stability & Cutback Absence** | Solver integrates smoothly with standard Newton-Raphson convergence (nominal 1–3 iterations per increment, 0 cutbacks). | Repeated cutbacks, severe iteration divergence ($>10$ iters), or step failure. |
| **AC-5** | **Raw MISESERI Presence & Element Recovery** | Element output field `MISESERI` populated on `All_elem` across both Step-1 and Step-2 frames. Exact 2,960 scalar values extracted per frame. | Missing `MISESERI` in ODB field outputs or corrupt recovery field. |
| **AC-6** | **Indicator Localization vs Unzipping Artifact** | In Step-1 ($u_x \le 0.0100\,\text{mm}$), MISESERI peak localizes at the sharp slit tip ($x=0.50, y=0.50$) with high-error process zone oriented into the lower right quadrant ($y \le 0.50, x \ge 0.50$), rather than unzipping horizontally along $y=0.50$. | MISESERI concentrates primarily along horizontal symmetry line or upper quadrant. |
| **AC-7** | **Physical Epistemology: Error Indicator vs Crack Path** | MISESERI is evaluated strictly as a linear-elastic stress recovery discretization error indicator; phase-field damage $d(x, y)$ is evaluated as the true fracture path. The two fields are distinguished explicitly. | Claiming MISESERI "is the crack" or confusing elastic error recovery with phase-field kinetics. |
| **AC-8** | **Strict Sequential Gate Hold on Remeshing** | Strictly NO native remeshing execution, NO adapted mesh generation, and NO submission of `Job-2_UEL.inp` until M2-2 terminal evidence is fully extracted and reviewed. | Launching native remeshing or Step-2 fracture jobs prematurely. |

---

## 2. Target Snapshot Extraction Matrix

The post-processing extraction pipeline (`extract_mode2_paper_horizon_terminal_evidence.py`) will automatically extract the exact state at the 5 benchmark levels:

1. **State 1 ($u_x = 0.00936\,\text{mm} = 9.36\,\mu\text{m}$):**
   - Corresponding to Pandey & Kumar (2025) Fig. 12(a).
   - Expected physical state: Linear-elastic response, pre-initiation stress singularity at slit tip, $d_{\max} \approx 0.0$.
2. **State 2 ($u_x = 0.01000\,\text{mm} = 10.0\,\mu\text{m}$):**
   - Step-1 terminal frame (transition between linear pre-analysis and crack propagation).
   - Base state for pre-analysis MISESERI adaptive remeshing.
3. **State 3 ($u_x = 0.011842\,\text{mm} = 11.84\,\mu\text{m}$):**
   - Corresponding to Pandey & Kumar (2025) Fig. 12(b).
   - Expected physical state: Onset of phase-field damage localization ($d \to 1.0$) at slit tip, forming oblique downward initiation band ($\theta \approx -45^\circ$ to $-50^\circ$).
4. **State 4 ($u_x = 0.01626\,\text{mm} = 16.26\,\mu\text{m}$):**
   - Corresponding to Pandey & Kumar (2025) Fig. 12(c).
   - Expected physical state: Fully developed curved shear crack extending towards the bottom-right boundary, terminal load drop in progress.
5. **State 5 ($u_x = 0.02000\,\text{mm} = 20.0\,\mu\text{m}$):**
   - Complete physical separation ($F_x \to 0$), terminal simulation horizon.

---

## 3. Post-Extraction Workflow Sequence

1. Wait for PBS Job `1410790.mmaster02` to reach `COMPLETED` (`F` in PBS).
2. Execute `run_postprocessing_extraction.sh` on the cluster.
3. Validate extracted datasets against AC-1 through AC-7.
4. Render `mode2_paper_horizon_miseseri_damage_evolution.png` and `.pdf`.
5. Compile comprehensive M2-2 closeout evaluation report in `project_coordination/sessions/`.
6. Only upon complete pass of Gate M2-2 may the project proceed to prepare Gate M2-3 (Pre-analysis adaptive remeshing rule definition).
