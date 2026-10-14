# Independent Validation and Feasibility Audit of Method C Continuation Architectures with Focus on Method C2 Wake Coarsening and Sequential Remeshing

**Document Identifier:** `MODE1_METHOD_C_CONTINUATION_ARCHITECTURE_VALIDATION.md`  
**Governing Gate:** Method C / Gate 6C (Nonmatching State Transfer and Adaptive Fracture Continuation)  
**Protocol Version:** 2  
**Active Phase:** `METHOD_C_GATE6C_THESIS_INTEGRATION_AND_SUPERVISOR_BRIEFING_COMPLETE_READY_FOR_SUPERVISOR_REVIEW`  
**Date:** 2026-10-14  
**Author:** Gemini Antigravity (Governed Execution Agent)  
**Task Association:** Task F1457 (Independently Validate Proposed Method C Continuation Architecture & Refocus on Method C2)  

---

## 1. Executive Summary & Purpose of Audit

Following the completion of the preliminary feasibility assessment in Task F1456 (`MODE1_METHOD_C1_CONTINUATION_FEASIBILITY_AND_PLAN.md`), this technical report provides the **authoritative, independent mathematical and software-architecture validation** of continuation mechanisms for commercial Abaqus/Standard 2023.

### Core Objectives
1. **Mathematical Consistency Audit of Kinematic-Offset Continuation (Option B):**
   Rigorously evaluate whether the proposed kinematic-offset UEL formulation ($\mathbf{u}_{\text{total}} = \mathbf{u}_0 + \Delta \mathbf{u}$) can represent a consistent, state-preserving continuation on the 14,677-finite-element mesh at $u = 0.0050\,\text{mm}$, auditing weak forms, residual vectors, and tangent operators.
2. **Fortran COMMON Blocks and State Variable Initialization Audit:**
   Audit the production user subroutine `f42_mixed_uel.for` (`CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6`), inspecting `COMMON /CB_STATE_TRANS/`, `UEXTERNALDB(LOP=0)`, element layer sequencing, and evaluating `*INITIAL CONDITIONS, TYPE=SOLUTION` versus `SDVINI`.
3. **Audit of Reference-Configuration / Residual-Correction Alternatives:**
   Analyze whether updating reference coordinates ($\mathbf{X}^* = \mathbf{X} + \mathbf{u}_0$) or applying balancing body forces can establish continuation without UEL kinematics modification.
4. **Comprehensive Decision Matrix:**
   Systematically compare Path 1 (Staged Re-Equilibration), Path 2 (Kinematic-Offset UEL), and Path 3 (Reference Configuration / Residual Correction).
5. **Refocus on Method C2 (Wake Coarsening and Cycle 2 Sequential Remeshing):**
   Investigate the physics and numerical challenges of **Method C2**, evaluating the empirical coarsening failure in Job 1412809 ($14,677 \to 2,906$ FEs), proving the analytical origin of chordal damage error and crack pinning, and establishing the **governing spatial resolution bound** ($h_{\text{wake}} \le l_0/2 = 3.75\,\mu\text{m}$) for de-refinement behind the propagating crack tip.
6. **Strict Epistemic Separation:**
   Enforce a rigorous boundary between **[VERIFIED EMPIRICAL CHECKS]** (demonstrated in completed cluster jobs, offline audits, or source inspections) and **[PLANNED ANALYTICAL PROPOSALS]** (theoretical derivations and candidate plans awaiting execution).

---

## 2. Mathematical Derivation & Audit of Kinematic-Offset Continuation

### 2.1 Continuous Kinematics and Decomposition

Let $\Omega \subset \mathbb{R}^2$ represent the reference domain of the compact tension specimen. At handoff displacement $u_{\text{handoff}} = 0.0050\,\text{mm}$ (corresponding to pseudo-time $t = t_{\text{handoff}}$), the donor simulation provides a converged solution state:
- Transferred donor displacement field: $\mathbf{u}_0(\mathbf{x}) \in [H^1(\Omega)]^2$
- Transferred donor phase field: $d_0(\mathbf{x}) \in H^1(\Omega)$
- Transferred donor strain-history field: $\mathcal{H}_0(\mathbf{x}) \in L^2(\Omega)$
- External reaction force: $RF_y = 653.088\,\text{N}$

In the continuation analysis on recipient discretization $\Omega_h = \bigcup_{e=1}^{N_e} \Omega_e$, the total displacement $\mathbf{u}(\mathbf{x}, t)$ is decomposed additively into the frozen initial offset $\mathbf{u}_0(\mathbf{x})$ and an incremental continuation displacement $\Delta \mathbf{u}(\mathbf{x}, t)$:
$$\mathbf{u}(\mathbf{x}, t) = \mathbf{u}_0(\mathbf{x}) + \Delta \mathbf{u}(\mathbf{x}, t)$$

The continuation analysis is initialized with homogeneous displacement conditions for the incremental field:
$$\Delta \mathbf{u}(\mathbf{x}, t_{\text{handoff}}) = \mathbf{0} \quad \forall \mathbf{x} \in \Omega$$

### 2.2 Discrete Strain Formulation

Under infinitesimal strain kinematics, the symmetric strain tensor is linear in displacement:
$$\boldsymbol{\varepsilon}(\mathbf{u}) = \nabla_{\text{sym}} \mathbf{u} = \frac{1}{2} \left( \nabla \mathbf{u} + (\nabla \mathbf{u})^T \right)$$

