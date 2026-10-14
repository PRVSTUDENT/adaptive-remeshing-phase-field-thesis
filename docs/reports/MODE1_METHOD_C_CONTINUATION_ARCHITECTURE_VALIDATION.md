# Independent Validation and Feasibility Audit of Method C Continuation Architectures: Corrected Scientific Claims and Operational C1/C2 Validation Gates

**Document Identifier:** `MODE1_METHOD_C_CONTINUATION_ARCHITECTURE_VALIDATION.md`  
**Governing Gate:** Method C / Gate 6C (Nonmatching State Transfer and Adaptive Fracture Continuation)  
**Protocol Version:** 2  
**Active Phase:** `METHOD_C_GATE6C_THESIS_INTEGRATION_AND_SUPERVISOR_BRIEFING_COMPLETE_READY_FOR_SUPERVISOR_REVIEW`  
**Date:** 2026-10-14  
**Author:** Gemini Antigravity (Governed Execution Agent)  
**Task Association:** Task F1458 (Correct Method C Scientific Claims and Establish a Defensible C1-to-C2 Validation Gate)  

---

## 1. Executive Summary & Scope of Independent Audit

This report provides the authoritative, scientifically qualified reassessment of continuation architectures for commercial Abaqus/Standard 2023 under Method C. It critically reviews and corrects prior assertions from Tasks F1456 and F1457, establishing a rigorous, evidence-backed framework for progressive evaluation.

### Core Reassessments & Reconciliations
1. **Reassessment of Method C1 Continuation:**
   - Staged re-equilibration from zero displacement is **not automatically genuine continuation**. It represents a *quasi-static reload through a pre-damaged state*. It cannot be declared qualified continuation without proving that the stress, displacement, damage, history, and internal energy at handoff match the donor state identically without premature damage evolution or artificial work dissipation.
   - Kinematic-offset continuation remains an **un-run experimental candidate**, not a verified solution.
2. **Mathematical Reassessment of Tangent Definiteness & Residuals:**
   - The structural tangent stiffness matrix $\mathbf{K}_{\text{tan}}$ is **not necessarily positive definite** in phase-field fracture mechanics. As material softening and strain localization develop, $\mathbf{K}_{\text{tan}}$ can admit zero or negative eigenvalues, reflecting macroscopic load drop and potential bifurcation.
   - A zero prescribed incremental displacement ($\Delta \mathbf{U}_{\text{prescribed}} = \mathbf{0}$) must be strictly distinguished from a zero transfer-induced residual ($\mathbf{R}_{\text{internal}, 0} \ne \mathbf{0}$) and zero boundary reaction-force discontinuity ($\Delta RF \ne 0$).
3. **Re-Evaluation of Method C2 Wake Coarsening:**
   - The condition $h \le l_0/2 = 3.75\,\mu\text{m}$ across damaged zones is a **conservative candidate mesh-resolution guideline**, not a universal mathematical theorem.
   - The $d \ge 0.05$ threshold, the $5l_0$ protection zone, and the chordal error formula are 1D surrogate models that require independent numerical validation in 2D multi-axial stress states.
   - Coarsening a fully fractured wake ($d \approx 1$) is **not trivial**: it can distort crack compliance, alter crack opening displacement (COD), artificially transfer traction across the crack flanks, alter fracture surface energy, and violate damage irreversibility.
   - The adaptive mesh generator must remain **trajectory-agnostic**: it must not hardcode a horizontal crack path ($y = 0.5\,\text{mm}$), but evaluate objective local field indicators ($d, |\nabla d|, \mathcal{H}, \dot{\mathcal{H}}$).
4. **Epistemic Classification Audit:**
   - All claims are strictly separated into a 5-tier evidence hierarchy: `[SOURCE CODE AUDIT]`, `[MATHEMATICAL DERIVATION]`, `[OFFLINE NUMERICAL PROJECTION]`, `[ABAQUS DATACHECK]`, and `[SOLVER RUNTIME VERIFICATION]`.
   - Forward recipient continuation ($2,906 \to 14,677$ FEs) is explicitly designated as `[OFFLINE NUMERICAL PROJECTION]` with `[SOLVER RUNTIME VERIFICATION: NOT YET EXECUTED]`.
5. **Project Authorization Reconciliation:**
   - **Gate 6B** evaluation is complete and prepared for supervisor sign-off on 22 October 2026.
   - **Gate 6C remains ON HOLD PENDING SUPERVISOR REVIEW.** Offline transfer results, unit tests, and general PBS script presence do not constitute authorization to execute solver continuation runs.
   - Execution restriction: Zero new Abaqus solver runs, zero PBS submissions, and zero modifications to production `f42_mixed_uel.for` (`CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6`).

---

## 2. Mathematical Derivation & Reassessment of Kinematic-Offset Continuation

### 2.1 Kinematic Decomposition & Strain Formulation

Let $\Omega \subset \mathbb{R}^2$ represent the reference domain of the specimen. At handoff displacement $u_{\text{handoff}} = 0.0050\,\text{mm}$ ($t = t_{\text{handoff}}$), the donor simulation provides a converged solution state:
- Transferred donor displacement field: $\mathbf{u}_0(\mathbf{x}) \in [H^1(\Omega)]^2$
- Transferred donor phase field: $d_0(\mathbf{x}) \in H^1(\Omega)$
- Transferred donor strain-history field: $\mathcal{H}_0(\mathbf{x}) \in L^2(\Omega)$
- External reaction force: $RF_y = 653.088\,\text{N}$

In the continuation analysis on recipient discretization $\Omega_h = \bigcup_{e=1}^{N_e} \Omega_e$, the total displacement $\mathbf{u}(\mathbf{x}, t)$ is decomposed additively into the transferred offset $\mathbf{u}_0(\mathbf{x})$ and an incremental continuation displacement $\Delta \mathbf{u}(\mathbf{x}, t)$:
$$\mathbf{u}(\mathbf{x}, t) = \mathbf{u}_0(\mathbf{x}) + \Delta \mathbf{u}(\mathbf{x}, t)$$

