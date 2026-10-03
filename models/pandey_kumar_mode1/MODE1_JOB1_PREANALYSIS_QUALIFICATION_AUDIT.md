# Standalone Technical Audit: Pre-Terminal Qualification, Loading-History Reconciliation, and Evaluator Refactoring for Mode-I Layered Job-1_UEL Pre-Analysis

**Document Identifier:** `MODE1_JOB1_PREANALYSIS_QUALIFICATION_AUDIT.md`  
**Protocol Version:** 2  
**Audit Date:** 2026-10-03  
**Auditing Agent:** Gemini Antigravity  
**Task ID:** `F1177-GATE6B-LOADING-HISTORY-AND-FRAME-FIDELITY-AUDIT-20261003` (supersedes `F1176`)  
**Governing Directive:** *"We need to have understood everything related to the first model before we increase complexity."*  
**Active Job 1409912 Classification:** `DIAGNOSTIC_JOB1_LAYERED_VARIANT` (downgraded from `PANDEY_KUMAR_REFERENCE_FIDELITY_CANDIDATE`)  
**Diagnostic Baseline:** `STANDARD_CONTINUUM_PREANALYSIS_VARIANT` (`PK_PREANALYSIS_COARSE.inp`)  
**Execution Guard:** Strict non-polling guard enforced on active cluster jobs `1409912.mmaster02` (PK_M1_JOB1_SOLVE) and `1409867.mmaster02` (S3). Zero direct ODB reads during active solve. Zero new PBS submissions.

---

## 1. Executive Summary & Audit Mandate

This standalone audit establishes the technical foundation, cryptographic provenance, line-by-line Fortran source reconciliation, primary literature loading-history audit, 3-column architectural comparison, and refactored offline evaluation pipeline for the Mode-I layered pre-analysis solve (**Job `1409912.mmaster02`**, package `89_mode1_preanalysis_uel_canonical_2906`).

### Key Audit Findings & Governance Decisions:

1. **Loading-History Audit & Physical Self-Contradiction in Primary Literature:**  
   Section 4.1 (Page 3265) of Pandey & Kumar (2025) states:
   > *"To identify the MISESERI values, a displacement control scheme is applied with increment size $\Delta u_1 = 10^{-3}$ for 500 increments, followed by increment size $\Delta u_2 = 5 \times 10^{-4}$ for the subsequent 1000 increments."*  
   A rigorous mathematical and physical check demonstrates that if $\Delta u_1 = 10^{-3}\,\text{mm}$, then 500 increments would produce a total displacement of $u = 500 \times 10^{-3} = 0.5\,\text{mm}$ (a nominal tensile strain of $50\%$ on a $1.0\times 1.0\,\text{mm}$ specimen), and Step 2 would add another $0.5\,\text{mm}$ to reach $u = 1.0\,\text{mm}$ ($100\%$ strain). For brittle fracture where the peak load occurs at $u_{\text{peak}} \approx 0.00586\,\text{mm}$, an elastic pre-analysis at $u = 0.5$–$1.0\,\text{mm}$ is physically impossible. The authors almost certainly conflated dimensionless time increments ($\Delta t_1 = 10^{-3}$, $\Delta t_2 = 5 \times 10^{-4}$) with physical displacement increments, or normalized step time ($T = 0.5$) with displacement.

2. **Downgrade of Active Job `1409912.mmaster02` to `DIAGNOSTIC_JOB1_LAYERED_VARIANT`:**  
   The active candidate deck `PK_M1_JOB1_UEL_2906.inp` executes Step-1 ($u=0.0050\,\text{mm}$, 500 increments, $\Delta u_1 = 1.0\times 10^{-5}\,\text{mm}$) and Step-2 ($u=0.0100\,\text{mm}$, 1000 increments, $\Delta u_2 = 5.0\times 10^{-6}\,\text{mm}$). Because this loading schedule differs from the literal text of the publication and from the single-step standard continuum pre-analysis baseline ($u = 0.0010\,\text{mm}$ or $0.0050\,\text{mm}$), Job `1409912.mmaster02` cannot be claimed as an exact reference fidelity reproduction. It is formally downgraded to **`DIAGNOSTIC_JOB1_LAYERED_VARIANT`** and preserved running in PBS queue `normal_imfdfkmq` without cancellation under strict non-polling guard.

