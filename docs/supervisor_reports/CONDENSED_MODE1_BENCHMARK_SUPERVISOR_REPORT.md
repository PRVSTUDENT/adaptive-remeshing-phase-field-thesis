# Mode-I Phase-Field Fracture Benchmark: Adaptive Remeshing & Scientific Reproduction Report

**Document Identifier**: `docs/supervisor_reports/CONDENSED_MODE1_BENCHMARK_SUPERVISOR_REPORT.md`  
**Author**: Pruthviraja Reddy Vandavagali (Matriculation No. 68865)  
**Supervisors**: Prof. Dipl.-Ing. Björn Kiefer, Ph.D., and Dr.-Ing. Stephan Roth  
**Institution**: Institute of Mechanics and Fluid Dynamics (IMFD), TU Bergakademie Freiberg  
**Date**: September 11, 2026  
**Governing Directive**: *"We need to have understood everything related to the first model before we increase complexity."*  
**Scientific Status**: `GATE6_ANOMALY_RESOLVED_REQUALIFICATION_VERIFIED` & `GATE5_LITERATURE_EFFECTIVE_ERROR_TARGET_NOT_ESTABLISHED`  

---

## Chapter 1: Benchmark Problem Definition

### 1.1 Boundary Value Problem (BVP) Specification
The foundational benchmark investigated throughout this thesis is the 2D square plate with a sharp horizontal edge crack under monotonic tensile Mode-I loading:
- **Domain Geometry**: $\Omega = [0.0, 1.0]\,\text{mm} \times [0.0, 1.0]\,\text{mm}$ ($L = 1.0\,\text{mm}, W = 1.0\,\text{mm}$).
- **Initial Crack Representation**: Horizontal zero-gap sharp slit seam along $y = 0.5\,\text{mm}$, spanning $x \in [0.0, 0.500]\,\text{mm}$ ($a_0 = 0.500\,\text{mm}$). (A finite-width blunt notch was proven in earlier diagnostic audits to alter structural compliance by $\approx 45\%$, and is strictly excluded; the zero-gap seam is the mandatory benchmark representation).
- **Boundary Conditions**:
  * Bottom boundary ($y = 0.0\,\text{mm}$): Roller supported ($u_y = 0.0\,\text{mm}$), with pinned origin $(0, 0)$ ($u_x = 0, u_y = 0$) to eliminate rigid-body translation.
  * Top boundary ($y = 1.0\,\text{mm}$): Monotonic displacement-controlled tensile extension ($u_y = \bar{u}$, with $u_x = 0$ in the standard clamped benchmark).
- **Material & Phase-Field Constitutive Constants**:
  * Young's modulus: $E = 210.0\,\text{GPa} = 210.0\,\text{kN/mm}^2$
  * Poisson's ratio: $\nu = 0.30$
  * Critical fracture energy release rate: $G_c = 2.70 \times 10^{-3}\,\text{kN/mm} = 2.70\,\text{kJ/m}^2$
  * Regularization length scale: $\ell_0 = 0.0075\,\text{mm} = 7.5\,\mu\text{m}$.

### 1.2 Expected Physical Response Progression
Under monotonic tensile displacement $\bar{u}$:
1. **Linear-Elastic Regime**: Initial uniform elastic stretching with global structural stiffness $K_0 \approx 138.0\,\text{kN/mm}$.
2. **Crack-Tip Localization**: Diffuse phase-field damage growth ($0 < d < 1$) concentrated in an elliptic zone of width $\sim 2\ell_0$ around $(0.500, 0.500)\,\text{mm}$.
3. **Peak Reaction Force**: Softening onset at peak load $F_{\max} \approx 0.758\,\text{kN}$ near displacement $u(F_{\max}) \approx 0.00586\,\text{mm}$.
4. **Sharp Post-Peak Rupture**: Sudden catastrophic propagation of fully damaged material ($d \approx 1.0$) horizontally along the ligament line $y = 0.500\,\text{mm}$ toward $x = 1.0\,\text{mm}$, with immediate force drop to zero.

---

## Chapter 2: Conventional Fixed-Mesh Reference Anchor

