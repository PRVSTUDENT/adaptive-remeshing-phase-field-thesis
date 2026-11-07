# Method C Paired Same-Mesh Control Checkpoint-03 Provenance Correction & Datacheck Qualification Report

**Task ID:** `F1623-METHOD-C-SAME-MESH-CHECKPOINT03-PROVENANCE-CORRECTION`  
**Protocol Version:** 2  
**Date:** 5 November 2026  
**Agent:** Gemini Antigravity  
**Predecessor Task:** `F1622-METHOD-C-SAME-MESH-ABAQUS-CONTROL-STAGING` (Status: `DATACHECKS_PASSED_BOTH_EXIT_0`)  
**Supervisory Directive Intake:** ChatGPT PAD Bridge Decision `HND-568381d9d20e` (Option 3 — Block Paired PBS Execution Pending One Bounded Donor-State Correction)  
**Governing Submission Constraint:** Strictly 0 production solver PBS submissions authorized under Task F1623 (`production_pbs_submissions: 0`, `zero_pbs_enforced: True`)

---

## 1. Executive Summary & Provenance Remediation

In accordance with supervisory directive `HND-568381d9d20e`, this report documents the complete remediation of donor-state provenance and the qualification of dynamic first-iteration Abaqus input decks for the paired same-mesh control experiment on accepted C5 donor Checkpoint 03 (Job `1419566.mmaster02`, $u_y = 0.0018703125$ mm, 12,996 elements).

### 1.1 The Checkpoint 02 Contamination Defect (Caught by ChatGPT)
In Task F1622, while Gauss-point history $H$ was correctly extracted from Checkpoint 03 (`converged_checkpoint_03.json`), `nodal_displacements_initial.csv`, `nodal_phase_field_initial.csv`, and element nodal damage in `d_lower_bounds.csv` were inadvertently copied from Package 167. Package 167 was initialized from Checkpoint 02 ($u_y = 0.0018653125$ mm), whereas Checkpoint 03 was solved at $u_y = 0.0018703125$ mm across a physical load increment $\Delta u_y = 5.0\times 10^{-6}$ mm.

Across this $5.0\,\text{nm}$ continuation increment, physical fields evolved as documented in `results/validation/checkpoint_02_vs_03_discrepancy_analysis.json`:
- **Displacement Evolution:** $\max \|\Delta u\| = 5.2203\times 10^{-6}$ mm ($\text{RMS} = 3.1741\times 10^{-6}$ mm).
- **History Evolution:** $\max |\Delta H| = 0.07509$ MPa ($\text{RMS} = 0.001115$ MPa), with physical history growth at 13,550 Gauss points.
- **Damage Evolution:** $\max |\Delta d| = 2.9776\times 10^{-8}$ ($\text{RMS} = 5.0407\times 10^{-9}$).

These differences represent legitimate physical state evolution across the continuation step rather than iterative tolerance violations. However, pairing Checkpoint 02 kinematics and damage with Checkpoint 03 history created an unphysical artificial state mismatch that confounded re-equilibration.

### 1.2 The Corrective Actions Executed
1. **100% Direct Checkpoint 03 Extraction:** Extracted $u$, $d$, and $H$ directly from authentic accepted Checkpoint 03 (`converged_checkpoint_03.json`), verifying complete coverage across all 13,278 nodes and 51,984 Gauss points.
2. **Clean Initial Fields Regenerated:** `nodal_displacements_initial.csv`, `nodal_phase_field_initial.csv`, `active_set_boundary_cards.inc`, and `d_lower_bounds.csv` were regenerated directly from Checkpoint 03 with zero contamination.
3. **Dynamic First-Iteration Deck Generation:** Generated authentic first-iteration mechanical and phase decks via `SameMeshControlPDASDriver._deck()`:
   - `P172_ITER1_MECH.inp` (91,942 lines) & `P172_ITER1_PHASE.inp` (117,824 lines)
   - `P173_ITER1_MECH.inp` (91,942 lines) & `P173_ITER1_PHASE.inp` (117,953 lines)
