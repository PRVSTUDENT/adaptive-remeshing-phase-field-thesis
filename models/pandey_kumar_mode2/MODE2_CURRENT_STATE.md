# Mode-II Pure Shear Benchmark: Current Scientific & Repository State

**Protocol version:** 2  
**Last updated:** `2026-10-07T09:50:00+02:00`  
**Governing Status:** `MODE2_STAGE15C_CORRECTED_REMESH_QUALIFIED__FRACTURE_SOLVE_NOT_YET_RUN`

---

## 1. Executive Summary & Authoritative Status

1. **Current Scientifically Governed Status:**
   - **Mode-I:** Fully validated, convergence-qualified, dual-reference semantics established, 10-page supervisor report frozen for the 08 October 2026 review.
   - **Mode-II:** Corrected paper-grounded pre-analysis **completed and qualified** (Job `1410178.mmaster02`), native adaptive remeshing sweep **completed and qualified** (selected best candidate: **ET2 with 21,496 finite elements**), production 3-layer UEL input deck (`Job-2_UEL.inp`) built and passed direct Abaqus datacheck with **Exit 0**.
   - **Full Corrected Mode-II Fracture Solve:** **NOT YET RUN**. Execution of the full phase-field fracture analysis is strictly held pending explicit supervisor / human authorization.

2. **Historical / Legacy Disambiguation:**
   - The earlier **7,865-element** Mode-II adaptive simulation (Job `M2_adapt_prod`, 24 September 2026) and its associated documentation (`docs/mode2/archive_pre_stage15c/`) represent an older, superseded preliminary workflow.
   - It is **strictly superseded** and must never be conflated with the canonical Stage-15C corrected result.
   - All historical pre-Stage-15C material has been permanently preserved in the dedicated immutable Git archive branch:
     `archive/legacy-mode2-pre-stage15c-2026-10-07`.

---

## 2. Strict Artifact Classification Matrix

All Mode-II assets in this repository are categorized under four mutually exclusive governance tiers:

| Tier | Directory / Asset Path | Description & Provenance | Governed Status |
| :--- | :--- | :--- | :---: |
| **`CANONICAL_CURRENT`** | `models/pandey_kumar_mode2/06_paper_grounded_uel_preanalysis/Job-1_UEL.inp` | Paper-grounded coarse pre-analysis input deck (2,960 elements; SHA256: `869A2DBD...`) | Active Master Input |
| **`CANONICAL_CURRENT`** | `models/pandey_kumar_mode2/06_paper_grounded_uel_preanalysis/f42_mixed_uel.for` | Dual-element UEL Fortran source (SHA256: `FA48CB4D...`) | Active Master UEL |
| **`CANONICAL_CURRENT`** | Cluster Job `1410178.mmaster02` (`M2_J1_UEL_PRE`) | Solved on `/scratch9/` compute node `mnode097`, completed Step 2 Frame 5021 ($u_x = 0.01500\,\text{mm}$), Exit 0 | Qualified Reference |
| **`CANONICAL_CURRENT`** | `models/pandey_kumar_mode2/04_adaptive_miseseri/JOB_MODE2_ADAPTIVE_ET2.inp` | Corrected native adaptive mesh (21,496 finite elements: 20,934 CPE4 + 562 CPE3; SHA256: `E137BDC3...`; +7.7% vs paper 19,963) | Qualified Adaptive Mesh |
| **`CANONICAL_CURRENT`** | `models/pandey_kumar_mode2/06_paper_grounded_uel_preanalysis/Job-2_UEL.inp` | Production 3-layer UEL fracture model deck built from 21,496-FE ET2 mesh | Datacheck Exit 0; Fracture Solve Pending |
| **`CANONICAL_CURRENT`** | `scripts/remeshing/generate_stage15_mode2_native_remesh.py` | Turnkey native remeshing generator implementing Pandey & Kumar (2025) Section 4.2 | Qualified Generator |
| **`CANONICAL_CURRENT`** | `results/figures/mode2/` | Publication-grade actual mesh topology figures for 21,496-FE ET2 mesh | Canonical Evidence |
| **`DIAGNOSTIC_ONLY`** | `models/pandey_kumar_mode2/00_aux_continuum_preanalysis` | Auxiliary continuum elasticity pre-analysis for baseline comparison | Diagnostic Reference |
| **`DIAGNOSTIC_ONLY`** | `models/pandey_kumar_mode2/05_tri_patch_test` | Abaqus CPE3/triangular element integration and patch verification | Diagnostic Reference |
| **`SUPERSEDED`** | `models/pandey_kumar_mode2/04_adaptive_miseseri/ModeII_adaptive_candidate.inp` | Older 7,865-element preliminary adaptive mesh (Sept 24) | Superseded by ET2 21.5k |
| **`SUPERSEDED`** | `docs/mode2/archive_pre_stage15c/` | Older 7,865-element report, figures, and manifests | Superseded (Archived) |
| **`SUPERSEDED`** | `models/pandey_kumar_mode2/01_baseline_h0`, `02_reference_h1`, `03_ultrafine_h2` | Preliminary uniform meshes from pre-Stage-15C exploration | Superseded (Archived) |
| **`INVALID_FAILED`** | Job `1410125.mmaster02` (`M2_J1_UEL_PRE`) | Stopped administratively for `/home` storage compliance; replaced cleanly by Job 1410178 | Administratively Terminated |

---

## 3. Corrected ET2 Adaptive Mesh Quantitative Characteristics

- **Element Count:** Exactly **21,496 finite elements** (20,934 quadrilateral CPE4 + 562 triangular CPE3).
- **Node Count:** Exactly **21,615 nodes**.
- **Comparison to Published Benchmark:**
  - Pandey & Kumar (2025) Fig. 12(b) reports **19,963 elements**.
  - Corrected Stage-15C ET2 mesh: **21,496 elements** ($\Delta = +7.68\%$, well within the 10% parity acceptance window).
- **Crack Corridor Alignment:**
  - Inclination chord angle: $\theta = -53.65^\circ$ (matching paper Fig. 12(b) $\theta = -53.65^\circ$).
  - Terminal exit position at bottom boundary ($y = 0$): $x = 0.868\,\text{mm}$ (matching paper $x = 0.868\,\text{mm}$).
  - Spurious branches: **Zero** (no unphysical refinement in upper-left domain).
  - Minimum element size: $h_{\min} = 0.00076\,\text{mm}$ ($h_{\min}/l_0 = 0.051 \le 0.10$, resolving $l_0 = 0.015\,\text{mm}$ with $>19$ elements per $l_0$).

---

## 4. Next Authorized Action Boundary

- **Immediate Action:** Export publication-grade mesh topology figures (actual mesh lines, full domain, zoomed corridor, and Fig. 12(b) comparison) into `results/figures/mode2/`.
- **Governing Hold:** Do **not** submit the full fracture simulation (`Job-2_UEL.inp`) until explicit supervisor signoff is obtained at the 08 October 2026 meeting.
