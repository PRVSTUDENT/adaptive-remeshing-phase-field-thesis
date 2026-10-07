# Mode-II Current State and Governed Lineage

**Last Updated:** 2026-10-07 12:00 CEST  
**Governing Phase:** `MODE2_SPATIAL_PATH_AUDIT_AND_ADAPTIVE_MESH_VALIDATION` (Task F1290)  
**Governing Agent:** Gemini Antigravity  
**Audit Status:** `AUDIT_FAILED: NATIVE_ADAPTIVE_MESH_DOES_NOT_FOLLOW_MODE2_CRACK_PATH`  
**Execution Boundary:** **STRICT SOLVER GATE -- ZERO SOLVER RUNS AUTHORIZED**

---

## 1. Executive Summary & Authoritative Status

1. **Spatial Trajectory Audit Verdict:**
   - The native adaptive mesh generated from the coarse UEL pre-analysis (`JOB_MODE2_ADAPTIVE_ET2.inp`, 21,496 FE) and its reconstructed 3-layer UEL production deck (`Job-2_UEL.inp`, 64,488 layered elements) **UNEQUIVOCALLY FAIL** the spatial trajectory audit.
   - Discretization Status: **`FAILED_SPATIAL_TRAJECTORY_AUDIT`**.
   - Solver Status: **`FRACTURE_SOLVE_STRICTLY_ON_HOLD`**.

2. **Core Physical Finding:**
   - Although the adaptive mesh achieves +7.68% element count parity with the literature mesh of Pandey & Kumar (2025, Fig. 12b: 19,963 FE vs. ET2: 21,496 FE), **element-count similarity is not a physical validity criterion**.
   - The fine mesh zone ($h \le 0.004\,\text{mm}$, $h/l_0 \le 0.267$) does **not** follow the physical Mode-II crack trajectory (which inclines downwards from the notch tip $(0.5, 0.5)$ towards the bottom boundary at $\theta \approx -53.65^\circ$, exiting at $x \approx 0.868\,\text{mm}$).
   - Instead, the fine zone is concentrated along the horizontal ligament ($y \approx 0.50\,\text{mm}$), the notch flank seam ($x \le 0.5\,\text{mm}$), and the Dirichlet boundaries ($y = 0.0\,\text{mm}$ and $y = 1.0\,\text{mm}$).
   - The critical active Mode-II crack corridor ($x \ge 0.50\,\text{mm}, y \in [0.15, 0.35]\,\text{mm}$) contains **exactly 2 fine elements ($0.02\%$ of fine elements)** and remains completely unrefined ($h \approx 0.015 - 0.020\,\text{mm}$).
   - Only **20.0%** of the physical Mode-II crack trajectory is covered by the refined mesh zone (only the immediate tip vicinity for $x \in [0.50, 0.59]\,\text{mm}$).
   - Over **58.3%** of the fine elements (4,784 of 8,200 elements) are completely off-path.

3. **Historical / Legacy Disambiguation:**
   - The earlier **7,865-element** Mode-II adaptive simulation (Job `M2_adapt_prod`, 24 September 2026) and its associated documentation (`docs/mode2/archive_pre_stage15c/`) represent an older, superseded preliminary workflow.
   - It is **strictly superseded** and permanently preserved in the dedicated immutable Git archive branch: `archive/legacy-mode2-pre-stage15c-2026-10-07`.

---

## 2. Quantitative Spatial Trajectory Comparison Table

