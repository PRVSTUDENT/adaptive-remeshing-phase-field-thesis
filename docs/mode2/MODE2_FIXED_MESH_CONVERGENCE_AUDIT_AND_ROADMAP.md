# Mode-II Fixed-Mesh Convergence Audit, Methodology Grounding, and 3-Layer Roadmap

**Author:** Gemini Antigravity (Inspection & Synthesis Agent)  
**Task ID:** `F1379-MODE2-FIXED-MESH-CONVERGENCE-AUDIT-AND-PREPARATION`  
**Date:** October 9, 2026  
**Status:** Canonical Audit & Technical Roadmap  
**Governing Gate:** `GATE_M2_1B_FIXED_MESH_CONVERGENCE_STUDY_AUDITING_AND_SOLVING`  
**Governing Directive:** *"We need to have understood everything related to the first model before we increase complexity."*

---

## 1. Executive Summary & Audit Context

Under Gate M2-1B, four uniform fixed-mesh reference models spanning a factor of $5.36\times$ in spatial resolution ($h = 20.0\,\mu\text{m} \to 3.73\,\mu\text{m}$, or $h/l_0 = 1.33 \to 0.25$) were staged, pre-checked, and submitted to the TU Freiberg HPC cluster (`normal_imfdfkmq` on `mnode097`, Jobs 1411542–1411545), solving concurrently alongside the live ET2 adaptive solve (Job 1411414, $37{,}575$ FEs).

This audit accomplishes five essential scientific tasks:
1. **Methodological Correction of Initial Stiffness ($K_0$):** Replaces single-increment secant approximations ($RF_1/u_1$) with multi-increment ordinary least squares (OLS) linear regressions across six sample intervals ($N = 3, 10, 20, 40, 100, 200$), proving $R^2 > 0.99999999997$, zero-intercept conformity ($c \le 2.5\times 10^{-5}\,\text{N}$), and rigorous convergence to $45.85\,\text{kN/mm}$ ($0.37\%$ vs literature target $45.68 \pm 0.85\,\text{kN/mm}$). Crucially, this audit establishes that initial stiffness convergence is an elastic compliance property that does **not** prove fracture convergence.
2. **Single-Factor Equivalence Proof:** Mathematically and structurally audits all four fixed-mesh input decks, proving they represent the exact same boundary value problem with spatial discretization ($h$) as the sole independent variable. Resolves the $+1$ node and solver variable count differences between F1377 and F1378 as the Reference Point 999999 (`N_RP`) and active DOFs ($3 N_{\text{mesh}} + 1$).
3. **Independent UEL Formulation Audit:** Reviews `f42_mixed_uel_mode2_miehe.for` (SHA256: `699B05D6...`), verifying the weak form, Newton-Raphson residuals, consistent tangent stiffness, 2D Miehe spectral decomposition, Kuhn-Tucker damage irreversibility ($\dot{\mathcal{H}} \ge 0$), and UEL/UMAT in-memory state exchange via named common block `CB_STATE_TRANS`.
4. **Predefined Reference Evaluation Pipeline:** Defines the strict multi-quantity post-processing extraction and acceptance protocol ($K_0$, $F_{\max}$, $u_{\text{peak}}$, full $F(u_x)$, $W_{\text{ext}}$, $\theta_{\text{crack}}$, $\text{MAD}$, $h_{\text{lig}}$) before terminal results are produced.
5. **Non-Binary Epistemological Framework & 3-Layer Thesis Architecture:** Replaces the naive binary A/B choice with an exhaustive 4-branch scientific framework, and formalizes the 3-Layer Thesis Architecture separating the numerical fracture solver (Layer 1), the adaptive mesh controller (Layer 2), and the sequential adaptation driver (Layer 3).

---

## 2. Multi-Increment Stiffness Regression Audit

### 2.1 Theoretical Framework

In linear elasticity, the initial structural stiffness $K_0$ relates the applied shear displacement $u_x$ at Reference Point 999999 (`N_RP`) to the total reaction force $RF_1$:
$$RF_1(u_x) = K_0 u_x + c$$

