# Mode-II Stage-E Batch E2 Non-Matching Transfer Validation 2-Job Submission Record

**Task ID**: `F311SUB-M2-STAGE-E-BATCH-E2-TRANSFER-VALIDATION-SUBMISSION1`  
**Date**: 19 August 2026  
**Status**: `PREFLIGHT_PASSED / GUARDED_2JOB_BATCH_SUBMITTED / JOBS_ACTIVE / WATCHER_VERIFIED`  
**Active Agent**: `gemini-antigravity`  

---

## 1. Batch E2 Scheduler & Accounting Metadata

```text
======================================================================================================================================================================
Job Name                             Exact PBS Job ID   Exec Host   State   Queue            Resources Requested   Resources Used   Watcher Status
-----------------------------------  -----------------  ----------  ------  ---------------  --------------------  ---------------  ------------------------------
M2CORR_STAGE_E_REFINED_TARGET_       1391281.mmaster02  mnode097/0  R       normal_imfdfkmq  1cpu / 16gb / 24:00   Active (00:00)   Active (mlogin01 PID 1213089)
TRANSFER_VAL (33.6k quads)
-----------------------------------  -----------------  ----------  ------  ---------------  --------------------  ---------------  ------------------------------
M2CORR_STAGE_E_COARSENED_TARGET_     1391282.mmaster02  mnode097/1  R       normal_imfdfkmq  1cpu / 16gb / 24:00   Active (00:00)   Active (mlogin01 PID 1213089)
TRANSFER_VAL (8.2k quads)
======================================================================================================================================================================
```

#### Detailed Scheduler Accounting:

