# Method C Case 3: Job-1 Coarse Baseline Solve Execution and Preflight Qualification Report

**Date:** 20 November 2026  
**Task ID:** `METHOD-C-CASE3-JOB1-COARSE-SOLVE`  
**Goal ID:** `METHOD_C_INCREMENTAL_ADAPTIVE_REMESHING_V1`  
**Author:** Gemini Antigravity (Operating sequentially with Codex)  
**Master Goal Status:** `OPEN`  
**Predecessor Review:** `HND-METHOD-C-CASE3-PREP-002` (Officially Approved)  
**Execution Adapter:** `scripts/hpc/Invoke-Mode1Execution.ps1`  
**PBS Submission Status:** Accepted & Queued as Job `1424711.mmaster02` (`M1_MC_C3_JOB1`)  
**PBS Accounting:** Consumed 1 of 1 authorized (Cumulative 62 -> 63)  

---

## 1. Executive Summary

Following independent structured review approval under `HND-METHOD-C-CASE3-PREP-002` (confirming closure of all three preparation gaps against commit `ff496aaa5`), the Job-1 coarse baseline solve for the Pandey & Kumar (2025) Section 4.3 benchmark (Rectangular Notched Plate with Central Hole and Pins) has been qualified and submitted to the TUBAF HPC cluster (`mmaster02`).

The submission was executed strictly through the guarded controller pipeline (`scripts/hpc/Invoke-Mode1Execution.ps1`) using manifest `models/pandey_kumar_mode1/290_method_c_case3/METHOD_C_CASE3_JOB1_AUTHORIZATION.json`. Prior to submission reservation, full technical preflight and Abaqus 2023 datachecks were verified on the cluster login node with Intel Fortran Compiler Classic (`ifort` 2021.13.0) and the bitwise frozen UEL (`CE8D5EDC...`). PBS accepted the job as **`1424711.mmaster02`** in queue `normal_imfdfkmq` (routed from `entry_imfdfkmq`). Dual-channel notifications (email and Telegram) were confirmed active, the observables extraction script was authored and staged, and the complete 10-suite Method C unit test suite verified at **51/51 PASS (100%)**.

---

## 2. Technical Preflight and Datacheck Verification

Prior to live job submission, the candidate package was staged to `/scratch9/pr21vyci/runs/mode1_290_method_c_case3/` and qualified:

1. **Bitwise Frozen UEL Compilation**:
   - Subroutine: `f42_mixed_uel.for` (`CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6`).
   - Compiler: Intel(R) Fortran Compiler Classic `ifort` 2021.13.0 with automatic CPU dispatch.
   - Result: Successful compilation and linking into `standard.exe` without errors.
2. **Abaqus 2023 Datacheck Execution**:
   - Input Deck: `PK_METHOD_C_CASE3_COARSE_JOB1.inp` (14,013 layered elements = 3 layers $\times$ 4,671 physical elements, 4,813 nodes, 14,437 variables).
   - Execution: Configured with `scratch=/tmp` to isolate node-local scratch I/O from PanFS write-lock contention.
   - Datacheck Artifact: `/scratch9/pr21vyci/runs/mode1_290_method_c_case3/PK_METHOD_C_CASE3_COARSE_JOB1_DC.dat`.
   - Verified Terminal Marker: `ANALYSIS DATACHECK COMPLETE`, 0 errors, 0 warnings during datacheck, 0 syntax violations.
3. **Dual-Channel Notification Transport**:
   - Shell Traps: `job_notifications.sh` sourced and initialized with terminal exit trap.
   - Submission Notification: Verified delivery to email (`pr21vyci@mailserver.tu-freiberg.de`) and Telegram bot (`api.telegram.org` acknowledgement `ok=true`, HTTP 200).
   - Technical Preflight Result: `TECHNICAL_PREFLIGHT_PASS` (`datachecks=PASS_BOTH`, `active jobs=0`).

---

## 3. HPC Job Receipt and Scheduler Attributes