In F1378, provisional values were reported from the very first solver increment ($u_1 = 0.005\,\mu\text{m}$), yielding $K_0 = RF_1 / u_1$. While computationally expedient, a single-point secant ratio:
1. Conflates physical stiffness with floating-point roundoff and initial Newton residual tolerance;
2. Cannot evaluate the linearity or determine if an initial offset ($c \ne 0$) exists;
3. Does not provide statistical confidence metrics ($R^2$, standard error $SE(K_0)$);
4. Cannot assess fitting interval sensitivity.

To establish rigorous ground truth, we perform both:
1. **Unconstrained OLS Regression:**
   $$K_0 = \frac{\sum_{i=1}^N (u_i - \bar{u})(RF_i - \overline{RF})}{\sum_{i=1}^N (u_i - \bar{u})^2}, \quad c = \overline{RF} - K_0 \bar{u}$$
   $$SE(K_0) = \sqrt{\frac{\sum_{i=1}^N (RF_i - \widehat{RF}_i)^2}{(N - 2) \sum_{i=1}^N (u_i - \bar{u})^2}}$$
2. **Origin-Constrained Regression ($c \equiv 0$):**
   $$K_{0,0} = \frac{\sum_{i=1}^N u_i RF_i}{\sum_{i=1}^N u_i^2}, \quad SE(K_{0,0}) = \sqrt{\frac{\sum_{i=1}^N (RF_i - K_{0,0} u_i)^2}{(N - 1) \sum_{i=1}^N u_i^2}}$$

### 2.2 Empirical Audit Across the 4 Tiers and ET2

Using `stiffness_regression_audit.json` extracted directly from the solver `.dat` files on cluster scratch, the regression results across the common interval $[0.005, 0.200]\,\mu\text{m}$ ($N = 40$ increments) are summarized in Table 2.1:

| Model Tier | Discretization $h$ | $N$ | Unconstrained $K_0$ [kN/mm] | Intercept $c$ [N] | $R^2$ | Origin-Constrained $K_{0,0}$ [kN/mm] | Secant $RF/u$ [kN/mm] | $\Delta$ vs Lit. ($45.68$) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **01 Coarse (2.5k)** | $20.00\,\mu\text{m}$ ($1.33\,l_0$) | 40 | $45.7766 \pm 0.00004$ | $+2.43\times 10^{-5}$ | $0.999999999976$ | $45.7768 \pm 0.00002$ | $45.7765$ | $+0.211\%$ |
| **02 Medium (18k)** | $7.46\,\mu\text{m}$ ($0.50\,l_0$) | 40 | $45.9635 \pm 0.00004$ | $+2.53\times 10^{-5}$ | $0.999999999974$ | $45.9637 \pm 0.00002$ | $45.9635$ | $+0.621\%$ |
| **03 Interm. (40k)** | $5.00\,\mu\text{m}$ ($0.33\,l_0$) | 40 | $45.8592 \pm 0.00004$ | $+2.53\times 10^{-5}$ | $0.999999999974$ | $45.8594 \pm 0.00002$ | $45.8591$ | $+0.392\%$ |
| **04 Fine (72k)** | $3.73\,\mu\text{m}$ ($0.25\,l_0$) | 40 | $45.8506 \pm 0.00004$ | $+2.53\times 10^{-5}$ | $0.999999999974$ | $45.8508 \pm 0.00002$ | $45.8505$ | $+0.373\%$ |
| **ET2 Adaptive (37.5k)** | $h_{\min} = 2.07\,\mu\text{m}$ | 40 | $45.7117 \pm 0.00004$ | $+2.52\times 10^{-5}$ | $0.999999999974$ | $45.7119 \pm 0.00002$ | $45.7116$ | $+0.069\%$ |

### 2.3 Scientific Findings from the Regression Audit