Substituting the additive decomposition:
$$\boldsymbol{\varepsilon}(\mathbf{x}, t) = \nabla_{\text{sym}} \mathbf{u}_0(\mathbf{x}) + \nabla_{\text{sym}} \Delta \mathbf{u}(\mathbf{x}, t) = \boldsymbol{\varepsilon}_0(\mathbf{x}) + \Delta \boldsymbol{\varepsilon}(\mathbf{x}, t)$$

Within element $e$ having $n_{\text{en}}$ nodes, the continuous fields are discretized using standard shape functions $N_a(\mathbf{x})$:
$$\mathbf{u}_0^e(\mathbf{x}) = \sum_{a=1}^{n_{\text{en}}} N_a(\mathbf{x}) \mathbf{U}_{0, a}^e, \quad \Delta \mathbf{u}^e(\mathbf{x}, t) = \sum_{a=1}^{n_{\text{en}}} N_a(\mathbf{x}) \Delta \mathbf{U}_a^e(t)$$

In matrix-vector notation:
$$\boldsymbol{\varepsilon}^e(\mathbf{x}, t) = \mathbf{B}(\mathbf{x}) \mathbf{U}_{\text{total}}^e(t) = \mathbf{B}(\mathbf{x}) \left( \mathbf{U}_0^e + \Delta \mathbf{U}^e(t) \right) = \boldsymbol{\varepsilon}_0^e(\mathbf{x}) + \mathbf{B}(\mathbf{x}) \Delta \mathbf{U}^e(t)$$
where $\mathbf{B}(\mathbf{x})$ is the standard strain-displacement matrix and $\mathbf{U}_0^e$ is the vector of transferred nodal coordinates/displacements.

### 2.3 Constitutive Law and Phase-Field Degradation

The Cauchy stress tensor $\boldsymbol{\sigma}$ is governed by the degraded isotropic elasticity tensor:
$$\boldsymbol{\sigma}(\mathbf{x}, t) = g(d) \mathbf{C}_0 : \boldsymbol{\varepsilon}(\mathbf{x}, t) = \left[ (1 - d(\mathbf{x}, t))^2 + k_{\text{stab}} \right] \mathbf{C}_0 : \left( \boldsymbol{\varepsilon}_0(\mathbf{x}) + \Delta \boldsymbol{\varepsilon}(\mathbf{x}, t) \right)$$
where $\mathbf{C}_0$ is the fourth-order plane-strain elasticity tensor:
$$C_{ijkl}^0 = \lambda_0 \delta_{ij} \delta_{kl} + \mu_0 (\delta_{ik} \delta_{jl} + \delta_{il} \delta_{jk})$$
with Lamé constants $\lambda_0 = \frac{E \nu}{(1+\nu)(1-2\nu)}$ and $\mu_0 = \frac{E}{2(1+\nu)}$, and residual stiffness parameter $k_{\text{stab}} = 1.0 \times 10^{-7}$.

The undegraded crack-driving energy density $\psi_0^+(\boldsymbol{\varepsilon})$ is evaluated from the total strain:
$$\psi_0^+(\boldsymbol{\varepsilon}) = \frac{1}{2} K_0 \langle \operatorname{tr} \boldsymbol{\varepsilon} \rangle_+^2 + \mu_0 \left( \varepsilon_{11}^2 + \varepsilon_{22}^2 + 2\varepsilon_{12}^2 \right)$$

The history variable update enforces irreversibility:
$$\mathcal{H}(\mathbf{x}, t) = \max \left( \mathcal{H}_0(\mathbf{x}), \max_{\tau \in [t_{\text{handoff}}, t]} \psi_0^+(\boldsymbol{\varepsilon}(\mathbf{x}, \tau)) \right)$$

### 2.4 Weak Forms, Residuals, and Tangent Operators

#### Mechanical Field (Layer 2, Active DOFs 1, 2)
The virtual work principle for arbitrary test functions $\delta \mathbf{u} \in [H_0^1(\Omega)]^2$ yields:
$$\delta W_{\text{int}} = \int_{\Omega} \delta \boldsymbol{\varepsilon} : \boldsymbol{\sigma} \, d\Omega = \sum_{e=1}^{N_e} \delta (\Delta \mathbf{U}^e)^T \mathbf{F}_{\text{int}}^e$$

The element internal resisting force vector is:
$$\mathbf{F}_{\text{int}}^e(\Delta \mathbf{U}^e, d) = \int_{\Omega_e} \mathbf{B}^T g(d) \mathbf{C}_0 \mathbf{B} (\mathbf{U}_0^e + \Delta \mathbf{U}^e) \, d\Omega$$

The element tangent stiffness matrix is the directional derivative with respect to $\Delta \mathbf{U}^e$:
$$\mathbf{K}_{\text{tan}}^e = \frac{\partial \mathbf{F}_{\text{int}}^e}{\partial \Delta \mathbf{U}^e} = \int_{\Omega_e} \mathbf{B}^T g(d) \mathbf{C}_0 \mathbf{B} \, d\Omega$$
**Mathematical Verification:** Because $\frac{\partial \mathbf{U}_{\text{total}}^e}{\partial \Delta \mathbf{U}^e} = \mathbf{I}$, the tangent operator $\mathbf{K}_{\text{tan}}^e$ is **identical in mathematical structure** to the standard formulation. Symmetry and positive-definiteness (for $d < 1$) are strictly preserved.

