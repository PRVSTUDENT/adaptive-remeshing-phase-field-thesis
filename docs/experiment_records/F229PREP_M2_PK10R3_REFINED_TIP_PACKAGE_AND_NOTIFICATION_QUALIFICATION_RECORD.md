# Package Preparation & Qualification Record: M2CORR_PK10R3_REFINED_TIP

**Task ID**: `F229PREP-M2-PK10R3-REFINED-TIP-PACKAGE-AND-NOTIFICATION-QUALIFICATION1`  
**Date**: 17 August 2026  
**Package Status**: `READY_FOR_FRESH_AUTHORIZATION`  
**Submission Gate**: `BLOCKED_PENDING_HUMAN_NOTIFICATION_RECEIPT_CONFIRMATION`  
**Active Agent**: `gemini-antigravity`  

---

## 1. Executive Summary

The diagnostic candidate package `M2CORR_PK10R3_REFINED_TIP` was prepared and fully qualified on the TU Freiberg cluster without submission (`qsub_called = false`). It implements the minimal controlled mesh refinement ($h = 0.0020\text{ mm}$, $h/l_0 = 0.1333 \le 0.15$) along the crack corridor to test recovery of the canonical Mode-II localization field observed in H1 (`1389686.mmaster02`) and H2 (`1389687.mmaster02`).

Non-submitting `abaqus datacheck` and Intel compiler subroutine linking completed with **0 errors**. The persistent login-node sidecar lifecycle was verified on `mlogin01`. The package is marked `READY_FOR_FRESH_AUTHORIZATION`, with submission strictly blocked pending explicit human confirmation of test notification receipt.

---

## 2. Model & Mesh Discretization Specifications

| Metric / Attribute | PK10R2 Baseline (`1390056`) | PK10R3 Refined Tip (Prepared) | Canonical H1 Reference (`1389686`) | Verification / Status |
| :--- | :--- | :--- | :--- | :--- |
| **Physical Nodes** | $6250$ | **`18118`** | $12323$ | Verified |
| **Physical Quads ($N_{\text{phys}}$)** | $6048$ | **`17732`** | $12064$ | Verified |
| **Total Elements (3 Layers)** | $18144$ | **`53196`** | $36192$ | Verified |
| **Crack Tip Element Size ($h_{\min}$)** | $0.00500\text{ mm}$ | **`0.002000 mm`** | $0.00250\text{ mm}$ ($h_{\min} = 0.0020\text{ mm}$) | $2.50\times$ refinement vs PK10R2 |
| **Outer Boundary Size ($h_{\max}$)** | $0.02500\text{ mm}$ | **`0.025000 mm`** | $0.00250\text{ mm}$ (Uniform) | Outer graded mesh preserved |
| **Regularization Ratio ($h_{\min} / l_0$)**| $0.3333$ | **`0.1333`** | $0.1667$ | **Target $\le 0.15$ satisfied** |
| **Nearest GP Distance to Tip ($r_{\min}$)**| $0.001494\text{ mm}$ ($1.494\ \mu\text{m}$) | **`0.000598 mm`** ($0.598\ \mu\text{m}$) | $0.000747\text{ mm}$ ($0.747\ \mu\text{m}$) | Closer to singularity than H1 |
| **Nearest GP Coordinates** | $(0.001057, 0.001057)\text{ mm}$ | **`(-0.000423, -0.000423) mm`**| $(0.000528, 0.000528)\text{ mm}$| Verified |
| **Slit Split-Node Flank Pairs** | $25$ pairs ($50$ nodes) | **`36 pairs`** ($72$ nodes) | $201$ pairs ($402$ nodes) | Fully open slit verified |
| **Tied Top Nodes (`*Equation`)** | $127$ individual ties | **`287 individual ties`** | $201$ individual ties | Individual 2-node blocks verified |
| **Jacobians ($\det \mathbf{J}$)** | $> 0$ everywhere | **`> 0 everywhere`** | $> 0$ everywhere | Convex regular quads |

---

## 3. Scientific Invariants & Changed vs. Unchanged Files

### A. Invariant Scientific Settings
- **Material Parameters**: $E = 210.0\text{ kN/mm}^2$, $\nu = 0.3$, $G_c = 0.0027\text{ kN/mm}$, $l_0 = 0.015\text{ mm}$, $k = 1.0 \times 10^{-7}$.
- **Kinematic Constraints**: Bottom edges clamped ($U_1, U_2 = 0$ on `N_BOTTOM`), reference point `RP` (node 99999) displaced monotonically $U_1 = 0.0500\text{ mm}$, rigid top coupling via individual 2-node `*Equation` blocks.
- **3-Layer Architecture**: Layer 1 Phase (TYPE=U1, DOF 3), Layer 2 Disp (TYPE=U2, DOFs 1, 2), Layer 3 Vis (TYPE=CPE4, passive material).
- **HPC Resources**: 1 CPU, 16 GB RAM, 24:00:00 walltime, queue `entry_imfdfkmq`, Abaqus 2023 / Intel 2024.2.0.