| Metric / Parameter | Literature Benchmark (Pandey & Kumar Fig. 12b) | Pre-Analysis UEL Localized Ridge (Job 1410178) | Adapted Native Mesh ET2 Refined Zone (`JOB_MODE2_ADAPTIVE_ET2.inp`) | Audit Evaluation / Discrepancy |
| :--- | :---: | :---: | :---: | :---: |
| **Propagation Angle $\theta$** | $\mathbf{-53.65^\circ}$ (kinking down) | $\mathbf{-7.80^\circ}$ (nearly horizontal) | Horizontal band along $y \approx 0.50$ | **$\Delta\theta = +45.85^\circ$ mismatch** |
| **Boundary Exit Location** | Bottom edge $(0.868, 0.000)\,\text{mm}$ | Right edge $(1.000, 0.380)\,\text{mm}$ | N/A (does not reach boundary) | Completely different boundary exit |
| **Path Normal Distance to Fig. 12(b)** | $0.000\,\text{mm}$ (reference) | Mean: $0.2310\,\text{mm}$, Max: $0.3075\,\text{mm}$ | Mean: $0.0558\,\text{mm}$, Max: $0.1389\,\text{mm}$ | Severe spatial deviation |
| **Corridor Width / Definition** | $d_{\text{corr}} = \pm 0.050\,\text{mm}$ ($3.33\,l_0$) | Ridge tracking threshold $d > 0.50$ | Refinement criterion $h \le 0.004\,\text{mm}$ | Rigorous spatial corridor |
| **Fine Elements in Expected Corridor** | Expected $\sim 10,000+$ elements | N/A (coarse run: 2,960 FE) | **3,416 elements (41.7%)** | Deficient ($< 50\%$) |
| **Fine Elements Off-Path** | Expected $< 20\%$ | N/A | **4,784 elements (58.3%)** | Spurious refinement dominant |
| **Expected Crack Path Covered** | $100\%$ | $0.0\%$ (diverged path) | **20.0%** ($x \in [0.50, 0.59]\,\text{mm}$ only) | **80% of crack path UNREFINED** |
| **Active Crack Zone ($y \in [0.15, 0.35], x \ge 0.5$)** | Dense refinement ($h \approx 0.002 - 0.004\,\text{mm}$) | $d \approx 0$, MISESERI $\approx 10^{-18}$ | **EXACTLY 2 ELEMENTS (0.02%)** | **Unrefined coarse mesh ($h \approx 0.020\,\text{mm}$)** |
| **Spurious Boundary Refinement** | Not observed in literature | Stress concentrations at corners | Top ($y \ge 0.95$): 913 FE (11.1%)<br>Bottom ($y \le 0.05$): 943 FE (11.5%) | 1,856 spurious boundary FE (22.6%) |
| **Notch Flank Refinement** | Crack tip only | Notch flank stress concentration | $x \le 0.50, y \approx 0.50$: 2,060 FE (25.1%) | 2,060 flank elements (25.1%) |
| **Total Finite Elements** | 19,963 FE (Fig. 12b) | 2,960 FE (coarse pre-analysis) | 21,496 FE (20,934 CPE4 + 562 CPE3) | $+7.68\%$ vs literature |

---

## 3. Systematic Failure Classification & Root Cause Diagnosis

The 9 candidate failure mechanisms have been rigorously evaluated against the empirical data:

### Primary Root Cause 1: Formulation Defect in `f42_mixed_uel.for` (Isotropic Shear Degradation)
- **Mechanism:** In `f42_mixed_uel.for` (lines 416-419), all mechanical stiffness components are degraded isotropically by `DEG = (1-d)^2 + k`:
  ```fortran
  C11_MECH = C11_0 * DEG
  C33_MECH = C33_0 * DEG
  POS_M = C12_0*HALF*E_POS**2 + C33_0*(E11**2 + E22**2 + TWO*E12**2)
  ```
- **Consequence:** The shear strain component $\varepsilon_{12}$ drives damage indiscriminately without directional spectral splitting. Under pure shear loading ($\gamma_{xy}$), the damage initiates along the maximum shear plane ($\theta = 0^\circ$, horizontal plane ahead of the notch). As damage accumulates, shear stiffness across this horizontal slip plane collapses to $k \cdot \mu \approx 10^{-6} \mu$. This triggers a numerical shear slip band / horizontal unzipping that propagates straight across to the right boundary at $y \approx 0.38\,\text{mm}$.
- **Contrast with Literature:** Pandey & Kumar (2025, Section 4.2, p. 14) explicitly state that they employ the **Miehe et al. (2010) anisotropic strain energy split**, which separates tensile and compressive principal strains:
  $$\psi_0^+(\boldsymbol{\varepsilon}) = \frac{1}{2}\lambda \langle \mathrm{tr}(\boldsymbol{\varepsilon}) \rangle_+^2 + \mu \mathrm{tr}(\boldsymbol{\varepsilon}_+^2)$$
  Under pure shear, the principal strain state consists of equal tension and compression inclined at $\pm 45^\circ$. In the Miehe formulation, only the tensile principal strain ($\theta = -45^\circ$) is degraded, preventing shear slip and driving the crack along the maximum tensile stress kink angle ($\theta \approx -53.65^\circ$).

