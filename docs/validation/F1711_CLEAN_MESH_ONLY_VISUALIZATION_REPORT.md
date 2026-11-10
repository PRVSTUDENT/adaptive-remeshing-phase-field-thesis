# Scientific Provenance Report: Task F1711 — Clean Standalone Mesh-Only Adaptive Remesh Visualization

**Protocol Version:** 2  
**Task ID:** `F1711-CLEAN-MESH-ONLY-ADAPTIVE-REMESH-IMAGE`  
**Agent:** `gemini-antigravity`  
**Starting Commit:** `53521da4`  
**Date:** 2026-11-10  
**Predecessor Task:** `F1710-AUTHENTIC-ADAPTIVE-REMESH-VISUALIZATION`  
**Governing Directive:**
> "Generate and push to GitHub a clean standalone adaptive-remesh image only, without phase-field damage contours, without rainbow coloring, and without any crack-path overlay lines.  
> The user wants to see the adaptive finite-element mesh itself, not the phase-field field plot.  
> FIGURES TO GENERATE:
> 1. Full adaptive-remesh image (mesh only) — entire specimen, visible element edges, no damage colormap, no crack contour fill, no artificial straight line.
> 2. Primary-process-zone mesh zoom — zoom near notch-to-hole region, mesh only.
> 3. Secondary-process-zone mesh zoom — zoom near hole-to-right-boundary region, mesh only.
> VISUAL STYLE REQUIREMENTS: Clean white background, thin dark element-edge lines, holes as white cutouts with dark boundaries, thesis-ready."

---

## 1. Executive Summary & Objective Fulfillment

Task F1711 fulfills the user directive to produce clean, publication-ready, standalone visualizations of the **adaptive finite-element mesh itself**, stripped of all scalar colormaps, phase-field damage fields, and trajectory overlays:

1. **Pure Finite-Element Wireframe Representation**:
   - Every element face is rendered in pure white (`#ffffff`) with crisp, dark element edges (`#1e293b` with linewidth $0.35\,\text{pt}$ for the global view, and `#0f172a` with linewidth $0.45\,\text{pt}$ for high-magnification process-zone zooms).
   - Void boundaries (the central circular hole at $(36.5, 51.0)\,\text{mm}$ with $R = 10.0\,\text{mm}$ and the two loading pin holes at $(20.0, 20.0)\,\text{mm}$ and $(20.0, 100.0)\,\text{mm}$ with $R = 5.0\,\text{mm}$) are rendered as clean white cutouts bounded by bold dark contours (`#0f172a`, linewidth $1.5\,\text{pt}$).
   - The initial slit notch ($10.0 \times 0.4\,\text{mm}$ at $y = 70.0\,\text{mm}$) is distinctly rendered in solid black.
2. **Strict Absence of Scalar Colormaps and Overlays**:
   - Zero phase-field damage scalar variables (`SDV1` or nodal $d$) are loaded or plotted.
   - Zero colormaps (`jet`, `viridis`, rainbow, or grayscale) and zero colorbars are instantiated.
   - Zero crack-trajectory lines, splines, or linear regression overlays are drawn.
3. **Natural Visual Depiction of Adaptive Refinement**:
   - The extreme edge density in the localized refinement corridors ($h \le 0.143\,\text{mm}$ in the primary notch-to-hole path and $h \le 0.051\,\text{mm}$ in the secondary hole-to-boundary path) naturally contrasts against the coarse background mesh ($h \approx 1.5 - 2.0\,\text{mm}$) through pure geometric edge concentration, vividly displaying the error-guided spatial adaptation.
4. **Standalone Deliverable Suite**:
   - **Global Specimen Mesh**: `fig_f1711_adaptive_remesh_only.png` & `.pdf` ($65 \times 120\,\text{mm}$ specimen).
   - **Primary Corridor Zoom**: `fig_f1711_primary_mesh_zoom_only.png` & `.pdf` ($x \in [0, 42]$, $y \in [44, 76]\,\text{mm}$).
   - **Secondary Corridor Zoom**: `fig_f1711_secondary_mesh_zoom_only.png` & `.pdf` ($x \in [33, 66]$, $y \in [43, 59]\,\text{mm}$).
5. **Zero Additional Cluster Jobs**:
   - Governed submission quota strictly respected (`max_new_pbs_submissions = 0`). All geometric and nodal topology extracted directly from the verified input model.

---

## 2. Authentic Discretization Provenance

