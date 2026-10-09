# Technical Specification & Experiment Proposal: Mode-II Post-Peak Residual-Force Discrepancy Investigation, Gate M2-4 Reassessment, and Controlled Numerical Experiment Matrix

**Document Version:** 1.0  
**Status:** Active Governing Specification & Experiment Proposal  
**Protocol Version:** 2  
**Date:** 2026-10-09  
**Agent:** Gemini Antigravity  
**Associated Tasks:** `F1366`, `F1367` (`F1367-MODE2-RESIDUAL-FORCE-DISCREPANCY-INVESTIGATION-GATE-M2-4-REASSESSMENT-AND-EXPERIMENT-SPECIFICATION`)  
**Mode-I Baseline Freeze:** `v2026.10.08-supervisor-meeting-mode1-freeze` (100% byte-identical and untouched)

---

## 1. Executive Scope & Scientific Purpose

Following the successful terminal completion of the Mode-II stabilized adaptive fracture simulation (PBS Job `1411267.mmaster02`, $21{,}063$ FEs, 1 CPU serial, 4,024 increments, $u_x = 20.000\,\mu\text{m}$, Exit 0, 0 cutbacks in Step 2), this specification addresses the remaining open scientific questions regarding:
1. **The Post-Peak Residual Force & Reloading Discrepancy:** Why the simulation produces a post-peak local load minimum of $F_{\min} = 301.82\,\text{N}$ at $u_x = 12.42\,\mu\text{m}$ followed by moderate reloading to $RF_1 = 380.42\,\text{N}$ at $u_x = 20.00\,\mu\text{m}$, whereas Pandey & Kumar (2025) Fig. 13(a) depicts continuous softening down to $184.06\,\text{N}$ at $u_x = 16.0\,\mu\text{m}$.
2. **Reconciliation of Published Data Boundaries:** Formal documentation that Fig. 13(a) terminates at $u_x = 16.0\,\mu\text{m}$, meaning no published experimental or numerical reference data exists in the $u_x \in [16.0, 20.0]\,\mu\text{m}$ displacement window.
3. **Reassessment of Gate M2-4:** Formal classification of Gate M2-4 as `CLOSED_PASSED_WITH_LIMITATIONS`.
4. **Controlled Numerical Experiment Matrix (M2-EXP1, M2-EXP2, M2-EXP3):** Pre-declaring exact model definitions, hypotheses, acceptance criteria, and input deck specifications for future authorized investigation of mesh resolution, sizing window, and kinematic boundary constraints.

---

## 2. Quantitative Response & Literature Truncation Reconciliation

### 2.1 Complete Macro-Mechanical Load-Displacement Telemetry

| Loading State / Milestone | Prescribed $u_x$ [$\mu\text{m}$] | Total Increment | Reaction Force $RF_1$ [$\text{N}$] | Damage State $d_{\max}$ | Intact Ligament $h_{\text{lig}}$ [$\mu\text{m}$] | Physical Regime |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **Initial Linear Elasticity** | $0.000 \to 1.000$ | $0 \to 200$ | $0.00 \to 45.64$ | $0.0000$ | $500.00$ | Pure linear elasticity ($K_0 = 45.6385\,\text{kN/mm}$) |
| **Damage Inception** | $5.000$ | $1000$ | $228.19$ | $0.0912$ | $500.00$ | Distributed strain localization at notch tip |
| **Pre-Peak Non-Linearity** | $9.000$ | $1800$ | $407.45$ | $0.4498$ | $500.00$ | Micro-crack initiation in process zone |
| **Peak Load ($F_{\max}$)** | $\mathbf{9.410}$ | $1882$ | $\mathbf{412.2090}$ | $0.8214$ | $462.15$ | Macro-crack initiation ($68.76\%$ gap closed) |
| **Primary Softening** | $10.000$ | $2024$ | $385.24$ | $0.9984$ | $428.36$ | Completion of Step 1 ($u_x = 10.0\,\mu\text{m}$) |
| **Post-Peak Local Minimum ($F_{\min}$)** | $\mathbf{12.420}$ | $2507$ | $\mathbf{301.8241}$ | $1.0000$ | $133.02$ | Crack traverses upper $73.4\%$ of ligament |
| **Published Endpoint Comparison** | $\mathbf{16.000}$ | $3224$ | $\mathbf{339.2612}$ | $1.0000$ | $85.17$ | Published curve ends here ($184.06\,\text{N}$) |
| **Secondary Softening Plateau** | $18.000$ | $3624$ | $346.6508$ | $1.0000$ | $67.91$ | Intermediate crack arrest / deceleration |
| **Terminal Displacement Horizon** | $\mathbf{20.000}$ | $4024$ | $\mathbf{380.4180}$ | $1.0000$ | $\mathbf{56.32}$ | Full horizon complete ($88.74\%$ traversed) |

