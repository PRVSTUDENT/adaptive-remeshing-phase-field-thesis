# Task F1515 Session Report: Investigate & Implement Intelligent PBS Queue Selection for Method C Experiments

**Date**: 16 October 2026  
**Agent**: Gemini Antigravity  
**Task ID**: `F1515-INVESTIGATE-AND-IMPLEMENT-INTELLIGENT-PBS-QUEUE-SELECTION`  
**Starting Commit**: `d01613e3`  
**Governance Protocol**: Protocol Version 2  

---

## 1. Executive Summary & Core Findings

Task F1515 investigated whether PBS Pro natively supports automatic earliest-feasible execution queue selection across distinct hardware pools accessible to user `pr21vyci` on the TU Freiberg HPC cluster (`mmaster02`), evaluated earliest-start forecasting feasibility without dummy probe submissions, designed and implemented an optional `AutoQueue` policy for `Invoke-Mode1Execution.ps1`, clarified the PBS scheduler decision hierarchy, and verified the preservation of the two active queued same-mesh control jobs (`1414558.mmaster02` and `1414563.mmaster02`).

### Key Discoveries:
1. **PBS Pro Native Routing vs User-Level Routing**:
   - **No Native Dynamic Load Balancing Across Pools**: PBS routing queues (`entry_imfdfkmq`, `entryq`) evaluate `route_destinations` in strict static sequential order based solely on job resource requests (`walltime`, `ncpus`, `mem`) and ACLs. PBS Pro does **not** simulate scheduler reservations or query downstream queue depths at routing time.
   - **Stationary Execution Placement**: Once a job is routed to an execution queue (`normal_imfdfkmq`, `shortq`, etc.), the job is stationary. PBS Pro has no native mechanism to dynamically migrate queued jobs across execution queues or hardware pools based on backfill opportunities or earlier start times.
   - **Conclusion**: Any dynamic earliest-start selection across distinct hardware pools must occur at the client/orchestration layer prior to `qsub`.