### 2.1 Quantitative Baseline Reference
To evaluate adaptive remeshing defensibly, the conventional structured fixed-mesh model is established as the mandatory quantitative reference anchor:
> *"This is the reference response that my adaptive solution must reproduce to an acceptable accuracy."*

- **Structured Quad Reference Discretization (Job `1398090`, $15,192$ finite elements)**:
  * Element formulation: 4-node plane strain displacement elements (`JTYPE = 2`, `CPE4` topology) coupled to 4-node phase-field elements (`JTYPE = 1`).
  * Mesh sizing: Uniform refined corridor of element size $h = 0.0015\,\text{mm} = \ell_0 / 5$ along the propagation band.
  * Canonical Initial Elastic Stiffness: $K_0 = \mathbf{137.945520\,\text{kN/mm}}$ ($R^2 = 0.99999960$, unconstrained OLS over $0 < u \le 0.001000\,\text{mm}$, $N=400$ uniform increments, intercept $F_0 = 4.472\times 10^{-5}\,\text{kN}$).
  * Peak Reaction Force: $F_{\max} = \mathbf{0.757778\,\text{kN}}$ ($-0.029\%$ vs $0.7580\,\text{kN}$ literature reference).
  * Displacement at Peak: $u(F_{\max}) = \mathbf{0.005857\,\text{mm}}$ ($-0.051\%$ vs $0.005860\,\text{mm}$ literature reference).
  * External Work Integral ($u \le 0.0070\,\text{mm}$): $W_{\text{pre}} = \mathbf{2.3017\,\text{mJ}}$, $W_{\text{post}} = \mathbf{0.0567\,\text{mJ}}$, $W_{\text{total}} = \mathbf{2.3584\,\text{mJ}}$ ($2,358.39\,\mu\text{J}$).
  * Serial Walltime: $23,460\,\text{s}$ ($06\text{h }31\text{m}$, 7,000 increments, 0 cutbacks).

> [!NOTE]
> **Complete UEL Energy Balance Status**: In the user-element (UEL) formulation, Abaqus' built-in `ALLSE` and `ALLFD` energy arrays are not assembled. Therefore, global energy quantities are reported as external boundary work $W_{\text{ext}} = \int F\,du$, governed by `COMPLETE_UEL_ENERGY_BALANCE_NOT_AVAILABLE`.

---

## Chapter 3: The Pandey–Kumar Adaptive Remeshing Method

### 3.1 Two-Job Adaptive Workflow Architecture
The adaptive remeshing methodology established by Pandey & Kumar (2025) operates as a multi-layer pre-analysis and remeshing sequence:
1. **Coarse Linear Pre-Analysis (Job-1)**: A coarse continuum mesh ($2,906$ standard plane strain elements, $h_{\text{coarse}} = 0.02\,\text{mm}$) is subjected to linear-elastic tensile loading.
2. **Stress Discretization Error Estimation (\texttt{MISESERI})**: Abaqus Standard evaluates the recovered von Mises stress discretization error indicator using Zienkiewicz–Zhu Superconvergent Patch Recovery (SPR).
3. **Native Sizing Evaluation & Topology Generation (\texttt{RemeshingRule} & \texttt{adaptiveRemesh})**: Abaqus CAE reads the \texttt{MISESERI} field output from Job-1, evaluates required local element sizes according to the specified error target (`errorTarget`), and meshes a new refined part.
4. **UEL/UMAT Model Deck Reconstruction**: The exported physical mesh is split into co-located user element layers (`JTYPE = 1/3` for phase field, `JTYPE = 2/4` for mechanical momentum balance) and coincident zero-stiffness companion visualization elements (`CPE4`/`CPE3`).
5. **Nonlinear Fracture Execution (Job-2)**: The fully reconstructed deck is solved monotonically through complete crack propagation.

### 3.2 Physical Nature of \texttt{MISESERI}
- \texttt{MISESERI} is strictly a **recovered von Mises stress discretization error indicator on the linear-elastic continuum pre-analysis**.
- It is **not** a phase-field error indicator, and it is **not** a damage error indicator.
- Refinement is driven by elastic stress singularity gradients at the crack tip during the pre-analysis stage before any phase-field damage occurs.

---

## Chapter 4: Expected Refinement Behaviour

