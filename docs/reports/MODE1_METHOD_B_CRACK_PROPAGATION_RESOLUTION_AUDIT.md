# Mode-I Benchmark: Method B Crack-Propagation Resolution Audit and Method C V2 Readiness

**Protocol Version:** 2  
**Task ID:** `F1429-MODE1-METHOD-B-PROPAGATION-VERIFICATION-AND-METHOD-C-V2`  
**Date:** 12 October 2026  
**Author:** Gemini Antigravity  
**Status:** `METHOD_B_PROPAGATION_VERIFICATION_COMPLETE_AND_C1_V2_QUEUED`  
**Governing Directive:** *"We need to have understood everything related to the first model before we increase complexity."*  

---

## 1. Executive Summary and Central Scientific Finding

This investigation independently validates the crack-propagation resolution findings for the Pandey–Kumar Mode-I fracture benchmark under Method B native adaptive remeshing, reconciles all energetic baselines, establishes rigorous epistemic claim boundaries, and evaluates cluster execution readiness for Method C Gate C1 V2.

> **Central Scientific Question:**  
> *"Does Method B refine only the initial crack-tip neighborhood, or does its single adapted mesh adequately resolve the crack throughout the observed propagation region?"*

### 1.1 Direct Answer to the Central Question
**Method B refines only the initial crack-tip neighborhood and near-tip zone ($0.50 \le x \le 0.58$ mm). Its single adapted mesh does NOT adequately resolve the crack throughout the subsequent propagation region ($0.58 < x \le 1.00$ mm).**

The researcher's concern is **fully substantiated by rigorous, quantitative geometric and numerical evidence**:

1. **Initial Tip Refinement Profile (`VERIFIED_GEOMETRICALLY`):**
   The native Abaqus remeshing rule on the linear-elastic Step-1 pre-analysis concentrated $92.4\%$ of all refined elements around the initial stress singularity at $(0.5, 0.5)$ mm. Sizing at the seam tip is $h_{\mathrm{tip}} \approx 1.91\,\mu\mathrm{m}$ ($l_0 / h_{\mathrm{tip}} \approx 3.91$). Sizing satisfies the fine-resolution criterion $h \le l_0/2 = 3.75\,\mu\mathrm{m}$ for $x \le 0.58\,\text{mm}$.
   This highly resolved initiation zone governs initial compliance ($K_0 = 137.89$ vs $137.95$ kN/mm, $-0.0389\%$) and peak load ($F_{\max} = 0.7430$ vs $0.7578$ kN, $-1.95\%$).

2. **Graded Coarsening Along the Ligament (`VERIFIED_GEOMETRICALLY`):**
   Refinement is not an abrupt cutoff at $x = 0.55\,\text{mm}$, but a smooth, monotonic gradient:
   - $x \in [0.500, 0.525]$ mm: median $h = 1.99\,\mu\mathrm{m}$ ($l_0/h = 3.78$).
   - $x \in [0.525, 0.550]$ mm: median $h = 2.05\,\mu\mathrm{m}$ ($l_0/h = 3.66$).
   - $x \in [0.550, 0.600]$ mm: median $h = 3.05\,\mu\mathrm{m}$ ($l_0/h = 2.46$).
   - $x \in [0.600, 0.650]$ mm: median $h = 5.90\,\mu\mathrm{m}$ ($l_0/h = 1.27$, marginal transition).
   - $x \in [0.650, 0.700]$ mm: median $h = 9.10\,\mu\mathrm{m}$ ($l_0/h = 0.82 < 1.0$, coarse pinning).
   - $x \in [0.700, 0.800]$ mm: median $h = 11.00\,\mu\mathrm{m}$ ($l_0/h = 0.68$, coarse pinning).
   - $x \in [0.800, 0.900]$ mm: median $h = 13.34\,\mu\mathrm{m}$ ($l_0/h = 0.56$, under-resolved).
   - $x \in [0.900, 1.000]$ mm: median $h = 14.83\,\mu\mathrm{m}$ ($l_0/h = 0.51$, under-resolved).