```text
=== qstat -xf 1391281.mmaster02 ===
Job Id: 1391281.mmaster02
    Job_Name = M2E_REFINED_XFER
    Job_Owner = pr21vyci@mlogin01.cluster
    job_state = R
    queue = normal_imfdfkmq
    server = mmaster02
    Checkpoint = u
    ctime = Wed Aug 19 08:18:23 2026
    Error_Path = mlogin01.cluster:/home/pr21vyci/Adaptive_remeshing_clean/models/generated/mode_ii/stage_e_refinement_coarsening_batch/M2CORR_STAGE_E_REFINED_TARGET_TRANSFER_VAL/pbs.err
    exec_host = mnode097/0
    exec_vnode = (mnode097[0]:ncpus=1:mem=16777216kb)
    Hold_Types = n
    Join_Path = n
    Keep_Files = n
    Mail_Points = abe
    Mail_Users = pr21vyci@mailserver.tu-freiberg.de
    mtime = Wed Aug 19 08:18:24 2026
    Output_Path = mlogin01.cluster:/home/pr21vyci/Adaptive_remeshing_clean/models/generated/mode_ii/stage_e_refinement_coarsening_batch/M2CORR_STAGE_E_REFINED_TARGET_TRANSFER_VAL/pbs.out
    Priority = 0
    qtime = Wed Aug 19 08:18:24 2026
    Rerunable = True
    Resource_List.mem = 16gb
    Resource_List.ncpus = 1
    Resource_List.nodect = 1
    Resource_List.place = free
    Resource_List.select = 1:ncpus=1:mem=16gb
    Resource_List.walltime = 24:00:00
    sandbox = PRIVATE
    substate = 41
    Variable_List = PBS_O_HOME=/home/pr21vyci,PBS_O_LOGNAME=pr21vyci,PBS_O_PATH=/home/pr21vyci/bin:/home/pr21vyci/texlive/2026/bin/x86_64-linux:/home/pr21vyci/.local/bin:/home/pr21vyci/bin:/usr/local/bin:/usr/bin:/usr/local/sbin:/usr/sbin:/opt/pbs/bin,PBS_O_SHELL=/bin/bash,PBS_O_INTERACTIVE_AUTH_METHOD=resvport,PBS_O_HOST=mlogin01.cluster,PBS_O_WORKDIR=/home/pr21vyci/Adaptive_remeshing_clean/models/generated/mode_ii/stage_e_refinement_coarsening_batch/M2CORR_STAGE_E_REFINED_TARGET_TRANSFER_VAL,PBS_O_SYSTEM=Linux,PBS_O_QUEUE=entry_imfdfkmq
    comment = Job was sent for execution at Wed Aug 19 at 08:18 on (mnode097[0]:ncpus=1:mem=16777216kb)
    etime = Wed Aug 19 08:18:24 2026
    run_count = 1
    eligible_time = 00:00:01
    Submit_arguments = submit_job.pbs
    project = _pbs_project_default
    Submit_Host = mlogin01.cluster

=== qstat -xf 1391282.mmaster02 ===
Job Id: 1391282.mmaster02
    Job_Name = M2E_COARSE_XFER
    Job_Owner = pr21vyci@mlogin01.cluster
    job_state = R
    queue = normal_imfdfkmq
    server = mmaster02
    Checkpoint = u
    ctime = Wed Aug 19 08:18:24 2026
    Error_Path = mlogin01.cluster:/home/pr21vyci/Adaptive_remeshing_clean/models/generated/mode_ii/stage_e_refinement_coarsening_batch/M2CORR_STAGE_E_COARSENED_TARGET_TRANSFER_VAL/pbs.err
    exec_host = mnode097/1
    exec_vnode = (mnode097[0]:ncpus=1:mem=16777216kb)
    Hold_Types = n
    Join_Path = n
    Keep_Files = n
    Mail_Points = abe
    Mail_Users = pr21vyci@mailserver.tu-freiberg.de
    mtime = Wed Aug 19 08:18:24 2026
    Output_Path = mlogin01.cluster:/home/pr21vyci/Adaptive_remeshing_clean/models/generated/mode_ii/stage_e_refinement_coarsening_batch/M2CORR_STAGE_E_COARSENED_TARGET_TRANSFER_VAL/pbs.out
    Priority = 0
    qtime = Wed Aug 19 08:18:24 2026
    Rerunable = True
    Resource_List.mem = 16gb
    Resource_List.ncpus = 1
    Resource_List.nodect = 1
    Resource_List.place = free
    Resource_List.select = 1:ncpus=1:mem=16gb
    Resource_List.walltime = 24:00:00
    sandbox = PRIVATE
    substate = 41
    Variable_List = PBS_O_HOME=/home/pr21vyci,PBS_O_LOGNAME=pr21vyci,PBS_O_PATH=/home/pr21vyci/bin:/home/pr21vyci/texlive/2026/bin/x86_64-linux:/home/pr21vyci/.local/bin:/home/pr21vyci/bin:/usr/local/bin:/usr/bin:/usr/local/sbin:/usr/sbin:/opt/pbs/bin,PBS_O_SHELL=/bin/bash,PBS_O_INTERACTIVE_AUTH_METHOD=resvport,PBS_O_HOST=mlogin01.cluster,PBS_O_WORKDIR=/home/pr21vyci/Adaptive_remeshing_clean/models/generated/mode_ii/stage_e_refinement_coarsening_batch/M2CORR_STAGE_E_COARSENED_TARGET_TRANSFER_VAL,PBS_O_SYSTEM=Linux,PBS_O_QUEUE=entry_imfdfkmq
    comment = Job was sent for execution at Wed Aug 19 at 08:18 on (mnode097[0]:ncpus=1:mem=16777216kb)
    etime = Wed Aug 19 08:18:24 2026
    run_count = 1
    eligible_time = 00:00:01
    Submit_arguments = submit_job.pbs
    project = _pbs_project_default
    Submit_Host = mlogin01.cluster
```

---

## 2. Pre-Submission Gates Verification

1. **Manifest & SHA-256 Hashes Verification**:
   - Refined Transfer Deck: `23edb39698af3a856ce47275af5e39988769e283c0439cbec6ceda9ae51e6d19` (100% Match)
   - Refined State Binary: `61b4a973c30936adf3b6350f65d3d1766186317c79cc7b7229271fd1df51e60d` (100% Match, 6,400,016 bytes)
   - Coarsened Transfer Deck: `34442361b61f061016bdefbefeb0aad473f64f6689f4f02937eba8f9c5067711` (100% Match)
   - Coarsened State Binary: `3fa2392bcfc228257433c46ef443fa6a355b1032f9c8f29d1400a263dd20cd7b` (100% Match, 6,400,016 bytes)
