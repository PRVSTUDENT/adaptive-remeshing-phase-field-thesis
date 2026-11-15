# Task F1775: Method A Adapted Coupled Phase-Field Fracture Qualification & Production Preflight Report

## Executive Summary

- **Task Identifier**: `F1775-COUPLED-PHASE-FIELD-FRACTURE-QUALIFICATION-AND-PREFLIGHT`
- **Master Objective**: `# F1737 — AUTONOMOUS FIVE-BENCHMARK METHOD A RESEARCH COMPLETION LOOP`
- **Strategic Milestone**: Strategic Transition from Criterion A (Unified Method A Adaptive Remeshing Framework Full-Suite Regression, successfully completed across all 4 non-duplicated core benchmarks in Task F1774) to **Criterion B (Coupled Phase-Field Fracture Validation on Adapted Discretizations)**.
- **Assigned Agent**: `gemini-antigravity`
- **Starting Source Commit**: `8b86ddc3b`
- **Research Freeze Deadline**: 13 December 2026; **Final MSc Submission**: 13 January 2027.
- **Governance & PBS Budget**: Strictly **zero new PBS submissions consumed** under Task F1775 (`max_new_pbs_submissions = 0`, `submissions_consumed = 0`); cumulative historical submissions permanently accounted as **33**.
- **Bitwise Frozen Production UEL**: `models/pandey_kumar_mode1/f42_mixed_uel.for` (SHA-256: `CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6`).
- **Core Production Decks Evaluated & Verified**:
  - **Case 1 (Mode-I Single-Edge Notched Plate, Section 4.1)**: `models/pandey_kumar_mode1/239_f1772_case1_remesh/PK_F1728_CASE_1_PROD.inp` (SHA-256: `976EF13CEAD9F8C541D93510BD48483F0ADCA297C95EEC3F8D67FE7429A1CD7E`). Physical mesh: 20,232 elements (97.17% quads); 60,696 layered elements.
  - **Case 5 (Seven-Hole Plate Tensile Failure, Section 4.6)**: `models/pandey_kumar_mode1/240_f1774_suite_regression/case5/PK_F1728_CASE_5_PROD.inp` (SHA-256: `174C2ABB82E1DB37A5ED57AA2E36A4B46005098A5264DDCF1164D8232A8CB19E`). Physical mesh: 15,330 elements (97.72% quads); 45,990 layered elements.
  - **Case 2 (Off-Axis Hole, Section 4.4)**: `models/pandey_kumar_mode1/240_f1774_suite_regression/case2/PK_F1728_CASE_2_PROD.inp` (SHA-256: `CFCFE01699552F8D4D66172B6D6EC6E3FC0213A93C20FECF598E6464E720FB36`). Physical mesh: 23,965 elements (97.23% quads); 71,895 layered elements.
  - **Case 3 (Notched Plate with Pins, Section 4.3)**: `models/pandey_kumar_mode1/240_f1774_suite_regression/case3/PK_F1728_CASE_3_PROD.inp` (SHA-256: `B356E39D051C9026B1F484244FA630A47544585086AF64423D541A02E2DE9E3B`). Physical mesh: 28,933 elements (96.91% quads); 86,799 layered elements.

---

## 1. Scientific Context & Master Objective F1737 Alignment

Master Objective F1737 requires establishing a scientifically defensible adaptive-remeshing and coupled phase-field fracture framework across the benchmark geometries:

$$\text{F1737 Acceptance} = \underbrace{\text{Criterion A (Adaptive Discretization Quality)}}_{\text{QUALIFIED in F1774}} \quad \land \quad \underbrace{\text{Criterion B (Coupled Fracture Physics Validation)}}_{\text{ACTIVE in F1775}}.$$

### 1.1 Resolution of Criterion A (Task F1774 Closeout)
In Task F1774, all four non-duplicated benchmarks in the reconciled regression matrix were adapted using one frozen reusable Python framework (`scripts/remeshing/reusable_2d_adaptive_framework.py`, blob `8D71F38F...`) and frozen UEL (`f42_mixed_uel.for`, `CE8D5EDC...`):
- **Case 1**: 20,232 physical elements, 97.17% quads, 100.0% ligament area compliant ($h \le \ell_0$), resolving the entire $0.5\text{ mm}$ advancing crack path.
- **Case 2**: 23,965 physical elements, 97.23% quads, $+1.47\%$ parity vs published benchmark (23,618 elements).
- **Case 3**: 28,933 physical elements, 96.91% quads, resolving both primary (notch-to-hole) and secondary (hole-to-boundary) corridors via 2-state cumulative adaptation.
- **Case 5**: 15,330 physical elements, 97.72% quads, $-2.44\%$ parity vs published benchmark (15,714 elements), with 100% selective localization across the seven-hole cluster ($y \in [0.2, 0.8]\text{ mm}$).

