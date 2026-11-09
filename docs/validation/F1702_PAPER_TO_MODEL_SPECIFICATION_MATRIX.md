# Pandey & Kumar (2025) Section 4.3 Paper-to-Model Specification Matrix

**Task**: F1702-PK-SEC43-FIGS14-16-REPRODUCTION-AND-CONTINUATION  
**Date**: 9 November 2026 (Iteration 3 Reconciled Version)  
**Status**: RECONCILED AGAINST DECK NODES, FROZEN UEL SOURCE, AND PAPER CITATIONS  
**Primary Reference**: Pandey, A. & Kumar, S. (2025), *Computer Modeling in Engineering & Sciences* (CMES), Vol. 144, No. 3, pp. 3251–3286, Section 4.3 ("Rectangular Notched Plate with a Hole"), Figures 14, 15(a,b), 16(a,b), 17(a,b).  
**Experimental Benchmark**: Ambati, M., Gerasimov, T., & De Lorenzis, L. (2015), *Computational Mechanics*, 55(2), 383–405 [Ref 39].

---

## 1. Reconciled Specification Matrix

| Parameter / Feature | Published Paper Specification (Pandey & Kumar 2025, Sec. 4.3 & Ambati [39]) | Repository Model Specification (`models/pandey_kumar_mode1/`) | Deck Node & Source Audit Basis | Classification & Reconciliation |
| :--- | :--- | :--- | :--- | :--- |
| **Specimen Geometry** | $65.0 \times 120.0\,\mathrm{mm}$ rectangular plate (Fig. 14, Ambati [39]) | $65.0 \times 120.0\,\mathrm{mm}$ ($X \in [0, 65]$, $Y \in [0, 120]$) | Node coordinates in `PK_SEC43_STAGGERED_JOB1.inp`: $X \in [0, 65]$, $Y \in [0, 120]$ | **EXACT MATCH** (0.00% diff) |
| **Central Hole** | $R = 10.0\,\mathrm{mm}$, center $(36.5, 51.0)\,\mathrm{mm}$ (Fig. 14, Ambati [39]) | $R = 10.0\,\mathrm{mm}$, center $(36.5, 51.0)\,\mathrm{mm}$ | `NSET N_CENTRAL_HOLE` (42 nodes): mean $(36.50, 51.00)\,\mathrm{mm}$, $X \in [26.5, 46.5]$, $Y \in [41.0, 61.0]$ | **EXACT MATCH** (earlier $(32.5, 60.0)$ plate-midpoint transcription corrected) |
| **Upper Pin Hole** | $R = 5.0\,\mathrm{mm}$, center $(20.0, 100.0)\,\mathrm{mm}$ (Fig. 14, Ambati [39]) | $R = 5.0\,\mathrm{mm}$, center $(20.0, 100.0)\,\mathrm{mm}$ | `NSET N_UPPER_HOLE` (21 nodes): mean $(20.00, 100.00)\,\mathrm{mm}$, $X \in [15.0, 25.0]$, $Y \in [95.0, 105.0]$ | **EXACT MATCH** (earlier $(32.5, 110.0)$ transcription corrected) |
| **Lower Pin Hole** | $R = 5.0\,\mathrm{mm}$, center $(20.0, 20.0)\,\mathrm{mm}$ (Fig. 14, Ambati [39]) | $R = 5.0\,\mathrm{mm}$, center $(20.0, 20.0)\,\mathrm{mm}$ | `NSET N_LOWER_HOLE` (21 nodes): mean $(20.00, 20.00)\,\mathrm{mm}$, $X \in [15.0, 25.0]$, $Y \in [15.0, 25.0]$ | **EXACT MATCH** (earlier $(32.5, 10.0)$ transcription corrected) |
| **Initial Notch** | Horizontal slit, length $10.0\,\mathrm{mm}$, width $0.4\,\mathrm{mm}$, at $Y = 70.0\,\mathrm{mm}$ | Length $10.0\,\mathrm{mm}$, width $0.4\,\mathrm{mm}$, flanks at $Y = 69.8$ and $70.2\,\mathrm{mm}$ | Explicit in Paper text (line 1306) & Inp node pairs at $(10.0, 69.8)$ and $(10.0, 70.2)$ | **EXACT MATCH** (0.00% diff) |
| **Boundary Conditions** | Lower hole fixed ($u_x = u_y = 0$); Upper hole $u_x = 0$, $u_y = \Delta u$ | Lower hole pinned ($U1=U2=0$); Upper hole coupled to RP 4040 at $(20, 100)$, $U1=0$, $U2$ prescribed | Explicit in Paper text (lines 1309–1311) & `*COUPLING` / `*BOUNDARY` cards | **EXACT MATCH** |
| **Young's Modulus $E$** | $E = 210.0\,\mathrm{GPa} = 210.0\,\mathrm{kN/mm^2}$ | $E = 210.0\,\mathrm{kN/mm^2}$ | Explicit in Paper text (line 1316) & `E_MOD = 210.D0` in UEL | **EXACT MATCH** (0.00% diff) |
| **Poisson's Ratio $\nu$** | $\nu = 0.30$ | $\nu = 0.30$ | Explicit in Paper text (line 1316) & `E_NU = 0.3D0` in UEL | **EXACT MATCH** (0.00% diff) |
| **Fracture Energy $G_c$** | $G_c = 2.28 \times 10^{-3}\,\mathrm{kN/mm} = 2280\,\mathrm{J/m^2}$ | $G_c = 2.70 \times 10^{-3}\,\mathrm{kN/mm}$ (Ambati reference) & $2.28 \times 10^{-3}\,\mathrm{kN/mm}$ | Paper text states $2.28 \times 10^{-3}$ (line 1317); default thesis UEL uses Ambati [39] constant $2.70 \times 10^{-3}$ | **DOCUMENTED VARIANT** (+18.4% in default UEL; load scale proportional to $\sqrt{G_c}$) |
| **Regularization Length $\ell_0$** | $\ell_0 = 0.285\,\mathrm{mm}$ | $\ell_0 = 0.285\,\mathrm{mm}$ | Explicit in Paper text (lines 1317, 1340) & `E_L0 = 0.285D0` in UEL | **EXACT MATCH** (0.00% diff) |
| **Stress State** | Plane strain assumed ($t = 1.0\,\mathrm{mm}$) | Plane strain CPE4 / CPE3 continuum elements | Paper Section 2.1 & UEL formulation `f42_mixed_uel.for` (lines 411–430) | **EXACT MATCH** |
| **Phase-Field Model** | AT2 second-order diffuse crack formulation with $w(d) = d^2$, $c_w = 1/2$ | AT2 formulation in UEL (JTYPE 1, 3) | Paper Section 2.1; verified in `f42_mixed_uel.for` (lines 330–350) | **EXACT MATCH** |
| **Constitutive & Strain Energy Split** | Paper text claims Miehe et al. [32] spectral split in $\psi_+(\boldsymbol{\varepsilon})$ | Volumetric positive-trace split for damage-driving energy history $H = \max_t \psi_+$; isotropic Cauchy stress degradation | Verified in `f42_mixed_uel.for` (lines 408–430, 516–525): $\boldsymbol{\sigma} = [(1-d)^2 + k_{\mathrm{res}}] \mathbf{C}_0 : \boldsymbol{\varepsilon}$; $\psi_+ = \frac{1}{2} C_{12} \langle \mathrm{tr}(\boldsymbol{\varepsilon}) \rangle_+^2 + C_{33} (\varepsilon_{11}^2 + \varepsilon_{22}^2 + 2\varepsilon_{12}^2)$ | **DOCUMENTED VARIANT / MODEL DIFFERENCE** (Volumetric trace split vs spectral split; Cauchy stress is isotropically degraded) |
| **Residual Stiffness $k_{\mathrm{res}}$** | $k \ll 1$ (typically $10^{-7}$) | $k_{\mathrm{res}} = 1.0 \times 10^{-7}$ | Paper Section 2.1; verified in UEL `E_K = 1.D-7` (line 409) | **EXACT MATCH** |
| **Initial Coarse Mesh** | $1.5\,\mathrm{mm}$ global unstructured mesh (Fig. 16b Job-1) | $1.5\,\mathrm{mm}$ nominal mesh: 3,923 elements, 4,039 physical nodes | Paper text (line 1350) & `PK_SEC43_STAGGERED_JOB1.inp` (3,814 quads, 109 tris) | **EXACT MATCH** (3,923 elements) |
| **Native Remeshing Rule** | Listing 1: `UNIFORM_ERROR`, $e_{\mathrm{tgt}} = 5.0\%$, $h_{\min} = 0.143\,\mathrm{mm}$, $h_{\max} = 1.5\,\mathrm{mm}$, `refinementFactor = 10` | Listing 1 exact call in `execute_f1700_native_adaptive_remesh.py` & F1701 | Paper Listing 1 & Section 4.3 text (lines 1351–1353) | **EXACT MATCH IN RULE SPECIFICATION** (Thesis F1702 also explored tightened $e_{\mathrm{tgt}} = 2.5\%$) |
| **Restart / State Transfer** | **NONE** — Explicitly declared as **FUTURE WORK** in Paper Conclusion (lines 1595–1598) | Offline state transfer evaluated as thesis extension; Paper uses two separate full solves | Paper Section 4.3 lines 1353–1356 & Conclusion line 1596 | **CRITICAL METHODOLOGICAL SCOPE: Paper is an OFFLINE PRE-REFINEMENT method, NOT a restart/continuation method** |
| **Load Schedule** | Two Abaqus steps: $\Delta u_1 = 5 \times 10^{-4}\,\mathrm{mm}$ (2000 incs, $u=1.0$), $\Delta u_2 = 2 \times 10^{-4}\,\mathrm{mm}$ (4000 incs, $u=1.8$) | Incremental displacement loading up to $u_y = 1.50\,\mathrm{mm}$ across 4,500 increments | Paper text (lines 1322–1324) & Job 1421286 / `PK_SEC43_STAGGERED_JOB1.inp` | **DOCUMENTED VARIANT** (Job-1 achieves full dual severance at $u_y = 1.50\,\mathrm{mm}$, load drop 99.98%; total displacement is $1.50\,\mathrm{mm}$ vs $1.80\,\mathrm{mm}$) |

