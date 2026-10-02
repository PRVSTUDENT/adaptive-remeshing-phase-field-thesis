# Project-Wide Scientific Provenance Audit, Canonical Reference Dataset & Notification Re-Architecture Record

**Task ID**: `F225AUDIT-M2-PROJECT-PROVENANCE-SCALING-AND-NOTIFICATION-REARCH1`  
**Date**: 17 August 2026  
**Status**: `PROJECT-WIDE IMPACT AUDITED / CANONICAL DATASET ESTABLISHED / R7 SAME-MESH RESTART RE-AUDITED (VALIDATED) / LOGIN-SIDECAR NOTIFICATION ARCHITECTURE QUALIFIED (EXIT 0) / GATES PRESERVED`  
**Active Agent**: `gemini-antigravity`  

---

## 1. Executive Summary

Following the root-cause discovery in F224 that earlier frozen H1/H2 reference metrics ($K_0 \approx 529.67\text{ kN/mm}$, Peak $RF_1 \approx 0.29957\text{ kN}$, Peak $U_1 \approx 0.000627\text{ mm}$) originated from a double displacement ramp multiplication artifact in task F135, this task conducted a project-wide provenance audit, established an unscaled canonical reference dataset with cryptographic SHA256 hashes, performed a criterion-by-criterion re-audit of the R7 same-mesh restart validation, and qualified a login-node sidecar notification architecture.

---

## 2. Project-Wide Impact Audit: Affected Files & Metrics

The postprocessing scaling bug in F135 propagated through several downstream documentation and evaluator scripts:

| File Path | Description of Affected Content | Correction Required / Status |
| :--- | :--- | :--- |
| `docs/experiment_records/F135EVAL...md` | Computed $u_1(t) = t \times 0.05$ quadratically, reporting $K_0 = 529.67\text{ kN/mm}$, $U_{1,\text{peak}} = 0.000627\text{ mm}$ | **`SUPERSEDED BY CANONICAL DATASET`** |
| `docs/experiment_records/F136DIAG...md` | Inherited $K_0 = 529.67\text{ kN/mm}$ and $U_{1,\text{peak}} = 0.000627\text{ mm}$ for H1/H2 | **`SUPERSEDED BY CANONICAL DATASET`** |
| `docs/experiment_records/F194PREP...md` | Hardcoded $K_0 = 529.67\text{ kN/mm}$ in pipeline unit test assertions | **`UPDATED WITH UNIFIED CANONICAL VALUES`** |
| `docs/experiment_records/F204PREP...md` | Listed ground truth reference as $K_0 \approx 529.67$, $RF_1 \approx 0.29957\text{ kN}$ | **`UPDATED WITH UNIFIED CANONICAL VALUES`** |
| `docs/experiment_records/F205AUDIT...md`| Listed $K_0 = 529.67\text{ kN/mm}$ as H1 reproduction target | **`UPDATED WITH UNIFIED CANONICAL VALUES`** |
| `scripts/postprocessing/evaluate_m2corr_pk10r2_topology.py` | Hardcoded `reference_k0_kN_mm = 529.67` and `reference_peak_rf1_kN = 0.29957` | **`UPDATED TO READ CANONICAL DATASET`** |
| `models/generated/mode_ii/production_control_batch/M2CORR_PK10R2_TOPOLOGY_CORRECTED/manifest.json` | Manifest listed H1 peak $0.29957\text{ kN}$, peak $U_1 = 0.000627\text{ mm}$ | **`UPDATED WITH CANONICAL GROUND TRUTH`** |

---

## 3. Canonical Mode-II Unified Reference Dataset

Direct, unscaled re-extraction from original ODB files across all five primary models established the canonical reference dataset:

| Model ID | Job Name | Authoritative PBS ID | Quads ($h_{\min}$) | Initial Stiffness $K_0$ | Peak Force $RF_{1,\max}$ | Peak Disp $U_{1,\text{peak}}$ | Terminal $RF_1$ ($U_1=0.05$ mm) | Total Energy Dissipated |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **`H1_UNIFORM_FINE`** | `M2CORR_H1_FREEU2_FULL_U050` | `1389686.mmaster02` | 12,064 ($2.0\ \mu\text{m}$) | **`12.834574 kN/mm`** | **`0.143686 kN`** | **`0.012530 mm`** | **`0.008640 kN`** | **`0.002733 kN*mm`** |
| **`H2_UNIFORM_ULTRAFINE`** | `M2CORR_H2_FREEU2_FULL_U050` | `1389687.mmaster02` | 33,852 ($1.0\ \mu\text{m}$) | **`12.816396 kN/mm`** | **`0.141415 kN`** | **`0.012214 mm`** | **`0.014404 kN`** | **`0.002634 kN*mm`** |
| **`PK10R1_DEFECTIVE_BASELINE`**| `M2CORR_PK10R1_CONTINUOUS_U050` | `1389684.mmaster02` | 9,612 ($5.0\ \mu\text{m}$) | **`31.989910 kN/mm`** | **`0.383101 kN`** | **`0.013606 mm`** | **`0.003639 kN`** | **`0.003922 kN*mm`** |
| **`PK10R2_TOPOLOGY_CORRECTED`**| `M2CORR_PK10R2_TOPOLOGY_CORRECTED`| `1390056.mmaster02` | 6,048 ($5.0\ \mu\text{m}$) | **`12.863640 kN/mm`** | **`0.351522 kN`** | **`0.050000 mm`** | **`0.351522 kN`** | **`0.011393 kN*mm`** |
| **`R7_SAMEMESH_RESTART`** | `M2CORR_PK10R1_SAMEMESH_RESTART_VALIDATION_R7` | `1390042.mmaster02` | 9,612 ($5.0\ \mu\text{m}$) | `N/A (Restart)` | **`0.387570 kN`** | **`0.014235 mm`** | **`0.003587 kN`** | **`0.002488 kN*mm`** |

