# Session Report: Mode-II Stage-E Replacement Continuous Baselines Batch Preparation & Submission

**Session Date**: 18 August 2026  
**Agent**: `gemini-antigravity`  
**Task ID**: `F300PREP-M2-STAGE-E-REPLACEMENT-CONTINUOUS-BASELINES-PREPARATION-AND-SUBMISSION1`  
**Status**: `QUALIFIED_AND_SUBMITTED / PBS_IDS_PRESERVED / BATCH_RUNNING / WATCHER_VERIFIED`  

---

## 1. Summary of Actions & Provenance

1. **Prepared Replacement Continuous E1 Baseline Packages**:
   - **Refined Replacement**: `M2CORR_STAGE_E_REFINED_TARGET_MINIMAL_CONTINUATION_VAL`
     - Mesh: 33,600 physical quads, 34,027 nodes, $h_{\min} = 0.002000\text{ mm}$.
     - Controls: $I_0=4, I_R=8, I_P=9, I_C=16, I_L=10, I_G=4, I_S=50, I_A=12$, $\Delta t_{\min}=1.0\times 10^{-9}\text{ s}$, default Line 2 growth factors.
   - **Coarsened Replacement**: `M2CORR_STAGE_E_COARSENED_TARGET_MINIMAL_CONTINUATION_VAL`
     - Mesh: 8,200 physical quads, 8,417 nodes, $h_{\min} = 0.004000\text{ mm}$.
     - Controls: $I_0=4, I_R=8, I_P=9, I_C=16, I_L=10, I_G=4, I_S=50, I_A=12$, $\Delta t_{\min}=1.0\times 10^{-9}\text{ s}$, default Line 2 growth factors.

2. **Executed Pre-Submission Qualification Suite**:
   - One-difference manifests against default baselines `1390527` and `1390528`: PASSED (only $I_A: 5 \to 12$ differs scientifically).
   - Fortran subroutine UEL SHA-256 (`62e35f74bbeccd3f5b1ac67312b79211f4ccb75648ae20dbb8985cb577fe1aab`): PASSED.
   - Subroutine compilation & linking with `intel/2024.2.0` (ifort): PASSED.
   - Abaqus Datachecks on cluster for both models: PASSED (0 errors, 3 expected warnings each).
   - Launcher script validation (entry queue, 16 GB, -m abe): PASSED.
   - Notification preflight on `mlogin01`: PASSED (`rc=0` email and Telegram).

3. **Guarded Batch Submission**:
   - Submitted both jobs simultaneously via `qsub`.
   - Preserved exact PBS Job IDs:
     - Refined Replacement: **`1390829.mmaster02`** (Running on `mnode097/0`)
     - Coarsened Replacement: **`1390830.mmaster02`** (Running on `mnode097/1`)
   - Enforced HPC concurrency rule: exactly 2 running jobs.
   - Verified login-node watcher PID `1213089` active on `mlogin01`.

---

## 2. Preserved Scientific Gates

- `stage_e_continuous_baselines_validation` = `PARTIALLY_USABLE_UNDER_FORENSIC_REVIEW`
- `same_mesh_restart_validation` = `VALIDATED`
- `history_transfer_rule_resolved` = `true`
- `selected_production_history_operator` = `HOST_ISOPARAMETRIC_BILINEAR_WITH_LOCAL_GP_BOUNDS_CLAMP`
- `stage_d_nonmatching_transfer_validation` = `VALIDATED`
- `nonmatching_transfer_algorithm_scientifically_unblocked` = `true`
- `production_adaptive_accuracy_validation_scientifically_unblocked` = `false`
- `PK10R1_topology_repair_required` = `true`
- `new_submission_authorized` = `false`
- `qdel_called` = `false`, `qmove_called` = `false`
- `git_commit_called` = `false`, `git_push_called` = `false`