4. **Deterministic Master-Deck Selection (Task F1624 Preflight Correction):** Resolved Blocker 1 by upgrading `SameMeshControlPDASDriver.load()` to select the explicit package master deck (`*_REEQUILIBRATION.inp` / `*_RESTART.inp`), excluding datacheck decks (`*_DC.inp`) and per-iteration decks (`*_ITER*.inp`), and failing closed if missing, ambiguous, or inconsistent with C5 mesh topology (12,996 elements, 13,278 nodes).
5. **Authentic Cluster Datacheck Qualification:** Staged both packages to cluster scratch and executed authentic interactive Abaqus 2023 datachecks on **all 8 subproblems** (preliminary + dynamic iter1) on `mlogin01.cluster`. All 8 passed with Exit 0, 0 errors, and completion banners.
6. **Active-Set & Localized Damage Characterization:**
   - **Written Initial Damage Boundary Cards:** Exactly 13,278 cards in `active_set_boundary_cards.inc` establishing the baseline damage Dirichlet field from Checkpoint 03.
   - **Localized Damage Characterization:** In Checkpoint 03, peak damage is $d_{\max} = 0.69098$ (0 nodes with $d \ge 0.95$; 23 nodes with $d \ge 0.65$; 66 nodes with $d \ge 0.60$).
   - **Runtime PDAS Active Set $\mathcal{A}_k$:** Evaluated dynamically at runtime by the solver from the signed KKT residual condition $\mathcal{A}_k = \{ i : d_i - d_{\min, i} + c \cdot r_i \le 0 \}$, not from a static geometric damage threshold.
7. **Fail-Closed Unit Tests:** Added regression tests verifying agreement with Checkpoint 03 to machine precision ($< 10^{-12}$), asserting deterministic master-deck selection under shuffled filesystem enumeration order, and verifying actual staged-driver loading.

---

## 2. Experimental Matrix & Controlled Variables

All variables between Arm 1 and Arm 2 are held strictly invariant with the sole exception of the transferred Gauss-point history operator:

| Parameter / Variable | Arm 1 (Control Old - P172) | Arm 2 (Control Corrected - P173) | Controlled Parity Status |
| :--- | :--- | :--- | :--- |
| **Package Directory** | `models/pandey_kumar_mode1/172_c5_same_mesh_old_control` | `models/pandey_kumar_mode1/173_c5_same_mesh_corrected_control` | Dedicated local trees |
| **Cluster Scratch Dir** | `/scratch9/pr21vyci/runs/mode1_c5_package172_old_control` | `/scratch9/pr21vyci/runs/mode1_c5_package173_corrected_control` | Dedicated scratch areas |
| **Mesh Topology** | C5 (12,996 CPE4 Quads, 13,278 nodes + RP 999999) | C5 (12,996 CPE4 Quads, 13,278 nodes + RP 999999) | **Bitwise Identical** |
| **Coincident Slit Pairs** | 53 slit pairs along $y = 0.05$ mm, $x \le 0.04$ mm | 53 slit pairs along $y = 0.05$ mm, $x \le 0.04$ mm | **Bitwise Identical** |
| **Initial Displacement $u_0$** | Checkpoint 03 direct ($u_y = 0.0018703125$ mm, 13,278 nodes) | Checkpoint 03 direct ($u_y = 0.0018703125$ mm, 13,278 nodes) | **Bitwise Identical** |
| **Initial Damage $d_0$** | Checkpoint 03 direct ($d \in [0.003390, 0.690981]$, 13,278 nodes) | Checkpoint 03 direct ($d \in [0.003390, 0.690981]$, 13,278 nodes) | **Bitwise Identical** |
| **Active-Set Boundary Cards** | Checkpoint 03 direct (`active_set_boundary_cards.inc`) | Checkpoint 03 direct (`active_set_boundary_cards.inc`) | **Bitwise Identical** |
| **Frozen Production UEL** | `f42_mixed_uel.for` (`CE8D5EDC...`, 29,722 bytes) | `f42_mixed_uel.for` (`CE8D5EDC...`, 29,722 bytes) | **Bitwise Identical** |
| **History Operator** | Element-Averaged Scalar Mean | Hardened Isoparametric Bilinear + Convex Clamp | **Experimental Variable** |
| **History Perturbation Max** | **6.3491085 MPa** (63,491$\times$ coupled tolerance) | **$2.7089\times 10^{-13}$ MPa** ($< 10^{-12}$ MPa) | **$2.3\times 10^{13}\times$ Error Reduction** |
| **History Perturbation RMS** | **0.0680823 MPa** (681$\times$ coupled tolerance) | **$2.2206\times 10^{-15}$ MPa** ($< 10^{-14}$ MPa) | **Machine Precision Identity** |
| **Points Exceeding $10^{-4}$ MPa** | **34,720 / 51,984 (66.79%)** | **0 / 51,984 (0.00%)** | **100% Elimination of Violations** |
| **Anderson Acceleration** | **DISABLED** (`anderson_enabled = False`) | **DISABLED** (`anderson_enabled = False`) | **Identical (Unconfounded)** |
| **Picard Phase Relaxation** | Stage 1 $\omega_d = 0.50$, Stage 2 $\omega_d = 0.85$ | Stage 1 $\omega_d = 0.50$, Stage 2 $\omega_d = 0.85$ | **Identical** |
| **Displacement Relaxation** | Stage 1 $\omega_u = 1.00$, Stage 2 $\omega_u = 0.85$ | Stage 1 $\omega_u = 1.00$, Stage 2 $\omega_u = 0.85$ | **Identical** |
| **Compound Active-Set Switch** | $\|A_k\| \le 500, \|\Delta A_k\| \le 10, \Delta A^+ = 0$ ($W=3$) | $\|A_k\| \le 500, \|\Delta A_k\| \le 10, \Delta A^+ = 0$ ($W=3$) | **Identical** |
| **Rollback Safeguards** | Growth factor 1.05, Divergence 1.50, Cap 0.05 | Growth factor 1.05, Divergence 1.50, Cap 0.05 | **Identical** |
| **Iteration Budget** | Max 140 outer iterations | Max 140 outer iterations | **Identical** |
| **Coupled Tolerances** | $\Delta d \le 10^{-5}, \Delta u \le 10^{-9}$ mm, $\Delta H \le 10^{-4}$ MPa, KKT $\le 10^{-6}$ | $\Delta d \le 10^{-5}, \Delta u \le 10^{-9}$ mm, $\Delta H \le 10^{-4}$ MPa, KKT $\le 10^{-6}$ | **Identical** |

---

## 3. Cluster Staging & Authentic Datacheck Verification

Both packages were staged to compute cluster scratch using guarded non-interactive SSH (`Invoke-GuardedSsh.ps1`) and qualified interactively with Abaqus 2023 on `mlogin01.cluster`.

### 3.1 Datacheck Execution Summary (All 8 Subproblems)

| Package | Subproblem Job | Role / Type | Memory | Walltime | Exit Code | Authentic Datacheck Banner | Errors |
| :--- | :--- | :--- | :--- | :--- | :---: | :--- | :---: |
| **Package 172** | `P172_MECHANICAL_DC` | Preliminary Mechanical DC | 8 GB | ~12 s | **0** | `THE ANALYSIS HAS COMPLETED SUCCESSFULLY` | **0** |
| **Package 172** | `P172_PHASE_DC` | Preliminary Phase DC | 8 GB | ~14 s | **0** | `THE ANALYSIS HAS COMPLETED SUCCESSFULLY` | **0** |
| **Package 172** | `P172_ITER1_MECH` | Dynamic Iter-1 Mechanical | 8 GB | ~12 s | **0** | `THE ANALYSIS HAS COMPLETED SUCCESSFULLY` | **0** |
| **Package 172** | `P172_ITER1_PHASE` | Dynamic Iter-1 Phase | 8 GB | ~14 s | **0** | `THE ANALYSIS HAS COMPLETED SUCCESSFULLY` | **0** |
| **Package 173** | `P173_MECHANICAL_DC` | Preliminary Mechanical DC | 8 GB | ~12 s | **0** | `THE ANALYSIS HAS COMPLETED SUCCESSFULLY` | **0** |
| **Package 173** | `P173_PHASE_DC` | Preliminary Phase DC | 8 GB | ~14 s | **0** | `THE ANALYSIS HAS COMPLETED SUCCESSFULLY` | **0** |
| **Package 173** | `P173_ITER1_MECH` | Dynamic Iter-1 Mechanical | 8 GB | ~12 s | **0** | `THE ANALYSIS HAS COMPLETED SUCCESSFULLY` | **0** |
| **Package 173** | `P173_ITER1_PHASE` | Dynamic Iter-1 Phase | 8 GB | ~14 s | **0** | `THE ANALYSIS HAS COMPLETED SUCCESSFULLY` | **0** |

