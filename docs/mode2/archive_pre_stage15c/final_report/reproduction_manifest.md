# Mode-II Validation & Adaptive Remeshing Reproduction Manifest

**Active Scientific Phase:** `MODE2_NATIVE_ADAPTIVE_WORKFLOW_VALIDATED — POSTPEAK_SPATIAL_SENSITIVITY_REMAINS`  
**Date:** 24 September 2026  
**Document Classification:** Standalone Scientific Report Reproduction Package  
**Governance:** Human Authorized (24 September 2026) — Isolated from Frozen Mode-I Thesis Package  

---

## 1. Master Report Artifacts

| Artifact Name | Path / Location | Format | Description |
| :--- | :--- | :--- | :--- |
| **Master LaTeX Source** | `docs/mode2/final_report/MODE2_VALIDATION_AND_ADAPTIVE_REMESHING_REPORT.tex` | LaTeX | 22-page comprehensive scientific report source |
| **Compiled PDF Document** | `docs/mode2/final_report/MODE2_VALIDATION_AND_ADAPTIVE_REMESHING_REPORT.pdf` | PDF | Compiled standalone PDF report with 14 figures & 11 tables |
| **BibTeX Database** | `docs/mode2/final_report/bibliography/references.bib` | BibTeX | Bibliographic references database |
| **Reproduction Manifest** | `docs/mode2/final_report/reproduction_manifest.md` | Markdown | Provenance, checksums, and execution instructions |

---

## 2. Complete Figure Inventory (14 Figures in PDF & PNG)

All figures located in `docs/mode2/final_report/figures/`:

| Figure ID | Filename | Topic / Content | Provenance & Evidence Basis |
| :--- | :--- | :--- | :--- |
| **Figure 1** | `fig01_mode2_bvp_schematic` | Mode-II Benchmark BVP Specification | 1x1 mm domain, sharp seam slit, clamped bottom, free-$u_y$ top loading |
| **Figure 2** | `fig02_workflow_methodology` | Adaptive Remeshing Research Methodology | 6-stage pipeline: Pre-analysis $\to$ MISESERI $\to$ Remesh $\to$ Reconstruct $\to$ Solve $\to$ Audit |
| **Figure 3** | `fig03_miseseri_field` | Coarse Pre-Analysis MISESERI Error Field | Job `1408551.mmaster02`, 3,930 CPE4 elements, WHOLE_ELEMENT position |
| **Figure 4** | `fig04_adaptive_mesh_topology` | Final Abaqus-Native Adaptive Mesh | 7,865 finite elements (7,641 quads + 224 tris), crack zone inset |
| **Figure 5** | `fig05_force_displacement_comparison`| Complete Force-Displacement Response | $H_1$ (12,064) vs $H_2$ (33,852) vs Adaptive (7,865) vs Pandey & Kumar (2025) |
| **Figure 6** | `fig06_prepeak_peak_zoom` | Pre-Peak Linear Elasticity & Peak Zoom | Fitted $K_{0,\mathrm{lin}} \approx 12.70\text{ kN/mm}$ ($\Delta = -0.28\%$), $F_{\max} \approx 0.1462\text{ kN}$ ($\Delta = +1.73\%$) |
| **Figure 7** | `fig07_postpeak_zoom` | Post-Peak Softening Divergence Zoom | Post-peak divergence at $u_1 = 0.04258\text{ mm}$ ($-44.31\%$ force vs $H_1$) |
| **Figure 8** | `fig08_damage_contours` | Matched-Displacement Damage Contours | Contours at $u_1 = 0.0125, 0.0250, 0.0426\text{ mm}$ for $H_1$, $H_2$, Adaptive |
| **Figure 9** | `fig09_extracted_crack_paths` | Extracted Crack Centerline Trajectories | $\theta_{\mathrm{kink}} = -21.89^\circ$ ($+7.50^\circ$), $\theta_{\mathrm{chord}} = -16.23^\circ$ ($+1.16^\circ$) |
| **Figure 10** | `fig10_local_resolution_heq_over_l0`| Resolution ($h_{\mathrm{eq}}/l_0$) along Path | Measured $h_{\mathrm{eq}} = \sqrt{A}$ at 23 centerline points ($h/l_0 \in [0.159, 0.716]$) |
| **Figure 11** | `fig11_path_resolution_distribution`| Path-Resolution Distribution Intervals | Sample-point fractions vs arc-length-weighted fractions |
| **Figure 12** | `fig12_crack_path_literature_comparison`| Published vs Simulated Crack Morphology | Qualitative morphology alignment against Pandey & Kumar Fig. 12/13 |
| **Figure 13** | `fig13_computational_cost_telemetry`| Audited HPC Solver Telemetry Audit | Telemetry: $-34.8\%$ elements, $+88.2\%$ walltime, $+165.2\%$ iterations |
| **Figure 14** | `fig14_triangular_patch_test_qualification`| Triangular Element Subroutine Verification | Job `1408559.mmaster02` constant-strain parity, $d=0.50$ scaling, SDV mapping |

