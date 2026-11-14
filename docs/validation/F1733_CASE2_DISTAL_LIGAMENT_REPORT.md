# F1733: Case 2 Distal Ligament Spatial Qualification and Datacheck Provenance Audit Report

**Benchmark:** Case 2 (Single Off-Axis Hole Plate, Pandey & Kumar 2025 Section 4.2 / Original Thesis Model C)  
**Task ID:** `F1733-CASE2-DISTAL-LIGAMENT-QUALIFICATION`  
**Predecessor Task:** `F1732-CASE2-ADAPTIVE-REMESH-CALIBRATION` (`HND-F1732-CASE2-CALIB-001`)  
**Assigned Agent:** `gemini-antigravity`  
**Date:** 14 November 2026  
**Execution Mode:** Strictly Offline Read-Only Audit on Immutable Task F1732 Mesh Artifacts  
**Authoritative Input Mesh:** `results/validation/f1732_case2_calibrated_evidence/PK_F1728_CASE_2_ADAPT_PHYS.inp`  
**Finite PBS Budget:** 0 submissions authorized, 0 consumed (Cumulative PBS jobs permanently preserved = 9)  
**Governing Review Protocol:** `INDEPENDENT_STRUCTURED_REVIEW_V1`

---

## 1. Executive Summary

This investigation directly addresses the review findings (**F1732-R01 to F1732-R07** from `HND-F1732-CASE2-CALIB-001` and **F1733-R01 to F1733-R08** from `HND-F1733-CASE2-DISTAL-001`).

In strict compliance with independent review directives:
1. **Provenance & Hash Reconciliation (Findings F1732-R05, F1733-R04):** We investigated the origin of the conflicting hash values between the initial F1732 dispatch prompt and the final disk artifacts. The solver artifacts generated on compute node `mnode097.cluster` under PBS Job `1423258.mmaster02` have **never changed** on disk:
   - Physical adapted mesh `PK_F1728_CASE_2_ADAPT_PHYS.inp`: SHA-256 `ED8D2905F458CBDB812C975A278A9038B19D613F0160A0AC77993E6A3F41F899` ($574,946$ bytes, $8,783$ physical elements).
   - Production 3-layer deck `PK_F1728_CASE_2_PROD.inp`: SHA-256 `4AD7AC4831B9E756AA4D625A317EA66E77B05225007BDC140CEE0E82E2CEE3F0` ($1,097,090$ bytes, $26,349$ layered elements).
   - Datacheck receipt `PK_F1732_CASE_2_DC.dat`: SHA-256 `0E029D8A9B6F728B0DBB5FCE2AF7AD78B4DA9279ABE98F6A26C55B1635BAB5D2` ($12,666$ bytes).
   The previous hashes (`F39F803D...`, `3788FBCB...`, `EC689C81...`) were draft markdown template placeholders written before files were downloaded via SCP and verified. The authoritative `ARTIFACT_REGISTRY.csv` registered the true hashes from commit `f246748a`.