### 4.1 Theoretical Expectation Prior to Execution
Based on linear-elastic fracture mechanics (LEFM), the stress field in the vicinity of a sharp slit crack exhibits an $r^{-1/2}$ singularity:
$$\sigma_{ij}(r, \theta) \sim \frac{K_I}{\sqrt{2\pi r}} f_{ij}(\theta)$$
- **Crack-Tip Singularity Zone**: Discretization error is intensely localized around the crack tip $(0.500, 0.500)\,\text{mm}$. The adaptive remesher is expected to place dense refinement ($h_{\min} \approx 0.0015\,\text{mm}$) at the crack tip and along the expected horizontal ligament corridor $y = 0.500\,\text{mm}$.
- **Far-Field Boundary Regions**: In regions remote from the crack ($x \to 0, x \to 1, y \to 0, y \to 1$), stress gradients are mild, allowing coarse elements ($h_{\max} \approx 0.02\,\text{mm}$) to be retained to economize computational degrees of freedom.
- **Spatial Correspondence Verification**: The spatial distribution of the \texttt{MISESERI} element-field extraction confirms a strong rank correlation ($\rho = -0.739$) between error indicator magnitude and resulting element size. The crack tip zone contains $100.00\%$ elements finer than the global median, confirming correct spatial targeting.

---

## Chapter 5: Actual Adaptive Results, Anomaly Resolution & Requalification

### 5.1 Reconciled Master Fracture Comparison Table

The following table summarizes the authoritative mechanical response across the reference, defective predecessor, corrected requalification, and empirical sensitivity models:

| Simulation Model Description | PBS Job ID | FE Count | Canonical $K_0$ ($\text{kN/mm}$) | $\Delta K_0$ vs Ref (%) | Peak Force $F_{\max}$ ($\text{kN}$) | $\Delta F_{\max}$ (%) | Peak Displ $u(F_{\max})$ ($\text{mm}$) | $\Delta u_{\text{peak}}$ (%) | Pre-Peak $L_2$ RMS (kN) | External Work $W_{\text{ext}}$ ($\text{mJ}$) | Walltime (Serial) | Final Scientific Classification |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **Fixed Ref Anchor** | `1398090` | $15,192$ | $137.9455$ | **Anchor** | $0.757778$ | **Anchor** | $0.005857$ | **Anchor** | **Anchor** | $2.3584$ | $06\text{h }31\text{m}$ | **`SCIENTIFIC_ANCHOR`** |
| **Defective Nominal 1%** | `1399632` | $71,320$ | $122.3785$ | **$-11.28\%$** | $0.478203$ | **$-36.89\%$** | $0.004150$ | **$-29.14\%$** | $0.03924$ | $2.0069$ | $35\text{h }08\text{m}$ | **`DEFECTIVE_NSET_TRUNCATED_RUN`** |
| **Corrected Nominal 1%** | `1404306` | $71,320$ | $\mathbf{137.8208}$ | $\mathbf{-0.09\%}$ | $\mathbf{0.745325}$ | $\mathbf{-1.64\%}$ | $\mathbf{0.005750}$ | $\mathbf{-1.83\%}$ | $\mathbf{0.00062}$ | $2.5726^*$ | $19\text{h }25\text{m}$ | **`REQUALIFIED_NOMINAL_1PCT_PREPEAK_VERIFIED_POSTPEAK_LIMITED`** |
| **Empirical 2% Adaptive** | `1400395` | $15,396$ | $137.8437$ | **$-0.07\%$** | $0.748197$ | **$-1.26\%$** | $0.005775$ | **$-1.40\%$** | $0.00072$ | $2.9465$ | $07\text{h }51\text{m}$ | **`EMPIRICAL_2PCT_PARTIAL_RESPONSE_AGREEMENT_ONLY`** |
| **Empirical 5% Adaptive** | `1400396` | $4,194$ | $137.9662$ | $+0.01\%$ | $0.764964$ | $+0.95\%$ | $0.007060$ | $+20.54\%$ | $0.00016$ | $3.1544$ | $02\text{h }16\text{m}$ | **`COARSE_DELAYED_PEAK`** |