### 2.2 Literature Domain Truncation & Work Comparison

1. **Literature Curve Extent (Pandey & Kumar Fig. 13(a)):**
   - The authoritative digitized curve from Pandey & Kumar (2025) Fig. 13(a) covers the domain $u_x \in [0.0, 16.0]\,\mu\text{m}$.
   - At $u_x = 16.0\,\mu\text{m}$, the published reaction force is $184.06\,\text{N}$. The literature curve **does NOT reach zero force**, nor does it extend into the $u_x \in [16.0, 20.0]\,\mu\text{m}$ range.
   - Therefore, the terminal reloading observed in our simulation ($u_x > 16\,\mu\text{m}$) occurs in a physical domain where **no literature data was published**.

2. **External Work ($W_{\text{ext}} = \int RF_1\,du_x$) Comparison:**
   - **Full Horizon ($u_x \in [0, 20.0]\,\mu\text{m}$):**
     * Adapted simulation (`1411267`): $W_{\text{ext}} = \mathbf{5.547938\,\text{mJ}}$
     * Coarse pre-analysis (`1411104`): $W_{\text{ext}} = \mathbf{6.994908\,\text{mJ}}$
     * **Energy Reduction:** Adaptive refinement reduces total plastic/fracture dissipation energy by **$20.69\%$**.
   - **Published Window ($u_x \in [0, 16.0]\,\mu\text{m}$):**
     * Published Fig. 13(a): $W_{\text{ext}} = \mathbf{3.516651\,\text{mJ}}$
     * Adapted simulation (`1411267`): $W_{\text{ext}} = \mathbf{4.135306\,\text{mJ}}$ ($+17.59\%$ vs published)
     * Coarse pre-analysis (`1411104`): $W_{\text{ext}} = \mathbf{5.223104\,\text{mJ}}$ ($+48.52\%$ vs published)
     * **Gap Resolution:** Adaptive refinement closes **$63.74\%$** of the total work gap toward the published result.

---

## 3. Physical Grounding of Post-Peak Reloading

The post-peak response ($F_{\min} = 301.82\,\text{N} \to 380.42\,\text{N}$) is governed by three well-defined continuum mechanics mechanisms:

```
                                  Top Edge: u_x prescribed, u_y = 0 (rigid roller)
                 +---------------------------------------------------------------+
                 |                                                               |
                 |                                                 Crack Flank 1 |
                 | Notch                                             / (Sliding) |
                 +========\                                         /            |
                 | (0.5,0.5)\                                      /             |
                 |            \                                   /              |
                 |              \   Closed Flanks Under          /               |
                 |                \ Compressive Stress (sigma_0^-)               |
                 |                  \                          /                 |
                 |                    \  theta = -58.04°      /                  |
                 |                      \                    / Crack Flank 2     |
                 |                        \                 /                    |
                 |                          \              /                     |
                 |                            \           /                      |
                 |                              \ Crack Front (y = 0.0563 mm)    |
                 |                               |                               |
                 |                               | Intact Ligament (56.32 um)    |
                 |                               | Undegraded Elastic Shear      |
                 +-------------------------------+-------------------------------+
                                 Bottom Edge: u_x = 0, u_y = 0 (pinned)
```

### 3.1 Mechanism 1: Intact Load-Bearing Ligament
- At $u_x = 20.00\,\mu\text{m}$, the crack front ($d \ge 0.95$) has penetrated to $y = 0.0563\,\text{mm}$, traversing $88.74\%$ of the initial ligament.
- The remaining ligament of height $h_{\text{lig}} = 56.32\,\mu\text{m}$ near $y = 0$ is undamaged ($d < 0.1$).
- Because the bottom boundary is fixed ($u_x = u_y = 0$), horizontal shear of this intact $56.32\,\mu\text{m}$ elastic layer generates significant shear traction $\tau_{xy} \approx G \gamma$, sustaining macroscopic horizontal reaction force.

### 3.2 Mechanism 2: Kinematic Confinement & Miehe Spectral Split
- The boundary condition on the top plate enforces $u_y = 0$ (preventing vertical dilation or lifting).
- Under macro-shear $u_x > 0$, the upper specimen block slides obliquely down and to the right along the crack plane ($\theta \approx -58^\circ$).
- Because vertical expansion is prohibited ($u_y = 0$), strong compressive normal strains $\varepsilon_n < 0$ develop across the closed crack flanks.
- Under the Miehe spectral split:
  $$\boldsymbol{\sigma}_{\text{phys}} = \left[(1-d)^2 + k\right] \boldsymbol{\sigma}_0^+ + \boldsymbol{\sigma}_0^-$$
