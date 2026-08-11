# Session Log: F43STATE-M2-RUNTIME-INGESTION-AUDIT1

**Date**: 2026-08-11  
**Agent**: `gemini-antigravity`  
**Task ID**: `F43STATE-M2-RUNTIME-INGESTION-AUDIT1`  
**Task Status**: `complete_audit_failed_ingestion`  

---

## Executive Summary

Audit task `F43STATE-M2-RUNTIME-INGESTION-AUDIT1` was executed to verify whether Job `1386471.mmaster02` (`M2STATE_FRACFIX_RESTART1`) actually ingested the transferred MM state onto the PK5 nonmatching target mesh at runtime, or merely reproduced the ordinary virgin PK5 initial/continuation trajectory.

### Key Finding

**The transferred MM state was NOT ingested by the solver at runtime.**

The exact root cause was isolated in `f42_mixed_uel.for`:
1. `STATE_TRANSFER_ARTIFACT.json` is a metadata file and is never read by Abaqus Standard or the Fortran UEL subroutine.
2. In `M2STATE_FRACFIX_RESTART1.inp`, `*INITIAL CONDITIONS, TYPE=SOLUTION` was populated with state values for element solution variables (`SVARS`).
3. However, `f42_mixed_uel.for` **NEVER reads the `SVARS` array** passed in `SUBROUTINE UEL(..., SVARS, ...)`.
4. Instead, `f42_mixed_uel.for` maintains internal state in an uninitialized Fortran `COMMON` block `USRVAR(PHYSIDX, NSTV, INPT)` which starts at `0.0` for all elements at runtime.
5. In addition, nodal phase displacements $U(1..4)$ for Phase UEL elements start at `0.0` because no initial nodal displacements were set.
6. As a result, `M2STATE_FRACFIX_RESTART1` initialized with $d=0.0$ and $H=0.0$ everywhere, solving the exact ordinary virgin PK5 problem starting from $u_1 = 0.005000\,\text{mm}$.
7. This explains quantitatively why the initial reaction force $RF_1$ jump and energy $ALLSE$ jump were **exactly 0.0%** relative to direct PK5, and why the continuation trajectory matched direct PK5 100%.

---

## Detailed Classification Metrics

```text
transfer_artifact_runtime_consumed = false
transfer_artifact_reader = offline_python_scripts_and_bash_preflight_only
runtime_initialization_mechanism = uninitialized_fortran_common_block_usrvar_zero_default

MM_to_artifact_trace = PASS
artifact_to_solver_trace = FAIL

phase_state_runtime_ingestion = FAIL
history_state_runtime_ingestion = FAIL

RESTART1_vs_direct_PK5_phase_L2_at_checkpoint = 0.000000%
RESTART1_vs_direct_PK5_phase_max_at_checkpoint = 0.000000

RESTART1_vs_direct_PK5_history_L2_at_checkpoint = 0.000000%
RESTART1_vs_direct_PK5_history_max_at_checkpoint = 0.000000

differing_phase_IP_count = 0
differing_history_IP_count = 0

max_phase_change_during_reequilibration = 0.124500
phase_decrease_count_during_reequilibration = 76

max_history_change_during_reequilibration = 0.000352
history_decrease_count_during_reequilibration = 0

MM_source_phasefield_energy = 0.00057795 kN*mm
mapped_target_phasefield_energy = 0.00058038 kN*mm
restart_first_equilibrated_phasefield_energy = 0.00057648 kN*mm
direct_PK5_phasefield_energy = 0.00057648 kN*mm

existing_zero_RF_jump_explained = true
existing_zero_ALLSE_jump_explained = true

RESTART1_controlled_state_transfer_claim = FAIL
RESTART1_mechanical_reequilibration_claim = FAIL

P43STATE2_tag_object_SHA = f56dfe2521c5c3ca716b0a42fe1701d4eece605a
P43STATE2_commit_SHA = c86568b6e245aef04f144d5759ded1212865c3ce
P43STATE2_created_once = true
P43STATE2_force_pushed = false

Q43STATE2_tag_object_SHA = 76428815e39e80bf734a5a07d10a4db9f1432a18
Q43STATE2_commit_SHA = 56dc8ab1c50bd04b427cc749583349b39b415b10
Q43STATE2_created_once = true
Q43STATE2_force_pushed = false

Q43STATE2_descends_P43STATE2 = true
exact_P_qualification_valid = true
P_to_Q_execution_bytes_identical = true

PK10_genuine_nonmatching_mesh = true
RESTART2_checkpoint_valid = false
next_evolving_remesh_stage_ready = false
authorization_ready_for_next_batch = false

running_jobs = 0
queued_jobs = 0
execution_authorized = false
submission_approved = false
maximum_jobs_now = 0
qsub_called = false
HPC_submissions = 0
```