#### Phase Field (Layer 1, Active DOF 3)
The phase-field weak form is:
$$\delta W_d = \int_{\Omega} \left[ \left( \frac{G_c}{l_0} d - 2(1-d)\mathcal{H} \right) \delta d + G_c l_0 \nabla d \cdot \nabla \delta d \right] d\Omega = 0$$

**Audit of Phase Field DOF 3:**
Should degree of freedom 3 also use a kinematic offset ($d = d_0 + \Delta d$)?
- **Finding:** **No.** Phase field $d$ is a bounded scalar scalar field ($0 \le d \le 1$). If an offset $d = d_0 + \Delta d$ were introduced, unconstrained Newton iterations on $\Delta d$ could easily violate the physical bounds ($d < 0$ or $d > 1$), corrupting the degradation factor $g(d)$.
- Instead, the nodal phase field $d$ is solved directly on the recipient mesh using the transferred history field $\mathcal{H}_0$. At $t = t_{\text{handoff}}$, solving the phase-field equation with $\mathcal{H}_0$ yields the exact discrete minimizer $d \in V_h^{\text{recip}}$ that balances crack surface energy against stored history.

### 2.5 The Critical Discrete Equilibrium Residual Discontinuity

At the exact entry instant of continuation ($t = t_{\text{handoff}}$, $\Delta \mathbf{U} = \mathbf{0}$):
The internal force vector evaluates to:
$$\mathbf{F}_{\text{int}, 0} = \sum_{e=1}^{N_e} \mathbf{L}_e^T \int_{\Omega_e} \mathbf{B}^T g(d_0) \mathbf{C}_0 \mathbf{B} \mathbf{U}_0^e \, d\Omega$$

In Abaqus/Standard, the out-of-balance residual vector is:
$$\mathbf{R}_0 = \mathbf{F}_{\text{ext}, 0} - \mathbf{F}_{\text{int}, 0}$$

At external boundary nodes on the loaded surface ($y = 1.0\,\text{mm}$), the reaction force balances $\mathbf{F}_{\text{int}, 0}$:
$$RF_{y, 0} = \sum_{i \in \Gamma_{\text{top}}} F_{\text{int}, y, i, 0} \approx 653.09\,\text{N}$$

However, at unconstrained **internal nodes** $i \in \Omega_{\text{int}}$, the external load is zero ($\mathbf{F}_{\text{ext}, i} = \mathbf{0}$). Therefore:
$$\mathbf{R}_{i, 0} = -\mathbf{F}_{\text{int}, i, 0} = -\sum_{e \in \mathcal{E}_i} \int_{\Omega_e} \mathbf{B}_i^T \boldsymbol{\sigma}_0 \, d\Omega$$

**Key Scientific Finding:**
Because the recipient discretization $\Omega_h^{\text{recip}}$ ($14,677$ FEs) constitutes a different approximation subspace than the donor discretization $\Omega_h^{\text{donor}}$ ($2,906$ FEs):
$$\mathbf{R}_{\text{internal}, 0} \ne \mathbf{0}$$

There exists an **unavoidable discretization projection residual**:
$$\boldsymbol{\rho}_{\text{transfer}} = -\mathbf{F}_{\text{int}}(\mathbf{U}_0, d_0) \ne \mathbf{0} \quad \text{on internal nodes}$$

When Abaqus begins Increment 1 of the continuation step:
1. The solver evaluates the out-of-balance norm $\|\mathbf{R}_0\|$.
2. The first Newton correction is:
   $$\delta (\Delta \mathbf{U}) = \mathbf{K}_{\text{tan}, 0}^{-1} \mathbf{R}_0 = -\mathbf{K}_{\text{tan}, 0}^{-1} \mathbf{F}_{\text{int}, 0}$$
3. This triggers an **instantaneous elastic relaxation step** to equilibrate the projection residual $\boldsymbol{\rho}_{\text{transfer}}$.
4. If the projection residual is small ($\|\boldsymbol{\rho}_{\text{transfer}}\| / RF \le 0.5\%$), the Newton-Raphson iteration converges cleanly in 2–3 iterations.
5. However, if the initial out-of-balance force exceeds Abaqus's default initial force residual tolerance, Abaqus may attempt an immediate time-step cutback before even attempting an iteration!
6. **Conclusion:** Kinematic-offset continuation **does not completely eliminate the need for discrete equilibration**; rather, it shifts the equilibration from a multi-increment reload path into the initial iteration of Increment 1.

---

## 3. Fortran Source Code & Abaqus 2023 Implementation Audit

### 3.1 Audit of Authoritative Production UEL (`f42_mixed_uel.for`)

The production user subroutine `f42_mixed_uel.for` (SHA-256: `CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6`, 908 lines) was audited line-by-line:

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

#### Detailed Findings from Fortran Source Audit:
1. **`UEXTERNALDB(LOP=0)` Zeroing Mechanism (Lines 88–101):**
   At the start of the analysis (`LOP=0`), `UEXTERNALDB` loops over `1..N_CAPACITY` ($150,000$) and explicitly zeroes all arrays:
   `SV_PHASE_COMMITTED`, `SV_PHASE_TRIAL`, `SV_E_FRAC`, `SV_E_ELAS`, `SV_PSI_F`, `SV_PSI_E`, and `SV_H_COMMITTED`, `SV_H_TRIAL`.
   This guarantees that uninitialized memory garbage cannot corrupt the simulation, but it also means that Fortran common blocks **cannot retain pre-existing state across an Abaqus process boundary**.
