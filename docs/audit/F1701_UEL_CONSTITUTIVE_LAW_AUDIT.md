# Task F1701: UEL Constitutive Law Source Code Audit

**Date**: 2026-11-09  
**Author**: Gemini Antigravity  
**Task ID**: `F1701-PK-SEC43-POINTWISE-STRESS-AND-HISTORY-AWARE-REMESH`  
**Target File**: `models/pandey_kumar_mode1/f42_mixed_uel.for`  
**File SHA-256**: `CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6`  
**Line Count**: 907 lines (Bitwise preserved and inviolable)

---

## 1. Executive Summary

This audit rigorously inspects the exact constitutive equations implemented in the production user element subroutine `f42_mixed_uel.for`. The findings establish the exact mathematical formulation of the mechanical Cauchy stress and tangent elasticity used during the authoritative fracture analysis (PBS Job 1421286), providing the authoritative mathematical foundation for Gate B (pointwise damage-informed stress recovery).

---

## 2. Element Architecture and Types

`f42_mixed_uel.for` implements a two-field staggered finite element formulation with four element types:

1. **`JTYPE = 1`**: 4-node quadrilateral phase-field element (DOF 8 / scalar phase-field $d$).
2. **`JTYPE = 2`**: 4-node quadrilateral mechanical element (DOFs 1, 2 / displacement $(u_x, u_y)$).
3. **`JTYPE = 3`**: 3-node triangular phase-field element (DOF 8 / scalar phase-field $d$).
4. **`JTYPE = 4`**: 3-node triangular mechanical element (DOFs 1, 2 / displacement $(u_x, u_y)$).
5. **`SUBROUTINE UMAT`**: Companion dummy elements (Layer 3, element IDs $> 2 \cdot N_{\mathrm{phys}}$) for CAE visualization. In the solver, `STRESS = 0.D0` and `DDSDDE(I,I) = 1.D-11`.

---

## 3. Exact Mechanical Constitutive Equations (`JTYPE = 2` & `JTYPE = 4`)

### 3.1 Kinematics and Strain Tensor
The standard 2D strain vector is computed from nodal displacements via the standard bilinear shape function derivatives:
$$
\boldsymbol{\varepsilon} = \begin{bmatrix} \varepsilon_{11} \\ \varepsilon_{22} \\ \gamma_{12} \end{bmatrix} = \mathbf{B} \mathbf{u}
$$
where $\gamma_{12} = 2 \varepsilon_{12}$ is engineering shear strain (`STRAIN(3)`).

### 3.2 Elasticity Tensor (Plane Strain Formulation)
The uncracked elasticity tensor is explicitly defined as **Plane Strain** linear elasticity (lines 411–415):
$$
C_{11}^0 = C_{22}^0 = \frac{E(1 - \nu)}{(1 + \nu)(1 - 2\nu)}
$$
$$
C_{12}^0 = \frac{E\nu}{(1 + \nu)(1 - 2\nu)}
$$
$$
C_{33}^0 = \frac{E}{2(1 + \nu)} = G
$$
For the Pandey & Kumar Section 4.3 benchmark:
- Young's modulus: $E = 210.0\,\mathrm{kN/mm^2} = 210.0\,\mathrm{GPa}$
- Poisson's ratio: $\nu = 0.30$
- $C_{11}^0 = C_{22}^0 = \frac{210.0 \times 0.70}{1.30 \times 0.40} = 282.6923077\,\mathrm{kN/mm^2}$
- $C_{12}^0 = \frac{210.0 \times 0.30}{1.30 \times 0.40} = 121.1538462\,\mathrm{kN/mm^2}$
- $C_{33}^0 = \frac{210.0}{2 \times 1.30} = 80.7692308\,\mathrm{kN/mm^2}$

### 3.3 Degradation Function and Stress Decomposition
In `f42_mixed_uel.for`, lines 408–410 and 416–420:
$$
g(d) = (1 - d)^2 + k_{\mathrm{res}}
$$
where $k_{\mathrm{res}} = 1.0 \times 10^{-7}$ (`PROPS(5)`).