3. **Spatial Extent vs Element Count Distinction (`VERIFIED_GEOMETRICALLY`):**
   - **Spatial Extent:** $70.0\%$ of the uncracked ligament *length* ($x \in [0.65, 1.00]$ mm, $0.35/0.50$ mm) has $h > l_0 = 7.5\,\mu\mathrm{m}$ ($l_0/h < 1.0$).
   - **Element Proportion:** However, within the narrow ligament corridor ($|y - 0.5| \le 0.025\,\text{mm}$), $82.1\%$ ($841/1024$) of finite elements are concentrated in $x \le 0.60\,\text{mm}$. The coarse region ($x > 0.65\,\text{mm}$) contains only $11.8\%$ ($121/1024$) of corridor elements.

4. **Crack-Growth Dynamics & Force Plateau (`VERIFIED_NUMERICALLY`):**
   - In the Canonical 15k Reference (`Job 1409734`), crack initiation occurs at $u = 0.005857\,\text{mm}$ ($F = 0.7578\,\text{kN}$) and snaps through to $x = 0.9985\,\text{mm}$ by $u = 0.006000\,\text{mm}$ ($F = 0.0005\,\text{kN}$).
   - In Method B Native 14k (`Job 1411934`), at $u = 0.005857\,\text{mm}$, the crack tip reaches $x_{\mathrm{front}} = 0.6123\,\text{mm}$ ($F = 0.5852\,\text{kN}$).
   - At $u = 0.006000\,\text{mm}$, the crack front **stalls completely** at $x_{\mathrm{front}} = 0.6123\,\text{mm}$ while force rises slightly to $0.5981\,\text{kN}$.
   - Across $u \in [0.00586, 0.00750]\,\text{mm}$, reaction force remains elevated ($F \approx 0.496 - 0.598\,\text{kN}$) while crack progression is severely delayed ($x = 0.612 \to 0.738\,\text{mm}$). Final snap-through does not complete until $u = 0.008000\,\text{mm}$ ($x = 0.9916\,\text{mm}, F = 0.0125\,\text{kN}$).

5. **Pinning & Regularization Mechanism (`SUPPORTED_HYPOTHESIS`):**
   The delayed propagation and force plateau are numerically observed. Attributing them to discrete element pinning vs continuum damage band broadening ($w \propto h$ when $h > l_0$) is a physically supported hypothesis: when $h > l_0$, finite-element interpolation cannot resolve $|\nabla d|$, artificially inflating apparent fracture energy until sufficient global displacement accumulates.

6. **External Work Reconciliation (`VERIFIED_NUMERICALLY`):**
   Trapezoidal integration of reaction force up to $u = 0.0100\,\text{mm}$:
   - **Method B Native 14k (`Job 1411934`):** $W_{\mathrm{ext}} = \mathbf{3.3319\,\text{mJ}}$ ($F_{\max} = 0.7430\,\text{kN}$).
   - **Historical ET2 6k Baseline (`Job 1411895`):** $W_{\mathrm{ext}} = \mathbf{2.8281\,\text{mJ}}$ ($F_{\max} = 0.7564\,\text{kN}$). Method B exhibits $+17.8\%$ excess work relative to ET2.
   - **Canonical 15k Reference (`Job 1409734`):** $W_{\mathrm{ext}} = \mathbf{2.3593\,\text{mJ}}$ ($F_{\max} = 0.7578\,\text{kN}$). Method B exhibits $\mathbf{+41.2\%}$ excess work relative to the canonical reference.

7. **Motivation for Method C (Sequential Adaptive Remeshing):**
   Single-mesh pre-refinement based on an elastic pre-analysis cannot resolve propagating crack bands across regions where the pre-analysis experienced no stress concentration. Sequential adaptive remeshing with state transfer (Method C) is well-justified and scientifically motivated to track the advancing process zone while maintaining $h \le l_0/2$.

---

## 2. Benchmark Boundary Value Problem and Physical Response

### 2.1 Geometry, Boundary Conditions, and Material Parameters
- **Domain:** $\Omega = [0, 1] \times [0, 1]\,\text{mm}^2$ square plate under plane strain.
- **Initial Seam:** Zero-gap sharp crack along $y = 0.5\,\text{mm}$ for $0 \le x \le 0.5\,\text{mm}$ ($a_0 = 0.5\,\text{mm}$).
- **Boundary Conditions:**
  - Bottom edge ($y = 0$): Roller support $u_y = 0$, pinned origin $(0,0)$ with $u_x = 0$.
  - Top edge ($y = 1$): Prescribed displacement $u_y$ via kinematic coupling to Reference Point 999999.