### Primary Root Cause 2: Coarse Pre-Analysis Mesh Resolution Defect ($h > l_0$)
- **Mechanism:** The coarse pre-analysis mesh `Job-1_UEL.inp` was seeded with $h_{\text{global}} = 0.020\,\text{mm}$, which is **coarser than the phase-field length scale** $l_0 = 0.015\,\text{mm}$ ($h/l_0 = 1.33 > 1.0$).
- **Consequence:** In standard phase-field theory, the regularization requires at least $h \le l_0/2$ to resolve the diffuse interface. Running a phase-field fracture analysis on a coarse mesh ($h > l_0$) causes mesh-induced localization instabilities, artificial notch-tip locking, and spurious shear band localization along mesh element row boundaries.

### Secondary Mechanism: Native Remeshing Error Propagation
- **Mechanism:** The Abaqus native remeshing generator (`UNIFORM_ERROR`) strictly obeyed the MISESERI error distribution extracted from Job 1410178.
- **Consequence:** Because Job 1410178 localized horizontally and produced zero damage ($d \approx 0$) and zero error indicator ($10^{-18}$) in the lower region ($y \in [0.0, 0.35]$), the remeshing algorithm had no signal to refine the physical crack corridor. It refined the horizontal unzipped band, the pre-existing notch flanks, and the Dirichlet boundary layers where stress concentrations occurred.

### Ruled-Out Candidate Mechanisms:
- **Seam Node Topology:** Intact and correct (93 duplicate pairs, 1 tip node, verified coordinate matches).
- **RP 999999 Coupling:** Kinematically verified (rigid top shear constraint correctly formulated).
- **Triangular CPE3 Elements:** Present only at transition zones (562 CPE3 out of 21,496, 2.6%), patch-test verified, not the cause of path deflection.
- **Execution Platform / HPC Environment:** Job 1410178 ran with zero errors on `/scratch9/` compute node `mnode097`.

---

## 4. Strict Artifact Classification Matrix

All Mode-II assets in this repository are categorized under four mutually exclusive governance tiers:

| Tier | Directory / Asset Path | Description & Provenance | Governed Status |
| :--- | :--- | :--- | :---: |
| **`CANONICAL_CURRENT`** | `models/pandey_kumar_mode2/06_paper_grounded_uel_preanalysis/Job-1_UEL.inp` | Paper-grounded coarse pre-analysis input deck (2,960 FE, 3,036 FE nodes, 8,880 layered elements, $h_{\text{global}} = 0.020\,\text{mm}$; SHA256: `869A2DBD...`) | Active Master Input |
| **`CANONICAL_CURRENT`** | `models/pandey_kumar_mode2/06_paper_grounded_uel_preanalysis/f42_mixed_uel.for` | Dual-element UEL Fortran source (SHA256: `FA48CB4D...`) | Active Master UEL (Isotropic Formulation) |
| **`CANONICAL_CURRENT`** | Cluster Job `1410178.mmaster02` (`M2_J1_UEL_PRE`) | Solved on `/scratch9/` compute node `mnode097`, completed Step 2 Frame 5021 ($u_x = 0.01500\,\text{mm}$), Exit 0 | Qualified Reference (Deflected Path) |
| **`FAILED_AUDIT`** | `models/pandey_kumar_mode2/04_adaptive_miseseri/JOB_MODE2_ADAPTIVE_ET2.inp` | Native adaptive mesh (21,496 FE: 20,934 CPE4 + 562 CPE3; 21,615 native nodes; SHA256: `E137BDC3...`) | **FAILED_SPATIAL_TRAJECTORY_AUDIT** |
| **`FAILED_AUDIT`** | `models/pandey_kumar_mode2/06_paper_grounded_uel_preanalysis/Job-2_UEL.inp` | Production 3-layer UEL fracture model deck (64,488 layered elements, 21,616 nodes including RP 999999; SHA256: `6B07E499...`) | **Datacheck Pass; FRACTURE SOLVE ON HOLD** |
| **`CANONICAL_CURRENT`** | `scripts/validation/audit_mode2_spatial_trajectory.py` | Turnkey spatial trajectory audit tool (SHA256: `0E42198A...`) | Active Master Audit Tool |
| **`CANONICAL_CURRENT`** | `results/figures/mode2/audit_fig[1-5]_*` | 5 publication-grade spatial trajectory audit figures (PNG + PDF) | Canonical Evidence |
| **`DIAGNOSTIC_ONLY`** | `models/pandey_kumar_mode2/00_aux_continuum_preanalysis` | Auxiliary continuum elasticity pre-analysis for baseline comparison | Diagnostic Reference |
| **`DIAGNOSTIC_ONLY`** | `models/pandey_kumar_mode2/05_tri_patch_test` | Abaqus CPE3/triangular element integration and patch verification | Diagnostic Reference |
| **`SUPERSEDED`** | `models/pandey_kumar_mode2/04_adaptive_miseseri/ModeII_adaptive_candidate.inp` | Older 7,865-element preliminary adaptive mesh (Sept 24) | Superseded by ET2 21.5k |
| **`SUPERSEDED`** | `docs/mode2/archive_pre_stage15c/` | Older 7,865-element report, figures, and manifests | Superseded (Archived) |
| **`SUPERSEDED`** | `models/pandey_kumar_mode2/01_baseline_h0`, `02_reference_h1`, `03_ultrafine_h2` | Preliminary uniform meshes from pre-Stage-15C exploration | Superseded (Archived) |
| **`INVALID_FAILED`** | Job `1410125.mmaster02` (`M2_J1_UEL_PRE`) | Stopped administratively for `/home` storage compliance; replaced cleanly by Job 1410178 | Administratively Terminated |

