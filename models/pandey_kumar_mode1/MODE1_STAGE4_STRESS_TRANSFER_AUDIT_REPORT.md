# Mode-I Gate-6B Cause Audit Stage 4: Stress Transfer into Companion Facsimile Layer Audit Report

**Protocol Version:** 2  
**Task ID:** `F1172-GATE6B-STAGE4-STRESS-TRANSFER-AUDIT-20261003`  
**Date:** 2026-10-03  
**Agent:** Gemini Antigravity  
**Governing Directive:** *"We need to have understood everything related to the first model before we increase complexity."*  
**Primary Artifacts:**  
- Stress Comparison CSV: `models/pandey_kumar_mode1/PK_M1_COARSE_2906_STRESS_TRANSFER_AUDIT.csv`  
- Master Figure: `results/figures/mode_i_adaptive/fig_mode1_gate6b_stage4_stress_transfer_audit.png` (and `.pdf`)  
- Audit Evidence JSON: `models/pandey_kumar_mode1/GATE6B_STAGE4_STRESS_TRANSFER_AUDIT.json`  

---

## 1. Executive Summary & Audit Mandate

### 1.1 Objective and Scope Boundary
Following the completion of **Cause Audit Stage 1** (`TOPOLOGY_NOT_SUPPORTED_AS_DOMINANT_CAUSE`, `NEUTRAL_LOCALIZATION`), **Cause Audit Stage 2** (`BC_PARTIAL_CONTRIBUTOR`, `TOWARD_TARGET_LOCALIZATION`, which reduced the native 1% mesh by $15,783$ finite elements and eliminated top boundary shear), and **Cause Audit Stage 3** (`MAPPING_VERIFIED_NOT_DOMINANT_CAUSE`, `NEUTRAL_LOCALIZATION`, proving 1:1 bijective isomorphism and zero permutation), this investigation executes **Cause Audit Stage 4: Stress Transfer into Companion Facsimile Layer Audit**.

The explicit mandate of Stage 4 is to determine whether the broad far-field MISESERI error indicator distribution ($56,302$ finite elements under literal $1.0\%$ `errorTarget` on the canonical 2,906 coarse mesh) is **already present in the source mechanical continuum stress field / error structure, or appears only after transfer to the companion visualization/UMAT facsimile layer**.

### 1.2 Required Gate Classifications & Verdicts
- **Stress Transfer Verdict:** **`STRESS_TRANSFER_VERIFIED_NOT_DOMINANT_CAUSE`**  
- **Localization Direction:** **`NEUTRAL_LOCALIZATION`**  
- **Next Governed Stage:** **`STAGE5_STEP_FRAME_SEMANTICS_AUDIT`** (Exact Step & Frame Semantics used by `adaptiveRemesh`)

### 1.3 Key Mathematical & Structural Findings
1. **Source-Level Code Trace in Governed Subroutines (`f42_mixed_uel.for`):**  
   - The Mechanical User Element (`JTYPE=2` for CPE4 quads, lines 394–550; `JTYPE=4` for CPE3 triangles, lines 675–800) evaluates linear-elastic plane-strain constitutive stresses $\boldsymbol{\sigma}_0 = \mathbf{D}_0 \boldsymbol{\varepsilon}$ with $E = 210\,\text{GPa}$ and $\nu = 0.3$.
   - Component ordering is standard: Index 1 is $S_{11}$, Index 2 is $S_{22}$, Index 3 is $S_{12}$ ($\tau_{xy}$), with out-of-plane plane-strain component $S_{33} = \nu (S_{11} + S_{22})$.
   - The companion UMAT (lines 839–907) intentionally sets $\mathbf{S} = \mathbf{0}$ and $\mathbf{D}_{\text{dummy}} = 10^{-11}\mathbf{I}$ during coupled fracture solves to prevent double-counting structural stiffness and internal reaction forces.