### 1.2 Motivation for Criterion B Forward Coupled Fracture Execution
While the spatial discretizations have been verified and all four production input decks have passed real Abaqus datacheck Exit 0 under Classic Intel Fortran 2021.13 and Abaqus 2023 on compute node `mnode099`, the physical predictive validation of coupled phase-field fracture mechanics on these adapted meshes remains to be demonstrated:
1. **Case 1**: The earlier fracture solve in Task F1739 (Job 1423321.mmaster02) completed Exit 0 with 99.96% load drop, but was performed on a hybrid geometric corridor mesh and omitted the `SDV` request in the field output card. Executing coupled fracture on the new 20,232-element advancing adapted mesh with `FREQUENCY=1` and `SDV` requested on Layer 3 companion elements will provide the definitive 2D damage field evolution ($d(x,y)$) alongside the macroscopic load-displacement response.
2. **Case 5**: The seven-hole square plate (Section 4.6) has **never had coupled phase-field fracture simulation performed on its adapted mesh** in this project. Demonstrating multi-crack nucleation and propagation through the cluster of 7 holes on the 15,330-element adapted mesh represents a foundational thesis achievement, proving the general applicability of Method A to unnotched specimens with complex stress concentrations.

---

## 2. Production Input Deck Technical Audit

Both primary production input decks were built by `ProductionDeckBuilder` in `reusable_2d_adaptive_framework.py`, downloaded to local repository storage, and audited against strict finite-element and solver standards:

### 2.1 Case 1 Production Deck (`PK_F1728_CASE_1_PROD.inp`)
- **Location**: `models/pandey_kumar_mode1/239_f1772_case1_remesh/PK_F1728_CASE_1_PROD.inp`
- **File Size**: 2,679,030 bytes; **SHA-256**: `976EF13CEAD9F8C541D93510BD48483F0ADCA297C95EEC3F8D67FE7429A1CD7E`
- **Nodal Discretization**: 20,498 nodes (20,497 physical nodes + 1 reference point `N_RP` at node 999999).
- **Element Discretization**:
  - Layer 1 (Phase-Field UEL, DOF 3): 19,660 quads (element type `U1`) + 572 triangles (element type `U2`).
  - Layer 2 (Mechanical UEL, DOFs 1–2): 19,660 quads (element type `U3`) + 572 triangles (element type `U4`).
  - Layer 3 (Companion Visualizer CPE4/CPE3 with UMAT dummy material): 19,660 CPE4 + 572 CPE3.
  - Total layered elements: **60,696 elements**.
- **Line Wrapping**: 100% of `*NSET` cards strictly wrapped at $\le 16$ entries per line, eliminating Abaqus parser buffer truncation risk.
- **Displacement Schedule**:
  - Step 1 (Pre-critical linear elastic): $u_y = 0.0050\text{ mm}$ via `*STATIC` with initial $\Delta t = 0.02$, $\Delta t_{\min} = 1.0 \times 10^{-7}$, $\Delta t_{\max} = 0.02$.
  - Step 2 (Fracture propagation): $u_y = 0.0100\text{ mm}$ via `*STATIC` with initial $\Delta t = 0.002$, $\Delta t_{\min} = 1.0 \times 10^{-8}$, $\Delta t_{\max} = 0.002$.
- **Field Output Requests**:
  ```abaqus
  *OUTPUT, FIELD, FREQUENCY=1
  *NODE OUTPUT, NSET=N_RP
  U, RF
  *ELEMENT OUTPUT, ELSET=umatelem
  MISESERI, MISESAVG, S, E, SDV
  *NODE PRINT, FREQ=1, NSET=N_RP
  U2, RF2
  ```
  Guarantees complete frame-by-frame capture of damage $d$ (`SDV1`), history $H$ (`SDV2`), and recovered error indicators.

### 2.2 Case 5 Production Deck (`PK_F1728_CASE_5_PROD.inp`)
- **Location**: `models/pandey_kumar_mode1/240_f1774_suite_regression/case5/PK_F1728_CASE_5_PROD.inp`
- **File Size**: 2,013,124 bytes; **SHA-256**: `174C2ABB82E1DB37A5ED57AA2E36A4B46005098A5264DDCF1164D8232A8CB19E`
- **Nodal Discretization**: 15,649 nodes (15,648 physical nodes + 1 reference point `N_RP` at node 999999).
- **Element Discretization**:
  - Layer 1 (Phase-Field UEL, DOF 3): 14,981 quads (`U1`) + 349 triangles (`U2`).
  - Layer 2 (Mechanical UEL, DOFs 1–2): 14,981 quads (`U3`) + 349 triangles (`U4`).
  - Layer 3 (Companion Visualizer CPE4/CPE3 with UMAT dummy material): 14,981 CPE4 + 349 CPE3.
  - Total layered elements: **45,990 elements**.
- **Line Wrapping**: 100% of `*NSET` cards strictly wrapped at $\le 16$ entries per line.
- **Displacement Schedule**:
  - Step 1 (Pre-critical linear elastic): $u_y = 0.0050\text{ mm}$ with initial $\Delta t = 0.02$.
  - Step 2 (Fracture propagation): $u_y = 0.0100\text{ mm}$ with initial $\Delta t = 0.002$, $\Delta t_{\min} = 1.0 \times 10^{-8}$.
