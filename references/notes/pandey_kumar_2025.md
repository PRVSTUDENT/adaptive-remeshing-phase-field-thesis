# Pandey and Kumar (2025)

**Source**: `Literature review/TSP_CMES_67858.pdf` / `references/pandey_pdf_text.txt`  
**Citation**: Pandey, A., & Kumar, S. (2025). *A Simple and Robust Mesh Refinement Implementation in Abaqus for Phase Field Modelling of Brittle Fracture*. Computer Modeling in Engineering & Sciences (CMES), 144(3), 3251–3276. doi:10.32604/cmes.2025.067858

---

## 1. Authoritative Benchmark Sizing & Target Matrix (Direct Literature Audit)

| Benchmark Case | Description / Parameters | Discretization Specification | Total Element Count | Node Count | Source Reference (CMES 144(3)) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Mode-I SENT (Standard PFM)** | $1.0\times 1.0\,\text{mm}$ plate, $a_0 = 0.5\,\text{mm}$, $l_0 = 0.0075\,\text{mm}$, $E = 210\,\text{GPa}, \nu = 0.3, G_c = 2.7\times 10^{-3}\,\text{kN/mm}$ | Global $h = 0.02\,\text{mm}$, manual refined band $h = 0.003\,\text{mm}$ | **26,282** (linear quads & tris) | ~26,500 | Sec. 4.1, Page 3264, Par. 3, Fig. 5a |
| **Mode-I SENT (Proposed PFM)** | Same geometry & material, $l_0 = 0.0075\,\text{mm}$, $R_r$: $\text{errorTarget}=1\%$, $h_{\min}=0.001\,\text{mm}, h_{\max}=0.02\,\text{mm}$ | Global $h = 0.02\,\text{mm}$, local adaptively refined $h = 0.001\,\text{mm}$ | **13,941** (linear quads & tris) | ~14,100 | Sec. 4.1, Page 3265, Par. 3, Fig. 5b, Fig. 7b |
| **Mode-I Sensitivity ($h_{cms}=0.02$)** | $l_0 = 0.01\,\text{mm}, \text{errorTarget}=5, \text{refinementFactor}=10$ | $h_{cms} = 0.02\,\text{mm}$ | **6,382** | 6,436 | Sec. 4.1.1, Table 1, Page 3268 |
| **Mode-I Sensitivity ($h_{cms}=0.03$)** | $l_0 = 0.01\,\text{mm}, \text{errorTarget}=5, \text{refinementFactor}=10$ | $h_{cms} = 0.03\,\text{mm}$ (Optimal baseline) | **4,547** | 4,580 | Sec. 4.1.1, Table 1, Page 3268 |
| **Mode-I Sensitivity ($h_{cms}=0.035$)**| $l_0 = 0.01\,\text{mm}, \text{errorTarget}=5, \text{refinementFactor}=10$ | $h_{cms} = 0.035\,\text{mm}$ | **4,462** | 4,497 | Sec. 4.1.1, Table 1, Page 3268 |
| **Mode-I Sensitivity ($h_{cms}=0.04$)** | $l_0 = 0.01\,\text{mm}, \text{errorTarget}=5, \text{refinementFactor}=10$ | $h_{cms} = 0.04\,\text{mm}$ | **4,934** | 4,951 | Sec. 4.1.1, Table 1, Page 3268 |
| **Mode-I Sensitivity ($h_{cms}=0.05$)** | $l_0 = 0.01\,\text{mm}, \text{errorTarget}=5, \text{refinementFactor}=10$ | $h_{cms} = 0.05\,\text{mm}$ | **3,141** | 3,253 | Sec. 4.1.1, Table 1, Page 3268 |

---

## 2. Requirements-to-Code Matrix (Task 4)