---

## 3. Verified Simulation Inputs, Subroutines & Checksums

| File Identifier | Relative Path | Size (bytes) | SHA-256 Checksum |
| :--- | :--- | :--- | :--- |
| **User Subroutine** | `f42_mixed_uel.for` | 29,401 | `5cd0d2c015c9ead91c99d7a744156cc86f5b5ea26473bbed7d6e5515fe30fa46` |
| **$H_1$ Reference Deck** | `M2_H1_reference.inp` | 2,202,929 | `59b639dd64e7441d70d93cdb3ed6a6cbfa1370fd3fd7553800591fc20bd850f4` |
| **Adaptive Candidate Deck** | `ModeII_adaptive_candidate.inp` | 1,526,716 | `d864d604292e5a7202d70a6bff82afda8cb65d71fe865454f06c08c2d4dbeabf` |
| **Pre-Analysis Deck** | `ModeII_MISESERI_preanalysis.inp` | 350,689 | `96af41fd4ffe09a046815e754f0b382c171e4c84f752c172be5eb2abf5e601fd` |
| **MISESERI CSV Dataset** | `ModeII_MISESERI_coarse_3930.csv` | 150,677 | `02d165fdd13b766f0682e7575ace4da153c30b02823d06b2e5880a49b9d15a74` |
| **Triangular UEL Patch Deck** | `M2_tri_patch_uel.inp` | 2,002 | `8de6ed37eccf5b3cf0eabe1f6009aa93f1431c6ac4cbf639ad7356ae8dda8d79` |
| **Reference CPE3 Patch Deck** | `M2_tri_patch_cpe3_ref.inp` | 769 | `e02766f5161f7155004d4df5a2e551d4f2da8c3f113f1839f252532d41a899b8` |
| **Digitized Publication CSV** | `pandey_kumar_fig13a_digitized.csv` | 2,145 | `0562087b8a4ac7ba7e0b327603d4984cfcafb757ba89f2059271ff66ce1c138e` |

---

## 4. HPC Cluster Solver Telemetry Ledger