- **Field Output Requests**: Identical complete coverage with `FREQUENCY=1` for `U`, `RF` on `N_RP` and `MISESERI, MISESAVG, S, E, SDV` on `ELSET=umatelem`.

---

## 3. Predeclared Acceptance Gate Matrix (G1–G8) for Forward Coupled Fracture

To ensure rigorous scientific validation without post-hoc threshold adjustments, the following quantitative acceptance criteria are declared prior to forward solver execution:

| Gate ID | Criterion Dimension | Predeclared Acceptance Threshold | Literature / Reference Basis | Evaluation Method |
| :--- | :--- | :--- | :--- | :--- |
| **G1** | Peak Reaction Force | $|F_{\max} - F_{\max}^{\text{ref}}| / F_{\max}^{\text{ref}} \le 5.0\%$ | Case 1: $F_{\max} \approx 0.758\text{ kN}$ (Job 1398090: $0.7578\text{ kN}$); Case 5: $F_{\max} \approx 0.65\text{ kN}$ | Reaction force extracted from `N_RP` RF2 history curve |
| **G2** | Post-Peak Softening Drop | $\Delta F / F_{\max} = (F_{\max} - F_{\text{final}}) / F_{\max} \ge 50.0\%$ (targeting complete severance $\ge 90\%$) | Pandey & Kumar (2025) Figs. 7(a) & 27(a) | Terminal reaction force vs peak reaction force |
| **G3** | Phase-Field Damage Bounds | $0.0 \le d \le 1.0$ (documenting known unconstrained Helmholtz smoothing oscillation without relaxation) | Variational phase-field formulation; negative $d$ within $[-0.02, 0.0]$ classified as boundary smoothing artifact | Pointwise inspection of Layer 3 SDV1 across all frames |
| **G4** | History Monotonicity | $\Delta H \ge 0.0\text{ MPa}$ across 100% of integration points | Irreversibility constraint enforced via local maximum history operator $H = \max(\psi_0^+, H_{t-\Delta t})$ | Pointwise inspection of Layer 3 SDV2 across all increments |
| **G5** | Crack Trajectory Fidelity | Complete horizontal ligament severance for Case 1 ($y = 0.5\text{ mm}$); Inter-hole crack bridging for Case 5 | Case 1: Fig. 4(a); Case 5: Fig. 26(b) | 2D contour plot of Layer 3 SDV1 ($d$) on deformed mesh |
| **G6** | Solution Convergence | Solver completion Exit 0 or physical termination without cutback exhaustion ($\Delta t \ge 1.0 \times 10^{-8}\text{ s}$) | Abaqus nonlinear Newton-Raphson solver telemetry | Abaqus `.sta`, `.msg`, and scheduler exit code |
| **G7** | Complete Field Capture | 100% of increments contain $d$, $H$, stress, and reaction force | Resolution of F1739 missing SDV field output limitation | Frame inspection of ODB `FieldOutputs` |
| **G8** | Thermodynamic Energy Dissipation | Monotonic increase of fracture dissipation energy $\Delta E_{\text{frac}} \ge 0$ | Griffith surface energy $E_{\text{frac}} = \int_{\Omega} G_c \left[ \frac{d^2}{2\ell_0} + \frac{\ell_0}{2} |\nabla d|^2 \right] d\Omega$ | UEL energy output audit (`uel_energy_balance.csv`) |

---

## 4. Execution Wrappers & Dual-Channel Notification Integration

Dedicated cluster PBS execution wrappers have been formulated with strict safety and monitoring directives:
1. **Directory Lock Guard**: Non-recursive atomic `mkdir` guard with trap `rmdir "${LOCK_DIR}" 2>/dev/null || true` (preventing directory-level race conditions without dangerous recursive deletions).
2. **Preflight File Integrity**: Fail-closed SHA-256 checks on input decks, config JSONs, and the bitwise frozen UEL before invoking Abaqus.
3. **Dual-Channel Notifications**:
   - Directives: `#PBS -m abe` and `#PBS -M pr21vyci@mailserver.tu-freiberg.de`.
   - Shell Trap: Sourcing `job_notifications.sh`, issuing `notify_submitted` at launch, `notify_start` on compute node initialization, and terminal exit traps for `COMPLETED`, `FAILED`, or `TERMINATED`.
4. **Resource Bounds**: 1 CPU, 16 GB RAM, 8 hours walltime per job on queue `normal_imfdfkmq`.

---

## 5. Governance, Standing Submission Accounting & Next Steps

- **Cumulative Historical PBS Submissions**: Exactly **33** permanently recorded in `HPC_JOB_LEDGER.csv` and `TASK_LEDGER.csv`.
- **Task F1775 Submissions Consumed**: Exactly **0** (preflight qualification only).
- **Unit Test Validation**: Standalone unit test suite `tests/unit/test_f1775_coupled_fracture_preflight.py` passing **5/5 tests in 0.43s**; full multi-task regression suite passing **29/29 tests in 1.46s**.
- **Recommended Successor Action**: Stage independent supervisory review packet across OpenClaw PAD bridge for formal approval of the forward coupled phase-field fracture execution on the qualified adapted meshes.