2. **Classification of Datacheck Warnings (Finding F1733-R05):** We extracted and audited all eight warnings from `PK_F1732_CASE_2_DC.dat`. All eight are identical: `***WARNING: THE *ELEMENT OUTPUT OPTION IS NOT SUPPORTED FOR USER ELEMENTS` (appearing 4 times in Step-1 and 4 times in Step-2, corresponding to element types `U1`, `U3`, `U2`, `U4`). They are 100% benign informational notices confirming that standard Abaqus field output bypasses user elements in favor of Layer 3 companion UMAT elements. There are zero severe warnings, zero MPC/equation defects, and zero element distortion warnings.
3. **Along-Path Trajectory Stations & Area-Weighted Resolution (Findings F1732-R02, R03, R04, F1733-R01):** The $158.11\,\mu\text{m}$ ($21.08\,\ell_0$) oblique crack trajectory from notch tip $(0.50, 0.50)\,\text{mm}$ to hole lower flank $(0.65, 0.55)\,\text{mm}$ was discretized into 10 longitudinal stations with sampling half-width $w_{\perp} = 2.5\,\ell_0 = 18.75\,\mu\text{m}$ (total strip width $37.5\,\mu\text{m} = 5.0\,\ell_0$), comprising 622 unique elements. Area-weighted compliance is only **$52.83\%$** (and $52.09\%$ across Window W2), revealing that coarse distal elements occupy $47.17\%$ of the trajectory area.
4. **Contiguous Longitudinal Extent & Exact Distal Compliance (Findings F1732-R02, F1733-R07):** Stations 7 to 10 ($s \in [0.60, 1.00]$, distal $40.0\%$ of crack path) form a contiguous under-resolved span of **$63.24\,\mu\text{m} = 8.43\,\ell_0$** (mean $h = 5.62\,\mu\text{m}$, range $[3.17, 7.78]\,\mu\text{m}$), failing $h \le \ell_0/2 = 3.75\,\mu\text{m}$. For $h \le \ell_0 = 7.50\,\mu\text{m}$, distal compliance is **$98.51\%$ by count and $95.61\%$ by area** (not 100%), with Station 9 reaching $h_{\max} = 7.62\,\mu\text{m}$ ($91.7\%$ compliance) and Station 10 reaching $h_{\max} = 7.78\,\mu\text{m}$ ($87.5\%$ compliance).
5. **Physical Root Cause (Finding F1732-R06, F1733-R08):** In the coarse donor state (Step-2 Peak, $u_y = 0.00729\,\text{mm}$), damage in the distal ligament is diffuse ($d \in [0.13, 0.24]$, 0 broken elements). The donor stress recovery error indicator $\text{MISESERI}$ is $127.27\,\text{MPa}$ at the hole boundary vs $1,357.85\,\text{MPa}$ at the notch tip ($10.7\times$ contrast). Native Abaqus sizing under $\eta_{\text{target}} = 3.80\%$ correctly sizes these elements to $h \sim 5.0 - 6.3\,\mu\text{m}$. The multi-material SPR section-homogeneity limitation is explicitly retained.
6. **Spatial Qualification Decision (Findings F1732-R07, F1733-R06):** Authoritative production fracture simulation is **REJECTED (FAIL)**. Pre-peak exploratory run viability is retained as an **unverified numerical hypothesis**, and forward fracture simulation remains strictly paused.
7. **Controlled One-Variable Calibration Proposal (Findings F1733-R02, F1733-R03):** To isolate the effect of error-target tightening, all remeshing settings are held strictly fixed to F1732 baselines (`min_size_mm = 0.0015 mm`, `max_size_mm = 0.0200 mm`, `mesh_gradation = 1.25`), changing only `error_target_percent` from $3.80\%$ to **$2.30\%$**. The unconstrained quadratic scaling formula $8,783 \times (3.80 / 2.30)^2 = \mathbf{23,975}$ elements is recorded as an idealized upper bound; all element-count predictions are classified as testable hypotheses. Physical spatial resolution ($h \le \ell_0/2 = 3.75\,\mu\text{m}$ across the corridor) serves as the primary governing objective.

---

## 2. Provenance Reconciliation & Artifact Verification (Findings F1732-R05, F1733-R04, F1733-R05)

### Provenance Investigation of Conflicting Hashes
Review Finding F1733-R04 noted that earlier dispatch prompt `dispatch_f1732_case2_calib_001.ps1` recorded physical mesh hash `F39F803D...` and production deck hash `3788FBCB...`, whereas subsequent reports recorded `ED8D2905...` and `4AD7AC48...`.

