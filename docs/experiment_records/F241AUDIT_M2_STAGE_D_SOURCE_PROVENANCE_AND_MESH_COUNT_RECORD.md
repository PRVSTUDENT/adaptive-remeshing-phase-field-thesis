# Stage-D Source Provenance, Diagnostic String Correction & Mesh Counts Reconciliation Record

**Task ID**: `F241AUDIT-M2-STAGE-D-SOURCE-PROVENANCE-AND-MESH-COUNT-RECONCILIATION1`  
**Date**: 17 August 2026  
**Status**: `PROVENANCE_VERIFIED / DIAGNOSTIC_STRING_CORRECTED / MESH_COUNTS_RECONCILED / PACKAGE_QUALIFIED / READY_FOR_FRESH_AUTHORIZATION`  
**Active Agent**: `gemini-antigravity`  

---

## 1. Source-State Provenance & Byte-by-Byte Verification

A complete audit of `models/generated/mode_ii/production_state_transfer_batch/M2CORR_STAGE_D_NONMATCHING_TRANSFER_VAL/STAGE_D_COMMITTED_STATE.bin` (SHA-256: `0ff4b468cbc6af6bedcaba025dd557d65cc715ced86a87f2a4324bd3d58234c5`) confirms:

1. **Source Simulation & ODB**: `M2CORR_H1_FREEU2_FULL_U050` (PBS Job ID: `1389686.mmaster02`).
2. **Step & Frame**: `Step-1` (`ShearStep`), **Frame 29** (Increment 29), physical shear displacement $U_1 = \mathbf{0.0101433\text{ mm}}$.
3. **Source Fields Transferred**:
   - **Nodal Displacements**: $U_1 \in [-0.000008, 0.010143]\text{ mm}$, $U_2 \in [-0.004277, 0.010725]\text{ mm}$.
   - **Nodal Phase Field**: $d \in [0.000000, 0.285585]$ ($d_{\max} = 0.285585$).
   - **Committed History $\mathcal{H}$**: Source peak occurs on **Element 5832, GP 3** at $(-0.000528, -0.000528)\text{ mm}$ with $H = \mathbf{0.848870\text{ kN/mm}^2}$.
4. **Binary Structure (4,000,016 bytes)**:
   - **Record 1 (800,000 bytes)**: Fortran sequential header `800000`, 100,000 double-precision entries for `SV_PHASE_COMMITTED`, tail `800000`.
   - **Record 2 (3,200,000 bytes)**: Fortran sequential header `3200000`, $100,000 \times 4$ double-precision entries for `SV_H_COMMITTED` (Column-Major order), tail `3200000`.
5. **Target Sample Slot Verification**:
   - Target Element 4371 GP 4: $H = \mathbf{0.848870\text{ kN/mm}^2}$ (mapped from Source EID 5832 GP3, distance $40\text{ nm}$).
   - Target Element 4372 GP 3: $H = 0.321009\text{ kN/mm}^2$.
   - Target Element 4465 GP 2: $H = 0.219181\text{ kN/mm}^2$.
   - Target Element 4466 GP 1: $H = 0.457134\text{ kN/mm}^2$.
   - Far-field Boundary Element 8836 GP 4: $H = 0.000001\text{ kN/mm}^2$.

---

## 2. Diagnostic String Correction in UEL

- **Issue**: In F240, `.msg` logged `SUCCESS: Imported restart state from PK10R1 state file`.
- **Root Cause**: Stale string literal in subroutine `UEXTERNALDB` inherited during template adaptation from R7.
- **Resolution**: Updated `WRITE(*,*) 'SUCCESS: Imported restart state from Stage-D state file'` in `f44_mixed_uel_restart_stateinit.for`.
- **Validation**: Re-running `abaqus datacheck` on `mlogin01` verified `.msg` now outputs:
  ```text
  SUCCESS: Imported restart state from Stage-D state file
  ```

---

## 3. H1 Source Mesh Counts Reconciliation

Direct inspection of `M2CORR_H1_FREEU2_FULL_U050.inp` and `M2CORR_H1_FREEU2_FULL_U050.odb`:

| Mesh Hierarchy Entity | Count | ID Range | Notes |
| :--- | :--- | :--- | :--- |
| **Physical Nodes** | **`12,383`** | `1 .. 12383` | Domain nodes on physical quadrilateral grid |
| **Reference Nodes** | **`1`** | `99999` | Rigid body kinematic coupling control node |
| **Total Nodes in INP** | **`12,384`** | `1 .. 99999` | Physical nodes + RP node |
| **Layer 1 (Phase UEL, `TYPE=U1`)** | **`12,064`** | `1 .. 12064` | $N_{\text{phys}} = 12,064$, primary DOF $U_3 = d$ |
| **Layer 2 (Mech UEL, `TYPE=U2`)** | **`12,064`** | `12065 .. 24128` | $N_{\text{phys}} = 12,064$, primary DOFs $U_1, U_2$ |
| **Total Stacked UELs** | **`24,128`** | `1 .. 24128` | $2 \times N_{\text{phys}}$ |
| **Visualization Overlay Elements**| **`12,064`** | `24129 .. 36192` | Postprocessing overlay (CPE4) in full ODB |
| **Total Elements in ODB** | **`36,192`** | `1 .. 36192` | Layer 1 + Layer 2 + Visualization |

---

## 4. Package Qualification Evidence

- **UEL Compilation (`abaqus make`)**: Completed with **`Exit 0`** on `mlogin01`.
- **Abaqus Datacheck (`abaqus datacheck`)**: Completed with **`Exit 0`** on `mlogin01`.
- **State Ingestion Log**: Verified `SUCCESS: Imported restart state from Stage-D state file` in `.msg`.

---

## 5. Frozen Cryptographic Manifest (SHA-256)

From [`models/generated/mode_ii/production_state_transfer_batch/M2CORR_STAGE_D_NONMATCHING_TRANSFER_VAL/manifest.json`](file:///D:/Master%20thesis/Adaptive%20remeshing/models/generated/mode_ii/production_state_transfer_batch/M2CORR_STAGE_D_NONMATCHING_TRANSFER_VAL/manifest.json):

```json
{
  "job_name": "M2CORR_STAGE_D_NONMATCHING_TRANSFER_VAL",
  "file_hashes_sha256": {
    "inp": "685c43504cb33d11c90a936d59bfe7f59b0a75139e50ede8671fd7c6f6501639",
    "uel": "f7e25fffe0d75a68551899c2a710c2ac110934c44a781a6669a73b59d57cde07",
    "primary_state_bc_include": "bcc1ccecc85c9691a7dffdb087ff79a977034fe1d844e0677bf97e032297b622",
    "u3_only_bc_include": "023ff2a97bddf1471267e71a6b326965ec62e5023fde8708b468cb372d938e18",
    "committed_state_bin": "0ff4b468cbc6af6bedcaba025dd557d65cc715ced86a87f2a4324bd3d58234c5",
    "launcher": "a376e0dfd3a4cbbfc92921710c598df6736d78676cd155f76cac610e2f6397a5",
    "source_mesh_generator": "3adaa1453d36c72018aec119edb92f7fcdfff6ed77aad9f2c07de702f2d5102d",
    "transfer_pipeline_script": "3885c711b40365d877e0e8d4f21d498854bee284b0c93e2f76b5326c2205105d"
  }
}
```

---

## 6. Preserved Scientific Gates & Multi-Agent Invariants

```text
same_mesh_restart_validation = VALIDATED
history_transfer_rule_resolved = true
selected_production_history_operator = HOST_NEAREST_GP_WITH_NONNEGATIVE_IRREVERSIBILITY
nonmatching_transfer_algorithm_scientifically_unblocked = false
production_adaptive_accuracy_validation_scientifically_unblocked = false
PK10R1_topology_repair_required = true
telegram_delivery_observed = true
email_delivery_observed = true
notification_pre_submission_gate_passed = true
M2CORR_STAGE_D_NONMATCHING_TRANSFER_VAL = READY_FOR_FRESH_AUTHORIZATION
```

```text
new_submission_authorized = false
qsub_called = false
qdel_called = false
qmove_called = false
git_commit_called = false
git_push_called = false
```
