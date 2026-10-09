# Mode-II Fixed-Mesh Reference Audit, Methodology Grounding, and Convergence Roadmap

**Date:** 2026-10-09  
**Task ID:** `F1376-MODE2-FIXED-MESH-REFERENCE-AUDIT-AND-CONVERGENCE-ROADMAP`  
**Author:** Gemini Antigravity  
**Status:** `MANDATORY_GATE_M2_1B_INSTITUTED`  
**Branch:** `mode2-pandey-kumar-reproduction`  

---

## 1. Executive Summary & Epistemological Pivot

This report establishes a foundational methodological correction for the Mode-II shear fracture investigation within the Master's thesis. 

### The Core Methodological Weakness Identified
In the Mode-I tensile benchmark, the thesis rigorously followed the canonical scientific sequence:
$$\text{[Define Problem]} \longrightarrow \text{[Establish Fixed-Mesh Converged Reference]} \longrightarrow \text{[Apply Adaptive Remeshing]} \longrightarrow \text{[Compare \& Explain Discrepancies]}$$
Specifically, in Mode-I, a verified, mesh-converged fixed-mesh reference solution was established (Job `1398090`, $15{,}192$ elements, with spatial convergence confirmed up to $57{,}929$ elements in Job `1410504`, establishing $K_0 = 137.95\,\text{kN/mm}$, $F_{\max} = 0.758\,\text{kN}$, $u_{\text{peak}} = 5.86\,\mu\text{m}$, and $W_{\mathrm{ext}}$). Every adaptive remeshing result was subsequently judged against this known, quantitative numerical anchor.

In Mode-II, however, this validation sequence was inadvertently truncated:
1. A single coarse pre-analysis simulation ($2{,}960$ finite elements) was executed.
2. Because the coarse pre-analysis completed successfully (Exit 0, full damage $d_{\max} = 1.0$), it was treated as a sufficient foundation to immediately launch native adaptive remeshing sweeps (`ET_5PCT` to `ET_1PCT`, $21{,}063$ to $37{,}575$ elements).
3. **No mesh-converged fixed-mesh reference solution was ever established for the active, paper-grounded boundary value problem.**

### The Consequence: Conflation of Fracture Solver and Adaptive Controller
When our completed ET3 adapted simulation ($21{,}063$ elements) predicted a peak force of $F_{\max} = 412.21\,\text{N}$, whereas the published curve of Pandey & Kumar (2025) reports $F_{\max} \approx 365.74\,\text{N}$, the absence of a fixed-mesh reference created an insurmountable epistemological ambiguity:
- **Possibility A (Solver-Level Concurrence):** The implemented phase-field formulation (Miehe spectral split with $l_0 = 15\,\mu\text{m}$, $G_c = 2.7\,\text{N/mm}$, $E = 210\,\text{GPa}$, $\nu = 0.3$) under true constrained shear ($u_y = 0$ on top and bottom) actually converges on a sufficiently fine fixed mesh to $F_{\max} \approx 410\text{--}415\,\text{N}$. In this scenario, the adaptive remeshing controller is **fully accurate and successful** in reproducing the true continuum solution of our numerical model, and the $12.7\%$ discrepancy with Pandey & Kumar stems from undocumented formulation details, boundary enforcement subtleties, or published reporting discrepancies.
- **Possibility B (Adaptive Remeshing Discretization Failure):** The implemented formulation under constrained shear converges on a fine fixed mesh to $F_{\max} \approx 360\text{--}370\,\text{N}$ (matching the paper). In this scenario, the adaptive remeshing controller is **failing** to capture the proper localized softening mechanics, potentially due to corridor width, transition gradation, or lack of phase-field gradient awareness in the error indicator.

Without an independent, mesh-converged fixed-mesh reference, **it is impossible to distinguish an adaptive-meshing failure from a fracture-model property**.

---

## 2. Comprehensive Forensic Audit of Historical Mode-II Simulations

To determine whether any previously executed simulations in the repository already constitute a valid fixed-mesh reference, a comprehensive audit was performed across all historical branches and stages.

