# Mode-II Stage-E Donor Single-Control Isolation Packages Preparation, Qualification, and Guarded Batch Submission Record

**Task ID**: `F316SUB-M2-STAGE-E-DONOR-SINGLE-CONTROL-ISOLATION-BATCH-SUBMISSION1`  
**Date**: 19 August 2026  
**Status**: `PACKAGES_PREPARED / ONE_DIFF_VERIFIED / PREFLIGHT_PASSED / GUARDED_2JOB_BATCH_SUBMITTED / JOBS_ACTIVE / WATCHER_VERIFIED`  
**Active Agent**: `gemini-antigravity`  

---

## 1. Submitted Donor Single-Control Isolation Jobs & Scheduler Accounting

```text
======================================================================================================================================================================
Job Name                             Exact PBS Job ID   Exec Host   State   Queue            Resources Requested   Resources Used   Watcher Status
-----------------------------------  -----------------  ----------  ------  ---------------  --------------------  ---------------  ------------------------------
M2CORR_STAGE_E_DONOR_IA13_           1391301.mmaster02  mnode097/0  R       normal_imfdfkmq  1cpu / 16gb / 24:00   Active (00:00)   Active (mlogin01 PID 1213089)
ISOLATION_VAL (I_A: 12 -> 13)
-----------------------------------  -----------------  ----------  ------  ---------------  --------------------  ---------------  ------------------------------
M2CORR_STAGE_E_DONOR_DTMIN5E12_      1391302.mmaster02  mnode097/1  R       normal_imfdfkmq  1cpu / 16gb / 24:00   Active (00:00)   Active (mlogin01 PID 1213089)
ISOLATION_VAL (dt_min: 1e-11->5e-12)
======================================================================================================================================================================
```

#### Detailed Scheduler Metadata:

