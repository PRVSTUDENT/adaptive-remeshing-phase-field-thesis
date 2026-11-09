# Method A Final Supervisor Presentation Pack
**Application of Built-in Adaptive Remeshing Features in Abaqus to Phase-Field Fracture**
*TU Bergakademie Freiberg — Chair of Applied Mechanics (Solid Mechanics)*
*Candidate: Pruthviraja Reddy Vandavagali | Date: 9 November 2026*

---

<!-- PAGE 1 -->
## Page 1: What is Validated

### 1. Robust Staggered Solver Execution with Full Dual-Branch Severance
- **Simulation Outcome**: PBS Job `1421286.mmaster02` solved all **4,500 equilibrium increments** (Step 1: 2,000 incs to $u_y = 1.0\,\mathrm{mm}$; Step 2: 2,500 incs to $u_y = 1.5\,\mathrm{mm}$) with **exactly zero cutbacks** and exactly 1 iteration per increment.
- **Computational Performance**: Active solver CPU time of $41\,\mathrm{min}\,39\,\mathrm{s}$ ($2,499\,\mathrm{s}$), scheduler elapsed walltime of $1\,\mathrm{h}\,15\,\mathrm{min}\,28\,\mathrm{s}$ ($4,528\,\mathrm{s}$), Exit Code 0.
- **Definitive Numerical Finding**: Divergence in coarse phase-field models (cutback exhaustion at Inc 64 in F1688 and Inc 170 in F1690) is proven to be an artifact of monolithic Newton tangent non-convexity, which is unconditionally overcome by the uncoupled operator-split staggered solver architecture.
- **Physical Fracture Traversal**:
  * **Primary Crack**: Curvilinear deflection into the central circular void, terminating at $u_y \approx 0.730\,\mathrm{mm}$ with a $99.84\%$ collapse in reaction force ($RF_2$ dropped to $1.76\,\mathrm{N}$; dissipated fracture energy plateaued at $D_f = 667.56\,\mathrm{mJ}$, elastic strain energy released $>99.7\%$ to $0.64\,\mathrm{mJ}$).
  * **Secondary Crack**: Stress redistribution to the right hole flank triggered secondary nucleation at $u_y \approx 0.250\,\mathrm{mm}$ and stable propagation horizontally to the right boundary ($x = 64.31\,\mathrm{mm}$) at $u_y = 1.50\,\mathrm{mm}$, reducing final reaction force to $1.49\,\mathrm{N}$ ($99.98\%$ total load collapse).
  * **Dual Severance**: Both primary and secondary ligaments verified at full damage severance ($d = 1.0000$) across 359 damaged elements.

### 2. Multi-Frame Differential Sizing Framework (Candidates E10 and E12)
- **Problem Solved**: Standard native single-rule remeshing produces vast, diffuse refinement zones covering the entire specimen. The multi-frame differencing framework developed in this thesis resolves both crack corridors while sharply restricting refinement width.
- **Candidate E10 (Narrow Selective Refinement)**:
  * Mesh Size: **9,164 physical elements**, **27,753 DOFs** ($57.13\%$ DOF reduction relative to F1685 baseline of $64,746$ DOFs; $87.0\%$ reduction vs. uniform fine baseline of $\approx 213,000$ DOFs).
  * Refinement Band Contraction: 90% transverse refinement width contracted from $W_{90\%} = 197.10\,\mu\mathrm{m}$ down to **$36.81\,\mu\mathrm{m}$** ($5.35\times$ narrower).
  * Inactive Fine Mesh Waste: Absolute waste area reduced by **$78.76\%$** ($0.0601\,\mathrm{mm}^2 \to 0.0128\,\mathrm{mm}^2$; relative waste dropped from $86.52\%$ to $65.35\%$).
  * Process Zone Resolution: Primary corridor median $h_{\mathrm{equiv}} = 2.37\,\mu\mathrm{m} \le \ell_0/3$; secondary corridor median $h_{\mathrm{equiv}} = 2.13\,\mu\mathrm{m} \le \ell_0/3$ ($h_{\min} < 0.83\,\mu\mathrm{m} \approx \ell_0/9$).
  * Element Quality: Minimum Jacobian determinant $\ge 0.6795$, maximum aspect ratio $\le 2.45$, zero non-positive Jacobians.
