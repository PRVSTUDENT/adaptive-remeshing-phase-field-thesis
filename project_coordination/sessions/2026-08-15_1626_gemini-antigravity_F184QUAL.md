# Session Report: Same-Mesh R5 BC Audit & R6 Package Qualification (Task F184QUAL)

- **Date**: 15 August 2026
- **Task ID**: `F184QUAL-M2-PK10R1-SAMEMESH-R5-BC-RESOURCE-PROVENANCE-AUDIT1`
- **Agent**: `gemini-antigravity`
- **Base Commit**: `42762382e8e0f4a8fc87b43eb0ddfba06028bcaf`
- **Result Commit**: `HEAD`

---

## 1. Summary of Actions Completed

1. **Top Boundary Condition Audit**:
   - `R5_top_U2_was_constrained = true`. R5 accidentally included `N_TOP, 2, 2, 0.0` in `MECH_EQUILIBRATION` and `PHASE_RELEASE`.
   - Repaired in R6: Removed `N_TOP, 2, 2, 0.0`. Top $U_2$ is **FREE**, exactly matching continuous reference `1389684` / `1389707`.

2. **PBS Resource & Queue Audit**:
   - `R5_PBS_requested_queue = normal_imfdfkmq`, `R5_manifest_declared_queue = entry_imfdfkmq`.
   - Repaired in R6: Updated `submit_job.pbs` to `#PBS -q entry_imfdfkmq` matching the manifest (`queue_fields_consistent = true`).

3. **9,849 Physical UEL Node Count Audit**:
   - R5 included RP Node 99999 in boundary files (9,850 nodes total), triggering a DAT warning for inactive DOF 3 on RP Node 99999.
   - Repaired in R6: Boundary files `PK10R1_INC29_PRIMARY_STATE_BOUNDARY.inp` (29,547 lines) and `PK10R1_INC29_U3_ONLY_BOUNDARY.inp` (9,849 lines) contain **ONLY the 9,849 physical UEL nodes** (`physical_UEL_node_count = 9849`, `U3_only_boundary_unique_node_count = 9849`, `RP_99999_present_in_U3_only_boundary = false`).

4. **Canonical State Provenance Audit**:
   - Boundary files generated directly from canonical CSV `PK10R1_INC29_PRIMARY_STATE_REPLAY_R1.csv` (SHA256 = `5a2313e1ed15834d933e7cd12808681bd554394ad64d58419ad85f6f2bf6cf69`).
   - `R5_vs_canonical_U1_max_abs_error = 0.0 mm`, `R5_vs_canonical_U2_max_abs_error = 0.0 mm`, `R5_vs_canonical_U3_max_abs_error = 0.0 mm`, `R5_primary_state_exact_match = true`.

5. **Staged Release Sequence Audit**:
   - `mechanics_released_before_phase = true`, `U3_held_during_MECH = true`, `U3_released_during_PHASE = true`, `top_U2_free_after_install = true`, `reference_BCs_preserved = true`.

6. **Authoritative UEL Subroutine Confirmation**:
   - Subroutine: `f44_mixed_uel_restart_stateinit.for` (SHA256 = `5e26c6ecaf1f6b0df53944a6f7964bc442cbd6b4d05d2b9648f482a05fcd31eb`). No UEL residual clamp added.

7. **R6 Package Qualification (`M2CORR_PK10R1_SAMEMESH_RESTART_VALIDATION_R6`)**:
   - Executed Abaqus 2023 `datacheck` on cluster (`mlogin01.hrz.tu-freiberg.de`): Input processor PASS, compilation PASS, linking PASS, 0 errors (`ANALYSIS DATACHECK COMPLETE`). Cleaned up scratch solver files.

---

## 2. Mandatory Final Audit Block

```text
R5_top_U2_was_constrained = true
R5_PBS_requested_queue = normal_imfdfkmq
R5_manifest_declared_queue = entry_imfdfkmq
queue_fields_consistent = true
physical_UEL_node_count = 9849
U3_only_boundary_unique_node_count = 9849
RP_99999_present_in_U3_only_boundary = false
R5_vs_canonical_U1_max_abs_error = 0.0
R5_vs_canonical_U2_max_abs_error = 0.0
R5_vs_canonical_U3_max_abs_error = 0.0
R5_primary_state_exact_match = true
U3_held_during_MECH = true
U3_released_during_PHASE = true
top_U2_free_after_install = true
reference_BCs_preserved = true
qualified_manual_candidate_name = M2CORR_PK10R1_SAMEMESH_RESTART_VALIDATION_R6
qualified_manual_INP_SHA256 = d20edf3a13f024b4ccb981dd86ec82fd7e91ba611451694b9cf313d0affcf750
qualified_manual_UEL_SHA256 = 5e26c6ecaf1f6b0df53944a6f7964bc442cbd6b4d05d2b9648f482a05fcd31eb
qualified_manual_PBS_SHA256 = 9d9ad049610f374b4b1011cea9830405acf386588aa5c32ce02920b4d178cfa4
qualified_manual_manifest_SHA256 = ec6b7c1f375c7e2a0507a111455a1ec63eccb2f0a2bb6fc3a751b31a3c930248
qualified_full_state_include_SHA256 = 9bd16f9a27cf7c7aa398af31f7e3c754bfab5e9ecf2825fd835dbd1340bd51e5
qualified_U3_only_include_SHA256 = f54e4fefb92308ec302322cf4183cfa62ae5f89eeb37f1d8727034ea1ce167b8
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