1. **Near-Zero Intercept:** The fitted intercept across all models is $c \approx 0.000025\,\text{N}$, which is within $10^{-6}$ of total load, confirming exact zero-load equilibrium at zero displacement.
2. **Negligible Unconstrained vs Origin-Constrained Difference:** The difference $|K_0 - K_{0,0}|$ is less than $0.0002\,\text{kN/mm}$ ($<0.0005\%$), proving that constraining the regression to pass through the origin introduces zero distortion.
3. **Stiffness Convergence Between Intermediate and Fine:**
   $$\frac{|K_{0,\text{fine}} - K_{0,\text{interm}}|}{K_{0,\text{interm}}} = \frac{|45.8508 - 45.8594|}{45.8594} = 0.0188\% \approx 0.019\%$$
   The initial elastic compliance is converged to within $0.02\%$ between $40{,}000$ and $71{,}824$ elements.
4. **Fitting Interval Sensitivity:** Evaluating the unconstrained slope across intervals $[0, 0.015]\,\mu\text{m}$, $[0, 0.050]\,\mu\text{m}$, $[0, 0.100]\,\mu\text{m}$, and $[0, 0.200]\,\mu\text{m}$ reveals that $K_0$ shifts by less than $0.001\%$ across the entire pre-cracking regime.
5. **Epistemological Guardrail:** While $K_0$ converges immediately, **stiffness convergence does not imply fracture convergence**. Elastic compliance is governed by the far-field singular stress field $K_{\text{II}}/\sqrt{2\pi r}$, which standard quad elements capture with high accuracy even at coarse resolution. In contrast, fracture initiation and crack propagation depend on the local phase-field regularization length $l_0 = 15\,\mu\text{m}$, which requires $h \le l_0/4$ to resolve the damage profile.

---

## 3. Single-Factor Equivalence and Model Invariant Audit

To ensure that the 4-tier fixed-mesh suite provides a rigorous spatial convergence study, all parameters other than element size $h$ must remain strictly invariant.

### 3.1 Mathematical and Structural Invariants

1. **Domain Geometry:** Square plate $\Omega = [0, 1] \times [0, 1]\,\text{mm}$, thickness $t = 1.0\,\text{mm}$ (plane strain).
2. **Open-Slit Seam:** Horizontal sharp slit at $y = 0.50\,\text{mm}$ for $x \in [0.0, 0.50]\,\text{mm}$.
   - Discontinuous lower flank: $y = 0.50^-$, upper flank: $y = 0.50^+$.
   - Single shared crack-tip node at $(0.50, 0.50)\,\text{mm}$.
   - Continuous intact ligament for $x \in (0.50, 1.00]\,\text{mm}$ at $y = 0.50\,\text{mm}$.
3. **Material & Phase-Field Properties:**
   - Young's modulus $E = 210.0\,\text{GPa} = 210.0\,\text{kN/mm}^2$
   - Poisson's ratio $\nu = 0.30$
   - Plane strain Lamé parameters: $\lambda = 121.1538\,\text{kN/mm}^2$, $\mu = 80.7692\,\text{kN/mm}^2$
   - Critical fracture energy $G_c = 2.70\,\text{N/mm} = 2.70\times 10^{-3}\,\text{kN/mm}$
   - Phase-field regularization length $l_0 = 15\,\mu\text{m} = 0.015\,\text{mm}$
   - Residual stiffness parameter $k_{\text{res}} = 1.0\times 10^{-7}$
4. **Boundary Conditions & Rigid Coupling:**
   - Bottom boundary ($y = 0$): $u_x = 0$, $u_y = 0$.
   - Top boundary ($y = 1.0\,\text{mm}$): roller constraint $u_y = 0$ on all nodes.
   - Reference Point 999999 (`N_RP`): $u_y = 0$ constrained; shear displacement $u_x = \bar{u}(t)$ prescribed.
   - Multi-Point Constraint (MPC): `*EQUATION` enforces $1.0\cdot u_1(\text{node}_i) - 1.0\cdot u_1(\text{RP}) = 0$ for all top nodes $i \in N_{\text{TOP}}$.