### 2.1 Stage F Legacy Fixed-Mesh Runs (H0, H1, H2)
During Stage F (July–August 2026), several fixed-mesh Mode-II simulations were conducted:
- `H0_BASELINE` (Job `1378942.mmaster02`): $3{,}930$ elements.
- `H1_UNIFORM_FINE` (Job `1389686.mmaster02`): $12{,}064$ elements ($h_{\min} = 2.0\,\mu\text{m}$).
- `H2_UNIFORM_ULTRAFINE` (Job `1389687.mmaster02`): $33{,}852$ elements ($h_{\min} = 1.0\,\mu\text{m}$).

**Audit Findings & Disqualification:**
1. **Top Boundary Condition Discrepancy (`FREEU2`):**
   In all Stage F H0/H1/H2 models, the job configuration explicitly set `FREEU2` (the vertical displacement $u_y$ on the top edge was left completely unconstrained). As established in `MODE2_ROOT_CAUSE_INVESTIGATION_REPORT.md`:
   - Under `FREEU2`, the specimen is free to contract and tilt vertically under shear, resulting in an initial structural stiffness of $K_0 \approx 12.8\,\text{kN/mm}$ and peak force $F_{\max} \approx 141\text{--}144\,\text{N}$.
   - In the authoritative literature benchmark (Pandey & Kumar 2025, Fig. 13(a); Navidtehrani et al. 2021), the top boundary is strictly constrained in the vertical direction ($u_y = 0$, pure constrained shear), which produces $K_0 \approx 45.68\,\text{kN/mm}$ and $F_{\max} \approx 365.74\,\text{N}$.
2. **Notch Topology Defect in Legacy H0:**
   As documented in `MODE_II_H0_H1_PARITY_AND_STIFFNESS_AUDIT.md`, the legacy H0 deck contained zero duplicated node pairs along the notch line, acting as an unnotched continuum.
3. **Verdict:**
   The Stage F H0, H1, and H2 simulations solved a fundamentally different boundary value problem (`FREEU2`). **They cannot serve as a reference solution for the paper-grounded Mode-II benchmark.**

### 2.2 Paper-Grounded BVP Simulations (October 2026)
In October 2026 (Tasks F1360–F1375), the true paper-grounded boundary value problem was established in `models/pandey_kumar_mode2/06_paper_grounded_uel_preanalysis/`:
- Domain: $1.0\,\text{mm} \times 1.0\,\text{mm}$ with sharp slit at $y = 0.5\,\text{mm}, x \in [0.0, 0.5]\,\text{mm}$.
- Bottom: $u_x = 0, u_y = 0$ along $y = 0$.
- Top: $u_x = \text{prescribed shear}$, $u_y = 0$ along $y = 1.0\,\text{mm}$.
- Material: $E = 210\,\text{GPa}$, $\nu = 0.3$, $G_c = 2.7\,\text{N/mm}$, $l_0 = 15\,\mu\text{m}$.
- Formulation: Staggered UEL with Miehe spectral strain-energy decomposition.

**Audit Findings:**
- **Coarse Retest (Job `1411104.mmaster02`):** Only $2{,}960$ elements ($h \approx 20\text{--}25\,\mu\text{m} > l_0 = 15\,\mu\text{m}$). Solved full horizon ($F_{\max} = 514.51\,\text{N}$, $u = 13.43\,\mu\text{m}$, $h_{\mathrm{lig}} = 144.92\,\mu\text{m}$).
- **Adapted ET3 (Job `1411267.mmaster02`):** $21{,}063$ elements (Exit 0, $F_{\max} = 412.21\,\text{N}$, $u = 9.41\,\mu\text{m}$, $h_{\mathrm{lig}} = 56.32\,\mu\text{m}$).
- **Adapted ET2 (Job `1411414.mmaster02`):** $37{,}575$ elements (currently solving Step 1 Inc 947+).

**Conclusive Audit Result:**
**Zero fine or converged fixed-mesh simulations have ever been executed for the paper-grounded Mode-II boundary value problem.**