*Note on External Work: Evaluated over common overlap window $0 \le u \le 0.006774069\,\text{mm}$, Corrected Nominal 1% work is $W_{\text{ext}} = 2.5726\,\text{mJ}$ vs. Fixed Reference Anchor $W_{\text{ext}} = 2.3583\,\text{mJ}$ ($+9.09\%$ difference, $+0.2143\,\text{mJ}$).

### 5.2 Resolution of Priority Question A: The 71,320-Element Stiffness Anomaly Root Cause
The core discrepancy between the low initial stiffness branch ($\approx 122.38 - 122.60\,\text{kN/mm}$) and the reference branch ($\approx 138\,\text{kN/mm}$) has been **isolated and mathematically/empirically verified at the equation and boundary set level**:

1. **Abaqus Preprocessor Card Truncation Rule**:
   The Abaqus/Standard input preprocessor (`pre`) strictly enforces a maximum limit of **16 node entries per line** under free-format `*NSET` definitions without `GENERATE`. When an input deck writes $> 16$ items on a single line, `pre` parses only the first 16 entries and silently discards all remaining entries on that line, issuing a compiler warning in the `.dat` file. Controlled benchmark Job `1404318.mmaster02` confirmed this general parser rule.
2. **Kinematic Boundary Defect in Defective Decks**:
   In the defective 71,320-element meshes (Case 61, Cases 72b–79, and full-fracture Job 1399632), the bottom roller node set `N_BOTTOM` contained 150 node labels formatted onto a single data line. Abaqus parsed only nodes 1 to 16 ($0.55 \le x \le 1.0\,\text{mm}$). The remaining **134 boundary nodes ($0.0 \le x < 0.55\,\text{mm}$), including origin pin node 37 $(0, 0)$, had zero vertical constraint ($u_y$ completely unconstrained)**.
3. **Bottom-Edge Lift Mechanism**:
   Under tensile displacement at the top edge, the unconstrained bottom nodes lifted vertically by up to **$+0.2304\,\text{nm}$ ($46.07\%$ of applied stroke)**, drastically increasing specimen compliance and causing an apparent $-11.17\%$ stiffness deficit ($122.60\,\text{kN/mm}$ vs $138.02\,\text{kN/mm}$). Origin pin node 37 was constrained only in $u_x = 0$, leaving it free to lift by $+0.1930\,\text{nm}$ ($38.6\%$ of stroke).
4. **Equation-Level Recovery & Verification**:
   Re-formatting the card with $\le 16$ entries per line (`PK_M1_NOM1_FULL_FRACTURE_WRAPPED.inp`) fully restored all 150 boundary nodes and pin node 37 in the runtime ODB (Job `1404312.mmaster02`). This eliminated all spurious bottom lift ($u_2 \equiv 0.000\,\text{nm}$ identically) and immediately restored the canonical stiffness $K_0 = \mathbf{138.0210\,\text{kN/mm}}$ in the linear frozen context and **$137.8208\,\text{kN/mm}$** in the full-fracture solve (Job `1404306.mmaster02`).
5. **Retraction of Earlier Hypotheses**:
   The hypothesis `FACTORIAL_UNSYMM_X_COMPANION_CAUSAL_INTERACTION` is formally **`RETRACTED`**. Companion visualization elements and solver asymmetry cause $0.000\%$ stiffness change when boundary conditions are properly parsed.