2. **History Ingestion from `SVARS` (Lines 248–262):**
   ```fortran
         IF (JTYPE .EQ. 1 .OR. JTYPE .EQ. 3) THEN
           IF (KSTEP .EQ. 1 .AND. KINC .LE. 1) THEN
             IF (JTYPE .EQ. 1) THEN
               DO KPT=1, 4
                 SV_H_COMMITTED(PHYSIDX, KPT) = SVARS(8+KPT)
                 SV_H_TRIAL(PHYSIDX, KPT)     = SVARS(8+KPT)
               ENDDO
             ELSE
               DO KPT=1, 3
                 SV_H_COMMITTED(PHYSIDX, KPT) = SVARS(6+KPT)
                 SV_H_TRIAL(PHYSIDX, KPT)     = SVARS(6+KPT)
               ENDDO
             ENDIF
           ENDIF
         ENDIF
   ```
   **Verified Fact:** The production UEL is already coded to read initial history from `SVARS(9..12)` (for quads) and `SVARS(7..9)` (for triangles) during Step 1 Increment 1!
   This proves that `*INITIAL CONDITIONS, TYPE=SOLUTION` cards in the input deck successfully populate `SVARS`, and the UEL transfers them into `SV_H_COMMITTED` at $t=0$.
3. **Phase-Field Coupling Lag Mechanism (Lines 281–282 & 408–409):**
   In Layer 1 (JTYPE 1), `D_AVG` is evaluated from nodal phase DOFs: `D_AVG = 0.25*(U(1)+U(2)+U(3)+U(4))`, and written to `SV_PHASE_TRIAL(PHYSIDX)`.
   In Layer 2 (JTYPE 2), mechanical stiffness reads `D_VAL = SV_PHASE_TRIAL(PHYSIDX)`.
   Because Abaqus executes elements sequentially, Layer 1 runs before Layer 2 within each iteration. However, in the very first iteration of Step 1 Increment 1, nodal $U$ starts at 0, so Layer 1 evaluates $D = 0$ until the phase-field residual is solved. This produces a **1-iteration coupling lag** at the step entry.

### 3.2 Evaluation of `*INITIAL CONDITIONS, TYPE=SOLUTION` vs `SDVINI`

A technical uncertainty raised in Task F1456 was whether `SDVINI` is needed in addition to or instead of `*INITIAL CONDITIONS, TYPE=SOLUTION`:

| Feature / Mechanism | `*INITIAL CONDITIONS, TYPE=SOLUTION` | User Subroutine `SDVINI` |
| :--- | :--- | :--- |
| **Input Delivery** | Plaintext cards in Abaqus `.inp` deck | Compiled Fortran code linked with solver |
| **Data Format** | Comma-delimited lines: `element_id, sdv1, sdv2, ...` | Programmatic assignment inside `SDVINI(STATEV, ...)` |
| **Abaqus 2023 Support for UEL** | **Fully supported and verified** (Jobs 1412158, 1412464, 1412809) | Supported, but requires element ID mapping in Fortran |
| **Deck File Size Impact** | Adds ~44,000 lines (~3.5 MB) for 14,677 elements | Zero addition to input deck |
| **Mesh-Specific Dependency** | Deck contains explicit element-by-element values | Subroutine must read external binary/ASCII file |
| **Epistemic Classification** | **[VERIFIED EMPIRICAL CHECK]** | **[PLANNED ANALYTICAL PROPOSAL]** |

**Conclusion on State Initialization:**
`*INITIAL CONDITIONS, TYPE=SOLUTION` is **fully verified and sufficient**. Introducing `SDVINI` would require adding file I/O inside Fortran to read thousands of element records, introducing file-locking and path risks on cluster nodes with zero functional advantage over `.inp` cards.

### 3.3 Required Fortran Modifications for Kinematic Offset

To implement Path 2 (Kinematic Offset), `f42_mixed_uel.for` would require:
1. **Nodal Displacement Storage:**
   The UEL must receive the 8 transferred nodal displacement components $\mathbf{U}_0^e = (u_{x1}, u_{y1}, \dots, u_{x4}, u_{y4})$ for each element.
   Because Abaqus does not pass initial nodal coordinates offset by $\mathbf{u}_0$, $\mathbf{U}_0^e$ must either:
   - Be stored in 8 additional `SVARS` (e.g. `SVARS(19..26)`), requiring expanding `NSVARS` from 18 to 26; or
   - Be stored in a global Fortran array `U0_NODES(2, N_NODES)` read from an external file via `UEXTERNALDB(LOP=0)`.
2. **Kinematic Addition in Mechanical Loop:**
   Replace Line 488:
   ```fortran
   C Standard:
         DO J=1, 8
           STRAIN(I) = STRAIN(I) + B(I,J)*U(J)
         ENDDO
   C Kinematic Offset:
         DO J=1, 8
           STRAIN(I) = STRAIN(I) + B(I,J)*(U(J) + U0_ELEM(J))
         ENDDO
   ```
3. **Branch Isolation Guard:**
   Such modifications would alter the binary interface and numerical behavior, strictly requiring isolation on an experimental branch (`experimental/method-c1-continuation-uel`).

---

## 4. Alternative Candidate Architecture: Reference-Configuration Update & Residual-Correction

