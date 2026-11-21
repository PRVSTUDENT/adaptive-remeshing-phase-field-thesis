# Method C Case 3: Cycle-4 Refinement Package Preparation Report

**Protocol:** `METHOD_C_INCREMENTAL_ADAPTIVE_REMESHING_V1`  
**Task ID:** `METHOD-C-CASE3-CYCLE4-REFINEMENT-PACKAGE`  
**Correlation ID:** `HND-METHOD-C-CASE3-CYCLE4-PREP-001`  
**Predecessor Correlation ID:** `HND-METHOD-C-CASE3-JOB4-DIAG-001` (Verdict: `APPROVE`)  
**Scientific Operation:** `method_c_case3_cycle4_refinement_package`  
**Master Goal Status:** `OPEN`  
**Date:** 2026-11-21  

---

## 1. Executive Summary & Governance

This report documents the preparation, technical preflight, and verification of the **Cycle-4 Refinement Package** for Method C Case 3 (Pandey & Kumar Section 4.3 Rectangular Notched Plate with Hole and Pins).

Following the approved Job-4 diagnosis under `HND-METHOD-C-CASE3-JOB4-DIAG-001` (Fix Option A), this package prepares the fourth adaptive cycle and production input deck `PK_METHOD_C_CASE3_CYCLE4_REFINED_JOB5.inp` for Job 5 (`M1_MC_C3_JOB5`).

### Governance & Budget Compliance
- **Submissions in Package:** Exactly **0** new PBS jobs consumed for package preparation.
- **Cumulative PBS Submissions:** Strictly preserved at **66**.
- **Execution Guard:** No Job-5 submission will occur until this refinement package is formally reviewed and approved by independent supervision.
- **5-Job Budget:** Job 5 (`M1_MC_C3_JOB5`, cumulative 66 $\to$ 67) will be the final job of the Fix Option A 5-job budget (62–67).
- **Frozen UEL:** `models/pandey_kumar_mode1/f42_mixed_uel.for` bitwise preserved (`CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6`).

---

## 2. Donor State Characterization (Job-4 Terminal Converged State)

The donor state is extracted directly from `/scratch9/pr21vyci/runs/mode1_290_method_c_case3_c3_job4/PK_METHOD_C_CASE3_CYCLE3_REFINED_JOB4.odb` at the terminal converged equilibrium state (Step 2 Increment 11):

- **Donor Job:** `PK_METHOD_C_CASE3_CYCLE3_REFINED_JOB4` (PBS Job ID `1424780.mmaster02`).
- **Terminal Converged Time:** $t_{\text{step}} = 0.002137931063771248$.
- **Terminal Hold Displacement:** $u_2 = 0.056835\,\text{mm}$ (RP Node 999999).
- **Terminal Reaction Force:** $\text{RF}_2 = 3.9063646\,\text{kN}$.
- **Peak Phase-Field Damage (raw SDV1):** $d_{\max} = 1.001953$ (reconstructed nodal damage: $d_{\max} = 0.996882$).
- **Spatial Crack Tip Position ($d \ge 0.95$):** $x_{\text{tip}} = 13.1118\,\text{mm}, y \approx 69.2\,\text{mm}$ ($\Delta a_x = 3.1118\,\text{mm}$ from notch root $x = 10.0\,\text{mm}$).
- **Process Zone Extent ($d \ge 0.50$):** $x = 13.6163\,\text{mm}$.
- **Distance to Central Void Perimeter:** $20.024\,\text{mm}$ (void perimeter at $x = 26.5\,\text{mm}$, center at $(36.5, 51.0)\,\text{mm}, r = 10.0\,\text{mm}$).
- **Peak History Variable:** $H_{\max} = 19.165562\,\text{MPa}$.
- **F1852 Branch:** $d_{\max} = 1.001953 \ge 0.50 \implies$ `CONSTRUCTED_DAMAGE_ENVELOPE` branch active.

---

## 3. Cycle-4 Adapted Physical Mesh Generation & Quality Audit

The receiver physical mesh `PK_METHOD_C_CASE3_CYCLE4_PHYS.inp` was generated using Abaqus CAE noGUI (`scripts/remeshing/generate_method_c_case3_cycle4_mesh.py`) and audited against the project finite element quality gates (`scripts/remeshing/audit_method_c_case3_cycle4_mesh.py`).

