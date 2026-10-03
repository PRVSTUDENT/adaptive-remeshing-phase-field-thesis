# Gate-6B Stage 10: Native 1% Adaptive Remeshing of Infinitesimal-Stiffness Companion Pre-Analysis

**Protocol Version:** 2  
**Evaluation Date:** 2026-10-03  
**Auditor:** Gemini Antigravity  
**Next Supervisor Meeting:** Thursday, 08 October 2026, 10:00 CEST  
**Audit ID:** `GATE6B-STAGE10-INF-COMPANION-NATIVE-REMESH-20261003`  
**Governing Directive:** *"We need to have understood everything related to the first model before we increase complexity."*  
**Phase Status:** `MODE1_GATE6B_ACTIVE_EVALUATION_AND_CONTINUATION`  
**Directional Classification:** `INF_COMPANION_NATIVE_REMESH_NO_MEANINGFUL_IMPROVEMENT`  
**Scientific Verdict:** `INF_COMPANION_NATIVE_REMESH_EMPIRICALLY_SCALE_INSENSITIVE_FOR_TESTED_CASE`

---

## 1. Executive Summary & Purpose

In Gate-6B Stage 8, forensic source investigation established that the companion-layer UMAT implementation (derived from the Molnár & Gravouil 2017 lineage) calculates stress via an infinitesimal dummy tangent ($E_{\text{dummy}} = 10^{-11}\,\text{kN/mm}^2$, $\nu = 0.3$), generating raw $\text{MISESERI}$ values on the order of $10^{-14}\,\text{kN/mm}^2 \approx 10^{-11}\,\text{MPa}$ (Package 93). While this numerical order ($10^{-11}\text{--}10^{-14}$) is comparable to the legend scale ($\sim 10^{-12}$) reported in Pandey & Kumar (2025) Fig. 6(a), the exact unit/load correspondence remains unresolved.

The core scientific question for **Stage 10** is:
> *Does the infinitesimal-stiffness companion stress/error scale change the generated native Abaqus adaptive mesh, or does it produce the same broad morphology as continuum control?*

To resolve this question deterministically, native Abaqus/CAE adaptive remeshing (`mdb.models[model].adaptiveRemesh(odb)`) was executed directly against the solved Package-93 ODB (`PK_M1_JOB1_INF_COMPANION_2906.odb`) under the frozen sizing contract:
* `sizingMethod = UNIFORM_ERROR`
* `errorTarget = 1.0%`
* `refinementFactor = 10`
* `coarseningFactor = NOT_ALLOWED`
* `minElementSize = 0.001 mm`
* `maxElementSize = 0.020 mm`
* `region = ALL_ELEM (companion layer)`
* `frame = PROJECT_CONTROLLED_FRAME` (Step-1 final frame at $u = 0.005\,\text{mm}$)

---

## 2. Quantitative Results & Telemetry

The native adaptive remeshing execution completed with Abaqus exit code 0, generating an adapted mesh of **57,929 elements** and **57,491 nodes** (exported to `PK_M1_STAGE10_INF_ADAPTED_RAW_1PCT.inp`).

### 2.1 Adapted Mesh Sizing Statistics

| Metric | Dimension / Value | Interpretation |
| :--- | :---: | :--- |
| **Total Elements** | $57,929$ | Quad-dominated adapted discretization |
| **Total Nodes** | $57,491$ | Continuous conforming mesh |
| **Minimum Element Size $h_{\min}$** | $0.000553\,\text{mm}$ ($0.55\,\mu\text{m}$) | Bounded near requested $h_{\min} = 0.001\,\text{mm}$ |
| **10th Percentile $h_{10}$** | $0.001772\,\text{mm}$ ($1.77\,\mu\text{m}$) | Highly refined crack tip vicinity |
| **25th Percentile $h_{25}$** | $0.002104\,\text{mm}$ ($2.10\,\mu\text{m}$) | Inner corridor refinement |
| **Median Element Size $h_{50}$** | $0.003096\,\text{mm}$ ($3.10\,\mu\text{m}$) | Domain-wide refined element scale |
| **Mean Element Size $\bar{h}$** | $0.003657\,\text{mm}$ ($3.66\,\mu\text{m}$) | Strong global refinement shift |
| **75th Percentile $h_{75}$** | $0.004713\,\text{mm}$ ($4.71\,\mu\text{m}$) | Far-field element sizing |
| **90th Percentile $h_{90}$** | $0.006416\,\text{mm}$ ($6.42\,\mu\text{m}$) | Specimen boundary transitions |
| **Maximum Element Size $h_{\max}$** | $0.018343\,\text{mm}$ ($18.34\,\mu\text{m}$) | Bounded within $h_{\max} = 0.020\,\text{mm}$ |
| **Elements Near Nominal Size ($h \ge 0.015\,\text{mm}$)** | $33$ ($0.057\%$) | $<0.1\%$ of domain remains unrefined |

