# Mode-II Canonical Committed State Provenance Recovery & NM1 Artifact Repair Record

**Task ID**: `F197RECOVER-M2-CANONICAL-COMMITTED-STATE-PROVENANCE-AND-NM1-REPAIR1`  
**Date**: 16 August 2026  
**Status**: `PROVENANCE RESOLVED / RP DEFECT REPAIRED / COMMITTED HISTORY UNRESOLVED`  
**Active Agent**: `gemini-antigravity`  

---

## 1. Executive Summary

This record resolves the critical provenance contradiction regarding `PK10R1_INC29_SOURCE_STATE.bin` (`28e0fc1c...`), establishes the exact binary layout requirements of the restart UEL, explains why integration-point history was not saved in the continuous ODB, details the technical repair of the Reference Point (RP) boundary contamination defect in the `NM1` state transfer tooling, and reclassifies all generated artifacts conservatively.

---

## 2. Canonical Committed-State Provenance Resolution

### Provenance Audit of `PK10R1_INC29_SOURCE_STATE.bin` (`28e0fc...`)
- **File Path**: `models/generated/mode_ii/production_control_batch/M2CORR_PK10R1_SAMEMESH_RESTART_VALIDATION_R6/PK10R1_INC29_SOURCE_STATE.bin`
- **File Size**: **1,055 bytes**
- **SHA256**: `28e0fc1c6b02a4e6013cea23f38dacfea0e2afaf52d92239d9d694bb2e55e66e`
- **Payload Structure**: 128-byte ASCII header (`PK10R1_INC29_STATE_HEADER_V1.0_...`) followed by 927 null bytes.
- **Root Cause of Historical Misclassification**:
  - The 1,055-byte file was originally synthesized during Stage F140 as a placeholder file to enable Fortran compile/link checks.
  - In subsequent task coordination logs and manifests (F174, F188, F189, F192), the hash `28e0fc...` was referenced as `"immutable_committed_state_bin_sha256"` and mistakenly treated as an authoritative capture of internal state from `1389684.mmaster02`.
  - **Correction**: The file `PK10R1_INC29_SOURCE_STATE.bin` (`28e0fc...`) is a **placeholder header only** and contains zero physical internal history values ($\mathcal{H} = 0, d_{\text{avg}} = 0$).

---

## 3. Authoritative Binary Layout Analysis from UEL Source Code

From `models/generated/mode_ii/production_control_batch/M2CORR_PK10R1_SAMEMESH_RESTART_VALIDATION_R6/f44_mixed_uel_restart_stateinit.for`:

```fortran
      PARAMETER(N_CAPACITY=100000)
      DOUBLE PRECISION SV_PHASE_COMMITTED(N_CAPACITY)
      DOUBLE PRECISION SV_H_COMMITTED(N_CAPACITY,4)
...
      READ(99) SV_PHASE_COMMITTED
      READ(99) SV_H_COMMITTED
```

- **Data Types**: `DOUBLE PRECISION` (8 bytes per value, IEEE 754 float64).
- **Array 1 (`SV_PHASE_COMMITTED`)**: Dimension `100,000` $\implies 800,000\text{ bytes}$.
  - Record structure: 4-byte header (`800000`) + 800,000 bytes + 4-byte footer (`800000`) = **800,008 bytes**.
- **Array 2 (`SV_H_COMMITTED`)**: Dimension `(100,000, 4)` $\implies 400,000\text{ doubles} = 3,200,000\text{ bytes}$.
  - Record structure: 4-byte header (`3200000`) + 3,200,000 bytes + 4-byte footer (`3200000`) = **3,200,008 bytes**.
- **Total Expected File Size**: $800,008 + 3,200,008 = \mathbf{4,000,016\text{ bytes}}$.
- **Fortran Memory Layout**: Column-major (`SV_H(1,1), ..., SV_H(100000,1), ..., SV_H(100000,4)`).

---

## 4. Investigation of Committed History Availability in Preserved ODBs

An offline Python inspection (`odbAccess`) was executed on `M2CORR_PK10R1_CONTINUOUS_U050_STATECAPTURE_R1.odb` (`1389707.mmaster02`):
- **Stored Field Outputs at Frame 29**:
  - `RF` (Reaction force vector, nodal)
  - `U` (Displacement vector $U_1, U_2, U_3$, nodal)
- **Element Output Fields**: None (`*ELEMENT OUTPUT` was not requested in the continuous job deck).
- **Outcome**: The internal Fortran common-block integration-point array $\mathcal{H}_n$ was never dumped to the ODB.
- **Status**:
  - `H_committed_available = false`
  - `SV_PHASE_committed_available = false`
  - `canonical_committed_state_recovery = UNRESOLVED`

