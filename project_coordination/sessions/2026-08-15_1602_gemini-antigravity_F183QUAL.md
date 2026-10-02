# Session Report: Same-Mesh R4 Hash Audit & R5 Minimal Package Qualification (Task F183QUAL)

- **Date**: 15 August 2026
- **Task ID**: `F183QUAL-M2-PK10R1-SAMEMESH-R4-HASH-AND-IRREVERSIBILITY-AUDIT1`
- **Agent**: `gemini-antigravity`
- **Base Commit**: `42762382e8e0f4a8fc87b43eb0ddfba06028bcaf`
- **Result Commit**: `HEAD`

---

## 1. Summary of Actions Completed

1. **R3 vs R4 INP Hash & Staging Discrepancy Resolution**:
   - Re-hashed R3 and R4 INPs byte-for-byte: Both returned `412af27d129f3beb3123ed2417d232e74474c445c84546d666086dd8d9311055` (`R3_R4_INP_byte_identical = true`).
   - Confirmed `R3_MECH_U3_constrained = false` and `R4_MECH_U3_constrained = false`. F182's claim that R4 modified INP staging was false because the INP file was byte-identical.

2. **SV_PHASE Committed Definition & Stored Phase Audit**:
   - `SV_PHASE_COMMITTED` is declared as `DOUBLE PRECISION SV_PHASE_COMMITTED(100000)`. `SV_PHASE_array_length = 100000`.
   - Indexing: `PHYSIDX = JELEM` for phase elements (JTYPE 1 and 3). Exactly 1 scalar $D_{\text{avg}} = \frac{1}{n_{\text{nodes}}}\sum U_{3,i}$ stored per physical element (`SV_PHASE_entries_per_quad = 1`, `SV_PHASE_entries_per_tri = 1`).
   - `quad_stored_phase_max_abs_error = 0.0`, `tri_stored_phase_max_abs_error = 0.0`, `global_stored_phase_relative_L2_error = 0.0`.
   - Proved that the previous `0.017487` error reported in F182 was not a state inconsistency, but an comparison of Gauss-point interpolated phase $d(\xi_k, \eta_k)$ vs element-average scalar $D_{\text{avg}}$.

3. **F46 Nodal Irreversibility & Variational Consistency Audit**:
   - Lower bound source: `SV_PHASE_COMMITTED(PHYSIDX)` (element-average scalar).
   - `same_node_can_receive_different_bounds_from_adjacent_elements = true`. Shared nodes receive incompatible bounds from adjacent elements with different $D_{\text{avg}}$.
   - Variational consistency: `residual_modified_by_clamp = true`, `tangent_modified_consistently_with_clamp = false`, `Jacobian_consistent = false`, `constitutive_physics_changed = true`.

4. **Minimal Correction Strategy & R5 Package Qualification (`M2CORR_PK10R1_SAMEMESH_RESTART_VALIDATION_R5`)**:
   - `minimal_correction_strategy = A`: Keep $U_3$ constrained during `MECHANICAL_EQUILIBRATION` (Step 2) via `PK10R1_INC29_U3_ONLY_BOUNDARY.inp`, then release $U_3$ during `PHASE_RELEASE` (Step 3) using original authoritative UEL physics `f44`. No UEL residual modification is required or permitted.
   - Prepared `M2CORR_PK10R1_SAMEMESH_RESTART_VALIDATION_R5` with 4 steps: `STATE_INSTALL`, `MECH_EQUILIBRATION`, `PHASE_RELEASE`, `CONTINUATION`.
   - Executed Abaqus 2023 `datacheck` on cluster (`mlogin01.hrz.tu-freiberg.de`): Input processor PASS, compilation PASS, linking PASS, 0 errors (`ANALYSIS DATACHECK COMPLETE`). Cleaned up scratch solver files.

---

## 2. Mandatory Final Audit Block

```text
R3_INP_SHA256 = 412af27d129f3beb3123ed2417d232e74474c445c84546d666086dd8d9311055
R4_INP_SHA256 = 412af27d129f3beb3123ed2417d232e74474c445c84546d666086dd8d9311055
R3_R4_INP_byte_identical = true
R3_MECH_U3_constrained = false
R4_MECH_U3_constrained = false
SV_PHASE_array_length = 100000
SV_PHASE_entries_per_quad = 1
SV_PHASE_entries_per_tri = 1
SV_PHASE_physical_meaning = one scalar per physical element storing element-average nodal phase D_AVG = sum(U3_i)/n_nodes
quad_stored_phase_max_abs_error = 0.0
tri_stored_phase_max_abs_error = 0.0
global_stored_phase_max_abs_error = 0.0
nodal_lower_bound_source = SV_PHASE_COMMITTED(PHYSIDX)
same_node_can_receive_different_bounds_from_adjacent_elements = true
residual_modified_by_clamp = true
tangent_modified_consistently_with_clamp = false
Jacobian_consistent = false
original_model_uses_history_field_for_irreversibility = true
original_model_has_explicit_d_lower_bound = false
F46_adds_new_irreversibility_constraint = true
minimal_correction_strategy = A
qualified_manual_candidate_name = M2CORR_PK10R1_SAMEMESH_RESTART_VALIDATION_R5
qualified_manual_INP_SHA256 = b8b2d5c7cbd9a1790953bd2f4641d181391cbc4f082ddf591ca6f6af7560c866
qualified_manual_UEL_SHA256 = 5e26c6ecaf1f6b0df53944a6f7964bc442cbd6b4d05d2b9648f482a05fcd31eb
qualified_manual_PBS_SHA256 = 8ea29cec056118daa26e016e7d8a6910eb0a54c6d10bec34f4f61b5bb3701e05
qualified_manual_manifest_SHA256 = aedb8b487d7cc5ba604e1db2d02cc8dc4dab18e6bfaf5044e63722034cd33c32
datacheck_result = PASS
next_manual_same_mesh_validation_ready_for_authorization = true
native_restart_control_validation = PASS
same_mesh_restart_validation = PARTIALLY_VALIDATED
nonmatching_transfer_algorithm_scientifically_unblocked = false
production_adaptive_accuracy_validation_scientifically_unblocked = false
PK10R1_topology_repair_required = true
production_submission_ready_for_authorization = false
new_submission_authorized = false
qsub_called = false
qdel_called = false
qmove_called = false
```
