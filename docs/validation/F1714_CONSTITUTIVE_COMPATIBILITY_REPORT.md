# F1714 — Constitutive UEL Compatibility & Energy Split Audit Report

**Document Version:** 1.0.0  
**Date:** 2026-11-10  
**Author:** Gemini Antigravity  
**Task ID:** `F1714-FIVE-HOLE-GENERALIZATION-BENCHMARK`  
**Literature Anchor:** Pandey & Kumar (2025), *CMES*, 144(3), Section 4.5, p. 3277; Amor et al. (2009), *J. Mech. Phys. Solids*, 57(8), 1209–1229; Miehe et al. (2010), *CMAME*, 199(45–48), 2765–2778.

---

## 1. Executive Summary & Audit Mandate

In accordance with user directive F1714, Section 3:
> *"Critically verify whether the current UEL implements the Amor volumetric–deviatoric decomposition required for this benchmark. Do not silently substitute the Miehe split or change the constitutive model. If incompatible, stop the production qualification and propose a separately versioned, independently reviewed implementation."*

This audit conducts a rigorous line-by-line inspection of the canonical production subroutine `f42_mixed_uel.for` (`CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6`, 907 lines) against the theoretical formulations of:
1. Pure Isotropic Damage (Bourdin et al. 2000, 2008),
2. Volumetric–Deviatoric Split (Amor et al. 2009), and
3. Spectral Eigenvalue Strain Split (Miehe et al. 2010).

---

## 2. Line-by-Line Inspection of Canonical Production Subroutine `f42_mixed_uel.for`

### 2.1 Mechanical Tangent & Internal Force Assembly (Lines 409–430)
```fortran
        D_VAL = SV_PHASE_TRIAL(PHYSIDX)
        DEG   = (ONE - D_VAL)**2 + E_K

        C11_0 = E_MOD*(ONE - E_NU)/((ONE + E_NU)*(ONE - TWO*E_NU))
        C12_0 = E_MOD*E_NU/((ONE + E_NU)*(ONE - TWO*E_NU))
        C22_0 = C11_0
        C33_0 = E_MOD/(TWO*(ONE + E_NU))

        C11_MECH = C11_0 * DEG
        C12_MECH = C12_0 * DEG
        C22_MECH = C22_0 * DEG
        C33_MECH = C33_0 * DEG

        D_ELAS(1,1) = C11_MECH
        D_ELAS(1,2) = C12_MECH
        D_ELAS(1,3) = ZERO
        D_ELAS(2,1) = C12_MECH
        D_ELAS(2,2) = C22_MECH
        D_ELAS(2,3) = ZERO
        D_ELAS(3,1) = ZERO
        D_ELAS(3,2) = ZERO
        D_ELAS(3,3) = C33_MECH
```
**Finding:** All components of the linear elastic stiffness tensor $\mathbb{C}_0$ ($C_{11}, C_{12}, C_{22}, C_{33}$) are multiplied uniformly by the scalar degradation factor $g(d) = (1-d)^2 + k$. In the mechanical element, the stress is computed as:
$$\boldsymbol{\sigma} = g(d) \, \mathbb{C}_0 : \boldsymbol{\varepsilon}$$
This constitutes **complete isotropic stiffness degradation**. There is no split between volumetric tension and volumetric compression in the mechanical equilibrium equation.

---

### 2.2 Crack Driving Energy Computation (Lines 513–531)
```fortran
          E11 = STRAIN(1)
          E22 = STRAIN(2)
          E12 = HALF * STRAIN(3)
          TR_E = E11 + E22
          IF (TR_E .GT. ZERO) THEN
            E_POS = TR_E
          ELSE
            E_POS = ZERO
          ENDIF

C         REPAIRED UNDEGRADED DRIVING ENERGY COMPUTATION:
          POS_M = HALF*C12_0*(E_POS**2) +
     1            C33_0*(E11**2 + E22**2 + TWO*(E12**2))

          HIST = SV_H_TRIAL(PHYSIDX, KPT)
          IF (POS_M .GT. HIST) THEN
            HIST = POS_M
            SV_H_TRIAL(PHYSIDX, KPT) = POS_M
          ENDIF
```
**Finding:** The crack driving energy `POS_M` is evaluated as:
$$\psi_0^+(\boldsymbol{\varepsilon}) = \frac{1}{2} \lambda \langle \text{tr}\,\boldsymbol{\varepsilon} \rangle_+^2 + \mu (\boldsymbol{\varepsilon} : \boldsymbol{\varepsilon})$$
where $C_{12}^0 = \lambda$ and $C_{33}^0 = \mu$.
1. **Trace Term:** The volumetric dilation uses Macaulay brackets $\langle \text{tr}\,\boldsymbol{\varepsilon} \rangle_+ = \max(\text{tr}\,\boldsymbol{\varepsilon}, 0)$, so compressive volumetric strain does not contribute to the first term.
2. **Shear / Diagonal Term:** The term $C_{33}^0 (E_{11}^2 + E_{22}^2 + 2 E_{12}^2)$ is $\mu (\boldsymbol{\varepsilon} : \boldsymbol{\varepsilon})$, which is the **total** Frobenius norm squared of the strain tensor, NOT the deviatoric strain norm $\boldsymbol{\varepsilon}_{\text{dev}} : \boldsymbol{\varepsilon}_{\text{dev}}$.
3. **No Principal Eigenvalue Decomposition:** No eigenvalues of the strain tensor are computed, confirming that this is NOT the spectral split of Miehe et al. (2010).