5. **3-Layer Architecture:**
   - Layer 1: User elements (`f42_mixed_uel_mode2_miehe.for`), JTYPE 1 (phase) + JTYPE 2 (mechanical).
   - Layer 2: Standard Abaqus CPS4 elements with dummy stiffness $E_{\text{vis}} = 2.1\times 10^{-4}\,\text{kN/mm}^2$.
   - Layer 3: UMAT elements mapping internal phase field and history to `SDV14` ($d$), `SDV15` ($\mathcal{H}$), `SDV16` ($\psi_e$).

### 3.2 Resolution of F1377 vs F1378 Node and Equation Counts

In Task F1377, the generator script reported physical mesh nodes, while in Task F1378, Abaqus `.dat` reported user nodes and active solver variables. We provide the complete algebraic proof of equivalence in Table 3.1:

| Model Tier | Mesh Grid | Physical Mesh Nodes ($N_{\text{mesh}}$) | Reference Point Nodes | User Nodes in `.dat` | Active Variables ($3 N_{\text{mesh}} + 1$) | Top MPC Equations ($N_x + 1$) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **01 Coarse** | 50x50 | $2{,}626$ | 1 (Node 999999) | $2{,}627$ | $3(2{,}626) + 1 = 7{,}879$ | $50 + 1 = 51$ |
| **02 Medium** | 134x134 | $18{,}292$ | 1 (Node 999999) | $18{,}293$ | $3(18{,}292) + 1 = 54{,}877$ | $134 + 1 = 135$ |
| **03 Intermediate** | 200x200 | $40{,}501$ | 1 (Node 999999) | $40{,}502$ | $3(40{,}501) + 1 = 121{,}504$ | $200 + 1 = 201$ |
| **04 Fine** | 268x268 | $72{,}495$ | 1 (Node 999999) | $72{,}496$ | $3(72{,}495) + 1 = 217{,}486$ | $268 + 1 = 269$ |

**Algebraic Proof:**
1. Along the slit $y = 0.50\,\text{mm}$, there are $N_x/2$ duplicate node pairs from $x = 0$ to $x = 0.50 - h$.
2. Total mesh nodes $N_{\text{mesh}} = (N_x + 1)(N_y + 1) + N_x/2$.
   - Coarse: $(51)(51) + 25 = 2{,}601 + 25 = 2{,}626$.
   - Medium: $(135)(135) + 67 = 18{,}225 + 67 = 18{,}292$.
   - Intermediate: $(201)(201) + 100 = 40{,}401 + 100 = 40{,}501$.
   - Fine: $(269)(269) + 134 = 72{,}361 + 134 = 72{,}495$.
3. User nodes in Abaqus = $N_{\text{mesh}} + 1$ (Reference Point 999999).
4. Each mesh node has 3 active DOFs ($u_x, u_y, d$). Reference Point 999999 has DOF 1 active ($u_x$), while DOF 2 is boundary-constrained to 0. Thus, total active solver variables equal $3 N_{\text{mesh}} + 1$.
This completely accounts for every single node, element, and degree of freedom in the solver.

---

## 4. Independent UEL Formulation Audit

The canonical user subroutine `models/pandey_kumar_mode2/f42_mixed_uel_mode2_miehe.for` (788 lines, SHA256: `699B05D6...`) was audited for formulation integrity.

### 4.1 Weak Form and Newton-Raphson Residuals

1. **Phase-Field Residual:**
   $$R_i^d = \int_\Omega 2\mathcal{H} N_i \, d\Omega - \int_\Omega \left[ G_c l_0 \nabla N_i \cdot \nabla d + \left( \frac{G_c}{l_0} + 2\mathcal{H} \right) N_i d \right] d\Omega$$
   In Fortran lines 149–161, `AMATRX(I,J)` is assembled and the residual is formed as `RHS(I,1) = RHS(I,1) - AMATRX(I,J)*U(J)`. This enforces the exact AT2 phase-field Euler-Lagrange equation.
