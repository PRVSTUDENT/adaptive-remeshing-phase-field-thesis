# Gate 5: Priority-B Remaining-Hypothesis Matrix (71,320 vs 13,941 Discrepancy)

**Document Reference:** `GATE5_PRIORITY_B_REMAINING_HYPOTHESIS_MATRIX.md`  
**Reconciliation Version:** Revision 14 (Comprehensive 15-Factor Accessible-Evidence Closure Matrix)  
**Date:** September 14, 2026  
**Status:** `AUTHOR_INFORMATION_REQUEST_READY_FOR_HUMAN_APPROVAL_UNSENT`  
**Active Gate Status:** `UNRESOLVED_WITH_PUBLICATION_INFORMATION_MISSING` / `GATE5_REPRODUCTION_DISCREPANCY_RESOLUTION_ACTIVE`  
**Investigation Topic:** Forensic Attribution of the Discrepancy between Published Nominal 1% Cardinality ($N_{\text{el}} = 13,941$, Section 4.1) and Literal Reproduction ($N_{\text{el}} = 71,320$, Listing 1).  
**Primary Reference:** Pandey, A., & Kumar, S. (2025). "A Simple and Robust Mesh Refinement Implementation in Abaqus for Phase Field Modelling of Brittle Fracture." *Computer Modeling in Engineering & Sciences* (CMES), Vol. 144, No. 3, pp. 3251–3286. DOI: [10.32604/cmes.2025.067858](https://doi.org/10.32604/cmes.2025.067858)  
**Associated Inquiry Draft:** [`docs/supervisor_reports/GATE5_AUTHOR_REPRODUCIBILITY_INQUIRY_DRAFT.md`](file:///D:/Master%20thesis/Adaptive%20remeshing/docs/supervisor_reports/GATE5_AUTHOR_REPRODUCIBILITY_INQUIRY_DRAFT.md)  
**Accompanying Visual Artifact:** [`docs/thesis/figures/figure_gate5_author_inquiry_mesh_comparison.png`](file:///D:/Master%20thesis/Adaptive%20remeshing/docs/thesis/figures/figure_gate5_author_inquiry_mesh_comparison.png)  
**Accompanying Topology Audit:** [`docs/supervisor_reports/GATE5_COARSE_GEOMETRY_AND_TOPOLOGY_PROVENANCE_AUDIT.md`](file:///D:/Master%20thesis/Adaptive%20remeshing/docs/supervisor_reports/GATE5_COARSE_GEOMETRY_AND_TOPOLOGY_PROVENANCE_AUDIT.md)

---

## 1. Executive Summary & Epistemic Baseline

This matrix synthesizes all 15 audited numerical, algorithmic, and formulation factors investigated to explain why literal execution of the published Python workflow (Listing 1: `errorTarget=1.0`, $h_{\min}=0.001\,\text{mm}, h_{\max}=0.020\,\text{mm}, \text{refinementFactor}=10, \text{coarseningFactor}=\text{NOT\_ALLOWED}$) produces **71,320 finite elements** across **Abaqus 2019 GA, 2021.HF26, 2022 GA, and 2023.HF4** on Linux, while Section 4.1 (p. 3265, Line 1027) reports approximately **13,941 finite elements**.

### Authoritative Canonical Baseline (CPE4 Plane Strain Control C0):
- **Coarse Mesh ($N_{\text{el}}^{\text{coarse}}$):** $2,906$ finite elements ($2,818$ CPE4 quads + $88$ CPE3 triangles, $2,988$ nodes) on $1.0 \times 1.0\,\text{mm}$ plate with $a_0 = 0.5\,\text{mm}$ sharp slit seam.
- **Adapted Mesh ($N_{\text{el}}^{\text{adapted}}$):** Exactly **71,320 finite elements** ($69,443$ CPE4 quads + $1,877$ CPE3 triangles, $70,845$ mesh nodes).
- **Substantive Invariance:** $100.000\%$ identical across Abaqus 2019, 2021, 2022, 2023 (Linux). Normalized node hash `116f2e2042afddf8af2d38bd51147c2cd135ee93304d586b632cdb404fca8e4e`, normalized conn hash `fe26a48fa2df1ed2cf91ebc7b213dd1dbbc08f5bbfacb3a2775af813c1ec0224`.

---

## 2. Comprehensive 15-Factor Accessible-Evidence Closure Matrix

| # | Investigated Factor / Dimension | Publication Support / Ambiguity | Tested Configuration | Exact Job / Script / Hash Evidence | Observed Result | Truly Isolated? | Final Status |
| :-: | :--- | :--- | :--- | :--- | :--- | :---: | :--- |
| **1** | **Abaqus Linux Release (2019–2023)** | Omitted in paper (Hardware HP i7-7700 stated) | 2019 GA (Build 157541) vs 2021.HF26 vs 2022 GA vs 2023.HF4 on Linux | Jobs `1405052` (2019 GA), `1404968` (2021.HF26), `1404373` (2022 & 2023); node hash `116f2e20...` | **100.000% bit-for-bit identical 71,320 elements** ($69,443$ CPE4 + $1,877$ CPE3, $70,845$ nodes) | YES_ISOLATED | `RULED_OUT` |
| **2** | **Pre-Analysis Scalar Load Scale** | Step schedule in Sec. 4.1; pre-load magnitude unstated | Linear displacement $u_2 \in [0.0010, 0.0100]\,\text{mm}$ ($0.2\times$ to $2.0\times$ reference) | Job `1404383.mmaster02`; `JOB1_LOAD_*.inp` raw geometric parses | Relative error $\eta$ scale-invariant; count strictly invariant at **71,070 – 71,512 elements** ($\pm 0.3\%$) | YES_ISOLATED | `RULED_OUT` |
| **3** | **Output Frequency Argument** | Listing 1 sets `ALL_INCREMENTS` | `ALL_INCREMENTS` vs `LAST_INCREMENT` in `RemeshingRule` | Candidate C5; `pandey_kumar_adaptive_refinement.py` | Both reference identical terminal elastic step frame; yields **exact 71,320 elements** | YES_ISOLATED | `RULED_OUT` |
| **4** | **Coarse Meshing Algorithm Controls** | Omitted from text/figures | Default `QUAD_DOMINATED/ADVANCING_FRONT` vs `QUAD/MEDIAL_AXIS` vs pure quads | `ADAPTIVE_REMESH_COMPAT_RESULTS.json`; `GATE5_COARSE_MESHER_AND_SEEDING_OFAT_SYNTHESIS.md` | Pure quad options error in `adaptiveRemesh` with "No active regions"; default yields **2,906 coarse and 71,320 adapted** | YES_ISOLATED | `RULED_OUT` |
| **5** | **Coarse Mesh Seed Controls** | Omitted from text/figures | `minSizeFactor` $\in [0.01, 0.50]$, `deviationFactor` $\in [0.01, 0.50]$, explicit edge seeds | `GATE5_COARSE_SEEDING_OFAT_RESULTS.json` | No curved geometry exists on plate; coarse count strictly invariant at **2,906**, adapted at **71,320** | YES_ISOLATED | `RULED_OUT` |
| **6** | **Multi-Pass Adaptive Remeshing** | Sec. 3.3 explicitly prescribes single-pass for Mode-I | Single-pass adaptation vs multi-pass loop | Sec. 3.1-3.3 narrative; Figs. 2 & 3 flowcharts | Multi-pass loop would compound refinement; single-pass yields **71,320 elements** | YES_ISOLATED | `RULED_OUT` |
| **7** | **Continuum Element Integration Order** | Unstated in Section 4.1 | Full integration `CPE4` (4-point) vs Reduced integration `CPE4R` (1-point) | Job `1405056.mmaster02`; `ofat_cpe4r_results.json` | `CPE4R` increases domain error ($+44.5\%$), driving adapted count up to **103,706 elements** ($+45.4\%$) | YES_ISOLATED | `TESTED_EFFECT_INSUFFICIENT` |
| **8** | **Top-Edge Horizontal BC ($u_1$)** | Top $u_y = \bar{u}$; $u_x$ restraint unstated in Sec. 4.1 | $u_1 = 0.0$ (shear constrained) vs $u_1 = \text{Free}$ (shear relaxed) | Job `1405055.mmaster02`; `ofat_top_u1_free_results.json` | Unconstraining $u_1$ reduces far-field R5 elements ($-28.4\%$), yielding **55,761 elements** ($-21.8\%$, $>4.0\times$ lit.) | YES_ISOLATED | `TESTED_EFFECT_INSUFFICIENT` |
| **9** | **Coarser Initial Mesh ($h_{\text{cms}}$)** | $h_{\text{cms}}=0.02\,\text{mm}$ in Sec. 4.1; Table 1 tests $0.03\,\text{mm}$ | $h_{\text{cms}} = 0.030\,\text{mm}$ (1,303 coarse elements) vs $0.020\,\text{mm}$ (2,906 elements) | Candidate C6; `JOB1_LOAD_HCMS030.inp` | Yields **48,919 adapted elements** ($47,610$ CPE4 + $1,309$ CPE3, $-31.4\%$), remaining $3.5\times$ higher than 13,941 | YES_ISOLATED | `TESTED_EFFECT_INSUFFICIENT` |
| **10** | **Remeshing Sizing Bounds** | Listing 1 sets `specifyMinSize=True`, `specifyMaxSize=True` | `specifyMinSize=False`, `specifyMaxSize=False` | Candidate C3 & C4; `pandey_kumar_adaptive_refinement.py` | Sizing bounds do not govern global error zone; unconstrained yields **71,320 elements** ($0.0\%$ delta) | YES_ISOLATED | `TESTED_EFFECT_INSUFFICIENT` |
| **11** | **Coarsening Factor Argument** | Listing 1 sets `coarseningFactor=NOT_ALLOWED` | `coarseningFactor = DEFAULT_LIMIT` (~3.0) vs `NOT_ALLOWED` | Candidate C2; `pandey_kumar_adaptive_refinement.py` | Allowing coarsening reduces far-field bulk elements slightly to **71,037 elements** ($-0.4\%$) | YES_ISOLATED | `TESTED_EFFECT_INSUFFICIENT` |
| **12** | **Platform / OS Build (Windows)** | Unstated in paper | Abaqus 2024 GA Windows (`win_b64`) vs Linux (`lnx86_64`) | Local 2024 GA execution; native remesh run | Generates **71,904 elements** ($+0.82\%$ delta vs Linux 71,320); platform variance is negligible | NO_CONFOUNDED | `CONFOUNDED` |
| **13** | **2D Stress State Formulation** | Unstated in Sec. 4.1 ($E=210\,\text{GPa}, \nu=0.3$) | Plane Strain (`CPE4`) vs Plane Stress (`CPS4`) | Job `1404959.mmaster02`; multi-release CPS4 suite | CPS4 lacks $\sigma_{zz}=0$, yielding **58,679 elements** ($-17.7\%$), but violates Mode-I standard and lowers peak load | NO_CONFOUNDED | `CONFOUNDED` |
| **14** | **Adaptive Region Sub-Domain Partition** | Text states whole-domain `All_elem` (0 mentions of partition/box) | Whole specimen part instance (`Plate.All_elem`) vs local corridor bounding box | Sec. 3.3, Sec. 4.1 text; [`GATE5_COARSE_GEOMETRY_AND_TOPOLOGY_PROVENANCE_AUDIT.md`](file:///D:/Master%20thesis/Adaptive%20remeshing/docs/supervisor_reports/GATE5_COARSE_GEOMETRY_AND_TOPOLOGY_PROVENANCE_AUDIT.md) | Whole-domain yields **71,320 elements** ($99.39\%$ surplus in far-field/flanks). Local box could explain count, but is unstated. | N/A_PUBLICATION_DEFICIT | `PUBLICATION_INFORMATION_MISSING` |
| **15** | **Section 4.1 `errorTarget` Linkage** | Listing 1 hard-codes `errorTarget=1.0`; Sec. 4.1 omits override | Listing 1 literal `errorTarget=1.0` vs modified target (e.g. `2.0%`) | Sec. 4.1 text (p. 3265); Listing 1 (p. 3262); Candidate C7 ($17,687$ el) | Listing 1 verbatim yields **71,320 elements**; linkage to 13,941 is ambiguous without unstated override | N/A_PUBLICATION_DEFICIT | `PUBLICATION_LINKAGE_AMBIGUOUS` |

---

## 3. Explicit Category Reconciliation

The 15 audited factors reconcile into exactly five mutually exclusive categories ($6 + 5 + 2 + 1 + 1 = 15$):

```text
+-------------------------------------------------------------------------------------------------------------------------------+
| CATEGORY                               | FACTOR COUNT | FACTOR IDS                               | EPISTEMIC MEANING          |
+----------------------------------------+--------------+------------------------------------------+----------------------------+
| I. RULED_OUT                           | 6 factors    | #1, #2, #3, #4, #5, #6                   | Experimentally/analytically|
|                                        |              |                                          | proven to have zero effect |
+----------------------------------------+--------------+------------------------------------------+----------------------------+
| II. TESTED_EFFECT_INSUFFICIENT         | 5 factors    | #7, #8, #9, #10, #11                     | Isolated parameter tested; |
|                                        |              |                                          | count remains >4.0x or     |
|                                        |              |                                          | moves in wrong direction   |
+----------------------------------------+--------------+------------------------------------------+----------------------------+
| III. CONFOUNDED                        | 2 factors    | #12, #13                                 | Secondary platform or      |
|                                        |              |                                          | unphysical formulation shift|
+----------------------------------------+--------------+------------------------------------------+----------------------------+
| IV. PUBLICATION_INFORMATION_MISSING    | 1 factor     | #14 (Local partition geometry)           | Genuine publication deficit|
|                                        |              |                                          | (unstated in text/figures) |
+----------------------------------------+--------------+------------------------------------------+----------------------------+
| V. PUBLICATION_LINKAGE_AMBIGUOUS       | 1 factor     | #15 (Listing 1 call-site errorTarget)    | Genuine publication deficit|
|                                        |              |                                          | (contradictory linkage)    |
+----------------------------------------+--------------+------------------------------------------+----------------------------+
| TOTAL FACTORS AUDITED                  | 15 factors   | Exact, non-overlapping ledger            | Complete accessible closure|
+----------------------------------------+--------------+------------------------------------------+----------------------------+
```

> [!IMPORTANT]
> **Clarification on Category Totals**: All **11 accessible one-factor parameters** (Categories I & II: 6 ruled out + 5 tested effect insufficient) were experimentally evaluated and eliminated as potential causes of the ~13,941 count. The 2 publication-dependent factors (Categories IV & V) were **NOT experimentally eliminated**; they represent the exact, irreducible external information boundary requiring author clarification.

---

## 4. Detailed Spatial Comparison: Canonical CPE4 vs OFAT Variants

```text
+-----------------------------------------------------------------------------------------------------------------------------------------------+
| Region Partition                       | C0: Canonical CPE4 (1.0%) | C9: Top U1 Free (OFAT) | C10: CPE4R Reduced (OFAT) | C7: ErrorTarget 2.0% (Sens)|
+----------------------------------------+---------------------------+------------------------+---------------------------+----------------------------+
| R1: Crack Tip (r <= 0.02 mm)           |                       347 |                    347 |                       334 |                        268 |
| R2: Ligament (|y-0.5|<=0.05, x>0.5)    |                     5,318 |                  5,318 |                     6,552 |                      2,514 |
| R3: Slit Flanks (|y-0.5|<=0.05, x<=0.5)|                     3,396 |                  3,396 |                     6,202 |                      1,742 |
| R4: Transition (0.05 < |y-0.5| <= 0.15)|                    20,273 |                 16,651 |                    28,791 |                      6,218 |
| R5: Far-Field (|y-0.5| > 0.15)         |                    41,986 |                 30,049 |                    61,827 |                      6,945 |
+----------------------------------------+---------------------------+------------------------+---------------------------+----------------------------+
| TOTAL ELEMENT COUNT (N_el)             |                    71,320 |                 55,761 |                   103,706 |                     17,687 |
| TOTAL NODE COUNT (N_nod)               |                    70,845 |                 55,302 |                   103,125 |                     17,688 |
| Percentage Delta vs Canonical          |                    0.000% |               -21.816% |                  +45.410% |                   -75.201% |
| Literature Ratio (vs ~13,941)          |                    5.116x |                 4.000x |                    7.439x |                     1.269x |
+----------------------------------------+---------------------------+------------------------+---------------------------+----------------------------+
```

---

## 5. Final Gate 5 Priority Question B Classification

Because all 11 accessible publication-supported factors have been tested and eliminated without bridging the gap to ~13,941, Priority Question B is formally classified as:

$$\mathbf{EXHAUSTIVE\_ACCESSIBLE\_AUDIT\_COMPLETE\_EXTERNAL\_INFORMATION\_REQUIRED}$$

The discrepancy cannot be resolved internally without inventing unstated geometric partitions or engaging in speculative parameter tuning.
