# Mode-II Stage-D Nonmatching Transfer Smooth-H Staged Restart Diagnostic Submission Record

**Task ID**: `F277SUB-M2-STAGE-D-NONMATCHING-TRANSFER-SMOOTH-H-SUBMISSION1`  
**Date**: 18 August 2026  
**Status**: `JOB_SUBMITTED / SCHEDULER_RUNNING / OPERATOR_QUALIFIED / DUAL_CHANNEL_NOTIFICATIONS_ACTIVE / GATES_HELD_CONSERVATIVE`  
**Active Agent**: `gemini-antigravity`  

---

## 1. Mathematical Invariant & Bookkeeping Audit Resolution

### A. H1 Mesh Provenance (1389686.mmaster02)
- **Physical Quads**: `12,064 elements`
- **Physical Mesh Nodes**: `12,383 nodes` (12,350 unique geometric coordinates + 33 duplicated slit crack-face nodes along $y = 0, x \le 0$)
- **Reference Point (RP)**: Node `99999`
- **Source State**: Accepted Frame 29 / Increment 29 ($U_1 = 0.0101433005\text{ mm}$, $RP\_RF_1 = 0.122822\text{ kN}$, $d_{\max} = 0.28558478$)

### B. Phase-Field Residual Units Propagation
- **Weak Form**:
  $$R_i^d = \int_\Omega \left[\left(\frac{G_c}{\ell_0} + 2\mathcal{H}\right)d - 2\mathcal{H}\right] N_i \, d\Omega + \int_\Omega G_c \ell_0 \nabla d \cdot \nabla N_i \, d\Omega$$
- **Units in 2D Plane Strain (unit thickness $t = 1.0\text{ mm}$)**:
  - $\text{Term 1}: [\text{kN/mm}^2] \times [-] \times [\text{mm}^2] = [\mathbf{kN}] \quad (= [\text{J/mm}])$
  - $\text{Term 2}: [\text{kN}] \times [1/\text{mm}] \times [1/\text{mm}] \times [\text{mm}^2] = [\mathbf{kN}] \quad (= [\text{J/mm}])$
- **Single-Element Numerical Verification**:
  - Evaluated on test quad ($0.01\times 0.01\text{ mm}$, $d = [0.1, 0.1, 0.2, 0.2]$, $\mathcal{H} = 0.5\text{ kN/mm}^2$):
    $$\mathbf{R}^d = [-2.309167 \times 10^{-5}, \; -2.309167 \times 10^{-5}, \; -1.805833 \times 10^{-5}, \; -1.805833 \times 10^{-5}] \, \mathbf{kN}$$
  - $\sum R_i^d = -8.230000 \times 10^{-5}\text{ kN}$.

### C. Mathematical Definition of Evaluated History Operators
1. **Operator 1: `HOST_NEAREST_GP` (Historical Control `1390279`)**:
   - $\mathcal{H}(\mathbf{x}_{\text{tgt}}) = \mathcal{H}_D(\mathbf{x}_{\text{GP}, i^*}), \quad i^* = \arg\min_i \|\mathbf{x}_{\text{tgt}} - \mathbf{x}_{\text{GP}, i}\|$.
   - Sampled Peak $\mathcal{H} = 0.848870\text{ kN/mm}^2$, Max Intra-Element Jump = $0.740684\text{ kN/mm}^2$.
2. **Operator 2: `HOST_ISOPARAMETRIC_BILINEAR_CLAMPED` (Submitted Diagnostic `1390454`)**:
   - Extrapolates 4 donor GPs to 4 vertices $\mathbf{H}_D^{\text{node}} = \mathbf{E}\mathbf{H}_D^{\text{GP}}$, evaluates bilinear field $\mathcal{H}(\xi, \eta) = \sum N_i H_{D, i}^{\text{node}}$, and clamps to local donor GP bounds $[\min_j H_{D, j}^{\text{GP}}, \max_j H_{D, j}^{\text{GP}}]$ with $\max(0, \cdot)$.
   - Sampled Peak $\mathcal{H} = 0.660654\text{ kN/mm}^2$, Max Intra-Element Jump = $0.445804\text{ kN/mm}^2$ ($39.8\%$ jump reduction).
   - $100\%$ exact constant and linear field reproduction in natural space; guarantees non-negativity and prevents extrapolation overshoot.
3. **Operator 3: `HOST_CONSERVATIVE_MAX_PRESERVING_RECONSTRUCTION`**:
   - Evaluated accuracy/conservatism tradeoff: Documented that enforcing nominal donor maximum across non-coincident target points artificially elevates driving force in low-gradient background quads.

---