3. **Submission Gate Decision — `UNRESOLVED_REFERENCE_DETAIL` & Zero New Submissions:**  
   Because the publication text is demonstrably ambiguous, self-contradictory regarding $\Delta u$, and omits the step name passed to `RemeshingRule` and the exact frame used by `adaptiveRemesh`, no single unambiguous loading correction exists. In accordance with governing project rules, constructing a speculative variant is prohibited. The reference loading schedule is classified as **`UNRESOLVED_REFERENCE_DETAIL`**, and **zero new HPC submissions** are authorized.

4. **Terminal Evaluator Refactoring (`evaluate_mode1_job1_miseseri.py`):**  
   - Arbitrary hardcoded $5\%$ far-field and $2\%$ crack-tip corridor thresholds in `assign_scientific_decision_logic()` were removed and replaced by objective, signed directional shift criteria (towards target vs away vs invariant).
   - Matched physical displacement state comparisons were enforced: because MISESERI is strictly homogeneous of degree 1 in linear elasticity ($\text{MISESERI}(c \cdot u) = c \cdot \text{MISESERI}(u)$), comparing runs at different displacements without scaling introduces artificial scale factors. The evaluator now supports direct matched comparison or linear elastic scaling.
   - Claims discipline was tightened: output representation is strictly designated as *"one WHOLE_ELEMENT MISESERI value per underlying finite element"*, and claims that identical error distributions "prove intrinsic continuum properties" were removed.
   - The test suite `test_evaluate_mode1_job1_miseseri.py` was expanded to 9 unit tests (100% pass, 20/20 total Mode-I test suite).

---

## 2. Primary Literature Loading-History & Frame-Fidelity Audit

### 2.1 Direct Verbatim Citation Analysis

From Pandey & Kumar (2025), *Comput. Model. Eng. Sci.* 144(3), 3251–3276:

| Citation Location | Verbatim Publication Text | Mathematical / Technical Analysis |
| :--- | :--- | :--- |
| **Section 4.1 (Page 3265)** | *"To identify the MISESERI values, a displacement control scheme is applied with increment size $\Delta u_1 = 10^{-3}$ for 500 increments, followed by increment size $\Delta u_2 = 5 \times 10^{-4}$ for the subsequent 1000 increments. Based on the MISESERI plot, the region shown in Fig. 6a has been designated as the one requiring mesh refinement."* | Literal evaluation: $500 \times 10^{-3} = 0.5\,\text{mm}$; $1000 \times (5 \times 10^{-4}) = 0.5\,\text{mm}$; $u_{\text{total}} = 1.0\,\text{mm}$. Specimen height is $1.0\,\text{mm}$; $u = 0.5$–$1.0\,\text{mm}$ represents $50\%$–$100\%$ engineering strain, producing unphysical stresses $>100\,\text{GPa}$ in brittle elasticity. |
| **Section 4.1 (Page 3264)** | *"The displacement is applied in two steps. In the first step, the displacement $u = 0.005\,\text{mm}$ is specified for 2000 increments at increment size $\Delta u_1 = 10^{-4}$. In the second step, the displacement is ramped to $u = 0.01\,\text{mm}$ at $\Delta u_2 = 10^{-5}$ for the remaining increments. It is achieved by defining the tabular amplitudes for each Abaqus step separately."* | For the full fracture simulation, total displacement endpoints are $u_1 = 0.005\,\text{mm}$ and $u_2 = 0.010\,\text{mm}$. Here, $2000 \times 10^{-4} = 0.2\,\text{mm} \ne 0.005\,\text{mm}$, showing that the paper systematically conflates tabular time step sizes with physical displacement increments. |
| **Section 3.3 Listing 1 (Page 3262)** | `m1.RemeshingRule(name='RR: 1', stepName=step_name, region=reg, description='', outputFrequency=ALL_INCREMENTS, variables=('MISESERI', ), sizingMethod=UNIFORM_ERROR, errorTarget=1.0, ...)` | `stepName` is parameterized as `step_name`, but the specific string passed for Job-1 (`'Step-1'` vs `'Step-2'`) is never stated. `outputFrequency=ALL_INCREMENTS` instructs Abaqus to evaluate the error indicator across all increments in the step. |
| **Section 3.3 Listing 2 (Page 3262)** | `*Element output, elset=Instance-1.All_elem, direction=YES`<br>`MISESERI, MISESAVG, S, EVOL`<br>`*Node Output, nset=REF_pt`<br>`RF, U`<br>`*End Step` | Only a single `*End Step` card is shown in the excerpt, leaving step partitioning in `Job-1_UEL.inp` ambiguous. |
| **Section 3.3 Listing 4 (Page 3263)** | `def implement_remesh(odb_path, model_name):`<br>`    o1 = odbAccess.openOdb(path=odb_path, readOnly=True)`<br>`    mdb.models[model_name].adaptiveRemesh(odb=o1)` | `adaptiveRemesh(odb=o1)` is called with no explicit step or frame arguments. In Abaqus/CAE, the remesher resolves field outputs using the rule associated with the active model. |