We examined Git commit history and disk archives:
1. In Git commit [`f246748a`](https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/commit/f246748a), `project_coordination/ARTIFACT_REGISTRY.csv` lines 6330–6331 registered:
   - `INP_F1732_CASE_2_ADAPT_PHYS`: `ED8D2905F458CBDB812C975A278A9038B19D613F0160A0AC77993E6A3F41F899`
   - `INP_F1732_CASE_2_PROD`: `4AD7AC4831B9E756AA4D625A317EA66E77B05225007BDC140CEE0E82E2CEE3F0`
2. Both physical files `models/pandey_kumar_mode1/223_f1732_case2_calibrated/PK_F1728_CASE_2_ADAPT_PHYS.inp` and `results/validation/f1732_case2_calibrated_evidence/PK_F1728_CASE_2_ADAPT_PHYS.inp` on disk have identical SHA-256 `ED8D2905...`.
3. The hashes `F39F803D...` and `3788FBCB...` (and `EC689C81...` for the `.dat` file) were temporary placeholder hashes written into the report markdown text and PowerShell dispatch script during turn preparation before the actual SCP retrieval of solver outputs from HPC compute node `mnode097.cluster`.
4. The solver artifacts generated by PBS Job `1423258.mmaster02` have remained immutable and unaltered on disk and in Git since their original creation on 14 November 2026 01:47:30 CET.

### Table 1: Authoritative and Reconciled F1732 Artifact Provenance

| Artifact Description | Canonical File Path | Authoritative SHA-256 Digest | File Size | Provenance Status |
| :--- | :--- | :--- | :-: | :---: |
| **Datacheck Output (.dat)** | `results/validation/f1732_case2_calibrated_evidence/PK_F1732_CASE_2_DC.dat` | `0E029D8A9B6F728B0DBB5FCE2AF7AD78B4DA9279ABE98F6A26C55B1635BAB5D2` | 12,666 B | **AUTHENTIC RECEIPT** |
| **Datacheck Messages (.msg)** | `results/validation/f1732_case2_calibrated_evidence/PK_F1732_CASE_2_DC.msg` | `2D9D5D6DA6626940C6278A1CA611E733F9E9C0AECC6D744561F89196EE6E3E37` | 1,423 B | **AUTHENTIC RECEIPT** |
| **Datacheck Parts (.prt)** | `results/validation/f1732_case2_calibrated_evidence/PK_F1732_CASE_2_DC.prt` | `FC12965B8E659FEDB9D3F380EFED3370DA8304D171CF069CDCD83E3FB2AE3FF7` | 5,013 B | **AUTHENTIC RECEIPT** |
| **PBS Execution Log** | `results/validation/f1732_case2_calibrated_evidence/pbs_execution.log` | `046B9830A7799A41AC6507E77104BF56AEFFB5BED96A70C1B293F351634F9D55` | 4,502 B | **AUTHENTIC RECEIPT** |
| **Physical Adapted Mesh** | `results/validation/f1732_case2_calibrated_evidence/PK_F1728_CASE_2_ADAPT_PHYS.inp` | `ED8D2905F458CBDB812C975A278A9038B19D613F0160A0AC77993E6A3F41F899` | 574,946 B | **AUTHENTIC MESH (8,783 el)** |
| **Production 3-Layer Deck**| `results/validation/f1732_case2_calibrated_evidence/PK_F1728_CASE_2_PROD.inp` | `4AD7AC4831B9E756AA4D625A317EA66E77B05225007BDC140CEE0E82E2CEE3F0` | 1,097,090 B | **AUTHENTIC DECK (26,349 el)** |
| **Spatial Audit JSON** | `results/validation/f1732_case2_calibrated_evidence/f1732_case2_ligament_spatial_audit.json`| `621939C18953A0ADCD0565FF0422F5BBD6691F7238CBDA728B43FC1670E8234B` | 12,168 B | **AUTHENTIC AUDIT** |