At the continuation entry instant ($t = t_{\text{handoff}}$):
$$\Delta \mathbf{u}(\mathbf{x}, t_{\text{handoff}}) = \mathbf{0} \quad \forall \mathbf{x} \in \Omega$$

Under infinitesimal strain kinematics, the total symmetric strain tensor is:
$$\boldsymbol{\varepsilon}(\mathbf{x}, t) = \nabla_{\text{sym}} \mathbf{u}_{\text{total}} = \nabla_{\text{sym}} \mathbf{u}_0(\mathbf{x}) + \nabla_{\text{sym}} \Delta \mathbf{u}(\mathbf{x}, t) = \boldsymbol{\varepsilon}_0(\mathbf{x}) + \Delta \boldsymbol{\varepsilon}(\mathbf{x}, t)$$

Within element $e$ having $n_{\text{en}}$ nodes:
$$\boldsymbol{\varepsilon}^e(\mathbf{x}, t) = \mathbf{B}(\mathbf{x}) \left( \mathbf{U}_0^e + \Delta \mathbf{U}^e(t) \right) = \boldsymbol{\varepsilon}_0^e(\mathbf{x}) + \mathbf{B}(\mathbf{x}) \Delta \mathbf{U}^e(t)$$
where $\mathbf{B}(\mathbf{x})$ is the standard strain-displacement matrix and $\mathbf{U}_0^e$ is the vector of transferred nodal coordinates/displacements.

### 2.2 Constitutive Degradation & History Evolution

The Cauchy stress tensor $\boldsymbol{\sigma}$ is governed by the degraded isotropic elasticity tensor:
$$\boldsymbol{\sigma}(\mathbf{x}, t) = g(d) \mathbf{C}_0 : \boldsymbol{\varepsilon}(\mathbf{x}, t) = \left[ (1 - d(\mathbf{x}, t))^2 + k_{\text{stab}} \right] \mathbf{C}_0 : \left( \boldsymbol{\varepsilon}_0(\mathbf{x}) + \mathbf{B} \Delta \mathbf{U}^e(t) \right)$$
where $k_{\text{stab}} = 1.0 \times 10^{-7}$ is the residual stiffness parameter preventing complete singularity at $d = 1$.

The undegraded crack-driving energy density $\psi_0^+(\boldsymbol{\varepsilon})$ is evaluated from the total strain:
$$\psi_0^+(\boldsymbol{\varepsilon}) = \frac{1}{2} K_0 \langle \operatorname{tr} \boldsymbol{\varepsilon} \rangle_+^2 + \mu_0 \left( \varepsilon_{11}^2 + \varepsilon_{22}^2 + 2\varepsilon_{12}^2 \right)$$

History variable irreversibility is enforced pointwise:
$$\mathcal{H}(\mathbf{x}, t) = \max \left( \mathcal{H}_0(\mathbf{x}), \max_{\tau \in [t_{\text{handoff}}, t]} \psi_0^+(\boldsymbol{\varepsilon}(\mathbf{x}, \tau)) \right)$$

### 2.3 Residual Vectors & Tangent Operator Reassessment

The internal virtual work vector for element $e$ is:
$$\mathbf{F}_{\text{int}}^e(\Delta \mathbf{U}^e, d) = \int_{\Omega_e} \mathbf{B}^T g(d) \mathbf{C}_0 \mathbf{B} (\mathbf{U}_0^e + \Delta \mathbf{U}^e) \, d\Omega$$

The mechanical tangent stiffness matrix is the directional derivative with respect to $\Delta \mathbf{U}^e$:
$$\mathbf{K}_{\text{tan}}^e = \frac{\partial \mathbf{F}_{\text{int}}^e}{\partial \Delta \mathbf{U}^e} = \int_{\Omega_e} \mathbf{B}^T g(d) \mathbf{C}_0 \mathbf{B} \, d\Omega$$

#### Scientific Correction: Reassessment of Tangent Definiteness
- **Prior Incorrect Assertion:** "Symmetry and positive-definiteness are strictly preserved."
- **Corrected Mathematical Fact:** 
  For fixed damage $d < 1$, the linear elastic operator with spatial degradation factor $g(d) > 0$ is symmetric and positive-definite on the subspace orthogonal to rigid-body modes.
  However, **in a coupled fracture simulation**, the true Jacobian of the mechanical residual includes the coupling to phase-field evolution:
  $$\mathbf{J}_{\text{mech}} = \frac{\partial \mathbf{F}_{\text{int}}}{\partial \Delta \mathbf{U}} + \frac{\partial \mathbf{F}_{\text{int}}}{\partial d} \frac{\partial d}{\partial \Delta \mathbf{U}}$$
  During macroscopic softening ($\dot{d} > 0$), material degradation introduces negative eigenvalues into the tangent operator. When crack propagation initiates, the structural tangent stiffness matrix $\mathbf{K}_{\text{tan}}$ **loses positive definiteness**, which can lead to bifurcation, snap-back, or localized convergence failure. Therefore, the tangent stiffness operator in phase-field continuation cannot be assumed to remain positive definite throughout the analysis.

### 2.4 Strict Distinction Between the Three Zero Quantities

A rigorous analysis requires keeping three distinct quantities strictly separated:

1. **Zero Prescribed Incremental Displacement ($\Delta \mathbf{U}_{\text{prescribed}} = \mathbf{0}$):**
   At the start of the continuation step, the boundary condition prescribes zero incremental displacement relative to the handoff state. This is an input boundary condition specification.