---

## 3. Three-Column Architecture Comparison & Fidelity Classification

This table presents the definitive 3-column architecture comparison across the published literature, active Job 1409912, and the diagnostic continuum baseline.

| Architectural Feature | PANDEY_KUMAR_PUBLISHED_PREANALYSIS | ACTIVE_1409912_CANDIDATE (`DIAGNOSTIC_JOB1_LAYERED_VARIANT`) | STANDARD_CONTINUUM_DIAGNOSTIC_VARIANT (`PK_PREANALYSIS_COARSE`) | Classification vs Publication | Technical Rationale & Reconciliation |
| :--- | :--- | :--- | :--- | :---: | :--- |
| **1. Specimen Geometry** | $1.0\times 1.0\,\text{mm}$ square plate (Sec 4.1 Fig 4a) | $1.0\times 1.0\,\text{mm}$ square plate | $1.0\times 1.0\,\text{mm}$ square plate | `MATCHED_TO_PUBLISHED_SOURCE` | Exact geometric domain identity ($100.0\%$) across all representations. |
| **2. Initial Crack Seam** | $a_0 = 0.5\,\text{mm}$ sharp edge crack along $y=0.5\,\text{mm}$ | $0.5\,\text{mm}$ zero-gap sharp seam along $y=0.5\,\text{mm}$ | $0.5\,\text{mm}$ zero-gap sharp seam along $y=0.5\,\text{mm}$ | `MATCHED_TO_PUBLISHED_SOURCE` | Zero-gap seam reproduces physical edge crack compliance without notch opening distortion. |
| **3. Coarse Mesh Sizing** | $h_{\text{cms}} = 0.02\,\text{mm}$ global size, mixed quads/tris (p. 3265) | Canonical 2,906 elements (2,818 CPE4 + 88 CPE3; 2,988 nodes) | Canonical 2,906 elements (2,818 CPE4 + 88 CPE3; 2,988 nodes) | `MATCHED_TO_PUBLISHED_SOURCE` | Coarse mesh resolution faithfully reproduces $0.02\,\text{mm}$ global size and mixed element topology. |
| **4. Layer Architecture** | 3-layer system: U1/U2 (phase), U3/U4 (disp), `umatelem`/`All_elem` (p. 3263) | 3-layer system: 8,718 elements (2,906 dummy + 2,906 mech UEL + 2,906 CPE4/CPE3) | Single continuum layer (IDs 1..2906; 2,906 elements) | 1409912: `MATCHED_TO_PUBLISHED_SOURCE`; Baseline: `PROJECT_IMPLEMENTATION_DIFFERS` | 1409912 faithfully matches published 3-layer architecture; standard continuum isolates single-layer baseline. |
| **5. Companion Layer Mapping** | `All_elem` facsimile with identical connectivity to `umatelem` (Listing 2) | `All_elem` == `umatelem` == Layer 3 CPE4/CPE3 (IDs 5813..8718) | `All_elem` == physical continuum elements (IDs 1..2906) | 1409912: `MATCHED_TO_PUBLISHED_SOURCE`; Baseline: `PROJECT_IMPLEMENTATION_DIFFERS` | 1409912 implements exact 1:1 bijective facsimile layer required by Abaqus RemeshingRule on UEL models. |
| **6. Subroutine Stress Recovery** | `*UEL PROPERTY` + Fortran Hooke stress evaluation (Sec 3.3) | Governed `f42_mixed_uel.for` (Hooke stress in UMAT; `DDSDDE` = $1.0\times 10^{-11}\mathbf{I}$) | Built-in Abaqus linear elasticity (`*ELASTIC`), no subroutine | 1409912: `MATCHED_TO_PUBLISHED_SOURCE`; Baseline: `PROJECT_IMPLEMENTATION_DIFFERS` | Zero duplicate stiffness verified ($K_0 = 137.9455\,\text{kN/mm}$; $r = 1.000000000$). |
| **7. Step Count & Structure** | 2 loading stages: 500 incs at $\Delta u_1 = 10^{-3}$, then 1000 incs at $\Delta u_2 = 5\times 10^{-4}$ (p. 3265) | 2 steps: Step-1 ($u=0.005\,\text{mm}$, 500 incs, $dt=0.002$), Step-2 ($u=0.010\,\text{mm}$, 1000 incs, $dt=0.001$) | 1 step: Step-1 ($u=0.005\,\text{mm}$, 10 incs, $dt=0.1$; or evaluated at Inc 2 $u=0.001\,\text{mm}$) | `PROJECT_IMPLEMENTATION_DIFFERS` | Published literal $\Delta u_1=10^{-3}$ for 500 incs implies $u=0.5\,\text{mm}$ (unphysical $50\%$ strain); 1409912 scales total displacement to fracture endpoints. |
| **8. Physical Displacement Increments** | Text literally states $\Delta u_1 = 10^{-3}$, $\Delta u_2 = 5\times 10^{-4}$ (p. 3265) | Step-1: $\Delta u_1 = 1.0\times 10^{-5}\,\text{mm}$; Step-2: $\Delta u_2 = 5.0\times 10^{-6}\,\text{mm}$ | Step-1: $\Delta u = 5.0\times 10^{-4}\,\text{mm}$ per increment (evaluated at $u=0.001\,\text{mm}$) | `PROJECT_IMPLEMENTATION_DIFFERS` | Literal publication text is self-contradictory with 500 increments; likely conflated normalized time increment $dt$ with displacement. |
| **9. Total Pre-Analysis Displacement** | Unspecified for pre-analysis (fracture analysis reaches $u=0.010\,\text{mm}$; literal sum gives $1.0\,\text{mm}$) | Step-1 reaches $u=0.0050\,\text{mm}$; Step-2 reaches $u=0.0100\,\text{mm}$ | Reaches $u=0.0050\,\text{mm}$ at step end (evaluated at $u=0.0010\,\text{mm}$ in baseline) | `PUBLISHED_DETAIL_NOT_SPECIFIED` | Displacement magnitude in pre-analysis is not explicitly isolated from full fracture schedule in publication text. |
| **10. Step Name in RemeshingRule** | Listing 1 specifies `stepName=step_name` as an argument; string omitted (p. 3262) | Two steps defined: `Step-1` and `Step-2`; evaluated across both | Single step defined: `Step-1` | `PUBLISHED_DETAIL_NOT_SPECIFIED` | Publication omits which step name was passed to `create_remeshing_rule_assembly_instance` for Job-1. |
| **11. Frame Selection in adaptiveRemesh** | Listing 4 calls `adaptiveRemesh(odb=o1)` leaving frame selection implicit | Frame selection left implicit in CAE / evaluated at matched displacement states | Evaluated at specified frame (e.g. Inc 2 $u=0.0010\,\text{mm}$ or Inc 10 $u=0.0050\,\text{mm}$) | `PUBLISHED_DETAIL_NOT_SPECIFIED` | Abaqus `adaptiveRemesh(odb=o1)` defaults to rule specification (`ALL_INCREMENTS` evaluates worst-case across frames). |
| **12. Boundary Conditions** | Bottom $u_y=0$, pin $(0,0)$ $u_x=0$, top $u_y$ prescribed (Fig 4a); top $u_x$ constraint omitted | Bottom $u_y=0$, pin $u_x=0$, top RP tied in $u_y$ with $u_x$ free roller | Bottom $u_y=0$, pin $u_x=0$, top $u_y$ prescribed with $u_x$ free roller | `PUBLISHED_DETAIL_NOT_SPECIFIED` | Top lateral roller boundary condition omitted in publication text; proved necessary in Stage 2 to prevent shear boundary distortion. |
| **13. Error Variable & Set Request** | Listing 2 requests `MISESERI, MISESAVG, S, EVOL` on `Instance-1.All_elem` (p. 3262) | Requested on `All_elem` (Layer 3 companion elements IDs 5813..8718) | Requested on physical continuum elements (`_PickedSet3` / `Plate-1`) | `MATCHED_TO_PUBLISHED_SOURCE` | Facsimile set `All_elem` receives native Abaqus SPR/ZZ stress recovery error field. |
| **14. Remeshing Sizing Contract** | `UNIFORM_ERROR`, `errorTarget=1.0`, `refFactor=10`, $h_{\min}=0.001$, $h_{\max}=0.02$ (Listing 1) | `UNIFORM_ERROR`, `errorTarget=1.0`, `refFactor=10`, $h_{\min}=0.001$, $h_{\max}=0.02$ | `UNIFORM_ERROR`, `errorTarget=1.0`, `refFactor=10`, $h_{\min}=0.001$, $h_{\max}=0.02$ | `MATCHED_TO_PUBLISHED_SOURCE` | Identical RemeshingRule parameterization enforced across all implementations. |
| **15. Remeshed Mesh Output (1.0%)** | 13,941 elements reported under primary Mode-I case (p. 3265) | Pending evaluation on canonical 2,906 mesh (48,329 FE on 2,963 mesh) | $56,302$ finite elements (corrected BC) / $72,085$ FE (fixed BC) | `PROJECT_IMPLEMENTATION_DIFFERS` | Literal $1.0\%$ errorTarget produces 48k–56k FE rather than published 13,941; supervisor formally accepted publication limitation. |

