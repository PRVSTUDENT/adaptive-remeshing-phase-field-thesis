# Scientific Provenance Report: Task F1710 — Authentic Adaptive-Remesh Visualization and Crack-Path Correction

**Protocol Version:** 2  
**Task ID:** `F1710-AUTHENTIC-ADAPTIVE-REMESH-VISUALIZATION`  
**Agent:** `gemini-antigravity`  
**Starting Commit:** `191e854d`  
**Date:** 2026-11-10  
**Predecessor Task:** `F1709-PK-SEC43-JOB2-RECOVERY-AND-FIG16` (Exit 0 across all 4,500 increments)  
**Governing Directive:**
> "Produce and push to GitHub a standalone, scientifically authentic adaptive-remesh visualization reproducing Pandey and Kumar (2025), Figure 16.
> No AI-generated images, artificial contours, manually drawn crack trajectories, or reconstructed fracture fields.
> Use authentic Abaqus finite-element mesh connectivity and phase-field damage results."

---

## 1. Executive Summary & Verification Scope

Task F1710 delivers a standalone, publication-quality scientific visualization of the authentic adapted finite-element mesh and its simulated phase-field fracture field, directly resolving all presentation gaps and eliminating artificial overlays:

1. **Authentic Numerical Data Source**: Sourced strictly from HPC Job **`1421915.mmaster02`**, which completed all 4,500 equilibrium increments with **zero cutbacks** to $u_y = 1.50\,\text{mm}$ under Abaqus 2023 on compute node `mnode100/0`.
2. **Complete Specimen & Discretization Fidelity**: Represents the entire $65 \times 120\,\text{mm}$ specimen containing all **10,065 physical elements** (9,724 CPE4 quads, 341 CPE3 triangles) and 10,096 mesh nodes, with both pin holes ($R=5\,\text{mm}$ at $(20, 20)$ and $(20, 100)$), the central circular void ($R=10\,\text{mm}$ at $(36.5, 51.0)$), and the initial notch ($10 \times 0.4\,\text{mm}$ at $y=70\,\text{mm}$).
3. **Elimination of Artificial Straight Crack-Path Overlays**:
   - The linear regression line ($y = 0.0821x + 46.92$) previously present in Figure 15 comparisons has been completely expunged from the plotting pipeline (`plot_f1707_figure15_reproduction.py`).
   - The genuine numerical crack path is extracted directly from the authentic phase-field damage ridge using a reproducible, power-weighted transverse centroid method ($w_e = d_e^6$, $d_e \ge 0.75$).
   - Experimental crack-path data from Ambati et al. (2015) are strictly distinguished and preserved without alteration.
4. **Standalone Publication Deliverables**:
   - `fig_f1710_authentic_adaptive_mesh.png` & `.pdf`: Full $65 \times 120\,\text{mm}$ specimen displaying individual adapted element edges, authentic damage contours, and a colorbar from 0.0 to 1.0.
   - `fig_f1710_primary_crack_mesh_zoom.png` & `.pdf`: High-resolution zoom ($x \in [0, 42]$, $y \in [44, 76]\,\text{mm}$) resolving the fine element sleeve ($h \le \ell_0/2 = 0.143\,\text{mm}$) around the initial notch root and the curved crack entering the circular void.
   - `fig_f1710_secondary_crack_mesh_zoom.png` & `.pdf`: High-resolution zoom ($x \in [33, 66]$, $y \in [43, 59]\,\text{mm}$) resolving the fine element corridor across the $18.56\,\text{mm}$ ligament and the secondary crack severing the right boundary.
5. **Zero Additional HPC Submissions**: Governed quota (`max_new_pbs_submissions = 0`) preserved; 100% of spatial and field data extracted from existing authentic simulation outputs.

---

## 2. Authentic Simulation Provenance & Metadata