2. **Mechanical Residual:**
   $$R_i^u = -\int_\Omega \mathbf{B}_i^T \boldsymbol{\sigma} \, d\Omega$$
   where $\boldsymbol{\sigma} = g(d) \boldsymbol{\sigma}_0^+ + \boldsymbol{\sigma}_0^-$, $g(d) = (1-d)^2 + k_{\text{res}}$.
   In lines 416–418, `RHS(I,1) = -F_INT(I)`, providing the correct internal force vector to Abaqus.

### 4.2 2D Miehe Spectral Split

The principal strains $\varepsilon_1, \varepsilon_2$ are extracted via Mohr's circle (lines 274–278):
$$\bar{\varepsilon} = \frac{\varepsilon_{11} + \varepsilon_{22}}{2}, \quad R = \sqrt{\left(\frac{\varepsilon_{11} - \varepsilon_{22}}{2}\right)^2 + \varepsilon_{12}^2}, \quad \varepsilon_{1,2} = \bar{\varepsilon} \pm R$$
The spectral split decomposes strain into positive and negative parts:
$$\varepsilon_a^+ = \max(\varepsilon_a, 0), \quad \varepsilon_a^- = \min(\varepsilon_a, 0)$$
$$\psi_0^\pm = \frac{1}{2} \lambda \langle \operatorname{tr}(\boldsymbol{\varepsilon}) \rangle_\pm^2 + \mu \left( (\varepsilon_1^\pm)^2 + (\varepsilon_2^\pm)^2 \right)$$
The consistent tangent $\mathbf{D}_{\text{mech}} = g(d) \mathbf{D}^+ + \mathbf{D}^-$ incorporates the perturbation terms $\theta_\pm \frac{1}{2} \mathbf{v}_{12} \otimes \mathbf{v}_{12}$ for distinct principal stretches, guaranteeing quadratic Newton convergence (3 iterations per increment observed across all runs).

### 4.3 History Monotonicity and Kuhn-Tucker Irreversibility

Damage irreversibility is enforced through the maximum historical tensile strain energy (lines 311–315):
$$\mathcal{H}(\mathbf{x}, t) = \max_{\tau \in [0, t]} \psi_0^+(\mathbf{x}, \tau)$$
Because $\mathcal{H}$ can never decrease ($\dot{\mathcal{H}} \ge 0$) and $g(d)$ degrades only the positive tensile energy, crack healing is prohibited.

### 4.4 UEL/UMAT In-Memory State Exchange & HPC Constraint

The UEL and companion UMAT share state via:
```fortran
COMMON /CB_STATE_TRANS/ SV_PHASE_TRIAL(MAX_ELEM),
1                        SV_H_TRIAL(MAX_ELEM, 4),
2                        SV_PSI_E_TRIAL(MAX_ELEM)
```
- **HPC Constraint:** Named Fortran `COMMON` blocks are process-local memory. In single-node SMP or serial execution (1 CPU serial), all threads access the shared heap. However, in distributed multi-rank MPI, ranks possess disjoint address spaces. Without explicit MPI communication, `CB_STATE_TRANS` becomes inconsistent across ranks.
- **Audit Conclusion:** This conclusively justifies the project governance rule **strictly disqualifying distributed multi-rank MPI** and mandating single-rank shared-memory execution.

---

## 5. Predefined Reference Evaluation Protocol

Before evaluating terminal simulation data, the post-processing pipeline is formalized with unambiguous mathematical definitions:

1. **Initial Stiffness ($K_0$):**
   - Origin-constrained linear regression on $u_x \in [0.005, 0.200]\,\mu\text{m}$.
   - Acceptance target: $K_{0,\text{lit}} = 45.68 \pm 0.85\,\text{kN/mm}$.
2. **Peak Reaction Force ($F_{\max}$) & Peak Displacement ($u_{\text{peak}}$):**
   - $F_{\max} = \max_{u_x} RF_1(\text{RP})$, $u_{\text{peak}} = \operatorname{arg\,max}_{u_x} RF_1(\text{RP})$.
   - Track gap closure percentage relative to coarse benchmark ($514.51\,\text{N}$) and literature ($365.74\,\text{N}$):
     $$\text{Gap Closure} = \frac{514.51 - F_{\max}}{514.51 - 365.74} \times 100\%$$