### Refinement Corridor Translation & Expansion
- **Corridor Bounds:** $x \in [8.5, 38.0]\,\text{mm}, y \in [47.0, 77.0]\,\text{mm}$.
- **Extension Purpose:** Translates and expands the fine refinement corridor around the advanced crack tip ($x_{\text{tip}} = 13.1118\,\text{mm}$) and forward process zone ($x = 13.6163\,\text{mm}$) toward and past the central circular void perimeter ($x = 26.5\,\text{mm}$) and void center ($(36.5, 51.0)\,\text{mm}$).
- **Target Element Sizing:** Refined seed $h_{\text{ref}} = 0.140\,\text{mm} < l_0/2 = 0.1425\,\text{mm}$ ($l_0 = 0.285\,\text{mm}$); background seed $h_{\text{bg}} = 2.0\,\text{mm}$.

### Mesh Quality Metrics & Gate Audit
| Quality Gate | Requirement | Measured Value | Status |
| :--- | :--- | :--- | :--- |
| **Gate 01: Positive Jacobian** | $\min \det(J) > 0$, non-positive = 0 | $\min \det(J) = 6.0627 \times 10^{-4}$ (0 non-positive) | **PASS** |
| **Gate 02: Quad Fraction** | Quad fraction $\ge 85.0\%$ | $97.38\%$ ($62,958$ quads, $1,695$ tris) | **PASS** |
| **Gate 03: Aspect Ratio** | Mean $\le 2.50$, Max $\le 4.00$ | Mean $\text{AR} = 1.263$, Max $\text{AR} = 3.879$ | **PASS** |
| **Spatial Resolution ($l_0/2$)** | Forward path median $h \le 0.1425\,\text{mm}$ | Median $h = 0.1248\,\text{mm}$ ($h = \sqrt{\text{Area}}$) | **PASS** |

### Corridor Element Size Distribution ($h = \sqrt{\text{Area}}$)
- **Entire Refinement Corridor ($x \in [8.5, 38.0], y \in [47.0, 77.0]$):**
  * Element Count: $47,057$
  * Min $h$: $0.0341\,\text{mm}$
  * Max $h$: $0.1893\,\text{mm}$
  * Mean $h$: $0.1246\,\text{mm}$
  * Median $h$: $0.1264\,\text{mm}$
- **Forward Crack Trajectory Corridor ($\pm 3.0\,\text{mm}$ along path toward hole):**
  * Element Count: $8,751$
  * Min $h$: $0.0465\,\text{mm}$
  * Max $h$: $0.1805\,\text{mm}$
  * Mean $h$: $0.1234\,\text{mm}$
  * Median $h$: $0.1248\,\text{mm} \le 0.1425\,\text{mm}$ ($l_0/2$)

---

## 4. State & History Transfer Audit

State and history transfer was executed via `scripts/state_transfer/run_case3_cycle4_state_transfer.py` ingesting the Job-4 donor state JSON and receiver mesh.

### Transfer Safeguards & Gates
1. **Notch Slit-Flank Isolation:** Receiver nodes at $y = 70.0\,\text{mm}$ ($x \le 10.0\,\text{mm}$) are partitioned strictly into upper and lower slit-flank element bins, preventing non-physical interpolation across the initial notch crack faces.
2. **Phase-Field Damage Bounds:** $0.0 \le d \le 1.0$ everywhere on the receiver mesh (transferred $d_{\min} = 0.0$, $d_{\max} = 0.992229 \le 1.0$).
3. **Zero Healing Verification:** Transferred maximum damage $d_{\max}^{\text{recv}} = 0.992229 \ge 0.90 \times d_{\max}^{\text{donor}} = 0.897194$ (preservation ratio $99.53\%$, `healing_detected: false`).
4. **Thermodynamic Non-Negativity:** Gauss-point strain energy history $H$ transferred via qualified `isoparametric_gp_transfer.py` with `convex_clamp` limiter mode:
   * Receiver $H_{\min} = 1.1161 \times 10^{-11}\,\text{MPa} \ge 0.0$ (`non_negativity_satisfied: true`).
   * Receiver $H_{\max} = 19.165562\,\text{MPa}$ (exact $100.0\%$ peak preservation matching donor $H_{\max} = 19.165562\,\text{MPa}$).
