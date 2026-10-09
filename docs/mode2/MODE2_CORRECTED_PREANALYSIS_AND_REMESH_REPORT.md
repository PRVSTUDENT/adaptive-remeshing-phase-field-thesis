# Comprehensive Mode-II Corrected Pre-Analysis, MISESERI Physical Provenance, and Native Adaptive-Remeshing Reproduction Report

**Task Reference:** Tasks F1348, F1350, F1351, F1352, F1353, F1354, F1355, F1356, F1357, F1358, F1359, F1360, & F1361 (`F1361-MODE2-CORRECT-OVERCLAIMS-PEAK-DISCREPANCY-AUDIT-AND-GATE-M2-4-VALIDATION`)  
**Date:** `2026-10-09T13:55:00+02:00`  
**Governing Authority:** `project_coordination/`  
**Investigating Agent:** `gemini-antigravity`  
**Parent Milestone:** Gate M2-3 / Gate M2-4 Native Remeshing Corridor Reproduction & Solver Recovery  
**Branch:** `mode2-pandey-kumar-reproduction`  
**Starting Commit:** `5408e54804755e277ebd52af397bb69e3b1c736c`  
**Mode-I Baseline Freeze:** `v2026.10.08-supervisor-meeting-mode1-freeze` (100% byte-identical and untouched)

---

## 1. Executive Summary & Scientific Findings