| Parameter / Field | Numerical Value / Provenance Basis |
| :--- | :--- |
| **PBS Job ID** | `1421915.mmaster02` (Package 205) |
| **Cluster Architecture** | Compute node `mnode100/0`, Queue `normal_imfdfkmq` |
| **Abaqus Release** | Abaqus 2023.HF4 + Intel Fortran Compiler Classic 2021.13.0 |
| **Solver Status** | `THE ANALYSIS HAS COMPLETED SUCCESSFULLY` (Exit Code 0) |
| **Total Increments** | Exactly 4,500 converged increments (2,000 in Step 1; 2,500 in Step 2; 0 cutbacks) |
| **Terminal Displacement** | $u_y = 1.5000\,\text{mm}$ |
| **Walltime & CPU Time** | Walltime: $2\,\text{h}\,01\,\text{m}\,54\,\text{s}$ ($121.9\,\text{min}$); CPU time: $1\,\text{h}\,30\,\text{m}\,39\,\text{s}$ ($5,439\,\text{s}$) |
| **Peak Memory** | $7.52\,\text{GB}$ |
| **Source ODB Path** | `/scratch9/pr21vyci/runs/mode1_pk_sec43_job2_staggered_f1709/M1_PK_SEC43_JOB2_STAGGERED.odb` |
| **Mesh File** | `models/pandey_kumar_mode1/203_pk_sec43_secondary_complete/PK_SEC43_F1703_SECONDARY_COMPLETE_ADAPT.inp` |
| **Physical Element Count** | Exactly 10,065 elements ($9,724$ CPE4 quads, $341$ CPE3 triangles) |
| **Physical Node Count** | Exactly 10,096 nodes (plus 1 reference point node 999999) |
| **Output Field Variable** | Companion element state variable `SDV1` representing phase-field damage $d(x,y)$ |
| **Damage Range in Raw Solution** | $d_{\min} = 0.0000$, $d_{\max} = 1.0000$ (strictly bounded within physical limits $[0, 1]$) |
| **Colormap Range & Clipping** | Displayed on linear scale $[0.0, 1.0]$; zero visual clipping or saturation required |

---

## 3. Damage Ridge Extraction Methodology

To eliminate arbitrary lines, linear regression overlays, or hand-drawn splines, the numerical crack trajectory was extracted objectively from the finite-element damage field using the following deterministic algorithm:

1. **Fracture Corridor Definition**:
   - Primary corridor: $x \in [10.0, 31.8]\,\text{mm}$, $y \in [50.0, 72.0]\,\text{mm}$ (originating at notch root $(10.0, 70.0)$ and entering void perimeter at $R=10\,\text{mm}$, center $(36.5, 51.0)$).
   - Secondary corridor: $x \in [46.5, 65.0]\,\text{mm}$, $y \in [48.0, 56.0]\,\text{mm}$ (nucleating at void flank $(46.5, 50.8)$ and traversing to free edge $x=65.0\,\text{mm}$).
2. **Transverse Slicing & Ridge Centroid**:
   - Each corridor was partitioned into 25 discrete longitudinal bins of width $\Delta x \approx 0.7 - 0.9\,\text{mm}$.
   - Elements within each bin satisfying $d_e \ge 0.75$ were collected.
   - The ridge coordinate $(x_{\text{ridge}}, y_{\text{ridge}})$ was calculated via power-weighted centroid:
     $$x_{\text{ridge}} = \frac{\sum_e x_e \cdot d_e^6}{\sum_e d_e^6}, \quad y_{\text{ridge}} = \frac{\sum_e y_e \cdot d_e^6}{\sum_e d_e^6}$$
   - The power $p = 6$ heavily weights the peak element of the localized phase-field band, identifying the true crack centerline without bias from asymmetric mesh grading.
3. **Reproducibility**: All 25 primary and 25 secondary ridge coordinates, associated element IDs, peak damage values, and element counts are archived in `results/validation/f1710_authentic_crack_paths.json`.

---

## 4. Key Trajectory Observations

1. **Primary Branch**:
   - Propagates nearly horizontally from the notch root for $x \in [10.0, 20.0]\,\text{mm}$ ($y \approx 69.5 - 70.0\,\text{mm}$).
   - At $x \approx 22 - 24\,\text{mm}$, the shear and tensile stress concentrations of the circular void pull the crack downward.
   - Bends smoothly along a downward curve ($y(x=24.6) = 68.21\,\text{mm}$, $y(x=27.5) = 66.36\,\text{mm}$, $y(x=29.5) = 64.66\,\text{mm}$, $y(x=31.3) = 62.51\,\text{mm}$) until cleanly entering the upper-left flank of the void.