### Classification of the Eight Datacheck Warnings (Finding F1733-R05)
Inspection of `PK_F1732_CASE_2_DC.dat` lines 202–225 confirms:
```
***WARNING: THE *ELEMENT OUTPUT OPTION IS NOT SUPPORTED FOR USER ELEMENTS (Line 203, Step-1, Type U1)
***WARNING: THE *ELEMENT OUTPUT OPTION IS NOT SUPPORTED FOR USER ELEMENTS (Line 205, Step-1, Type U3)
***WARNING: THE *ELEMENT OUTPUT OPTION IS NOT SUPPORTED FOR USER ELEMENTS (Line 207, Step-1, Type U2)
***WARNING: THE *ELEMENT OUTPUT OPTION IS NOT SUPPORTED FOR USER ELEMENTS (Line 209, Step-1, Type U4)
***WARNING: THE *ELEMENT OUTPUT OPTION IS NOT SUPPORTED FOR USER ELEMENTS (Line 219, Step-2, Type U1)
***WARNING: THE *ELEMENT OUTPUT OPTION IS NOT SUPPORTED FOR USER ELEMENTS (Line 221, Step-2, Type U3)
***WARNING: THE *ELEMENT OUTPUT OPTION IS NOT SUPPORTED FOR USER ELEMENTS (Line 223, Step-2, Type U2)
***WARNING: THE *ELEMENT OUTPUT OPTION IS NOT SUPPORTED FOR USER ELEMENTS (Line 225, Step-2, Type U4)
```
- **Root Cause:** Standard Abaqus `*ELEMENT OUTPUT` requests field output for element set `umatelem`. The preprocessor scans all element types in the model and issues an informational warning for each user element type (`U1`, `U3`, `U2`, `U4`) stating that user elements do not support built-in element output.
- **Classification:** Strictly benign informational notices. Zero warnings exist for boundary conditions, MPC equations, contact, material definitions, or element distortion.

---

## 3. Station-by-Station Along-Path Trajectory Resolution (Findings F1732-R02, R04, F1733-R01)

### Geometric Definition of Trajectory Strip
- **Start Point (Notch Root):** $(x_0, y_0) = (0.5000, 0.5000)\,\text{mm}$
- **End Point (Hole Lower Flank):** $(x_1, y_1) = (0.6500, 0.5500)\,\text{mm}$
- **Direction Vector:** $(\Delta x, \Delta y) = (0.1500, 0.0500)\,\text{mm}$
- **Total Arc Length:** $L_{\text{traj}} = \sqrt{0.15^2 + 0.05^2} = \mathbf{158.11\,\mu\text{m}} = \mathbf{21.08\,\ell_0}$
- **Sampling Half-Width:** $w_{\perp} = 2.5\,\ell_0 = 18.75\,\mu\text{m}$ (total strip width $2 w_{\perp} = 37.50\,\mu\text{m} = \mathbf{5.0\,\ell_0}$)
- **Element Selection Rule:** Projection coordinate $\text{proj} \in [s_{\min}, s_{\max})$ and perpendicular distance $\text{dist}_{\perp} \le w_{\perp}$. Centroids uniquely partition into stations $1$ to $10$. Total elements in strip $= \mathbf{622}$.

### Table 2: Ten Longitudinal Trajectory Stations ($s \in [0, 1]$)