2. **Non-Zero Transfer-Induced Internal Residual ($\mathbf{R}_{\text{internal}, 0} \ne \mathbf{0}$):**
   Because the recipient discretization $\Omega_h^{\text{recip}}$ ($14,677$ FEs) constitutes a different approximation subspace than the donor discretization $\Omega_h^{\text{donor}}$ ($2,906$ FEs), the transferred stress state $\boldsymbol{\sigma}_0 = g(d_0)\mathbf{C}_0 : \boldsymbol{\varepsilon}_0$ is **not in discrete equilibrium** on the recipient mesh:
   $$\mathbf{R}_{\text{internal}, 0} = -\mathbf{F}_{\text{int}, 0} = -\sum_{e=1}^{N_e} \mathbf{L}_e^T \int_{\Omega_e} \mathbf{B}^T \boldsymbol{\sigma}_0 \, d\Omega \ne \mathbf{0} \quad \text{at unconstrained internal nodes}$$
   There is an unavoidable discretization projection residual $\boldsymbol{\rho}_{\text{transfer}} = \mathbf{R}_{\text{internal}, 0}$.
   When Increment 1 begins, Abaqus evaluates this non-zero residual norm and solves for an initial Newton relaxation step:
   $$\delta (\Delta \mathbf{U}) = \mathbf{K}_{\text{tan}, 0}^{-1} \mathbf{R}_{\text{internal}, 0}$$
   If this projection residual is large, it can trigger an immediate time-step cutback before convergence.
3. **Boundary Reaction-Force Discontinuity ($\Delta RF \ne 0$):**
   The reaction force at the prescribed boundary evaluates to $RF = \sum_{i \in \Gamma_{\text{top}}} F_{\text{int}, y, i}$.
   The difference between recipient entry force and donor exit force $|\Delta RF| = |RF_{\text{recip}} - RF_{\text{donor}}|$ reflects both domain compliance differences and boundary integration errors.

Conflating $\Delta \mathbf{U}_{\text{prescribed}} = \mathbf{0}$ with $\mathbf{R}_{\text{internal}, 0} = \mathbf{0}$ or $\Delta RF = 0$ is a severe epistemic error: applying zero displacement increment does **not** ensure discrete equilibrium or force continuity.

---

## 3. Re-Evaluation of Staged Static Re-Equilibration (Path 1) vs Kinematic Offset (Path 2)

### 3.1 Critique of Staged Static Re-Equilibration (Path 1)

In Task F1456, staged static re-equilibration (ramping displacement from $u = 0$ to $u = 0.0050\,\text{mm}$ in 20–50 increments) was presented as a practical continuation method that keeps production UEL `f42_mixed_uel.for` frozen.

#### Critical Scientific Reassessment:
- Staged re-equilibration from $u = 0$ is a **quasi-static reload through a pre-damaged state**, **NOT genuine state continuation**.
- Ramping the boundary displacement from zero forces the structure to re-traverse an elastic loading path under pre-existing damage.
- To claim that staged re-equilibration is a valid surrogate for continuation, it must satisfy **five mandatory equivalence criteria** at $u = u_{\text{handoff}}$:
  1. **Displacement Equivalence:** $\mathbf{u}_{\text{recip}}(u_{\text{handoff}}) \approx \mathbf{u}_{\text{donor}}(u_{\text{handoff}})$;
  2. **Stress Equivalence:** $\boldsymbol{\sigma}_{\text{recip}}(u_{\text{handoff}}) \approx \boldsymbol{\sigma}_{\text{donor}}(u_{\text{handoff}})$;
  3. **Damage Preservation:** $\dot{d} = 0$ for all $u < u_{\text{handoff}}$ (no premature damage growth during reload);
  4. **History Preservation:** $\mathcal{H}_{\text{recip}}(u_{\text{handoff}}) = \mathcal{H}_0$ (no spurious driving energy accumulation during reload);
  5. **Energy Equivalence:** $E_{\text{elas}}(u_{\text{handoff}}) \approx E_{\text{elas}}^{\text{donor}}$ with zero artificial hysteresis work.
- In Job 1412464, a 1,000-increment reload was required to reach $u = 0.0050\,\text{mm}$ with $\Delta RF = 0.09\,\text{N}$, but the computational cost of reloading was 1,000 increments. In Job 1412809, a single-increment jump caused a $21.55\,\text{N}$ force jump.
- **Classification:** Staged re-equilibration remains a *provisional numerical surrogate*, not a verified continuation method.

### 3.2 Status of Kinematic-Offset UEL (Path 2)

- Kinematic-offset continuation incorporates the transferred displacement field into the element kinematics ($\mathbf{u} = \mathbf{u}_0 + \Delta \mathbf{u}$).
- While mathematically consistent under infinitesimal elasticity, it remains an **un-run experimental proposal**:
  * No recipient-mesh continuation simulation has been implemented or executed;
  * The ingestion of 8 nodal displacement values per element requires expanding `NSVARS` from 18 to 26 or implementing table lookups in Fortran;
  * The initial projection residual $\boldsymbol{\rho}_{\text{transfer}}$ has not been tested against Abaqus convergence tolerances in a running solver.
- **Classification:** An experimental R&D candidate requiring isolated branch investigation, not a qualified solution.

---

## 4. Fortran Source Code & Abaqus 2023 Implementation Audit

### 4.1 Audit of Authoritative Production UEL (`f42_mixed_uel.for`)

The production user subroutine `f42_mixed_uel.for` (SHA-256: `CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6`, 908 lines) was audited:

```fortran
C Common block coupling in f42_mixed_uel.for:
      DOUBLE PRECISION SV_PHASE_COMMITTED(N_CAPACITY)
      DOUBLE PRECISION SV_PHASE_TRIAL(N_CAPACITY)
      DOUBLE PRECISION SV_H_COMMITTED(N_CAPACITY,4)
      DOUBLE PRECISION SV_H_TRIAL(N_CAPACITY,4)
      DOUBLE PRECISION SV_E_FRAC(N_CAPACITY)
      DOUBLE PRECISION SV_E_ELAS(N_CAPACITY)
      DOUBLE PRECISION SV_PSI_F(N_CAPACITY)
      DOUBLE PRECISION SV_PSI_E(N_CAPACITY)

      COMMON /CB_STATE_TRANS/ SV_PHASE_COMMITTED, SV_PHASE_TRIAL,
     1                        SV_H_COMMITTED, SV_H_TRIAL,
     2                        SV_E_FRAC, SV_E_ELAS,
     3                        SV_PSI_F, SV_PSI_E
```