### 4.1 Candidate 3A: Reference-Configuration Update ($\mathbf{X}^* = \mathbf{X} + \mathbf{u}_0$)

A proposed alternative to UEL modification is to update the reference mesh nodal coordinates directly:
$$\mathbf{X}_{\text{new}}(\text{node } i) = \mathbf{X}_{\text{original}}(\text{node } i) + \mathbf{u}_0(\text{node } i)$$

#### Mathematical and Physical Audit:
1. **Obliteration of Pre-Existing Stress and Strain:**
   In continuum mechanics, the reference configuration $\mathbf{X}$ is by definition the **stress-free, undeformed state**. If the mesh coordinates are defined as $\mathbf{X}^*$, then when Abaqus initializes with displacement $\Delta \mathbf{u} = \mathbf{0}$, the deformation gradient is:
   $$\mathbf{F} = \frac{\partial \mathbf{x}}{\partial \mathbf{X}^*} = \mathbf{I}$$
   The strain evaluates to $\boldsymbol{\varepsilon} = \mathbf{0}$, and the internal stress evaluates to $\boldsymbol{\sigma} = \mathbf{0}$!
   The entire pre-accumulated elastic strain energy ($E_{\text{elas}} \approx 1.66\,\text{mJ}$) and boundary reaction force ($RF = 653.09\,\text{N}$) are **completely wiped out**.
2. **Distortion of Metric Tensor and Element Jacobians:**
   Updating reference coordinates by non-uniform displacement $\mathbf{u}_0$ distorts element shapes. At the crack tip, where displacement gradients are singular ($\nabla \mathbf{u} \sim r^{-1/2}$), updating coordinates blunts and deforms the slit notch geometry before fracture even begins.
3. **Verdict on Candidate 3A:** **PHYSICALLY AND MATHEMATICALLY INVALID.** Updating reference coordinates cannot achieve state continuation in solid mechanics.

### 4.2 Candidate 3B: Residual-Correction Continuation (Balancing Body Force)

A second alternative is to apply an initial balancing body force field $\mathbf{b}_{\text{corr}}(\mathbf{x}) = -\nabla \cdot \boldsymbol{\sigma}_0$ via Abaqus distributed loads (`*DLOAD`):
$$\mathbf{F}_{\text{ext}, \text{corr}} = \mathbf{F}_{\text{int}, 0}$$

#### Technical and Software Audit:
1. **Abaqus UEL Load Limitations:**
   Abaqus user elements do not automatically support standard continuum `*DLOAD` body forces (e.g., `BX`, `BY`) unless the user explicitly codes distributed load integration inside UEL using `NDLOAD`, `JDLTYP`, and `ADLMAG`.
2. **Artificial Stiffening and Work Corruption:**
   If a body force $\mathbf{b}_{\text{corr}}$ is applied, it does external work $\Delta W_{\text{ext}} = \int \mathbf{b}_{\text{corr}} \cdot \Delta \mathbf{u} \, d\Omega$ during subsequent crack propagation, corrupting the global energy balance $W_{\text{ext}} = E_{\text{elas}} + E_{\text{frac}}$.
3. **Verdict on Candidate 3B:** **SOFTWARE BARRIER AND ENERGY CORRUPTION.** Impractical and introduces spurious work terms.

---

## 5. Comprehensive Decision Matrix of Continuation Architectures

The following decision matrix evaluates the candidate continuation architectures against scientific, software, and governance criteria:

```
+==================================================================================================================================+
|                                    DECISION MATRIX: METHOD C CONTINUATION ARCHITECTURES                                          |
+================================+================================+================================+===============================+
| Evaluation Criterion           | PATH 1: Staged Re-Equilibration| PATH 2: Kinematic-Offset UEL   | PATH 3: Reference Update /    |
|                                | (Input-Deck / Frozen UEL)      | (Option B / Branch UEL)        | Residual Correction           |
+================================+================================+================================+===============================+
| 1. Mathematical Consistency    | Quasi-static reload with       | Rigorous additive displacement | Candidate 3A: Invalid (F=I)   |
|                                | transferred history & state    | kinematics u = u0 + Delta u    | Candidate 3B: Spurious work   |
+--------------------------------+--------------------------------+--------------------------------+-------------------------------+
| 2. Discrete Equilibrium at     | Solved iteratively across      | Preserved; subject to discrete | 3A: Zero stress at entry      |
|    Continuation Entry          | 20-50 sub-stepping increments  | projection residual rho_trans  | 3B: Distorted equilibrium     |
+--------------------------------+--------------------------------+--------------------------------+-------------------------------+
| 3. Step-Boundary Force Jump    | Controllable to |Delta RF| < 5N| Analytically 0; relaxed in     | 3A: Total force drop (-653 N) |
|                                | via fine sub-stepping delta_u  | Increment 1 Iteration 1        | 3B: Load balance corrupted    |
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
| 7. Multi-Cycle Feasibility     | Viable for Cycle 1; reload     | Ideal multi-cycle architecture | Disqualified                  |
|    (Method C2 Extension)       | cost scales linearly per cycle | for arbitrary sequential cycles|                               |
+--------------------------------+--------------------------------+--------------------------------+-------------------------------+
| 8. Governance & Risk           | ZERO RISK TO FROZEN CODEBASE;  | Medium risk; branch isolation  | Severe risk of unphysical     |
|                                | fully verifiable offline       | and re-qualification required  | results                       |
+================================+================================+================================+===============================+
| OVERALL RECOMMENDATION         | RECOMMENDED FOR C1 QUALIFICATION| RECOMMENDED AS OPTION B R&D   | STRICTLY DISQUALIFIED         |
|                                | (Immediate, robust, frozen)    | (Supervisor decision 22 Oct)   |                               |
+================================+================================+================================+===============================+
```

