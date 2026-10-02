# Session Report: Mode-II Stage-E Donor Combined Controls Qualification Submission

**Session Date**: 19 August 2026  
**Agent**: `gemini-antigravity`  
**Task ID**: `F320SUB-M2-STAGE-E-DONOR-COMBINED-CONTROLS-SUBMISSION1`  
**Status**: `DUAL_LINEAGE_PROVEN / DATACHECK_PASSED / NOTIFICATION_PREFLIGHT_PASSED / JOB_SUBMITTED_AND_RUNNING`  

---

## 1. Summary of Actions & Provenance

1. **Dual-Lineage Derivation**:
   - Derivation A: Derived from `1391301.mmaster02` (`IA13_ISO`) by changing only $\Delta t_{\min}: 1.0\times 10^{-11} \to 5.0\times 10^{-12}\text{ s}$.
   - Derivation B: Derived from `1391302.mmaster02` (`DTMIN5E12_ISO`) by changing only $I_A: 12 \to 13$.
   - Verified that both derivations produce **100.0000% byte-identical files with identical SHA-256** (`14e86a073f4d6d1565a5893a0279e8d3fe7ad2dbeafda82c76a59dcbaec5e33d`).

2. **Pre-Submission Qualification**:
   - Mesh: 8,836 physical quads, 9,073 physical nodes (excl RP 99999).
   - UELs: 8,836 mechanical UELs + 8,836 phase UELs = 17,672 total UELs.
   - $\text{PROPS}(1..7) = (0.015, 0.0027, 210.0, 0.3, 1.0\times 10^{-7}, 8836.0, 0.0)$.
   - Subroutine: `f44_mixed_uel_restart_stateinit.for` SHA-256 `62e35f74bbeccd3f5b1ac67312b79211f4ccb75648ae20dbb8985cb577fe1aab`.
   - Datacheck: Interactive compile/link and datacheck passed on `tu_freiberg` (`DATACHECK_RC=0`).
   - Notifications: Preflight test passed for Email (`mailx`) and Telegram (`rc=0`).
   - Concurrency Guard: 0 running jobs $\to$ 1 job submitted $\to \le 2$ limit satisfied.

3. **Guarded Submission**:
   - **Exact PBS Job ID**: **`1391319.mmaster02`** (`M2E_D_COMB_VAL`).
   - Exec Host: `mnode098/0`, Queue: `normal_imfdfkmq`, Walltime: `24:00:00`.
   - Active Login Watcher: `PID 1213089` on `mlogin01`.
   - Emitted [`docs/experiment_records/F320SUB_M2_STAGE_E_DONOR_COMBINED_CONTROLS_SUBMISSION_RECORD.md`](file:///D:/Master%20thesis/Adaptive%20remeshing/docs/experiment_records/F320SUB_M2_STAGE_E_DONOR_COMBINED_CONTROLS_SUBMISSION_RECORD.md).

4. **Frozen Evaluation Criteria**:
   - Compare increment-by-increment and frame-by-frame against `1390876.mmaster02` across all 439 increments / 440 frames upon job completion.
   - Classification: `COMBINED_PATH_NEUTRAL_VALIDATED`, `COMBINED_ALTERS_EQUILIBRIUM_PATH`, `COMBINED_JOB_FAILED_BEFORE_QUALIFICATION`, or `UNRESOLVED`.

---

## 2. Preserved Scientific Gates

- `coarsened_stage_e_transfer_validation` = `VALIDATED`
- `refined_stage_e_transfer_validation` = `REFINED_STAGE_E_CONTINUATION_GATE_UNRESOLVED`
- `stage_e_continuous_baselines_validation` = `PARTIALLY_USABLE_UNDER_FORENSIC_REVIEW`
- `same_mesh_restart_validation` = `VALIDATED`
- `history_transfer_rule_resolved` = `true`
- `selected_production_history_operator` = `HOST_ISOPARAMETRIC_BILINEAR_WITH_LOCAL_GP_BOUNDS_CLAMP`
- `stage_d_nonmatching_transfer_validation` = `VALIDATED`
- `nonmatching_transfer_algorithm_scientifically_unblocked` = `true`
- `production_adaptive_accuracy_validation_scientifically_unblocked` = `false`
- `PK10R1_topology_repair_required` = `true`
- `telegram_delivery_observed` = `true`
- `telegram_human_receipt_confirmed` = `true`
- `email_delivery_observed` = `true`
- `email_human_receipt_confirmed = false / unverified`
- `notification_pre_submission_gate_passed` = `true`
- `new_submission_authorized` = `false`
- `qsub_called` = `true (Job 1391319.mmaster02 submitted under today's authorized directive)`
- `qdel_called` = `false`, `qmove_called` = `false`
- `git_commit_called` = `false`, `git_push_called` = `false`
