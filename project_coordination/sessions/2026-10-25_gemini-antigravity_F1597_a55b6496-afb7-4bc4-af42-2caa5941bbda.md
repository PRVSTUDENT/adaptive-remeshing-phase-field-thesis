# F1597-CORRECT-PACKAGE72-STATE-TRANSFER controlled scientific step

Controller Run ID: a55b6496-afb7-4bc4-af42-2caa5941bbda
Stage: Complete

## 1. Verified Research Preparation Finding

- Reconciled completed R15 Job 1417298 (8 outer iterations Exit 0, 5.39e-11 mm displacement accuracy, 0 healing nodes, RF2 relaxed to 180.895 N with +0.357% reference parity).
- Classified R15 as `FULL_DISPLACEMENT_PASS__ACTIVE_SET_INCOMPLETE` due to 51 active nodes retaining driving forces exceeding 5e-8 kN/mm at the 8-iteration limit.
- Formulated and qualified Candidate Package 108 Revision 16 with outer active-set iteration ceiling expanded from 8 to 15 (B_max=20, tau_release=5e-8 kN/mm, tau_heal=1e-8), retaining 100% bitwise frozen production UEL and verified repaired unified 12-DOF UEL for complete active-set closure.
- Submitted Job 1417299.mmaster02.

Evidence: results/validation/preparation-a55b6496-afb7-4bc4-af42-2caa5941bbda.json
Status: PREPARATION_COMPLETE

## 2. Formulation & Qualification of Package 108 Revision 16 (R16)

- **Artifacts Created**:
  - `models/pandey_kumar_mode1/108_r16_c3_autonomous_active_set/f42_unified_12dof_active_set_uel.for` (SHA `ab0a5a71...`).
  - `models/pandey_kumar_mode1/108_r16_c3_autonomous_active_set/driver_r16_autonomous_continuation.py` (SHA `06dcb716...`).
  - `models/pandey_kumar_mode1/108_r16_c3_autonomous_active_set/M1_C3_ACTIVE_SET_R16_CONTINUATION.inp` (SHA `cfd1c98e...`).
  - `models/pandey_kumar_mode1/108_r16_c3_autonomous_active_set/M1_C3_ACTIVE_SET_R16_AUTHORIZATION.json` (SHA `e3e9fcfa...`).
  - `models/pandey_kumar_mode1/108_r16_c3_autonomous_active_set/submit_M1_C3_ACTIVE_SET_R16.pbs` (SHA `0725a1f3...`).
- **Preflight Datacheck**: Completed on cluster scratch `/scratch9/pr21vyci/runs/mode1_c3_active_set_continuation_r16/` with 0 errors (`M1_C3_ACTIVE_SET_R16 COMPLETED`).
- **Unit Tests**: `tests/unit/test_mode1_f1597_turn146_r16_qualification.py` (6/6 tests passed in 0.004s).

## 3. HPC Submission

- **PBS Job ID**: `1417299.mmaster02` (`M1_C3_ACTIVE_SET_R16`)
- **Queue**: `entry_imfdfkmq` -> `normal_imfdfkmq` (1 CPU, 16 GB, 8h)
- **Status**: Running (`S = R`) on compute node `mnode104`.

Turn complete. No unqualified HPC job submitted.

Finished