### 5.3 Full-Fracture Requalification Response (Job 1404306) & Post-Peak Limitation
With the NSET truncation defect resolved, Job `1404306.mmaster02` executed the full monotonic fracture loading:
- **Linear Elastic Precision**: Canonical $K_0 = \mathbf{137.820804\,\text{kN/mm}}$ matches the fixed reference ($137.945520\,\text{kN/mm}$) to within **$-0.0904\%$**, completely recovering $+12.62\%$ from the defective predecessor ($122.378544\,\text{kN/mm}$).
- **Peak Reproduction**: $F_{\max} = \mathbf{0.745325\,\text{kN}}$ at $u_{\text{peak}} = \mathbf{0.005750\,\text{mm}}$, matching reference values to within $-1.64\%$ and $-1.83\%$ respectively.
- **Pre-Peak Trajectory Precision**: Over 2,752 converged increments up to peak load, the $L_2$ RMS error against the reference anchor is **$0.000625\,\text{kN}$** ($0.625\,\text{N}$). This demonstrates excellent recovery of the pre-peak elastic and hardening branch ($K_0 -0.09\%$, $F_{\max} -1.64\%$). Full trajectory recovery, however, cannot be claimed due to post-peak softening divergence and premature convergence termination.
- **Common-Overlap External Work**: Over the converged common overlap window $0 \le u \le 0.006774069\,\text{mm}$, external boundary work is $W_{\text{ext}} = \mathbf{2.5726\,\text{mJ}}$ for Job 1404306 versus $\mathbf{2.3583\,\text{mJ}}$ for the fixed reference anchor Job 1398090 ($+9.09\%$ or $+0.2143\,\text{mJ}$).
- **Exact Increment Bookkeeping**:
  * Step 1 (monotonic extension to $u = 0.0050\,\text{mm}$): **2,000 converged increments**.
  * Step 2 (crack initiation and propagation): **1,783 converged increments**.
  * Total successfully converged increments: **3,783 increments**.
  * Increment 1784 of Step 2 was attempted but never converged.
  * The Abaqus `.msg` summary statement "TOTAL OF 3784 INCREMENTS" indicates increment numbers attempted/opened, not converged count.
- **Cutbacks in Automatic Incrementation**: The solve recorded exactly **21 cutbacks in automatic incrementation** per the authoritative Abaqus `.msg` summary statement (`21 CUTBACKS IN AUTOMATIC INCREMENTATION`), superseding the preliminary count of 30 attempt lines in `.sta`.
- **Post-Peak Convergence Termination & Solver Telemetry Symptom**: At Step 2 increment 1784 ($u = 0.006774069\,\text{mm}$, reaction force $RF = 0.184465\,\text{kN}$, $24.7\%$ of peak load), automatic cutbacks reduced time increments until $\Delta t < \Delta t_{\min} = 1.0 \times 10^{-14}\,\text{s}$. Solver diagnostic output in `.msg` records large displacement corrections to the phase-field degree of freedom (DOF 3) at crack-tip node 61805 (largest correction $\Delta c_i = 0.05386$, increment $0.121$, residual force $-1.561 \times 10^{-3}\,\text{kN}$). This behavior is strictly a **numerical solver observation/symptom** during cutback; physical damage-field evolution remains unresolved pending terminal analysis of Job 1404454.

### 5.4 Priority Question B: Gate-5 71,320 vs 13,941 Discrepancy & Documentation Boundary
The persistent discrepancy between our publication-literal reconstruction (71,320 finite elements) and Pandey & Kumar's reported count ($\approx 13,941$ elements) was investigated through exhaustive isolated OFAT experiments:

1. **Software Release Invariance**:
   Clean twin simulations (Job `1404373.mmaster02`) across Dassault Systèmes Abaqus 2022 (Build `2021_09_15`) and Abaqus 2023 (Build `2022_09_28`) generated **100.000% bit-for-bit identical meshes** ($71,320$ elements at 1% error target; $17,687$ elements at 2% error target). Software release differences are definitively **ruled out** (`NO_RELEASE_EFFECT_DETECTED_FOR_THE_TESTED_CPE4_MODE1_CONFIGURATION`). (Note: The exploratory test with plane stress `CPS4` elements was retired/confounded because the physical BVP is strictly plane strain `CPE4`, and is not an active causal explanation).
2. **Pre-Analysis Load Level Invariance**:
   A 10-fold sweep of pre-analysis displacement ($0.2\times$ to $2.0\times$ baseline, Job `1404383.mmaster02`) confirmed that refined element counts remain invariant at $71,070 - 71,512$ ($\pm 0.3\%$). Load magnitude is **ruled out**.
3. **Discretization Breakdown**:
   Spatial partitioning into 5 normalized regions reveals that crack-tip element sizing is nearly identical between 1% and 2% ($h_{\text{median}} = 1.84\,\mu\text{m}$ vs $1.96\,\mu\text{m}$, differing by only $6.6\%$, both reaching the $1.0\,\mu\text{m}$ floor). Crucially, **$99.39\%$ of all surplus elements in the 71k mesh reside in the far-field bulk $R_5$ (+34,872 elements) and corridor flanks $R_2+R_3+R_4$ (+19,716 elements)**.