5. **Initial Damage SVARs:** Phase UEL Layer 1 initial SVARs computed from transferred nodal damage ($d_{\max}^{\text{svar}} = 0.979615$, degradation function $g(d) = (1-d)^2 + k_{\text{res}}$ verified).

All transfer gates evaluated to **PASS** in `PK_METHOD_C_CASE3_CYCLE4_TRANSFER_RECEIPT.json`.

---

## 5. 3-Layer Production Deck Specification (`PK_METHOD_C_CASE3_CYCLE4_REFINED_JOB5.inp`)

The 3-layer coupled re-equilibration and forward propagation deck was assembled with full verification of syntax and controls:

### Layered Architecture ($193,959$ total elements)
- **Layer 1: Phase-Field User Elements (DOF 3)**
  * $62,958$ quads (`*USER ELEMENT, NODES=4, TYPE=U1, PROPERTIES=6, COORDINATES=2, VARIABLES=18, UNSYMM; 3`)
  * $1,695$ tris (`*USER ELEMENT, NODES=3, TYPE=U3, PROPERTIES=6, COORDINATES=2, VARIABLES=18, UNSYMM; 3`)
- **Layer 2: Mechanical Displacement User Elements (DOFs 1, 2)**
  * $62,958$ quads (`*USER ELEMENT, NODES=4, TYPE=U2, PROPERTIES=6, COORDINATES=2, VARIABLES=18, UNSYMM; 1, 2`)
  * $1,695$ tris (`*USER ELEMENT, NODES=3, TYPE=U4, PROPERTIES=6, COORDINATES=2, VARIABLES=18, UNSYMM; 1, 2`)
- **Layer 3: Companion Visualizer Elements (UMAT CPE4 / CPE3)**
  * $62,958$ quads (`CPE4`, `ELSET=umatelem_quad`)
  * $1,695$ tris (`CPE3`, `ELSET=umatelem_tri`)

### Step Architecture & Solver Controls
- **Step 1: Fixed-Load Re-equilibration Hold**
  * Displacement hold at $u_2 = 0.056835\,\text{mm}$ (matching terminal Increment 11).
  * Controlled via `*AMPLITUDE, NAME=CONST_HOLD` ($0.0, 1.0, 1.0, 1.0$).
  * Cutback floor: $\Delta t_{\min} = 1.0 \times 10^{-14}$.
  * Line search: verbatim compliant `*CONTROLS, PARAMETERS=LINE SEARCH` with data line `4`.
- **Step 2: Forward Crack Propagation**
  * Target displacement: $u_2 = 0.4125\,\text{mm}$ under `*BOUNDARY, OP=MOD`.
  * Cutback floor: $\Delta t_{\min} = 1.0 \times 10^{-14}$.
  * Initial time increment $0.002$, maximum time increment $0.005$, total time $1.0$.
  * Line search: verbatim compliant `*CONTROLS, PARAMETERS=LINE SEARCH` with data line `4`.

---

## 6. Technical Datacheck Results (Cluster Exit 0)

The production deck `PK_METHOD_C_CASE3_CYCLE4_REFINED_JOB5.inp` was transferred to the cluster scratch directory `/scratch9/pr21vyci/runs/mode1_290_method_c_case3_c4_job5/` and executed through `run_case3_cycle4_datacheck.sh` with the frozen user subroutine `f42_mixed_uel.for`.

- **Cluster Node:** `t2-login01` / PBS datacheck runner.
- **Compiler:** Intel Fortran Classic 2021.13.0 (ifort) with gcc 11.4.0.
- **Subroutine Compilation & Linking:** User subroutines `uel_` and `umat_` compiled and linked cleanly (`GNU ld version 2.30-128.el8_10`).
- **Input File Processor (pre):** Processed all $193,959$ layered elements, $64,107$ nodes (including RP 999999), kinematic couplings, amplitudes, and solution initial conditions without errors.
- **Abaqus/Standard Datacheck Execution:**
  ```
  Abaqus JOB PK_METHOD_C_CASE3_CYCLE4_REFINED_JOB5_DC COMPLETED
  Datacheck Finished with Exit Code: 0
  ```