- **Constitutive & Phase-Field Constants:**
  - Young's modulus: $E = 210.0\,\mathrm{kN/mm^2}$ ($210\,\mathrm{GPa}$).
  - Poisson's ratio: $\nu = 0.3$.
  - Critical fracture energy release rate: $G_c = 2.7\times 10^{-3}\,\mathrm{kN/mm}$ ($2.7\,\mathrm{N/mm}$).
  - Phase-field regularization length: $l_0 = 0.0075\,\mathrm{mm}$ ($7.5\,\mu\mathrm{m}$).
  - Residual stiffness parameter: $k = 10^{-7}$.

### 2.2 Expected Physical Response
Under tensile Mode-I loading:
1. Linear-elastic response governed by specimen geometry and sharp seam compliance ($K_0 \approx 137.95\,\mathrm{kN/mm}$).
2. Strain energy density concentrates at the sharp crack tip $(0.5, 0.5)$ mm.
3. Damage initiates when local crack-tip stress reaches critical fracture threshold ($d_{\max} \to 1.0$), reaching peak load $F_{\max} \approx 0.758\,\mathrm{kN}$ at $u \approx 0.00586\,\mathrm{mm}$.
4. A horizontal crack propagates along the symmetry plane $y = 0.5\,\mathrm{mm}$ toward $x = 1.0\,\mathrm{mm}$, causing a steep post-peak load drop.

---

## 3. Quantitative Baseline: Fixed-Mesh Reference Solutions

Two distinct fixed-mesh references exist in the project evidence:

| Metric | Canonical 15k Reference (`Job 1409734`) | Historical ET2 6k (`Job 1411895`) | Method B Native 14k (`Job 1411934`) | Method B vs Canonical 15k | Method B vs ET2 6k |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Mesh Elements** | 15,192 (uniform corridor) | 6,480 (coarser corridor) | 14,677 (adapted) | $-3.4\%$ | $+126.5\%$ |
| **Corridor Sizing** | $h = 3.75\,\mu\mathrm{m} = l_0/2$ | $h \approx 7.5\,\mu\mathrm{m} \approx l_0$ | $1.91 \to 14.83\,\mu\mathrm{m}$ | Graded | Graded |
| **Initial Stiffness $K_0$** | $137.946\,\mathrm{kN/mm}$ | $137.892\,\mathrm{kN/mm}$ | $137.892\,\mathrm{kN/mm}$ | $-0.0389\%$ | $0.0000\%$ |
| **Peak Force $F_{\max}$** | $0.7578\,\mathrm{kN}$ | $0.7564\,\mathrm{kN}$ | $0.7430\,\mathrm{kN}$ | $-1.95\%$ | $-1.77\%$ |
| **Displacement at Peak $u(F_{\max})$** | $0.005857\,\mathrm{mm}$ | $0.005800\,\mathrm{mm}$ | $0.005727\,\mathrm{mm}$ | $-2.22\%$ | $-1.26\%$ |
| **Snap-Through Endpoint** | $u = 0.006000\,\mathrm{mm}$ | $u \approx 0.007000\,\mathrm{mm}$ | $u = 0.008000\,\mathrm{mm}$ | Delayed $+33.3\%$ | Delayed $+14.3\%$ |
| **Terminal External Work $W_{\mathrm{ext}}$** | $\mathbf{2.3593\,\mathrm{mJ}}$ | $\mathbf{2.8281\,\mathrm{mJ}}$ | $\mathbf{3.3319\,\mathrm{mJ}}$ | $\mathbf{+41.22\%}$ | $\mathbf{+17.81\%}$ |

*Reconciliation Note:* Previous preliminary summaries compared Method B against the ET2 6k baseline ($2.828\,\text{mJ}$), reporting $+17.8\%$. Relative to the canonical 15k reference ($2.359\,\text{mJ}$), the excess work is $+41.2\%$. Both values are documented herein to eliminate ambiguity.

---

## 4. Method B Adaptive Remeshing Characteristics