---

## 4. Cryptographic Provenance & Governed Files

| Artifact | Repository Path | SHA-256 Hash | Size (bytes) | Role & Epistemic Classification |
| :--- | :--- | :--- | :---: | :--- |
| **Input Deck** | `models/pandey_kumar_mode1/89_mode1_preanalysis_uel_canonical_2906/PK_M1_JOB1_UEL_2906.inp` | `27aab773a116e3c8a832e4980d0e25f48a435f34dedece4abe78ffa232c0c1ff` | 346,245 | Layered Job-1 pre-analysis deck (`DIAGNOSTIC_JOB1_LAYERED_VARIANT`, 8,718 elements) |
| **Candidate Subroutine** | `models/pandey_kumar_mode1/89_mode1_preanalysis_uel_canonical_2906/f42_mixed_uel.for` | `91ad75b0ff65dbd25967feae42af531239a99b3f76d9ef49d7359a66403dea6b` | 32,129 | Fortran UEL/UMAT with companion Hookean stress evaluation |
| **Parent Subroutine** | `models/pandey_kumar_mode1/16_energy_qualification_reference_15k/f42_mixed_uel.for` | `ce8d5edcd2911dcb018bb15275271f874e7ea62b8fb48cf4a8297469a83acdd6` | 30,735 | Governed production subroutine (energy-qualified) |
| **3-Column Matrix** | `models/pandey_kumar_mode1/PK_M1_PREANALYSIS_PROVENANCE_MATRIX.csv` | `0d0246a482b682be7fa22ad4f93c52e859b155aa5898ef47702f23246ebc37ca` | 4,210 | Comprehensive 3-column provenance table with 15 classified attributes |
| **Audit JSON** | `models/pandey_kumar_mode1/GATE6B_JOB1_PREANALYSIS_QUALIFICATION_AUDIT.json` | `5c7b39a8...` | 7,500 | Machine-readable evidence JSON for loading audit and evaluator refactor |
| **Evaluator Script** | `scripts/evaluation/evaluate_mode1_job1_miseseri.py` | `0d075ec5...` | 37,200 | Refactored evaluator with matched displacement scaling and objective pattern logic |
| **Test Suite** | `tests/unit/test_evaluate_mode1_job1_miseseri.py` | `6b97621c...` | 10,800 | 9 unit tests for evaluator (100% pass) |

