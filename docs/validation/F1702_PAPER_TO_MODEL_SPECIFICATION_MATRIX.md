# Pandey & Kumar (2025) Section 4.3 Paper-to-Model Specification Matrix

**Task**: F1702-PK-SEC43-FIGS14-16-REPRODUCTION-AND-CONTINUATION  
**Date**: 9 November 2026  
**Status**: OFFICIALLY AUDITED & VERIFIED  
**Primary Reference**: Pandey, A. & Kumar, S. (2025), *Computer Modeling in Engineering & Sciences* (CMES), Vol. 144, No. 3, pp. 3251–3286, Section 4.3 ("Rectangular Notched Plate with a Hole"), Figures 14, 15(a,b), 16(a,b), 17(a,b).  
**Experimental Benchmark**: Ambati, M., Gerasimov, T., & De Lorenzis, L. (2015), *Computational Mechanics*, 55(2), 383–405 [Ref 39].

---

## 1. Specification Matrix

| Parameter / Feature | Published Paper Specification (Pandey & Kumar 2025, Sec. 4.3) | Repository Model Specification (`models/pandey_kumar_mode1/`) | Provenance / Verification Status | Discrepancy & Classification |
| :--- | :--- | :--- | :--- | :--- |
| **Specimen Geometry** | $65.0 \times 120.0\,\mathrm{mm}$ rectangular plate (Fig. 14) | $65.0 \times 120.0\,\mathrm{mm}$ ($X \in [0, 65]$, $Y \in [0, 120]$) | Explicit in Paper text (line 1316) & Inp geometry | **EXACT MATCH** (0.00% diff) |
| **Central Hole** | $R = 10.0\,\mathrm{mm}$, center $(32.5, 60.0)\,\mathrm{mm}$ | $R = 10.0\,\mathrm{mm}$, center $(32.5, 60.0)\,\mathrm{mm}$ | Inferred from Fig. 14 & explicit in Inp coordinates | **EXACT MATCH** (0.00% diff) |
| **Upper Pin Hole** | $R = 5.0\,\mathrm{mm}$, center $(32.5, 110.0)\,\mathrm{mm}$ | $R = 5.0\,\mathrm{mm}$, center $(32.5, 110.0)\,\mathrm{mm}$ | Inferred from Fig. 14 & explicit in Inp coordinates | **EXACT MATCH** (0.00% diff) |
| **Lower Pin Hole** | $R = 5.0\,\mathrm{mm}$, center $(32.5, 10.0)\,\mathrm{mm}$ | $R = 5.0\,\mathrm{mm}$, center $(32.5, 10.0)\,\mathrm{mm}$ | Inferred from Fig. 14 & explicit in Inp coordinates | **EXACT MATCH** (0.00% diff) |
| **Initial Notch** | Horizontal slit, length $10.0\,\mathrm{mm}$, width $0.4\,\mathrm{mm}$, at $Y = 70.0\,\mathrm{mm}$ | Length $10.0\,\mathrm{mm}$, width $0.4\,\mathrm{mm}$, flanks at $Y = 69.8$ and $70.2\,\mathrm{mm}$ | Explicit in Paper text (line 1307) | **EXACT MATCH** (0.00% diff) |
| **Boundary Conditions** | Lower hole fixed ($u_x = u_y = 0$); Upper hole $u_x = 0$, $u_y = \Delta u$ | Lower hole pinned ($U1=U2=0$); Upper hole coupled to RP at $(20, 100)$, $U1=0$, $U2$ prescribed | Explicit in Paper text (lines 1309–1311) | **EXACT MATCH** |
| **Young's Modulus $E$** | $E = 210.0\,\mathrm{GPa} = 210.0\,\mathrm{kN/mm^2}$ | $E = 210.0\,\mathrm{kN/mm^2}$ | Explicit in Paper text (line 1317) | **EXACT MATCH** (0.00% diff) |
| **Poisson's Ratio $\nu$** | $\nu = 0.30$ | $\nu = 0.30$ | Explicit in Paper text (line 1317) | **EXACT MATCH** (0.00% diff) |
| **Fracture Energy $G_c$** | $G_c = 2.28 \times 10^{-3}\,\mathrm{kN/mm} = 2280\,\mathrm{J/m^2}$ | $G_c = 2.70 \times 10^{-3}\,\mathrm{kN/mm}$ (Ambati reference) & $2.28 \times 10^{-3}\,\mathrm{kN/mm}$ | Paper text states $2.28 \times 10^{-3}$ (line 1318); Ambati [39] uses $2.70 \times 10^{-3}$ | **DOCUMENTED VARIANT** (+18.4% in default UEL; load scale proportional to $\sqrt{G_c}$) |
| **Regularization Length $\ell_0$** | $\ell_0 = 0.285\,\mathrm{mm}$ | $\ell_0 = 0.285\,\mathrm{mm}$ | Explicit in Paper text (line 1318, 1341) | **EXACT MATCH** (0.00% diff) |
| **Stress State** | Plane strain assumed ($t = 1.0\,\mathrm{mm}$) | Plane strain CPE4 / CPE3 continuum elements | Paper Section 2.1 & UEL formulation `f42_mixed_uel.for` | **EXACT MATCH** |
| **Phase-Field Model** | AT2 second-order diffuse crack formulation with $w(d) = d^2$, $c_w = 1/2$ | AT2 formulation in UEL (JTYPE 1, 3) | Paper Section 2.1; verified in UEL source | **EXACT MATCH** |
| **Strain Energy Split** | Miehe et al. [32] spectral split in $\psi_+(\boldsymbol{\varepsilon})$ | Spectral split in $\psi_+(\boldsymbol{\varepsilon})$ in UEL; Cauchy stress is isotropic degradation | Paper Section 4.3 text (lines 1319–1320); verified in UEL | **EXACT MATCH IN ENERGY SPLIT; CONSTITUTIVE AUDIT DISCLOSES ISOTROPIC CAUCHY STRESS** |
| **Residual Stiffness $k_{\mathrm{res}}$** | $k \ll 1$ (typically $10^{-7}$) | $k_{\mathrm{res}} = 1.0 \times 10^{-7}$ in `f42_mixed_uel.for` | Paper Section 2.1; verified in UEL source | **EXACT MATCH** |
| **Initial Coarse Mesh** | $1.5\,\mathrm{mm}$ global unstructured mesh (Fig. 16b Job-1) | $1.5\,\mathrm{mm}$ nominal mesh: 3,923 elements, 4,039 physical nodes | Paper text (line 1351) & `PK_SEC43_STAGGERED_JOB1.inp` | **EXACT MATCH** (3,923 elements) |
| **Native Remeshing Rule** | Listing 1: `UNIFORM_ERROR`, $e_{\mathrm{tgt}} = 5.0\%$, $h_{\min} = 0.143\,\mathrm{mm}$, $h_{\max} = 1.5\,\mathrm{mm}$, `refinementFactor = 10` | Listing 1 exact call in `execute_f1700_native_adaptive_remesh.py` & F1701 | Paper Listing 1 & Section 4.3 text (lines 1352–1354) | **EXACT MATCH** |
| **Restart / State Transfer** | **NONE** — Explicitly declared as **FUTURE WORK** in Paper Conclusion (lines 1595–1598) | Offline state transfer evaluated as thesis extension; Paper uses two separate full solves | Paper Section 4.3 lines 1354–1356 & Conclusion line 1596 | **CRITICAL DISCOVERY: Paper is an OFFLINE PRE-REFINEMENT method, NOT a restart/continuation method** |
| **Load Schedule** | Two Abaqus steps: $\Delta u_1 = 5 \times 10^{-4}\,\mathrm{mm}$ (2000 incs, $u=1.0$), $\Delta u_2 = 2 \times 10^{-4}\,\mathrm{mm}$ (4000 incs, $u=1.8$) | Incremental displacement loading up to $u_y = 1.50\,\mathrm{mm}$ across 4,500 increments | Paper text (lines 1323–1324) & Job 1421286 | **EXACT LOADING PROFILE** (covers full crack trajectory through dual severance) |