| Parameter / Field | Discretization Characteristic |
| :--- | :--- |
| **Source Model Deck** | `models/pandey_kumar_mode1/203_pk_sec43_secondary_complete/PK_SEC43_F1703_SECONDARY_COMPLETE_ADAPT.inp` |
| **Total Physical Elements** | Exactly **10,065 elements** ($9,724$ CPE4 quadrilaterals, $341$ CPE3 triangles) |
| **Total Physical Nodes** | Exactly **10,096 nodes** (plus 1 reference point node 999999) |
| **Coarse Bulk Element Size** | $h_{\text{coarse}} \approx 1.5 - 2.0\,\text{mm}$ |
| **Primary Refinement Zone** | $x \in [10.0, 32.0]\,\text{mm}, y \in [50.0, 72.0]\,\text{mm}$; element size $h \le \ell_0/2 = 0.143\,\text{mm}$ |
| **Secondary Refinement Zone** | $x \in [46.5, 65.0]\,\text{mm}, y \in [48.0, 56.0]\,\text{mm}$; element size $h \le \ell_0/5 \approx 0.051\,\text{mm}$ |
| **Primary Fracture Path** | Curved path originating at $(10, 70)$ and entering circular void at $(31.3, 62.5)$ |
| **Secondary Fracture Path** | Transverse path across the $18.56\,\text{mm}$ ligament from $(46.8, 50.6)$ to right free boundary $(64.8, 51.8)$ |
| **Simulation Provenance** | Meshed geometry solved to completion in Job `1421915.mmaster02` ($u_y = 1.50\,\text{mm}$, 4,500 increments, Exit 0) |

---

## 3. Deliverables & SHA-256 Provenance Ledger

| Artifact Description | Local Path | Format | SHA-256 Hash |
| :--- | :--- | :--- | :--- |
| **Adaptive Remesh (Full Specimen, PDF)** | `MA_AdaptiveRemeshing_Report_2026/figures/pandey_kumar_fig14_16_reproduction/fig_f1711_adaptive_remesh_only.pdf` | Vector PDF | `5BDCC38EFDE2D609E124A2568F573876F4388214FB273D02240F68B49BD78A50` |
| **Adaptive Remesh (Full Specimen, PNG)** | `MA_AdaptiveRemeshing_Report_2026/figures/pandey_kumar_fig14_16_reproduction/fig_f1711_adaptive_remesh_only.png` | 300-DPI PNG | `526EB0A394856612E1FCF58B06CFABDBBE603E7225622CC242465C6D39E6369C` |
| **Primary Process-Zone Zoom (PDF)** | `MA_AdaptiveRemeshing_Report_2026/figures/pandey_kumar_fig14_16_reproduction/fig_f1711_primary_mesh_zoom_only.pdf` | Vector PDF | `B960A07B476FDBE41843185371DA6C6EC04C0A1AB9C023D9AD844849ECE69C31` |
| **Primary Process-Zone Zoom (PNG)** | `MA_AdaptiveRemeshing_Report_2026/figures/pandey_kumar_fig14_16_reproduction/fig_f1711_primary_mesh_zoom_only.png` | 300-DPI PNG | `B5F25CFEEB66430B7E5CD37E7AC3D8CC78F5858115FE7171DAB015E660F9F024` |
| **Secondary Process-Zone Zoom (PDF)** | `MA_AdaptiveRemeshing_Report_2026/figures/pandey_kumar_fig14_16_reproduction/fig_f1711_secondary_mesh_zoom_only.pdf` | Vector PDF | `8B5344912C516CDD2A0082C19AC122ECBA50E9109392D7727C94584DF437BF6C` |
| **Secondary Process-Zone Zoom (PNG)** | `MA_AdaptiveRemeshing_Report_2026/figures/pandey_kumar_fig14_16_reproduction/fig_f1711_secondary_mesh_zoom_only.png` | 300-DPI PNG | `F06313E2B8A247405ACEC382054B8CFCD24B827997DB24663B3F9104702983ED` |
| **Mesh-Only Plotting Script** | `scripts/visualization/plot_f1711_clean_mesh_only.py` | Python 3 | `3ADFE889C211E5E614873F4A11AA08A72662FE849B627AC65DA4A3A294D19E7E` |
| **Unit Verification Suite** | `tests/unit/test_f1711_clean_mesh_only_visualization.py` | Pytest | `165528E5A1D6E357EF9E1DDE78D183B7F51BDC094018EE6089D1ACE461BFE8F5` |
| **Task Definition** | `project_coordination/task_definitions/F1711-CLEAN-MESH-ONLY-ADAPTIVE-REMESH-IMAGE.json` | JSON Data | `D9016D1DB7170E64671026F431EE8BA5113CAFA70B81A8F24BA060E0744A7F60` |

---

## 4. Disclaimers & Governance Discipline

1. The adapted finite-element mesh depicted in these figures is the authentic 10,065-element discretization generated offline by the multi-state history-aware adaptive remeshing workflow (Task F1703) and solved in Job `1421915.mmaster02`. It did **not** undergo dynamic online remeshing during the forward Abaqus solution.
2. In accordance with university thesis writing rules, this discretization is characterized as an error-guided adapted mesh with dual-corridor refinement.
3. The production UEL subroutine `f42_mixed_uel.for` remains bitwise identical (`CE8D5EDC...`, 907 lines) and was not modified.