| Stn | $s$-Range | Arc Span ($\mu\text{m}$) | Centroid $(x, y)$ | Elems | Area ($\text{mm}^2$) | Mean $h$ ($\mu\text{m}$) | Min $h$ ($\mu\text{m}$) | Max $h$ ($\mu\text{m}$) | Count $\le \ell_0/2$ | Area $\le \ell_0/2$ | Count $\le \ell_0$ | Physical Status |
| :-: | :---: | :---: | :---: | :-: | :---: | :-: | :-: | :-: | :---: | :---: | :---: | :--- |
| **1** | $[0.0, 0.1]$ | $0.0 - 15.8$ | $(0.5075, 0.5025)$ | 162 | $5.92 \times 10^{-4}$ | **1.90** | 0.94 | 2.74 | **100.0%** | **100.0%** | 100.0% | Fully Resolved Process Zone |
| **2** | $[0.1, 0.2]$ | $15.8 - 31.6$ | $(0.5225, 0.5075)$ | 128 | $5.90 \times 10^{-4}$ | **2.11** | 1.01 | 3.09 | **100.0%** | **100.0%** | 100.0% | Fully Resolved Process Zone |
| **3** | $[0.2, 0.3]$ | $31.6 - 47.4$ | $(0.5375, 0.5125)$ | 106 | $5.93 \times 10^{-4}$ | **2.34** | 1.27 | 3.69 | **100.0%** | **100.0%** | 100.0% | Fully Resolved Process Zone |
| **4** | $[0.3, 0.4]$ | $47.4 - 63.2$ | $(0.5525, 0.5175)$ | 66 | $5.91 \times 10^{-4}$ | **2.96** | 1.76 | 4.25 | **92.4%** | **86.2%** | 100.0% | Fully Resolved Process Zone |
| **5** | $[0.4, 0.5]$ | $63.2 - 79.1$ | $(0.5675, 0.5225)$ | 51 | $5.90 \times 10^{-4}$ | **3.32** | 2.15 | 4.62 | **78.4%** | **68.5%** | 100.0% | Transition Zone |
| **6** | $[0.5, 0.6]$ | $79.1 - 94.9$ | $(0.5825, 0.5275)$ | 42 | $5.94 \times 10^{-4}$ | **3.81** | 2.12 | 4.96 | **45.2%** | **36.0%** | 100.0% | Transition Zone |
| **7** | $[0.6, 0.7]$ | $94.9 - 110.7$ | $(0.5975, 0.5325)$ | 25 | $5.92 \times 10^{-4}$ | **4.80** | 4.00 | 5.67 | **0.0%** | **0.0%** | 100.0% | **Deficient Resolution** |
| **8** | $[0.7, 0.8]$ | $110.7 - 126.5$ | $(0.6125, 0.5375)$ | 22 | $5.88 \times 10^{-4}$ | **5.22** | 3.17 | 6.00 | **4.5%** | **1.7%** | 100.0% | **Deficient Resolution** |
| **9** | $[0.8, 0.9]$ | $126.5 - 142.3$ | $(0.6275, 0.5425)$ | 12 | $4.87 \times 10^{-4}$ | **6.14** | 5.26 | 7.62 | **0.0%** | **0.0%** | **91.7%** | **Deficient Resolution** |
| **10**| $[0.9, 1.0]$ | $142.3 - 158.1$ | $(0.6425, 0.5475)$ | 8 | $3.25 \times 10^{-4}$ | **6.31** | 5.72 | 7.78 | **0.0%** | **0.0%** | **87.5%** | **Deficient Resolution** |

---

## 4. Area-Weighted Coverage vs Element-Count Compliance (Finding F1732-R03)

Because element area scales quadratically ($A \propto h^2$), coarse elements represent disproportionately larger physical areas than fine elements.

### Table 3: Area-Weighted vs Count-Based Resolution Comparison

| Geometric Sampling Domain | Elements | Total Area ($\text{mm}^2$) | Element-Count Compliance ($h \le 3.75\,\mu\text{m}$) | Area-Weighted Compliance ($h \le 3.75\,\mu\text{m}$) | Element-Count Compliance ($h \le 7.50\,\mu\text{m}$) | Area-Weighted Compliance ($h \le 7.50\,\mu\text{m}$) |
| :--- | :-: | :-: | :-: | :-: | :-: | :-: |
| **Window W2 (Full Primary Corridor)** | 1,595 | 0.019500 | **81.94%** | **52.09%** | 99.87% | 99.41% |
| **Narrow Trajectory Strip ($w_{\perp} = 2.5\,\ell_0$)** | 622 | 0.005542 | **83.12%** | **52.83%** | 99.52% | 98.42% |
| **Stations 1–3 (Notch Process Zone)** | 396 | 0.001775 | **100.0%** | **100.0%** | 100.0% | 100.0% |
| **Stations 4–6 (Mid-Ligament Transition)** | 159 | 0.001775 | **75.47%** | **63.55%** | 100.0% | 100.0% |
| **Stations 7–10 (Distal Ligament to Hole)** | 67 | 0.001992 | **1.49%** | **0.49%** | **98.51%** | **95.61%** |