2. **Empirical Queue & Node Pool Comparison**:
   - **Dedicated IMFD Pool (`extension2`)**:
     - Nodes: 10 nodes (`mnode097`..`106`), 16 CPUs/node (160 total), 748 GB RAM/node.
     - `normal_imfdfkmq`: Priority **1000**, max walltime 336h. Currently 10 running jobs (160/160 CPUs full), **2 queued jobs** (our jobs `1414558` and `1414563` at positions #1 and #2).
     - `short_imfdfkmq`: Priority 50, max walltime 12h. Shares the exact same 10 nodes. Moving to it would lower priority 20-fold with zero additional node headroom.
   - **General University Pool (`main`)**:
     - Nodes: 96 nodes (`mnode001`..`096`), 40 CPUs/node (3,840 total), 181 GB RAM/node.
     - `shortq`: Priority 75, max walltime 12h. Currently 9 running, **83 queued** (+20 held; 103 total in short queues).
     - `mediumq`: Priority 40, max walltime 36h. Currently 5 running, **11 queued**.
     - `longq`: Priority 10, max walltime 168h. Currently 198 running, **402 queued**.
   - **Verdict**:
     Even though the general cluster pool has 3,840 CPUs, `shortq` has an 83-job backlog at Priority 75. In contrast, `normal_imfdfkmq` has Priority 1000 and only 2 queued jobs. `entry_imfdfkmq` is empirically superior and strongly favored.

3. **Earliest-Start Forecasting Feasibility**:
   - Standard non-admin users have `query_other_jobs = False`. Standard users cannot query running jobs' start times or remaining walltimes to compute an exact deterministic start time without dummy probe submissions.
   - However, **heuristic queue congestion scoring** using `Priority - 10.0 * Queued + 1.5 * IdleCPUs` is lightweight, deterministic, and operates with zero dummy submissions.

4. **Implementation of `AutoQueue`**:
   - Developed `scripts/hpc/mode1_queue_selector.py` with full queue modeling, walltime filtering, and congestion scoring.
   - Integrated optional `-AutoQueue` switch into `scripts/hpc/Invoke-Mode1Execution.ps1`.
   - Verified that under both `-DryRun` and `-VerifyOnly`, `AutoQueue` evaluates candidate queues, selects `entry_imfdfkmq` (score 1030.0 vs -395.0 for `shortq`), and preserves all once-only accounting and safety invariants.

5. **Active Job Preservation**:
   - Both jobs `1414558.mmaster02` and `1414563.mmaster02` remain safely queued in `normal_imfdfkmq` at queue positions #1 and #2. Zero cancellation, migration, or re-submission occurred.

---

## 2. PBS Scheduler Decision Hierarchy Clarification

The PBS Pro scheduler decision hierarchy on `mmaster02` operates across five distinct layers:

```
[1. Submission Layer]
  - User passes -q <queue> (or defaults to server default_queue = entryq)
  - Target queue inspected (Route vs Execution)

[2. Routing Layer (Synchronous at Submission)]
  - Route queue evaluates route_destinations in fixed declaration order
  - Filters by: ACLs, requested walltime, memory, ncpus
  - First matching execution queue accepted; job permanently assigned
  - NO dynamic queue-depth or backfill inspection occurs here

[3. Queue Placement & Node Matching (Qlist)]
  - Execution queue assigns default_chunk.Qlist (e.g. normal_imfdfkmq)
  - Scheduler matches job chunks against eligible nodes where resources_available.Qlist contains job Qlist:
      * normal_imfdfkmq -> mnode097..106 (extension2 pool, 160 cpus)
      * shortq / mediumq / longq -> mnode001..096 (main pool, 3840 cpus)
  - Nodes outside placement set are filtered out (yielding "Placement set too small: Qlist mismatch")

[4. Priority Sorting Layer]
  - Scheduler sorts eligible queued jobs across each execution queue using:
      job_sort_formula = queue_priority + (eligible_time / 3600.0) + adminp
  - normal_imfdfkmq: base priority 1000 (+ eligible_time hours)
  - shortq: base priority 75
  - mediumq: base priority 40
  - longq: base priority 10

[5. Dispatch & Backfill Layer]
  - Evaluated every scheduler_iteration (600 seconds = 10 minutes)
  - Top priority jobs receive future resource reservations based on running job walltimes
  - Backfilling (backfill_depth = 10) dispatches lower-priority jobs ONLY if they fit into
    idle slots without delaying the reserved start time of top-priority jobs
  - When running jobs complete, top queued jobs on eligible nodes dispatch immediately
```

---

## 3. Empirical Hardware & Queue Comparison Table

| Metric / Dimension | Dedicated IMFD `normal_imfdfkmq` | Dedicated IMFD `short_imfdfkmq` | General Cluster `shortq` | General Cluster `mediumq` | General Cluster `longq` | Test Queue `testq` |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Submission Route** | `entry_imfdfkmq` | `entry_imfdfkmq` | `entryq` | `entryq` | `entryq` | `testq` |
| **Queue Type** | Execution | Execution | Execution | Execution | Execution | Execution |
| **From Route Only** | `True` | `True` | `True` | `True` | `True` | `False` |
| **Queue Priority** | **1000** | 50 | 75 | 40 | 10 | 125 |
| **Max Walltime** | 336 hours | 12 hours | 12 hours | 36 hours | 168 hours | 4 hours |
| **Node Pool** | `extension2` | `extension2` | `main` | `main` | `main` | `hybrid` |
| **Node Hardware** | 10 nodes (160 cpus, 748 GB) | 10 nodes (160 cpus, 748 GB) | 96 nodes (3840 cpus, 181 GB) | 96 nodes (3840 cpus, 181 GB) | 96 nodes (3840 cpus, 181 GB) | 10 ext2 + 3 fatnodes |
| **Running Jobs** | 10 (160 cpus, 100% full) | 0 | 9 (1060 cpus) | 5 (700 cpus) | 198 (721 cpus) | 0 |
| **Queued Jobs** | **2** (`1414558`, `1414563`) | 0 | **83** (+20 held) | 11 | **402** (+2 held) | 0 |
| **User Eligibility** | `t2-dl-rights-hpc_hw_kieferams` | `t2-dl-rights-hpc_hw_kieferams` | `t2-dl-rights-hpc_user` | `t2-dl-rights-hpc_user` | `t2-dl-rights-hpc_user` | `t2-dl-rights-hpc_user` |
| **Dispatch Score (1h)** | **1030.0 (Winner)** | 100.0 | -395.0 | 290.0 | -3650.0 | 125.0 |
| **Disqualification (24h)**| Feasible (336h max) | **DISQUALIFIED (12h)** | **DISQUALIFIED (12h)** | Feasible (36h max) | Feasible (168h max) | **DISQUALIFIED (4h)** |

---

## 4. Verification & Testing

1. **Unit Test Suite Authoring**:
   - Authored `tests/unit/test_mode1_f1515_intelligent_queue_selection.py` covering:
     * `test_native_pbs_queue_definitions_and_routing_limits` (PASS)
     * `test_score_queue_walltime_filtering` (PASS)
     * `test_score_queue_priority_and_congestion_dynamics` (PASS)
     * `test_select_best_queue_live_snapshot_favors_dedicated_hardware` (PASS)
     * `test_scheduler_decision_hierarchy_and_non_migration_invariants` (PASS)
     * `test_autoqueue_cli_json_interface` (PASS)
   - Result: **6/6 PASS** in 0.20s.

2. **Full Active Regression Battery**:
   - Ran `pytest` across all active tasks (F1507 through F1515):
     * F1507 Evaluate Release & Hold (5/5 PASS)
     * F1508 Isolate Release & Hold (6/6 PASS)
     * F1510 Audit Same-Mesh State (5/5 PASS)
     * F1511 Complete Same-Mesh Control & Validate Inverse State (6/6 PASS)
     * F1512 Reconcile Data & Audit Clipped Reconstruction (5/5 PASS)
     * F1513 Offline Diagnostics & Decision Rules (4/4 PASS)
     * F1514 Diagnose PBS Queue & Placement Architecture (5/5 PASS)
     * F1515 Intelligent Queue Selection (6/6 PASS)
   - Total: **42/42 PASS** in 1.61s.

3. **PowerShell CLI Integration Verification**:
   - `Invoke-Mode1Execution.ps1 -ManifestPath ... -DryRun`: Default mode preserved (PASS).
   - `Invoke-Mode1Execution.ps1 -ManifestPath ... -AutoQueue -DryRun`: Evaluates queue and outputs:
     `AUTO_QUEUE_SELECTION: selected 'entry_imfdfkmq' (target: normal_imfdfkmq, score: 1030.0, details: Priority=1000, Queued=2 (penalty -20), Running=10, IdlePoolCPUs=0 (bonus +0), Dedicated=IMFD-FKM)` (PASS).
   - `Invoke-Mode1Execution.ps1 -ManifestPath ... -AutoQueue -VerifyOnly`: Technical preflight verified (PASS).

---

## 5. Ledger & Artifact Summary

- **New Source Files**:
  * `scripts/hpc/mode1_queue_selector.py` (Intelligent queue selection & scoring engine)
  * `tests/unit/test_mode1_f1515_intelligent_queue_selection.py` (Unit tests, 6/6 PASS)
- **Modified Scripts**:
  * `scripts/hpc/Invoke-Mode1Execution.ps1` (Added optional `-AutoQueue` switch)
- **Queued PBS Jobs Preserved**:
  * `1414558.mmaster02` (`M1_MC_C1_1_SM`, 1 CPU, 8 GB, 1h, lumped projection $d_{\max} = 0.3045$)
  * `1414563.mmaster02` (`M1_MC_C1_1_SMC`, 1 CPU, 8 GB, 1h, consistent inverse $d_{\max} = 0.3423$)
- **Gate Status**: `GATE_6B_PASS__STAGE_C1_0_CLOSED_PASSED__STAGE_C1_1_SAMEMESH_DIAGNOSTIC_BRACKET_QUEUED__GATE_6C_HOLD`.