4. **The 4-Point Missing Information Boundary**:
   A rigorous textual audit of Pandey & Kumar (2025) reveals that while Listing 1 provides a generic helper function with `errorTarget=1.0`, Section 4.1 narrative for the 13,941-element Mode-I simulation **omits any numerical value for `errorTarget`**, omits the free meshing algorithm (`MEDIAL_AXIS` vs `ADVANCING_FRONT`), omits initial coarse mesh counts, and omits whether an `elementCountLimit` cap was enforced. Consequently, Gate 5 is formally classified as `LITERATURE_EFFECTIVE_ERROR_TARGET_NOT_ESTABLISHED`. The four missing parameters constitute the definitive external information boundary; unstated parameters (such as an assumed 2% target) cannot be scientifically asserted without author confirmation.
5. **Minimal Author Query Specification (Unsent)**:
   A concise 4-point technical inquiry addressing only these missing parameters has been drafted and preserved in `docs/supervisor_reports/GATE5_EXTERNAL_INFORMATION_BOUNDARY.md` for supervisor authorization.

---

## Chapter 6: Supervisor Figure References & Visual Deliverables

The accompanying publication-quality figures illustrate the verified mechanisms and are located in `ModeI_Supervisor_Report_Reproduction_Package/images/` and `docs/supervisor_reports/`:

- **Figure 1**: [`fig1_full_fu_requalification_comparison.png`](file:///D:/Master%20thesis/Adaptive%20remeshing/ModeI_Supervisor_Report_Reproduction_Package/images/fig1_full_fu_requalification_comparison.png)  
  *Complete Reaction Force vs. Displacement Comparison*: Shows the reference anchor (Job 1398090, 15k), defective predecessor (Job 1399632, 71k), Empirical 2% model (Job 1400395, 15.4k), and corrected nominal 1% model (Job 1404306, 71k). Demonstrates recovery of pre-peak response ($K_0$ error $-0.09\%$, peak force error $-1.64\%$), while explicitly annotating post-peak softening divergence and premature convergence termination at $u = 0.006774\,\text{mm}$.
- **Figure 2**: [`fig2_k0_elastic_stiffness_recovery.png`](file:///D:/Master%20thesis/Adaptive%20remeshing/ModeI_Supervisor_Report_Reproduction_Package/images/fig2_k0_elastic_stiffness_recovery.png)  
  *Initial Elastic Stiffness Regression ($0 < u \le 1.0\,\mu\text{m}$)*: Displays the unconstrained OLS fits over 400 points, highlighting the recovery from the defective low branch ($K_0 = 122.38\,\text{kN/mm}$) to the reference physical branch ($K_0 = 137.82\,\text{kN/mm}$, $-0.09\%$ error).
- **Figure 3**: [`fig3_bottom_edge_lift_kinematics.png`](file:///D:/Master%20thesis/Adaptive%20remeshing/ModeI_Supervisor_Report_Reproduction_Package/images/fig3_bottom_edge_lift_kinematics.png)  
  *Kinematic Bottom-Edge Lift Profile at Increment 1*: Plots the 150 bottom nodes along $y=0$, illustrating the 134 unconstrained lifting nodes ($u_2$ up to $+0.2304\,\text{nm}$, $46.07\%$ stroke) in the defective deck vs. $u_2 \equiv 0.000\,\text{nm}$ in the corrected deck.
- **Figure 4**: [`fig4_mesh_regional_discretization_breakdown.png`](file:///D:/Master%20thesis/Adaptive%20remeshing/ModeI_Supervisor_Report_Reproduction_Package/images/fig4_mesh_regional_discretization_breakdown.png)  
  *5-Region Discretization Breakdown (Gate 5)*: Bar chart of element counts across regions $R_1$ to $R_5$ for 1% (71,320), 2% (15,396), and 5% (4,194) meshes, showing that $99.39\%$ of surplus elements reside in non-critical far-field zones.
- **Figure 5**: [`fig5_computational_cost_and_convergence_summary.png`](file:///D:/Master%20thesis/Adaptive%20remeshing/ModeI_Supervisor_Report_Reproduction_Package/images/fig5_computational_cost_and_convergence_summary.png)  
  *Computational Performance Matrix*: 4-panel comparison of finite element count, serial walltime, cumulative iterations, converged increments (Panel (c): 3,783 converged increments), and cutbacks (Panel (d): 21 cutbacks in automatic incrementation) across all four benchmark jobs.

---

## Chapter 7: Epistemological Governance & Claims Discipline

### 7.1 I Know This (Analytical Definitions & Governing Physics)
1. **Governing BVP**: Pure Mode-I tensile extension on a $1\times 1\,\text{mm}$ square plate with an initial sharp slit seam $a_0 = 0.5\,\text{mm}$ along $y=0.5\,\text{mm}$, with constitutive parameters $E = 210\,\text{GPa}, \nu = 0.30, G_c = 2.7\,\text{kJ/m}^2, \ell_0 = 0.0075\,\text{mm}$.
2. **Canonical Initial Stiffness**: $K_0$ is a global structural stiffness $[\text{kN/mm}]$ defined as the unconstrained OLS slope over $0 < u \le 0.001000\,\text{mm}$ ($N=400$ increments), distinct from material modulus $E$.
3. **MISESERI Nature**: \texttt{MISESERI} is strictly a recovered von Mises stress discretization error indicator on the linear-elastic continuum pre-analysis, not a damage or phase-field error.
4. **Abaqus Card Grammar**: Free-format `*NSET` without `GENERATE` in Abaqus/Standard input preprocessor enforces a strict 16-entry limit per line; subsequent entries on the same line are silently ignored.

### 7.2 I Verified This Numerically (Empirical Solver & Forensic Evidence)
1. **Fixed Reference Benchmark (`1398090`)**: Reproduces literature reference values within $-0.029\%$ peak force ($0.757778\,\text{kN}$) and $-0.051\%$ peak displacement ($0.005857\,\text{mm}$), with $K_0 = 137.945520\,\text{kN/mm}$.
2. **NSET Truncation Root Cause**: ODB boundary set extraction (Job `1404312.mmaster02`) and parser limit verification (Job `1404318.mmaster02`) proved that 134 of 150 bottom nodes were omitted in defective decks, causing up to $+0.2304\,\text{nm}$ edge lift ($46.07\%$ stroke) and dropping stiffness to $122.38 - 122.60\,\text{kN/mm}$.
3. **Nominal 1% Requalification (`1404306`)**: Correcting `*NSET` line wrapping restored $K_0 = \mathbf{137.820804\,\text{kN/mm}}$ ($-0.09\%$ vs reference, $+12.62\%$ recovery), peak force $F_{\max} = \mathbf{0.745325\,\text{kN}}$ ($-1.64\%$), and pre-peak $L_2$ RMS error of $0.000625\,\text{kN}$.
4. **Software Release Invariance**: Clean twin remeshing (Job `1404373.mmaster02`) across Abaqus 2022 and 2023 yielded bit-for-bit identical meshes (71,320 at 1%, 17,687 at 2%), ruling out solver version as the cause of the 13,941 discrepancy.
5. **Spatial Surplus Concentration**: $99.39\%$ of surplus elements in the 71k mesh reside in far-field and non-critical corridor regions, while crack-tip element size differs by only $6.6\%$ ($1.84\,\mu\text{m}$ vs $1.96\,\mu\text{m}$).

### 7.3 I Do Not Yet Understand This (Open Scientific Questions)
1. **Literature 13,941 Mesh Parameter Provenance**: Why the literal published setting `errorTarget=1.0` produces $71,320$ elements in Abaqus CAE while the paper reported $\approx 13,941$ remains unresolved due to unstated parameters in Section 4.1 narrative (`GATE5_LITERATURE_EFFECTIVE_ERROR_TARGET_NOT_ESTABLISHED`).
2. **Post-Peak Robustness & Solver Formulations**: Whether deep post-peak softening convergence at $u > 0.006774\,\text{mm}$ on the 71,320-element mesh can be extended via line search tuning or viscous damping without corrupting energy dissipation requires further diagnostic investigation.