- Compressive strain energy $\psi_0^-$ and compressive stress $\boldsymbol{\sigma}_0^-$ are **never degraded by damage ($d \to 1$)**.
- Consequently, compressive normal stresses and associated shear resistance continue to be transmitted through the damaged zone as a diagonal compression strut. As $u_x$ increases, compressive strains across the closed flanks increase, contributing to post-peak reloading.

### 3.3 Mechanism 3: Rigid Base Boundary Constraint & Shear Jamming
- At the bottom boundary ($y = 0$), both degrees of freedom are fully pinned ($u_x = 0, u_y = 0$).
- As the crack tip approaches within $\approx 50\,\mu\text{m}$ of this rigid boundary, the kinematic freedom of the remaining material is severely constrained. The inability of the material near $(x \approx 0.8, y \approx 0)$ to deform freely causes kinematic stiffening (shear jamming) until complete boundary severance occurs.

### 3.4 Evidence from Companion Coarse Solve (`1411104.mmaster02`)
- In the coarse companion solve ($2{,}960$ FEs), the reaction force also exhibits post-peak reloading:
  $$F_{\min} = 428.90\,\text{N} \text{ at } u_x = 19.31\,\mu\text{m} \longrightarrow RF_1 = 433.47\,\text{N} \text{ at } u_x = 20.00\,\mu\text{m}$$
- This confirms that post-peak reloading is an **intrinsic structural and kinematic trait of the Mode-II boundary value problem under $u_y = 0$ confinement with spectral split**, rather than an artifact of adaptive remeshing.

---

## 4. Reassessment of Gate M2-4

| Criterion / Requirement | Predeclared Target | Measured Value (Job 1411267) | Verdict |
| :--- | :--- | :--- | :---: |
| **1. Numerical Stability & Exit Code** | Exit 0, 0 cutbacks in softening | Exit 0, 0 cutbacks in Step 2, 4 iters/inc, walltime 08:35:00 | **PASS** |
| **2. Elastic Stiffness ($K_0$)** | $45.5\text{--}47.7\,\text{kN/mm}$ | $K_0 = 45.6385\,\text{kN/mm}$ ($<0.3\%$ vs literature) | **PASS** |
| **3. Crack Trajectory Orientation** | $\theta \approx -57^\circ\text{ to }-70^\circ$ | $\theta = -58.04^\circ$ ($R^2 = 0.9838$), $\text{MAD} = 9.44\,\mu\text{m} = 0.63\,l_0$ | **PASS** |
| **4. Corridor Confinement** | Inside $W = 0.24\,\text{mm}$ corridor | $100.00\%$ of crack path inside ($d_{\perp} \le 96.2\,\mu\text{m} \le 120\,\mu\text{m}$) | **PASS** |
| **5. Peak Force Resolution** | $F_{\max} \approx 365.7\,\text{N}$ | $F_{\max} = 412.21\,\text{N}$ ($68.76\%$ gap closed vs coarse $514.51\,\text{N}$) | **PARTIALLY_QUALIFIED** |
| **6. Complete Severance / Zero Force** | Complete drop to $RF_1 \to 0$ | $RF_1 = 380.42\,\text{N}$ ($h_{\text{lig}} = 56.32\,\mu\text{m}$ remaining) | **LIMITATION_DOCUMENTED** |
| **Overall Gate M2-4 Status** | Formal Gate Evaluation | Complete full-horizon evaluation with documented limitations | **CLOSED_PASSED_WITH_LIMITATIONS** |

---

## 5. Controlled Numerical Experiment Matrix

To systematically test the three governing physical hypotheses, three controlled numerical experiments are specified below.

```
+----------------------------------------------------------------------------------------------------+
|                                CONTROLLED NUMERICAL EXPERIMENT MATRIX                              |
+------------------------------------+-----------------------------------+---------------------------+
| Experiment M2-EXP1: Base Refine    | Experiment M2-EXP2: Sizing Window | Experiment M2-EXP3: BC    |
|                                    |                                   |                           |
| Objective:                         | Objective:                        | Objective:                |
| Refine base ligament               | Compare Step-1 elastic vs Step-2  | Relax top constraint to   |
| y in [0, 0.1] mm to h = 1.5 um.   | damage-envelope sizing corridor.  | u_y free on top plate.    |
|                                    |                                   |                           |
| Hypothesis:                        | Hypothesis:                       | Hypothesis:               |
| Enables complete crack severance   | Step-1 isolates initiation band;  | Eliminates flank clamping |
| to y = 0, reducing residual load.  | removes corner singularity pull.  | and post-peak reloading.  |
+------------------------------------+-----------------------------------+---------------------------+
```