## 2. Package Architecture & Single-Difference Manifest

- **Package Directory**: `models/generated/mode_ii/production_state_transfer_batch/M2CORR_STAGE_D_NONMATCHING_TRANSFER_VAL_SMOOTH_H/`
- **Target Mesh**: 8,836 physical quads, 9,073 nodes (identical to `1390279.mmaster02`).
- **Mapped State**:
  - Mapped $(u_1, u_2)$ installed from `STAGE_D_PRIMARY_STATE_BOUNDARY.inp` (identical to `1390279`).
  - Mapped $d$ installed from `STAGE_D_PRIMARY_STATE_BOUNDARY.inp` (identical to `1390279`).
  - **Single Difference**: `STAGE_D_COMMITTED_STATE.bin` history record generated using Operator 2 (`HOST_ISOPARAMETRIC_BILINEAR_CLAMPED`).
- **UEL Formulation**: Explicit Mode 1 architecture (`PROPERTIES=7`, `PROPS(7)=1.0`).
- **Staged Sequence**: 4-Step (`STATE_INSTALL` $\to$ `MECH_EQUILIBRATION` $\to$ `PHASE_RELEASE` $\to$ `CONTINUATION`).

### SHA-256 Checksums:
```json
{
  "M2CORR_STAGE_D_NONMATCHING_TRANSFER_VAL_SMOOTH_H.inp": "8205f98bd0fdbeeca283a460e8f5ebcf05c52d9cdafa00a3e76d6eda4bbf6f1d",
  "MODE_STAGED.flag": "dc1fe8e9a76f03a0b032af5a7fe247d3df41e396d19bf6c0212500c6a0aaba23",
  "STAGE_D_COMMITTED_STATE.bin": "fe885df1c2f32466d9f10c82465bafc55f334bbb43048750d84244524d0d7ea9",
  "STAGE_D_PRIMARY_STATE_BOUNDARY.inp": "bcc1ccecc85c9691a7dffdb087ff79a977034fe1d844e0677bf97e032297b622",
  "STAGE_D_U3_ONLY_BOUNDARY.inp": "023ff2a97bddf1471267e71a6b326965ec62e5023fde8708b468cb372d938e18",
  "f44_mixed_uel_restart_stateinit.for": "863090488269b5cf14b244ec405727b47aee9329b91146e72f67499443d08062",
  "one_difference_scientific_manifest.json": "a8620ca74d0c8896b20836e54a44c13eb9af95aa16d5ae3a084907349a4d5a4c",
  "submit_job.pbs": "14a9f2d1a4f636d01f21174a83ac56d085b1d03bd7d16b8aca90bbabe100521d"
}
```

---

## 3. Remote Qualification & Submission Evidence

- **Compilation & Linking**: Intel Fortran 2021.13.0 + GCC 11.4.0 exit 0.
- **Abaqus Standard Datacheck**: Completed with **Exit 0** (`Abaqus JOB M2CORR_STAGE_D_NONMATCHING_TRANSFER_VAL_SMOOTH_H COMPLETED`).
- **Dual-Channel Preflight Smoke Test**:
  - Email: `rc=0` (pr21vyci@mailserver.tu-freiberg.de via mailx)
  - Telegram: `rc=0` (HTTP 200 OK)
- **Submission Details**:
  - **PBS Job ID**: **`1390454.mmaster02`**
  - **Queue / Host**: `entry_imfdfkmq` $\to$ `normal_imfdfkmq`, running on `mnode097/0`
  - **Resources**: `select=1:ncpus=1:mem=16gb`, `walltime=24:00:00`
  - **Sidecar Daemon**: Active (`PID 811775` on `mlogin01`)

---

## 4. Preserved Conservative Scientific Invariants

```text
same_mesh_restart_validation = VALIDATED
history_transfer_rule_resolved = false (UNDER_FORENSIC_REVIEW)
selected_production_history_operator = HOST_NEAREST_GP_WITH_NONNEGATIVE_IRREVERSIBILITY (PROVISIONAL)
stage_d_nonmatching_transfer_validation = UNDER_FORENSIC_REVIEW
nonmatching_transfer_algorithm_scientifically_unblocked = false
production_adaptive_accuracy_validation_scientifically_unblocked = false
PK10R1_topology_repair_required = true
telegram_delivery_observed = true
email_delivery_observed = true
notification_pre_submission_gate_passed = true
new_submission_authorized = true (Single diagnostic job 1390454.mmaster02 submitted)
qsub_called = true (Job 1390454.mmaster02 active)
qdel_called = false
qmove_called = false
git_commit_called = false
git_push_called = false
```