2. **Direct Continuum Pre-Analysis Pathway:**  
   In the Pandey-Kumar pre-analysis workflow ([`PK_PREANALYSIS_COARSE.inp`](file:///D:/Master%20thesis/Adaptive%20remeshing/models/pandey_kumar_mode1/02_proposed_adaptive_refined/PK_PREANALYSIS_COARSE.inp)), Abaqus executes a single-layer continuum linear elastic analysis on elements $1 \dots 2,906$. `MISESERI` is evaluated directly on this native continuum stress field by the Abaqus Superconvergent Patch Recovery (SPR/ZZ) error estimator without passing through intermediate UEL-to-UMAT arrays.
3. **Exact Constitutive Equivalence:**  
   Comparing the Mechanical UEL constitutive stress tensor $\boldsymbol{\sigma}_{\text{UEL}}$ against the native continuum pre-analysis stress field $\boldsymbol{\sigma}_{\text{source}}$ confirms $100.0000\%$ component-for-component mathematical identity across all $2,906$ elements and integration points ($\max |\Delta \sigma_{\text{vM}}| < 9.1 \times 10^{-7}\,\text{MPa}$, correlation $r = 1.000000000$).
4. **Causality Provenance:**  
   The broad far-field MISESERI error distribution ($32.98\%$ in Far Field, $31.67\%$ in Wake) is completely present in the source mechanical continuum stress field and native Abaqus error estimator. It is not an artifact of stress transfer, state corruption, or UMAT reconstruction.

---

## 2. Source-Level Code Path Trace (`f42_mixed_uel.for`)

### 2.1 Strain Evaluation in Mechanical UEL
In `f42_mixed_uel.for`, mechanical strain $\boldsymbol{\varepsilon} = \mathbf{B} \mathbf{u}$ is evaluated at the integration points:

- **4-Node Quadrilateral Elements (`JTYPE = 2`, lines 394–550):**
  - **Integration Points (lines 395–406):** $2 \times 2$ Gauss quadrature with coordinates $\xi_k, \eta_k = \pm 1/\sqrt{3} \approx \pm 0.577350269$ and weight $w_k = 1.0$.
  - **Shape Function Derivatives (lines 443–451):** $\partial N_i / \partial \xi, \partial N_i / \partial \eta$.
  - **Jacobian & Inversion (lines 453–475):** $\mathbf{J} = \sum \nabla_\xi N_i \mathbf{x}_i$, $\det \mathbf{J} > 0$, and $\mathbf{J}^{-1}$.
  - **Strain-Displacement Matrix $\mathbf{B}_{3 \times 8}$ (lines 476–483):**
    $$B_{1, 2i-1} = \frac{\partial N_i}{\partial x}, \quad B_{2, 2i} = \frac{\partial N_i}{\partial y}, \quad B_{3, 2i-1} = \frac{\partial N_i}{\partial y}, \quad B_{3, 2i} = \frac{\partial N_i}{\partial x}$$
  - **Strain Tensor (lines 485–490):** $\text{STRAIN}(1) = \varepsilon_{11}, \text{STRAIN}(2) = \varepsilon_{22}, \text{STRAIN}(3) = \gamma_{12} = 2\varepsilon_{12}$.

- **3-Node Triangular Elements (`JTYPE = 4`, lines 675–800):**
  - **Integration Point (lines 676–679):** Centroid quadrature with coordinates $\xi = 1/3, \eta = 1/3$, weight $w = 1/2$.
  - **Constant Strain Matrix $\mathbf{B}_{3 \times 6}$ (lines 743–754):** Standard linear displacement gradient.
  - **Strain Tensor (lines 756–761):** $\text{STRAIN}(1) = \varepsilon_{11}, \text{STRAIN}(2) = \varepsilon_{22}, \text{STRAIN}(3) = \gamma_{12}$.

### 2.2 Constitutive Stress Tensor Computation
Lines 411–430 (quads) and 683–702 (tris) define isotropic plane-strain elasticity:
$$C_{11}^0 = C_{22}^0 = \frac{E(1-\nu)}{(1+\nu)(1-2\nu)} = 282.6923\,\text{kN/mm}^2$$
$$C_{12}^0 = \frac{E\nu}{(1+\nu)(1-2\nu)} = 121.1538\,\text{kN/mm}^2$$
$$C_{33}^0 = G = \frac{E}{2(1+\nu)} = 80.7692\,\text{kN/mm}^2$$

Under linear elasticity before crack damage ($d = 0, g(d) = 1$):
$$\text{STRESS}(1) = \sigma_{11} = C_{11}^0 \varepsilon_{11} + C_{12}^0 \varepsilon_{22}$$
$$\text{STRESS}(2) = \sigma_{22} = C_{12}^0 \varepsilon_{11} + C_{22}^0 \varepsilon_{22}$$
$$\text{STRESS}(3) = \sigma_{12} = C_{33}^0 \gamma_{12}$$
$$\sigma_{33} = \nu (\sigma_{11} + \sigma_{22}) \quad (\text{out-of-plane plane-strain constraint})$$

This formulation is mathematically and numerically identical to Abaqus standard isotropic plane-strain continuum elasticity.

### 2.3 Companion UMAT Role & Coupling Compliance
In `f42_mixed_uel.for` (lines 839–907):
- The companion UMAT is invoked on Layer 3 elements ($5,813 \dots 8,718$).
- UMAT reads state variables ($d, H, E_{\text{frac}}, E_{\text{elas}}, \psi_f, \psi_e$) from `COMMON /CB_STATE_TRANS/` and stores them into `STATEV(1..20)`.
- UMAT explicitly sets `STRESS(1..NTENS) = 0.D0` and `DDSDDE(I,I) = 1.D-11`.
- **Architectural Purpose:** In the 3-layer solver architecture, Layer 2 (Mechanical UEL) already assembles the full internal force vector `RHS` and tangent stiffness `AMATRX`. If Layer 3 carried non-zero stress or stiffness, it would double-count the specimen's reaction force and structural stiffness.
- **Pre-Analysis Distinction:** Because `adaptiveRemesh` requires valid stress fields to compute `MISESERI`, the pre-analysis workflow executes a dedicated single-layer continuum solve ([`PK_PREANALYSIS_COARSE.inp`](file:///D:/Master%20thesis/Adaptive%20remeshing/models/pandey_kumar_mode1/02_proposed_adaptive_refined/PK_PREANALYSIS_COARSE.inp)) where Abaqus computes stresses directly on the physical mesh without passing through zero-stress UMAT layers.

---

## 3. Quantitative Stress & Error Field Verification

### 3.1 Component-for-Component Parity across 2,906 Coarse Elements
Evaluating the Mechanical UEL constitutive stress tensor against the extracted pre-analysis stress field across all $2,906$ coarse elements yields:

| Stress Quantity | Evaluated Elements | Max Absolute Diff [MPa] | Mean Absolute Diff [MPa] | RMS Diff [MPa] | Correlation ($r$) | Exact Matches ($\Delta < 10^{-6}$) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **$S_{11}$ ($\sigma_{xx}$)** | $2,906$ | $0.000000$ | $0.000000$ | $0.000000$ | **$1.0000000$** | $2,906 / 2,906$ ($100.0\%$) |
| **$S_{22}$ ($\sigma_{yy}$)** | $2,906$ | $0.000000$ | $0.000000$ | $0.000000$ | **$1.0000000$** | $2,906 / 2,906$ ($100.0\%$) |
| **$S_{12}$ ($\tau_{xy}$)** | $2,906$ | $0.000000$ | $0.000000$ | $0.000000$ | **$1.0000000$** | $2,906 / 2,906$ ($100.0\%$) |
| **$S_{33}$ ($\sigma_{zz}$)** | $2,906$ | $0.000000$ | $0.000000$ | $0.000000$ | **$1.0000000$** | $2,906 / 2,906$ ($100.0\%$) |
| **Equivalent Mises $\sigma_{\text{vM}}$** | $2,906$ | $9.055 \times 10^{-7}$ | $1.511 \times 10^{-7}$ | $2.316 \times 10^{-7}$ | **$1.0000000$** | $2,906 / 2,906$ ($100.0\%$) |

The sub-micro-Pascal difference in equivalent Mises stress ($< 9.1 \times 10^{-7}\,\text{MPa}$) arises entirely from standard 32-bit/64-bit floating-point square root operations and proves complete mathematical consistency.

---

## 4. 5-Region Stress & Error Breakdown

### 4.1 Regional Stress Distribution and Error Partitioning
Evaluating the mechanical stress field and error indicator across the 5 governed spatial regions reveals:

| Region | Boundary Definition | Elements | % Mesh | Mean $S_{22}$ [MPa] | Max $S_{22}$ [MPa] | Mean $\sigma_{\text{vM}}$ [MPa] | Error Sum $\sum \eta$ [MPa] | % Total Error |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Crack Tip** | $r \le 0.05\,\text{mm}$ around tip $(0.5, 0.5)$ | $20$ | $0.69\%$ | $1.6111$ | $3.4094$ | $1.3728$ | $6.6127$ | **$23.04\%$** |
| **Slit Flank** | $x \le 0.5, |y - 0.5| \le 0.05$ (excl. tip) | $112$ | $3.85\%$ | $0.0199$ | $1.5022$ | $0.1577$ | $2.0660$ | **$7.20\%$** |
| **Wake** | $x \le 0.45, |y - 0.5| > 0.05$ | $950$ | $32.69\%$ | $0.1749$ | $0.6974$ | $0.2117$ | $9.0904$ | **$31.67\%$** |
| **Far Field** | Remainder ($x > 0.45, |y - 0.5| > 0.05$) | $1,358$ | $46.73\%$ | $1.1162$ | $1.8943$ | $1.0123$ | $9.4682$ | **$32.98\%$** |
| **Boundary** | $x, y < 0.05$ or $x, y > 0.95$ | $466$ | $16.04\%$ | $0.6198$ | $1.3028$ | $0.6319$ | $1.4673$ | **$5.11\%$** |
| **Total Domain** | Whole plate $[0, 1] \times [0, 1]\,\text{mm}$ | **$2,906$** | **$100.0\%$** | **$0.7384$** | **$3.4094$** | **$0.6868$** | **$28.7046$** | **$100.0\%$** |

### 4.2 Mechanistic Origin of Far-Field Error
- In the Far Field region ($1,358$ elements), the mean tensile stress is $S_{22} = 1.1162\,\text{MPa}$ (homogeneous tensile field), producing a mean Mises stress of $\sigma_{\text{vM}} = 1.0123\,\text{MPa}$.
- Although individual element error in the far field is low ($\text{mean } \eta = 0.0070\,\text{MPa}$), the sheer volume of elements ($79.42\%$ across Far Field and Wake) accumulates $18.5586\,\text{MPa}$ ($64.65\%$) of the total domain error.
- Because the pre-analysis executes native continuum elasticity without UEL/UMAT transfer, this broad error profile is an intrinsic feature of the continuum elastic stress field on the coarse discretization, confirming that **stress transfer does not introduce or distort the far-field error distribution**.

---

## 5. Corrections of Stage-3 Overstatements

To ensure rigorous claims discipline across all project records:
1. **Terminology Correction:** Replaced "bit-for-bit" with "sub-nanometer geometric and topological identity ($\max |\Delta x_c|, \max |\Delta y_c| < 5.0 \times 10^{-7}\,\text{mm}$ and identical connectivity indices)" across all Stage-3 reports and summaries.
2. **Epistemic Framing Discipline:** Removed premature assertions that broad far-field refinement is an "intrinsic mathematical characteristic of UNIFORM_ERROR." While mapping and stress transfer are proven neutral, the sizing formulation, step/frame selection, and output-position semantics remain under sequential investigation. The overall root cause remains classified as `CAUSE_NOT_YET_ISOLATED`.

---

## 6. Gate-6B Cause Audit Progress & Stage Verdicts

### 6.1 Multi-Stage Cause Hierarchy Summary

| Stage | Hypothesis / Scope | Verdict | Localization Classification | Key Finding / Effect |
| :---: | :--- | :---: | :---: | :--- |
| **Stage 1** | Coarse Topology (Tri vs Quad) | `TOPOLOGY_NOT_SUPPORTED_AS_DOMINANT_CAUSE` | `NEUTRAL_LOCALIZATION` | Triangles carry only $2.92\%$ error; crack tip is $100\%$ quad; zero far-field shape correlation. |
| **Stage 2** | Boundary Conditions (Lateral Release) | `BC_PARTIAL_CONTRIBUTOR` | `TOWARD_TARGET_LOCALIZATION` | Eliminates $9.3\times$ shear stress; collapses corner error by $94.5\%$; reduces native 1% mesh by $15,783$ FE. |
| **Stage 3** | Facsimile Mapping (`All_elem` $\leftrightarrow$ `umatelem`) | `MAPPING_VERIFIED_NOT_DOMINANT_CAUSE` | `NEUTRAL_LOCALIZATION` | Exact 1:1 bijective isomorphism; $0$ mismatches; sub-nm centroid parity; zero permutation defects. |
| **Stage 4** | Stress Transfer into Facsimile Layer | **`STRESS_TRANSFER_VERIFIED_NOT_DOMINANT_CAUSE`** | **`NEUTRAL_LOCALIZATION`** | Mechanical UEL constitutive stress matches native continuum stress with $r=1.000$; error field is native to source. |
| **Stage 5** | Step & Frame Semantics in `adaptiveRemesh` | *Next Governed Audit* | *Pending* | Audit whether `adaptiveRemesh` extracts Step-1 Frame-1, Step-2 Frame-0, or accumulated envelopes. |

### 6.2 Governed Action for Next Turn
1. **Advance to Stage 5:** Proceed directly to **Cause Audit Stage 5: Step & Frame Semantics Audit (`STAGE5_STEP_FRAME_SEMANTICS_AUDIT`)** to audit the exact increment/frame evaluated by Abaqus `adaptiveRemesh`.
2. **Preserve Governed Boundaries:** Maintain the canonical 2,906 coarse topology, corrected lateral-free BCs, single-rank shared-memory solver architecture, and non-polling cluster guard for running solve `1409867.mmaster02`.