#### Key Technical Findings:
1. **`UEXTERNALDB(LOP=0)` Zeroing Loop (Lines 88–101):**
   At the start of analysis (`LOP=0`), `UEXTERNALDB` zeroes all committed/trial arrays across $150,000$ element slots. This guarantees memory hygiene, but also means that Fortran common blocks **cannot retain state across Abaqus process executions**.
2. **History Variable Ingestion via `SVARS` (Lines 248–262):**
   In Step 1 Increment 1, Layer 1 (JTYPE 1/3) reads `SV_H_COMMITTED(PHYSIDX, KPT) = SVARS(8+KPT)`. This proves that `*INITIAL CONDITIONS, TYPE=SOLUTION` cards in `.inp` decks successfully populate `SVARS`, and the UEL transfers them into `SV_H_COMMITTED` at $t=0$.
3. **`*INITIAL CONDITIONS, TYPE=SOLUTION` vs `SDVINI`:**
   `*INITIAL CONDITIONS, TYPE=SOLUTION` delivers state variables directly from the input deck and is fully supported in Abaqus 2023. Implementing user subroutine `SDVINI` would require reading external binary/ASCII files inside Fortran, introducing path and file-locking vulnerabilities with zero technical benefit.
4. **Staggered Coupling Lag:**
   Layer 1 (Phase) and Layer 2 (Mechanical) communicate across `COMMON /CB_STATE_TRANS/`. Because Abaqus executes element loops sequentially, Layer 2 evaluates degraded stiffness using the phase state from the preceding iteration/increment, creating a 1-iteration staggered coupling lag across step boundaries.

---

## 5. Alternative Candidate Architectures: Reference Configuration & Residual Correction

### 5.1 Candidate 3A: Reference-Configuration Update ($\mathbf{X}^* = \mathbf{X} + \mathbf{u}_0$)

A proposed alternative is to update the reference mesh nodal coordinates directly:
$$\mathbf{X}^*(\text{node } i) = \mathbf{X}_{\text{original}}(\text{node } i) + \mathbf{u}_0(\text{node } i)$$

#### Mathematical and Physical Disqualification:
1. **Obliteration of Stored Elastic Stress and Strain:**
   In continuum mechanics, the reference configuration $\mathbf{X}^*$ is the stress-free undeformed state. Initializing continuation with displacement $\Delta \mathbf{u} = \mathbf{0}$ yields:
   $$\mathbf{F} = \frac{\partial \mathbf{x}}{\partial \mathbf{X}^*} = \mathbf{I} \implies \boldsymbol{\varepsilon} = \mathbf{0} \implies \boldsymbol{\sigma} = \mathbf{0}$$
   The pre-accumulated elastic strain energy ($E_{\text{elas}} \approx 1.66\,\text{mJ}$) and boundary reaction force ($RF = 653.09\,\text{N}$) are **completely obliterated**.
2. **Geometric Distortion of Crack Seam:**
   Displacement gradients near the crack tip are singular ($\nabla \mathbf{u} \sim r^{-1/2}$). Updating reference coordinates blunts and deforms the zero-thickness crack seam into an artificial notch.
3. **Verdict:** **PHYSICALLY AND MATHEMATICALLY INVALID.**

### 5.2 Candidate 3B: Residual-Correction Continuation (Balancing Body Force)

Applying an initial balancing body force field $\mathbf{b}_{\text{corr}}(\mathbf{x}) = -\nabla \cdot \boldsymbol{\sigma}_0$ via Abaqus distributed loads (`*DLOAD`):
1. **Abaqus UEL Limitation:** Abaqus user elements do not automatically support standard continuum `*DLOAD` body forces without extensive custom coding of `NDLOAD`, `JDLTYP`, and `ADLMAG` inside the UEL.
2. **External Work Corruption:** The balancing body force performs work during subsequent crack propagation ($\Delta W = \int \mathbf{b}_{\text{corr}} \cdot \Delta \mathbf{u} \, d\Omega$), corrupting the global energy balance $W_{\text{ext}} = E_{\text{elas}} + E_{\text{frac}}$.
3. **Verdict:** **SOFTWARE BARRIER AND WORK CORRUPTION.**

---

## 6. Re-Evaluation of Method C2 Wake Coarsening: Physics, Pitfalls & Mesh Guidelines

### 6.1 The Physical Necessity of Coarsening in Method C2

In progressive crack propagation, adaptive remeshing must satisfy two competing demands:
- **Refinement in Active Zones:** Maintain fine resolution ($h \le l_0/2 = 3.75\,\mu\text{m}$) in the active fracture process zone (FPZ) to resolve damage gradients.
- **De-Refinement in Inactive Zones:** Coarsen inactive regions to prevent monotonic element inflation ($N_e^{(k+1)} > N_e^{(k)}$), which would otherwise cause the fine mesh to cover the entire domain and defeat adaptive efficiency.

### 6.2 Three Material Regimes & Pitfalls of Coarsening Fully Fractured Wakes

Coarsening cannot be treated uniformly across the domain. Three distinct regimes must be separated:

```
+----------------------------------------------------------------------------------------------------+
|                               THREE MATERIAL REGIMES IN METHOD C2                                  |
+--------------------------+------------------------------+------------------------------------------+
| Material Regime          | Physical & Damage State      | Coarsening Feasibility & Governing Rules |
+--------------------------+------------------------------+------------------------------------------+
| 1. Intact Far Field      | d = 0, grad(d) = 0           | SAFE TO COARSEN: Elements can coarsen    |
|                          | Fully elastic bulk           | to coarse sizes (h = 20-50 um) without   |
|                          |                              | phase-field distortion or energy loss.   |
+--------------------------+------------------------------+------------------------------------------+
| 2. Active FPZ            | 0 < d < 1, d_dot > 0         | STRICTLY FORBIDDEN TO COARSEN: Must      |
|                          | Active damage dissipation    | maintain fine mesh (h <= l0/4 to l0/2)   |
|                          |                              | to resolve grad(d) and energy release.   |
+--------------------------+------------------------------+------------------------------------------+
| 3. Fully Fractured Wake  | d ~ 1, d_dot = 0             | FRAUGHT WITH SEVERE NUMERICAL PITFALLS:  |
|                          | Stress relaxed (sigma ~ 0)   | Coarsening across crack seam alters arm  |
|                          |                              | compliance, distorts COD, risks bridging,|
|                          |                              | and alters fracture energy quadrature.   |
+--------------------------+------------------------------+------------------------------------------+
```

#### Detailed Pitfalls in the Fully Fractured Wake ($d \approx 1$):
1. **Crack Opening Displacement (COD) & Arm Compliance:**
   Even though the material in the wake is de-stressed, the broken arms of the specimen undergo finite bending and rotation. If elements along the crack faces are coarsened, the discrete representation of the crack boundary becomes coarse, altering the bending compliance of the broken arms and distorting the global reaction force.
2. **Spurious Crack Bridging / Flank Penetration:**
   Coarse elements spanning the crack line can average the phase field across the slit, leading to artificial traction transfer or locking between upper and lower crack flanks.
3. **Fracture Surface Energy Quadrature Distortion:**
   The integrated fracture surface energy $\int_{\text{wake}} \frac{G_c}{2} (\frac{d^2}{l_0} + l_0 |\nabla d|^2) d\Omega \approx G_c \cdot a$ must be preserved. Coarsening changes the numerical quadrature of this term, potentially causing artificial energy jumps or drops.
4. **Irreversibility Violation upon Interpolation:**
   Projecting a sharp wake profile $d \approx 1$ onto coarse linear elements can cause local undershoot ($d < d_{\text{donor}}$), violating the thermodynamic irreversibility condition $\dot{d} \ge 0$.

### 6.3 Reassessment of the C2 Resolution Guideline (Not a "Theorem")

- **Prior Assertion Corrected:** The condition $h \le l_0/2 = 3.75\,\mu\text{m}$ was previously called "The Method C2 Resolution Theorem".
- **Corrected Formulation:** This condition is a **candidate engineering resolution guideline**, derived from a 1D surrogate profile:
  $$h(\mathbf{x}) \le \frac{l_0}{2} = 3.75\,\mu\text{m} \quad \text{for regions with active or localized damage}$$
- **Limitations of the 1D Surrogate Model:**
  The analytical chordal error formula $\varepsilon_{\text{chordal}}(\xi) = \xi \coth(\xi) - 1$ ($\xi = \frac{h}{2l_0}$) assumes a 1D exponential profile $d(y) = d_0 \exp(-|y|/l_0)$.
  * In 2D, the phase-field equation involves the 2D Laplacian $\nabla^2 d$, producing curved contours around the crack tip;
  * The elements are 2D quadrilaterals/triangles with bilinear/linear interpolation;
  * The 1D surrogate predicts $+53.25\%$ element-level error for $h = 20\,\mu\text{m}$, whereas the evaluated 2D whole-domain damage error in Job 1412809 was $+5.0465\%$ (because the damaged band occupies only a fraction of the domain);
  * On the fine mesh ($h = 1.875\,\mu\text{m}$), the 1D surrogate predicts $+0.5208\%$, whereas the evaluated 2D domain error was $0.1322\%$.
  Therefore, the chordal error formula is an illustrative analytical surrogate that explains the mechanism of over-estimation, but cannot substitute for 2D numerical evaluation.
- **Provisional Thresholds:** The proposed damage threshold $d \ge 0.05$ and the $5l_0$ protection zone are provisional heuristics that require systematic numerical validation.

### 6.4 Trajectory-Agnostic Adaptive Formulation

The general-purpose controller must **never hardcode a geometric crack path** (such as assuming horizontal extension along $y = 0.5\,\text{mm}$).
The adaptive sizing field $h(\mathbf{x})$ must be formulated strictly as a function of objective local field variables:
$$h(\mathbf{x}) = \mathcal{F}\left( d(\mathbf{x}), |\nabla d(\mathbf{x})|, \mathcal{H}(\mathbf{x}), \dot{\mathcal{H}}(\mathbf{x}), \eta_{\text{error}}(\mathbf{x}) \right)$$
This ensures that the mesh refinement and coarsening algorithms naturally generalize to arbitrary crack paths, curved trajectories, Mode-II, or mixed-mode problems without manual intervention.

---

## 7. Comprehensive 5-Tier Epistemic Evidence Classification

To maintain rigorous scientific discipline, all technical statements and findings are classified according to the 5-tier evidence hierarchy:

```
+==================================================================================================================================+
|                                    5-TIER EPISTEMIC EVIDENCE CLASSIFICATION TABLE                                                |
+==========================================================+============================+==========================================+
| Feature / Claim / Result                                 | Epistemic Classification   | Exact Provenance / Evidence Basis        |
+==========================================================+============================+==========================================+
| Abaqus Error 144: *INITIAL CONDITIONS, TYPE=DISPLACEMENT | [SOLVER RUNTIME            | Preflight Abaqus/Standard runs on cluster|
| is fatal in *STATIC procedures                           |  VERIFICATION]             | (Task F1447, Exit 1 with Error 144)      |
+----------------------------------------------------------+----------------------------+------------------------------------------+
| *INITIAL CONDITIONS, TYPE=SOLUTION successfully loads    | [SOLVER RUNTIME            | Cluster jobs 1412158, 1412464, 1412809   |
| SVARS 1..18 for 44,031 element records                   |  VERIFICATION]             | (M1_MC_GEN_CONT, Exit 0)                 |
+----------------------------------------------------------+----------------------------+------------------------------------------+
| Coarse Donor Handoff State at u = 0.0050 mm:             | [SOLVER RUNTIME            | Job 1411891 (M1_PRE_1S) extracted to     |
| RF = 653.088 N, E_int = 1.6634 mJ, d_max = 0.094910      |  VERIFICATION]             | coarse_donor_state_u0050.json (3F9198CD..|
+----------------------------------------------------------+----------------------------+------------------------------------------+
| Reverse Coarsening Damage Integral Failure (+5.0465%):   | [SOLVER RUNTIME            | Job 1412809 & genuine_continuation_      |
| caused by coarse element chordal over-estimation         |  VERIFICATION]             | evaluation.json (Task F1450)             |
+----------------------------------------------------------+----------------------------+------------------------------------------+
| Reverse Coarsening Severe Crack Pinning:                 | [SOLVER RUNTIME            | Job 1412809 load-displacement CSV:       |
| F_max = 1085.41 N (+43.2%), u_peak = 0.009219 mm (+57.4%) | VERIFICATION]             | coarse mesh pins crack initiation        |
+----------------------------------------------------------+----------------------------+------------------------------------------+
| Single-Increment Secant Step-Boundary Jump:              | [SOLVER RUNTIME            | Job 1412809: |653.17 - 674.72| = 21.55 N |
| Delta RF = 21.55 N > 5.0 N (Criterion 1 FAIL)           |  VERIFICATION]             | evaluated across Step 1 -> Step 2 boundary|
+----------------------------------------------------------+----------------------------+------------------------------------------+
| Fortran UEXTERNALDB(LOP=0) zeroing and CB_STATE_TRANS    | [SOURCE CODE AUDIT]        | Line-by-line inspection of production UEL|
| staggered coupling lag in f42_mixed_uel.for              |                            | CE8D5EDCD2911DCB018BB15275271F874E7EA62B8|
+----------------------------------------------------------+----------------------------+------------------------------------------+
| Reference-Configuration Update (X* = X + u0) Invalidity  | [MATHEMATICAL DERIVATION]  | Proof that F = I, strain = 0, stress = 0,|
|                                                          |                            | and crack-tip blunting geometry occurs   |
+----------------------------------------------------------+----------------------------+------------------------------------------+
| Analytical 1D Chordal Error Formula:                     | [MATHEMATICAL DERIVATION]  | Analytical integration: xi*coth(xi) - 1, |
| xi*coth(xi) - 1 produces +53.25% for h/l0 = 2.67         |                            | derived for 1D exponential surrogate     |
+----------------------------------------------------------+----------------------------+------------------------------------------+
| Forward State Transfer Metrics (2,906 -> 14,677 FEs):    | [OFFLINE NUMERICAL         | audit_forward_transfer_summary.json:     |
| L2 = 0.1347%, Delta d = 0.000, Delta I = 0.1322%, min(H)>=0 | PROJECTION]              | evaluated in Python; UN-RUN IN SOLVER    |
+----------------------------------------------------------+----------------------------+------------------------------------------+
| Forward Recipient Solver Continuation (14,677 FEs):      | [SOLVER RUNTIME            | Un-run candidate input deck              |
| Reaction force continuity, F-u curve, post-peak softening|  VERIFICATION: NOT YET RUN]| (M1_MC_C1_FORWARD_14K.inp); zero solver runs|
+----------------------------------------------------------+----------------------------+------------------------------------------+
| Kinematic-Offset UEL Continuation Formulation:           | [MATHEMATICAL DERIVATION / | Derived on paper; requires experimental  |
| u = u0 + Delta u, F_int, and K_tan operators             |  UNIMPLEMENTED PROPOSAL]   | UEL implementation and verification      |
+----------------------------------------------------------+----------------------------+------------------------------------------+
| Candidate C2 Wake Coarsening Resolution Guideline:       | [MATHEMATICAL DERIVATION / | Heuristic engineering guideline; awaits  |
| h_wake <= l0/2 = 3.75 um for d >= 0.05                   |  UNIMPLEMENTED PROPOSAL]   | candidate C2 mesh synthesis & solve      |
+==================================================================================================================================+
```

---

## 8. Corrected Decision Matrix: C1 Continuation & C2 Coarsening