### 3.2 Output File Authentication and Hashes

All 24 datacheck receipts (`.dat`, `.msg`, `.stdout.txt`) were downloaded to local package trees and verified:

- **Package 172 (Arm 1 - Control Old):**
  * `P172_MECHANICAL_DC.dat`: SHA-256 = `10F3CEB0CB9F6F0356BC35E84B3D77108B31DB38673375972A9675D0DF7A5564`
  * `P172_MECHANICAL_DC.msg`: SHA-256 = `BD83CFAB3CC82297D4AD7B7ABFCB1B3EF0A6A55DAEE53E3486040B7759A9E66B`
  * `P172_PHASE_DC.dat`: SHA-256 = `F8926BC801735ED1909DBA14ED1B813A4C947DBDACB1F9E3595250E30E0201F2`
  * `P172_PHASE_DC.msg`: SHA-256 = `F4A921227923E3B4795AD1DC3D57049B62A0A8D3E32E3857E7EC34EDA44573CC`
  * `P172_ITER1_MECH.dat`: SHA-256 = `A8240074995FAC0503FDB4EE304B108B6E8AEDF2A4D7CCE07C9051DE1D486061`
  * `P172_ITER1_MECH.msg`: SHA-256 = `CAFBC246F48B56433D4F1A8E4CE1E706ED65CEDB80917DD5AC8CB224CB6A27D2`
  * `P172_ITER1_PHASE.dat`: SHA-256 = `6C0DE7AFB494875A51D35382A2E98E5BF9D014E4B8A3D36EBE512D2F1B02D93E`
  * `P172_ITER1_PHASE.msg`: SHA-256 = `2AFB95D7B847863D605615EA4559EB06442F32C632E7730FB01AD6286CD3CDCB`

- **Package 173 (Arm 2 - Control Corrected):**
  * `P173_MECHANICAL_DC.dat`: SHA-256 = `04CAD91DD1E5589DC112A2288BE3073FEE06679FC11CFFA80E1AA354319B8E96`
  * `P173_MECHANICAL_DC.msg`: SHA-256 = `3CE577FDD7613A615DC61E6FE92C8ACACF4FB18F8EBB83E170764E559F562F72`
  * `P173_PHASE_DC.dat`: SHA-256 = `2F9E479D896E5A7E69489A538B6759FD76E51323FEA043CC2B902CA3EA76EDBB`
  * `P173_PHASE_DC.msg`: SHA-256 = `B0E7AC694D7419B07D7E642A55769CFAC18BB14710A2FA43CFB797FB7715041F`
  * `P173_ITER1_MECH.dat`: SHA-256 = `910A19A2ECCE2CA152A6218D2CD87258DB695932D78506638E0BDED460B354BF`
  * `P173_ITER1_MECH.msg`: SHA-256 = `A261016D01D026B23813EC0169920369B9494D4F9D36DA7EB2D533ACC1DD8B6B`
  * `P173_ITER1_PHASE.dat`: SHA-256 = `531EB5725F80998D5C5D826B99CBDFB54A13ACBB200A43CD00820503FD1AEB55`
  * `P173_ITER1_PHASE.msg`: SHA-256 = `3FEA09F53E090DA24A5C2AF2227A081BC158522100C294CDE7B7510F0AE43F88`