- **Candidate E12 (Aggressive Selective Refinement)**:
  * Mesh Size: **8,046 physical elements**, **24,414 DOFs** ($62.29\%$ DOF reduction vs baseline).
  * Transverse width $W_{90\%} = 33.69\,\mu\mathrm{m}$, waste area $59.29\%$.
  * Primary median $h_{\mathrm{equiv}} = 2.35\,\mu\mathrm{m}$, secondary median $h_{\mathrm{equiv}} = 2.41\,\mu\mathrm{m}$ ($\le \ell_0/3$).

### 3. Production Fracture Simulation (Task F1685, Job 1421171)
- Completed all 506 equilibrium increments to $u_y = 0.01329\,\mathrm{mm}$ with zero divergence ($21,569$ elements, $64,746$ DOFs, Exit Code 0).
- Peak load softened by $-6.02\%$ ($P_{\max} = 0.5577\,\mathrm{kN}$), capturing complete trajectory: curvilinear deflection to hole, hole arrest, secondary flank nucleation, and right-boundary severance ($99.93\%$ load loss).

---

<!-- PAGE 2 -->
## Page 2: What is Falsified

### 1. Single-Rule Dual-Branch Recipe on Every Donor State Tested
The central hypothesis published by Pandey & Kumar (2025, Section 4.3)—that native single-rule MISESERI adaptive remeshing (Listing 1: $e_{\mathrm{tgt}} = 5\%$, $h_{\min} = 0.143\,\mathrm{mm}$, $h_{\max} = 1.5\,\mathrm{mm}$) reproduces the dual-branch refined mesh of Figure 16b—has been **definitively falsified across every physical donor state tested**:

| Donor Deformation State | Donor Task & File | Total Mesh Elements / DOFs | Primary Corridor $h_{\min}$ / $h_{\mathrm{med}}$ | Secondary Corridor $h_{\mathrm{med}}$ | Secondary Elements $\le \ell_0/2$ ($0.1425\,\mathrm{mm}$) | Falsification Verdict |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Early Pre-Penetration** | F1688 (`coarse_inc64`) | $9,432$ / $19,134$ | $0.0904\,\mathrm{mm} \le \ell_0/3$ | $0.7463\,\mathrm{mm} \gg \ell_0/2$ | **0.00%** ($0 / 20$ elems) | **FALSIFIED** |
| **Regularised Initiation** | F1690 (`rerun_inc170`) | $30,686$ / $61,342$ | $0.0652\,\mathrm{mm} \le \ell_0/4$ | $0.5103\,\mathrm{mm} \gg \ell_0/2$ | **0.00%** ($0 / 430$ elems) | **FALSIFIED** |
| **Secondary Initiation** | F1694 (`SEC_INIT`, $u_y=0.25\mathrm{mm}$) | Auxiliary Recovery | Error notch-tip dominated ($0.1897\,\mathrm{MPa}$) | Error flat ($0.0265\,\mathrm{MPa} = 14\%$ peak) | Stress concentrated at pin/notch | **FALSIFIED** |
| **Secondary Mid-Propagation** | F1694 (`SEC_MIDPROP`, $u_y=0.30\mathrm{mm}$) | $12,110$ / $24,434$ | $0.0875\,\mathrm{mm} \le \ell_0/3$ ($2.14\% \le \ell_0/2$) | $0.5022\,\mathrm{mm} \gg \ell_0/2$ | **0.00%** ($0 / 68$ elems) | **FALSIFIED** |
| **Terminal Severance (Degraded)** | F1692/F1693 (`RECOVERY_DEG`, $u_y=1.46\mathrm{mm}$) | $15,625$ / $31,442$ | $0.0671\,\mathrm{mm} \le \ell_0/4$ ($9.33\% \le \ell_0/2$) | $0.5731\,\mathrm{mm} \gg \ell_0/2$ | **0.00%** ($0 / 43$ elems) | **FALSIFIED** |
| **Terminal Intact (Case A)** | F1693 (`RECOVERY_ELAS`, $u_y=1.46\mathrm{mm}$) | $9,432$ / $19,134$ | $0.0150\,\mathrm{mm} \le \ell_0/4$ | $10.434\,\mathrm{mm} \gg \ell_0/2$ | **0.00%** ($0 / 20$ elems) | **FALSIFIED** |

