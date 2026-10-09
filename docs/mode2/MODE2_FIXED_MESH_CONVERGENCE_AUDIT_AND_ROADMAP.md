# Mode-II Fixed-Mesh Convergence Audit, Methodology Grounding, and 3-Layer Roadmap

**Author:** Gemini Antigravity (Inspection & Synthesis Agent)  
**Task ID:** `F1382-MODE2-FIXED-MESH-FRACTURE-EVALUATION-AND-ADAPTIVE-CONTROLLER-SYNTHESIS`  
**Date:** October 9, 2026  
**Status:** Canonical Audit, Verification & Technical Roadmap  
**Governing Gate:** `GATE_M2_1B_FIXED_MESH_CONVERGENCE_STUDY_AUDITING_AND_SOLVING`  
**Governing Directive:** *"We need to have understood everything related to the first model before we increase complexity."*

---

## 1. Executive Master Dashboard & Milestone Closeout

Under Gate M2-1B, four uniform fixed-mesh reference models spanning a factor of $5.36\times$ in spatial resolution ($h = 20.0\,\mu\text{m} \to 3.73\,\mu\text{m}$, or $h/l_0 = 1.33 \to 0.25$) were staged, pre-checked, and submitted to the TU Freiberg HPC cluster (`normal_imfdfkmq` on `mnode097`, Jobs 1411542–1411545), solving concurrently alongside the live ET2 adaptive solve (Job 1411414, $37{,}575$ FEs).

### 1.1 Live Cluster Job Status (mnode097)

| PBS Job ID | Discretization / Mesh Tier | Status | Current $u_x$ | Reaction Force $RF_1$ | Peak $F_{\max}$ [N] | Cutbacks / Iters | Walltime / State |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **`1411542.mmaster02`** | `M2_FIX_COARSE_2P5K` ($2{,}500$ quads, $h=20.0\,\mu\text{m}$) | `COMPLETED` | $20.00\,\mu\text{m}$ (100%) | $489.25\,\text{N}$ (softened) | $525.70\,\text{N}$ (at $13.99\,\mu\text{m}$) | 0 cutbacks / 3 iters | 01:00:48 (Exit 0) |
| **`1411543.mmaster02`** | `M2_FIX_MED_18K` ($17{,}956$ quads, $h=7.46\,\mu\text{m}$) | `RUNNING` | $6.00\,\mu\text{m}$ (Inc 1199) | $272.28\,\text{N}$ (elastic) | Pending ($>272.3\,\text{N}$) | 0 cutbacks / 3 iters | Live solving |
| **`1411544.mmaster02`** | `M2_FIX_INT_40K` ($40{,}000$ quads, $h=5.00\,\mu\text{m}$) | `RUNNING` | $2.73\,\mu\text{m}$ (Inc 545) | $124.67\,\text{N}$ (elastic) | Pending ($>124.7\,\text{N}$) | 0 cutbacks / 3 iters | Live solving |
| **`1411545.mmaster02`** | `M2_FIX_FINE_72K` ($71{,}824$ quads, $h=3.73\,\mu\text{m}$) | `RUNNING` | $1.49\,\mu\text{m}$ (Inc 297) | $68.04\,\text{N}$ (elastic) | Pending ($>68.0\,\text{N}$) | 0 cutbacks / 3 iters | Live solving |
| **`1411414.mmaster02`** | `M2_J2_ADAPT_ET2_STAB` ($37{,}575$ FEs, $h_{\min}=3.73\,\mu\text{m}$) | `RUNNING` | $8.50\,\mu\text{m}$ (Inc 1700) | $378.25\,\text{N}$ (pre-peak) | Pending ($\approx 410\text{--}412\,\text{N}$) | 0 cutbacks / 3 iters | Live solving |

---

## 2. Quantitative Verification of Fixed Coarse Simulation (Job 1411542)

The coarse fixed-mesh simulation completed the entire 4,000-increment horizon ($u_x \in [0, 20.00]\,\mu\text{m}$) with zero cutbacks and exact Newton convergence (3 iterations/increment).

### 2.1 Macro-Mechanical Response Summary

1. **Initial Elastic Stiffness ($K_0$):**
   - Ordinary least squares regression on $u_x \in [0.005, 1.000]\,\mu\text{m}$ yields $K_0 = 45.7637\,\text{kN/mm}$ with $R^2 = 0.99999999$ and zero-intercept $c = 2.43\times 10^{-5}\,\text{N}$.
   - Matches the published literature baseline ($45.68 \pm 0.85\,\text{kN/mm}$) within $+0.18\%$.
2. **Peak Load & Crack Initiation ($F_{\max}$):**
   - $F_{\max} = 525.7028\,\text{N}$ occurs at $u_x = 13.990\,\mu\text{m}$.
   - Proves severe coarse-mesh artificial damage diffusion: the peak force is elevated by $+27.5\%$ relative to the adapted ET3 simulation ($412.21\,\text{N}$) and by $+43.7\%$ relative to the published peak ($365.74\,\text{N}$), while the critical displacement at peak is delayed from $9.41\,\mu\text{m} \to 13.990\,\mu\text{m}$ ($+48.7\%$ delay).
