# Mode-II Pure Shear Benchmark: Current Scientific & Repository State

**Protocol version:** 2  
**Last updated:** `2026-10-07T11:25:00+02:00`  
**Governing Status:** `MODE2_STAGE15C_CORRECTED_REMESH_QUALIFIED__FRACTURE_SOLVE_NOT_YET_RUN`

---

## 1. Executive Summary & Authoritative Status

1. **Current Scientifically Governed Status:**
   - **Mode-I:** Fully validated, convergence-qualified, dual-reference semantics established, 10-page supervisor report frozen for the 08 October 2026 review.
   - **Mode-II:** Corrected paper-grounded pre-analysis **completed and qualified** (Job `1410178.mmaster02`, Exit 0, 2,960 finite elements, $h_{\text{global}} = 0.020\,\text{mm}$), native adaptive remeshing sweep **completed and qualified** (selected best candidate: **ET2 with 21,496 finite elements**, 21,615 native nodes), production 3-layer UEL input deck (`Job-2_UEL.inp`, 64,488 layered elements, 21,616 nodes including RP 999999) fully constructed.
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
| **`CANONICAL_CURRENT`** | `models/pandey_kumar_mode2/06_paper_grounded_uel_preanalysis/Job-1_UEL.inp` | Paper-grounded coarse pre-analysis input deck (2,960 FE, 3,036 FE nodes, 8,880 layered elements, $h_{\text{global}} = 0.020\,\text{mm}$; SHA256: `869A2DBD...`) | Active Master Input |
| **`CANONICAL_CURRENT`** | `models/pandey_kumar_mode2/06_paper_grounded_uel_preanalysis/f42_mixed_uel.for` | Dual-element UEL Fortran source (SHA256: `FA48CB4D...`) | Active Master UEL |
| **`CANONICAL_CURRENT`** | Cluster Job `1410178.mmaster02` (`M2_J1_UEL_PRE`) | Solved on `/scratch9/` compute node `mnode097`, completed Step 2 Frame 5021 ($u_x = 0.01500\,\text{mm}$), Exit 0 | Qualified Reference |
| **`CANONICAL_CURRENT`** | `models/pandey_kumar_mode2/04_adaptive_miseseri/JOB_MODE2_ADAPTIVE_ET2.inp` | Corrected native adaptive mesh (21,496 finite elements: 20,934 CPE4 + 562 CPE3; 21,615 native nodes; SHA256: `E137BDC3...`; +7.7% vs paper 19,963) | Qualified Adaptive Mesh |
| **`CANONICAL_CURRENT`** | `models/pandey_kumar_mode2/06_paper_grounded_uel_preanalysis/Job-2_UEL.inp` | Production 3-layer UEL fracture model deck (64,488 layered elements, 21,616 nodes including RP 999999; SHA256: `6B07E499...`) built from 21,496-FE ET2 mesh | Datacheck Qualified; Fracture Solve Pending |
| **`CANONICAL_CURRENT`** | `scripts/remeshing/generate_stage15_mode2_native_remesh.py` | Turnkey native remeshing generator implementing Pandey & Kumar (2025) Section 4.2 | Qualified Generator |
| **`CANONICAL_CURRENT`** | `results/figures/mode2/` | Publication-grade actual mesh topology figures for 21,496-FE ET2 mesh | Canonical Evidence |
| **`DIAGNOSTIC_ONLY`** | `models/pandey_kumar_mode2/00_aux_continuum_preanalysis` | Auxiliary continuum elasticity pre-analysis for baseline comparison | Diagnostic Reference |
| **`DIAGNOSTIC_ONLY`** | `models/pandey_kumar_mode2/05_tri_patch_test` | Abaqus CPE3/triangular element integration and patch verification | Diagnostic Reference |
| **`SUPERSEDED`** | `models/pandey_kumar_mode2/04_adaptive_miseseri/ModeII_adaptive_candidate.inp` | Older 7,865-element preliminary adaptive mesh (Sept 24) | Superseded by ET2 21.5k |
| **`SUPERSEDED`** | `docs/mode2/archive_pre_stage15c/` | Older 7,865-element report, figures, and manifests | Superseded (Archived) |
| **`SUPERSEDED`** | `models/pandey_kumar_mode2/01_baseline_h0`, `02_reference_h1`, `03_ultrafine_h2` | Preliminary uniform meshes from pre-Stage-15C exploration | Superseded (Archived) |
| **`INVALID_FAILED`** | Job `1410125.mmaster02` (`M2_J1_UEL_PRE`) | Stopped administratively for `/home` storage compliance; replaced cleanly by Job 1410178 | Administratively Terminated |

---

## 3. Reconciled Canonical Mesh Discretization & Topology Metrics

To ensure strict provenance integrity, raw native mesh statistics and reconstructed 3-layer UEL deck statistics are explicitly distinguished below:

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

### Detailed Disambiguation Notes:
1. **Coarse Pre-Analysis Element Count (2,960 FE):**
   - The authoritative coarse pre-analysis mesh has exactly **2,960 finite elements** (2,860 CPE4 quadrilaterals + 100 CPE3 triangles) and **3,036 FE nodes** (3,037 in deck including RP 999999).
   - Any prior casual mention of non-canonical element counts is explicitly debunked and purged.
2. **Coarse Global Mesh Size (0.020 mm):**
   - The global background seeding size is strictly **0.020 mm** ($0.02\,\text{mm}$), as governed by `PACKAGE_MANIFEST.json` and `execute_mode2_native_remesh_suite.py` (`p.seedPart(size=0.02)`).
   - Any prior casual mention of non-canonical global sizing is explicitly debunked and purged.
3. **Node Count Semantics (21,615 vs. 21,616):**
   - Raw native adaptive mesh `JOB_MODE2_ADAPTIVE_ET2.inp`: exactly **21,615 FE nodes**. The zero-gap crack seam ($y = 0.5\,\text{mm}, x \le 0.5\,\text{mm}$) is already embedded directly in the native mesh with 93 duplicate node pairs (186 flank nodes) plus 1 shared crack-tip node at $(0.5, 0.5)$, totalling 187 seam nodes.
   - Production UEL deck `Job-2_UEL.inp`: exactly **21,616 nodes**, consisting of all 21,615 native FE nodes plus **1 Reference Point node (RP 999999)** at $(0.5, 1.0)$ required for kinematic `*EQUATION` rigid top shear coupling.
   - There is no node duplication discrepancy; the $+1$ node difference is solely the analytical Reference Point RP 999999.
4. **Element Count Semantics (21,496 vs. 64,488):**
   - Raw native adaptive mesh `JOB_MODE2_ADAPTIVE_ET2.inp`: exactly **21,496 finite elements** (20,934 CPE4 + 562 CPE3).
   - Production UEL deck `Job-2_UEL.inp`: exactly **64,488 total elements** across 3 co-located layers ($3 \times 21,496$: Layer 1 Phase UEL IDs 1..21,496, Layer 2 Mechanical UEL IDs 21,497..42,992, Layer 3 Companion UMAT CPE4/CPE3 IDs 42,993..64,488).

---

## 4. Next Authorized Action Boundary

- **Immediate Action:** Keep Mode-II strictly on hold pending formal supervisor review and signoff on Mode-I at the Thursday 08 October 2026 meeting (10:00 CEST).
- **Governing Hold:** Do **not** submit the full fracture simulation (`Job-2_UEL.inp`) and do **not** launch any Mode-II HPC jobs.
