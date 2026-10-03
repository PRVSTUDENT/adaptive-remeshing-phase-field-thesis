# Pre-Job Architecture-Isolation Card

**Package:** `90_mode1_preanalysis_continuum_matched_2906`  
**Input Deck:** `PK_M1_JOB1_CONTINUUM_MATCHED_2906.inp` (SHA-256: `b60dd35d56ab2824902f2d90912e222cf9d335d7d9911cf8dd17a3dc2b52e5f9`)  
**Target Benchmark:** Mode-I Pre-Analysis (Pandey & Kumar, 2025, *CMES* 144(3), 3251–3276)  
**Execution Mode:** 1-CPU Serial, 16 GB, 2h walltime in PBS queue `normal_imfdfkmq`  
**Date:** 2026-10-03  
**Governing Meeting:** Thursday, 08 October 2026, 10:00 CEST  

---

## 1. Governance & Boundary Exclusions

1. **NOT an Attempt to Force 13,941 Elements:**  
   Per the supervisor's binding decision of 17 September 2026, the reproduction of exactly 13,941 elements is closed as a publication limitation (`SUPERVISOR_ACCEPTED_REPRODUCTION_LIMITATION_CLOSED`). This simulation does NOT tune `errorTarget`, does not alter mesh sizing parameters, and does NOT execute `adaptiveRemesh`.

2. **NOT a Resolution of Publication Loading Schedule Ambiguity:**  
   The publication text prescribing $\Delta u_1 = 10^{-3}$ for 500 increments is physically contradictory ($\Delta u_1 \times 500 = 0.5\,\text{mm}$ vs $u_{\text{peak}} = 0.005857\,\text{mm}$) and remains formally classified as **`UNRESOLVED_REFERENCE_DETAIL`**. This run does not attempt to prove what the authors ran, but mirrors the exact two-step loading schedule executing in active PBS Job `1409912.mmaster02`.

---

## 2. Sole Scientific Question

> **"Does the layered Job-1 architecture itself alter MISESERI localization?"**

- **Primary Hypothesis:**  
  If the companion UMAT Hookean stress transfer into `All_elem` in the 3-layer architecture (`PK_M1_JOB1_UEL_2906.inp`, Job `1409912.mmaster02`) is mechanically neutral ($r = 1.000000000$), then the resulting raw centroid `MISESERI` error distribution on `All_elem` should match the raw centroid `MISESERI` error distribution from this standard continuum model across identical steps, frames, and displacement states.
- **Alternative Hypothesis:**  
  If multi-point constraint coupling, user element displacement interpolation, or UMAT/facsimile extraction introduces numerical dispersion or distortion, a systematic divergence in `MISESERI` field values or localization metrics will be observed.

---

## 3. Single Controlled Factor of Variation

| Attribute | Layered Candidate (`1409912.mmaster02`, Package 89) | Matched Continuum Control (Package 90) |
| :--- | :--- | :--- |
| **Specimen Geometry** | $1.0 \times 1.0\,\text{mm}$ square plate | $1.0 \times 1.0\,\text{mm}$ square plate (Identical) |
| **Crack Representation**| Zero-gap sharp seam ($a_0 = 0.5\,\text{mm}$) | Zero-gap sharp seam ($a_0 = 0.5\,\text{mm}$) (Identical) |
| **Mesh Topology** | Canonical project 2,906 elements (2,818 quads, 88 tris) | Canonical project 2,906 elements (2,818 quads, 88 tris) (Identical) |
| **Node Coordinates** | 2,988 nodes + 1 RP (Node 999999) | 2,988 nodes + 1 RP (Node 999999) (Identical) |
| **Boundary Conditions** | Lateral-free Mode-I roller ($u_x$ free at top) | Lateral-free Mode-I roller ($u_x$ free at top) (Identical) |
| **Material Properties** | $E = 210.0\,\text{GPa}$, $\nu = 0.3$ | $E = 210.0\,\text{GPa}$, $\nu = 0.3$ (Identical) |
| **Loading History** | Step-1: $u=0.005\,\text{mm}$ (500 incs)<br>Step-2: $u=0.010\,\text{mm}$ (1000 incs) | Step-1: $u=0.005\,\text{mm}$ (500 incs)<br>Step-2: $u=0.010\,\text{mm}$ (1000 incs) (Identical) |
| **Output Schedule** | Field frequency = 1, `MISESERI, MISESAVG, S, E, EVOL` | Field frequency = 1, `MISESERI, MISESAVG, S, E, EVOL` (Identical) |
| **Discretization Architecture**| **3 Layers:** U1/U3 (phase) + U2/U4 (mech UEL) + Layer 3 UMAT (`umatelem` / `All_elem`) | **1 Layer:** Standard continuum `CPE4` / `CPE3` (`All_elem`) with built-in elasticity |

**Sole intended change:** Discretization architecture (3-layer UEL/UMAT/facsimile vs standard single-layer continuum). Everything else is frozen.

---

## 4. Pre-Declared Acceptance & Evaluation Criteria

1. **Exact Step/Frame Matched Comparison:**  
   Compare at identical physical displacement states ($u = 0.0050\,\text{mm}$ at Step-1 completion, $u = 0.0100\,\text{mm}$ at Step-2 completion) without any displacement rescaling shortcut.
2. **Evaluation Metrics:**
   - One `WHOLE_ELEMENT` `MISESERI` value per underlying finite element (2,906 values).
   - Raw spatial error maps and element-by-element differences ($\Delta e_i = e_{i,\text{layered}} - e_{i,\text{continuum}}$).
   - Pearson correlation coefficient $r$ and mean/max absolute differences.
   - Partitioned regional shares: crack-tip corridor, wake, right ligament, far-field, and boundary sets.
   - Normalized footprint fractions: $e/e_{\max} \ge 50\%, 10\%, 1\%$.
   - High-error bounding boxes.
3. **Directional Evidence Classification:**
   - `TOWARD_TARGET_LOCALIZATION`: Layered architecture concentrates error more closely to the crack tip than continuum.
   - `NO_MEANINGFUL_IMPROVEMENT`: Layered architecture produces an error field essentially identical to continuum ($r \approx 1.0$, identical spatial footprint).
   - `AWAY_FROM_TARGET_LOCALIZATION`: Layered architecture broadens or disperses error further into the far field.