### 3.3 Remote Environment Verification

1. **PBS Submit Script Syntax:**
   * `bash -n submit_M1_C5_P172_OLD_CONTROL.pbs`: **PASS (Exit 0)**
   * `bash -n submit_M1_C5_P173_CORRECTED_CONTROL.pbs`: **PASS (Exit 0)**
2. **Python Import Smoke Test:**
   * Package 172 `python3 smoke_import.py`: `REMOTE_IMPORT_SUCCESS: True`
   * Package 173 `python3 smoke_import.py`: `REMOTE_IMPORT_SUCCESS: True`
   * Verified that `SameMeshControlPDASDriver`, `Mesh2D`, `PDASReEquilibrationSolver`, and reference constants import cleanly without missing dependencies.

---

## 4. Falsifiable Scientific Hypotheses for Paired Solver Execution

With both packages corrected, staged, and fully datacheck-qualified across both preliminary and dynamic first-iteration decks, the paired experiment is positioned to test the following alternative hypotheses:

### Hypothesis $H_1$ (History Transfer is Primary Causal Bottleneck):
- **Prediction:** Arm 1 (Package 172) exhibits severe active-set churning, oscillatory damage increments ($\Delta d$), or early convergence stall due to the 6.35 MPa history perturbation and 34,720 violated Gauss points.
- In contrast, Arm 2 (Package 173) converges rapidly within 10–25 outer iterations, meeting all coupled tolerances ($\Delta d \le 10^{-5}$, $\Delta u \le 10^{-9}$ mm, $\Delta H \le 10^{-4}$ MPa, KKT $\le 10^{-6}$) and passing all physical acceptance gates with $\le 2.0\%$ force/energy drift.
- **Scientific Implication:** Confirms that element-averaged history distortion was the dominant root cause of non-convergence in Packages 171-R7 through R10. Authorizes immediate integration of the hardened isoparametric GP operator into production C6 remeshing (Package 171-R12).

### Hypothesis $H_0$ (History Transfer is Secondary to Coupled Fixed-Point Stagnation):
- **Prediction:** Both Arm 1 and Arm 2 experience similar convergence difficulties or require large numbers of outer iterations, indicating that same-mesh re-equilibration itself struggles under the current staggered coupling formulation regardless of history perturbation.
- **Scientific Implication:** Redirects immediate research focus to the staggered fixed-point operator, relaxation scheme, or initialization procedure rather than mesh transfer interpolation.

---

## 5. Governance and Safety Compliance

- **Zero PBS Production Submissions Maintained:** Exactly 0 PBS production solver jobs were submitted or queued during Task F1623 (`max_new_pbs_submissions: 0` strictly enforced).
- **Frozen UEL Integrity:** UEL hash `CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6` (29,722 bytes) strictly preserved bitwise across all decks.
- **Unit and Regression Test Suite:** 11/11 tests pass in 0.51s; full regression suite passing 34/34 tests in 16.29s.
- **Artifacts Reconciled:** All deliverables, datacheck receipts, manifests, and scripts are indexed with verified SHA-256 hashes and byte counts in `project_coordination/ARTIFACT_REGISTRY.csv`.

---

## 6. Next Decision Needed

Task F1623 is complete with status `DATACHECKS_PASSED_ALL_8_SUBPROBLEMS_EXIT_0`.

To proceed with testing the falsifiable hypothesis, supervisory authorization is requested to register a successor execution task (`F1624-METHOD-C-SAME-MESH-ABAQUS-CONTROL-EXECUTION`) authorizing:
1. Submission of Job Arm 1 (Package 172): `M1_C5_P172_OLD_CONTROL` (1 CPU serial, 16 GB RAM, 8 hours walltime, queue `entry_imfdfkmq` / `normal_imfdfkmq`).
2. Submission of Job Arm 2 (Package 173): `M1_C5_P173_CORRECTED_CONTROL` (1 CPU serial, 16 GB RAM, 8 hours walltime, queue `entry_imfdfkmq` / `normal_imfdfkmq`).
3. Total PBS submission quota: exactly 2 jobs.