3. **Post-Peak Softening Trajectory:**
   - Softens progressively from $525.70\,\text{N} \to 489.25\,\text{N}$ at $u_x = 20.00\,\mu\text{m}$, achieving a verified net load drop of $\Delta F = -36.45\,\text{N}$ ($-6.93\%$).
4. **Cumulative External Work ($W_{\text{ext}}$):**
   - $W_{\text{ext}}(16.0\,\mu\text{m}) = 5.2613\,\text{mJ}$ (vs published $3.517\,\text{mJ}$, $+49.6\%$ excess energy).
   - $W_{\text{ext}}(20.0\,\mu\text{m}) = 7.2309\,\text{mJ}$ (vs adapted ET3 $5.548\,\text{mJ}$, $+30.3\%$ excess energy).

---

## 3. Comparison of Both Completed Coarse Discretizations

We compare the structured $50\times 50$ orthogonal quad mesh (`1411542.mmaster02`, $2,500$ FEs) with the irregular pre-analysis mesh (`1411104.mmaster02`, $2,960$ FEs):

| Metric / Characteristic | Structured Quad Mesh (`1411542`) | Irregular Pre-Analysis Mesh (`1411104`) | Difference / Assessment |
| :--- | :---: | :---: | :---: |
| **Element Count & Type** | $2,500$ quads (100% CPS4/CPE4) | $2,960$ FEs ($2,872$ quads + $88$ tris) | Graded irregular paving |
| **Grid Orientation** | Orthogonal $0^\circ / 90^\circ$ | Unstructured / Delaunay-aligned | Non-orthogonal facet edges |
| **Initial Stiffness $K_0$** | $45.7637\,\text{kN/mm}$ | $45.8016\,\text{kN/mm}$ | $\Delta = 0.08\%$ (identical elastic response) |
| **Peak Reaction Force $F_{\max}$** | $525.7028\,\text{N}$ at $13.99\,\mu\text{m}$ | $514.5100\,\text{N}$ at $13.78\,\mu\text{m}$ | $\Delta = 2.18\%$ ($+11.19\,\text{N}$ on structured) |
| **Terminal Softening $RF_1(20\,\mu\text{m})$** | $489.2489\,\text{N}$ | $433.4700\,\text{N}$ | Structured retains $+55.78\,\text{N}$ higher load |
| **Cumulative Work $W_{\text{ext}}(20\,\mu\text{m})$** | $7.2309\,\text{mJ}$ | $6.9950\,\text{mJ}$ | $\Delta = 3.37\%$ |
| **Crack Path Angle $\theta$** | $\approx -58^\circ$ (diagonal stair-stepping) | $-57.95^\circ$ (facet-following) | Common oblique propagation |
| **Intact Ligament $h_{\text{lig}}$** | Arrests at $y = 144.9\,\mu\text{m}$ ($29\%$) | Arrests at $y = 144.9\,\mu\text{m}$ ($29\%$) | Coarse mesh prevents base breakthrough |

### 3.1 Physical Interpretation of Grid Orientation Effects
Because the physical crack in Mode-II propagates at an oblique angle $\theta \approx -58^\circ$, an orthogonal Cartesian grid ($0^\circ/90^\circ$) forces the phase-field crack band to cross element diagonals. This geometric mismatch creates artificial stair-stepping, elevating the peak load ($525.7\,\text{N}$ vs $514.5\,\text{N}$) and restricting post-peak softening ($489.2\,\text{N}$ vs $433.5\,\text{N}$). In contrast, the irregular mesh provides inclined element edges that more naturally align with the shear localization corridor.

---

## 4. Production Fortran UEL Verification & Mathematical Analysis

We audited the production Fortran source code `models/pandey_kumar_mode2/f42_mixed_uel_mode2_miehe.for` (SHA-256: `699B05D6C430FCE6242F8C603B45BB0783CF376451EFD52C56BC984B0CE71188`).

### 4.1 2D Plane Strain Miehe Spectral Split
Under plane strain with $\varepsilon_{33} = 0$, the principal strains are:
$$\varepsilon_1 = \bar{\varepsilon} + R, \quad \varepsilon_2 = \bar{\varepsilon} - R, \quad \bar{\varepsilon} = \frac{\varepsilon_{11} + \varepsilon_{22}}{2}, \quad R = \sqrt{\left(\frac{\varepsilon_{11} - \varepsilon_{22}}{2}\right)^2 + \varepsilon_{12}^2}$$
The strain energy density split is:
$$\psi_0^+(\boldsymbol{\varepsilon}) = \frac{1}{2}\lambda \langle \operatorname{tr}(\boldsymbol{\varepsilon}) \rangle_+^2 + \mu \left(\langle \varepsilon_1 \rangle_+^2 + \langle \varepsilon_2 \rangle_+^2\right)$$
$$\psi_0^-(\boldsymbol{\varepsilon}) = \frac{1}{2}\lambda \langle \operatorname{tr}(\boldsymbol{\varepsilon}) \rangle_-^2 + \mu \left(\langle \varepsilon_1 \rangle_-^2 + \langle \varepsilon_2 \rangle_-^2\right)$$
where $\langle x \rangle_+ = \max(x, 0)$ and $\langle x \rangle_- = \min(x, 0)$.

