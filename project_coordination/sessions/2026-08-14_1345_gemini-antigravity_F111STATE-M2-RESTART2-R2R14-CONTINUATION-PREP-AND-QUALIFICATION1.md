# Session Report: F111STATE-M2-RESTART2-R2R14-CONTINUATION-PREP-AND-QUALIFICATION1

- **Session Timestamp**: 2026-08-14 13:45 CEST
- **Agent**: Gemini Antigravity
- **Task ID**: `F111STATE-M2-RESTART2-R2R14-CONTINUATION-PREP-AND-QUALIFICATION1`
- **Scope**: Prepare and qualify candidate `M2STATE_FRACFIX_RESTART2R14` extending Mode-II displacement loading from $u_1 = 0.030000\text{ mm}$ to $u_1 = 0.050000\text{ mm}$ ($\Delta u_1 = 0.020000\text{ mm}$) starting from the verified terminal state of Job `1389325.mmaster02` on the unchanged `PK10R1` mesh.
- **Protocol Version**: 1
- **Status**: `QUALIFICATION_COMPLETE_AWAITING_AUTHORIZATION`

---

## 1. Executive Summary

1. **Candidate Objective**:
   - Starting from the verified terminal state of completed Job `1389325.mmaster02` (`M2STATE_FRACFIX_RESTART2R13`) at $u_1 = 0.030000\text{ mm}$, $RF_1 = 0.654334\text{ kN}$, $d_{\max} = 0.845700$, candidate `M2STATE_FRACFIX_RESTART2R14` continues the simulation on the unchanged `PK10R1` mesh up to $u_1 = 0.050000\text{ mm}$ to determine whether the global force peak and post-peak softening response are reached.

2. **Formulation & Architecture Preservation**:
   - **Staggered Architecture**: Preserves exact staggered UEL formulation (`U1`/`U3`: DOF 3 phase field, `U2`/`U4`: DOFs 1,2 displacement fields).
   - **Residual Vector**: Preserves the verified out-of-loop mechanical residual calculation `RHS(I,1) = -F_INT(I)`.
   - **Property ABI**: Preserves clean 6-slot real property array `PROPS = (0.015, 0.0027, 210.0, 0.3, 1.0e-7, 9612.0)`.
   - **Mesh Topology**: Unchanged `PK10R1` mesh (9,849 nodes, 9,612 physical elements: 9,588 quads, 24 tris).
   - **Dual-Channel Notifications**: Integrated `#PBS -m abe` email directives and Telegram shell trap `job_notifications.sh`.
   - **Guarded Wrapper**: `submit_m2state_fracfix_restart2r14.sh` with fail-closed manifest check and dry-run mode.

3. **Remote Qualification Evidence (Cluster `mlogin01`, Abaqus 2023)**:
   - **Package Manifest Integrity**: `ALL FILES MATCH MANIFEST SHA256: PASS`.
   - **Abaqus 2023 Datacheck**: `Abaqus JOB M2STATE_FRACFIX_RESTART2R14_DATACHECK COMPLETED` (Exit 0, 0 errors).
   - **Step 1 PhaseInit Solve**:
     - Prescribed displacement: $u_1 = 0.030000\text{ mm}$.
     - Transferred nodal phase field: $d(\mathbf{x}) \in [0.000623, 0.845716]$.
     - Transferred integration point history: $H(\mathbf{x}) \in [0.000000, 0.446824]$.
     - Source Terminal Reaction Force ($u_1 = 0.030\text{ mm}$): $0.654334\text{ kN}$.
     - Target Step 1 Reaction Force ($u_1 = 0.030\text{ mm}$): $0.654321\text{ kN}$.
     - Target Step 1 Bottom Sum Force: $-0.654321\text{ kN}$.
     - Absolute Force Difference: $0.000013\text{ kN}$.
     - Percentage Discrepancy: **`0.0020%`** (Tolerance $\le 2.0\%$).
     - Global Force Equilibrium: $RF_1(\text{RP}) + \sum RF_1(\text{bottom}) = +3.10 \times 10^{-9}\text{ kN}$ (Machine Zero!).
     - Bottom Transverse Balance: $\sum RF_2(\text{bottom}) = -3.61 \times 10^{-9}\text{ kN}$ (Machine Zero!).
   - **Guarded Submission Wrapper Dry-Run**: `DRY-RUN MODE: Package validated successfully. qsub call count = 0.`

---

## 2. Quantitative Handoff & Qualification Reconciliation Table