```
+==================================================================================================================================+
|                                    CORRECTED DECISION MATRIX: METHOD C CONTINUATION ARCHITECTURES                                |
+================================+================================+================================+===============================+
| Evaluation Criterion           | PATH 1: Staged Re-Equilibration| PATH 2: Kinematic-Offset UEL   | PATH 3: Reference Update /    |
|                                | (Input-Deck / Frozen UEL)      | (Option B / Branch UEL)        | Residual Correction           |
+================================+================================+================================+===============================+
| 1. Mathematical Consistency    | Quasi-static reload through    | Additive displacement          | Candidate 3A: Invalid (F=I)   |
|                                | existing damage; NOT genuine   | kinematics u = u0 + Delta u;   | Candidate 3B: Spurious body   |
|                                | state continuation             | subject to softening tangent   | force work corrupts balance   |
+--------------------------------+--------------------------------+--------------------------------+-------------------------------+
| 2. Discrete Equilibrium at     | Solved iteratively across      | Subject to nonmatching discrete| 3A: Zero stress at entry      |
|    Continuation Entry          | 20-50 sub-stepping increments  | projection residual rho_trans  | 3B: Distorted equilibrium     |
+--------------------------------+--------------------------------+--------------------------------+-------------------------------+
| 3. Step-Boundary Force Jump    | Controllable via fine sub-     | Analytically 0 prescribed inc; | 3A: Total force drop (-653 N) |
|                                | stepping delta_u <= 1e-5 mm    | relaxed in Increment 1 Iter 1  | 3B: Load balance corrupted    |
+--------------------------------+--------------------------------+--------------------------------+-------------------------------+
| 4. Production UEL Freeze       | 100% FROZEN & UNCHANGED        | MODIFIES UEL SOURCE; requires  | Requires UEL *DLOAD rewrite   |
|    (CE8D5EDC... Integrity)     | (Preserved on canonical main)  | isolated experimental branch   | or deck distortions           |
+--------------------------------+--------------------------------+--------------------------------+-------------------------------+
| 5. Abaqus 2023 Compatibility   | 100% COMPATIBLE                | Compatible; requires expanded  | 3A: Compatible but wrong      |
|                                | (No new keywords or ABI change)| NSVARS (18 -> 26) or table     | 3B: Incompatible with UEL     |
+--------------------------------+--------------------------------+--------------------------------+-------------------------------+
| 6. Computational Cost          | +20-50 increments in Step 1    | Starts directly at Inc 1;      | N/A (Disqualified)            |
|                                | (~3-5% additional walltime)    | zero reload steps              |                               |
+--------------------------------+--------------------------------+--------------------------------+-------------------------------+
| 7. Multi-Cycle Feasibility     | Inefficient for multiple cycles| Ideal multi-cycle architecture | Disqualified                  |
|    (Method C2 Extension)       | (reloads scale per cycle)      | for arbitrary sequential cycles|                               |
+--------------------------------+--------------------------------+--------------------------------+-------------------------------+
| 8. Governance & Risk           | Zero risk to frozen codebase;  | Medium risk; branch isolation  | Severe risk of unphysical     |
|                                | reload equivalence unproven    | and re-qualification required  | results                       |
+================================+================================+================================+===============================+
| SCIENTIFIC VERDICT             | PROVISIONAL SURROGATE CANDIDATE| EXPERIMENTAL R&D CANDIDATE     | STRICTLY DISQUALIFIED         |
|                                | (Requires reload equivalence)  | (Requires branch R&D)          |                               |
+================================+================================+================================+===============================+
```

### Explicit List of Unresolved Technical Barriers
1. **Commercial Abaqus Displacement Rejection:** Abaqus/Standard rejects `*INITIAL CONDITIONS, TYPE=DISPLACEMENT` in general static steps (Error 144).
2. **Transfer-Induced Projection Residual:** Mesh-to-mesh interpolation creates internal out-of-balance forces $\boldsymbol{\rho}_{\text{transfer}} \ne \mathbf{0}$ that trigger initial Newton relaxation cutbacks.
3. **Staggered Dual-Layer COMMON Coupling Lag:** Layer 1 (Phase) and Layer 2 (Mechanical) have a 1-iteration lag at step entry across `COMMON /CB_STATE_TRANS/`.
4. **Wake Coarsening Distortion:** Coarsening the phase-field wake risks altering specimen bending compliance, violating damage irreversibility, and distorting fracture surface energy.
5. **Multi-Cycle Compounding Error:** State transfer across multiple sequential cycles risks progressive numerical diffusion of damage gradients.

### Smallest Justified Next Experimental Step
The smallest justified next experimental step (pending formal supervisor release of Gate 6C) is:
**Generate and datacheck (without solver execution) the single-cycle forward-refinement input deck (`M1_MC_C1_FORWARD_14K.inp`) using staged re-equilibration, verifying deck syntax, card wrapping, and memory requirements on the cluster login node.**

---

## 9. Operational Validation Gates for Method C1 and Method C2

To replace ad-hoc assessments with rigorous, falsifiable criteria, independent validation gates are established for C1 and C2:

### 9.1 Gate C1: Forward-Refinement Continuation Validation Gate

Before any coarsening or multi-cycle work can be undertaken, Method C1 must achieve **PASS** across all six operational criteria on the forward refinement experiment ($2,906 \to 14,677$ FEs at $u_{\text{handoff}} = 0.0050\,\text{mm}$):

```
+==================================================================================================================================+
|                                    GATE C1: OPERATIONAL ACCEPTANCE CRITERIA                                                      |
+----+--------------------------------+---------------------------------------+------------------+---------------------------------+
| #  | Criterion Name                 | Governing Metric Formula              | Pass Threshold   | Falsification / Failure Condition|
+----+--------------------------------+---------------------------------------+------------------+---------------------------------+
| C1-1| Boundary Reaction Continuity   | |RF_entry - RF_donor|                 | <= 5.0 N         | > 5.0 N force jump at handoff   |
|    |                                | |RF_step2_inc1 - RF_step1_end|        |                  |                                 |
+----+--------------------------------+---------------------------------------+------------------+---------------------------------+
| C1-2| Transfer Energy Error          | Delta E_trans / W_ext(u_handoff)      | <= 5.0%          | > 5.0% energy gain/loss         |
+----+--------------------------------+---------------------------------------+------------------+---------------------------------+
| C1-3| Global Energy Balance Residual | |W_ext - (E_elas + E_frac)| / W_ext   | <= 10.0%         | > 10.0% un-conserved work       |
+----+--------------------------------+---------------------------------------+------------------+---------------------------------+
| C1-4| Damage Irreversibility         | min(d_{n+1} - d_n)                    | >= -1.0e-6       | Artificial damage healing       |
|    |                                | min(H_{n+1} - H_n)                    | >= 0.0           | Negative history variable       |
+----+--------------------------------+---------------------------------------+------------------+---------------------------------+
| C1-5| Fracture Response Parity       | |K_0 - K_0^ref| / K_0^ref             | <= 1.0%          | Initial stiffness mismatch      |
|    | vs Fixed Reference             | |F_max - F_max^ref| / F_max^ref       | <= 3.0%          | Crack pinning (F_max > 0.78 kN) |
|    |                                | RF_final / F_max                      | <= 0.02          | Incomplete softening tail       |
+----+--------------------------------+---------------------------------------+------------------+---------------------------------+
| C1-6| Repeatability & Determinism    | Pre-peak cutbacks                     | 0 cutbacks       | Pre-peak cutback or solver hang |
|    |                                | Parity across identical hardware      | 100% hash parity | Non-deterministic divergence    |
+----+--------------------------------+---------------------------------------+------------------+---------------------------------+
```