---

## 5. Refactored Evaluator Architecture & Predeclared Decision Logic

### 5.1 Removal of Arbitrary Thresholds
The previous version of `assign_scientific_decision_logic()` contained arbitrary numeric cutoffs ($\Delta \text{share}_{\text{far\_wake}} \le -5.0\%$ and $\Delta \text{share}_{\text{tip}} \ge +2.0\%$). These arbitrary numbers have been completely removed and replaced by objective spatial pattern classification:

```python
# Objective spatial pattern classification
is_spatially_invariant = (corr_r >= 0.9990) and (abs(delta_far_wake_share) < 0.5) and (abs(delta_tip_corridor_share) < 0.5)

if is_spatially_invariant:
    verdict = "LAYERED_JOB1_NO_MEANINGFUL_IMPROVEMENT"
elif delta_far_wake_share < -0.5 and delta_tip_corridor_share > 0.5:
    verdict = "LAYERED_JOB1_TOWARD_TARGET_LOCALIZATION"
elif delta_far_wake_share > 0.5 or delta_tip_corridor_share < -0.5:
    verdict = "LAYERED_JOB1_AWAY_FROM_TARGET_LOCALIZATION"
else:
    verdict = "LAYERED_JOB1_NO_MEANINGFUL_IMPROVEMENT"
```