---

## 3. Epistemological Clarification: Abaqus Native Sizing Mechanics

In Task F1375, the multi-increment error evaluation of `outputFrequency=ALL_INCREMENTS` was described as a "mathematically proven cumulative sizing envelope." In accordance with strict scientific epistemology, this statement must be clarified and properly scoped:

1. **Observed Operational Behavior vs. Mathematical Proof:**
   - It is an **empirically observed and documented operational mechanism** of the Abaqus CAE `RemeshingRule` algorithm that when `outputFrequency=ALL_INCREMENTS` is selected, Abaqus evaluates the error indicator field $\eta_k(\mathbf{x})$ across all stored increments $k = 1, \dots, N_{\mathrm{inc}}$ in the specified step, and computes a target element size distribution $h(\mathbf{x})$ that accounts for the maximum error experienced at each material point.
   - However, the proprietary Abaqus kernel combines multiple internal heuristics—including spatial error smoothing, background mesh interpolation, element aspect ratio control, and user-specified gradation parameters (`gradation=0.2`).
   - Therefore, describing this as an "independent mathematical proof" overstates an empirical observation of closed-source commercial software.
2. **Correct Formulation:**
   "The continuous diagonal refinement corridor is an **empirically verified emergent feature** of the Abaqus CAE multi-increment error sizing envelope across a propagating stress concentration, rather than a mathematically proven closed-form theorem."

---

## 4. The 3-Layer Thesis Architecture for General Adaptive Fracture

The user's insight directly clarifies the overarching objective of this Master's thesis:
> *"We are not simply trying to reproduce Pandey and Kumar. We are trying to develop an adaptive-remeshing framework that works reliably across different fracture problems without knowing the crack path beforehand."*

To achieve this objective, the thesis architecture is formally divided into three independently verifiable layers:

```
+-----------------------------------------------------------------------------------+
|               LAYER 3: SEQUENTIAL ADAPTIVE FRACTURE FRAMEWORK                     |
|  - Evolving / multi-step external driver (Solve -> Evaluate -> Remesh -> Transfer)|
|  - State transfer of displacement (u) and phase field (d)                         |
|  - Energetic consistency & irreversibility enforcement across remeshing cycles    |
|  - Autonomous crack tracking without a priori crack path knowledge                |
+-----------------------------------------------------------------------------------+
                                         ^
                                         |
+-----------------------------------------------------------------------------------+
|               LAYER 2: GENERAL ADAPTIVE REFINEMENT CONTROLLER                     |
|  - Error estimation & discretization quality evaluation                           |
|  - Multi-physics refinement indicator: eta_K = F(eta_stress, eta_damage, h/l0)   |
|  - Automated geometry-preserving remeshing & gradation control                    |
|  - Refinement corridor confinement and mesh-transition verification               |
+-----------------------------------------------------------------------------------+
                                         ^
                                         |
+-----------------------------------------------------------------------------------+
|               LAYER 1: VERIFIED FRACTURE SOLVER & CONVERGED BENCHMARK             |
|  - UEL constitutive formulation (Miehe spectral decomposition, irreversibility)   |
|  - Global equilibrium & reaction force verification (sum F = 0, MPC condensation) |
|  - Thermodynamically consistent energy balance (W_ext = E_elas + E_frac)         |
|  - Fixed-mesh spatial convergence (h -> 0) & temporal convergence (dt -> 0)      |
|  - Unambiguous numerical reference anchor established BEFORE adaptivity           |
+-----------------------------------------------------------------------------------+
```

