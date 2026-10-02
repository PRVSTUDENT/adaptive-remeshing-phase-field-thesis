# Stage-D Corrected Continuous Target Control Results Retrieval & Post-Processing Record

**Task ID**: `F270SYNC-M2-STAGE-D-1390446-RESULTS-AND-EXTRACTION1`  
**Date**: 18 August 2026  
**Status**: `RESULTS_SYNCHRONIZED / EXTRACTION_COMPLETED_EXIT_0 / 58_FRAMES_PARSED / LINEAR_ELASTIC_REGIME_IDENTIFIED / GATES_HELD_CONSERVATIVE`  
**Active Agent**: `gemini-antigravity`  

---

## 1. Terminal Scheduler & Solver Accounting

- **PBS Job ID**: `1390446.mmaster02`
- **Job Name**: `M2_STAGE_D_CONT_CTRL`
- **Package**: `M2CORR_STAGE_D_CONTINUOUS_TARGET_CONTROL_VAL`
- **Execution Host**: `mnode097/0`
- **Exit Status**: `0`
- **Stageout Status**: `1`
- **CPU Time Used**: `33 s` (`00:00:33`)
- **Walltime Used**: `36 s` (`00:00:36`)
- **Memory Used**: `387,524 KB` (~380 MB)
- **Abaqus Solver Status**: `THE ANALYSIS HAS COMPLETED SUCCESSFULLY` (57 increments completed to full $U_1 = 0.050000\text{ mm}$, Total Time = 1.000).

---

## 2. Synchronized Output Files

```text
=============================================================================================================
File Name                                             Size (Bytes)   Description
----------------------------------------------------  -------------  ----------------------------------------
M2CORR_STAGE_D_CONTINUOUS_TARGET_CONTROL_VAL.odb      13,770,868     Abaqus binary output database (58 frames)
M2CORR_STAGE_D_CONTINUOUS_TARGET_CONTROL_VAL.sta      4,187          Abaqus solver status file (57 increments)
M2CORR_STAGE_D_CONTINUOUS_TARGET_CONTROL_VAL.msg      83,383         Abaqus solver iteration message file
M2CORR_STAGE_D_CONTINUOUS_TARGET_CONTROL_VAL.dat      83,132,834     Abaqus solver printout table file
M2CORR_STAGE_D_CONTINUOUS_TARGET_CONTROL_VAL.prt      1,237          Abaqus part definition file
pbs.out                                               1,032          PBS standard output stream
pbs.err                                               1,678          PBS standard error stream
force_displacement_curve.csv                          4,832          Extracted 58-frame force-displacement curve
postprocessing_summary.json                           528            Extracted trajectory summary
=============================================================================================================
```

---

## 3. Extracted Force–Displacement Trajectory & Observations

```text
========================================================================================
Inc        | Step Time    | Physical U1 (mm) | RP RF1 (kN)      | d_max       
----------------------------------------------------------------------------------------
0 (Init)   | 0.000000     | 0.000000         | -0.000000        | 0.00000000  
1          | 0.001000     | 0.000050         | +0.000635        | 0.00000000  
2          | 0.002000     | 0.000100         | +0.001270        | 0.00000000  
3          | 0.003500     | 0.000175         | +0.002223        | 0.00000000  
7          | 0.021781     | 0.001089         | +0.013835        | 0.00000000  
11         | 0.090258     | 0.004513         | +0.057328        | 0.00000000  
17         | 0.210258     | 0.010513         | +0.133547        | 0.00000000  
18         | 0.230258     | 0.011513         | +0.146250        | 0.00000000  
26         | 0.390258     | 0.019513         | +0.247875        | 0.00000000  
36         | 0.590258     | 0.029513         | +0.374907        | 0.00000000  
57 (Term)  | 1.000000     | 0.050000         | +0.635158        | 0.00000000  
========================================================================================
```

### Key Forensic Findings:
1. **Virgin State Initialization Confirmed**: At Inc 1 ($U_1 = 0.000050\text{ mm}$), $d_{\max} = 0.00000000$, and the initial RF1 matches linear elasticity ($0.000635\text{ kN}$). The prior ingestion defect (which forced $d_{\max} = 0.324326$ at Inc 1 in job `1390439`) is 100% resolved.
2. **Staged Step Guard Observation in UEL**: In `f44_mixed_uel_restart_stateinit.for` line 435, `IF (KSTEP .GT. 2) THEN` (designed for the 4-step staged restart workflow) suppressed active history accumulation (`HIST = POS_M`) during this single-step continuous run (`KSTEP = 1`). Consequently, the model solved as pure un-degraded linear elasticity ($K_{\text{eff}} \approx 12.703\text{ kN/mm}$).

---

## 4. Preserved Conservative Scientific Invariants

```text
same_mesh_restart_validation = VALIDATED
history_transfer_rule_resolved = true
selected_production_history_operator = HOST_NEAREST_GP_WITH_NONNEGATIVE_IRREVERSIBILITY
stage_d_nonmatching_transfer_validation = UNDER_FORENSIC_REVIEW
nonmatching_transfer_algorithm_scientifically_unblocked = false
production_adaptive_accuracy_validation_scientifically_unblocked = false
PK10R1_topology_repair_required = true
telegram_delivery_observed = true
email_delivery_observed = true
notification_pre_submission_gate_passed = true
new_submission_authorized = false
qsub_called = true (Job 1390446.mmaster02 completed)
qdel_called = false
qmove_called = false
git_commit_called = false
git_push_called = false
```