---

## 2. Key Scientific Insights from the Reconciled Specification Audit

1. **Resolution of Geometry Inconsistency (Q1)**:
   The physical benchmark modeled across Tasks F1688–F1702 has its central hole at $(36.5, 51.0)\,\mathrm{mm}$, lower pin hole at $(20.0, 20.0)\,\mathrm{mm}$, and upper pin hole at $(20.0, 100.0)\,\mathrm{mm}$. These coordinates originate directly from the Ambati et al. (2015) [Ref 39] experimental benchmark and match Pandey & Kumar (2025) Figure 14. An earlier draft of this matrix transcribed the plate centroid $(32.5, 60.0)\,\mathrm{mm}$ as the hole location. This error has been corrected based on the explicit node set coordinates extracted from `PK_SEC43_STAGGERED_JOB1.inp`.

2. **Constitutive Law Audit (Q9)**:
   While Pandey & Kumar (2025) Section 4.3 cites the anisotropic formulation of Miehe et al. [32], the production UEL code `f42_mixed_uel.for` (SHA-256 `ce8d5edc...`, 907 lines) implements:
   - Isotropic degradation of the Cauchy stress tensor: $\boldsymbol{\sigma} = [(1-d)^2 + k_{\mathrm{res}}] \mathbf{C}_0 : \boldsymbol{\varepsilon}$.
   - A volumetric positive-trace strain energy split for the scalar damage driving history $H = \max_t \psi_+$.
   This distinction is formally recorded as a documented formulation variant.

3. **Published Method Scope: Offline Pre-Refinement vs Dynamic Continuation**:
   Section 4.3 (lines 1353–1356) and the Conclusions (lines 1595–1598) confirm that Pandey & Kumar (2025) solved Job-1 from $u=0$ to extract the error indicator, meshed the post-adaptive domain to generate `Job-2.inp`, and solved Job-2 **from scratch ($u=0$) to failure**. They never performed state transfer or dynamic continuation.
   State transfer evaluated in Gate G is strictly a thesis exploration, and its $5553.6\%$ energy discontinuity formally classifies it as **NOT QUALIFIED FOR FRACTURE CONTINUATION**.
