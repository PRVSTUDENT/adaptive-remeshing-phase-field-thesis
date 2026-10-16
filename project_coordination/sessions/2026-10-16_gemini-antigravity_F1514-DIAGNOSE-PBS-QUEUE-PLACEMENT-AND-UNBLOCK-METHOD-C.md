# Session Report: F1514 — Diagnose PBS Queue Placement and Unblock Method C Experiments

**Date:** 16 October 2026  
**Agent:** Gemini Antigravity  
**Task ID:** `F1514-DIAGNOSE-PBS-QUEUE-PLACEMENT-AND-UNBLOCK-METHOD-C`  
**Starting Commit:** `22e66305`  
**Phase:** `STAGE_C1_1_NONMATCHING_STATE_TRANSFER_SAME_MESH_CONTROL_EVALUATION`  
**Gate Status:** `GATE_6B_PASS__STAGE_C1_0_CLOSED_PASSED__STAGE_C1_1_SAMEMESH_DIAGNOSTIC_BRACKET_QUEUED__GATE_6C_HOLD`  

---

## 1. Executive Summary & Epistemic Diagnostics

This session conducted an exhaustive, read-only empirical investigation into the PBS scheduler architecture, queue placement restrictions, node pool allocations, and Abaqus licensing to conclusively determine why the two Method C diagnostic control jobs (`1414558.mmaster02` and `1414563.mmaster02`) remain in state `Q`:

1. **Decoding the Scheduler Comment:**
   - Detailed job record:
     ```
     comment = Not Running: Placement set is too small: Insufficient amount of resource: Qlist (normal_imfdfkmq != adminq,gpuq,longq,mediumq,shortq,normal_imfdcpuq,testq,normal_stofatq,qpulongq,gpulongq,teachingq)
     estimated.exec_vnode = (mnode099[0]:ncpus=1:mem=8388608kb)
     estimated.start_time = Tue Oct 20 08:27:51 2026
     ```
   - **Root Cause Isolated:** This comment is an informational PBS placement-set filter log, **not** an error, user hold, or syntax defect. PBS checks all compute nodes in the cluster. Nodes `mnode001` through `mnode096` (`nodetype = main`) have `Qlist = adminq,gpuq,longq,mediumq,shortq`, which do not match `normal_imfdfkmq`. Only nodes `mnode097` through `mnode106` (`nodetype = extension2`) have `Qlist` containing `normal_imfdfkmq`.
   - On those 10 dedicated extension2 nodes, **100% of all 160 CPUs are currently assigned to 10 running jobs** (16/16 CPUs on every single node). Therefore, available CPUs in `normal_imfdfkmq` currently equals zero.
2. **Conclusive Root Cause Distinctions:**
   - **Insufficient Eligible Node Resources:** **YES, PRIMARY BOTTLENECK**. Exactly 160 of 160 CPUs across all 10 eligible nodes are occupied.
   - **Queue-Specific Placement Restrictions:** **YES**. The job is restricted by its execution queue's `default_chunk.Qlist` to the 10 extension2 nodes.
   - **Per-User or Per-Queue Limits:** **NO**. User `pr21vyci` has 0 running CPUs (limit: 640 CPUs, 4 TB RAM). Queue `normal_imfdfkmq` has no `max_run` limit.
   - **Scheduler Priority / Fair-Share Delays:** **NO**. In `normal_imfdfkmq`, there are exactly 2 queued jobs (`Queued: 2`). Our two jobs are the **TOP TWO** jobs in the entire queue.
   - **Abaqus License Restrictions:** **NO**. Directly queried `/cluster/application/abaqus/2023/Commands/abaqus licensing lmstat -a`:
     ```
     Users of standard: (Total of 300 licenses issued; Total of 74 licenses in use)
     ```
     Exactly **226 Abaqus Standard licenses are free and available**. Licensing is completely unconstrained.