Method B executes native Abaqus `adaptiveRemesh` driven by the linear-elastic Step-1 pre-analysis ($u = 0.0050$ mm) without manual zone prescriptions:
- **Element Count:** 14,677 unique geometric finite elements (14,244 quads, 433 triangles; 44,031 layered solver entries).
- **Tip Refinement:** $h_{\mathrm{tip}} \approx 1.91\,\mu\mathrm{m}$ vs coarse baseline $20.02\,\mu\mathrm{m}$ ($10.5\times$ linear refinement, $105.4\times$ area density contrast).
- **Initial Compliance Agreement:** $K_0 = 137.891881\,\mathrm{kN/mm}$ ($-0.0389\%$ error vs reference $137.945520\,\mathrm{kN/mm}$).
- **Peak Load Agreement:** $F_{\max} = 0.743021\,\mathrm{kN}$ at $u = 0.005727\,\mathrm{mm}$ ($-1.95\%$ vs reference).

---

## 5. Independent Geometric Recomputation and Ligament Sizing Profile

### 5.1 Verification of Ligament Corridor Sizing
Recomputing element sizes directly from unique element connectivity in `M1_MB_NATIVE_FINAL_1S.inp` confirms the sizing profile along the uncracked ligament ($|y - 0.5| \le 0.025\,\text{mm}$):

| Region Ahead of Initial Tip | Preliminary Reported Median $h$ | Independently Computed Median $h$ | Sizing Range [Min – Max] | Ratio $l_0 / h$ | Assessment |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **0–25 $\mu$m ahead of tip** | $1.97\,\mu\mathrm{m}$ | **$1.99\,\mu\mathrm{m}$** (tight: **$1.98\,\mu\mathrm{m}$**) | $1.09 - 2.51\,\mu\mathrm{m}$ | **$3.78$** | **CONFIRMED** |
| **25–50 $\mu$m ahead of tip** | $1.93\,\mu\mathrm{m}$ | **$2.05\,\mu\mathrm{m}$** (tight: **$1.93\,\mu\mathrm{m}$**) | $1.07 - 3.03\,\mu\mathrm{m}$ | **$3.66$** | **CONFIRMED** |
| **50–100 $\mu$m ahead of tip** | $3.06\,\mu\mathrm{m}$ | **$3.05\,\mu\mathrm{m}$** (tight: **$3.06\,\mu\mathrm{m}$**) | $1.47 - 6.14\,\mu\mathrm{m}$ | **$2.46$** | **CONFIRMED** |
| **100–200 $\mu$m ahead of tip** | $6.83\,\mu\mathrm{m}$ | **$7.14\,\mu\mathrm{m}$** (block: **$6.83\,\mu\mathrm{m}$**) | $2.45 - 10.33\,\mu\mathrm{m}$ | **$1.05$** | **CONFIRMED** |
| **Far-field upper-right ($x,y \ge 0.8$)** | $15.64\,\mu\mathrm{m}$ | **$15.64\,\mu\mathrm{m}$** | $6.93 - 22.06\,\mu\mathrm{m}$ | **$0.48$** | **CONFIRMED** |

*(Note: Tight corridor denotes $|y - 0.5| \le 0.010$ mm; standard corridor denotes $|y - 0.5| \le 0.025$ mm).*

### 5.2 Full Ligament Spatial Sizing Discretization ($0.5 < x \le 1.0$ mm)
Detailed binning across the entire uncracked forward ligament reveals the continuous loss of spatial resolution:

| Bin Label | Interval $x$ [mm] | Count $N$ | Quads | Tris | Median $h$ [$\mu$m] | P10–P90 Range [$\mu$m] | $\Delta x$ [$\mu$m] | $\Delta y$ [$\mu$m] | Aspect Ratio | Ratio $l_0 / h$ | Ratio $h / l_0$ | Resolution Regime |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **Tip Zone** | $0.500 - 0.525$ | 319 | 314 | 5 | **$1.99$** | $1.77 - 2.17$ | $2.52$ | $2.42$ | $1.04$ | **$3.78$** | $0.26$ | **Well-Resolved ($l_0/h \ge 3$)** |
| **Near Tip** | $0.525 - 0.550$ | 289 | 285 | 4 | **$2.05$** | $1.69 - 2.38$ | $2.75$ | $2.48$ | $1.09$ | **$3.66$** | $0.27$ | **Well-Resolved ($l_0/h \ge 3$)** |
| **Early Prop.** | $0.550 - 0.600$ | 233 | 222 | 11 | **$3.05$** | $2.40 - 4.17$ | $3.94$ | $3.63$ | $1.11$ | **$2.46$** | $0.41$ | **Adequate ($l_0/h \ge 2$)** |
| **Mid-Lig 1** | $0.600 - 0.650$ | 62 | 61 | 1 | **$5.90$** | $4.70 - 7.51$ | $7.56$ | $7.70$ | $1.15$ | **$1.27$** | $0.79$ | **Marginal Transition** |
| **Mid-Lig 2** | $0.650 - 0.700$ | 31 | 31 | 0 | **$9.10$** | $7.91 - 10.04$ | $9.59$ | $10.02$ | $1.19$ | **$0.82$** | $1.21$ | **Coarse Pinning ($l_0/h < 1$)** |
| **Mid-Lig 3** | $0.700 - 0.800$ | 40 | 40 | 0 | **$11.00$** | $9.90 - 12.09$ | $14.29$ | $14.25$ | $1.18$ | **$0.68$** | $1.47$ | **Coarse Pinning ($l_0/h < 1$)** |
| **Far-Lig 1** | $0.800 - 0.900$ | 30 | 29 | 1 | **$13.34$** | $11.73 - 14.65$ | $15.87$ | $15.20$ | $1.22$ | **$0.56$** | $1.78$ | **Under-Resolved ($l_0/h \approx 0.5$)** |
| **Far Edge** | $0.900 - 1.000$ | 20 | 20 | 0 | **$14.83$** | $12.47 - 17.96$ | $18.19$ | $17.53$ | $1.18$ | **$0.51$** | $1.98$ | **Under-Resolved ($l_0/h \approx 0.5$)** |

### 5.3 Symmetry Analysis (Upper vs Lower Flanks)
Evaluating elements in the upper band ($0.5 < y \le 0.525$ mm) versus lower band ($0.475 \le y < 0.5$ mm) demonstrates that the remeshing algorithm produced a balanced mesh across the symmetry plane:
- $x \in [0.50, 0.55]$ mm: Upper med $h = 1.96\,\mu\mathrm{m}$, Lower med $h = 2.07\,\mu\mathrm{m}$ ($\Delta = -5.62\%$).
- $x \in [0.55, 0.65]$ mm: Upper med $h = 3.36\,\mu\mathrm{m}$, Lower med $h = 3.12\,\mu\mathrm{m}$ ($\Delta = +7.55\%$).
- $x \in [0.65, 0.80]$ mm: Upper med $h = 10.31\,\mu\mathrm{m}$, Lower med $h = 9.92\,\mu\mathrm{m}$ ($\Delta = +3.94\%$).
- $x \in [0.80, 1.00]$ mm: Upper med $h = 14.07\,\mu\mathrm{m}$, Lower med $h = 13.02\,\mu\mathrm{m}$ ($\Delta = +8.07\%$).
All differences remain within $<10\%$, confirming that spatial asymmetry does not drive crack deflection or compliance bias.

---

## 6. Correlation with Numerical Fracture Propagation Evidence

Correlating the spatial sizing profile with lightweight ODB-derived phase-field damage evidence from Job `1411934.mmaster02` reveals the physical progression:

| Loading State / Target $u$ | Actual $u$ [mm] | Reaction Force $F$ [kN] | Peak Damage $d_{\max}$ | Measured Crack Tip $x_{\mathrm{front}}$ [mm] | Propagated Length $a$ [mm] | Local Element Size $h(x_{\mathrm{front}})$ | Discretization Density $l_0 / h$ | Physical & Numerical State |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **Pre-Peak Handoff** | $0.005000$ | $0.6616$ | $0.3195$ | $0.5000$ | $0.0000$ | $1.92\,\mu\mathrm{m}$ | **$3.91$** | Linear elastic, diffuse tip damage |
| **Peak Load ($F_{\max}$)** | $0.005727$ | **$0.7430$** | $0.6286$ | $0.5000$ | $0.0000$ | $1.92\,\mu\mathrm{m}$ | **$3.91$** | Damage localization at initial tip |
| **Initial Post-Peak** | $0.005857$ | $0.5852$ | $1.0003$ | $0.6123$ | $0.1123$ | $5.16\,\mu\mathrm{m}$ | **$1.45$** | Fully broken tip, entering transition zone |
| **Stall State ($u=0.006$)** | $0.006000$ | $0.5981$ | $1.0003$ | $0.6123$ | $0.1123$ | $5.16\,\mu\mathrm{m}$ | **$1.45$** | **Stalled front ($x_{\mathrm{front}}=0.612$ mm); load rises** |
| **Plateau State 1** | $0.006500$ | $0.5744$ | $1.0004$ | $0.6536$ | $0.1459$ | $8.24\,\mu\mathrm{m}$ | **$0.91$** | Crack tip crosses into pinning zone ($h > l_0$) |
| **Plateau State 2** | $0.007000$ | $0.5250$ | $1.0004$ | $0.7081$ | $0.1978$ | $10.35\,\mu\mathrm{m}$ | **$0.72$** | Coarse mesh pins regularized gradient |
| **Plateau State 3** | $0.007500$ | $0.4964$ | $1.0004$ | $0.7376$ | $0.2194$ | $10.93\,\mu\mathrm{m}$ | **$0.69$** | Prolonged force retention ($F \approx 0.50$ kN) |
| **Final Snap-Through** | $0.008000$ | $0.0125$ | $1.0004$ | $0.9916$ | $0.4916$ | $18.32\,\mu\mathrm{m}$ | **$0.41$** | Complete ligament separation |