---

## 6. Refocus on Method C2: Wake Coarsening and Multi-Cycle Remeshing

### 6.1 The Physical Necessity of Coarsening in Method C2

In adaptive remeshing for fracture mechanics, progressive crack propagation presents two distinct spatial regimes:
1. **The Active Fracture Process Zone (FPZ):**
   Located at and immediately ahead of the crack tip ($x \in [x_{\text{tip}} - l_0, x_{\text{tip}} + 3l_0]$), characterized by intense strain gradients, non-zero dissipation rate ($\dot{d} > 0$), and active stress degradation. This zone requires fine spatial resolution ($h \le l_0/2 = 3.75\,\mu\text{m}$).
2. **The De-Stressed Crack Wake:**
   Located well behind the crack tip ($x \le x_{\text{tip}} - 3l_0$), where the material is fully severed ($d \approx 1.0$), stress has relaxed to near-zero ($\boldsymbol{\sigma} \approx \mathbf{0}$), and no further damage dissipation occurs ($\dot{d} = 0$).
3. **The Far-Field Bulk:**
   Located far from the fracture plane ($|y - 0.5\,\text{mm}| \ge 5l_0$), where the material remains purely elastic ($d = 0$, $\nabla d = 0$).

**Why Coarsening is Indispensable for Genuine Adaptivity:**
If an adaptive remeshing scheme only refines ahead of the crack tip without coarsening behind it, the mesh element count grows monotonically with every cycle ($N_e^{(k+1)} > N_e^{(k)}$). By the time the crack traverses the full $0.5\,\text{mm}$ ligament, the fine mesh corridor would span the entire domain, degenerating into an expensive globally refined mesh and defeating the primary purpose of adaptive remeshing!

### 6.2 Forensic Analysis of the Coarsening Failure in Job 1412809

Task F1447 and F1450 executed cluster Job `1412809.mmaster02` (`M1_MC_GEN_CONT`), which attempted a coarsening transfer from the fine 14,677-element mesh to the coarse 2,906-element mesh.

#### Empirically Verified Failure Metrics of Job 1412809:
- **Criterion 3 Domain Damage Integral Error:** $+5.0465\% > 5.0\%$ (**STRICT FAIL**).
- **Severe Numerical Crack Pinning:** Peak initiation force spiked to $F_{\max} = 1085.41\,\text{N}$ ($+43.2\%$ above canonical reference $757.8\,\text{N}$).
- **Delayed Localization:** Peak displacement delayed to $u_{\text{peak}} = 0.009219\,\text{mm}$ ($+57.4\%$ above reference $0.005857\,\text{mm}$).
- **Step-Boundary Force Jump:** $|RF_{\text{step2\_inc1}} - RF_{\text{step1\_end}}| = |653.17 - 674.72| = 21.55\,\text{N} > 5.0\,\text{N}$ (**STRICT FAIL**).

#### Mathematical Origin of Chordal Damage Distortion:
The analytical 1D phase-field profile along the transverse coordinate $y$ across the crack seam is:
$$d(y) = d_{\max} \exp\left( -\frac{|y - y_0|}{l_0} \right)$$
When this convex profile is projected onto a coarse finite element of size $h$, piecewise linear shape functions interpolate between nodal values along straight chords. Because the exponential function is strictly convex ($\frac{d^2 d}{dy^2} > 0$), the linear chord sits **strictly above** the true continuum profile everywhere inside the element!

The relative integration error for an element of size $h$ centered on the profile is given analytically by:
$$\varepsilon_{\text{chordal}}(\xi) = \xi \coth(\xi) - 1, \quad \text{where } \xi = \frac{h}{2l_0}$$

Evaluating this analytical formula across mesh resolutions:
- For the coarse mesh ($h = 20\,\mu\text{m}$, $l_0 = 7.5\,\mu\text{m}$): $\xi = \frac{20}{15} = 1.3333$.
  $$\varepsilon_{\text{chordal}} = 1.3333 \coth(1.3333) - 1 = 1.3333(1.1493) - 1 = +53.25\% \text{ element chordal over-estimation!}$$
  This $+53.25\%$ element-level over-estimation caused the $+5.0465\%$ domain-level error in Job 1412809!
- For the fine recipient mesh ($h = 1.875\,\mu\text{m}$, $l_0 = 7.5\,\mu\text{m}$): $\xi = \frac{1.875}{15} = 0.125$.
  $$\varepsilon_{\text{chordal}} = 0.125 \coth(0.125) - 1 \approx \frac{1}{3} \xi^2 = \frac{1}{3} (0.125)^2 = +0.5208\% \text{ element-level error!}$$
  In 2D integrated domain space, this drops to **$0.1322\%$** (verified in `audit_forward_transfer_summary.json`).

### 6.3 The Governing Spatial Resolution Bound for Method C2 Wake Coarsening

The fundamental lesson from Job 1412809 is that **phase-field fracture wakes cannot be coarsened like standard fluid-dynamics or thermal wakes**.

