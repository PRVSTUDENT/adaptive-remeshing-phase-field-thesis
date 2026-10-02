# Mode-I Proposal Task 5: Frozen Qualification Specification & Evidence Protocol

**Document Identifier**: `docs/supervisor_reports/TASK5_FROZEN_QUALIFICATION_SPECIFICATION.md`  
**Protocol Status**: `FROZEN_BEFORE_PRODUCTION_EVALUATION`  
**Execution Date**: 2026-09-11  
**Author**: Pruthviraja Reddy Vandavagali (Matriculation No. 68865)  
**Supervisors**: Prof. Dipl.-Ing. Björn Kiefer, Ph.D., and Dr.-Ing. Stephan Roth  
**Governing Directive**: *"We need to have understood everything related to the first model before we increase complexity."*  

---

## 1. Protocol Purity & Anti-Tuning Declaration

This protocol establishes the frozen multi-quantity evaluation criteria and evidence ledger for **Proposal Task 5 — Reproduction of reference results with mesh refinement**. 

- **Independent Pre-Declaration**: This specification is frozen while production job `1404454.mmaster02` is running (`R` state).
- **Zero Result Contamination**: No production field results or active ODB outputs from `1404454.mmaster02` have been inspected or used to formulate or tune these criteria.
- **Physical Claims Discipline**: Unverified speculative mechanisms (e.g., localization pinning, distributed damage, integration singularities) are excluded from pre-outcome classifications and remain purely hypotheses to be tested against empirical evidence.

---

## 2. Verified Data Provenance & Baseline Anchor Ledger

| Role in Task 5 Evaluation | Identifier / PBS Job ID | Exact File Path / Source Location | Authoritative Quantities / Verification Role |
| :--- | :--- | :--- | :--- |
| **Fixed Mechanical Reference** | `1398090.mmaster02` | `runs/molnar_single_notch/1398090/PK_MODE1_STANDARD_PFM.odb` | Canonical benchmark anchor ($15{,}192$ elements); $K_{0,\text{ref}} = 137.945520\text{ kN/mm}$, $F_{\max} = 0.757778\text{ kN}$ at $u = 0.005857\text{ mm}$ |
| **Corrected Mechanical Baseline** | `1404306.mmaster02` | `models/pandey_kumar_mode1/83_gate6_adaptive_nominal_1pct_field_qualification/` | Corrected $71{,}320$-element mechanical baseline; $K_0 = 137.820\text{ kN/mm}$, $F_{\max} = 0.7453\text{ kN}$ at $u = 0.005750\text{ mm}$, $u_{\text{term}} \approx 0.006774\text{ mm}$ |
| **Production Field Case** | `1404454.mmaster02` | `models/pandey_kumar_mode1/83_gate6_adaptive_nominal_1pct_field_qualification/PK_M1_NOM1_FIELD_QUAL.odb` | Candidate $71{,}320$-element field qualification solve |
| **Field-Reference Fixture** | Lineage & SHA-256 Validated | `docs/supervisor_reports/GATE6_FIELD_EXTRACTION_PROVENANCE_AUDIT.md` | Verified benchmark field extraction dataset |

---

## 3. Authoritative Benchmark Reference Anchors

### 3.1 Initial Elastic Stiffness
- **Canonical Method**: Ordinary Least Squares (OLS) with unconstrained intercept across $0 < u \le 0.0010\text{ mm}$ ($N = 400$ sampling points, origin $u=0$ excluded).
- **Authoritative Reference Value**:
  $$K_{0,\text{ref}} = 137.945520\text{ kN/mm} \quad (R^2 = 1.00000000)$$

### 3.2 Verified Discrete Force Checkpoints (Fixed Reference `1398090`)
- **$u = 0.004000\text{ mm}$**: $F_{\text{ref}} = 0.538196\text{ kN}$
- **$u = 0.005000\text{ mm}$**: $F_{\text{ref}} = 0.662052\text{ kN}$
- **$u = 0.005750\text{ mm}$**: $F_{\text{ref}} = 0.748219\text{ kN}$
- **$u = 0.005857\text{ mm}$ ($F_{\max}$)**: $F_{\text{ref}} = 0.757778\text{ kN}$
- **$u = 0.006000\text{ mm}$ (Post-Peak)**: $F_{\text{ref}} = 0.000546\text{ kN}$ *(preserved exact value; not simplified to zero)*

### 3.3 Verified Common-Overlap External Work ($0 \le u \le 0.006774069\text{ mm}$)
- **Corrected Mechanical (`1404306`)**: $W_{\text{ext}} = 2.5726\text{ mJ}$
- **Fixed Reference (`1398090`)**: $W_{\text{ext}} = 2.3583\text{ mJ}$
- **External Work Difference**: $+9.09\%$

---

## 4. Phase-Field Bounds & Crack Path Methodology

### 4.1 Phase-Field Bounds Classification
Raw minimum and maximum damage values ($d_{\min}, d_{\max}$) will be extracted and classified without artificial clipping:
- **`BOUND_STRICT_PASS`**: $d \in [-1\times 10^{-5}, 1.00001]$
- **`SMALL_BOUND_OVERSHOOT_OBSERVED`**: $d_{\max} \in (1.00001, 1.005]$ (Note: Validated reference fixture exhibits empirical maximum $d_{\max} \approx 1.00072217$)
- **`BOUNDS_VIOLATION`**: $d_{\min} < -1\times 10^{-5}$ or $d_{\max} > 1.005$