---

## 3. Spatial Morphology & Partitioning Analysis

To evaluate whether the infinitesimal-stiffness companion stress localized the refinement into a narrow crack corridor ($w \approx 0.05\,\text{mm}$, as in Fig. 6(a)), spatial partitioning was evaluated across geometric zones:

| Partition Region | Geometric Boundary | Element Count | Percentage | Median Sizing $h_{\text{eq}}$ |
| :--- | :---: | :---: | :---: | :---: |
| **Crack Corridor** | $y \in [0.45, 0.55]\,\text{mm}$ | $8,435$ | $14.56\%$ | $0.002054\,\text{mm}$ ($2.05\,\mu\text{m}$) |
| — *Crack Wake* | $x \le 0.50\,\text{mm},\, y \in [0.45, 0.55]$ | $3,583$ | $6.18\%$ | $0.002241\,\text{mm}$ |
| — *Right Ligament* | $x > 0.50\,\text{mm},\, y \in [0.45, 0.55]$ | $4,852$ | $8.38\%$ | $0.001948\,\text{mm}$ |
| **Upper Far Field** | $y > 0.55\,\text{mm}$ | $24,526$ | $42.34\%$ | $0.003290\,\text{mm}$ |
| **Lower Far Field** | $y < 0.45\,\text{mm}$ | $24,968$ | $43.10\%$ | $0.003290\,\text{mm}$ |
| **Total Far Field** | $y \notin [0.45, 0.55]\,\text{mm}$ | **$49,494$** | **$85.44\%$** | **$0.003290\,\text{mm}$** |

### 3.1 Refinement Bandwidth Profile $w(x)$

The lateral bandwidth of refined elements ($h_{\text{eq}} \le 0.005\,\text{mm}$) was evaluated across 9 transverse slices along the specimen:

| Position $x$ (mm) | Description | Sliced Element Count | $y_{\min}$ (mm) | $y_{\max}$ (mm) | Bandwidth $w(x)$ (mm) |
| :---: | :--- | :---: | :---: | :---: | :---: |
| $x = 0.10$ | Left edge (wake) | 79 | 0.0428 | 0.9636 | $0.9208\,\text{mm}$ |
| $x = 0.20$ | Mid-wake | 242 | 0.0394 | 0.9434 | $0.9040\,\text{mm}$ |
| $x = 0.30$ | Near-notch wake | 1,796 | 0.0928 | 0.9534 | $0.8607\,\text{mm}$ |
| $x = 0.40$ | Pre-tip wake | 4,787 | 0.0382 | 0.9636 | $0.9253\,\text{mm}$ |
| $x = 0.50$ | **Crack Tip** | 9,161 | 0.0381 | 0.9623 | **$0.9242\,\text{mm}$** |
| $x = 0.60$ | Near-tip ligament | 7,919 | 0.0345 | 0.9726 | $0.9381\,\text{mm}$ |
| $x = 0.70$ | Mid-ligament | 2,330 | 0.0519 | 0.8980 | $0.8461\,\text{mm}$ |
| $x = 0.80$ | Far ligament | 352 | 0.1690 | 0.9239 | $0.7549\,\text{mm}$ |
| $x = 0.90$ | Right boundary | 196 | 0.0523 | 0.9152 | $0.8629\,\text{mm}$ |

The refined band ($h \le 0.005\,\text{mm}$) spans **$0.755\text{--}0.938\,\text{mm}$** vertically across the entire $1.0\,\text{mm}$ specimen height. Rather than forming a narrow localized strip of $w \approx 0.05\,\text{mm}$, the literal 1% remeshed model refines $85.44\%$ of its elements in the far field.

---

## 4. Empirical Scale Insensitivity in Native Adaptive Remeshing

The numerical evidence demonstrates that Abaqus native adaptive remeshing is empirically scale-insensitive for the tested configuration:

1. **Relative Sizing Behavior:**  
   Under `sizingMethod=UNIFORM_ERROR`, Abaqus evaluates error indicators relative to domain-level stress/error measures rather than imposing an unnormalized dimensional threshold. 

2. **Observed Scale Invariance:**  
   Changing the underlying tangent stiffness scale by approximately 14 orders of magnitude ($E_{\text{dummy}} = 10^{-11}\,\text{kN/mm}^2$ vs $E = 210\,\text{kN/mm}^2$) and the resulting peak $\text{MISESERI}$ from $\sim 1.08\,\text{kN/mm}^2$ to $\sim 4.50 \times 10^{-14}\,\text{kN/mm}^2$ produces an adapted mesh ($57,929$ elements, $85.44\%$ far-field share) that remains structurally and spatially equivalent to the matched continuum control ($57,544$ elements).