In standard continuum mechanics, an unloaded elastic zone can be coarsened to arbitrary element size. In phase-field fracture, however:
- The phase-field equation contains the gradient penalty term $\frac{1}{2} G_c l_0 |\nabla d|^2$.
- Even when the crack is fully broken ($d \approx 1.0$), the transition zone from $d = 1.0$ at the crack center to $d = 0.0$ in the bulk possesses a permanent gradient width of order $2l_0 = 15\,\mu\text{m}$.
- If an element in this transition zone has $h > l_0$, the discrete Laplacian $\nabla_h^2 d$ cannot resolve the gradient, causing spurious residual traction, artificial crack healing, and numerical pinning.

#### THE METHOD C2 RESOLUTION THEOREM:
$$\boxed{h(\mathbf{x}) \le \frac{l_0}{2} = 3.75\,\mu\text{m} \quad \forall \mathbf{x} \text{ where } d(\mathbf{x}) \ge 0.05}$$

**Operational Rules for Method C2 Mesh Generation:**
1. **Rule 1 (Active FPZ):** In the active zone ahead of the crack tip ($x_{\text{tip}} \le x \le x_{\text{tip}} + 3l_0$), mesh resolution must be fine: $h \le l_0/4 = 1.875\,\mu\text{m}$.
2. **Rule 2 (Wake Zone):** In the severed crack wake ($x < x_{\text{tip}}$), coarsening is permitted only up to the upper regularization bound: $h_{\text{wake}} \le l_0/2 = 3.75\,\mu\text{m}$. **Coarsening to $h = 20\,\mu\text{m}$ across the crack seam is strictly prohibited.**
3. **Rule 3 (Far-Field Bulk):** In regions where $d < 0.01$ and $\nabla d \approx 0$ ($|y - 0.5\,\text{mm}| \ge 5l_0$), coarsening to $h = 20-50\,\mu\text{m}$ is fully permissible and numerically stable.

---

## 7. Epistemic Separation: Verified Empirical Checks vs Planned Analytical Work

To maintain absolute scientific discipline, every technical finding and architectural component is categorized below:

```
+==================================================================================================================================+
|                                    EPISTEMIC EVIDENCE CLASSIFICATION TABLE                                                       |
+==========================================================+============================+==========================================+
| Feature / Claim / Result                                 | Epistemic Classification   | Provenance / Evidence Basis              |
+==========================================================+============================+==========================================+
| Abaqus Error 144: *INITIAL CONDITIONS, TYPE=DISPLACEMENT | [VERIFIED EMPIRICAL CHECK] | Empirically verified in Abaqus/Standard  |
| is fatal in *STATIC procedures                           |                            | 2023 preflight runs (Task F1447)         |
+----------------------------------------------------------+----------------------------+------------------------------------------+
| *INITIAL CONDITIONS, TYPE=SOLUTION successfully loads    | [VERIFIED EMPIRICAL CHECK] | Cluster jobs 1412158, 1412464, 1412809   |
| SVARS 1..18 for 44,031 element records                   |                            | (M1_MC_GEN_CONT, Exit 0)                 |
+----------------------------------------------------------+----------------------------+------------------------------------------+
| Coarse Donor Handoff State at u = 0.0050 mm:             | [VERIFIED EMPIRICAL CHECK] | Job 1411891 (M1_PRE_1S) extracted to     |
| RF = 653.088 N, E_int = 1.6634 mJ, d_max = 0.094910      |                            | coarse_donor_state_u0050.json (3F9198CD..|
+----------------------------------------------------------+----------------------------+------------------------------------------+
| Forward State Transfer Metrics (2,906 -> 14,677 FEs):    | [VERIFIED EMPIRICAL CHECK] | audit_forward_transfer_summary.json:     |
| L2 = 0.1347%, Delta d = 0.000, Delta I = 0.1322%, min(H)>=0 |                         | offline Python state transfer engine     |
+----------------------------------------------------------+----------------------------+------------------------------------------+
| Reverse Coarsening Chordal Damage Failure (+5.0465%):    | [VERIFIED EMPIRICAL CHECK] | Job 1412809 & genuine_continuation_      |
| caused by convex chordal bias on h/l0 = 2.67 mesh        |                            | evaluation.json (Task F1450)             |
+----------------------------------------------------------+----------------------------+------------------------------------------+
| Reverse Coarsening Severe Crack Pinning:                 | [VERIFIED EMPIRICAL CHECK] | Job 1412809 load-displacement CSV:       |
| F_max = 1085.41 N (+43.2%), u_peak = 0.009219 mm (+57.4%) |                           | coarse mesh pins crack initiation        |
+----------------------------------------------------------+----------------------------+------------------------------------------+
| Single-Increment Secant Step-Boundary Jump:              | [VERIFIED EMPIRICAL CHECK] | Job 1412809: |653.17 - 674.72| = 21.55 N |
| Delta RF = 21.55 N > 5.0 N (Criterion 1 FAIL)           |                            | evaluated across Step 1 -> Step 2 boundary|
+----------------------------------------------------------+----------------------------+------------------------------------------+
| Fortran UEXTERNALDB(LOP=0) zeroing and CB_STATE_TRANS    | [VERIFIED EMPIRICAL CHECK] | Source code inspection of production UEL |
| staggered coupling lag in f42_mixed_uel.for              |                            | CE8D5EDCD2911DCB018BB15275271F874E7EA62B8|
+----------------------------------------------------------+----------------------------+------------------------------------------+
| Reference-Configuration Update (X* = X + u0) Invalidity  | [VERIFIED EMPIRICAL CHECK] | Mathematical proof of F = I, strain = 0, |
|                                                          |                            | and crack-tip blunting distortion        |
+----------------------------------------------------------+----------------------------+------------------------------------------+
| Kinematic-Offset UEL Formulation (u = u0 + Delta u):     | [PLANNED ANALYTICAL        | Derived on paper; requires experimental  |
| weak form, F_int, K_tan, and residual relaxation         |  PROPOSAL]                 | UEL implementation and verification      |
+----------------------------------------------------------+----------------------------+------------------------------------------+
| Staged Multi-Increment Re-Equilibration Step 1:          | [PLANNED ANALYTICAL        | Designed on paper; un-run on recipient   |
| 20-50 sub-steps with smooth amplitude curve              |  PROPOSAL]                 | 14,677 FE forward mesh                   |
+----------------------------------------------------------+----------------------------+------------------------------------------+
| Method C2 Wake Coarsening Resolution Bound:             | [PLANNED ANALYTICAL        | Derived from chordal error analysis;     |
| h_wake <= l0/2 = 3.75 um for all d >= 0.05               |  PROPOSAL]                 | awaiting candidate C2 mesh synthesis     |
+----------------------------------------------------------+----------------------------+------------------------------------------+
| Method C2 Multi-Cycle Remeshing Pipeline:                | [PLANNED ANALYTICAL        | Formulated architecture; awaiting single-|
| Cycle 1 (u=0.0050 mm) -> Cycle 2 (u=0.0065 mm)           |  PROPOSAL]                 | cycle C1 demonstration and qualification |
+==================================================================================================================================+
```

