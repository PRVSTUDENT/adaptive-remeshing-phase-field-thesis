# Gate-6B Stage 14C/14D Terminal Evaluator & Energy-Mapping Qualification Audit Report

**Protocol Version:** 2  
**Task ID:** `F1186-GATE6B-STAGE14D-EVALUATOR-REFERENCE-RECONCILIATION-20261003`  
**Date:** 2026-10-03  
**Author:** Gemini Antigravity  
**Status:** `EVALUATOR_AND_ENERGY_QUALIFICATION_RECONCILED_QUALIFIED`  
**Governing Directive:** *"We need to have understood everything related to the first model before we increase complexity."*  

---

## 1. Executive Summary & Audit Dashboard

This audit report records the independent verification, authoritative energy-baseline reconciliation, and qualification of the terminal scientific evaluator [`models/pandey_kumar_mode1/25_stage14_adaptive_candidate_14k/evaluate_mode1_stage14_adaptive_14k.py`](file:///D:/Master%20thesis/Adaptive%20remeshing/models/pandey_kumar_mode1/25_stage14_adaptive_candidate_14k/evaluate_mode1_stage14_adaptive_14k.py) for the authoritative Gate-6B Stage-14 Adaptive Candidate Model (14,483 underlying finite elements, 43,449 3-layer finite elements, 14,456 nodes) currently solving under PBS Job `1409947.mmaster02` (`PK_M1_ADAPT_14K_FRACTURE`) on cluster node `mnode097`.

### Core Audit Findings & Reconciliations
1. **Terminology Compliance (`PASS`):**
   - The prohibited phrase "physical element" is completely eliminated from all reporting, metadata, and test descriptions.
   - All references strictly utilize standard finite element terminology: **"underlying finite elements"** ($N_{\text{base}} = 14,483$) and **"layered finite elements"** ($N_{\text{layered}} = 43,449$).
2. **Authoritative Reference Energy Baseline Provenance Reconciled (`PASS`):**
   - Every reference energy value in the terminal comparison template is rigorously reconciled against the governed qualified Mode-I reference baseline (Job `1409734.mmaster02`, `PK_MODE1_REF15K_ENERGY`, status `CORRECTED_S1_ENERGY_QUALIFIED`).
   - Unverified provisional numbers from prior drafts have been replaced with the verified values from `models/pandey_kumar_mode1/16_energy_qualification_reference_15k/uel_energy_balance.csv` (SHA-256: `9991f7f1ec5645b7e422fc12e1b2e367dd840c3b24a49b22dcf782c0d13f3875`).
3. **Elimination of Invented Numerical Thresholds (`PASS`):**
   - All arbitrary numerical pass/fail thresholds ($|\Delta K_0| \le 0.50\%$, $|\Delta F_{\max}| \le 2\%$, $E_{\text{elas}} < 0.10\,\text{mJ}$, $\varepsilon_{\text{book}} < 3\%$) are removed from gate evaluation.
   - Metrics are reported as direct deltas and evaluated with descriptive classifications: `STABLE`, `MESH_SENSITIVE`, `TEMPORALLY_SENSITIVE`, or `NOT_YET_QUALIFIED`.
4. **Layer Naming & Implementation Declaration Re-Audited (`PASS`):**
   - Established exact element types and DOF allocations from `PK_MODE1_STAGE14_ADAPT_14K_FRACTURE.inp` and `f42_mixed_uel.for`:
     - **Layer 1 (Phase-Field DOFs):** `U1` (quads, $1 \dots 14,082$), `U3` (tris, $14,083 \dots 14,483$), Active DOF 3 ($d$).
     - **Layer 2 (Displacement DOFs):** `U2` (quads, $14,484 \dots 28,565$), `U4` (tris, $28,566 \dots 28,966$), Active DOFs 1, 2 ($u_x, u_y$).
     - **Layer 3 (Companion/Facsimile UMAT):** `CPE4` (quads, $28,967 \dots 43,048$), `CPE3` (tris, $43,049 \dots 43,449$), `ELSET=UMATELEM`.
5. **Strengthened Integration-Point Deduplication & Equality Proof (`PASS`):**
   - The evaluator groups explicitly by `(instanceName, elementLabel)`.
   - Scopes directly to `UMATELEM` element set to eliminate cross-layer collisions.
   - Verifies that all Gauss-point copies within an element for both SDV17 ($E_{\text{frac}}$) and SDV18 ($E_{\text{elas}}$) are numerically equal within machine precision.
   - Fails loudly with `ValueError` upon encountering inconsistent IP energy copies.
6. **Synthetic Regression Unit Test Suite (`100% PASS`):**
   - 11/11 tests pass in [`tests/unit/test_evaluate_mode1_stage14_synthetic_disambiguation.py`](file:///D:/Master%20thesis/Adaptive%20remeshing/tests/unit/test_evaluate_mode1_stage14_synthetic_disambiguation.py). All 71 Mode-I unit tests pass 100%.

---

## 2. Authoritative Fixed-Reference Energy Baseline Provenance

The table below records the complete, unambiguous provenance of every reference quantity against which the Stage-14 adaptive candidate is evaluated:

| Dimension / Metric | Value | Units | Provenance Source & Details |
| :--- | :---: | :---: | :--- |
| **Mechanical Reference Job** | `1398090.mmaster02` | — | Uninstrumented 15,192-element mechanical anchor (`PK_MODE1_STANDARD_PFM`). |
| **Energy Qualified Job** | `1409734.mmaster02` | — | Exact instrumented twin of Job 1398090 on identical 15,192-element discretization (`CORRECTED_S1_ENERGY_QUALIFIED`). |
| **Input Deck SHA-256** | `ec560a4c265730647b43dab125d166ebc57cac285d574d38222a498a967535d9` | — | `models/pandey_kumar_mode1/16_energy_qualification_reference_15k/PK_MODE1_REF15K_ENERGY.inp` |
| **Fortran Subroutine SHA-256** | `ce8d5edcd2911dcb018bb15275271f874e7ea62b8fb48cf4a8297469a83acdd6` | — | `models/pandey_kumar_mode1/16_energy_qualification_reference_15k/f42_mixed_uel.for` |
| **Energy Data CSV & SHA-256** | `9991f7f1ec5645b7e422fc12e1b2e367dd840c3b24a49b22dcf782c0d13f3875` | — | `models/pandey_kumar_mode1/16_energy_qualification_reference_15k/uel_energy_balance.csv` |
| **Qualification Report SHA-256** | `1aa535f8efa94598ebf79465459dfdc59ee81c6711fb0128abab69d30237af21` | — | `models/pandey_kumar_mode1/16_energy_qualification_reference_15k/S1_1409734_SCIENTIFIC_QUALIFICATION_REPORT.json` |
| **Extraction Script SHA-256** | `9270c0f2dc77f84799e2b6435e2d5bcb4ff693204a08ef76bd815d6414332e8a` | — | `scripts/validation/extract_authoritative_mode1_energy_complete.py` |
| **Initial Stiffness $K_0$** | **137.945520** | $\text{kN/mm}$ | OLS regression on initial elastic range ($N=400$, $0.5\Delta u < u \le 0.0010 + 0.5\Delta u$, $R^2 = 0.99999960$). |
| **Peak Reaction Force $F_{\max}$** | **0.757778** | $\text{kN}$ | Tensile reaction force ($F = -RF_2$) at $u(F_{\max}) = 0.005857\,\text{mm}$. |
| **Final Reaction Force $F_{\text{final}}$** | **0.000232** | $\text{kN}$ | Residual load at $u = 0.010000\,\text{mm}$ ($99.97\%$ load drop). |
| **Terminal External Work $W_{\text{ext}}$** | **2.359329** | $\text{mJ}$ | Trapezoidal integration $W_{\text{ext}} = \int_0^{0.010} F \, du$ ($0.002359329\,\text{kN}\cdot\text{mm}$). |
| **Terminal Fracture Energy $E_{\text{frac}}$** | **2.340220** | $\text{mJ}$ | Implemented phase-field crack-surface functional at $u = 0.010\,\text{mm}$ ($0.002340220\,\text{kN}\cdot\text{mm}$). |
| **Terminal Elastic Strain Energy $E_{\text{elas}}$** | **0.001161** | $\text{mJ}$ | Degraded elastic strain energy in fully broken state at $u = 0.010\,\text{mm}$ ($1.1608108\times 10^{-6}\,\text{kN}\cdot\text{mm}$). |
| **Total Model Energy $E_{\text{model}}$** | **2.341381** | $\text{mJ}$ | $E_{\text{elas}} + E_{\text{frac}} = 0.0023413808\,\text{kN}\cdot\text{mm}$. |
| **Bookkeeping Difference $\Delta_{\text{book}}$** | **-0.017949** | $\text{mJ}$ | $(E_{\text{elas}} + E_{\text{frac}}) - W_{\text{ext}} = -1.794856\times 10^{-5}\,\text{kN}\cdot\text{mm}$. |
| **Normalized Bookkeeping Error $\varepsilon_{\text{book}}$** | **0.7607%** | $\%$ | $|\Delta_{\text{book}}| / W_{\text{ext}} \times 100\%$ (descriptive diagnostic). |

---

## 3. Implementation Layer Architecture & Element Mapping

The mixed quadrilateral-triangular formulation decouples the multi-field problem into three co-located numerical layers sharing identical physical node coordinates:

```
+-----------------------------------------------------------------------------------------------+
| LAYER 1: Phase-Field UEL (JTYPE 1 Quad [U1], JTYPE 3 Tri [U3])                                |
| - Elements: 1 to 14,483 (14,082 quads in PHASE_QUADS, 401 tris in PHASE_TRIS)                 |
| - Active DOF: 3 (Phase field d)                                                               |
| - Calculates: Phase field evolution, grad(d), E_frac = \int G_c [d^2/(2 l_0) + (l_0/2)|grad d|^2] d\Omega |
| - Stores in Common Block: SV_PHASE_TRIAL(e), SV_E_FRAC(e), SV_PSI_F(e)                        |
+-----------------------------------------------------------------------------------------------+
                                            | (Shared Common Block CB_STATE_TRANS)
                                            v
+-----------------------------------------------------------------------------------------------+
| LAYER 2: Mechanical UEL (JTYPE 2 Quad [U2], JTYPE 4 Tri [U4])                                 |
| - Elements: 14,484 to 28,966 (14,082 quads in MECH_QUADS, 401 tris in MECH_TRIS)              |
| - Active DOFs: 1, 2 (Displacements u_x, u_y)                                                  |
| - Reads: Phase field d from SV_PHASE_TRIAL(e) -> Degradation g(d) = (1-d)^2 + k               |
| - Calculates: Degraded stresses \sigma, History variable H = max(H, \psi_0^+),                |
|               Elastic strain energy E_elas = \int (1/2 \sigma : \epsilon) d\Omega             |
| - Stores in Common Block: SV_H_TRIAL(e, pt), SV_E_ELAS(e), SV_PSI_E(e)                        |
+-----------------------------------------------------------------------------------------------+
                                            | (Shared Common Block CB_STATE_TRANS)
                                            v
+-----------------------------------------------------------------------------------------------+
| LAYER 3: Companion / Facsimile UMAT (CPE4 Quad, CPE3 Tri)                                     |
| - Elements: 28,967 to 43,449 (14,082 quads in UMAT_QUADS, 401 tris in UMAT_TRIS)              |
| - Element Set: UMATELEM                                                                       |
| - Active DOFs: 1, 2 (Passive stiffness E_passive = 10^-11 GPa, benign to solver)              |
| - Populates STATEV for ODB Visualization & Diagnostic Extraction:                             |
|     * STATEV(1)  = Phase-field d                                                              |
|     * STATEV(2)  = History variable H                                                         |
|     * STATEV(14) = Phase-field d (mirrored)                                                   |
|     * STATEV(15) = Degradation function g(d) = (1-d)^2 + k                                    |
|     * STATEV(16) = History variable H (mirrored)                                               |
|     * STATEV(17) = Integrated element fracture energy E_frac (kN*mm = J)                      |
|     * STATEV(18) = Integrated element elastic strain energy E_elas (kN*mm = J)                |
|     * STATEV(19) = Fracture energy density \bar{\psi}_f (kN/mm = J/mm^2)                      |
|     * STATEV(20) = Elastic strain energy density \bar{\psi}_e (kN/mm = J/mm^2)                |
+-----------------------------------------------------------------------------------------------+
```

### Underlying Finite-Element Index Mapping
For any companion element $e_{\text{UMAT}} \in [28,967, 43,449]$:
$$e_{\text{base}} = e_{\text{UMAT}} - 2 \cdot N_{\text{base}} = e_{\text{UMAT}} - 28,966$$
This mapping guarantees a strictly bijective 1-to-1 correspondence between underlying finite elements and companion diagnostic records.

---

## 4. Integration-Point Deduplication & Equality Verification Algorithm

### The Multi-IP Problem
In Abaqus:
- Quadrilateral `CPE4` elements have 4 Gauss points ($2 \times 2$ rule).
- Triangular `CPE3` elements have 1 Gauss point (centroid).
Because `UMAT` is called at every integration point `NPT`, it writes the full element-integrated energies $E_{\text{frac}, e}$ and $E_{\text{elas}, e}$ to `STATEV(17)` and `STATEV(18)` for all `NPT = 1..4`. Naive un-deduplicated summation yields:
$$E_{\text{naive}} = 4 \sum_{e \in \text{CPE4}} E_e + \sum_{e \in \text{CPE3}} E_e \approx 4 \times E_{\text{true}}$$

### Strict Extraction & Verification Implementation
[`evaluate_mode1_stage14_adaptive_14k.py`](file:///D:/Master%20thesis/Adaptive%20remeshing/models/pandey_kumar_mode1/25_stage14_adaptive_candidate_14k/evaluate_mode1_stage14_adaptive_14k.py) implements `extract_element_energies_strict`:
1. Scopes query to `region_set = odb.rootAssembly.elementSets['UMATELEM']`.
2. Groups all FieldValues by key `(instanceName, elementLabel)`.
3. Verifies that for every element, all integration points satisfy:
   $$|E_{\text{IP}, k} - E_{\text{IP}, 1}| \le \max(\text{atol}, \text{rtol} \cdot |E_{\text{IP}, 1}|)$$
   If any integration point deviates, execution immediately halts with `ValueError`.
4. Takes exactly one verified representative value per element.
5. Accurately counts quad elements (IP count $>1$) and tri elements (IP count $=1$).

---

## 5. Rebuilt Terminal Comparison Table Template

This table anchors all extraction metrics against the reconciled qualified reference baseline (Job `1409734.mmaster02` / Job `1398090.mmaster02`, 15,192 elements) and will be completed upon terminal closeout of Job `1409947.mmaster02`:

| Metric / Dimension | Fixed Reference Anchor (Job 1409734 / 1398090) | Published Target (Pandey & Kumar 2025) | Stage 14 Adaptive Candidate (Job 1409947) | Parity Delta vs Ref ($\Delta_{\text{rel}}$) | Descriptive Classification |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Underlying Finite Elements ($N_{\text{base}}$)** | 15,192 | 13,941 | 14,483 | $-4.67\%$ vs Ref ($+3.89\%$ vs Pub) | `QUALIFIED_CANDIDATE` |
| **Layered FE Elements** | 45,576 | — | 43,449 | $-4.67\%$ | `3_LAYER_COMPLIANT` |
| **Mesh Nodes** | 15,521 | — | 14,456 | $-6.86\%$ | `TOPOLOGY_VERIFIED` |
| **Initial Stiffness $K_0$ ($\text{kN/mm}$)** | **137.945520** | $\sim 137.95$ | *[Computing]* | *[Pending]* | *[Pending]* |
| **Linear Regression $R^2$ ($N=400$)** | **0.99999960** | — | *[Computing]* | *[Pending]* | *[Pending]* |
| **Peak Reaction Force $F_{\max}$ ($\text{kN}$)** | **0.757778** | 0.758 | *[Computing]* | *[Pending]* | *[Pending]* |
| **Peak Displacement $u_{\text{peak}}$ ($\text{mm}$)** | **0.005857** | 0.005860 | *[Computing]* | *[Pending]* | *[Pending]* |
| **Final Reaction Force $F_{\text{final}}$ ($\text{kN}$)** | **0.000232** | — | *[Computing]* | *[Pending]* | *[Pending]* |
| **Terminal External Work $W_{\text{ext}}$ ($\text{mJ}$)** | **2.359329** | — | *[Computing]* | *[Pending]* | *[Pending]* |
| **Terminal Fracture Energy $E_{\text{frac}}$ ($\text{mJ}$)** | **2.340220** | — | *[Computing]* | *[Pending]* | *[Pending]* |
| **Terminal Elastic Energy $E_{\text{elas}}$ ($\text{mJ}$)** | **0.001161** | — | *[Computing]* | *[Pending]* | *[Pending]* |
| **Bookkeeping Residual $\Delta_{\text{book}}$ ($\text{mJ}$)** | **-0.017949** | — | *[Computing]* | *[Pending]* | Descriptive diagnostic |
| **Normalized Residual $\varepsilon_{\text{book}}$ ($\%$)** | **0.7607%** | — | *[Computing]* | *[Pending]* | Descriptive diagnostic |
| **Solver Cutbacks & Iterations** | 0 cutbacks, 1 iter/inc | — | *[Computing]* | *[Pending]* | *[Pending]* |
| **Solver Exit Status** | Exit 0 | — | *[Running]* | — | *[Running]* |

---

## 6. Unit Test & Disambiguation Verification Suite

The dedicated unit test suite [`tests/unit/test_evaluate_mode1_stage14_synthetic_disambiguation.py`](file:///D:/Master%20thesis/Adaptive%20remeshing/tests/unit/test_evaluate_mode1_stage14_synthetic_disambiguation.py) was executed to verify all mathematical and software components:

```
test_comparison_vs_reference_interpolation:          Verify discrete RMS and continuous L2 norm against reference ... PASS
test_descriptive_energy_bookkeeping_residual:         Verify calculation of Delta_book and normalized error .......... PASS
test_extract_element_energies_strict_mixed_quad_tri:  Verify strict deduplication on mixed CPE4/CPE3 mesh ............. PASS
test_float_helper:                                   Verify _is_float string parsing ................................ PASS
test_force_sign_and_initial_stiffness_regression:    Verify tensile force F = -RF2 and K0 OLS linear regression ...... PASS
test_layer_namespace_boundaries_and_metadata:        Verify layer label partitioning for 14,483 elements ............ PASS
test_layer_set_disambiguation_scoping:               Prove scoping to UMATELEM prevents cross-layer collision ........ PASS
test_multi_instance_duplicate_label_disambiguation:  Prove (instanceName, elementLabel) resolves duplicate IDs ...... PASS
test_reconciled_canonical_reference_provenance:      Verify provenance and values of reference energy baseline ...... PASS
test_strict_extraction_fails_loudly_on_inconsistent_ip_values: Prove loud ValueError on inconsistent IP energies ..... PASS
test_trapezoidal_work_and_monotonicity_guard:        Verify work integration and rejection of non-monotonic steps .. PASS

Total: 11/11 unit tests passed (100% PASS, Execution time: 0.009s)
```

---

## 7. Conclusions & Governance Status

1. **Evaluator Requalification Status:** The Stage-14 Mode-I Terminal Evaluator [`evaluate_mode1_stage14_adaptive_14k.py`](file:///D:/Master%20thesis/Adaptive%20remeshing/models/pandey_kumar_mode1/25_stage14_adaptive_candidate_14k/evaluate_mode1_stage14_adaptive_14k.py) is strictly qualified, fully reconciled against the governed reference energy baseline (Job `1409734.mmaster02`), and fortified with within-element IP equality verification and multi-instance scoping.
2. **Cluster Solver Status:** Job `1409947.mmaster02` (`PK_M1_ADAPT_14K_FRACTURE`) is progressing smoothly on `mnode097` (Step 1 >65% complete, 1 iteration/increment, 0 cutbacks).
3. **Next Step:** Maintain active monitoring of Job `1409947.mmaster02`. Upon solver completion, execute the qualified evaluator, extract the final force-displacement and energy trajectories, populate the comparison table, and prepare the final Gate-6B synthesis.