| PBS Job ID | Job Name | Exit Status | Increments | Walltime | CPU Time | Peak RAM | Scientific Status |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| `1408540.mmaster02` | `M2_H1_CORR_DC` | 0 | --- | 00:00:12 | 00:00:08 | 185 MB | `H1_GEN3_DATACHECK_QUALIFIED` |
| `1408541.mmaster02` | `M2_H1_CORR_PROD` | 0 | 32 | 00:02:15 | 00:02:01 | 340 MB | `INVALID_ABI_DIAGNOSTIC` |
| `1408542.mmaster02` | `M2_H1_CORR_DC` | 0 | --- | 00:00:14 | 00:00:09 | 185 MB | `H1_GEN3_ABI_CORRECTED_DC_QUALIFIED` |
| `1408543.mmaster02` | `M2_H1_CORR_PROD` | 0 | 144 | 00:10:36 | 00:09:46 | 652 MB | `H1_GEN3_REFERENCE_PROD_QUALIFIED` |
| `1408548.mmaster02` | `M2_H2_CORR_DC` | 0 | --- | 00:00:18 | 00:00:12 | 310 MB | `INVALID_PHASE_DOF_DIAGNOSTIC` |
| `1408549.mmaster02` | `M2_H2_CORR_DC` | 0 | --- | 00:00:20 | 00:00:14 | 310 MB | `H2_GEN3_DATACHECK_QUALIFIED` |
| `1408550.mmaster02` | `M2_H2_CORR_PROD` | 1 | 105 | 00:21:14 | 00:19:52 | 1,447 MB | `H2_SPATIAL_SENSITIVITY_QUALIFIED` |
| `1408551.mmaster02` | `M2_COARSE_PRE` | 0 | 10 | 00:00:45 | 00:00:32 | 198 MB | `MODE2_COARSE_PREANALYSIS_QUALIFIED` |
| `1408554.mmaster02` | `M2_ADAPT_DC` | 0 | --- | 00:00:15 | 00:00:10 | 215 MB | `MODE2_ADAPTIVE_DATACHECK_QUALIFIED` |
| `1408555.mmaster02` | `M2_ADAPT_PROD` | 0 | 358 | 00:19:57 | 00:16:42 | 1,712 MB | `MODE2_NATIVE_ADAPTIVE_PROD_COMPLETED` |
| `1408558.mmaster02` | `M2_TRI_PATCH_DC` | 0 | --- | 00:00:08 | 00:00:05 | 120 MB | `TRI_PATCH_DATACHECK_QUALIFIED` |
| `1408559.mmaster02` | `M2_TRI_PATCH_PROD` | 0 | 2 | 00:00:15 | 00:00:10 | 193 MB | `TRI_JTYPE3_4_PATCH_QUALIFIED` |

---

## 5. Exact Non-Interactive Reproduction Commands

### Step 1: Pre-Analysis Execution & Error Indicator Recovery
```powershell
abaqus datacheck job=ModeII_MISESERI_preanalysis interactive
abaqus job=ModeII_MISESERI_preanalysis cpus=1 memory="8000 mb" interactive
abaqus python extract_miseseri_field.py ModeII_MISESERI_preanalysis.odb
```

### Step 2: Native Adaptive Remeshing & UEL Reconstruction
```powershell
abaqus python generate_mode2_native_adaptive_mesh.py
```

### Step 3: Triangular Element Patch Test Verification
```powershell
abaqus job=M2_tri_patch_uel user=f42_mixed_uel.for cpus=1 interactive
abaqus job=M2_tri_patch_cpe3_ref cpus=1 interactive
python compare_triangular_patch_results.py
```

### Step 4: Adaptive Production Execution
```powershell
abaqus datacheck job=ModeII_adaptive_candidate user=f42_mixed_uel.for interactive
abaqus job=ModeII_adaptive_candidate user=f42_mixed_uel.for cpus=1 memory="16000 mb" interactive
```

### Step 5: Post-Processing & Figure Generation
```powershell
python postprocess_mode2_adaptive_full.py M2_adapt_prod.dat
python generate_all_mode2_report_figures.py
```

### Step 6: LaTeX Report Compilation
```powershell
pdflatex -interaction=nonstopmode MODE2_VALIDATION_AND_ADAPTIVE_REMESHING_REPORT.tex
bibtex MODE2_VALIDATION_AND_ADAPTIVE_REMESHING_REPORT
pdflatex -interaction=nonstopmode MODE2_VALIDATION_AND_ADAPTIVE_REMESHING_REPORT.tex
pdflatex -interaction=nonstopmode MODE2_VALIDATION_AND_ADAPTIVE_REMESHING_REPORT.tex
```