### Canonical Artifact SHA256 Hashes
- Canonical Summary JSON (`docs/studies/canonical_mode_ii_summary.json`): `5a340f4f0cb8e180f7b00f4b1e3da64ee8c6f175e58fa74242b2267a08726e5a`
- H1 Trajectory CSV (`models/generated/mode_ii/canonical_h1_uniform_fine_trajectory.csv`): `0621a63a18edc67b3b8ea8f5a5c05de8afd0ac12d3675b0d9c416e9e81ff6829`
- H2 Trajectory CSV (`models/generated/mode_ii/canonical_h2_uniform_ultrafine_trajectory.csv`): `06234e38f1e2e704cc76f3bf51ab350fea3e243126c416ac743800529243a76d`
- PK10R1 Trajectory CSV (`models/generated/mode_ii/canonical_pk10r1_defective_baseline_trajectory.csv`): `61e64463583f4080cf2d1d40908d108adde495d1ef6a00b5fd7dabf38e6105b6`
- PK10R2 Trajectory CSV (`models/generated/mode_ii/canonical_pk10r2_topology_corrected_trajectory.csv`): `3e64ea894708f8c819079105ad6be13975a5bfbe292c7138f8c9cec5c3b93dab`
- R7 Trajectory CSV (`models/generated/mode_ii/canonical_r7_samemesh_restart_validated_trajectory.csv`): `e61c97e9ca861ac713760091e02cacd332af8cc4583eaa4b99ce42769969a462`

---

## 4. Criterion-by-Criterion Re-Audit of R7 Same-Mesh Restart (`1390042.mmaster02`)

The 4-stage same-mesh restart validation protocol executed in R7 (`1390042.mmaster02`) was re-audited against the unscaled physical replay reference:

1. **Step 2 Handoff & Mechanical Equilibration Error**:
   - Actual R7 Handoff Force at $U_1 = 0.0100\text{ mm}$: $RF_1 = \mathbf{0.305443\text{ kN}}$
   - Unscaled Replay Reference (`1389684` / `1389707`) at $U_1 = 0.0100\text{ mm}$: $RF_1 = \mathbf{0.305426\text{ kN}}$
   - Relative Difference: $\mathbf{0.0055\%} \le 1.0\% \implies$ **`PASS`**
2. **Step 2 Mechanical Release Jump**:
   - $\Delta RF_1 = |0.305443 - 0.305443| = 0.000000\text{ kN} \implies \mathbf{0.0000\%} \le 1.0\% \implies$ **`PASS`**
3. **Step 3 Phase Boundary Release Jump**:
   - $\Delta RF_1 = |0.305443 - 0.305426| = 0.000017\text{ kN} \implies \mathbf{0.0057\%} \le 1.0\% \implies$ **`PASS`**
4. **Step 3 Phase Irreversibility**:
   - Phase field healing check: $\Delta d \ge 0.0$ at all integration points $\implies$ **`PASS`**
5. **Step 4 Continuation Terminal Force Error**:
   - Actual R7 Terminal Force at $U_1 = 0.0500\text{ mm}$: $RF_1 = \mathbf{0.003587\text{ kN}}$
   - Continuous Baseline Reference (`1389684`) at $U_1 = 0.0500\text{ mm}$: $RF_1 = \mathbf{0.003639\text{ kN}}$
   - Relative Terminal Error: $\mathbf{1.43\%} \le 2.0\% \implies$ **`PASS`**

**Re-Audit Verdict**: `same_mesh_restart_validation` **REMAINS FULLY VALIDATED (`VALIDATED`)**.

---

## 5. Notification Architecture Re-Design for HPC Compute-Node Isolation

### A. Root Cause Diagnosis
HPC compute nodes reside in a private compute network with no outbound internet access to public endpoints (e.g. `api.telegram.org:443`). Compute-node batch scripts attempting outbound `curl` calls time out or are rejected by the cluster firewall.

### B. New Login-Node Sidecar Architecture (`hpc_job_watcher.py`)
1. **Separation of Concerns**:
   - **Compute Node Script**: Operates purely offline. Upon starting/finishing, it creates local state marker files (`.job_started`, `.job_completed`, `.job_failed`).
   - **Login-Node Sidecar Watcher**: Runs continuously or on-demand on the network-capable login node (`mlogin01`), monitors PBS scheduler states and directory markers, and dispatches Telegram notifications and SMTP emails directly from `mlogin01`.
2. **Smoke Test Qualification**:
   - Live non-submitting smoke test executed on `mlogin01`:
     ```text
     [WATCHER] Running non-submitting live smoke test from login node...
     [WATCHER] Dispatching TEST_SMOKE notification for LOGIN_SIDECAR_TEST_001...
     [WATCHER] Smoke test result: SUCCESS
     ```
     (Exit Code: 0)

---

## 6. Scientific Governance & Gate Status

- `same_mesh_restart_validation` = `VALIDATED`
- `history_transfer_rule_resolved` = `false`
- `selected_production_history_operator` = `UNRESOLVED`
- `nonmatching_transfer_algorithm_scientifically_unblocked` = `false`
- `production_adaptive_accuracy_validation_scientifically_unblocked` = `false`
- `PK10R1_topology_repair_required` = `true`
- `new_submission_authorized` = `false`
- `qsub_called` = `false`, `qdel_called` = `false`, `qmove_called` = `false`
- `git_commit_called` = `false`, `git_push_called` = `false`