---

## 5. Scientific Clarification on Remeshing Irreversibility

In phase-field fracture mechanics:
1. **Temporal Irreversibility**: At a fixed material point $\mathbf{X}$ over time, $\dot{d}(\mathbf{X}, t) \ge 0$ and $\dot{\mathcal{H}}(\mathbf{X}, t) \ge 0$.
2. **Spatial Transfer / Projection**: When transferring state from mesh $\mathcal{M}_A$ to nonmatching mesh $\mathcal{M}_B$, pointwise inequality $\mathcal{H}_B(\mathbf{x}) \ge \mathcal{H}_A(\mathbf{x})$ is not a standard finite-element relation without a mathematically defined projection operator.
3. **Non-negativity**: $\mathcal{H} \ge 0$ is a trivial lower bound, not irreversibility.
4. **Governing Status**: `history_transfer_rule_resolved = false`.

---

## 6. Technical Repair of NM1 Reference Point (RP) Contamination

### Defect Identified in F195
In F195, auxiliary control Node 6562 (Reference Point at $(0.0, 0.5)$) was passed into the spatial FE search engine, resulting in spurious $U_1, U_2, U_3$ interpolation and improper Dirichlet BC generation (spurious DOF 3 and locked vertical dilation $U_2$).

### Tooling Repairs Executed
1. `src/state_transfer/primary_field_transfer.py`:
   - Added explicit `auxiliary_node_ids` handling.
   - Auxiliary/RP nodes are completely excluded from spatial element search (`auxiliary_nodes_FE_interpolated = 0`).
   - RP node receives exact scalar handoff displacement $u_{1,\text{handoff}} = 0.010143300518393517\text{ mm}$, with $U_2 = \text{None}$ and $U_3 = \text{None}$.
2. `src/state_transfer/restart_artifact_generator.py`:
   - `STATE_INSTALL_BOUNDARY.inp`: Prescribes $U_1, U_2, U_3$ on physical mesh nodes (1..6561). On RP node 6562, writes ONLY $U_1$, leaving $U_2$ free and omitting DOF 3.
   - `U3_ONLY_BOUNDARY.inp`: Excludes RP node 6562 completely.

### Verification of Physical Node Mapping Post-Repair
- `target_physical_nodes` = **6561**
- `target_auxiliary_nodes` = **1** (Node 6562)
- `physical_nodes_mapped` = **6561 (100.00%)**
- `auxiliary_nodes_FE_interpolated` = **0**
- `unmapped_physical_nodes` = **0**
- `fallback_physical_nodes` = **0**
- `max_mapping_residual` = **$1.665\times 10^{-16}\text{ mm}$**

---

## 7. Artifact Reclassification & Hashes

| Artifact Path | Old SHA256 | New SHA256 | Classification |
| :--- | :--- | :--- | :--- |
| `models/.../TARGET_NM1_MESH.inp` | `30bff1db...` | `30bff1db...` | **`VALID`** |
| `models/.../TARGET_NM1_INC29_PRIMARY_STATE.csv` | `a9b9f16f...` | `f48d15d4d466aa2c5f3e492be32f18d099a21e5bb697bf994b92a6923ee9a89d` | **`TECHNICALLY_REPAIRED`** |
| `models/.../TARGET_NM1_INC29_STATE_INSTALL_BOUNDARY.inp` | `c54fd06e...` | `61220882b6eb9cb6b4942d99cf03cbcdc2327af41ce3fc8dd7110a1c6565bc77` | **`TECHNICALLY_REPAIRED`** |
| `models/.../TARGET_NM1_INC29_U3_ONLY_BOUNDARY.inp` | `83c44fdf...` | `9f2350539807c86f31e727f6e95cbdfdc5aa608f9f8e03d0489c53174221fe8b` | **`TECHNICALLY_REPAIRED`** |
| `models/.../TARGET_NM1_INC29_SOURCE_STATE.bin` | `a85e32a9...` | `a85e32a9...` | **`INVALID_HISTORY_PAYLOAD`** |
| `models/.../TARGET_NM1_INC29_TRANSFER_MANIFEST.json` | `fe830b06...` | `075a3d255ae998f7c5ca50551e87643d3922f7fc4f9def85133fbc7e79c7d847` | **`TECHNICALLY_REPAIRED`** |
| `runs/.../F195_NONMATCHING_TRANSFER_DRYRUN_DIAGNOSTICS.json` | `b8598e73...` | `da48dfa5713b927ae5c84cd1f26ff94d858425745508bed01c4d21cb1869a83b` | **`TECHNICALLY_REPAIRED`** |