| Component | Paper Specification / Provenance | Repository Implementation | Status |
| :--- | :--- | :--- | :---: |
| **Error Indicator Trigger** | Sec. 3.1, Listing 1, 3: `MISESERI` superconvergent patch recovery on `Instance-1.All_elem` | [`scripts/remeshing/extract_miseseri_from_odb.py`](file:///D:/Master%20thesis/Adaptive%20remeshing/scripts/remeshing/extract_miseseri_from_odb.py), [`scripts/adaptive_online/trigger_engine.py`](file:///D:/Master%20thesis/Adaptive%20remeshing/scripts/adaptive_online/trigger_engine.py) | **`COMPLETE_VERIFIED_END_TO_END`** |
| **Remeshing Rule Spec** | Sec. 3.3 Listing 1: `RemeshingRule` with `UNIFORM_ERROR`, `errorTarget=1.0`, `coarseningFactor=NOT_ALLOWED`, `refinementFactor=10`, `minElementSize`, `maxElementSize` | [`scripts/remeshing/pandey_kumar_adaptive_refinement.py`](file:///D:/Master%20thesis/Adaptive%20remeshing/scripts/remeshing/pandey_kumar_adaptive_refinement.py) `create_remeshing_rule_spec()` | **`COMPLETE_VERIFIED_END_TO_END`** |
| **Relative Error Marking** | Sec. 3.3, Sec. 4.1: $MISESERI_i / \max(MISESERI) \ge \text{errorTarget}$ (1%–5%) | [`scripts/remeshing/pandey_kumar_adaptive_refinement.py`](file:///D:/Master%20thesis/Adaptive%20remeshing/scripts/remeshing/pandey_kumar_adaptive_refinement.py) `evaluate_miseseri_marking()` | **`COMPLETE_VERIFIED_END_TO_END`** |
| **Layered UEL Architecture** | Sec. 3.2: U1/U3 (phase-field), U2/U4 (displacement), `umatelem` / `All_elem` overlay | [`scripts/adaptive_online/deck_rebuilder.py`](file:///D:/Master%20thesis/Adaptive%20remeshing/scripts/adaptive_online/deck_rebuilder.py), `f42_mixed_uel.for` | **`COMPLETE_VERIFIED_END_TO_END`** |
| **Graded Refined Mesher** | Sec. 4.1: Bounded refined window along crack path, smooth geometric ratio grading ($h_{\min} = 0.001\,\text{mm}, h_{\max} = 0.02\,\text{mm}$) | [`scripts/remeshing/pandey_kumar_adaptive_refinement.py`](file:///D:/Master%20thesis/Adaptive%20remeshing/scripts/remeshing/pandey_kumar_adaptive_refinement.py) `generate_graded_axis_coordinates()`, `build_mode1_mesh()` | **`COMPLETE_VERIFIED_END_TO_END`** |
| **Python 2-Pass Orchestrator** | Sec. 3.3 Fig. 2–3, Listing 4: `Job-1.inp` (coarse) $\to$ Pre-analysis $\to$ `mdb.models[m].adaptiveRemesh(odb=o1)` $\to$ `Job-2_UEL.inp` (refined) $\to$ Final solve | [`scripts/remeshing/run_pandey_kumar_native_orchestration.py`](file:///D:/Master%20thesis/Adaptive%20remeshing/scripts/remeshing/run_pandey_kumar_native_orchestration.py) | **`COMPLETE_VERIFIED_END_TO_END`** |
| **End-to-End Deck Integrity Audit** | Direct verification of actual `PK_MODE1_JOB2_REFINED.inp` vs `Job-2_UEL.inp` | [`scripts/remeshing/generate_task5_production_package.py`](file:///D:/Master%20thesis/Adaptive%20remeshing/scripts/remeshing/generate_task5_production_package.py) | **`COMPLETE_VERIFIED_END_TO_END` (0 mismatches across 2,288 nodes)** |
| **Unit & Regression Tests** | Verification of data structures, bounds, shoelace areas, monotonic step schedules, deck conversion, coarsening rules, fail-closed mesh alteration | [`tests/unit/test_pandey_kumar_adaptive_refinement.py`](file:///D:/Master%20thesis/Adaptive%20remeshing/tests/unit/test_pandey_kumar_adaptive_refinement.py), [`tests/unit/test_pandey_kumar_step_increment_consistency.py`](file:///D:/Master%20thesis/Adaptive%20remeshing/tests/unit/test_pandey_kumar_step_increment_consistency.py) | **`COMPLETE_VERIFIED_END_TO_END` (11/11 PASS)** |

---

## 3. Task 5 Production Package & Solver Execution

- **Package Directory**: `models/pandey_kumar_mode1/02_proposed_adaptive_refined/`
- **Case Name**: `PK_MODE1_PROPOSED_PFM`
- **Parameters**: $E = 210\,\text{GPa}, \nu = 0.3, l_0 = 0.0075\,\text{mm}, G_c = 2.7\times 10^{-3}\,\text{kN/mm}, \eta = 1.0\times 10^{-7}$
- **Remeshing Rule**: `errorTarget = 1.0%`, $h_{\min} = 0.001\,\text{mm}$, $h_{\max} = 0.02\,\text{mm}$, `coarsening = NOT_ALLOWED`, `refinementFactor = 10`
- **Datacheck PBS Job**: `1398806.mmaster02` (COMPLETED, EXIT: 0, 0 ERRORS)
- **Production Solver PBS Job**: `1398807.mmaster02` (RUNNING on `mnode097/0`, Increment 1 complete)
- **Notification Route**: Verified Telegram Active (Sidecar Daemon PID 163440)