```text
=== qstat -xf 1391301.mmaster02 ===
Job Id: 1391301.mmaster02
    Job_Name = M2E_D_IA13_ISO
    Job_Owner = pr21vyci@mlogin01.cluster
    job_state = R
    queue = normal_imfdfkmq
    server = mmaster02
    Checkpoint = u
    ctime = Wed Aug 19 09:33:13 2026
    Error_Path = mlogin01.cluster:/home/pr21vyci/Adaptive_remeshing_clean/models/generated/mode_ii/stage_e_refinement_coarsening_batch/M2CORR_STAGE_E_DONOR_IA13_ISOLATION_VAL/pbs.err
    exec_host = mnode097/0
    exec_vnode = (mnode097[0]:ncpus=1:mem=16777216kb)
    Hold_Types = n
    Join_Path = n
    Keep_Files = n
    Mail_Points = abe
    Mail_Users = pr21vyci@mailserver.tu-freiberg.de
    mtime = Wed Aug 19 09:33:18 2026
    Output_Path = mlogin01.cluster:/home/pr21vyci/Adaptive_remeshing_clean/models/generated/mode_ii/stage_e_refinement_coarsening_batch/M2CORR_STAGE_E_DONOR_IA13_ISOLATION_VAL/pbs.out
    Priority = 0
    qtime = Wed Aug 19 09:33:13 2026
    Rerunable = True
    Resource_List.mem = 16gb
    Resource_List.ncpus = 1
    Resource_List.nodect = 1
    Resource_List.place = free
    Resource_List.select = 1:ncpus=1:mem=16gb
    Resource_List.walltime = 24:00:00
    sandbox = PRIVATE
    substate = 42
    Variable_List = PBS_O_HOME=/home/pr21vyci,PBS_O_LOGNAME=pr21vyci,PBS_O_PATH=/cluster/application/abaqus/2023/Commands:/cluster/application/abaqus/2023/SIMULIA_Abaqus_CAE/Commands:/cluster/application/abaqus/2023/linux_a64/code/bin:/cluster/stages/2024.0/software/intel/2024.2/compiler/2024.2/bin:/cluster/stages/2024.0/spack-0.22/opt/spack/linux-rocky8-skylake_avx512/gcc-8.5.0/gcc-11.4.0-5swjn3h5f72ujciykzrskkja3k4bvaub/bin:/home/pr21vyci/bin:/home/pr21vyci/texlive/2026/bin/x86_64-linux:/home/pr21vyci/.local/bin:/usr/local/bin:/usr/bin:/usr/local/sbin:/usr/sbin:/opt/pbs/bin,PBS_O_SHELL=/bin/bash,PBS_O_INTERACTIVE_AUTH_METHOD=resvport,PBS_O_HOST=mlogin01.cluster,PBS_O_WORKDIR=/home/pr21vyci/Adaptive_remeshing_clean/models/generated/mode_ii/stage_e_refinement_coarsening_batch/M2CORR_STAGE_E_DONOR_IA13_ISOLATION_VAL,PBS_O_SYSTEM=Linux,PBS_O_QUEUE=entry_imfdfkmq
    comment = Job run at Wed Aug 19 at 09:33 on (mnode097[0]:ncpus=1:mem=16777216kb)
    etime = Wed Aug 19 09:33:13 2026
    run_count = 1
    eligible_time = 00:00:05
    Submit_arguments = submit_job.pbs
    project = _pbs_project_default
    Submit_Host = mlogin01.cluster

=== qstat -xf 1391302.mmaster02 ===
Job Id: 1391302.mmaster02
    Job_Name = M2E_D_DT5E12_ISO
    Job_Owner = pr21vyci@mlogin01.cluster
    job_state = R
    queue = normal_imfdfkmq
    server = mmaster02
    Checkpoint = u
    ctime = Wed Aug 19 09:33:13 2026
    Error_Path = mlogin01.cluster:/home/pr21vyci/Adaptive_remeshing_clean/models/generated/mode_ii/stage_e_refinement_coarsening_batch/M2CORR_STAGE_E_DONOR_DTMIN5E12_ISOLATION_VAL/pbs.err
    exec_host = mnode097/1
    exec_vnode = (mnode097[0]:ncpus=1:mem=16777216kb)
    Hold_Types = n
    Join_Path = n
    Keep_Files = n
    Mail_Points = abe
    Mail_Users = pr21vyci@mailserver.tu-freiberg.de
    mtime = Wed Aug 19 09:33:18 2026
    Output_Path = mlogin01.cluster:/home/pr21vyci/Adaptive_remeshing_clean/models/generated/mode_ii/stage_e_refinement_coarsening_batch/M2CORR_STAGE_E_DONOR_DTMIN5E12_ISOLATION_VAL/pbs.out
    Priority = 0
    qtime = Wed Aug 19 09:33:13 2026
    Rerunable = True
    Resource_List.mem = 16gb
    Resource_List.ncpus = 1
    Resource_List.nodect = 1
    Resource_List.place = free
    Resource_List.select = 1:ncpus=1:mem=16gb
    Resource_List.walltime = 24:00:00
    sandbox = PRIVATE
    substate = 42
    Variable_List = PBS_O_HOME=/home/pr21vyci,PBS_O_LOGNAME=pr21vyci,PBS_O_PATH=/cluster/application/abaqus/2023/Commands:/cluster/application/abaqus/2023/SIMULIA_Abaqus_CAE/Commands:/cluster/application/abaqus/2023/linux_a64/code/bin:/cluster/stages/2024.0/software/intel/2024.2/compiler/2024.2/bin:/cluster/stages/2024.0/spack-0.22/opt/spack/linux-rocky8-skylake_avx512/gcc-8.5.0/gcc-11.4.0-5swjn3h5f72ujciykzrskkja3k4bvaub/bin:/home/pr21vyci/bin:/home/pr21vyci/texlive/2026/bin/x86_64-linux:/home/pr21vyci/.local/bin:/usr/local/bin:/usr/bin:/usr/local/sbin:/usr/sbin:/opt/pbs/bin,PBS_O_SHELL=/bin/bash,PBS_O_INTERACTIVE_AUTH_METHOD=resvport,PBS_O_HOST=mlogin01.cluster,PBS_O_WORKDIR=/home/pr21vyci/Adaptive_remeshing_clean/models/generated/mode_ii/stage_e_refinement_coarsening_batch/M2CORR_STAGE_E_DONOR_DTMIN5E12_ISOLATION_VAL,PBS_O_SYSTEM=Linux,PBS_O_QUEUE=entry_imfdfkmq
    comment = Job run at Wed Aug 19 at 09:33 on (mnode097[0]:ncpus=1:mem=16777216kb)
    etime = Wed Aug 19 09:33:13 2026
    run_count = 1
    eligible_time = 00:00:05
    Submit_arguments = submit_job.pbs
    project = _pbs_project_default
    Submit_Host = mlogin01.cluster
```

---

## 2. Package Provenance & Exact One-Difference Lineage