### B. Changed vs. Unchanged Files
- **Changed**:
  - `M2CORR_PK10R3_REFINED_TIP.inp`: Refined mesh resolution along crack band ($h = 0.0020\text{ mm}$).
  - `submit_job.pbs`: Job name updated to `M2PK10R3_REFTIP`.
  - `manifest.json`: Updated element counts and cryptographic hashes.
- **Unchanged**:
  - `f42_mixed_uel.for`: Exact unchanged Fortran subroutine with 6-slot ABI and dummy UMAT stub.
  - `job_notifications.sh`: Unchanged notification library.

---

## 4. Cryptographic SHA-256 Hashes

| Artifact File | Absolute Repo Path | SHA-256 Hash |
| :--- | :--- | :--- |
| **INP Deck** | `models/generated/mode_ii/production_control_batch/M2CORR_PK10R3_REFINED_TIP/M2CORR_PK10R3_REFINED_TIP.inp` | `68fe0ff24272fca78ab76a771671c2bb8f65c4d99d8421aae93851d1401f192c` |
| **UEL Subroutine** | `models/generated/mode_ii/production_control_batch/M2CORR_PK10R3_REFINED_TIP/f42_mixed_uel.for` | `e0865b5eba43c14d21a733e72717e157d65c778319e6556e5eca8ab222364e58` |
| **PBS Launcher** | `models/generated/mode_ii/production_control_batch/M2CORR_PK10R3_REFINED_TIP/submit_job.pbs` | `193ec4ae1b5e1a42b09c9497cae88467b808e5de83061f1d63b94028b0b08611` |
| **Notification Shell** | `models/generated/mode_ii/production_control_batch/M2CORR_PK10R3_REFINED_TIP/job_notifications.sh` | `96756a681d2d36c11b36b89288f631f8ecc9537543c2c745a4bae1b425984b47` |
| **Package Manifest** | `models/generated/mode_ii/production_control_batch/M2CORR_PK10R3_REFINED_TIP/manifest.json` | `4a7512a8ad11c20e2063b5ee87ffac1791c0455662d0ac0b90acac10cba54045` |
| **Generator Script** | `scripts/model_generation/build_pk10r3_refined_tip_candidate.py` | `c8169de0fb7f228e379bc0f6fb44e9c0a9cf363033d7896d4f893045691272f8` |

---

## 5. Non-Submitting Solver & Subroutine Datacheck Qualification

- **Command**: `abaqus job=M2CORR_PK10R3_REFINED_TIP user=f42_mixed_uel.for datacheck interactive`
- **Compiler / Linker**: Intel(R) Fortran Compiler Classic 2021.13.0 Build 20240602_000000 / GNU ld 2.30.
- **Outcome**: `ANALYSIS DATACHECK COMPLETE` with **0 errors**.
- **Exit Code**: `0`.

---

## 6. Evaluation Framework (Quantitative Diagnostic Comparison)

Upon future authorized execution, the evaluation of `M2CORR_PK10R3_REFINED_TIP` will be conducted strictly as a quantitative diagnostic comparison against canonical H1 (`1389686.mmaster02`) and H2 (`1389687.mmaster02`):
1. **$RF_1 - U_1$ Trajectory**: Direct comparison across elastic ascent ($U_1 \le 0.010\text{ mm}$), peak load $RF_{1,\max}$ and corresponding displacement $U_{1,\text{peak}}$, and post-peak softening ($U_1 \in [0.015, 0.050\text{ mm}]$).
2. **Crack-Driving & Phase Fields**: Spatial distribution and maximum of committed strain energy $H(x,y)$ and phase field damage $d(x,y)$ at matched displacements ($U_1 = 0.005, 0.010, 0.0125, 0.020, 0.050\text{ mm}$).
3. **Localization Path**: Identification of damage band orientation and shear band propagation.
4. **Falsification Evaluation**: Rejection of arbitrary numeric PASS criteria in favor of verifying whether mesh refinement to $h/l_0 \le 0.15$ successfully overcomes non-local gradient resistance and activates phase degradation.

---

## 7. Dual-Channel Notification Status & Submission Gates

- **Transport Acknowledgement**:
  - Telegram API HTTPS Transport: `ACKNOWLEDGED` (HTTP 200)
  - Login Node MTA Mail Queue: `ACKNOWLEDGED` (Exit code 0)
- **Human Delivery Observation**:
  - `telegram_delivery_observed` = `false`
  - `email_delivery_observed` = `false`
- **Package Status**: `READY_FOR_FRESH_AUTHORIZATION`
- **Submission Gate**: `BLOCKED_PENDING_HUMAN_NOTIFICATION_RECEIPT_CONFIRMATION`

---

## 8. Scientific Governance & Preserved Invariants

```text
same_mesh_restart_validation = VALIDATED
history_transfer_rule_resolved = false
selected_production_history_operator = UNRESOLVED
nonmatching_transfer_algorithm_scientifically_unblocked = false
production_adaptive_accuracy_validation_scientifically_unblocked = false
PK10R1_topology_repair_required = true
email_delivery_observed = false
telegram_delivery_observed = false
```

```text
new_submission_authorized = false
qsub_called = false
qdel_called = false
qmove_called = false
git_commit_called = false
git_push_called = false
```