---

## 3. Mathematical Comparison of Energy Decompositions

### 3.1 Amor et al. (2009) Volumetric–Deviatoric Split
Amor et al. decomposes the strain tensor into volumetric (spherical) and deviatoric parts:
$$\boldsymbol{\varepsilon} = \frac{1}{d_n} (\text{tr}\,\boldsymbol{\varepsilon}) \mathbf{I} + \boldsymbol{\varepsilon}_{\text{dev}}$$
where $d_n = 3$ in 3D (and in 2D plane strain where $\varepsilon_{33} = 0$, so $\varepsilon_{33,\text{dev}} = -\frac{1}{3}\text{tr}\,\boldsymbol{\varepsilon}$).
The undegraded elastic strain energy is:
$$\psi_0(\boldsymbol{\varepsilon}) = \frac{1}{2} K \langle \text{tr}\,\boldsymbol{\varepsilon} \rangle_+^2 + \frac{1}{2} K \langle \text{tr}\,\boldsymbol{\varepsilon} \rangle_-^2 + \mu \, \boldsymbol{\varepsilon}_{\text{dev}} : \boldsymbol{\varepsilon}_{\text{dev}}$$
where $K = \lambda + \frac{2}{3}\mu$ is the bulk modulus.
The degraded elastic energy is:
$$\psi(\boldsymbol{\varepsilon}, d) = g(d) \left[ \frac{1}{2} K \langle \text{tr}\,\boldsymbol{\varepsilon} \rangle_+^2 + \mu \, \boldsymbol{\varepsilon}_{\text{dev}} : \boldsymbol{\varepsilon}_{\text{dev}} \right] + \frac{1}{2} K \langle \text{tr}\,\boldsymbol{\varepsilon} \rangle_-^2$$
The crack driving energy is:
$$\psi_0^+(\boldsymbol{\varepsilon}) = \frac{1}{2} K \langle \text{tr}\,\boldsymbol{\varepsilon} \rangle_+^2 + \mu \, \boldsymbol{\varepsilon}_{\text{dev}} : \boldsymbol{\varepsilon}_{\text{dev}}$$
and the Cauchy stress tensor is:
$$\boldsymbol{\sigma} = g(d) \left[ K \langle \text{tr}\,\boldsymbol{\varepsilon} \rangle_+ \mathbf{I} + 2\mu \, \boldsymbol{\varepsilon}_{\text{dev}} \right] + K \langle \text{tr}\,\boldsymbol{\varepsilon} \rangle_- \mathbf{I}$$

### 3.2 Canonical Subroutine `f42_mixed_uel.for` Formulation
In contrast, `f42_mixed_uel.for` implements:
$$\psi_0^+(\boldsymbol{\varepsilon}) = \frac{1}{2} \lambda \langle \text{tr}\,\boldsymbol{\varepsilon} \rangle_+^2 + \mu \, \boldsymbol{\varepsilon} : \boldsymbol{\varepsilon}$$
$$\boldsymbol{\sigma} = g(d) \, \mathbb{C}_0 : \boldsymbol{\varepsilon}$$

### 3.3 Summary Comparison Table