### 9.2 Gate C2: Selective Wake Coarsening & Cycle 2 Validation Gate

Gate C2 may be activated **only after Gate C1 achieves formal PASS**. It governs the investigation of selective coarsening in the de-stressed wake and the second sequential remeshing cycle:

```
+==================================================================================================================================+
|                                    GATE C2: OPERATIONAL ACCEPTANCE CRITERIA                                                      |
+----+--------------------------------+---------------------------------------+------------------+---------------------------------+
| #  | Criterion Name                 | Governing Metric Formula              | Pass Threshold   | Falsification / Failure Condition|
+----+--------------------------------+---------------------------------------+------------------+---------------------------------+
| C2-1| Coarsening Energy Discrepancy  | |E_int^C2 - E_int^C1| / W_ext         | <= 5.0%          | > 5.0% energy loss upon coarsen |
+----+--------------------------------+---------------------------------------+------------------+---------------------------------+
| C2-2| Crack Opening Compliance (COD) | |COD_C2 - COD_C1| / COD_C1            | <= 3.0%          | Coarse elements alter arm bend  |
+----+--------------------------------+---------------------------------------+------------------+---------------------------------+
| C2-3| Wake Surface Energy Quadrature | |E_frac^wake_C2 - E_frac^wake_C1|/E_fr| <= 5.0%          | Coarsening distorts crack area  |
+----+--------------------------------+---------------------------------------+------------------+---------------------------------+
| C2-4| Wake Flank Non-Penetration     | Interface contact traction            | 0 spurious shear | Spurious crack bridging/locking |
|    | and Irreversibility            | min(d_C2 - d_C1)                      | >= -1.0e-6       | Damage healing in wake          |
+----+--------------------------------+---------------------------------------+------------------+---------------------------------+
| C2-5| Net Computational Efficiency   | Walltime_C2 / Walltime_C1             | <= 0.85          | Coarsening fails to reduce CPU  |
|    |                                | Element count N_e^C2 / N_e^C1         | <= 0.70          | time by at least 15%            |
+----+--------------------------------+---------------------------------------+------------------+---------------------------------+
```

### 9.3 Standardized Evidence-Reporting Template

Every future Method C continuation solver evaluation must report results using the following standardized template:

```markdown
### Method C Solver Execution Telemetry & Evidence Summary
- **Job ID & Queue:** `<job_id>.mmaster02` in `<queue>` on `<node>`
- **Model Decks & Lineage:** Donor `<donor_deck.inp>` -> Recipient `<recipient_deck.inp>`
- **Finite Element Count:** Donor `<N_donor>` FEs -> Recipient `<N_recip>` FEs
- **Step Architecture:** Step 1 (`<N_inc1>` incs, `<time1>`) -> Step 2 (`<N_inc2>` incs, `<time2>`)
- **Cutback Diagnostics:** `<total_cutbacks>` cutbacks (pre-peak: `<pre_cutbacks>`, post-peak: `<post_cutbacks>`)
- **Boundary Reaction Continuity:**
  * Donor handoff force: $RF_{\text{donor}} = \dots\,\text{N}$
  * Recipient entry force: $RF_{\text{recip}} = \dots\,\text{N}$
  * Step boundary jump: $|\Delta RF| = \dots\,\text{N}$ (Verdict: PASS / FAIL)
- **UEL Energy Balance Tracking:**
  * External work: $W_{\text{ext}} = \dots\,\text{mJ}$
  * Elastic strain energy: $E_{\text{elas}} = \dots\,\text{mJ}$
  * Fracture surface energy: $E_{\text{frac}} = \dots\,\text{mJ}$
  * Bookkeeping residual: $\Delta E = \dots\,\text{mJ}$ ($\dots\%$ relative error)
- **Damage Profile & Irreversibility:**
  * Maximum phase field: $d_{\max} = \dots$
  * Irreversibility check: $\min(\Delta d) = \dots \ge -10^{-6}$
  * Crack-tip location & path: $x_{\text{tip}} = \dots\,\text{mm}$, $y = \dots\,\text{mm}$
- **Fracture Response Comparison:**
  * Initial stiffness: $K_0 = \dots\,\text{kN/mm}$ ($\dots\%$ vs canonical reference)
  * Peak load: $F_{\max} = \dots\,\text{kN}$ at $u = \dots\,\text{mm}$ ($\dots\%$ vs reference)
  * Post-peak load drop: $RF_{\text{final}} = \dots\,\text{N}$ ($\dots\%$ softened)
- **Gate Evaluation Verdict:** Gate C1 [PASS / FAIL] | Gate C2 [NOT ACTIVATED / PASS / FAIL]
```

---

## 10. Reconciliation of Project Authorization & Supervisor Review Status

1. **Gate 6B Status:** Formally `GATE6B_EVALUATION_COMPLETE_READY_FOR_SUPERVISOR_SIGNOFF`. Method B is completely evaluated across 14,483 elements, eliminating the artificial force plateau and reducing external work by $31.49\%$. It is ready for formal sign-off during the meeting on **Thursday, 22 October 2026 at 10:00 CEST**.
2. **Gate 6C Status:** Formally **ON HOLD PENDING SUPERVISOR REVIEW**. Milestone 1 (mesh refinement) and Milestone 2 (offline mathematical state transfer) are verified offline, but Milestone 3 (solver continuation) has not been achieved. Gate 6C must NOT auto-promote.
3. **Execution Safety Boundary:**
   - Zero Abaqus solver runs or PBS job submissions are permitted.
   - Production UEL `f42_mixed_uel.for` (`CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6`) remains strictly frozen and unmodified.
   - All research recommendations and candidate paths are submitted for supervisor review and determination.