### The Inherent Limitation of Pure Stress-Error Indicators (MISESERI)
MISESERI is a linear-elastic stress-recovery error indicator ($\eta_{\mathrm{stress}} \approx \|\boldsymbol{\sigma}^* - \boldsymbol{\sigma}_h\|_{L_2} / \|\boldsymbol{\sigma}\|_{L_2}$). 
In a phase-field fracture problem:
- In the initial elastic regime, stress concentration at the crack tip drives refinement.
- However, inside the fracture process zone, as material degrades ($d \to 1$), the stresses soften and drop toward zero ($\boldsymbol{\sigma} \to (1-d)^2 \boldsymbol{\sigma}_0$).
- A pure stress-error indicator will paradoxically perceive degraded, fully broken regions as having **low stress error**, potentially causing the mesh generator to de-refine or fail to refine the wake!
- True phase-field resolution requires resolving the phase-field gradient $|\nabla d| \sim 1/l_0$, requiring element sizes $h \le l_0 / 2$ (ideally $h \le l_0 / 5$).
- A truly general adaptive controller (Layer 2) should therefore evaluate a combined multi-field indicator:
$$\eta_K = \mathcal{F}\left(\eta_{\mathrm{stress}, K},\; \eta_{\mathrm{damage}, K},\; \frac{h_K}{l_0},\; \eta_{\mathrm{energy}, K}\right)$$

---

## 5. Mandatory New Gate: Gate M2-1B (Fixed-Mesh Fracture Reference Qualified)

To ensure that the thesis methodology remains rigorous and immune to false conclusions, we formally institute:

### Gate M2-1B: Fixed-Mesh Fracture Reference Qualified
**Pre-Condition for Accepting Adaptive Remeshing Accuracy:**
Before any adaptive remeshing results (ET3, ET2, etc.) can be evaluated for physical fidelity or accepted as proof of accuracy, the underlying fracture formulation must demonstrate a verified, mesh-converged solution on a sequence of uniform or fixed refined meshes for the exact boundary value problem.

**Pre-Declared Acceptance Criteria for Gate M2-1B:**
1. **Spatial Convergence Series:** Minimum 3 fixed mesh resolutions:
   - Coarse Baseline: $h \approx 20\,\mu\mathrm{m} > l_0$ ($2{,}960$ elements, Job `1411104`).
   - Medium Refined: $h \approx 7.5\,\mu\mathrm{m} = 0.5\,l_0$ ($\approx 20{,}000\text{--}25{,}000$ elements).
   - Fine Reference: $h \approx 3.75\,\mu\mathrm{m} = 0.25\,l_0$ ($\approx 60{,}000\text{--}80{,}000$ elements, or locally graded fixed mesh).
2. **Convergence Metrics:**
   - Asymptotic stabilization of peak force $F_{\max}(h)$ and peak displacement $u(F_{\max})$.
   - Convergence of initial structural stiffness $K_0$ to $45.68 \pm 0.5\,\mathrm{kN/mm}$.
   - Asymptotic convergence of the crack trajectory $\theta(h)$ and terminal ligament $h_{\mathrm{lig}}(h)$.
   - Convergence of total external work $W_{\mathrm{ext}} = \int F \, du$ over the common comparison domain $[0, 16.0]\,\mu\mathrm{m}$.
3. **Outcome Resolution:**
   - Establish whether the converged fixed-mesh peak force is $F_{\max} \approx 410\,\text{N}$ (Possibility A) or $F_{\max} \approx 365\,\text{N}$ (Possibility B).

---

## 6. Immediate Action Plan

1. **Keep Live Production Solve Running:**
   - Job `1411414.mmaster02` (`M2_J2_ADAPT_ET2_STAB`, $37{,}575$ FEs) remains active on `mnode097/0`. It provides vital evidence regarding adaptive-mesh convergence (ET3 vs ET2) and will complete without disruption.
2. **Design Fixed-Mesh Convergence Suite:**
   - Construct the input deck generator for the fixed-mesh convergence study (preserving exact UEL `f42_mixed_uel_mode2_miehe.for` and exact boundary conditions).
   - Prepare a batch submission proposal for the supervisor-governed HPC queue.
3. **Compare Adaptive Results to the True Fixed Reference:**
   - Once the fixed-mesh reference is established, benchmark ET3 ($21{,}063$ elements) and ET2 ($37{,}575$ elements) against the numerical fixed-mesh reference to quantify the genuine efficiency, accuracy, and limitations of native MISESERI remeshing.
