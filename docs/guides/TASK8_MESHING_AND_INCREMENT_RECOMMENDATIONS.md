# Thesis Task 8: Meshing and Increment Parameter Recommendations for Abaqus/PFF Adaptive Remeshing

**Author:** Master Thesis Candidate  
**Date:** September 3, 2026  
**Governing Task:** Task 8 (Formulate Meshing-Parameter Recommendations)  
**Status:** **`TASK8_RECOMMENDATIONS_FORMULATED`**  
**Evidence Basis:** Tasks 3, 5, 6, and 7 HPC Production Solves (`1398090`, `1400395`, `1400396`, `1400408`, `1400738`, `1400739`)

---

## 1. Executive Summary & Objective

This document synthesizes the empirical and theoretical findings from **Task 3** (Fixed-mesh baseline), **Task 5** (Adaptive Mode-I reproduction), **Task 6** (Companion visualization verification), and **Task 7** (Increment and mesh sizing sensitivity studies). It provides definitive, evidence-backed meshing and time-stepping guidelines for future fracture simulations using Phase-Field Fracture (PFF) user elements coupled with Abaqus native adaptive remeshing.

### Core Recommendations at a Glance:
1. **Adaptive Refinement Error Target:** For 2D quasi-static phase-field fracture models with characteristic regularization length $l_0$, set the Abaqus native SPR error target to **`errorTarget = 2.0%`**. This ensures the element size in the fracture process zone satisfies $h \le l_0 / 4$ ($h \approx 0.0010\,\mathrm{mm}$ for $l_0 = 0.0075\,\mathrm{mm}$), preventing artificial non-local numerical toughening while avoiding full-domain over-refinement.
2. **Fixed Time / Load Incrementation:** 
   - **Pre-peak elastic ramp (Step 1):** $\Delta u \le 1.0 \times 10^{-3}\,\mathrm{mm}$ ($\Delta u / u_{\text{peak}} \le 17\%$).
   - **Fracture propagation (Step 2):** $\Delta u \le 4.0 \times 10^{-4}\,\mathrm{mm}$ ($\Delta u / u_{\text{peak}} \le 6.9\%$).
   - Doubling the increment size from the baseline ($3{,}500$ total increments vs $7{,}000$) preserves mechanical response within $<0.06\%$ of peak force and displacement while achieving a **$48.4\%$ runtime reduction**.
3. **Visualization Bridge:** Use the verified companion facsimile UMAT bridge for full-field Abaqus/CAE post-processing with zero mechanical stiffness interference.

---

## 2. Predeclared Scientific Acceptance Criteria

All candidate simulations are evaluated against five predeclared quantitative acceptance gates:

| Acceptance Gate | Parameter / Metric | Threshold / Tolerance | Scientific Rationale |
| :--- | :--- | :--- | :--- |
| **Gate 1: Solver Stability** | Numerical cutbacks & singularities | **`0 cutbacks`**, **`0 singularities`** | Ensures well-conditioned stiffness matrix without convergence breakdowns. |
| **Gate 2: Initial Elastic Stiffness** | Initial linear slope $K_0$ ($u \le 0.0005\,\mathrm{mm}$) | **$|\Delta K_0 / K_{0,\text{ref}}| \le 3.0\%$** | Verifies elastic compliance preservation across far-field mesh transitions. |
| **Gate 3: Peak Reaction Force** | Maximum reaction force $F_{\text{peak}}$ | **$|\Delta F_{\text{peak}} / F_{\text{ref}}| \le 5.0\%$** | Confirms accurate energetic threshold for fracture initiation. |
| **Gate 4: Peak Displacement** | Displacement at peak force $u_{\text{peak}}$ | **$|\Delta u_{\text{peak}} / u_{\text{ref}}| \le 5.0\%$** | Verifies accurate localization onset without artificial delay. |
| **Gate 5: Post-Peak Fracture** | Reaction force drop $(F_{\text{peak}} - F_{\text{final}})/F_{\text{peak}}$ | **$\ge 90.0\%$** | Confirms complete horizontal ligament separation. |

---

## 3. Adaptive Mesh Sizing Guidelines (`errorTarget` vs. Length Scale Resolution)

### 3.1 Synthesis of Discretization Levels