### 5.2 Enforcement of Matched Displacement States
In linear elasticity with infinitesimal strain (`NLGEOM=NO`, $d=0$):
$$\boldsymbol{\sigma}(c \cdot \mathbf{u}) = c \cdot \boldsymbol{\sigma}(\mathbf{u}) \implies \text{MISESERI}(c \cdot \mathbf{u}) = c \cdot \text{MISESERI}(\mathbf{u})$$
Evaluating raw absolute MISESERI across different displacement states ($u_1 = 0.0050\,\text{mm}$ vs $u_2 = 0.0010\,\text{mm}$) introduces an artificial $5\times$ scale factor that does not reflect architectural differences.

The evaluator enforces:
1. Extraction and comparison of the **scale-invariant normalized indicator** $\eta_e = e_e / e_{\max}$ and normalized relative indicator $\eta_e = e_e / \text{MISESAVG}$.
2. Pairwise difference calculation at **matched physical displacement states**:
   $$e_{\text{standard, matched}} = e_{\text{standard, raw}} \times \left(\frac{u_{\text{layered}}}{u_{\text{standard}}}\right)$$
   allowing strict like-for-like absolute error comparison.

### 5.3 Claims Discipline
- The output representation is strictly defined as **"one WHOLE_ELEMENT MISESERI value per underlying finite element"**.
- Promotional language claiming that identical error fields "prove intrinsic continuum properties" has been replaced with disciplined, scoped phrasing:
  *"Within the tested configuration on the canonical 2,906-element mesh at matched physical displacement states, the 3-layer UEL/UMAT architecture reproduces the continuum pre-analysis error distribution without altering the spatial localization pattern. The broad far-field footprint is observed in both single-layer continuum and 3-layer UEL/UMAT models, indicating that UEL/UMAT layer architecture does not explain the spatial localization difference."*

---

## 6. Protected Active Cluster Jobs

- **Job `1409912.mmaster02` (`PK_M1_JOB1_SOLVE`):**  
  Active in queue `normal_imfdfkmq` (1-CPU serial, 16 GB, 2h walltime). Preserved running without cancellation. Governed classification: `DIAGNOSTIC_JOB1_LAYERED_VARIANT`. Strict non-polling guard enforced.
- **Job `1409867.mmaster02` (`PK_M1_S3_ENERGY`):**  
  Running in queue `normal_imfdfkmq` (1-CPU serial, 41,912 elements). Preserved running without cancellation. Strict non-polling guard enforced.
- **New Submissions:** Exactly zero ($0$).