| Metric | Source Job `1389325.mmaster02` (Inc 19) | Target Candidate `M2STATE_FRACFIX_RESTART2R14` (Step 1) | Discrepancy / Balance | Verdict |
| :--- | :--- | :--- | :--- | :--- |
| **Displacement $u_1$** | $0.030000\text{ mm}$ | $0.030000\text{ mm}$ | $0.000000\text{ mm}$ | **EXACT_MATCH** |
| **Reaction Force $RF_1$** | $0.654334\text{ kN}$ | $0.654321\text{ kN}$ | $0.000013\text{ kN}$ (**0.0020%**) | **PASS** ($\le 2.0\%$) |
| **Bottom Sum $RF_1$** | N/A (runtime history) | $-0.654321\text{ kN}$ | Balanced to RP | **PASS** |
| **Global Equilibrium Residual** | $< 2.3 \times 10^{-9}\text{ kN}$ | $3.10 \times 10^{-9}\text{ kN}$ | Machine Zero | **PASS** |
| **Max Phase Field $d_{\max}$** | $0.845716$ | $0.845716$ | $0.000000$ | **EXACT_MATCH** |
| **Max History $H_{\max}$** | $0.446824\text{ kN/mm}^2$ | $0.446824\text{ kN/mm}^2$ | $0.000000$ | **EXACT_MATCH** |
| **Physical Elements** | 9,612 (PK10R1) | 9,612 (PK10R1) | 0 difference | **EXACT_MATCH** |
| **Total Nodes** | 9,849 | 9,849 (+ RP 99999) | 0 difference | **EXACT_MATCH** |
| **Abaqus 2023 Datacheck** | Pass (Exit 0) | Pass (Exit 0) | 0 errors | **PASS** |
| **Guarded Wrapper Dry-Run** | Pass | Pass | `qsub_call_count = 0` | **PASS** |

---

## 3. Package File Hashes (Manifest SHA256: `2e88b80156426bf73b78403214bf44dc69cec479cbddbbd9cfe24fc954f3c58d`)

| File Name | Size (Bytes) | SHA256 Hash |
| :--- | :--- | :--- |
| `M2STATE_FRACFIX_RESTART2R14.inp` | 4,975,191 | `2d46d03a110a113ec4e7fa2eb85fbf803b9fb756912301fdb0b7da98f828a2a5` |
| `f42_mixed_uel.for` | 16,683 | `3a18a9965d1d6a90890aa9dc8b1fa2b70f9a7aa9dd936d8d9b1c7dcabf1b88e1` |
| `M2STATE_FRACFIX_RESTART2R14.pbs` | 1,101 | `ef6443c984950ce434c264251cb1c95116741b6cae142bcad2d0fe2c0fb8d4a9` |
| `submit_m2state_fracfix_restart2r14.sh` | 797 | `7d79ff4df2fec49f69747a83d3e51f8a846cfffeff91b8d6fcb2d713c7bb61cb` |
| `validate_package_manifest.py` | 955 | `0a80e15967b57951a84ce432b036cb56ec236db5153fb50949d0cb74e5ba7903` |
| `job_notifications.sh` | 10,663 | `79fe7b9fc6fbfe29baaeafbe39a85bbd1ca93aee70c1d68378c85eb6bf5ff49e` |
| `STATE_TRANSFER_ARTIFACT.json` | 539 | `8bc3a504cb1a50a1168f047702f37c5ea2d8f9ffda5e5fb25d2efaa536b3f7bf` |
| `TRANSFER_MANIFEST.json` | 239 | `0507a216c5b967885b5d84877be15598165cf459dc47cf0fbf377f0a6b7d3da3` |
| `RESTART_ACCEPTANCE_CONTRACT.json` | 231 | `1e95c1a89f929bc2b882200dcda95191cf0ebda76c66cf17f694e9f9064c58cf` |
| `PACKAGE_MANIFEST.json` | 1,058 | `2e88b80156426bf73b78403214bf44dc69cec479cbddbbd9cfe24fc954f3c58d` |

---

## 4. Qualified Resource Contract for Proposed Submission

```text
candidate = M2STATE_FRACFIX_RESTART2R14
source_job = 1389325.mmaster02
target_mesh = PK10R1 (9,849 nodes, 9,612 physical elements)
handoff_displacement = 0.030000 mm
continuation_terminal_displacement = 0.050000 mm
cpus = 1
memory = 16 GB
walltime = 24:00:00
queue = entry_imfdfkmq
automatic_retry = false
```

- **Submission wrapper ready on cluster**:
  `/home/pr21vyci/projects/adaptive-remeshing/models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART2R14/submit_m2state_fracfix_restart2r14.sh`
- **Submission command (when explicitly authorized)**:
  `./submit_m2state_fracfix_restart2r14.sh --execute`
- **Qsub Call Count during this task**: `0` (Preparation and qualification only).