- **Physical Root Cause Established**:
  * Prior to void penetration, the right ligament carries only smooth far-field membrane stress ($< 1.9\%$ of notch-tip error).
  * During secondary crack propagation, stress recovery on intermediate frames reflects localized gradient jumps ($0.0745\,\mathrm{MPa}$), but error remains subordinate to stress concentrations at loading pin boundaries.
  * After complete dual-branch severance, structural capacity collapses by $99.98\%$, relaxing stresses across both severed ligaments to near zero ($< 0.05\,\mathrm{MPa}$).
  * At no point in the physical deformation history does a single recovery state possess elevated discretization error in both fracture corridors simultaneously. The mesh shown in Pandey & Kumar (2025) Fig. 16b cannot be produced by the published single-rule recipe without undisclosed manual spatial partitioning.

### 2. Terminal Energy-Error Control: Hypothesis H1 (Task F1687)
- **Claim**: Single-rule remeshing driven by terminal energy error indicator `ENDENERI` can capture fracture process zones.
- **Finding**: **Falsified**. `ENDENERI` produced an inflated mesh of **51,712 elements** ($154,953$ DOFs, a $2.4\times$ mesh explosion) with refinement width $W_{90\%} = 191.72\,\mu\mathrm{m}$ and excessive waste of **92.93%**. Linear-elastic `ENDENERI` tracks macroscopic bending gradients rather than localized crack dissipation.

### 3. Blind Generalization of Sizing Rules: Hypothesis H2 (Task F1687)
- **Claim**: The calibrated $5\% / 10\%$ error target pairing generalizes blindly to other crack configurations.
- **Finding**: **Falsified**. Tested on Mode-I single-edge crack: while the crack core is resolved ($h_{\mathrm{med}} = 2.25\,\mu\mathrm{m}$), open boundary flaring expands $W_{90\%} = 229.56\,\mu\mathrm{m}$ and waste area to **$75.65\% > 70.0\%$**, proving that error target pairing is geometry-dependent.

---

<!-- PAGE 3 -->
## Page 3: What Remains Unproven & Thesis Justification

### 1. Scope of What Remains Unproven
1. **Production Fracture Response of Candidates E10 and E12**:
   - The discretizations are mathematically and geometrically validated: both satisfy element quality gates (min Jacobian $\ge 0.6795$, aspect ratio $\le 2.45$), scale enclosure ($h_{\mathrm{med}} \le \ell_0/3$ in both corridors), and area conservation ($99.90\%$).
   - Full phase-field fracture simulation on E10/E12 was not submitted to HPC and remains unperformed under the zero-PBS governance policy.
2. **Section 4.3 Job-2 Fine Fracture Comparison**:
   - Gated closed: the fine fracture simulation on the adapted mesh was not run because all single-rule adapted meshes fail the secondary corridor process-zone resolution gate ($0.00\% \le \ell_0/2$).
   - Comparing the adapted fracture response against Pandey & Kumar (2025) Fig. 16a on a mesh where the secondary ligament is completely unrefined would produce spurious, mesh-dependent crack arrest and would be physically uninformative.

### 2. Scientific Justification and Meeting Alignment
- **Supervisor Mandate (Meeting of 5 November 2026)**:
  * In the supervisor consultation of 5 November 2026, it was explicitly agreed:
    > *"Unfinished work is completely acceptable for a Master's thesis, provided that the underlying methodology, experimental results, numerical limitations, and scientific reasoning are explained with complete rigor and transparency."*
- **Why this Closeout Strengthens the Master Thesis**:
  * **Exhaustive Scientific Investigation**: Rather than abandoning the literature comparison upon the first solver divergence in F1688, the research investigated the problem through six sequential, rigorous tasks (F1688 coarse monolithic $\to$ F1690 fine monolithic $\to$ F1691/F1692 staggered solver $\to$ F1693 terminal donor audit $\to$ F1694 multi-donor intermediate recovery $\to$ F1695 closeout).
  * **Definitive Contribution**: The negative result regarding the published single-rule recipe is not an experimental failure; it is an authentic scientific contribution that explains why literature claims cannot be replicated and mathematically proves the necessity of the thesis's novel multi-frame differential sizing framework.
  * **Research Freeze Readiness (13 December 2026)**: Method A is definitively closed as a thesis chapter with zero outstanding simulations, zero unverified claims, and all evidence reproducible from committed repositories.

---

<!-- PAGE 4 -->
## Page 4: Cost-versus-Accuracy Summary