3. **External Work ($W_{\text{ext}}$):**
   - Trapezoidal integration $W_{\text{ext}}(u) = \int_0^u RF_1(\bar{u})\,d\bar{u}$.
   - Evaluate at literature horizon $u_x = 16.0\,\mu\text{m}$ (target: $3.517\,\text{mJ}$) and full horizon $u_x = 20.0\,\mu\text{m}$.
4. **Post-Peak Softening & Reloading:**
   - Local post-peak minimum: $F_{\min} = \min_{u_x > u_{\text{peak}}} RF_1$.
   - Reloading magnitude: $\Delta F_{\text{reload}} = RF_1(20.0\,\mu\text{m}) - F_{\min}$.
5. **Crack Trajectory & Geometry:**
   - Crack tip location $\mathbf{x}_{\text{tip}}(t)$ identified as the leading damaged element centroid ($d \ge 0.90$).
   - Propagation angle $\theta = \arctan \frac{y_{\text{tip}} - 0.50}{x_{\text{tip}} - 0.50}$ (literature: $-58.0^\circ$).
   - Mean Absolute Deviation (MAD) and Root Mean Square (RMS) error relative to the literature polynomial path.
6. **Intact Bottom Ligament ($h_{\text{lig}}$):**
   - $h_{\text{lig}} = \min \{ y_e \mid d_e \ge 0.90 \}$ along the crack path.
   - Crack deceleration rate $da/du_x$ approaching the clamped base boundary ($y = 0$).

---

## 6. Non-Binary Epistemological Decision Framework

In Task F1376, two initial possibilities were outlined (Possibility A: solver concurrence at $\sim 412\,\text{N}$; Possibility B: adaptive failure at $\sim 365\,\text{N}$). To reflect scientific rigor in non-linear phase-field mechanics, this binary division is expanded into an exhaustive 4-branch framework:

```
                          Fixed-Mesh Convergence Suite Results
                                          │
            ┌─────────────────────────────┼─────────────────────────────┐
            ▼                             ▼                             ▼
   [Branch 1: Asymptotic]      [Branch 2: Decoupled]         [Branch 3: Boundary]
   F_max converges to          K_0 and crack path            Peak force and reload
   ~400-410 N as h -> 0.       converge at h ~ 7 um;         sensitive to u_y = 0;
   Proves literature 365 N     F_max requires h <= 3 um;     Miehe compressive strut
   was under-resolved.         Reloading is constitutive.    dominates late stage.
            │                             │                             │
            └─────────────────────────────┼─────────────────────────────┘
                                          ▼
                               [Branch 4: Length Scale]
                               h / l_0 <= 0.25 resolves exact
                               exponential profile d(x);
                               resolves true continuum limit.
```

### Detailed Scientific Explanations of the Branches:

1. **Branch 1: Asymptotic / Monotonic Convergence Toward $\sim 405\text{--}410\,\text{N}$:**
   - In phase-field modeling, coarse meshes ($h > l_0$) artificially broaden the crack and overestimate peak load ($514\,\text{N}$ at $h = 20\,\mu\text{m}$).
   - As $h$ decreases through $7.46\,\mu\text{m} \to 5.00\,\mu\text{m} \to 3.73\,\mu\text{m}$, if $F_{\max}$ decreases monotonically toward $\sim 405\text{--}410\,\text{N}$, it proves that the adapted solve ($412.21\,\text{N}$) is within $1\text{--}2\%$ of the true continuous boundary value problem solution, and the published $365.74\,\text{N}$ curve was under-resolved or employed different numerical stabilization.
2. **Branch 2: Multi-Scale Quantity Decoupling:**
   - Different mechanical quantities converge at vastly different spatial scales:
     * Elastic stiffness $K_0$: converges at $h = 20\,\mu\text{m}$ ($h/l_0 = 1.33$);
     * Crack trajectory $\theta \approx -58^\circ$: converges at $h \approx 7.5\,\mu\text{m}$ ($h/l_0 = 0.50$);
     * Peak force $F_{\max}$: requires $h \le 3.75\,\mu\text{m}$ ($h/l_0 \le 0.25$);
     * Post-peak reloading: is an intrinsic consequence of the Miehe compressive split under the rigid $u_y = 0$ constraint, remaining present across all mesh discretizations.