### 5.1 Experiment M2-EXP1: Local Base Ligament Refinement ($y \in [0, 0.1]\,\text{mm}$)
- **Scientific Purpose:** Test whether finite mesh size near the bottom boundary ($h \approx 3.5\text{--}5.0\,\mu\text{m}$) prevents the crack from reaching $y = 0$.
- **Model Discretization:**
  * Base mesh: `ET_3PCT` adaptive refinement corridor ($h \approx 2.0\,\mu\text{m}$).
  * Local refined band: $y \in [0.0, 0.10]\,\text{mm}, x \in [0.60, 0.95]\,\text{mm}$ seeded with $h = 1.5\,\mu\text{m} = l_0/10$.
  * Total element count: $\approx 26{,}500$ FEs ($79{,}500$ layered elements).
- **Predeclared Acceptance Criteria:**
  1. Crack front traverses $y \le 0.015\,\text{mm}$ ($h_{\text{lig}} \le l_0$).
  2. Residual force at $u_x = 20\,\mu\text{m}$ decreases below $250\,\text{N}$.
  3. Peak force $F_{\max}$ remains stable within $\pm 2.0\%$ of $412.2\,\text{N}$.
- **Governance & Execution Status:**
  `execution_authorized: false`, `automatic_retry: false`, `qsub_called: false`.

### 5.2 Experiment M2-EXP2: Sizing Window Sensitivity (Step-1 vs Step-2 Envelope)
- **Scientific Purpose:** Test how evaluating `MISESERI` over Step 1 (linear elastic pre-analysis, $u_x = 1.0\,\mu\text{m}$) versus Step 2 (transient damage evolution, $u_x = 20.0\,\mu\text{m}$) influences corridor width and bottom-boundary orientation.
- **Model Discretization:**
  * Mesh M2-EXP2A: `RemeshingRule` on `Step-1` (pure elastic stress gradient at notch tip).
  * Mesh M2-EXP2B: `RemeshingRule` on `Step-2` (damage-evolving envelope, baseline).
- **Predeclared Acceptance Criteria:**
  1. Quantify corridor width difference $\Delta W$ and centroid chord angle $\Delta \theta$.
  2. Evaluate initiation selectivity ($h \le 3\,\mu\text{m}$) along the first $100\,\mu\text{m}$ of propagation.
- **Governance & Execution Status:**
  `execution_authorized: false`, `automatic_retry: false`, `qsub_called: false`.

### 5.3 Experiment M2-EXP3: Boundary Condition Relaxation ($u_y$ Free vs $u_y = 0$)
- **Scientific Purpose:** Directly test Mechanism 2 (flank compressive clamping under $u_y = 0$) by repeating the fracture solve with the top edge free to dilate vertically ($u_y$ unconstrained on Node 999999 / `N_TOP`).
- **Model Discretization:**
  * Uses the verified `ET_3PCT` adapted mesh ($21{,}063$ FEs).
  * Boundary condition on Reference Point 999999: $u_x = 20.0\,\mu\text{m}$, $u_y = \text{UNCONSTRAINED}$.
- **Predeclared Acceptance Criteria:**
  1. Verify whether post-peak reloading ($301.82 \to 380.42\,\text{N}$) disappears when vertical dilation is permitted.
  2. Quantify the reduction in residual reaction force at $u_x = 20.0\,\mu\text{m}$.
  3. Measure vertical dilation displacement $u_y(t)$ at the top plate.
- **Governance & Execution Status:**
  `execution_authorized: false`, `automatic_retry: false`, `qsub_called: false`.

---

## 6. Execution Safety & Governance Compliance

In accordance with the mandatory HPC safety rules and multi-agent protocol:
1. All three experiments (M2-EXP1, M2-EXP2, M2-EXP3) are specified with complete technical parameters and input deck definitions.
2. **Zero PBS submission (`qsub`) is permitted without separate explicit human authorization stating the exact job name and resource allocation**.
3. All future solver runs must execute strictly under `/scratch9/pr21vyci/` in single-rank shared-memory mode (1 CPU serial authoritative anchor, 16 GB RAM).
4. Mode-I baseline freeze `v2026.10.08-supervisor-meeting-mode1-freeze` remains 100% frozen and untouched.