Across the $158.11\,\mu\text{m}$ trajectory, while $83.12\%$ of elements have $h \le 3.75\,\mu\text{m}$, they cover only **$52.83\%$ of the physical strip area**. The remaining $47.17\%$ of the area is occupied by coarse distal elements ($h \sim 4.8 - 6.3\,\mu\text{m}$).

---

## 5. Contiguous Longitudinal Under-Resolved Extent & Distal Compliance (Findings F1732-R02, F1733-R07)

- **Contiguous Under-Resolved Region:** Stations 7 through 10
- **Parametric Arc Range:** $s \in [0.60, 1.00]$ ($40.0\%$ of the crack path)
- **Physical Arc Length:** $94.87\,\mu\text{m}$ to $158.11\,\mu\text{m}$
- **Contiguous Longitudinal Extent:** **$63.24\,\mu\text{m} = \mathbf{8.43\,\ell_0}$**
- **Element Size in Extent:** $h \in [3.17, 7.78]\,\mu\text{m}$ (Mean $h = \mathbf{5.62\,\mu\text{m}} = \mathbf{0.75\,\ell_0}$)
- **Maximum Local Unresolved Element Size:** $h_{\max} = \mathbf{7.78\,\mu\text{m}} > \ell_0 = 7.50\,\mu\text{m}$ (in Station 10)
- **Clarification on $h \le \ell_0$ Coverage (Finding F1733-R07):** Coverage is **not** 100%. Station 9 reaches $h_{\max} = 7.62\,\mu\text{m}$ ($91.7\%$ compliance) and Station 10 reaches $h_{\max} = 7.78\,\mu\text{m}$ ($87.5\%$ compliance). Across the distal span (Stations 7–10), $h \le \ell_0$ compliance is **$98.51\%$ by count and $95.61\%$ by area**.

---

## 6. Physical Root Cause: Precritical Donor Damage vs Error Starvation (Findings F1732-R06, F1733-R08)

- **Donor Model:** `PK_HOLE_COARSE_JOB1.odb` (Step-2, Frame 167, $u_y = 0.00729\,\text{mm}$, peak force $F_{\max} = 0.7310\,\text{kN}$).
- **Damage Distribution:** 48 actively softening elements ($d \ge 0.10$), zero broken elements ($d \ge 0.90$).
- **Recovered Error Indicator ($\text{MISESERI}$):**
  * Notch root peak: **$1,357.85\,\text{MPa}$** (crack-tip stress singularity).
  * Distal ligament (Stations 7–10): **$127.27\,\text{MPa}$** (diffuse softening, $10.67\times$ lower contrast).
- **Native Sizing Mechanism:** $h_{\text{new}} \approx h_{\text{old}} \cdot (\eta_{\text{target}} / \eta_e)^{1/p}$. Under $\eta_{\text{target}} = 3.80\%$, distal elements naturally size to $h \sim 5.0 - 6.3\,\mu\text{m}$.
- **Retained Limitation (Finding F1733-R08):** The provisional recovery donor retains the multi-material SPR section-homogeneity limitation, which remains explicit in all subsequent claims.

---

## 7. Spatial Qualification Decision (Findings F1732-R07, F1733-R06)

### Production Phase-Field Fracture Simulation: FAIL (REJECTED)
- **Rationale:** The contiguous $8.43\,\ell_0$ under-resolved distal span ($h \in [3.17, 7.78]\,\mu\text{m}$) fails $h \le \ell_0/2 = 3.75\,\mu\text{m}$. Propagating a phase-field crack through this region risks artificial mesh pinning and spurious toughness elevation. Authoritative production designation is rejected.

