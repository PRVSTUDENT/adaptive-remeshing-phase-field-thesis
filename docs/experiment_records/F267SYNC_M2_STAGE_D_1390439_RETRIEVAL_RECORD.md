# Stage-D Continuous Target Control Results Retrieval & Extraction Record

**Task ID**: `F267SYNC-M2-STAGE-D-1390439-RESULTS-AND-EXTRACTION1`  
**Date**: 18 August 2026  
**Status**: `RESULTS_SYNCHRONIZED / EXTRACTION_COMPLETED_EXIT_0 / 63_FRAMES_PARSED / GATES_HELD_CONSERVATIVE`  
**Active Agent**: `gemini-antigravity`  

---

## 1. Terminal Scheduler & Solver Accounting

- **PBS Job ID**: `1390439.mmaster02`
- **Job Name**: `M2_STAGE_D_CONT_CTRL`
- **Package**: `M2CORR_STAGE_D_CONTINUOUS_TARGET_CONTROL_VAL`
- **Execution Host**: `mnode097/0`
- **Exit Status**: `0`
- **Stageout Status**: `1`
- **CPU Time Used**: `73 s` (`00:01:13`)
- **Walltime Used**: `76 s` (`00:01:16`)
- **Memory Used**: `460,684 KB` (~450 MB)
- **Abaqus Completion Message**: `THE ANALYSIS HAS COMPLETED SUCCESSFULLY`

---

## 2. Synchronized Output Files

```text
=============================================================================================================
File Name                                             Size (Bytes)   Description
----------------------------------------------------  -------------  ----------------------------------------
M2CORR_STAGE_D_CONTINUOUS_TARGET_CONTROL_VAL.odb      15,175,352     Abaqus binary output database (63 frames)
M2CORR_STAGE_D_CONTINUOUS_TARGET_CONTROL_VAL.sta      4,589          Abaqus solver status file (62 increments)
M2CORR_STAGE_D_CONTINUOUS_TARGET_CONTROL_VAL.msg      175,747        Abaqus solver iteration message file
M2CORR_STAGE_D_CONTINUOUS_TARGET_CONTROL_VAL.dat      92,613,751     Abaqus solver printout table file
M2CORR_STAGE_D_CONTINUOUS_TARGET_CONTROL_VAL.prt      1,237          Abaqus part definition file
pbs.out                                               1,032          PBS standard output stream
pbs.err                                               1,679          PBS standard error stream
force_displacement_curve.csv                          5,248          Extracted 63-frame force-displacement curve
postprocessing_summary.json                           528            Extracted trajectory summary
=============================================================================================================
```

---

## 3. Extracted Trajectory & Key Observables

```text
=============================================================================================================
Metric / Event                   Value                          Units / Details
-------------------------------  -----------------------------  ---------------------------------------------
Total Converged Increments       62                             Completed 100% time to U1 = 0.050 mm
Total ODB Frames                 63                             Frame 0 to Frame 62
Damage Initiation (d > 0.01)     U1 = 0.000050 mm               Linear elasticity prior to localized yielding
Peak Reaction Force (RP_RF1)     0.069092 kN                    Occurs at U1 = 0.019212 mm (d_max = 1.000)
Trajectory at U1 = 0.010212 mm   RP_RF1 = +0.054843 kN          d_max = 1.000000
Trajectory at U1 = 0.011212 mm   RP_RF1 = +0.060213 kN          d_max = 1.000000
Terminal Prescribed Load         RP_RF1 = +0.035753 kN          Occurs at U1 = 0.050000 mm (d_max = 1.000)
=============================================================================================================
```

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
qsub_called = true (Job 1390439.mmaster02 completed)
qdel_called = false
qmove_called = false
git_commit_called = false
git_push_called = false
```