Both packages are derived directly from validated donor job `1390876.mmaster02` (`M2CORR_STAGE_E_DONOR_MINIMAL_DTMIN_CONTINUATION_VAL`):
- Mesh: 8,836 physical quads, 9,074 physical nodes excluding RP 99999 ($h_{\text{tip}} = 0.004\text{ mm}$).
- Subroutine: `f44_mixed_uel_restart_stateinit.for` (SHA-256: `62e35f74bbeccd3f5b1ac67312b79211f4ccb75648ae20dbb8985cb577fe1aab`).
- Material PROPS: `PROPS(6)=0.004 mm` ($l_0$), `PROPS(7)=0.0` (Standard continuous mode).

```text
======================================================================================================================================================================
Package Name                         INP SHA-256 (64 hex)               Single Parameter Modified          Frozen Numerical Controls
-----------------------------------  ---------------------------------  ---------------------------------  ---------------------------------------------------
M2CORR_STAGE_E_DONOR_IA13_           593cfc59ed9f2b76d8186bdf5c144be90  I_A: 12 -> 13                      dt_min = 1.0e-11, I_0=4, I_R=8, I_P=9, I_C=16,
ISOLATION_VAL                        2ff53155baf5c930a7e7eb3b6a3d834                                       I_L=10, I_G=4, I_S=50
-----------------------------------  ---------------------------------  ---------------------------------  ---------------------------------------------------
M2CORR_STAGE_E_DONOR_DTMIN5E12_      346543717faf73e85fabffb008bcda8e5  dt_min: 1.0e-11 -> 5.0e-12         I_A = 12, I_0=4, I_R=8, I_P=9, I_C=16,
ISOLATION_VAL                        2b19a9a9a081c7e197c943d65fa1fc5                                       I_L=10, I_G=4, I_S=50
======================================================================================================================================================================
```

- **Manifest**: [`models/generated/mode_ii/stage_e_refinement_coarsening_batch/donor_single_control_isolation_manifest.json`](file:///D:/Master%20thesis/Adaptive%20remeshing/models/generated/mode_ii/stage_e_refinement_coarsening_batch/donor_single_control_isolation_manifest.json)
- **Interactive Datachecks**: `DC1_RC=0`, `DC2_RC=0` (Both PASSED cleanly on `tu_freiberg`).
- **Dual-Channel Notification Preflight**: `rc=0` on both Email and Telegram.
- **Concurrency Guard**: Enforced $\le 2$ simultaneous running jobs (currently exactly 2 running).
- **Login-Node Watcher Sidecar**: Active on `mlogin01` (`PID 1213089`).

---

## 3. Frozen Path-Neutrality Acceptance Criteria

Both jobs will be evaluated across all 440 accepted increments through $U_1 = 0.050\text{ mm}$ against exact donor control `1390876.mmaster02`:
- Exact bit-for-bit frame count and accepted $U_1$ progression.
- Exact reaction force parity ($|\Delta RF_1| = 0.0\text{ N}$).
- Nodal phase field $d$, committed history $\mathcal{H}$, energies, crack path.
- Record whether the modified setting was exercised.
- Classify each isolation as exactly one of: `PATH_NEUTRAL_VALIDATED`, `ALTERS_EQUILIBRIUM_PATH`, `JOB_FAILED_BEFORE_QUALIFICATION`, `UNRESOLVED`.

---

## 4. Preserved Scientific Gates

```text
coarsened_stage_e_transfer_validation = VALIDATED
refined_stage_e_transfer_validation = REFINED_STAGE_E_CONTINUATION_GATE_UNRESOLVED
stage_e_continuous_baselines_validation = PARTIALLY_USABLE_UNDER_FORENSIC_REVIEW
same_mesh_restart_validation = VALIDATED
history_transfer_rule_resolved = true
selected_production_history_operator = HOST_ISOPARAMETRIC_BILINEAR_WITH_LOCAL_GP_BOUNDS_CLAMP
stage_d_nonmatching_transfer_validation = VALIDATED
nonmatching_transfer_algorithm_scientifically_unblocked = true
production_adaptive_accuracy_validation_scientifically_unblocked = false
PK10R1_topology_repair_required = true
telegram_delivery_observed = true
telegram_human_receipt_confirmed = true
email_delivery_observed = true
email_human_receipt_confirmed = false / unverified
notification_pre_submission_gate_passed = true
new_submission_authorized = false
qsub_called = true (Guarded 2-job donor isolation batch: 1391301 and 1391302)
qdel_called = false
qmove_called = false
git_commit_called = false
git_push_called = false
```