3. **Queue Alternatives & Hardware Pool Evaluation:**
   - **`entry_imfdfkmq` vs `normal_imfdfkmq`:**
     * `entry_imfdfkmq` is a Route queue (`queue_type = Route`) with destinations `normal_imfdfkmq,short_imfdfkmq`. It possesses **no** compute nodes of its own. It routes directly to `normal_imfdfkmq`.
   - **`short_imfdfkmq`:**
     * Execution queue (`from_route_only = True`, max walltime 12h, `default_chunk.Qlist = short_imfdfkmq`).
     * It shares the **exact same 10 nodes** (`mnode097`..`106`). Since those nodes are 100% full, `short_imfdfkmq` has zero idle CPUs as well.
     * Furthermore, `short_imfdfkmq` has `Priority = 50`, whereas `normal_imfdfkmq` has `Priority = 1000`. Routing to `short_imfdfkmq` would reduce priority 20-fold.
   - **General Cluster Queues (`entryq` -> `shortq`, `mediumq`, `longq`):**
     * User `pr21vyci` has group `t2-dl-rights-hpc_user` and can access `entryq`, which maps to `mnode001`..`096`.
     * However, the general queues are severely backlogged: `shortq` has 83 queued jobs; `mediumq` has 11 queued jobs; `longq` has 402 queued jobs. Migrating would lose the top-of-queue priority and add days of queue waiting.
4. **Preservation of Existing Jobs:**
   - Both jobs `1414558.mmaster02` and `1414563.mmaster02` are preserved in the scheduler without modification, requeueing, migration, or cancellation.
   - As the top two queued jobs in `normal_imfdfkmq`, they will be the very next jobs dispatched the moment any running job releases resources on `mnode097`..`106`.
5. **Clarification of PBS Default Queue Handling:**
   - Server-level default queue is `default_queue = entryq`.
   - All Mode-I submission scripts and wrappers explicitly pass `#PBS -q entry_imfdfkmq` and `qsub -q entry_imfdfkmq`, deliberately bypassing the server default to target the dedicated IMFD-FKM hardware pool.

---

## 2. Cluster Hardware and Queue Architecture Comparison Table

| Attribute | `normal_imfdfkmq` | `short_imfdfkmq` | `entry_imfdfkmq` | General `shortq` / `longq` |
| :--- | :---: | :---: | :---: | :---: |
| **Queue Type** | Execution | Execution | Route | Execution |
| **Priority** | **1000** | 50 | 10 | 75 (`shortq`), 10 (`longq`) |
| **Max Walltime** | 336:00:00 (14 days) | 12:00:00 (12 h) | 336:00:00 | 12:00:00 / 168:00:00 |
| **Node Pool** | `mnode097`..`mnode106` | `mnode097`..`mnode106` | None (Routing) | `mnode001`..`mnode096` |
| **Node Architecture** | `extension2` (10 nodes) | `extension2` (10 nodes) | N/A | `main` (96 nodes) |
| **CPUs per Node** | 16 CPUs (160 total) | 16 CPUs (160 total) | N/A | 40 CPUs (3,840 total) |
| **RAM per Node** | 748 GB | 748 GB | N/A | 181 GB |
| **Qlist Attribute** | `normal_imfdfkmq` | `short_imfdfkmq` | N/A | `adminq,gpuq,longq,mediumq,shortq` |
| **Current Assigned CPUs** | **160 / 160 (100% full)** | **160 / 160 (100% full)** | N/A | 1,060 / 721 assigned |
| **Current Queued Jobs** | **2 (our 2 jobs)** | 0 | 0 | 83 (`shortq`), 402 (`longq`) |
| **User Access Group** | `t2-dl-rights-hpc_hw_kieferams` | `t2-dl-rights-hpc_hw_kieferams` | `t2-dl-rights-hpc_hw_kieferams` | `t2-dl-rights-hpc_user` |

---

## 3. Dedicated Extension2 Node Inventory (`mnode097`..`mnode106`)

All 10 nodes are 100% assigned to running jobs as verified by `pbsnodes`:

| Node Name | Sockets/CPUs | Total RAM | Assigned CPUs | Running PBS Job ID | Node Qlist |
| :--- | :---: | :---: | :---: | :---: | :--- |
| `mnode097` | 16 | 748 GB | 16 / 16 | `1414506.mmaster02` (16 cpus) | `normal_imfdfkmq,short_imfdfkmq,testq` |
| `mnode098` | 16 | 748 GB | 16 / 16 | `1414507.mmaster02` (16 cpus) | `normal_imfdfkmq,short_imfdfkmq,testq` |
| `mnode099` | 16 | 748 GB | 16 / 16 | `1410506.mmaster02` (16 cpus) | `normal_imfdfkmq,short_imfdfkmq,testq` |
| `mnode100` | 16 | 748 GB | 16 / 16 | `1414508.mmaster02` (16 cpus) | `normal_imfdfkmq,short_imfdfkmq,testq` |
| `mnode101` | 16 | 748 GB | 16 / 16 | `1414509.mmaster02` (16 cpus) | `normal_imfdfkmq,short_imfdfkmq,testq` |
| `mnode102` | 16 | 748 GB | 16 / 16 | `1414515.mmaster02` (16 cpus) | `normal_imfdfkmq,short_imfdfkmq,testq,teachingq` |
| `mnode103` | 16 | 748 GB | 16 / 16 | `1414510.mmaster02` (16 cpus) | `normal_imfdfkmq,short_imfdfkmq,testq,teachingq` |
| `mnode104` | 16 | 748 GB | 16 / 16 | `1414511.mmaster02` (16 cpus) | `normal_imfdfkmq,short_imfdfkmq,testq,teachingq` |
| `mnode105` | 16 | 748 GB | 16 / 16 | `1414513.mmaster02` (16 cpus) | `normal_imfdfkmq,short_imfdfkmq,testq,teachingq` |
| `mnode106` | 16 | 748 GB | 16 / 16 | `1414514.mmaster02` (16 cpus) | `normal_imfdfkmq,short_imfdfkmq,testq,teachingq` |

---

## 4. Scientific Baseline & Nodal Ground Truth Assessment

1. **Status of Existing Baseline Artifacts:**
   - Continuous fine-mesh baseline Job 1412465 (14,483 FEs) has its 21 GB ODB (`M1_MB_CORRECTED_PROPAGATION_14K.odb`) preserved on cluster scratch.
   - However, the deck requested `*NODE OUTPUT, NSET=N_RP` only. The ODB contains no interior nodal displacements $(u_x, u_y)$ and no nodal DOF 3 phase field.
2. **Minimal Additional Baseline Requirements:**
   - To obtain exact ground-truth interior displacements and nodal damage at $u = 0.005000\,\text{mm}$, a 2,000-increment run with `*NODE OUTPUT` across all nodes would be required.
   - However, this run is **not** currently an execution blocker:
     * Macroscopic force ($RF_2 = 661.7254\,\text{N}$), external work ($W_{\text{ext}} = 1.691029\,\text{mJ}$), stored elastic energy ($1.654313\,\text{mJ}$), fracture energy ($0.036786\,\text{mJ}$), total energy ($1.691099\,\text{mJ}$), tip element average damage ($\bar{d}_{661} = 0.318142$), and peak history ($H_{\max} = 0.773272\,\text{kN/mm}^2$) are already bitwise reconciled and established.
     * The two queued same-mesh controls directly test whether the Step 1 static re-equilibration + Step 2 release-and-hold maintains equilibrium.
     * Only if the outcome is inconclusive (Case D of the codified decision matrix) would an enriched baseline run be necessary.
3. **Formulation & Cycle Status:**
   - Production UEL [`f42_mixed_uel.for`](file:///D:/Master%20thesis/Adaptive%20remeshing/models/pandey_kumar_mode1/49_method_c_stage_c1_1_nonmatching_transfer/f42_mixed_uel.for) (`CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6`) remains bitwise frozen.
   - Authentic 4-panel mesh-and-phase comparison figure preserved: [`fig_mode1_method_c_stage_c1_1_mesh_and_phase_transfer.png`](file:///D:/Master%20thesis/Adaptive%20remeshing/results/figures/mode1_method_c_gate_c1/fig_mode1_method_c_stage_c1_1_mesh_and_phase_transfer.png).
   - Method C stage: **Stage C1-1, nonmatching state-transfer qualification** (2,906 $\to$ 14,483 FEs).
   - Qualified sequential cycles: **0**.
   - Forward continuation and Stage C1-2 remain strictly **BLOCKED** at Gate 6C.

---

## 5. Deliverables & Regression Suite

- **Unit Test Suite Authored:**
  - `tests/unit/test_mode1_f1514_diagnose_pbs_queue_and_placement_architecture.py` (5/5 PASS).
  - Full 36-test regression battery across Tasks F1507–F1514: **36/36 PASS**.
- **Coordination State Updated:**
  - `project_coordination/CURRENT_STATE.md`
  - `project_coordination/ACTIVE_TASK.json`
  - `project_coordination/TASK_LEDGER.csv`
  - `project_coordination/ARTIFACT_REGISTRY.csv`
  - `project_coordination/ACTIVE_SESSION.json` (released)