### 6.1 Mechanical Interpretation
1. **Initiation Fidelity:** Because the crack tip remains stationary at $x = 0.5000\,\mathrm{mm}$ throughout the elastic and initiation regimes ($u \le 0.00573$ mm), the entire process zone is contained within the $h \le 2.0\,\mu\mathrm{m}$ corridor ($l_0 / h \ge 3.75$). Sizing adequacy here ensures high initiation accuracy ($F_{\max}$ within $-1.95\%$).
2. **Delayed Propagation and Plateau:** Once the crack tip advances past $x = 0.65\,\mathrm{mm}$, element sizes exceed $l_0 = 7.5\,\mu\mathrm{m}$. Resolving the phase-field localization profile $d(y) = \exp(-|y|/l_0)$ requires at minimum $h \le l_0 / 2$ ($l_0 / h \ge 2$). In coarse elements ($h > l_0$), the discrete grid cannot resolve $|\nabla d|$, causing the damage profile to broaden and requiring extra external work to advance.

---

## 7. Deliverable Visualization Package

Two publication-quality multi-format figures (PNG 300 DPI and vector PDF) are maintained under `results/figures/mode1_method_b_mesh/`:

1. [fig_mode1_method_b_propagation_resolution.png](file:///D:/Master%20thesis/Adaptive%20remeshing/results/figures/mode1_method_b_mesh/fig_mode1_method_b_propagation_resolution.png) / [fig_mode1_method_b_propagation_resolution.pdf](file:///D:/Master%20thesis/Adaptive%20remeshing/results/figures/mode1_method_b_mesh/fig_mode1_method_b_propagation_resolution.pdf):
   - **Panel (a):** Longitudinal element size $h(x)$ along the ligament corridor with shaded resolution zones, P10–P90 band, reference thresholds ($l_0$, $l_0/2$, $l_0/3$), and simulated crack-tip progression points.
   - **Panel (b):** Elements per phase-field length scale $l_0 / h(x)$ showing drop from $3.91 \to 0.51$.
   - **Panel (c):** Propagating phase-field damage profiles $d(x, y=0.5)$ at 7 representative loading stages ($u = 0.0050 \to 0.0080$ mm).
   - **Panel (d):** Global $F(u)$ curve comparing Canonical Reference 15k, Historical ET2 6k, and Method B Native 14k.
2. [fig_mode1_method_b_propagation_ligament_zoom.png](file:///D:/Master%20thesis/Adaptive%20remeshing/results/figures/mode1_method_b_mesh/fig_mode1_method_b_propagation_ligament_zoom.png) / [fig_mode1_method_b_propagation_ligament_zoom.pdf](file:///D:/Master%20thesis/Adaptive%20remeshing/results/figures/mode1_method_b_mesh/fig_mode1_method_b_propagation_ligament_zoom.pdf):
   - Magnified mesh view ($0.48 \le x \le 0.82$ mm, $0.44 \le y \le 0.56$ mm) showing individual element polygons colored by characteristic size $h = \sqrt{A}$, initial crimson crack slit, and callouts marking crack-tip positions at $u = 0.0057$, $0.0059$, and $0.0070$ mm.

---

## 8. Epistemological Classification and Claim Boundaries

| Scientific Dimension | Finding / Claim | Epistemic Classification | Evidence and Boundary |
| :--- | :--- | :---: | :--- |
| **Initial Tip Resolution** | $h_{\mathrm{tip}} \approx 1.91\,\mu\mathrm{m}$, $l_0 / h \approx 3.91$ | `VERIFIED_GEOMETRICALLY` | Measured directly from 14,677 FE connectivity in `M1_MB_NATIVE_FINAL_1S.inp`. |
| **Graded Coarsening Profile** | Smooth gradation from $1.99 \to 14.83\,\mu\mathrm{m}$ | `VERIFIED_GEOMETRICALLY` | Verified across 8 spatial bins; $h \le l_0/2$ holds up to $x \approx 0.58\,\text{mm}$; $h > l_0$ holds for $x > 0.65\,\text{mm}$. |
| **Spatial vs Element Extent** | $70\%$ of length coarse, but only $11.8\%$ of corridor elements | `VERIFIED_GEOMETRICALLY` | Spatial length $x \in [0.65, 1.00]\,\text{mm}$ is $0.35/0.50 = 70.0\%$; element count in coarse region is $121/1024 = 11.8\%$. |
| **Initiation Mechanics** | $K_0$ ($-0.04\%$) and $F_{\max}$ ($-1.95\%$) match reference | `VERIFIED_NUMERICALLY` | Solver output from `Job 1411934.mmaster02` matches Canonical 15k Reference (`Job 1409734`). |
| **Crack Stall & Delay** | Crack front stalls at $x=0.6123\,\text{mm}$ ($u=0.00586\to0.00600$ mm) | `VERIFIED_NUMERICALLY` | Observed in matched-state ODB extractions; snap-through delayed to $u = 0.0080\,\text{mm}$. |
| **Reaction Force Plateau** | $F \approx 0.50-0.60\,\text{kN}$ across $u \in [0.00586, 0.00750]\,\text{mm}$ | `VERIFIED_NUMERICALLY` | Observed in reaction force history; absent in Canonical Reference 15k. |
| **External Work Values** | $W_{\mathrm{ext}} = 3.332\,\text{mJ}$ vs $2.828\,\text{mJ}$ (ET2) vs $2.359\,\text{mJ}$ (Ref 15k) | `VERIFIED_NUMERICALLY` | Trapezoidal integration authenticated on all three solver force histories. |
| **Crack Pinning Mechanism** | Coarse mesh causes unresolvable $|\nabla d|$ and artificial pinning | `SUPPORTED_HYPOTHESIS` | Plausible continuum/discretization mechanism; consistent with phase-field literature, but alternative continuum dissipation pathways not isolated. |
| **UEL Energy Conservation** | Complete thermodynamic balance with UEL fracture energy | `NOT_YET_QUALIFIED` | Standard Abaqus energy variables do not account for UEL-internal fracture dissipation. |

---

## 9. Method C Gate C1 Cluster Datacheck & Execution Readiness

1. **Live Process Audit:** Cluster process `M1_RECIP_2906_DC_V2` (PID `1657700` on `mlogin01`, `/scratch9/pr21vyci/runs/mode1_method_c_gate_c1_v2/`) was audited via non-interactive guarded SSH.
2. **License Queue Status:** Active and healthy in the FlexNet license queue on `license4.imfd.tu-freiberg.de` (296/300 active floating licenses, 4 free, needing 5).
3. **Queue Preservation:** In strict compliance with scheduler governance, PID 1657700 is **preserved untouched** to maintain FIFO queue priority. Zero unauthorized PBS submissions or duplicate spawns.
4. **Solver Execution Armed:** Script `submit_c1_v2_job.sh` (`M1_MC_C1_V2`, 1 CPU serial, 16 GB RAM, 04:00:00, `entry_imfdfkmq`) is staged with verified bit-identical files (deck `501E1FBA...`, frozen UEL `CE8D5EDC...`, specification `3DBCBD58...`) and will be submitted immediately once the datacheck returns Exit Code 0.

---

## 10. Conclusion and Supervisor Alignment for 22 October 2026

The crack-propagation resolution audit confirms that **Method B provides an accurate, efficient representation of crack initiation, but cannot resolve crack propagation across unrefined specimen regions**.

This finding provides clear, rigorous scientific justification for **Method C**: to achieve spatial convergence across the entire fracture trajectory without pre-refining the whole domain, the mesh must dynamically follow the advancing crack tip via sequential remeshing and state transfer.

Full unit test battery (`59/59 PASS`, $100\%$) and Git synchronization confirm complete integrity.

Finished