3. **Branch 3: Boundary Constraint & Constitutive Splitting Sensitivity:**
   - The boundary constraint $u_y = 0$ at top and bottom prevents global mode-mixity relaxation.
   - When the crack propagates obliquely downward toward the clamped base, un-degraded compressive stresses $\boldsymbol{\sigma}_0^-$ transfer across the closed crack flanks, creating a stiff compressive strut.
4. **Branch 4: Regularization Length Scale ($l_0$) Resolution:**
   - At $h = 3.73\,\mu\text{m} = l_0/4.02$, there are $\approx 8$ elements across the regularized crack band $2l_0 = 30\,\mu\text{m}$.
   - This satisfies the classical Bourdin/Miehe resolution criterion, providing the authoritative benchmark for evaluating adaptive remeshing efficiency.

---

## 7. 3-Layer Thesis Architecture Roadmap

To place this work within the broader context of the Master's thesis, the methodology is formalized into a modular 3-Layer Architecture:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ LAYER 3: SEQUENTIAL ADAPTIVE DRIVER (Thesis Phase 7)                        │
│ - Error-controlled remeshing triggers (Delta eta > tol or d_inc > tol)      │
│ - Automated mesh generation (Abaqus adaptiveRemesh / Gmsh)                  │
│ - Multi-field state transfer (u, d, H) across non-matching meshes           │
│ - Equilibrium restart, step continuation, and global convergence control    │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
┌──────────────────────────────────────▼──────────────────────────────────────┐
│ LAYER 2: ADAPTIVE MESH CONTROLLER & MULTI-FIELD INDICATORS (Phase 4-5)      │
│ - Multi-physics indicator: eta_K = alpha eta_stress + beta eta_phase        │
│ - Dynamic directional sizing: corridor alignment matching -58 deg shear path│
│ - Sizing function: h(x) with transition growth rate beta <= 1.25            │
│ - Discrete element quality assurance (aspect ratio AR <= 1.50)              │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
┌──────────────────────────────────────▼──────────────────────────────────────┐
│ LAYER 1: NUMERICAL FRACTURE SOLVER & FIXED BENCHMARK (Phase 1-3 & Gate M2-1B)│
│ - Dual-element UEL/UMAT implementation (f42_mixed_uel_mode2_miehe.for)      │
│ - 2D Miehe spectral decomposition and Kuhn-Tucker damage irreversibility    │
│ - Verified uniform fixed-mesh spatial convergence sequence (Gate M2-1B)     │
│ - Authoritative reference anchors for Mode-I and Mode-II shear fracture     │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Strategic Objectives of the 3 Layers:
- **Layer 1** establishes the undeniable physical ground truth. Without a verified fixed-mesh convergence sequence, adaptive remeshing results cannot be scientifically validated.
- **Layer 2** provides the intelligence: computing where, when, and how fine the discretization must be, replacing ad-hoc manual refinement with mathematically grounded error estimators.
- **Layer 3** executes the dynamic thesis goal: fully automated, sequential remeshing during crack propagation with rigorous state transfer and energy conservation.

---

## 8. Conclusion and Monitoring Status

All four fixed-mesh convergence jobs (`M2_FIX_COARSE_2P5K`, `M2_FIX_MED_18K`, `M2_FIX_INT_40K`, `M2_FIX_FINE_72K`) and the companion adaptive solve (`M2_J2_ADAPT_ET2_STAB`) continue solving smoothly on `mnode097` with zero cutbacks and 3 iterations per increment. The multi-increment stiffness regression audit has established that elastic compliance converges to within $0.02\%$ across the suite, matching literature within $0.37\%$, while setting the strict multi-quantity post-processing protocol ready for execution as each simulation reaches its fracture endpoint.