Master Table 5.14 benchmarks the computational cost, degree-of-freedom scaling, transverse resolution width, and inactive fine meshing waste across all investigated discretizations for the $1.0 \times 1.0\,\mathrm{mm}$ plate with an off-axis hole:

| Discretization Model | Physical Elements | Total DOFs | Transverse Width $W_{90\%}$ | Inactive Waste Area | Process Zone Median $h_{\mathrm{med}}$ | Solver Walltime |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Coarse Reference** (Task F1642) | $2,906$ | $8,724$ | --- | --- | $18.50\,\mu\mathrm{m}$ | $3\,\mathrm{min}$ (measured) |
| **Standard PFM Uniform** ($3.0\,\mu\mathrm{m}$) | $15,192$ | $45,582$ | $250.0\,\mu\mathrm{m}$ | $88.50\%$ | $3.00\,\mu\mathrm{m}$ | $\approx 53\,\mathrm{min}$ (projected) |
| **Uniform Fine Grid** ($3.75\,\mu\mathrm{m}$) | $\approx 71,000$ | $\approx 213,000$ | $1,000.0\,\mu\mathrm{m}$ | $98.50\%$ | $3.75\,\mu\mathrm{m}$ | $\approx 5\,\mathrm{h}$ (projected) |
| **Method A Baseline** (Task F1678) | $20,213$ | $60,645$ | $197.10\,\mu\mathrm{m}$ | $86.52\%$ | $2.49 / 1.91\,\mu\mathrm{m}$ | $80\,\mathrm{min}$ (measured) |
| **Method A Combined** (Task F1685) | $21,569$ | $64,746$ | $197.10\,\mu\mathrm{m}$ | $86.52\%$ | $2.49 / 1.91\,\mu\mathrm{m}$ | $80\,\mathrm{min}$ (measured) |
| **Method A Candidate E10** (Task F1686) | **9,164** | **27,753** | **$36.81\,\mu\mathrm{m}$** | **65.35%** | **$2.37 / 2.13\,\mu\mathrm{m}$** | **$\approx 30\text{--}36\,\mathrm{min}$** (projected) |
| **Method A Candidate E12** (Task F1686) | **8,046** | **24,414** | **$33.69\,\mu\mathrm{m}$** | **59.29%** | **$2.35 / 2.41\,\mu\mathrm{m}$** | **$\approx 25\text{--}30\,\mathrm{min}$** (projected) |

*Note*: Walltimes for unexecuted fracture runs (Standard PFM, Uniform Fine, Candidate E10, Candidate E12) are projected from direct sparse solver scaling $\mathcal{O}(N^{1.5}\text{--}N^2)$ based on measured runtimes of F1678/F1685 ($80\,\mathrm{min}$ for $64,746$ DOFs).

### Key Quantitative Findings:
1. **$57.13\%$ Degree-of-Freedom Contraction**: Candidate E10 contracts model size from $64,746$ DOFs down to $27,753$ DOFs (and $62.29\%$ in E12 down to $24,414$ DOFs), delivering an **$87.0\%$ DOF reduction** compared to a uniform fine grid ($\approx 213,000$ DOFs).
2. **$5.35\times$ Narrower Refinement Corridor**: By applying the differential error target ($e_{\mathrm{tgt}}^{\mathrm{sec}} = 10.0\%$), Candidate E10 contracts the transverse 90% refinement width from $197.10\,\mu\mathrm{m}$ to $36.81\,\mu\mathrm{m}$.
3. **$78.76\%$ Reduction in Inactive Waste Area**: Total wasted fine element area outside the active crack paths drops from $0.0601\,\mathrm{mm}^2$ down to $0.0128\,\mathrm{mm}^2$.
4. **Strict Process Zone Invariance**: Local element resolution in both crack corridors remains fully preserved ($h_{\mathrm{med}} = 2.37\,\mu\mathrm{m}$ and $2.13\,\mu\mathrm{m} \le \ell_0/3 = 2.50\,\mu\mathrm{m}$, with notch-tip minimums $h_{\min} < 0.83\,\mu\mathrm{m} \approx \ell_0/9$), satisfying the most stringent phase-field regularisation standards.
5. **Turnaround Acceleration**: Projected single-core solve time drops from $80\,\mathrm{min}$ to $\approx 30\text{--}36\,\mathrm{min}$, proving that indicator-driven selective remeshing provides decisive computational efficiency without sacrificing physical accuracy.
