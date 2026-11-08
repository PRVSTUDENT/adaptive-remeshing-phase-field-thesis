# Task F1688: Geometry Datum & Benchmark Specification Record
**Benchmark:** Pandey & Kumar (2025) Section 4.3 — Rectangular Notched Plate with a Hole
**Task ID:** `F1688-PANDEY-KUMAR-SEC43-REPRODUCTION-CONTROL`
**Date:** 8 November 2026
**Agent:** Gemini Antigravity

---

## 1. Executive Summary & Purpose

This document provides the authoritative geometry datum check and parameter specification for reproducing the benchmark problem in Section 4.3 of **Pandey & Kumar (2025)** (*Computers, Materials & Continua*, 144(3), pp. 3251–3276): *Rectangular Notched Plate with a Hole*. 

The objective of Task F1688 is to perform an independent control test of the native Abaqus MISESERI adaptive remeshing framework on the paper's own geometry, comparing directly against:
- **Figure 15b:** Coarse-mesh MISESERI error indicator contour.
- **Figure 16b:** Single-rule adaptively refined mesh.

---

## 2. Geometric Dimensions & Hole Datum Verification

### 2.1 Plate Domain
- **Width:** $W = 65.0\,\mathrm{mm}$ ($x \in [0.0, 65.0]\,\mathrm{mm}$).
- **Height:** $H = 120.0\,\mathrm{mm}$ ($y \in [0.0, 120.0]\,\mathrm{mm}$).
- **Thickness:** $t = 1.0\,\mathrm{mm}$ (plane strain conditions assumed).

### 2.2 Horizontal Notch
- **Length:** $a = 10.0\,\mathrm{mm}$ ($x \in [0.0, 10.0]\,\mathrm{mm}$).
- **Width:** $w = 0.4\,\mathrm{mm}$ ($y \in [69.8, 70.2]\,\mathrm{mm}$, centered at $y = 70.0\,\mathrm{mm}$).
- **Representation:** Rectangular cutout slot with planar tip at $x = 10.0\,\mathrm{mm}$.

### 2.3 Loading & Support Holes (Verification of Undimensioned Lower Hole Datum)
In Pandey & Kumar (2025) Figure 14, the upper loading hole is explicitly dimensioned at center $(20, 100)\,\mathrm{mm}$ with diameter $10.0\,\mathrm{mm}$, while the lower hole's $y$-coordinate is not dimensioned.
- **Literature Origin:** Pandey & Kumar attribute this experimental/numerical benchmark to **Ambati, Gerasimov, and De Lorenzis (2015)** (*Comput. Mech.* 55(2), pp. 383–405, Section 4).
- **Independent Verification:** In the canonical benchmark implementation archived in the COMSOL Multiphysics Application Library (`holed_plate_fracture.pdf`), the lower loading pin hole (Circle `c2`) is explicitly positioned at:
  $$\mathbf{x}_{\mathrm{lower}} = (20.0\,\mathrm{mm},\, 20.0\,\mathrm{mm}), \quad R = 5.0\,\mathrm{mm}$$
  This positions the lower hole exactly $20.0\,\mathrm{mm}$ from the bottom boundary ($y = 0$) and $20.0\,\mathrm{mm}$ from the left boundary ($x = 0$), in perfect vertical mirror symmetry with the upper hole ($20.0\,\mathrm{mm}$ from the top boundary $y = 120.0\,\mathrm{mm}$ and $20.0\,\mathrm{mm}$ from the left boundary $x = 0$).
- **Conclusion:** The lower hole center is authoritatively established as $(20.0,\, 20.0)\,\mathrm{mm}$ ($D = 10.0\,\mathrm{mm}$).

### 2.4 Central Eccentric Void
- **Diameter:** $D = 20.0\,\mathrm{mm}$ ($R = 10.0\,\mathrm{mm}$).
- **Positioning:** Dimensioned in Figure 14 as $28.5\,\mathrm{mm}$ from the right boundary and $51.0\,\mathrm{mm}$ from the bottom boundary:
  $$x_{\mathrm{center}} = 65.0 - 28.5 = 36.5\,\mathrm{mm}$$
  $$y_{\mathrm{center}} = 51.0\,\mathrm{mm}$$
  $$\mathbf{x}_{\mathrm{center}} = (36.5\,\mathrm{mm},\, 51.0\,\mathrm{mm})$$

---

## 3. Physical & Numerical Parameters

| Parameter | Symbol | Value | Unit | Notes |
| :--- | :---: | :---: | :---: | :--- |
| Young's Modulus | $E$ | $210.0$ | $\mathrm{GPa}$ ($=\mathrm{kN/mm^2}$) | Literature [62] (Patil et al. 2018) |
| Poisson's Ratio | $\nu$ | $0.3$ | — | Literature [62] |
| Phase-Field Length Scale | $\ell_0$ | $0.285$ | $\mathrm{mm}$ | Paper Section 4.3 |
| Critical Fracture Energy | $G_c$ | $2.28 \times 10^{-3}$ | $\mathrm{kN/mm}$ ($=2.28\,\mathrm{N/mm}$) | Paper Section 4.3 |
| Residual Stiffness | $k$ | $1.0 \times 10^{-7}$ | — | Consistent with `f42_mixed_uel.for` |
| Strain Split | — | Miehe split | — | Implemented in `f42_mixed_uel.for` |

---

## 4. Boundary Conditions & Loading Protocol

1. **Lower Hole Boundary:** Pinned support ($u_x = 0, u_y = 0$) on all nodes along the hole circumference.
2. **Upper Hole Boundary:** Tensile displacement loading with $u_x = 0$ and $u_y = u(t)$ applied via a reference node kinematically tied to the upper hole perimeter.
3. **Displacement Schedule:**
   - **Step 1 (Pre-critical):** $\Delta u_1 = 5 \times 10^{-4}\,\mathrm{mm}$ per increment up to $u_1 = 1.0\,\mathrm{mm}$ ($2{,}000$ increments).
   - **Step 2 (Fracture):** $\Delta u_2 = 2 \times 10^{-4}\,\mathrm{mm}$ per increment up to $u_2 = 1.5\,\mathrm{mm}$ (capturing point $u_{s4} \approx 1.46\,\mathrm{mm}$).

---

## 5. Mesh & Remeshing Specifications

1. **Coarse Initial Mesh (Job-1):**
   - Global element size: $h_{\mathrm{global}} = 1.5\,\mathrm{mm}$.
   - Target element count: $\approx 3{,}500$ linear quad/tri elements.
   - Initial resolution ratio: $h/\ell_0 = 1.5 / 0.285 \approx 5.26$ (deliberately under-resolved to test adaptive marking).
2. **Native Abaqus Remeshing Rule (Listing 1):**
   - Variable: `MISESERI`
   - Sizing Method: `UNIFORM_ERROR`
   - Target Error: $e_{\mathrm{tgt}} = 5.0\%$
   - Min Element Size: $h_{\min} = 0.143\,\mathrm{mm}$ ($h_{\min}/\ell_0 \approx 0.50$)
   - Max Element Size: $h_{\max} = 1.5\,\mathrm{mm}$
   - Refinement Factor: $10$
   - Coarsening Factor: `NOT_ALLOWED`
   - Region: `All_elem`