2. **Strict Unix LF Line Endings**: Verified 0 `\r\n` characters in all submission artifacts.
3. **Dual-Channel Notification Preflight**:
   - `python3 notify_hpc_event.py --mode test --channel both` returned `rc=0` on `mlogin01`.
   - Telegram: `rc=0` (dispatched).
   - Email: `rc=0` (dispatched to `pr21vyci@mailserver.tu-freiberg.de`).
4. **Concurrency Guard**:
   - Active running jobs before submission: `0`.
   - Submitted 2-job batch $\to$ exactly 2 running jobs (`1391281` and `1391282`), respecting the max-2 limit.
5. **Watcher Coverage**:
   - Confirmed active on `mlogin01` (`PID 1213089`).

---

## 3. Frozen Stage-E Evaluation Logic & Comparison Windows

```text
======================================================================================================================================================================
Category                             Evaluated Stage-E Metrics                                          Stopping / Passing Logic
-----------------------------------  -----------------------------------------------------------------  --------------------------------------------------------------
Governing Required Gates             CRIT_E_PRIMARY_PHASE_BOUNDS (REQUIRED_HARD_GATE)                   0.0 <= d <= 1.0 at all nodes
                                     CRIT_E_POINTWISE_PHASE_IRREVERSIBILITY (REQUIRED_HARD_GATE)        min(Δd) >= -1.0e-6 across all steps
                                     CRIT_E_HISTORY_NONNEGATIVITY (REQUIRED_HARD_GATE)                  H >= 0.0 at all GPs
                                     CRIT_E_TEMPORAL_HISTORY_MONOTONICITY (REQUIRED_HARD_GATE)          H_{n+1} >= H_n across all steps
                                     CRIT_E_SLIT_BARRIER_ISOLATION (REQUIRED_HARD_GATE)                 cross_slit_leak == 0
                                     CRIT_E_MECH_EQUILIBRATION_U3_DRIFT (REQUIRED_SOFTWARE_GATE)        max |Δu3| <= 1.0e-6 during Step 2
-----------------------------------  -----------------------------------------------------------------  --------------------------------------------------------------
Diagnostic Parity Comparisons        CRIT_E_HANDOFF_RF1_COMPARISON (DIAGNOSTIC_ONLY)                    Step 1 RF1 vs donor Frame 17 RF1
                                     CRIT_E_MECH_EQUILIBRATION_RF1_JUMP (DIAGNOSTIC_ONLY)               Step 1 -> Step 2 RF1 relaxation
                                     CRIT_E_MATCHED_BASELINE_PEAK_PARITY (DIAGNOSTIC_ONLY)              Trajectory parity inside accepted comparison window
                                     CRIT_E_MATCHED_BASELINE_TERMINAL_PARITY (DIAGNOSTIC_ONLY)          Trajectory parity inside accepted comparison window
-----------------------------------  -----------------------------------------------------------------  --------------------------------------------------------------
Accepted Comparison Windows          Refined Mesh (1391281 vs 1391277)                                  Evaluated within U1 in [0.000000, 0.01258393] mm (29 frames)
                                     Coarsened Mesh (1391282 vs 1391279)                                Evaluated within U1 in [0.000000, 0.01311632] mm (476 frames)
======================================================================================================================================================================
```

---

## 4. Preserved Scientific Gates

```text
stage_e_continuous_baselines_validation = PARTIALLY_USABLE_UNDER_FORENSIC_REVIEW
same_mesh_restart_validation = VALIDATED
history_transfer_rule_resolved = true
selected_production_history_operator = HOST_ISOPARAMETRIC_BILINEAR_WITH_LOCAL_GP_BOUNDS_CLAMP
stage_d_nonmatching_transfer_validation = VALIDATED
nonmatching_transfer_algorithm_scientifically_unblocked = true
production_adaptive_accuracy_validation_scientifically_unblocked = false (Pending Batch E2 retrieval and evaluation)
PK10R1_topology_repair_required = true
telegram_delivery_observed = true
telegram_human_receipt_confirmed = true
email_delivery_observed = true
email_human_receipt_confirmed = false / unverified
notification_pre_submission_gate_passed = true
new_submission_authorized = false
qsub_called = true (Batch E2 guarded 2-job submission)
qdel_called = false
qmove_called = false
git_commit_called = false
git_push_called = false
```