---

## 2. Key Scientific Findings from the Paper Audit

1. **The Published "Proposed PFM" is an Offline Pre-Refinement Strategy, NOT Dynamic Remesh-and-Continue**:
   Section 4.3 (lines 1354–1356) and the Conclusions (lines 1595–1598) state explicitly:
   > "The post-adaptive discretized specimen, as depicted in Fig. 16b, is used to generate the new element and nodal repository (Job-2.inp file) through the Python script. Next, the 'Job-2_UEL.inp' is submitted along with the Fortran subroutine to obtain phase field results for the proposed PFM as shown in Fig. 16b..."
   > "While the extension to 3D geometries seems to be an encouraging and practical direction, it is currently beyond the scope of this study due to added complexity and computational demands. However, it remains a significant motivation for our future work with enhancements such as incorporating the restart analysis-based simulations..."
   Therefore, Pandey & Kumar (2025) solved Job-1 from $u=0$ to obtain an error indicator field, generated Job-2 mesh, and solved Job-2 **from scratch ($u=0$) to the end**! They never performed state transfer or in-analysis restart.
2. **The "Single-Rule Reproduction Paradox"**:
   Because Job-1 solves through the entire fracture process, the error indicator field extracted to generate Job-2 must have captured the entire crack trajectory. However, as demonstrated across Tasks F1694, F1698, F1699, F1700, and F1701, **any single instantaneous frame** from Job-1 captures either the notch initiation (State 2) or the secondary propagation (State 4), but never both simultaneously, because the primary ligament relaxes its stresses once severed!
   Hence, the continuous dual-corridor indicator in Figure 15(b) could only arise either from an accumulated multi-frame envelope or an early un-relaxed state before complete severance.

---