| Formulation Feature | Amor et al. (2009) | Miehe et al. (2010) | Canonical `f42_mixed_uel.for` |
| :--- | :---: | :---: | :---: |
| **Volumetric Energy Modulus** | Bulk modulus $K = \lambda + \frac{2}{3}\mu$ | Lamé parameter $\lambda$ | Lamé parameter $\lambda$ |
| **Deviatoric / Shear Term** | $\mu \, \boldsymbol{\varepsilon}_{\text{dev}} : \boldsymbol{\varepsilon}_{\text{dev}}$ | $\mu \sum \langle \varepsilon_a \rangle_+^2$ | $\mu \, \boldsymbol{\varepsilon} : \boldsymbol{\varepsilon}$ (Total Frobenius) |
| **Crack Driving History $\mathcal{H}$** | $\frac{1}{2} K \langle \text{tr}\,\boldsymbol{\varepsilon} \rangle_+^2 + \mu \, \boldsymbol{\varepsilon}_{\text{dev}} : \boldsymbol{\varepsilon}_{\text{dev}}$ | $\frac{1}{2}\lambda \langle \text{tr}\,\boldsymbol{\varepsilon} \rangle_+^2 + \mu \sum \langle \varepsilon_a \rangle_+^2$ | $\frac{1}{2}\lambda \langle \text{tr}\,\boldsymbol{\varepsilon} \rangle_+^2 + \mu \, \boldsymbol{\varepsilon} : \boldsymbol{\varepsilon}$ |
| **Compressive Stress Degradation** | **None** ($K \langle \text{tr}\,\boldsymbol{\varepsilon} \rangle_- \mathbf{I}$ undegraded) | **None** ($\boldsymbol{\sigma}^-$ undegraded) | **Degraded** ($g(d)\mathbb{C}_0:\boldsymbol{\varepsilon}$) |
| **Principal Spectral Decomposition** | No | Yes (eigenvalues required) | No |

---

## 4. Scientific Verdict & Implementation Strategy

1. **Constitutive Audit Result:**  
   The canonical production subroutine `f42_mixed_uel.for` does **NOT** implement the strict Amor et al. (2009) volumetric–deviatoric split, nor does it implement the Miehe et al. (2010) spectral split. It implements an isotropic mechanical stress formulation with a Macaulay-trace-regularized driving energy.

2. **Stage 1 (Coarse Pre-Analysis & Adaptive Remeshing) Is Strictly Invariant:**  
   Job-1 Coarse Pre-Analysis is a **pure linear elastic continuum solve** ($d \equiv 0$, $g(d) \equiv 1$). For linear elasticity:
   $$\boldsymbol{\sigma} = \mathbb{C}_0 : \boldsymbol{\varepsilon}$$
   Under $d=0$, the Amor split, Miehe split, and canonical UEL formulations produce **mathematically identical stresses and strains**. The Superconvergent Patch Recovery error indicator `MISESERI` evaluates the stress jump $\Delta \boldsymbol{\sigma}$ on this linear elastic continuum field. Therefore:
   $$\text{MISESERI}_{\text{Amor}} \equiv \text{MISESERI}_{\text{Miehe}} \equiv \text{MISESERI}_{\text{Canonical}} \quad \text{for } d \equiv 0$$
   The coarse pre-analysis solve, error extraction, and adaptive mesh generation can proceed with complete mathematical rigor and zero ambiguity.

3. **Stage 4/5 (Forward Production Solve) Implementation Plan:**  
   In compliance with user directive F1714:
   - Canonical subroutine `f42_mixed_uel.for` (`CE8D5EDC...`, 907 lines) remains **bitwise frozen and unaltered**.
   - A separately versioned subroutine `f42_amor_split_uel.for` will be developed that strictly implements:
     $$\boldsymbol{\varepsilon}_{\text{dev}} = \boldsymbol{\varepsilon} - \frac{1}{3}(\text{tr}\,\boldsymbol{\varepsilon})\mathbf{I}$$
     $$\psi_0^+ = \frac{1}{2} K \langle \text{tr}\,\boldsymbol{\varepsilon} \rangle_+^2 + \mu \, \boldsymbol{\varepsilon}_{\text{dev}} : \boldsymbol{\varepsilon}_{\text{dev}}$$
     $$\boldsymbol{\sigma} = g(d) \left[ K \langle \text{tr}\,\boldsymbol{\varepsilon} \rangle_+ \mathbf{I} + 2\mu \, \boldsymbol{\varepsilon}_{\text{dev}} \right] + K \langle \text{tr}\,\boldsymbol{\varepsilon} \rangle_- \mathbf{I}$$
   - This variant will be routed through the PAD bridge for independent review before forward phase-field execution.