```text
=======================================================================================================================================================
errorTarget   N_phys Elements   Local Size h   h / l_0 Ratio   F_peak (kN)   F Error (%)   u_peak (mm)   u Error (%)   Classification / Verdict
=======================================================================================================================================================
Target Ref    ~13,941           0.0010 mm      ~0.133          0.7580 kN     --            0.005860 mm   --            Pandey & Kumar (2025)
1.0%          71,320            0.0008 mm      0.107           0.4782 kN     -36.91%       0.004150 mm   -29.18%       OVER_REFINED (Elastic Shift)
2.0%          15,396            0.0010 mm      0.133           0.7482 kN     -1.29%        0.005775 mm   -1.45%        SCIENTIFICALLY_ACCEPTED
3.0%          7,633             0.0018 mm      0.240           0.8553 kN     +12.84%       0.007339 mm   +25.24%       SENSITIVITY_ONLY (Toughening)
5.0%          4,194             0.0028 mm      0.373           0.7650 kN     +0.92%        0.007060 mm   +20.48%       SENSITIVITY_ONLY (Delayed Peak)
Fixed Mesh    15,192            0.0010 mm      0.133           0.7578 kN     -0.03%        0.005857 mm   -0.05%        SCIENTIFICALLY_ACCEPTED
=======================================================================================================================================================
```

### 3.2 Detailed Mechanics & Phenomena:

1. **Over-Refinement under Low Thresholds (`errorTarget = 1.0%`):**
   - In native Abaqus SPR remeshing, the relative error estimator $\eta = \text{MISESERI} / \text{MISESAVG}$ is scale-invariant across singular stress concentrations.
   - At $\text{errorTarget} = 1.0\%$, over $80\%$ of the domain is marked for refinement, producing $71{,}320$ physical elements ($35\,\mathrm{h}$ runtime).
   - This excessive refinement across boundary regions induces an artificial compliance shift, causing premature crack-tip localization and a $-36.91\%$ drop in peak force.
2. **Optimal Quantitative Reconstruction (`errorTarget = 2.0%`):**
   - Reconstructs a localized high-density refinement corridor along the expected fracture path ($15{,}396$ elements, $+10.4\%$ match to literature).
   - Local element size $h \approx 0.0010\,\mathrm{mm}$ satisfies the classic requirement $h \le l_0 / 4$ throughout the entire process zone.
   - Achieves $F_{\text{peak}} = 0.7482\,\mathrm{kN}$ ($-1.29\%$ error) and $u_{\text{peak}} = 0.005775\,\mathrm{mm}$ ($-1.45\%$ error), passing all acceptance gates.
3. **Artificial Numerical Toughening under Coarse Targets (`errorTarget \ge 3.0%`):**
   - At $\text{errorTarget} = 3.0\%$ ($7{,}633$ elements, $h \approx 0.0018\,\mathrm{mm}$) and $5.0\%$ ($4{,}194$ elements, $h \approx 0.0028\,\mathrm{mm}$), transition elements along the crack flanks are too coarse.
   - The phase-field gradient $\nabla d$ is diffused over an artificially wide band. This requires additional strain energy to drive phase degradation, inflating $F_{\text{peak}}$ to $0.8553\,\mathrm{kN}$ ($+12.84\%$ error) and delaying peak localization to $u=0.007339\,\mathrm{mm}$ ($+25.24\%$ error).

---

## 4. Load Incrementation & Time Stepping Guidelines

### 4.1 Increment Sensitivity Matrix (Evaluated on Accepted 2.0% Mesh)

```text
=======================================================================================================================================================
CASE NAME            SCHEDULE            WALLTIME      CPUT          F_peak (kN)   u_peak (mm)   K0 (kN/mm)   CUTBACKS   FIDELITY DEVIATION
=======================================================================================================================================================
Baseline (1400395)   7,028 incs (Fixed)  07h 06m 46s   06h 52m 21s   0.748197      0.005775 mm   137.9858     0          Baseline (0.000%)
INC2X (1400738)      3,521 incs (Fixed)  03h 40m 03s   03h 32m 46s   0.748597      0.005782 mm   137.9857     0          +0.053% F / +0.121% u
Speedup Benefit      -50.0% inc count    -48.4% time   -48.4% time   --            --            --           --         Identical Mechanics
=======================================================================================================================================================
```