| Parameter | Value | Verification Status |
| :--- | :--- | :--- |
| **PBS Job ID** | `1424711.mmaster02` | Accepted by PBS scheduler |
| **Job Name** | `M1_MC_C3_JOB1` | Verified in `qstat -u pr21vyci` |
| **Target Scratch Directory** | `/scratch9/pr21vyci/runs/mode1_290_method_c_case3/` | Verified on cluster |
| **Submission Queue** | `entry_imfdfkmq` | Route queue to `normal_imfdfkmq` |
| **Execution Queue** | `normal_imfdfkmq` | Active execution queue |
| **Allocated Resources** | 1 node, 16 CPUs (SMP), 48 GB RAM, 72:00:00 walltime | Directives verified in `qstat -f` |
| **Solver Input Deck** | `PK_METHOD_C_CASE3_COARSE_JOB1.inp` | SHA `1b3c9a62a9644e1e9fd6e8f4ad4b2dc734d69688d80e2655b0a11f8a7a7bddc2` |
| **Physical Mesh** | `PK_METHOD_C_CASE3_COARSE_PHYS.inp` | SHA `29af8622a20c006f31b488cced8e0c054749cb243acb0f2b2d9cbef35067ccdd` |
| **User Subroutine** | `f42_mixed_uel.for` | Frozen SHA `ce8d5edcd2911dcb018bb15275271f874e7ea62b8fb48cf4a8297469a83acdd6` |
| **PBS Wrapper** | `submit_case3_coarse_job1.pbs` | SHA `eb53f43543dd576807642ee775628bb862d9cec9bcc23b87143c605891f3e6d4` |
| **Authorization Manifest** | `METHOD_C_CASE3_JOB1_AUTHORIZATION.json` | SHA `03b7f59919448ffc221b2ff5e622ca11a368e782e2db25ff4536ad18e6d90d00` |
| **Observables Extractor** | `extract_case3_job1_observables.py` | SHA `f33f0ad4d723facc97b2d3de7626d2c37ad204f1c82fc61918e1c75b74b42441` |
| **Submitted At** | `2026-11-20T06:39:47Z` | Atomic timestamp recorded |

---

## 4. PBS Budget and Accounting Verification

- **Pre-Submission Cumulative PBS Jobs:** 62
- **Authorized Jobs in `HND-METHOD-C-CASE3-PREP-002`:** 1
- **Consumed Submissions:** 1 (`1424711.mmaster02`)
- **Post-Submission Cumulative PBS Jobs:** **63** (`max_new_pbs_submissions = 0`)
- **Ledger Entries Recorded:**
  - `project_coordination/HPC_JOB_LEDGER.csv` (Row 690 appended for `1424711.mmaster02`).
  - `project_coordination/MODE1_BATCH_SUBMISSIONS.json` (Atomic submission receipt recorded under manifest digest key `1768`).
  - `project_coordination/ACTIVE_TASK.json` (`active_pbs_job_id = "1424711.mmaster02"`, `submissions_consumed = 1`, `cumulative_pbs_submissions = 63`).
  - `project_coordination/TASK_LEDGER.csv` (`METHOD-C-CASE3-JOB1-COARSE-SOLVE` recorded).

---

## 5. Automated Unit Test Verification

The unit test suite was expanded to include `tests/unit/test_method_c_case3_job1_execution.py`, verifying submission provenance, ledger accounting, manifest integrity, PBS script directives, and extractor schema. All 10 Method C unit test suites pass with **51/51 tests PASS (100%)**:

1. `tests/unit/test_method_c_phase1_kickoff.py`: 10/10 PASS
2. `tests/unit/test_method_c_job1_observables.py`: 3/3 PASS
3. `tests/unit/test_method_c_job2_reequilibration.py`: 3/3 PASS
4. `tests/unit/test_method_c_transfer_reequilibration.py`: 5/5 PASS
5. `tests/unit/test_method_c_phase3_forward_propagation.py`: 6/6 PASS
6. `tests/unit/test_method_c_phase4_meeting_materials.py`: 5/5 PASS
7. `tests/unit/test_method_c_cycle2_package.py`: 5/5 PASS
8. `tests/unit/test_method_c_cycle2_job4_execution.py`: 4/4 PASS
9. `tests/unit/test_method_c_case3_package.py`: 6/6 PASS
10. `tests/unit/test_method_c_case3_job1_execution.py`: 4/4 PASS

---

## 6. Next Steps

1. **Solver Execution Monitoring**:
   - Maintain non-polling monitoring of job `1424711.mmaster02` in `normal_imfdfkmq`.
   - Upon completion, verify Exit Code 0 and inspect solver status file (`PK_METHOD_C_CASE3_COARSE_JOB1.sta`).
2. **Observable Extraction**:
   - Execute staged `extract_case3_job1_observables.py` on cluster:
     - Step 1: $u_2 = 0.05\,\text{mm}$ (50 increments), $RF_2$, $U_2$, peak damage $d_{\max}$, mean damage, $H_{\max}$, native $\text{MISESERI} / \text{MISESAVG}$.
     - Step 2: $u_2 = 0.4125\,\text{mm}$ propagation, $RF_2(u_2)$, peak load, softening tail, crack-tip coordinates $(x_{\text{tip}}, y_{\text{tip}})$, crack extension $\Delta a$.
     - Energies: $E_{\text{elastic}}, E_{\text{fracture}}, E_{\text{total}}$ from `uel_energy_balance.csv`.
   - Publish `PK_METHOD_C_CASE3_COARSE_JOB1_SUMMARY.json` and `RECEIPT.json`.
3. **Cycle 2 Adaptive Remeshing**:
   - Evaluate driver sizing branch on the extracted Job-1 end state ($u_2 = 0.4125\,\text{mm}$).
   - Construct adapted receiver mesh resolving the evolving crack path toward the central hole at $(36.5, 51.0)\,\text{mm}$.
   - Transfer state $(u, d, H)$ and stage Cycle-2 fixed-load re-equilibration deck.