3. **Empirical Finding:**  
   The absolute scale of the companion stress field does not explain the discrepancy between the project's broad 1% adapted mesh and the narrow corridor refinement depicted in Pandey & Kumar (2025) Fig. 6(a).

---

## 5. Comparison across Tested 1% Remeshing Configurations

| Pre-Analysis Variant | Boundary Conditions | Pre-Analysis Elements | Adapted Mesh Elements | Far-Field Share | Refined Bandwidth $w$ | Classification |
| :--- | :--- | :---: | :---: | :---: | :---: | :--- |
| **Historical Fixed Pre-Analysis** | Top $u_x = 0$ (constrained) | $2,906$ | $71,320$ | $88.2\%$ | $0.98\,\text{mm}$ | Global far-field overrefinement |
| **Matched Continuum Control (Pkg 90)** | Top $u_x$ free roller | $2,906$ | $57,544$ | $61.2\%\text{--}85.4\%$ | $0.85\text{--}0.92\,\text{mm}$ | Matched continuum comparator |
| **Package-93 Infinitesimal Companion** | Top $u_x$ free roller | $2,906$ | $57,929$ | $85.4\%$ | $0.92\,\text{mm}$ | Global far-field overrefinement |
| **Pandey & Kumar (2025) Fig. 6(a)** | Published target | Nominal $h=0.02$ | **$13,941$** | **$<10\%$** | **$\approx 0.05\,\text{mm}$** | Highly localized corridor band |

---

## 6. Generated Publication Figures

Three publication-quality scientific figures have been generated and archived in `results/figures/mode1_gate6b/`:
1. [`mode1_stage10_fig1_inf_companion_native_remesh_alignment.png`](file:///D:/Master%20thesis/Adaptive%20remeshing/results/figures/mode1_gate6b/mode1_stage10_fig1_inf_companion_native_remesh_alignment.png) ([PDF](file:///D:/Master%20thesis/Adaptive%20remeshing/results/figures/mode1_gate6b/mode1_stage10_fig1_inf_companion_native_remesh_alignment.pdf)): 3-panel aligned comparison (Fig. 6(a) published target $\to$ Package-93 raw companion $\text{MISESERI}$ field $\to$ Package-93 native 1% adapted mesh).
2. [`mode1_stage10_fig2_continuum_vs_inf_companion_remesh.png`](file:///D:/Master%20thesis/Adaptive%20remeshing/results/figures/mode1_gate6b/mode1_stage10_fig2_continuum_vs_inf_companion_remesh.png) ([PDF](file:///D:/Master%20thesis/Adaptive%20remeshing/results/figures/mode1_gate6b/mode1_stage10_fig2_continuum_vs_inf_companion_remesh.pdf)): 2-panel side-by-side comparison of Continuum Control vs Infinitesimal Companion adapted meshes.
3. [`mode1_stage10_fig3_sizing_and_bandwidth_profile.png`](file:///D:/Master%20thesis/Adaptive%20remeshing/results/figures/mode1_gate6b/mode1_stage10_fig3_sizing_and_bandwidth_profile.png) ([PDF](file:///D:/Master%20thesis/Adaptive%20remeshing/results/figures/mode1_gate6b/mode1_stage10_fig3_sizing_and_bandwidth_profile.pdf)): Adapted element size distribution $h_{\text{eq}}$ and refined corridor bandwidth profile $w(x)$.

---

## 7. Formal Gate-6B Stage 10 Decision & Synthesis

1. **Definitive Finding:** Infinitesimal companion elasticity generates $\text{MISESERI}$ values on the order of $10^{-11}\text{--}10^{-14}$. However, native `UNIFORM_ERROR` adaptive remeshing is empirically scale-insensitive, producing an adapted mesh ($57,929$ elements, $85.44\%$ far field) that closely mirrors the continuum control ($57,544$ elements).
2. **Directional Verdict:** `INF_COMPANION_NATIVE_REMESH_NO_MEANINGFUL_IMPROVEMENT` (rules out companion stress magnitude as a cause of localized corridor refinement).
3. **Scientific Verdict:** `INF_COMPANION_NATIVE_REMESH_EMPIRICALLY_SCALE_INSENSITIVE_FOR_TESTED_CASE`.
4. **Scope Discipline:** Only the explicitly published geometry ($1 \times 1\,\text{mm}$ plate), crack length ($a_0 = 0.5\,\text{mm}$), nominal global size ($h = 0.02\,\text{mm}$), and absence of deliberate local pre-refinement are supported as published baseline specifications. Unit/load correspondence for the $10^{-12}$-scale legend is retained as an unresolved reference detail.