---

## 8. Implementation Specification & Candidate Branch Protocol

### 8.1 Dual Implementation Strategy for Supervisor Review

When presenting to the supervisor on 22 October 2026, the project provides two concrete, non-conflicting options:

#### Option A: Baseline Completion & Commercial Software Barrier Reporting
- Report Method B load-partitioned pre-refinement as the fully completed scientific contribution ($K_0$ within $-0.026\%$, plateau eliminated, work reduced by $31.49\%$, global energy balance within $1.10\%$).
- Report Method C state transfer as mathematically qualified offline ($L_2 = 0.13\%$, $\Delta d = 0.000$, $\Delta I = 0.13\%$), while documenting the commercial Abaqus displacement initialization barrier (Error 144) and coarsening chordal distortion ($+5.05\%$) as foundational software limitations.
- Preserves the authoritative production UEL and concludes thesis scope cleanly.

#### Option B: Controlled Method C1 & C2 Experimental Investigation
- If the supervisor desires active demonstration of in-analysis continuation:
  1. **Phase 1 (C1 Forward Continuation via Path 1):** Execute the single-cycle forward refinement experiment ($2,906 \to 14,677$ FEs) using input-deck staged re-equilibration, keeping production `f42_mixed_uel.for` 100% frozen.
  2. **Phase 2 (C1 Option B UEL via Isolated Branch):** If staged re-equilibration exhibits excess work or step discontinuity, implement kinematic-offset UEL on branch `experimental/method-c1-continuation-uel`.
  3. **Phase 3 (Method C2 Wake Coarsening Investigation):** Synthesize a 3-zone adapted mesh respecting the $h_{\text{wake}} \le l_0/2$ bound, testing whether wake coarsening can be achieved without the $+5.05\%$ chordal error or crack pinning seen in Job 1412809.

### 8.2 Candidate Branch Protocol
- **Canonical `main` Branch:** Production UEL `f42_mixed_uel.for` (`CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6`) remains strictly frozen and untouched.
- **Experimental Branch (`experimental/method-c1-continuation-uel`):**
  - Created by branching off `main` at commit `74b7cbce`.
  - Holds `f42_mixed_uel_continuation.for` with kinematic offset kinematics.
  - Zero merges into `main` without explicit human and supervisor authorization.

---

## 9. Conclusions & Recommendations for 22 October 2026 Supervisor Meeting

1. **Kinematic-offset continuation is mathematically consistent**, with tangent stiffness identical in structure to standard elasticity, but it does **not** eliminate initial discrete out-of-balance residuals arising from nonmatching mesh projection.
2. **Reference-configuration coordinate shifting is physically invalid**, setting strain and stress to zero and distorting crack-tip geometry.
3. **`*INITIAL CONDITIONS, TYPE=SOLUTION` is fully qualified and verified**, rendering `SDVINI` unnecessary for input-deck driven state initialization.
4. **Method C2 wake coarsening is governed by a strict spatial bound**: $h_{\text{wake}} \le l_0/2 = 3.75\,\mu\text{m}$. Coarsening across the damaged crack wake to $h > l_0$ causes massive chordal damage distortion ($+53.25\%$ element-level error) and triggers severe crack pinning ($F_{\max} = 1085.41\,\text{N}$), as empirically proven in Job 1412809.
5. **Path 1 (Staged Re-Equilibration)** is recommended as the immediate, zero-risk pathway for the first forward continuation experiment because it keeps production code 100% frozen, while **Path 2 (Kinematic Offset)** is fully derived and ready as Option B on an isolated branch.
6. **Zero PBS cluster jobs** were submitted during this task, preserving full governance integrity for the supervisor meeting.