### 4.2 Analytical Tangent Consistency & Subgradient Discontinuity
1. **Off Trace-Zero Consistency:**
   For any strain state with $\operatorname{tr}(\boldsymbol{\varepsilon}) \ne 0$, central finite-difference perturbations ($h = 10^{-7}$) confirm:
   $$\|\mathbb{D}_{\text{analytical}} - \mathbb{D}_{\text{numerical}}\|_{\infty} < 10^{-5}$$
   and major symmetry $\mathbb{D}_{ijkl} = \mathbb{D}_{klij}$ holds to machine precision ($< 10^{-10}$).
2. **Subgradient Jump Discontinuity at $\operatorname{tr}(\boldsymbol{\varepsilon}) = 0$:**
   Because $\langle \operatorname{tr}(\boldsymbol{\varepsilon}) \rangle_+$ has a non-smooth derivative (Heaviside step $H(\operatorname{tr}(\boldsymbol{\varepsilon}))$), the tangent modulus undergoes an exact jump across the zero-trace surface:
   $$\Delta \mathbb{D} = -(1 - g(d))\lambda \mathbf{I} \otimes \mathbf{I}$$
   - When $d = 0$, $g(d) \approx 1$ and $\Delta \mathbb{D} = 0$, smoothly recovering isotropic linear elasticity.
   - When $d > 0$, the jump reflects the abrupt degradation of tensile volumetric stiffness while preserving full compressive bulk stiffness.

### 4.3 History Parameter Monotonicity vs Linear Damage PDE
- **Gauss-Point History Monotonicity:** Enforced via $\mathcal{H}_{n+1} = \max(\mathcal{H}_n, \psi_0^+(\boldsymbol{\varepsilon}_{n+1}))$, ensuring $\dot{\mathcal{H}} \ge 0$ unconditionally at all Gauss integration points.
- **Far-Field Damage Fluctuations:** In the unconstrained linear Helmholtz damage PDE ($d - l_0^2 \nabla^2 d = \frac{2l_0}{G_c}(1-d)\mathcal{H}$), local damage fluctuations ($\Delta d \sim -10^{-4}$) during elastic unloading occur exclusively in the far field ($d \approx 0$) as an intrinsic property of $H^1$ elliptic projection, with zero damage reduction in the crack process zone ($d \ge 0.80$).

---

## 5. Multi-Field Adaptive Controller Specification

In the 3-Layer Thesis Architecture, the Layer-2 Controller generates the spatial mesh sizing field $h(\mathbf{x})$.

### 5.1 Formulation of Multi-Field Refinement Indicator
To eliminate artificial crack-wake coarsening:
$$\eta_K = \max\left(\eta_{\sigma,K}, \, \eta_{d,K}\right)$$
where:
- $\eta_{\sigma,K} = \frac{\|\boldsymbol{\sigma}^* - \boldsymbol{\sigma}_h\|_{L^2(K)}}{\|\boldsymbol{\sigma}^*\|_{L^2(\Omega)}}$ (Zienkiewicz–Zhu stress recovery indicator).
- $\eta_{d,K} = \max_{\mathbf{x} \in K} d(\mathbf{x})$ (phase-field damage indicator).

### 5.2 Research Design Hypotheses
1. $\eta_K$ ensures that once damage localizes ($d \ge 0.80$), element sizing $h \le l_0/4$ is preserved indefinitely along the entire fracture wake, preventing spurious remeshing distortion.
2. Element sizing gradient bounds $|\nabla h| \le 0.30$ ensure smooth mesh grading between the fine process zone ($h_{\min} = 3.73\,\mu\text{m}$) and the far-field coarse mesh ($h_{\max} = 20.0\,\mu\text{m}$).

---

## 6. Publication Figures & Verification Lineage

- **Master Figure:** `results/figures/mode2/fig_mode2_f1382_fixed_mesh_fracture_and_adaptive_assessment.pdf` and `.png` (6-panel publication figure, 300 dpi).
- **Master Unit Test:** `tests/unit/test_mode2_f1382_fixed_mesh_fracture_and_adaptive_assessment.py` (6/6 PASS, 100%).
- **Mode-II Master Suite:** 189/189 unit tests passing (100% PASS).
- **Mode-I Baseline Freeze:** Tag `v2026.10.08-supervisor-meeting-mode1-freeze` strictly preserved.