2. **Secondary Branch**:
   - Nucleates on the opposite void flank at $(46.83, 50.62)\,\text{mm}$.
   - Advances across the $18.56\,\text{mm}$ ligament with subtle physical undulation ($y \in [50.62, 52.44]\,\text{mm}$) tracking the local minimum energy path.
   - Severs the right free boundary at $(64.85, 51.85)\,\text{mm}$.

---

## 5. Deliverables & SHA-256 Provenance Ledger

| Artifact Description | Local Path | Format | SHA-256 Hash |
| :--- | :--- | :--- | :--- |
| **Authentic Adaptive Mesh Figure (PDF)** | `MA_AdaptiveRemeshing_Report_2026/figures/pandey_kumar_fig14_16_reproduction/fig_f1710_authentic_adaptive_mesh.pdf` | Vector PDF | `06CBB757BDDAE7C51235EFD3824A6A9C1E825B7EE8E0D4F32B18E8882338422B` |
| **Authentic Adaptive Mesh Figure (PNG)** | `MA_AdaptiveRemeshing_Report_2026/figures/pandey_kumar_fig14_16_reproduction/fig_f1710_authentic_adaptive_mesh.png` | 300-DPI PNG | `EEB14690F4B932A132C9CE025186E5B5849CFFF29C3499975BDA6C37AEF9B1F7` |
| **Primary Process-Zone Zoom (PDF)** | `MA_AdaptiveRemeshing_Report_2026/figures/pandey_kumar_fig14_16_reproduction/fig_f1710_primary_crack_mesh_zoom.pdf` | Vector PDF | `226E76B657DFE1E62F18C88BBFAB3E33746C89E1CDC83C7534B520C0CDAEB03B` |
| **Primary Process-Zone Zoom (PNG)** | `MA_AdaptiveRemeshing_Report_2026/figures/pandey_kumar_fig14_16_reproduction/fig_f1710_primary_crack_mesh_zoom.png` | 300-DPI PNG | `FF40E24336390CA1A519413C9898C4DF09B38414D640FDB8A9B8407CFE84E421` |
| **Secondary Process-Zone Zoom (PDF)** | `MA_AdaptiveRemeshing_Report_2026/figures/pandey_kumar_fig14_16_reproduction/fig_f1710_secondary_crack_mesh_zoom.pdf` | Vector PDF | `B7FAE7B7F90AED4C86337A0FAA55E4AC3AC6F0E060E3B074ACAD45452C89F8CF` |
| **Secondary Process-Zone Zoom (PNG)** | `MA_AdaptiveRemeshing_Report_2026/figures/pandey_kumar_fig14_16_reproduction/fig_f1710_secondary_crack_mesh_zoom.png` | 300-DPI PNG | `EDD4B93DE76860A2AACD99962924A818D50C3AC4A106F4AE8F1337318D004EDF` |
| **Authentic Crack Paths JSON** | `results/validation/f1710_authentic_crack_paths.json` | JSON Data | `738EFD767B1FF104E433E372F853B2387B5D4788E6B7D4AED2D9F44BB604692E` |
| **Plotting Script** | `scripts/visualization/plot_f1710_authentic_adaptive_mesh.py` | Python 3 | `7350098463FA4A74752CBC751E01A6D60D24945D1A50201AEB33D167520D3C75` |
| **Crack Ridge Extraction Script** | `scripts/extract_authentic_crack_paths.py` | Python 3 | `9C58DAF29206B1DCE81784C96D18C244F9FBE90C4E813708C01F9A917E11194D` |
| **Unit Verification Suite** | `tests/unit/test_f1710_authentic_adaptive_mesh_visualization.py` | Pytest | `D891B9FBFE0CC0BBF261D271E0B9AFCFA1C688A775F7372F679BAFDDBB448127` |

---

## 6. Disclaimers & Governance Discipline

1. The adapted mesh used for Job `1421915.mmaster02` is a fixed, non-uniform discretization generated offline by the multi-state history-aware adaptive remeshing workflow (Task F1703). It did **not** undergo additional dynamic online remeshing during the forward finite-element solution in Abaqus.
2. In accordance with university thesis writing rules, this simulation is characterized as a forward phase-field fracture simulation on an error-guided adapted mesh.