---

## 5. Reconciled Canonical Mesh Discretization & Topology Metrics

| Discretization Metric | Coarse Pre-Analysis Mesh (`Job-1_UEL.inp` / Job 1410178) | Raw Native Adapted ET2 Mesh (`JOB_MODE2_ADAPTIVE_ET2.inp`) | Reconstructed 3-Layer UEL Production Deck (`Job-2_UEL.inp`) |
| :--- | :---: | :---: | :---: |
| **Finite Elements (FE)** | **2,960 FE** (2,860 CPE4 + 100 CPE3) | **21,496 FE** (20,934 CPE4 + 562 CPE3) | **21,496 FE** (underlying physical mesh) |
| **Deck Elements (Total)** | **8,880 elements** ($3 \times 2,960$) | **21,496 elements** (single physical layer) | **64,488 elements** ($3 \times 21,496$) |
| **- Layer 1 (Phase UEL)** | 2,860 U1 quads + 100 U3 tris (2,960) | N/A (single layer) | 20,934 U1 quads + 562 U3 tris (21,496) |
| **- Layer 2 (Mech UEL)** | 2,860 U2 quads + 100 U4 tris (2,960) | N/A (single layer) | 20,934 U2 quads + 562 U4 tris (21,496) |
| **- Layer 3 (Companion UMAT)** | 2,860 CPE4 quads + 100 CPE3 tris (2,960) | N/A (single layer) | 20,934 CPE4 quads + 562 CPE3 tris (21,496) |
| **Native FE Mesh Nodes** | **3,036 FE nodes** (IDs 1..3036) | **21,615 FE nodes** (IDs 1..21615) | **21,615 FE nodes** (preserved intact) |
| **Deck Nodes (Total)** | **3,037 nodes** (3,036 FE + 1 RP) | **21,615 nodes** | **21,616 nodes** (21,615 FE + 1 RP) |
| **Reference Point (RP)** | Node 999999 at $(0.5, 1.0)$ | None | Node 999999 at $(0.5, 1.0)$ |
| **Pre-existing Seam Nodes** | Boundary-constrained notch | 187 nodes (93 duplicate pairs + 1 tip) | 187 nodes (93 duplicate pairs + 1 tip) |
| **Global / Background Sizing** | $h_{\text{global}} = \mathbf{0.020\,\text{mm}}$ ($0.02\,\text{mm}$) | $h_{\text{global}} = \mathbf{0.020\,\text{mm}}$ | $h_{\text{global}} = \mathbf{0.020\,\text{mm}}$ |
| **Corridor Refined Sizing** | Unrefined coarse baseline | $h_{\text{refined}} \approx 0.00412\,\text{mm}$, $h_{\min} \approx 0.00076\,\text{mm}$ | $h_{\text{refined}} \approx 0.00412\,\text{mm}$, $h_{\min} \approx 0.00076\,\text{mm}$ |
| **Literature Parity Baseline** | Auxiliary pre-analysis anchor | $+7.68\%$ vs 19,963 FE (Pandey & Kumar Fig 12b) | $+7.68\%$ vs 19,963 FE (Pandey & Kumar Fig 12b) |