### 4.2 Transverse Crack Ridge & Symmetry Evaluation
- **Ridge Search Corridor**: $x \in [0.50, 1.00]\text{ mm}$, $y \in [0.40, 0.60]\text{ mm}$.
- **Transverse Ridge Definition**: $y_{\text{ridge}}(x) = \arg\max_{y \in [0.4, 0.6]} d(x, y)$.
- **Centerline Deviation**: $\Delta y(x) = y_{\text{ridge}}(x) - 0.500000\text{ mm}$, reporting maximum and mean deviations alongside unthresholded damage profiles along $y = 0.500\text{ mm}$.

---

## 5. Master Comparison Table Schema

The final Task-5 evaluation will compile the complete multi-quantity evidence set across the following parameters:

| Evaluation Quantity | Extraction Domain / Method | Fixed Reference (`1398090`) | Corrected Baseline (`1404306`) | Production Field (`1404454`) | Relative Difference / Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Canonical $K_0$** | OLS w/ intercept, $0 < u \le 0.001\text{ mm}$ | $137.945520\text{ kN/mm}$ | $137.820\text{ kN/mm}$ | *To be extracted* | $\Delta K_0 / K_{0,\text{ref}}$ |
| **Peak Force $F_{\max}$** | Maximum Reaction Force ($F_2$) | $0.757778\text{ kN}$ | $0.7453\text{ kN}$ | *To be extracted* | $\Delta F_{\max} / F_{\max,\text{ref}}$ |
| **Peak Disp. $u(F_{\max})$** | Prescribed $U_2$ at $F_{\max}$ | $0.005857\text{ mm}$ | $0.005750\text{ mm}$ | *To be extracted* | Shift in peak displacement |
| **Checkpoint $u=0.0040\text{ mm}$** | Discrete frame reaction force | $0.538196\text{ kN}$ | Extracted | *To be extracted* | Pre-peak force parity |
| **Checkpoint $u=0.0050\text{ mm}$** | Discrete frame reaction force | $0.662052\text{ kN}$ | Extracted | *To be extracted* | Non-linear onset parity |
| **Checkpoint $u=0.00575\text{ mm}$**| Discrete frame reaction force | $0.748219\text{ kN}$ | $0.7453\text{ kN}$ | *To be extracted* | Pre-peak inflection parity |
| **Checkpoint $u=0.0060\text{ mm}$**| Discrete frame reaction force | $0.000546\text{ kN}$ | Extracted | *To be extracted* | Post-peak load drop parity |
| **Deepest State $u_{\text{common}}$** | Last common converged $U_2$ | $0.006774\text{ mm}$ | $0.006774\text{ mm}$ | *To be extracted* | Overlap interval limit |
| **External Work $W_{\text{ext}}$** | $\int F\,du$ over $[0, u_{\text{common}}]$ | $2.3583\text{ mJ}$ | $2.5726\text{ mJ}$ ($+9.09\%$) | *To be extracted* | Integral energy balance |
| **Field Bounds ($d_{\min}, d_{\max}$)**| Global extrema over mesh | $[-1\text{e-}5, 1.000722]$ | — | *To be extracted* | Bounds status |
| **Crack-Tip $d(0.50, 0.50)$** | Centroid value at initial tip | Extracted | — | *To be extracted* | Evolution across checkpoints |
| **Centerline Profile** | Raw $d(x, 0.50)$ on $[0.50, 1.00]$ | Extracted | — | *To be extracted* | Ligament damage distribution |
| **Path Deviation** | $\max \|y_{\text{ridge}} - 0.50\|$ | $0.000000\text{ mm}$ | — | *To be extracted* | Horizontal symmetry |
| **Achieved $u_{\text{term}}$** | Terminal prescribed displacement | $0.010000\text{ mm}$ | $0.006774\text{ mm}$ | *To be extracted* | Propagation progression |
| **Solver Performance** | Newton iterations / cutbacks | Baseline ($0$ cutbacks)| Recorded | *To be extracted* | Iteration efficiency |
| **Mesh Element Count** | Total finite elements | $15{,}192$ | $71{,}320$ | $71{,}320$ | Discretization count |
| **Resource Cost** | Walltime, CPU time, RAM | Baseline | Recorded | *To be extracted* | Computational efficiency |

---

## 6. Pre-Declared Decision Criteria

The final scientific classification for Proposal Task 5 will be assigned from the complete evidence set without arbitrary isolated thresholding:

1. **`TASK5_QUALIFIED`**:
   Assigned only if the complete mechanical and field response of the refined adaptive model is demonstrated to be sufficiently equivalent to the reference solution across the full loading history (elastic, peak, softening, and crack path) and any computational efficiency claims are supported by measured resource metrics.

2. **`TASK5_DEFENSIBLE_NEGATIVE_QUALIFICATION`**:
   Assigned if the refined model accurately reproduces pre-peak behavior ($K_0 \approx 137.82\text{ kN/mm}$) but exhibits a documented failure to reproduce reference post-peak softening or complete fracture propagation, with the empirical discrepancy characterized directly from solver and field data without inventing an unverified root cause.

3. **`TASK5_REMAINS_UNRESOLVED`**:
   Assigned if numerical extraction errors, incomplete output fields, or inconsistencies between the mechanical and field evaluations prevent a conclusive determination.