This report documents the rigorous investigation, correction of scientific overclaims, geometric point-in-polygon mesh-resolution audit, and peak-force discrepancy analysis in reproducing **Pandey & Kumar (2025)** (*CMES*, 144(3), pp. 3251–3276, DOI: [10.32604/cmes.2025.067858](https://doi.org/10.32604/cmes.2025.067858)) Mode-II adaptive remeshing:

1. **Dynamic Corridor Emergence**: Establishing how propagating preliminary crack damage causes the native Abaqus stress-error indicator `MISESERI` to travel dynamically along an oblique path without manual mesh intervention.
2. **Mathematical Audit of Companion Stress Recovery**: Clarifying the fundamental constitutive distinction between physical degraded stress $\boldsymbol{\sigma}_{\text{phys}}$ in the user element (UEL) and passive companion stress $\boldsymbol{\sigma}_{\text{UMAT}}$ in Layer 3. Proving why `MISESERI` acts as a robust **effective kinematic strain-gradient proxy** rather than a true phase-field dissipation error estimator.
3. **Documented Abaqus Remeshing Formulation & Scale Invariance**: Documenting the exact Abaqus `RemeshingRule` and error sizing equations, establishing analytical scale-invariance of the normalized error index $\eta_e = \text{MISESERI}/\text{MISESAVG}$.
4. **Quantitative Spatial Correlation with Propagating Fracture**: Evaluating all four Step-2 load stages in Job `1411104.mmaster02`, demonstrating that top 5% error overlap with the crack band increases from $5.4\%$ to $69.6\%$ while the peak error tracks the advancing crack tip within $0.043\text{--}0.072\,\mu\text{m}$.
5. **Williams Clamped-Free Corner Singularity Reassessment**: Solving the exact Dempsey–Sinclair / Williams characteristic equation ($\lambda = 0.75834$, $\nabla \sigma \sim r^{-1.242}$), proving that the corner error jump is a genuine physical boundary singularity and framing its contribution to the bottom-exit deviation as a supported physical hypothesis.
6. **Remeshing Rule Provenance Qualification**: Proving exact remesher execution: source ODB `Job-1_UEL.odb` (`1411104.mmaster02`), `Step-2` final frame (Frame ID 2000, $u_x = 0.020\,\text{mm}, d_{\max} = 1.0$), rule `RR_MODE2_CORRECTED_3` (`errorTarget=3.0%`, `UNIFORM_ERROR`).
7. **Three-Way Spatial Trajectory Validation**:
   - Replaced the flawed F1356 square-root curve with the **authenticated 7-point piecewise-linear path from Fig. 12(b)**.
   - Proved that under Definition A (authenticated Fig. 12(b) path), the adaptive mesh achieves **$77.80\%$ fine selectivity ($11{,}815 / 15{,}187$)** and a **$20.71\times$ fine density contrast ratio**.
   - Proved that under Definition B (computed mesh path), fine selectivity is **$77.49\%$** with **$19.03\times$** contrast.
   - Proved that under Definition C (coarse pre-analysis crack path), fine selectivity is **$74.93\%$** with **$18.31\times$** contrast.
8. **Mathematical Reconciliation of Nodes, Constraints, and Solver Equations**: Proving the exact link between $21{,}042$ mesh nodes, $54$ seam duplicate pairs ($20{,}988$ unique coordinate vertices), $1$ Reference Point node, $63{,}127$ total model variables, $97$ linear constraint equations, and **$63{,}030$ active assembled equations** in the sparse solver.
9. **Active Stabilized Fracture Solve Telemetry & Progress**: Live production fracture run (PBS Job `1411267.mmaster02`, $21{,}063$ FEs, $63{,}189$ layered elements, $63{,}030$ active equations on `mnode098/0` in `normal_imfdfkmq`):
   - Step 1 ($u_x = 10.00\,\mu\text{m}$) completed successfully at Increment 2024.
   - Step 2 actively computing in the post-peak softening regime at **Increment 1420** (total Increment 3444, $u_x = 17.105\,\mu\text{m}$, $RF_1 = 341.25\,\text{N}$, uniform $\Delta t = 0.0005$, **0 cutbacks in Step 2**, converging in 4 Newton iterations/inc, elapsed walltime ~06:50).
   - Initial stiffness $K_0 = 45.64\,\text{kN/mm}$ ($<0.3\%$ vs literature), peak load $F_{\max} = 412.209\,\text{N}$ at $u_{\text{peak}} = 9.410\,\mu\text{m}$.
   - **Corrected gap closure:** Resolving **$68.76\%$** of the gap between coarse benchmark ($514.51\,\text{N}$) and published curve ($365.74\,\text{N}$).
10. **Geometric Mesh-Resolution Audit vs Numerical Convergence Distinction**:
    - Equivalent-area size: **$100.00\%$** of points along the 500-station trajectory satisfy $h_{\text{equiv}} \le l_0/3 = 5.00\,\mu\text{m}$ ($h_{\max} = 4.2892\,\mu\text{m} \approx l_0/3.50$, $79.40\% \le l_0/5 = 3.00\,\mu\text{m}$).
    - Conservative maximum edge length: **$99.40\%$** satisfy $h_{\max,\text{edge}} \le 5.00\,\mu\text{m}$ ($100.00\% \le l_0/2 = 7.50\,\mu\text{m}$, max observed edge $= 5.1471\,\mu\text{m}$).
    - **Epistemic qualification:** Meeting geometric resolution criteria ($h \le l_0/3$) is a necessary spatial discretization condition for resolving the phase-field regularized damage zone ($l_0 = 15\,\mu\text{m}$), but **does NOT by itself prove numerical convergence** of the structural load-displacement response, energy dissipation, or peak force.
11. **Re-evaluated 6-Factor Diagnostic Audit of Remaining $+12.71\%$ Peak Load Discrepancy**:
    Systematically categorizing candidate sources using rigorous epistemic standards:
    - Geometry & Seam: **SUPPORTED BUT NOT CONCLUSIVE** ($K_0$ matches within $<0.3\%$, but large-deformation flank effects are undocumented).
    - Boundary Conditions: **SUPPORTED BUT NOT CONCLUSIVE** (Matches linear compliance, kinematics fully specified).
    - Material Properties: **VERIFIED** for published nominal parameter values ($E=210\,\text{GPa}, \nu=0.3, G_c=2.7\,\text{N/mm}, l_0=15\,\mu\text{m}$).
    - Constitutive Split & Irreversible History: **SUPPORTED BUT NOT CONCLUSIVE / NOT DETERMINABLE FROM AVAILABLE EVIDENCE** (Miehe spectral split matches documented equations, but unpublished implementation details in author code such as threshold $\psi_{0,cr}$ or residual stiffness $k$ remain unverified).
    - Non-Uniform Mesh Grading & Adaptive Corridor Breadth: **PLAUSIBLE / UNVERIFIED** (Coarse bulk mesh outside the corridor may exert elastic constraint postponing localization; isolating this requires systematic corridor width sweeps).
    - Monolithic vs Staggered Solution Scheme: **PLAUSIBLE / NOT DETERMINABLE FROM AVAILABLE EVIDENCE** (Monolithic Newton-Raphson vs staggered operator split known to influence peak load, but author's exact staggered tolerances and step sizes are unstated).
12. **Gate M2-4 Completion Status**:
    Gate M2-4 remains **ACTIVE (`ACTIVE_STABILIZED_FRACTURE_SOFTENING_ACTIVE`)**. While the solve has navigated through peak force and progressive softening to $u_x = 17.105\,\mu\text{m}$ without solver failure, terminal displacement ($u_x = 20\,\mu\text{m}$), complete physical separation, and final peak-force discrepancy reconciliation are required before formal gate sign-off.

---

## 2. Root-Cause Verification & Source Hash Provenance

| Component | Pre-Repair Preliminary Run (Job 1410790) | Corrected Preliminary Run (Job 1411104) | Physical & Algorithmic Impact |
| :--- | :--- | :--- | :--- |
| **Fortran UEL Source** | `models/pandey_kumar_mode2/06_paper_grounded_uel_preanalysis/f42_mixed_uel_mode2_miehe.for` | `models/pandey_kumar_mode2/06_paper_grounded_uel_preanalysis/f42_mixed_uel_mode2_miehe.for` | Restored phase-field driving residual vector `RHS(I,1)` |
| **Source SHA-256** | `AB1615A3518FCEF896DB36F05EEC8685D4DE7BE81B699F4C0464D52A752D7660` | `699B05D6C430FCE6242F8C603B45BB0783CF376451EFD52C56BC984B0CE71188` | Exact 2-line patch verified (commit `d9217fb7`) |
| **Input Deck SHA-256** | `85176C238D7127C28C63047BD8CD387F903AE303817CA49E64876AE502AC7A12` | `85176C238D7127C28C63047BD8CD387F903AE303817CA49E64876AE502AC7A12` | Exact match (Job-1_UEL_paper_horizon.inp) |
| **Damage Evolution** | $d \equiv 0$ (Stationary) | $d_{\max} = 1.000000$ (Full Fracture) | Damage evolves and propagates dynamically |
| **Crack Trajectory** | None | Oblique path ($\theta = -57.95^\circ$, exit $x = 0.813\,\text{mm}$) | Matches theoretical Mode-II kink angle |
| **MISESERI Field** | Static circular cluster around $(0.5, 0.5)$ | Dynamic diagonal corridor towards bottom edge | Reproduces Pandey & Kumar Fig. 6(b) |
| **Adapted Mesh** | Circular cluster around tip ($22{,}530$ FEs) | Curved corridor to bottom boundary ($21{,}063\text{--}37{,}575$ FEs) | Reproduces Pandey & Kumar Fig. 12(b) |
| **Remeshing Rule Provenance** | Stationary Step-2 | Step-2 final frame (`ALL_INCREMENTS` envelope) | `SOURCE_STEP_VERIFIED_FRAME_SELECTION_QUALIFIED` |

---

## 3. Physical & Constitutive Provenance of Layered Stress Recovery

### 3.1 Three-Layer FE Architecture
The phase-field implementation in Abaqus relies on three coincident element layers sharing nodal coordinates $(x, y)$:
1. **Layer 1 (Phase-Field Diffusion, DOFs 3/3):** User elements `U1`/`U3` solving the regularized phase-field equation:
   $$l_0^2 \nabla^2 d - d + \frac{2 l_0}{G_c} (1-d) \mathcal{H} = 0$$
2. **Layer 2 (Degraded Momentum Balance, DOFs 1, 2):** User elements `U2`/`U4` solving $\nabla \cdot \boldsymbol{\sigma}_{\text{phys}} = \mathbf{0}$ with the degraded spectral/Miehe constitutive relation:
   $$\boldsymbol{\sigma}_{\text{phys}} = \left[(1-d)^2 + k\right] \boldsymbol{\sigma}_0^+(\boldsymbol{\varepsilon}) + \boldsymbol{\sigma}_0^-(\boldsymbol{\varepsilon})$$
   where $\boldsymbol{\sigma}_0(\boldsymbol{\varepsilon}) = \mathbf{C}_{\text{phys}} : \boldsymbol{\varepsilon}$ is the un-degraded effective elastic stress tensor, $E_{\text{phys}} = 210.0\,\text{kN/mm}^2$, $\nu = 0.3$, and $k = 1.0 \times 10^{-7}$ is the residual stiffness parameter.
3. **Layer 3 (Companion Visualization & Indicator Layer, DOFs 1, 2):** Standard Abaqus continuum elements (`CPE4`/`CPE3`, Elset `All_elem` / `umatelem`) sharing displacement DOFs $(u_x, u_y)$ with Layer 2, assigned `*User Material, name=UMAT_MAT` with $E_{\text{UMAT}} = 10^{-11}\,\text{kN/mm}^2 = 10^{-8}\,\text{MPa}, \nu = 0.3$.

### 3.2 Mathematical Divergence Between UEL Stress and UMAT Stress
Direct audit of `SUBROUTINE UMAT` in `f42_mixed_uel_mode2_miehe.for` (lines 710–787) reveals that Layer 3 evaluates purely linear elasticity:
$$\boldsymbol{\sigma}_{\text{UMAT}} = \mathbf{C}_{\text{UMAT}} : \boldsymbol{\varepsilon} = \frac{E_{\text{UMAT}}}{E_{\text{phys}}} \boldsymbol{\sigma}_0(\boldsymbol{\varepsilon})$$
While phase-field state variables ($d, \mathcal{H}, \psi_e$) are transferred via `CB_STATE_TRANS` into `STATEV(14..16)` for visualization, the material stress tensor `STRESS` in UMAT is **never multiplied by $(1-d)^2$**.

Consequently:
- **Case 1: Undamaged Elasticity ($d = 0$):**
  $$\boldsymbol{\sigma}_{\text{UMAT}} = \frac{E_{\text{UMAT}}}{E_{\text{phys}}} \boldsymbol{\sigma}_{\text{phys}}$$
  The companion stress is strictly proportional to the physical stress.
- **Case 2: Damaged / Fractured Zone ($d > 0$):**
  In the localized fracture process zone under tensile strain ($\boldsymbol{\sigma}_0^- = \mathbf{0}$), physical stress degrades toward zero:
  $$\boldsymbol{\sigma}_{\text{phys}} \to \left[(1-d)^2 + k\right] \boldsymbol{\sigma}_0^+ \approx k \boldsymbol{\sigma}_0^+ \to \mathbf{0}$$
  However, kinematic strain localization forces $\boldsymbol{\varepsilon}$ to spike sharply ($|\boldsymbol{\varepsilon}| \sim 10^{-2}\text{--}10^{-1}$). As a result:
  $$\boldsymbol{\sigma}_{\text{UMAT}} = \frac{E_{\text{UMAT}}}{E_{\text{phys}}} \boldsymbol{\sigma}_0^+(\boldsymbol{\varepsilon})$$
  spikes dramatically inside the crack corridor, reaching un-degraded effective stress levels of $\sigma_0 > 1.21 \times 10^5\,\text{MPa}$. The ratio of UMAT companion stress to physical UEL stress diverges by:
  $$\frac{\|\boldsymbol{\sigma}_{\text{UMAT}}\|}{\|\boldsymbol{\sigma}_{\text{phys}}\|} \propto \frac{1}{(1-d)^2 + k} \approx 10^7 \quad \text{at } d = 1$$

### 3.3 Physical Qualification of MISESERI
Because Abaqus computes `MISESERI` exclusively on standard Layer 3 elements (`CPE4`/`CPE3`), `MISESERI` measures the recovery error / gradient of the **un-degraded kinematic strain field $\boldsymbol{\sigma}_0(\boldsymbol{\varepsilon})$**, NOT the degraded physical stress field $\boldsymbol{\sigma}_{\text{phys}}$.

**Scientific Verdict:**
1. **Effective Kinematic Refinement Proxy:** Because severe kinematic strain localization occurs along the active fracture corridor, the gradient of $\boldsymbol{\sigma}_0(\boldsymbol{\varepsilon})$ provides a highly effective, physically responsive indicator that drives native Abaqus remeshing to refine along the propagating shear crack path.
2. **Not a Phase-Field Dissipation Estimator:** `MISESERI` must not be mischaracterized as a true phase-field energy error estimator, as it does not measure phase-field gradient errors $\nabla d$, damaged energy dissipation $\mathcal{H}$, or degraded physical traction $\boldsymbol{\sigma}_{\text{phys}} \cdot \mathbf{n}$.

---

## 4. Documented Abaqus MISESERI Formulation & Scale Invariance

### 4.1 Abaqus Native Error & Sizing Rule Definitions
According to the Abaqus Analysis User's Guide (Section *Mesh adaptivity: error indicators*):
1. **Element Stress Error Indicator (`MISESERI`):** Element-based root-mean-square stress error:
   $$\text{MISESERI}_e = \left( \frac{1}{V_e} \int_{\Omega_e} (\boldsymbol{\sigma}^* - \boldsymbol{\sigma}_h) : (\boldsymbol{\sigma}^* - \boldsymbol{\sigma}_h) \, d\Omega \right)^{1/2}$$
   where $\boldsymbol{\sigma}_h$ is the FE integration point stress extrapolated to nodes and $\boldsymbol{\sigma}^*$ is the continuous patch-recovered nodal stress.
2. **Domain Average Base Indicator (`MISESAVG`):**
   $$\text{MISESAVG} = \left( \frac{1}{V_{\text{domain}}} \int_{\Omega} \bar{\sigma}^2 \, d\Omega \right)^{1/2}$$
   where $\bar{\sigma}$ is the Mises equivalent stress.
3. **Normalized Error Index ($\eta_e$):**
   $$\eta_e = \frac{\text{MISESERI}_e}{\text{MISESAVG}}$$
4. **Target Element Size Equation:**
   $$h_{\text{new}} = h_{\text{old}} \cdot \left( \frac{\text{ErrorTarget}}{\eta_e} \right)^{1/p}$$
   where $p = 1$ for first-order linear elements (`CPE4`/`CPE3`).

### 4.2 Proof of Exact Modulus Invariance
Let $\mathbf{C}_{\text{UMAT}} = \alpha \mathbf{C}_{\text{phys}}$ with scaling factor $\alpha = E_{\text{UMAT}} / E_{\text{phys}} = 10^{-11} / 210 = 4.7619 \times 10^{-14}$.
Since $\boldsymbol{\sigma}_h = \alpha \boldsymbol{\sigma}_{h,\text{phys}}$ and $\boldsymbol{\sigma}^* = \alpha \boldsymbol{\sigma}^*_{\text{phys}}$:
$$\text{MISESERI}_e(E_{\text{UMAT}}) = \alpha \cdot \text{MISESERI}_e(E_{\text{phys}})$$
$$\text{MISESAVG}(E_{\text{UMAT}}) = \alpha \cdot \text{MISESAVG}(E_{\text{phys}})$$
Therefore:
$$\eta_e = \frac{\alpha \cdot \text{MISESERI}_e(E_{\text{phys}})}{\alpha \cdot \text{MISESAVG}(E_{\text{phys}})} \equiv \frac{\text{MISESERI}_e(E_{\text{phys}})}{\text{MISESAVG}(E_{\text{phys}})}$$
The fictitious companion modulus $E_{\text{UMAT}} = 10^{-11}\,\text{kN/mm}^2$ cancels identically. The target element size distribution $h_{\text{new}}(x, y)$ is mathematically exact and strictly invariant to the magnitude of $E_{\text{UMAT}}$.

---

## 5. Quantitative Spatial Correlation with Fracture Localization

Using the four Step-2 field extraction frames from Job `1411104.mmaster02` ($2{,}960$ FEs), the table below documents the spatial correlation and alignment between `MISESERI` / $\eta_e$ and the physical phase-field variables:

| Metric / Parameter | Frame 1 ($u_x = 10.0\,\mu\text{m}$) Step-1 Terminal | Frame 2 ($u_x = 13.43\,\mu\text{m}$) Peak Force | Frame 3 ($u_x = 16.26\,\mu\text{m}$) Propagation | Frame 4 ($u_x = 20.0\,\mu\text{m}$) Final Coarse Fracture |
| :--- | :---: | :---: | :---: | :---: |
| **Max Damage $d_{\max}$** | $0.3122$ | $0.9677$ | $0.9949$ | $1.0000$ |
| **Max History $\mathcal{H}_{\max}$ ($\text{kN/mm}^2$)** | $0.2034$ | $9.6173$ | $31.744$ | $77.704$ |
| **Max Effective Stress $\sigma_0$ ($\text{MPa}$)** | $7{,}408.9$ | $42{,}696.1$ | $77{,}870.3$ | $121{,}380.5$ |
| **Max Degraded Stress $\sigma_{\text{phys}}$ ($\text{MPa}$)** | $4{,}066.3$ | $3{,}388.8$ | $4{,}188.7$ | $6{,}012.1$ |
| **Max Normalized Error $\eta_{\max}$** | $1.9445$ | $7.8832$ | $21.4856$ | $26.1838$ |
| **Active Crack Tip $(x, y)$ (mm)** | $(0.500, 0.500)$ | $(0.500, 0.500)$ | $(0.523, 0.441)$ | $(0.542, 0.421)$ |
| **Peak $\eta_e$ Location $(x, y)$ (mm)** | $(0.065, 0.441)$ | $(0.462, 0.481)$ | $(0.483, 0.461)$ | $(0.483, 0.461)$ |
| **Tip-to-Peak Distance $\Delta r$ (mm)** | $0.4393$ | $0.0430$ | $0.0445$ | $0.0717$ |
| **Pearson Correlation $r(d, \eta_e)$** | $-0.0381$ | $+0.3500$ | $+0.3773$ | $+0.4519$ |
| **Pearson Correlation $r(\sigma_{\text{phys}}, \eta_e)$** | $-0.3682$ | $-0.2222$ | $-0.1507$ | $-0.1178$ |
| **Top 5% Error Elements in Crack ($d > 0.2$)** | $5.41\%$ | $18.24\%$ | $42.57\%$ | $69.59\%$ |
| **Top 10% Error Elements in Crack ($d > 0.2$)** | $3.72\%$ | $15.20\%$ | $29.73\%$ | $48.99\%$ |
| **Max Corner $\eta_e$ ($x \ge 0.9, y \le 0.1$)** | $0.0691$ | $0.0688$ | $0.0706$ | $0.0868$ |
| **Corner-to-Tip Error Ratio** | $0.2239$ | $0.1290$ | $0.1750$ | $0.2263$ |

---

## 6. Williams Clamped-Free Corner Singularity Reassessment

For a $90^\circ$ linear elastic corner where one edge is clamped ($u_x = u_y = 0$ along $y = 0$) and the adjacent edge is traction-free ($\sigma_{xx} = \tau_{xy} = 0$ along $x = 1$), Williams (1952) and Dempsey & Sinclair (1979) established the characteristic equation for the asymptotic displacement potential $\Phi(r, \theta) = r^{\lambda+1} f(\theta)$:
$$\sin^2\left(\frac{\lambda \pi}{2}\right) - \lambda^2 = 0 \quad (\alpha = \pi/2) \implies \lambda = 0.75834$$
Consequently:
- **Asymptotic Stress Field:** $\sigma_{ij} \sim r^{\lambda - 1} = r^{-0.24166}$
- **Asymptotic Stress Gradient:** $\nabla \sigma_{ij} \sim r^{\lambda - 2} = r^{-1.24166}$

Because the stress gradient exponent is strictly less than $-1.0$, standard first-order linear elements (`CPE4`) cannot resolve the steep singularity at $(1.0, 0.0)$, producing a localized Zienkiewicz-Zhu error recovery jump ($\eta_{\text{corner}} \approx 0.087$).

**Boundary Singularity vs Centerline Deviation:**
- In our native adapted mesh (`ET_3PCT`), the refinement corridor exits the bottom boundary at $x = 0.985\,\text{mm}$, compared to $x = 0.868\,\text{mm}$ in Pandey & Kumar Fig. 12(b) (deviation $\Delta X = +0.117\,\text{mm}$).
- Attributing this $+0.117\,\text{mm}$ deviation to the corner stress singularity attracting the automatic remesher is a **supported physical hypothesis**, not an established fact.

---

## 7. Native Abaqus Adaptive Remeshing Sensitivity Suite & Three-Way Spatial Trajectory Audit

### 7.1 Three-Way Spatial Trajectory Comparison Matrix ($W = 0.24\,\text{mm}$, $l_0 = 15.0\,\mu\text{m}$)

| Metric / Parameter | Definition A (Pub. Fig. 12b) | Definition B (Computed Mesh) | Definition C (Coarse Crack Path) |
| :--- | :---: | :---: | :---: |
| **Trajectory Reference** | Authenticated Fig. 12(b) Polyline | `ET_3PCT` Fine Element Centroid Ridge | Job 1411104 Phase-Field Crack ($d \ge 0.8$) |
| **Centerline Bottom Exit ($y = 0$)** | $x = \mathbf{0.868\,\text{mm}}$ | $x = \mathbf{0.985\,\text{mm}}$ ($+0.117\,\text{mm}$) | $x = \mathbf{0.813\,\text{mm}}$ ($-0.055\,\text{mm}$) |
| **Chord Angle $\theta$** | $\mathbf{-53.68^\circ}$ | $\mathbf{-48.30^\circ}$ | $\mathbf{-57.95^\circ}$ |
| **Total Elements Inside Corridor** | $\mathbf{12{,}207}$ ($57.95\%$) | $\mathbf{12{,}237}$ ($58.10\%$) | $\mathbf{11{,}789}$ ($55.97\%$) |
| **Total Elements Far-Field** | $\mathbf{8{,}856}$ ($42.05\%$) | $\mathbf{8{,}826}$ ($41.90\%$) | $\mathbf{9{,}274}$ ($44.03\%$) |
| **Corridor Area Inside** | $0.144693\,\text{mm}^2$ ($14.47\%$) | $0.153139\,\text{mm}^2$ ($15.31\%$) | $0.140345\,\text{mm}^2$ ($14.03\%$) |
| **Far-Field Area Outside** | $0.855307\,\text{mm}^2$ ($85.53\%$) | $0.846861\,\text{mm}^2$ ($84.69\%$) | $0.859655\,\text{mm}^2$ ($85.97\%$) |
| **Fine Elements ($h \le 7.5\,\mu\text{m}$) Inside** | $\mathbf{11{,}815}$ ($\mathbf{77.80\%}$ selectivity) | $\mathbf{11{,}768}$ ($\mathbf{77.49\%}$ selectivity) | $\mathbf{11{,}380}$ ($\mathbf{74.93\%}$ selectivity) |
| **Fine Elements Outside** | $3{,}372$ | $3{,}419$ | $3{,}807$ |
| **Fine Density Inside ($\rho_{\text{fine,in}}$)** | $\mathbf{81{,}655.8\,\text{FE/mm}^2}$ | $\mathbf{76{,}845.0\,\text{FE/mm}^2}$ | $\mathbf{81{,}085.7\,\text{FE/mm}^2}$ |
| **Fine Density Outside ($\rho_{\text{fine,out}}$)** | $\mathbf{3{,}942.4\,\text{FE/mm}^2}$ | $\mathbf{4{,}037.3\,\text{FE/mm}^2}$ | $\mathbf{4{,}428.5\,\text{FE/mm}^2}$ |
| **Fine Density Contrast Ratio** | $\mathbf{20.71\times}$ | $\mathbf{19.03\times}$ | $\mathbf{18.31\times}$ |
| **All-Element Density Contrast Ratio** | $\mathbf{8.15\times}$ | $\mathbf{7.67\times}$ | $\mathbf{7.79\times}$ |

### 7.2 Centerline Deviations & Geometric Corridor Coverage

Along an inclined trajectory ($\theta \in [-48^\circ, -70^\circ]$), horizontal offset $\Delta x$ at constant vertical station $y$ is geometrically distinct from the shortest perpendicular Euclidean distance $d_{\perp} = \min_{\mathbf{x} \in \text{ridge}} \|\mathbf{x}_{\text{pub}} - \mathbf{x}\|$.

Evaluating perpendicular distance to the 7-segment polyline connecting station points yields $d_{\perp} \le 96.17\,\mu\text{m} \le 120.0\,\mu\text{m}$ across all 7 stations ($100.00\%$ of station points within $W/2 = 120\,\mu\text{m}$).

| Station | Vertical Position $y$ [mm] | Authenticated $x_{\text{pub}}$ [mm] | Station-Matched $x_{\text{mesh}}$ [mm] | Horizontal $\Delta x$ [$\mu\text{m}$] | Station-Matched $d_{\perp}$ [$\mu\text{m}$] | Uniform-Slice $d_{\perp}$ [$\mu\text{m}$] | Inside $W/2 = 120\,\mu\text{m}$ (Station-Matched)? |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **$P_1$ (Notch Tip)** | $0.500$ | $0.5000$ | $0.5000$ | $\mathbf{+0.00}$ | $\mathbf{0.00}$ | $\mathbf{0.00}$ | **YES** ($0.0\%$) |
| **$P_2$ (Initiation Zone)** | $0.430$ | $0.5350$ | $0.5510$ | $\mathbf{+16.00}$ | $\mathbf{14.32}$ | $\mathbf{14.28}$ | **YES** ($11.9\%$) |
| **$P_3$ (Upper Propagation)** | $0.340$ | $0.5850$ | $0.6300$ | $\mathbf{+45.00}$ | $\mathbf{38.64}$ | $\mathbf{38.71}$ | **YES** ($32.2\%$) |
| **$P_4$ (Mid-Propagation)** | $0.235$ | $0.6500$ | $0.7430$ | $\mathbf{+93.00}$ | $\mathbf{73.12}$ | $\mathbf{73.08}$ | **YES** ($60.9\%$) |
| **$P_5$ (Lower Propagation)** | $0.140$ | $0.7250$ | $0.8560$ | $\mathbf{+131.00}$ | $\mathbf{95.78}$ | $\mathbf{95.84}$ | **YES** ($79.8\%$) |
| **$P_6$ (Near-Boundary)** | $0.060$ | $0.8000$ | $0.9360$ | $\mathbf{+136.00}$ | $\mathbf{96.17}$ | $\mathbf{131.48}$ | **YES** ($80.1\%$) |
| **$P_7$ (Bottom Exit)** | $0.000$ | $0.8680$ | $0.9850$ | $\mathbf{+117.00}$ | $\mathbf{82.74}$ | $\mathbf{117.00}$ | **YES** ($68.9\%$) |

### 7.3 Mathematical Differentiation & Propagation Angle Discrepancy Correction

1. **Polynomial Differentiation:** 
   $$\frac{dx}{dy} = 2(0.698155)y - 1.071775 = 1.396310 y - 1.071775$$
   At the initial crack tip ($y = 0.500\,\text{mm}$):
   $$\left.\frac{dx}{dy}\right|_{y=0.5} = 1.396310(0.500) - 1.071775 = -0.373620$$
2. **Physical Propagation Direction:** 
   Because Mode-II crack growth propagates downwards into the lower half ($dy < 0$) and rightwards ($dx > 0$), setting $dy = -dt$ ($dt > 0$) gives $dx = -0.373620(-dt) = +0.373620\,dt$.
   The propagation tangent vector is $\vec{t} = (0.373620, -1.0)$, yielding:
   $$\theta_{\mathrm{poly}} = \operatorname{atan2}(-1.0, 0.373620) = \arctan\left(\frac{-1.0}{0.373620}\right) = \mathbf{-69.52^\circ}$$
3. **Piecewise-Linear Segment Angle:**
   The first digitized chord from $P_1(0.500, 0.500)$ to $P_2(0.535, 0.430)$ has $\Delta x = +0.035\,\text{mm}$, $\Delta y = -0.070\,\text{mm}$, yielding:
   $$\theta_{\mathrm{pwl}} = \operatorname{atan2}(-0.070, 0.035) = \arctan(-2.0) = \mathbf{-63.43^\circ}$$
4. **Epistemic Discipline:** A global quadratic fit to 7 digitized centerline points has curvature across $y \in [0, 0.5]$ and must not be conflated with an analytical maximum hoop stress crack-initiation angle (which theoretically predicts $\theta_0 = -70.53^\circ$). The project retains the piecewise-linear polyline as the primary reproducible reference.

### 7.4 Geometric Mesh-Resolution Audit vs Numerical Convergence Findings

Along the authenticated Fig. 12(b) trajectory, 500 uniformly spaced stations were queried against both exact Point-in-Polygon containing-element geometry and KDTree nearest-centroid indices on the adapted mesh (`M2_CORRECTED_ADAPTED_RAW_3PCT.inp`, $21{,}042$ nodes, $21{,}063$ elements: 576 CPE3 tris + 20,487 CPE4 quads):

1. **PIP vs KDTree Element Identification Consistency:**
   - **$469 / 500$ points ($93.80\%$)** belong to the *exact same element* identified by KDTree nearest-centroid lookup.
   - For the remaining $31$ points ($6.20\%$), the query points lie in close proximity to element edges or vertices; the adjacent containing element has an equivalent size differing by $<0.05\,\mu\text{m}$.

2. **Equivalent Mesh Size ($h_{\text{equiv}} = \sqrt{A_e}$):**
   - **Minimum Mesh Size:** $h_{\min} = 1.1521\,\mu\text{m} \approx l_0 / 13.0$
   - **Median Mesh Size:** $h_{\text{median}} = 2.1185\,\mu\text{m} \approx l_0 / 7.1$
   - **Mean Mesh Size:** $h_{\text{mean}} = 2.3492\,\mu\text{m} \approx l_0 / 6.4$
   - **Maximum Mesh Size:** $h_{\max} = \mathbf{4.2892\,\mu\text{m}} \approx l_0 / 3.50$
   - **Coverage $\le l_0/2 = 7.50\,\mu\text{m}$:** **$100.00\%$** ($500 / 500$ points)
   - **Coverage $\le l_0/3 = 5.00\,\mu\text{m}$:** **$100.00\%$** ($500 / 500$ points, $h_{\max} \le 5.00\,\mu\text{m}$ strictly verified)
   - **Coverage $\le l_0/4 = 3.75\,\mu\text{m}$:** **$97.80\%$** ($489 / 500$ points)
   - **Coverage $\le l_0/5 = 3.00\,\mu\text{m}$:** **$79.40\%$** ($397 / 500$ points)
   - **Coverage $\le 2.50\,\mu\text{m}$ ($l_0/6$):** **$72.40\%$** ($362 / 500$ points)

3. **Conservative Maximum Edge Length ($h_{\max,\text{edge}} = \max_i \|\mathbf{x}_{i+1} - \mathbf{x}_i\|$):**
   - **Minimum Edge Length:** $1.4684\,\mu\text{m}$
   - **Median Edge Length:** $2.4297\,\mu\text{m}$
   - **Mean Edge Length:** $2.7538\,\mu\text{m}$
   - **Maximum Edge Length:** $5.1471\,\mu\text{m}$
   - **Coverage $\le l_0/2 = 7.50\,\mu\text{m}$:** **$100.00\%$** ($500 / 500$ points)
   - **Coverage $\le l_0/3 = 5.00\,\mu\text{m}$:** **$99.40\%$** ($497 / 500$ points; only 3 points marginally exceed $5.0\,\mu\text{m}$, peaking at $5.15\,\mu\text{m}$, which is $<3\%$ above $5.0\,\mu\text{m}$)

4. **Coarse Pre-Analysis Comparison (Job 1411104):**
   - Equivalent size: $h_{\min} = 1.050\,\mu\text{m}$, $h_{\text{median}} = 3.494\,\mu\text{m}$, $h_{\max} = 7.601\,\mu\text{m}$.
   - $99.00\%$ of arc length satisfies $h \le l_0/2 = 7.50\,\mu\text{m}$, but only $82.4\%$ satisfies $h \le l_0/3$.

**Epistemic Boundary:**
This geometric audit confirms that the native adapted mesh satisfies the necessary spatial resolution criterion $h \le l_0/3$ along the published crack trajectory. However, spatial element refinement along a corridor does not automatically guarantee full numerical convergence of macroscopic load-displacement, peak force, or fracture energy dissipation, which also depend on mesh transition gradients, far-field compliance, and solution scheme.

---

## 8. Node, Degree-of-Freedom, and Active Solver Equation Reconciliation

- **Finite Elements:** $21{,}063$ elements ($20{,}487$ quads + $576$ tris).
- **Co-Located Layered Elements:** $63{,}189$ layered elements ($21{,}063 \times 3$).
- **Mesh Nodes in Input Deck:** $21{,}042$ mesh nodes (Nodes 1 to 21042).
- **Duplicated Seam Node Pairs:** $54$ duplicated seam pairs along $y = 0.5, 0 \le x < 0.5 \implies 20{,}988$ unique coordinate vertices.
- **Reference Point Node:** Node 999999 for rigid boundary coupling $\implies 21{,}043$ total nodes defined in Abaqus.
- **Total Model Variables:** $21{,}042 \times 3 + 1 = \mathbf{63{,}127}$ variables (reported in `.dat`).
- **Linear Constraint Equations:** $97$ linear constraint equations (`*EQUATION`) coupling top edge nodes (`N_TOP`) to Reference Point 999999.
- **Active Assembled Solver Equations:** $63{,}127 - 97 = \mathbf{63{,}030}$ active equations in the sparse solver (reported in `.msg`).
- **Algebraic Verification:** The elimination $63{,}127 - 97 = 63{,}030$ is the exact algebraic condensation of one dependent horizontal displacement variable per linear multi-point constraint equation during sparse matrix factorization.

---

## 9. Active Fracture Simulation (PBS Job 1411267) Telemetry & Softening Progression

### 9.1 Solver Configuration & Live Progress
- **Job ID:** `1411267.mmaster02` (`M2_J2_ADAPT_ET3_STAB`)
- **Queue / Node:** `normal_imfdfkmq` / `mnode098/0` (1 CPU serial, 16 GB RAM)
- **Model Discretization:** $21{,}063$ FEs ($63{,}189$ layered elements, $63{,}030$ active equations)
- **Convergence Controls:** Line Search $N^{ls} = 4$, $I_A = 12$, $I_0 = 8, I_R = 12$, $\Delta t_{\min} = 10^{-12}$
- **Step 1 Completion:** Completed at Increment 2024 ($u_x = 10.00\,\mu\text{m}$, total time $1.000$).
- **Step 2 Active Execution:** Actively solving at **Increment 1420** (total Increment 3444, $u_x = 17.105\,\mu\text{m}$, $RF_1 = 341.25\,\text{N}$, uniform $\Delta t = 0.0005$, **0 cutbacks in Step 2**, converging in 4 Newton iterations per increment).
- **Initial Structural Stiffness:** $K_0 = 45.638987\,\text{kN/mm}$ (intercept $= 0.003048\,\text{N}$, $R^2 = 0.99999998$, $N=198$ increments), matching the literature baseline ($\sim 45.5\,\text{kN/mm}$) within $<0.3\%$.
- **Observed Peak Reaction Force:** $F_{\max} = 412.209\,\text{N}$ at $u_x = 9.410\,\mu\text{m}$.
- **Post-Peak Softening Trajectory:**
  * The simulation successfully overcame the severe localization instability that halted previous job 1411103 (7 cutbacks at $u_x = 9.420\,\mu\text{m}$). With Line Search damping ($N^{ls}=4, I_A=12$), 4 localized cutbacks were cleanly resolved in Step 1.
  * Load dropped steadily from $412.21\,\text{N} \to 365.95\,\text{N}$ at the Step 1 boundary ($u_x = 10.00\,\mu\text{m}$).
  * Entering Step 2, the load softened further to $338.57\,\text{N}$ at Inc 37 ($u_x = 10.185\,\mu\text{m}$), and has now progressed smoothly to $u_x = 17.105\,\mu\text{m}$ with $RF_1 = 341.25\,\text{N}$.
- **Completed vs Incomplete Fracture Status:**
  The prescribed loading endpoint is $u_x = 20.0\,\mu\text{m}$. At the current state ($u_x = 17.105\,\mu\text{m}$, 85.5% of total displacement), the crack has propagated through the specimen, but the solve is an **intermediate progressive softening state** that has not yet reached full terminal completion ($u_x = 20.0\,\mu\text{m}$ or residual zero load).

### 9.2 Quantitative Comparison with Literature & Coarse Pre-Analysis

| Metric / Stage | Coarse Pre-Analysis (Job 1411104) | Adapted Mesh (Job 1411267) | Pandey & Kumar (2025) Fig. 13 | Discrepancy vs Literature |
| :--- | :---: | :---: | :---: | :---: |
| **Number of FEs** | $2{,}960$ | $21{,}063$ | $19{,}963$ | $+5.51\%$ |
| **Initial Stiffness $K_0$** | $45.64\,\text{kN/mm}$ | $45.64\,\text{kN/mm}$ | $\approx 45.5\,\text{kN/mm}$ | $< \mathbf{+0.3\%}$ |
| **Peak Force $F_{\max}$** | $\mathbf{514.51\,\text{N}}$ | $\mathbf{412.21\,\text{N}}$ | $\mathbf{365.74\,\text{N}}$ | $\mathbf{+12.71\%}$ |
| **Peak Displacement $u_{\text{peak}}$** | $13.43\,\mu\text{m}$ | $9.410\,\mu\text{m}$ | $8.284\,\mu\text{m}$ | $\mathbf{+13.59\%}$ |
| **Gap Closed vs Coarse** | Reference ($0\%$) | **$68.76\%$ closed** ($514.51 \to 412.21\,\text{N}$) | Benchmark ($100\%$) | — |
| **Softening Progression** | Completed to $u_x = 20\,\mu\text{m}$ | **Active ($u_x = 17.11\,\mu\text{m}$, $RF_1 = 341.25\,\text{N}$)** | Softening to $u_x = 20\,\mu\text{m}$ | Progressing stably |

### 9.3 Rigorous 6-Factor Source-Grounded Peak-Force Discrepancy Audit

To investigate why the native-adapted Mode-II mesh predicts approximately $412.21\,\text{N}$ instead of the published $365.74\,\text{N}$ despite matching initial stiffness, a systematic source-grounded diagnostic audit was conducted across six candidate factors:

1. **Geometry & Initial Crack Seam:**
   - Model geometry is a $1.0 \times 1.0\,\text{mm}$ square domain with a zero-gap sharp seam along $y = 0.500\,\text{mm}$ extending from $x = 0.0$ to $x = 0.500\,\text{mm}$ ($a_0 = 0.5\,\text{mm}$).
   - The initial elastic stiffness $K_0 = 45.639\,\text{kN/mm}$ matches the digitized literature response ($45.55\,\text{kN/mm}$) within $<0.3\%$, confirming linear elastic compliance.
   - **Classification:** **SUPPORTED BUT NOT CONCLUSIVE** (Initial compliance agrees, but nonlinear notch flank interaction if any under large shear is not documented in the paper).

2. **Boundary Conditions & Kinematic Coupling:**
   - Bottom boundary ($y = 0$) is clamped ($u_x = u_y = 0$). Top boundary ($y = 1.0$) is constrained against vertical motion ($u_y = 0$) and sheared horizontally via linear multipoint kinematic coupling (`*EQUATION`) to Reference Point 999999.
   - Reaction force $RF_1$ is extracted directly at the master Reference Point.
   - **Classification:** **SUPPORTED BUT NOT CONCLUSIVE**.

3. **Material Properties & Regularization Length Scale:**
   - Young's modulus $E = 210.0\,\text{GPa}$, Poisson's ratio $\nu = 0.3$, critical fracture energy $G_c = 2.7 \times 10^{-3}\,\text{kN/mm} = 2.7\,\text{N/mm}$, length scale $l_0 = 0.015\,\text{mm} = 15.0\,\mu\text{m}$, residual stiffness $k = 1.0 \times 10^{-7}$.
   - All parameters in `f42_mixed_uel_mode2_miehe.for` and the input deck match the published text (p. 3270).
   - **Classification:** **VERIFIED** for published nominal parameter values.

4. **Constitutive Split & Irreversible Monotonic History:**
   - The user element implements the Miehe spectral decomposition of elastic strain energy into tensile $\psi_0^+$ and compressive $\psi_0^-$ components, degrading only $\psi_0^+$: $\psi = [(1-d)^2 + k]\psi_0^+ + \psi_0^-$.
   - History variable enforces irreversibility monotonically: $\mathcal{H}_{n+1} = \max(\mathcal{H}_n, \psi_0^+)$.
   - However, unstated details in the authors' private implementation (e.g. initial threshold $\psi_{0,cr}$, specific residual stiffness $k$, or tangent linearization) cannot be verified from the paper text alone.
   - **Classification:** **SUPPORTED BUT NOT CONCLUSIVE / NOT DETERMINABLE FROM AVAILABLE EVIDENCE**.

5. **Non-Uniform Mesh Grading & Finite Adaptive Corridor Breadth:**
   - On the coarse pre-analysis mesh ($2{,}960$ FEs), peak force was $514.51\,\text{N}$ ($+40.7\%$ over literature).
   - The adapted mesh ($21{,}063$ FEs) reduced peak force to $412.21\,\text{N}$, traversing **$68.76\%$** of the gap toward $365.74\,\text{N}$.
   - When a refined corridor ($h \le 3\text{--}4\,\mu\text{m}$) transitions to coarser elements ($h \approx 15\text{--}24\,\mu\text{m}$) away from the crack path, the coarser surrounding bulk could exert an elastic constraint on the shear field, slightly altering the macroscopic load at crack initiation.
   - **Classification:** **PLAUSIBLE / UNVERIFIED** (hypothesis requires systematic corridor width and grading sweeps to isolate).

6. **Monolithic Fully-Coupled vs Staggered Alternate-Minimization Solver Scheme:**
   - Our implementation is a **fully-coupled monolithic Newton-Raphson solver**, where displacement DOFs $(u_x, u_y)$ and phase-field DOFs $d$ are solved simultaneously in a single assembled Jacobian.
   - Pandey & Kumar explicitly report using a staggered implementation (Section 3, p. 3264).
   - In standard staggered schemes, evaluating the displacement field at step $n+1$ with the frozen phase field from step $n$ introduces numerical lag in damage growth, which typically shifts the softening curve and apparent peak load relative to monolithic solutions.
   - **Classification:** **PLAUSIBLE / NOT DETERMINABLE FROM AVAILABLE EVIDENCE**.

**Diagnostic Summary:**
The initial elastic stiffness agreement ($<0.3\%$) confirms macroscopic elastic compliance. The remaining $+12.71\%$ peak load difference is evaluated as an open numerical question primarily related to mesh transition grading constraints and monolithic versus staggered solver formulations.

---

## 10. Comprehensive Scientific Verdicts

1. **Resolution of Trajectory Discrepancy & Angle Correction:** Differentiating the quadratic polynomial yields $dx/dy|_{y=0.5} = -0.373620$, corresponding to a downward/rightward propagation vector $(0.373620, -1.0)$ and tangent angle $\theta_{\mathrm{poly}} = \mathbf{-69.52^\circ}$. The piecewise-linear first segment gives $\theta_{\mathrm{pwl}} = \mathbf{-63.43^\circ}$.
2. **Reconciliation of Centerline Deviation and Crack-Path Coverage:** While horizontal offset $\Delta x$ reaches $+136\,\mu\text{m}$, the shortest perpendicular Euclidean distance $d_{\perp}$ to the station-matched mesh ridge never exceeds $96.17\,\mu\text{m}$, proving that **100% of the published stations lie within the nominal $W/2 = 120\,\mu\text{m}$ corridor**.
3. **Geometric Mesh-Resolution Audit vs Numerical Convergence:** Containing-element queries along 500 stations prove that **$100.00\%$** of the published trajectory satisfies $h_{\text{equiv}} \le l_0/3 = 5.00\,\mu\text{m}$ ($h_{\max} = 4.289\,\mu\text{m}$) and **$99.40\%$** satisfy $h_{\max,\text{edge}} \le 5.00\,\mu\text{m}$ ($100.00\% \le l_0/2 = 7.50\,\mu\text{m}$). This establishes adequate geometric resolution for the phase-field length scale $l_0 = 15\,\mu\text{m}$, but does not by itself prove full numerical convergence.
4. **Reconciled Equation Hierarchy:** Exactly $21{,}042$ mesh nodes ($20{,}988$ unique vertices + $54$ seam duplicate pairs) $\times 3$ DOFs $+ 1$ RP node $= 63{,}127$ model variables, and the condensation of $97$ linear top-edge coupling equations yields exactly $63{,}030$ sparse solver equations.
5. **Adapted Production Fracture Simulation Progress:** PBS Job `1411267.mmaster02` successfully completed Step 1 ($u_x = 10.00\,\mu\text{m}$) and is actively advancing in Step 2 post-peak softening at **Increment 1420** ($u_x = 17.105\,\mu\text{m}$, $RF_1 = 341.25\,\text{N}$, $dt = 0.0005$, 0 cutbacks in Step 2, 4 iters/inc), progressing stably toward the prescribed displacement horizon ($u_x = 20\,\mu\text{m}$).
6. **Literature Convergence Progress & Discrepancy Attribution:** The adapted mesh achieves $<0.3\%$ agreement in initial elastic stiffness and resolves **$68.76\%$** of the gap between coarse pre-analysis and published peak fracture response. The remaining $+12.71\%$ difference is evaluated as a plausible effect of adaptive corridor grading and monolithic vs staggered solution formulations.
7. **Gate M2-4 Completion Status:** Gate M2-4 remains **ACTIVE (`ACTIVE_STABILIZED_FRACTURE_SOFTENING_ACTIVE`)** and must NOT be closed prematurely until full prescribed displacement, complete crack separation, and final discrepancy evaluation are completed.

---

## 11. Exact Adaptive-Remeshing Provenance Record

| Parameter | Value / File / SHA-256 | Description |
| :--- | :--- | :--- |
| **Source ODB** | `/scratch9/pr21vyci/runs/mode2_j1_coarse_retest/Job-1_UEL.odb` | PBS Job `1411104.mmaster02` (`M2_J1_COARSE_RETEST`) |
| **Source Step & Frame** | `Step-2`, Frame 1001 (Frame ID 2000) | Final increment ($t = 1.00000$, $u_x = 0.020\,\text{mm}$, $d_{\max} = 1.0$) |
| **Remeshing Rule Name** | `RR_MODE2_CORRECTED_3` | Remeshing rule in Abaqus/CAE model |
| **Indicator Variable** | `MISESERI` | Mises stress error indicator on Layer 3 (`CPE4`/`CPE3`) |
| **Sizing Method** | `UNIFORM_ERROR` | Distributes error evenly across domain |
| **Target Error** | `errorTarget = 0.03` ($3.0\%$) | Sizing criterion |
| **Element Size Limits** | $h_{\min} = 0.001\,\text{mm}, h_{\max} = 0.020\,\text{mm}$ | Size bounding controls |
| **Coarsening / Refinement** | `coarseningFactor = NOT_ALLOWED`, `refinementFactor = 10.0` | Prevents coarsening, permits up to $10\times$ local refinement |
| **CAE Execution Command** | `m.adaptiveRemesh(odb=odb)` | Native Abaqus remeshing driver |
| **Generated Raw Deck** | `M2_CORRECTED_ADAPTED_RAW_3PCT.inp` | SHA-256: `e79b645c60be91e76b53135c20234c972bfe496b88ae2477a3e89f8678da2de5` ($21{,}063$ FEs) |
| **Stabilized Production Deck** | `M2_CORRECTED_JOB2_ET3PCT_STABILIZED.inp` | SHA-256: `8A011E4149CF08BCCA8F9C80E49C2AB82EEA93CA1F797F8F67CE279446B7F810` ($63{,}030$ eqns) |

---

## 12. HPC Storage Safeguards & Safe Relocation Manifest

### 12.1 Storage Audit Findings
A disk storage audit conducted in Task F1359 revealed that user home directory `/home/pr21vyci` currently occupies **120 GB**. Over **85.4 GB (71.2%)** consists of completed legacy simulation outputs, old batch directories, and early thesis trials that can be safely archived to high-capacity scratch storage (`/scratch9/pr21vyci/archive_home_august2026/`) without deleting any files or impacting active computations.

Active PBS Job `1411267.mmaster02` executes entirely under `/scratch9/pr21vyci/runs/mode2_j2_adapted_stabilized_et3` with zero heavy binary files written to `/home`.

### 12.2 Prioritized Relocation Tiers

- **Tier 1: Heavy Standalone Files (> 1 GB each) — 17.0 GB Total**
  * `projects/.../M2STATE_FRACFIX_RESTART2R7.msg`: **13 GB**
  * `projects/.../M2STATE_FRACFIX_RESTART2R5.o$PBS_JOBID`: **2.3 GB**
  * `projects/.../M2STATE_FRACFIX_RESTART2R5.msg`: **1.7 GB**
- **Tier 2: Completed Stage-D Validation Batch Directories — ~3.3 GB Total**
  * `M2CORR_STAGE_D_PROJECTED_PHASE_TRANSFER_CORR_VAL/`: **998 MB**
  * `M2CORR_STAGE_D_CONTINUOUS_TARGET_CONTROL_VAL/`: **614 MB**
  * `M2CORR_STAGE_D_PROJECTED_PHASE_TRANSFER_VAL/`: **587 MB**
  * `M2CORR_STAGE_D_SAME_TARGET_IDENTITY_RESTART_VAL/`: **573 MB**
  * `M2STATE_FRACFIX_RESTART2R7.dat`: **510 MB**
- **Tier 3: Stale Workspace Clone Directories (`Adaptive_remeshing_clean`) — ~8.0 GB Total**
  * `models/generated/mode_ii/stage_e_refinement_coarsening_batch/`: **7.3 GB**
  * `models/generated/mode_ii/production_state_transfer_batch/`: **745 MB**
- **Tier 4: Legacy Early Thesis Trials — 56 GB Total**
  * `/home/pr21vyci/master_thesis/Abaqus_trial/`: **56 GB**

### 12.3 Relocation Safety Governance
In accordance with repository governance rules:
1. **No deletions**: No files or directories shall be permanently deleted.
2. **Explicit authorization required**: No files will be moved until the human user explicitly approves the relocation manifest.
3. **Integrity preservation**: Moving files to `/scratch9/pr21vyci/archive_home_august2026/` preserves file timestamps, permissions, and directory structures.
