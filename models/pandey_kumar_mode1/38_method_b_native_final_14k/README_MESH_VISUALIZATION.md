# Method B Native Adaptive Mesh Visualization Package
**Pandey--Kumar Mode-I Benchmark (14,677 Finite Elements)**

**Date:** 2026-10-12  
**Agent:** Gemini Antigravity  
**Task:** F1427-MODE1-METHOD-B-MESH-VISUALIZATION-AND-C1-SUBMISSION  
**Model Deck:** `models/pandey_kumar_mode1/38_method_b_native_final_14k/M1_MB_NATIVE_FINAL_1S.inp` (SHA-256: `39CFD486C87A48A72F145919998E4FE698367DDA452B0F20C2E8F43EA13B0A6D`)

---

## 1. Executive Summary

This package provides publication-quality visualizations and reproducible standalone Python tools for visualizing the genuine **Method B native Abaqus CAE adapted mesh** (14,677 physical finite elements) directly from the underlying geometry without requiring Abaqus or multi-gigabyte `.odb` files.

The adapted mesh is generated automatically by Abaqus CAE's `adaptiveRemesh` engine driven by the pre-peak linear-elastic stress error indicator (`MISESERI`) from the Method B preliminary pre-analysis step ($u_{\text{pre}} = 0.0050\,\text{mm}$, $\alpha = 0.854$).

---

## 2. Discretization Architecture & Layer Decoupling

A critical distinction in this model is the separation between **unique physical geometry** and **co-located solver layers**:

| Layer | Type / Formulation | Elements | Purpose |
| :--- | :--- | :---: | :--- |
| **Layer 1** | Phase UEL (`U1` quads, `U3` tris) | 1 to 14,677 | Solves Phase-Field Helmholtz weak form (DOFs 3 = $d$) |
| **Layer 2** | Mechanical UEL (`U2` quads, `U4` tris) | 14,678 to 29,354 | Solves Mechanical momentum balance (DOFs 1, 2 = $u_x, u_y$) |
| **Layer 3** | Companion UMAT (`CPE4` quads, `CPE3` tris) | 29,355 to 44,031 | Infinitesimal tangent ($E_{\text{dummy}} = 10^{-11}\,\text{kN/mm}^2$), post-processing & energy field visualization |

- **Unique Physical Elements:** **14,677 elements** (14,244 quads, 433 triangles).
- **Total Co-located Records:** **44,031 element entries** in `M1_MB_NATIVE_FINAL_1S.inp`.
- **Mesh Nodes:** **14,646 unique nodes** (+ 1 Reference Point node 999999).
- **Domain Geometry:** Square plate $1.0 \times 1.0\,\text{mm}$ ($x \in [0, 1]$, $y \in [0, 1]$ mm).
- **Sharp Crack Seam:** $y = 0.5\,\text{mm}$, $0 \le x \le 0.5\,\text{mm}$ with **62 duplicate node pairs** across upper and lower crack flanks ($y = 0.5^+$ and $y = 0.5^-$) and **1 singleton tip node** (Node 135) at $(0.5, 0.5)\,\text{mm}$.

---

## 3. Discretization Resolution Contrast

Comparison between the 2,906-element coarse pre-analysis mesh and the 14,677-element Method B native adapted mesh:

| Metric | Coarse Baseline (`M1_PRE_1S`) | Method B Adapted (`M1_MB_NATIVE_FINAL_1S`) | Enhancement / Ratio |
| :--- | :---: | :---: | :---: |
| **Total Finite Elements** | 2,906 (2,818 quads, 88 tris) | 14,677 (14,244 quads, 433 tris) | $5.05\times$ global FE count |
| **Total Mesh Nodes** | 2,988 | 14,646 | $4.90\times$ nodal density |
| **Crack Tip Element Size ($h_{\text{tip}}$)** | $\approx 20.02\,\mu\text{m}$ | $\approx 1.91\,\mu\text{m}$ | **$10.5\times$ finer spatial sizing** |
| **Crack Tip Element Area ($A_{\text{tip}}$)** | $\approx 400.7\,\mu\text{m}^2$ | $\approx 3.80\,\mu\text{m}^2$ | **$105.4\times$ area density contrast** |
| **Median Element Size ($h_{\text{med}}$)** | $18.81\,\mu\text{m}$ | $6.07\,\mu\text{m}$ | $3.10\times$ median reduction |
| **Far-Field Element Size ($h_{\max}$)** | $25.75\,\mu\text{m}$ | $22.37\,\mu\text{m}$ | Preserves coarse far field |
| **Regularization Sizing ($l_0 / h_{\text{tip}}$)** | $0.37$ (Severely under-resolved) | **$3.93$ (Well-resolved: $> 3$ FEs across $l_0$)** | Standard guideline satisfied |

---

## 4. Generated Publication Figures

Figures are rendered in high resolution (300 DPI PNG) and vector PDF under `results/figures/mode1_method_b_mesh/`:

1. **`fig_mode1_method_b_native_full_mesh.png` / `.pdf`**:
   - Complete 1.0 × 1.0 mm specimen showing the global non-uniform refinement topology.
   - Highlights the initial sharp crack slit in red ($a_0 = 0.5\,\text{mm}$), the crack tip $(0.5, 0.5)\,\text{mm}$, the ligament ahead of the tip, boundary constraints ($u_y = 0$ on bottom, $u_x = u_y = 0$ at pinned origin, top displacement control), and the refinement corridor zoom box.
2. **`fig_mode1_method_b_native_crack_tip_zoom.png` / `.pdf`**:
   - Magnified crack-tip refinement corridor ($0.42 \le x, y \le 0.58\,\text{mm}$).
   - Shows individual element edges with element sizing color coding ($h = \sqrt{A}$).
   - Annotates upper and lower crack flanks, crack propagation direction, $50\,\mu\text{m}$ scale bar, and the phase-field length scale $l_0 = 7.5\,\mu\text{m}$.
3. **`fig_mode1_method_b_vs_coarse_comparison.png` / `.pdf`**:
   - 2 × 2 comparison panel:
     - Top row: Full-domain coarse (2,906 FE) vs Method B adapted (14,677 FE).
     - Bottom row: Crack-tip close-ups showing the $10.5\times$ local refinement and $105\times$ area density contrast.
4. **`fig_mode1_method_b_element_size_distribution.png` / `.pdf`**:
   - Subplot (a): 2D spatial colormap of characteristic size $h(x,y)$ over the full plate.
   - Subplot (b): Statistical histogram and probability density comparing coarse vs adapted element sizes against the $l_0 = 7.5\,\mu\text{m}$, $l_0/2 = 3.75\,\mu\text{m}$, and $h_{\text{tip}} \approx 1.91\,\mu\text{m}$ thresholds.

---

## 5. Standalone Reproduction Script

The visualization can be re-run at any time without Abaqus or license requirements:

```bash
# From repository root:
python scripts/visualization/plot_mode1_method_b_adaptive_mesh.py \
    --adapted-inp models/pandey_kumar_mode1/38_method_b_native_final_14k/M1_MB_NATIVE_FINAL_1S.inp \
    --coarse-inp models/pandey_kumar_mode1/method_b_preflight_decks/M1-MB-1S.inp \
    --outdir results/figures/mode1_method_b_mesh \
    --dpi 300
```