---

## 6. Publication Figures Generated (Canonical Evidence)

The 5 publication-grade trajectory audit figures have been generated and archived under `results/figures/mode2/`:

1. **`audit_fig1_pandey_kumar_reference_paths` (.png / .pdf):**
   - Digitized and parameterized reference Mode-II crack paths from literature and benchmarks:
     - Pandey & Kumar (2025) Fig. 12(b): $\theta = -53.65^\circ$, exit $(0.868, 0.000)\,\text{mm}$.
     - Pandey & Kumar (2025) Fig. 6(b): $\theta = -49.76^\circ$, exit $(0.930, 0.000)\,\text{mm}$.
     - H2 ultrafine uniform mesh reference: $\theta = -24.23^\circ$, exit $(1.000, 0.276)\,\text{mm}$.
2. **`audit_fig2_raw_miseseri_field_and_ridge` (.png / .pdf):**
   - Full-domain contour of the raw final-frame MISESERI field ($E_{\text{mises}}$) from Job 1410178 (`miseseri_raw_field.csv`).
   - Shows the extracted localization ridge (terminating horizontally at $y = 0.380\,\text{mm}$) and highlights the 7-order-of-magnitude drop to $10^{-18}$ in the active crack region ($y \in [0.15, 0.35]\,\text{mm}$).
3. **`audit_fig3_et2_true_mesh_and_centerline` (.png / .pdf):**
   - Actual element mesh representation of `JOB_MODE2_ADAPTIVE_ET2.inp` colored by local element sizing $h = \sqrt{A}$.
   - Overlays the extracted refined-zone centerline ($h \le 0.004\,\text{mm}$).
4. **`audit_fig4_comprehensive_trajectory_overlay` (.png / .pdf):**
   - Direct spatial comparison of all 4 trajectories across the entire $1.0\,\text{mm} \times 1.0\,\text{mm}$ shear specimen:
     - Expected Fig. 12(b) corridor ($\pm 0.05\,\text{mm}$).
     - Pre-analysis localized ridge (Job 1410178).
     - ET2 adaptive mesh refined zone centerline.
     - H2 uniform reference trajectory.
5. **`audit_fig5_zoomed_notch_corridor_audit` (.png / .pdf):**
   - Detailed zoom near the initial notch tip $(0.5, 0.5)$ documenting the unrefined active crack corridor ($h \approx 0.020\,\text{mm}$), the horizontal unzipping, and the spurious boundary refinement.

---

## 7. Governing Directive & Next Actions

- **Governing Directive:** Mode-II fracture simulation (`Job-2_UEL.inp`) is **STRICTLY ON HOLD**.
- **No Solver Submissions:** Do **NOT** submit `Job-2_UEL.inp` or any replacement jobs to PBS.
- **Supervisor Presentation:** The spatial trajectory audit evidence, figures, and failure classification will be presented to the supervisor during the Thursday 08 October 2026 meeting (10:00 CEST).
- **Remediation Path (Post-Meeting):**
  1. Implement the Miehe anisotropic strain energy split in the UEL (`f42_mixed_uel.for`) to prevent shear slip and properly drive tensile crack kinking.
  2. Re-run pre-analysis either with pure continuum linear elasticity (as in Mode-I `PK_PREANALYSIS_COARSE.inp`) or with an adequately resolved phase-field mesh to prevent coarse-mesh shear localization.
  3. Re-run native remeshing to generate a physically grounded adaptive mesh that faithfully tracks the $-53.65^\circ$ crack corridor down to the bottom boundary.