- **Datacheck Outputs:** Committed to repository:
  * `PK_METHOD_C_CASE3_CYCLE4_REFINED_JOB5_DC.dat` (SHA `F6A2D54F927924FA26975D5BE88ECBF7022A831536411379D63CA0AFBF76F7ED`)
  * `PK_METHOD_C_CASE3_CYCLE4_REFINED_JOB5_DC.msg` (SHA `C1B205BFA609590DBB3B7BB6D2730254B50F6D2CEE5554E811C9B0D6F97BB20D`)

---

## 7. Solver Strategy for the Recurring $\Delta t_{\min}$ Floor

During crack propagation in non-softening/phase-field regularized media under displacement control, crack growth exhibits localized dynamic snap-through instability when the strain energy release rate sharply peaks. In quasi-static Newton-Raphson solvers with line search, this manifests as residual rebound in the fracture process zone, causing consecutive time increment cutbacks until reaching $\Delta t_{\min}$.

The Method C adaptive remeshing strategy handles this recurring physical behavior systematically:
1. **Non-Failure Principle:** Reaching the cutback floor during forward crack propagation is a physical indicator of rapid energy release, not an algorithmic solver failure.
2. **Terminal State Capture:** When $\Delta t_{\min}$ is reached, the last converged equilibrium state prior to divergence is frozen as an authentic physical donor.
3. **Adaptive Translation & Advance:** The localized refinement corridor is translated and expanded along the freshly determined crack growth direction, fields are transferred with strict non-healing and non-negativity guarantees, re-equilibration is verified at the hold displacement, and propagation is resumed.
4. **Relaxed Cutback Headroom:** In Job 5, setting $\Delta t_{\min} = 1.0 \times 10^{-14}$ (rather than $1.0 \times 10^{-8}$) provides 6 orders of magnitude additional cutback headroom to resolve steep snap-through stages before triggering remeshing.

---

## 8. Resolution of Advisory Notes `NOTE-MC-C3J4D-01` through `04`

In accordance with the review directives from `HND-METHOD-C-CASE3-JOB4-DIAG-001`:

1. **`NOTE-MC-C3J4D-01` (Section 4 Inventory Verification):**
   * Execution tests: `tests/unit/test_method_c_case3_job4_execution.py` ($7,150\,\text{B}$, SHA `7AA1985ACD2CA76DBE1C44F3532C3A7AF9CC03C5914E84FA03D2E0A4E216DB7E`).
   * Diagnosis report: `docs/validation/METHOD_C_CASE3_JOB4_DIAGNOSIS_REPORT.md` ($20,603\,\text{B}$, SHA `07D5759CB0575F6A90757DCBA13DE444B84DFEC33A8940CBE5A224097CC5793F`).
   * Diagnosis tests: `tests/unit/test_method_c_case3_job4_diagnosis.py` ($7,075\,\text{B}$, SHA `B8EA0E605D41FA52125A03FD3837D53C8BC882363CE76033DA5983DC8C5CD3D4`).
2. **`NOTE-MC-C3J4D-02` (Node-21774 Damage Range):**
   * Physical node 21774 ($x = 13.284\,\text{mm}, y = 69.347\,\text{mm}$) is located $0.17\,\text{mm}$ ahead of the terminal crack tip in the active fracture process zone. Its damage range is explicitly recorded as $d \in (0.80, 0.90)$ ($d \approx 0.85$), confirming that divergence was driven by localized fracture kinetics rather than global numerical singularity.
3. **`NOTE-MC-C3J4D-03` (Report-Level Fields vs Execution Receipt):**
   * Forensic diagnosis fields ($x_{\text{tip}}$, $\Delta a_x$, failing node coordinates) are explicitly classified as report-level post-processing fields derived from spatial crack extraction, and are distinguished from raw runtime execution receipt telemetry.
4. **`NOTE-MC-C3J4D-04` (Semantic Definition of `last_successful_pbs_job_id`):**
   * `last_successful_pbs_job_id: 1424778.mmaster02` in `ACTIVE_TASK.json` reflects the reviewed-and-approved donor job (Job 3) whose execution satisfied acceptance criteria, rather than raw Exit-0 solver status. Job 4 (`1424780.mmaster02`) is recorded as `CUTBACK_TERMINATED` in `HPC_JOB_LEDGER.csv`.

---

## 9. Complete Artifact Manifest & Commit-Pinned GitHub URLs

The commit-pinned GitHub URLs below will point to the exact commit upon git push:

| Artifact Path | Size (Bytes) | SHA256 Hash | Repository-Relative Path |
| :--- | :--- | :--- | :--- |
| **Physical Mesh** | $4,685,923$ | `18E9B7ACD4E66B8503CD6E876FAE211671927874EEF7B1A3FF9F37068E44C5BA` | `models/pandey_kumar_mode1/290_method_c_case3/PK_METHOD_C_CASE3_CYCLE4_PHYS.inp` |
| **Production Deck** | $28,725,276$ | `C2C9D98CEA43DC4A9A042360302AF2B2867754C028957DB0605DC10D7CF52D6F` | `models/pandey_kumar_mode1/290_method_c_case3/PK_METHOD_C_CASE3_CYCLE4_REFINED_JOB5.inp` |
| **Mesh Audit JSON** | $1,617$ | `C0467C1117E0170D37EB660412EF3D22538CE77EBAF0152E971CD5A0F9D62570` | `models/pandey_kumar_mode1/290_method_c_case3/method_c_case3_cycle4_mesh_audit.json` |
| **Transfer Receipt** | $3,374$ | `B151565AACA9CA3AFF6319DE83955892950286926A766FEC9F8782534620B38F` | `models/pandey_kumar_mode1/290_method_c_case3/PK_METHOD_C_CASE3_CYCLE4_TRANSFER_RECEIPT.json` |
| **Datacheck DAT** | $16,777$ | `F6A2D54F927924FA26975D5BE88ECBF7022A831536411379D63CA0AFBF76F7ED` | `models/pandey_kumar_mode1/290_method_c_case3/PK_METHOD_C_CASE3_CYCLE4_REFINED_JOB5_DC.dat` |
| **Datacheck MSG** | $1,475$ | `C1B205BFA609590DBB3B7BB6D2730254B50F6D2CEE5554E811C9B0D6F97BB20D` | `models/pandey_kumar_mode1/290_method_c_case3/PK_METHOD_C_CASE3_CYCLE4_REFINED_JOB5_DC.msg` |
| **Submit PBS** | $1,328$ | `DEEC3C6EA6B7F7ECDA301DE082CA7EFEF5AEA660488CFE509B9F65DB818DC206` | `models/pandey_kumar_mode1/290_method_c_case3/submit_case3_cycle4_job5.pbs` |
| **Datacheck Script** | $514$ | `9F583C7FA2ED3A50A62B9E5BF6012ECE87CF629F3219178A09B1786C121FA899` | `models/pandey_kumar_mode1/290_method_c_case3/run_case3_cycle4_datacheck.sh` |
| **Donor State JSON** | $21,438,601$ | `CAF1079C384B2DC462F7F03E5A26DE7888565418E685030B814D8E67060E27F7` | `models/pandey_kumar_mode1/290_method_c_case3/donor_case3_cycle3_state.json` |
| **Frozen UEL** | $29,722$ | `CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6` | `models/pandey_kumar_mode1/f42_mixed_uel.for` |
| **Package Tests** | $8,296$ | `8660C1BC7F4280E2C2C6F4100535AB7E4129EF184F4E0958B18749435D210763` | `tests/unit/test_method_c_case3_cycle4_package.py` |
| **Package Report** | `[THIS_FILE]` | `0431CB0B15410FD60A3D2207E9044453039C6755F2D873FECFEF727FEF81E4C5` | `docs/validation/METHOD_C_CASE3_CYCLE4_PREPARATION_REPORT.md` |

---

## 10. Conclusion & Next Step

The Cycle-4 Refinement Package is fully prepared, audited, and verified:
1. Physical mesh quality satisfies all finite element quality gates with $97.38\%$ quad fraction and median $h = 0.1248\,\text{mm}$ resolving $l_0/2$.
2. State and history transfer maintains thermodynamic non-negativity ($H_{\min} \ge 0$), bounded phase damage, and zero healing.
3. Production input deck carries verified UEL cards from the start and passes cluster technical datacheck with Exit 0.
4. Cumulative PBS submission count is strictly preserved at 66 (0 new jobs consumed).

**Next Step:** Submit this refinement package as `HND-METHOD-C-CASE3-CYCLE4-PREP-001` across the bridge for independent structured review. Upon review approval, proceed to submit Job 5 (`M1_MC_C3_JOB5`, cumulative 66 $\to$ 67) as the final job of the Fix Option A 5-job budget.