### Bounded Exploratory Pre-Peak Loading Pilot: UNVERIFIED HYPOTHESIS (PAUSED)
- **Finding F1733-R06 Compliance:** Pre-peak exploratory run viability is explicitly classified as an **unverified numerical hypothesis**, not a demonstrated safety guarantee. Forward fracture simulation remains **strictly paused**.

---

## 8. Controlled One-Variable Calibration Proposal for Successor Task F1734 (Findings F1733-R02, F1733-R03)

In strict compliance with the controlled one-variable calibration rule:
1. **Settings Held Constant (Identical to F1732):**
   - `min_size_mm`: **$0.0015\,\text{mm}$** ($1.5\,\mu\text{m} = \ell_0/5$)
   - `max_size_mm`: **$0.0200\,\text{mm}$** ($20.0\,\mu\text{m}$)
   - `mesh_gradation`: **$1.25$**
   - `step_name`: `RECOVERY_STEP`
   - `region_name`: `ALL_ELEM`
   - Geometry, donor ODB (`PK_HOLE_COMPANION_RECOVERY.odb`), and boundary conditions remain bitwise identical.
2. **Single Parameter Varied:**
   - `error_target_percent`: Tightened from $3.80\%$ to **$2.30\%$**.
   - Derived from linear scaling: $\eta_{\text{target, new}} = 3.80\% \times (3.50\,\mu\text{m} / 5.80\,\mu\text{m}) = \mathbf{2.29\%} \approx \mathbf{2.30\%}$.
3. **Element-Count Scaling Arithmetic & Classification (Finding F1733-R02):**
   - Idealized isotropic unconstrained scaling:
     $$N_{\text{predicted}} = 8,783 \times \left( \frac{3.80}{2.30} \right)^2 = 8,783 \times 2.7297 = \mathbf{23,975} \text{ elements}$$
   - Because `max_size` caps bulk element growth and gradation restricts rapid transitions, the actual element count will be constrained.
   - **Classification:** All element-count estimates are unverified hypotheses. Physical spatial resolution ($h \le \ell_0/2$ across the corridor) is the primary calibration objective.

---

## 9. Verification & Regression Evidence

1. **Static Analysis Script:** [scripts/remeshing/investigate_case2_distal_ligament.py](file:///D:/Master%20thesis/Adaptive%20remeshing/scripts/remeshing/investigate_case2_distal_ligament.py)
2. **Machine-Readable Results:** [results/validation/f1733_case2_distal_ligament_investigation.json](file:///D:/Master%20thesis/Adaptive%20remeshing/results/validation/f1733_case2_distal_ligament_investigation.json) (SHA-256: `612244794D2B0217433090610302F73642BED8D0476979E368E4D66BE1B6D191`)
3. **Automated Unit Test Suite:** [tests/unit/test_f1733_case2_distal_ligament.py](file:///D:/Master%20thesis/Adaptive%20remeshing/tests/unit/test_f1733_case2_distal_ligament.py)
4. **Pytest Regression Receipt:** [results/validation/f1733_pytest_receipt.txt](file:///D:/Master%20thesis/Adaptive%20remeshing/results/validation/f1733_pytest_receipt.txt) (63/63 tests pass across full Case 2 suite F1728 to F1733 in $3.08\,\text{s}$, SHA-256: `7FA8E1DC866011A622336BCF79EA00800729D8A100A91A5DFC24C103D5A8E5B9`)
5. **Frozen Subroutine Preservation:** Subroutine `f42_mixed_uel.for` remains bitwise unaltered (`CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6`).
6. **Cumulative PBS Accounting:** Permanently preserved at 9 jobs (`1423095`, `1423101`, `1423102`, `1423103`, `1423169`, `1423234`, `1423235`, `1423257`, `1423258`). Exactly 0 PBS jobs consumed for Task F1733.