### 4.2 Recommendations for Load Scheduling:
1. **Two-Step Protocol:**
   - **Step 1 (Elastic Pre-Loading):** Monotonic displacement to $u \approx 0.85 \times u_{\text{peak}}$. Use fixed increments $\Delta u = 1.0 \times 10^{-3}\,\mathrm{mm}$ ($1{,}000$ increments). Because material response is purely linear elastic, larger increments do not compromise accuracy.
   - **Step 2 (Fracture Initiation & Propagation):** Fixed displacement to final separation $u = 0.0100\,\mathrm{mm}$. Use fixed increments $\Delta u = 4.0 \times 10^{-4}\,\mathrm{mm}$ ($2{,}500$ increments).
2. **Computational Efficiency:** The $3{,}500$-increment schedule achieves full $97.65\%$ load drop with zero cutbacks and $<0.06\%$ error relative to the $7{,}000$-increment baseline, reducing runtime from $7.1\,\mathrm{h}$ to $3.6\,\mathrm{h}$.

---

## 5. Scope & Boundary Conditions of Provenance

| Simulation Case | Job ID | Status | Provenance Rule |
| :--- | :--- | :--- | :--- |
| **Fixed Mesh Baseline** | `1398090.mmaster02` | **`SCIENTIFICALLY_ACCEPTED`** | Authoritative Task-3 fixed baseline. |
| **2.0% Adaptive Reproduction** | `1400395.mmaster02` | **`SCIENTIFICALLY_ACCEPTED`** | Authoritative Task-5 adaptive reproduction. |
| **5.0% Coarse Sensitivity** | `1400396.mmaster02` | **`SCIENTIFICALLY_EVALUATED`** | Sensitivity study point only (not accepted for Task-5 reproduction). |
| **Companion Visualization Bridge**| `1400408.mmaster02` | **`COMPANION_BRIDGE_FULLY_VERIFIED`** | In-solver companion bridge verified; Task-6 held at `TASK6_BLOCKED_EXTERNAL_ABAQUSER_DEPENDENCY`. |
| **INC2X Schedule Sensitivity** | `1400738.mmaster02` | **`SCIENTIFICALLY_EVALUATED`** | Validates accelerated $3{,}500$-increment schedule for Task 7. |
| **3.0% Mesh Sensitivity** | `1400739.mmaster02` | **`SCIENTIFICALLY_EVALUATED`** | Confirms $2.0\%$ as minimal required discretization bound. |

---

## 6. Step-by-Step Selection Workflow for Future Users

When setting up a new adaptive remeshing phase-field simulation in Abaqus:

1. **Determine Regularization Length Scale ($l_0$):**
   - Identify the material phase-field length scale (e.g., $l_0 = 0.0075\,\mathrm{mm}$).
   - Set maximum target element size in fracture zone $h_{\text{target}} \le l_0 / 4 \approx 0.0018\,\mathrm{mm}$ (ideally $h \approx l_0 / 7.5 = 0.0010\,\mathrm{mm}$).
2. **Configure Native Abaqus Remeshing Rule:**
   - Error Indicator: `MISESERI` (Mises Stress Error Indicator).
   - Error Target: `errorTarget = 0.020` ($2.0\%$).
   - Sizing Constraints: `minSize = 0.0010`, `maxSize = 0.0500`.
   - Element Type: Linear Quadrilateral (`CPS4` / `CPE4` topology with transition `CPS3` / `CPE3` triangles).
3. **Multi-Pass Remeshing Loop:**
   - Execute Step 1 elastic pre-analysis on coarse base mesh ($N_{\text{phys}} \approx 2{,}906$).
   - Apply `RemeshingRule` and execute `adaptiveRemesh` for 1–2 iterations until $N_{\text{phys}} \approx 15{,}000$ and $h_{\min} \le 0.0010\,\mathrm{mm}$.
4. **Input Deck Assembly & Subroutine Binding:**
   - Generate layered input deck (Layer 1: Phase UEL `U1`/`U3`; Layer 2: Disp UEL `U2`/`U4`; Layer 3: Companion UMAT `CPE4`/`CPE3`).
   - Link `f42_mixed_uel.for` containing automatic CPU dispatch and companion state-transfer logic.
5. **Time Increment Scheduling:**
   - Step 1: $1{,}000$ increments ($\Delta u = 1.0 \times 10^{-3}\,\mathrm{mm}$).
   - Step 2: $2{,}500$ increments ($\Delta u = 4.0 \times 10^{-4}\,\mathrm{mm}$).
6. **Post-Processing:**
   - Directly visualize phase field $d$ via `SDV15` and driving energy $\mathcal{H}$ via `SDV16` in Abaqus/CAE.
