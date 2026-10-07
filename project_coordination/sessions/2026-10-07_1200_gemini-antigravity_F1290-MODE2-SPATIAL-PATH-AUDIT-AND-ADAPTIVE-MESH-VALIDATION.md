# Session Report: Task F1290 Mode-II Spatial Path Audit and Adaptive Mesh Validation

**Session Date:** 2026-10-07 12:00 CEST  
**Task ID:** `F1290-MODE2-SPATIAL-PATH-AUDIT-AND-ADAPTIVE-MESH-VALIDATION`  
**Agent:** Gemini Antigravity  
**Starting Commit:** `636e7f3a33b20e716385035e0ebef281bdb0a17d`  
**Audit Verdict:** `AUDIT_FAILED: NATIVE_ADAPTIVE_MESH_DOES_NOT_FOLLOW_MODE2_CRACK_PATH`  
**Execution Boundary:** **STRICT SOLVER GATE -- ZERO SOLVER RUNS AUTHORIZED**

---

## 1. Executive Summary & Objective

In this session, an independent, quantitative spatial trajectory audit of the Mode-II adaptive mesh was performed, starting from raw canonical artifacts:
- Pre-analysis Job `1410178.mmaster02` (`M2_J1_UEL_PRE`) raw evidence on cluster `/scratch9/`
- Actual final-frame MISESERI field (`miseseri_raw_field.csv`, 2,960 elements, Step 2 Frame 5021)
- Reconstructed native adapted mesh `JOB_MODE2_ADAPTIVE_ET2.inp` (21,496 finite elements: 20,934 CPE4 + 562 CPE3)
- Reconstructed 3-layer UEL production fracture deck `Job-2_UEL.inp` (64,488 layered elements, 21,616 nodes)
- Literature Mode-II shear crack trajectories from Pandey & Kumar (2025, Fig. 6b, Fig. 12b) and H2 ultrafine uniform benchmark.

**The Core Scientific Verdict:**
The native adaptive mesh **does NOT refine along the expected Mode-II crack path**. Element-count parity (+7.68% vs. paper 19,963 FE) is an artificial coincidence resulting from horizontal shear localization and spurious boundary refinement.

---

## 2. Quantitative Spatial Comparison Findings

| Trajectory / Discretization Metric | Literature Reference (Pandey & Kumar Fig. 12b) | Coarse Pre-Analysis Ridge (Job 1410178) | Adapted Native Mesh ET2 Refined Zone (`JOB_MODE2_ADAPTIVE_ET2.inp`) | Quantitative Discrepancy / Evaluation |
| :--- | :---: | :---: | :---: | :---: |
| **Kink / Propagation Angle $\theta$** | $\mathbf{-53.65^\circ}$ (downwards) | $\mathbf{-7.80^\circ}$ (nearly horizontal) | Horizontal band along $y \approx 0.50$ | **$\Delta\theta = +45.85^\circ$ severe mismatch** |
| **Boundary Exit Coordinates** | Bottom edge $(0.868, 0.000)\,\text{mm}$ | Right edge $(1.000, 0.380)\,\text{mm}$ | N/A (does not reach boundary) | Divergent exit boundary |
| **Path Normal Distance to Fig. 12(b)** | $0.000\,\text{mm}$ (datum) | Mean: $0.2310\,\text{mm}$, Max: $0.3075\,\text{mm}$ | Mean: $0.0558\,\text{mm}$, Max: $0.1389\,\text{mm}$ | Substantial spatial deviation |
| **Corridor Definition ($d_{\text{corr}} = \pm 0.05\,\text{mm}$)** | Expected $100\%$ fine coverage | N/A (coarse run: 2,960 FE) | $h \le 0.004\,\text{mm}$ criterion | Strict physical corridor |
| **Fine Elements in Expected Corridor** | Expected $> 80\%$ | N/A | **3,416 elements (41.7%)** | Deficient ($< 50\%$) |
| **Fine Elements Off-Path** | Expected $< 20\%$ | N/A | **4,784 elements (58.3%)** | Spurious refinement dominant |
| **Expected Crack Path Covered** | $100\%$ | $0.0\%$ | **20.0%** ($x \in [0.50, 0.59]\,\text{mm}$ only) | **80% of crack path UNREFINED** |
| **Active Crack Corridor ($y \in [0.15, 0.35], x \ge 0.5$)** | Dense refinement ($h \approx 0.002 - 0.004$) | $d \approx 0$, MISESERI $\approx 10^{-18}$ | **EXACTLY 2 ELEMENTS (0.02%)** | **Unrefined coarse mesh ($h \approx 0.020\,\text{mm}$)** |
| **Top Boundary Band ($y \ge 0.95$)** | Unrefined coarse | Boundary stress concentration | 913 elements (11.1%) | Spurious Dirichlet refinement |
| **Bottom Boundary Band ($y \le 0.05$)** | Unrefined coarse | Boundary stress concentration | 943 elements (11.5%) | Spurious Dirichlet refinement |
| **Notch Flank Band ($x \le 0.5, y \approx 0.5$)** | Tip only | Flank stress concentration | 2,060 elements (25.1%) | Spurious flank refinement |