The degraded elasticity matrix is computed by scalar multiplication:
$$
\mathbf{D}_{\mathrm{elas}} = g(d) \begin{bmatrix} C_{11}^0 & C_{12}^0 & 0 \\ C_{12}^0 & C_{22}^0 & 0 \\ 0 & 0 & C_{33}^0 \end{bmatrix}
$$
And the Cauchy stress is evaluated at each Gauss point as:
$$
\boldsymbol{\sigma} = \mathbf{D}_{\mathrm{elas}} \boldsymbol{\varepsilon} = g(d) \mathbf{D}_0 \boldsymbol{\varepsilon}
$$
Specifically:
$$
\sigma_{11} = g(d) \left( C_{11}^0 \varepsilon_{11} + C_{12}^0 \varepsilon_{22} \right)
$$
$$
\sigma_{22} = g(d) \left( C_{12}^0 \varepsilon_{11} + C_{11}^0 \varepsilon_{22} \right)
$$
$$
\sigma_{12} = g(d) \left( C_{33}^0 \gamma_{12} \right) = g(d) \cdot 2 G \varepsilon_{12}
$$

### 3.4 Crucial Finding: Absence of Stress Spectral Split in Equilibrium
- **Stress Decomposition**: There is **NO spectral or tensile/compressive split** in the mechanical stress tensor $\boldsymbol{\sigma}$ or in the internal force vector $\mathbf{f}_{\mathrm{int}} = \int \mathbf{B}^T \boldsymbol{\sigma} \, \mathrm{d}\Omega$. Both tensile and compressive components are degraded isotropically by $g(d)$.
- **Driving Energy Split**: A volumetric split is implemented **only in the damage driving energy** (`POS_M`, lines 516–526):
  $$
  \text{tr}(\boldsymbol{\varepsilon}) = \varepsilon_{11} + \varepsilon_{22}, \quad \langle \text{tr}(\boldsymbol{\varepsilon}) \rangle_+ = \max(0, \text{tr}(\boldsymbol{\varepsilon}))
  $$
  $$
  \psi_+ = \frac{1}{2} C_{12}^0 \langle \text{tr}(\boldsymbol{\varepsilon}) \rangle_+^2 + C_{33}^0 \left( \varepsilon_{11}^2 + \varepsilon_{22}^2 + 2\varepsilon_{12}^2 \right)
  $$
  which updates the history variable $\mathcal{H}_n = \max(\mathcal{H}_{n-1}, \psi_+)$.
- **Significance for Stress Recovery**: Pointwise constitutive recovery requires evaluating the exact isotropic degraded plane-strain Cauchy stress $\boldsymbol{\sigma} = g(d) \mathbf{D}_0 \boldsymbol{\varepsilon}$ at each integration point.

---

## 4. Verification and Mathematical Equivalence Matrix

| Property | UEL Implementation (`f42_mixed_uel.for`) | F1700 Recovery Model (20 Bins) | F1701 Pointwise Recovery |
| :--- | :--- | :--- | :--- |
| **Element Kinematics** | Bilinear Quad / Linear Tri | Standard CPE4 / CPE3 | Standard CPE4 / CPE3 |
| **Elastic Formulation** | Plane Strain | Plane Strain | Plane Strain |
| **Stiffness Discretization**| Continuous $g(d)$ per element | 20 piecewise-constant bins | Continuous $g(d(\mathbf{x}_{\mathrm{IP}}))$ |
| **$g(d)$ Form** | $(1-d)^2 + 10^{-7}$ | $(1-\bar{d}_k)^2 + 10^{-7}$ | $(1-d_{\mathrm{IP}})^2 + 10^{-7}$ |
| **Spectral Split in $\boldsymbol{\sigma}$**| None (Isotropic Degradation) | None (Isotropic Degradation) | None (Isotropic Degradation) |
| **Companion Force Parity**| Zero parallel force in UEL | Zero (solved in separate step) | Zero (post-processed recovery) |

---

## 5. Conclusion for Gate B Execution

Gate B requires computing pointwise Cauchy stress directly from the authentic integration point strains $\boldsymbol{\varepsilon}(\mathbf{x}_{\mathrm{IP}})$ and damage $d(\mathbf{x}_{\mathrm{IP}})$ extracted from the converged restart file of Job 1421286 (`results/validation/f1700_extracted_uel_full_field.json`).
By comparing this pointwise field against the 20-bin approximation, we can rigorously quantify the discretization error introduced by binning, confirming whether binning altered the SPR error distribution or if the failure to resolve the secondary corridor is an intrinsic property of instantaneous linear SPR recovery.