---

## 3. Root Cause Diagnosis & Failure Classification

A systematic investigation of the 9 candidate failure mechanisms revealed two compounding primary root causes:

1. **Primary Root Cause 1: Isotropic Degradation in `f42_mixed_uel.for`:**
   - Lines 416-419 of `f42_mixed_uel.for` degrade all stiffness components isotropically: `C11_MECH = C11_0 * DEG`, `C33_MECH = C33_0 * DEG` with `DEG = (1-d)^2 + k`.
   - The shear strain $\varepsilon_{12}$ directly drives damage via `POS_M = C12_0*HALF*E_POS**2 + C33_0*(E11**2 + E22**2 + TWO*E12**2)`.
   - In pure shear, isotropic degradation destroys shear stiffness across the horizontal plane ahead of the notch tip, producing horizontal shear slip/unzipping rather than Mode-II tensile kinking at $-53.65^\circ$.
   - In contrast, Pandey & Kumar (2025, Section 4.2) employ the **Miehe et al. (2010) anisotropic spectral split**, degrading only the tensile principal strain component ($\theta = -45^\circ$) while preserving compressive shear resistance, thereby forcing the crack to kink downwards.

2. **Primary Root Cause 2: Coarse Pre-Analysis Mesh Resolution Defect ($h > l_0$):**
   - The coarse pre-analysis mesh `Job-1_UEL.inp` had $h_{\text{global}} = 0.020\,\text{mm}$, which is coarser than the diffuse phase-field regularization length $l_0 = 0.015\,\text{mm}$ ($h/l_0 = 1.33 > 1.0$).
   - Coarse-mesh phase-field models suffer from mesh-induced shear localization and row-locking instabilities.

3. **Secondary Mechanism: Native Remeshing Error Propagation:**
   - Abaqus native remeshing with `UNIFORM_ERROR` strictly obeys the error field. Because Job 1410178 unzipped horizontally and produced zero damage and $10^{-18}$ MISESERI in $y \in [0.15, 0.35]$, the remesher had zero signal to refine the physical crack corridor.

---

## 4. Generated Canonical Figures & Evidence

Five publication-grade figures were generated and deposited in `results/figures/mode2/`:
1. `audit_fig1_pandey_kumar_reference_paths.png` / `.pdf`: Reference paths comparison (Fig 12b vs Fig 6b vs H2).
2. `audit_fig2_raw_miseseri_field_and_ridge.png` / `.pdf`: Raw MISESERI field contour and localized ridge.
3. `audit_fig3_et2_true_mesh_and_centerline.png` / `.pdf`: True ET2 element mesh, sizing $h$, and refined centerline.
4. `audit_fig4_comprehensive_trajectory_overlay.png` / `.pdf`: Full domain trajectory overlay across all paths.
5. `audit_fig5_zoomed_notch_corridor_audit.png` / `.pdf`: Zoomed notch tip audit documenting the unrefined corridor.

---

## 5. Artifacts and Hashes

| Artifact Path | Classification | SHA256 Hash |
| :--- | :--- | :--- |
| `scripts/validation/audit_mode2_spatial_trajectory.py` | Canonical Master Tool | `0E42198A4C9B559826D8EBD0BFABEEBEADABF70E680B04C09ADCD5108275B7AB` |
| `tests/unit/test_stage15d_mode2_spatial_trajectory_audit.py` | Governed Unit Test | `9453B0938BA0A2115FF9064A9551772C3F23C1B68DAFC2C40BA8CCA463FE2A0E` |
| `models/pandey_kumar_mode2/MODE2_CURRENT_STATE.md` | Governed State Doc | `4CADEC6F891AB4DFA97C1AF6FFFB7318A1D61F0EBC7CED84AF86B6F09FB1904B` |
| `docs/mode2/MODE2_CURRENT_STATE.md` | Governed State Mirror | `4CADEC6F891AB4DFA97C1AF6FFFB7318A1D61F0EBC7CED84AF86B6F09FB1904B` |
| `results/figures/mode2/audit_fig1_pandey_kumar_reference_paths.png` | Canonical Raster Figure | `21BF46E19964326EAD147DD67C86A05A814AB3E46BFFBED5F99BE9CB01D19817` |
| `results/figures/mode2/audit_fig1_pandey_kumar_reference_paths.pdf` | Canonical Vector Figure | `CE1DEA59113445665DC0C13CD5240D1DDEF35EEFC21D43A43F5948A8D1DD90D4` |
| `results/figures/mode2/audit_fig2_raw_miseseri_field_and_ridge.png` | Canonical Raster Figure | `463C996682B35382527550E0582642A743BD0AC23FE8B3B2240BB4B69512E834` |
| `results/figures/mode2/audit_fig2_raw_miseseri_field_and_ridge.pdf` | Canonical Vector Figure | `F7E900745388501DF20E435B42434429F25BAC8B3268C00BC86421A68ACBAE40` |
| `results/figures/mode2/audit_fig3_et2_true_mesh_and_centerline.png` | Canonical Raster Figure | `57EB65B43692894196C8867D8D9E2859401D1D01E0CB6C2502E5534B51F2567D` |
| `results/figures/mode2/audit_fig3_et2_true_mesh_and_centerline.pdf` | Canonical Vector Figure | `46B437E5019B7706A6EE32E89F8E2C9B8D7BBEE8C8FC4429C5CD3F11C25B83FC` |
| `results/figures/mode2/audit_fig4_comprehensive_trajectory_overlay.png` | Canonical Raster Figure | `0AF9A150C6162F34B34DA857A3B2AC62B667D9040E00EA37E9FBF990B9ADBFBD` |
| `results/figures/mode2/audit_fig4_comprehensive_trajectory_overlay.pdf` | Canonical Vector Figure | `4BC94C44B61B1F7BBAE1329524E326B9436B3163BFBE886BE51EE01533C1762A` |
| `results/figures/mode2/audit_fig5_zoomed_notch_corridor_audit.png` | Canonical Raster Figure | `244C57715192700E3615E16B96CD2AC747A14C6CCB8F5E0F750783C221F3952F` |
| `results/figures/mode2/audit_fig5_zoomed_notch_corridor_audit.pdf` | Canonical Vector Figure | `86900029F9186E4C438314CB1B5FA174CFD60CF0EBB9CE20197ECC4FCF80EC5B` |

---

## 6. Governed Next Steps

- **Hold Mode-II Fracture Submissions:** Zero PBS submissions for Mode-II.
- **Supervisor Review:** Present findings at Thursday 08 October meeting (10:00 CEST).
- **Post-Review Remediation:** Implement Miehe anisotropic split in `f42_mixed_uel.for` and re-run pre-analysis / adaptive remeshing.
