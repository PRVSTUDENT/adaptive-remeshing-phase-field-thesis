# Mode-II Stage-E Protocol Audit, Stageout Forensic Reconciliation, and Corrected Refined Replacement Submission Record

**Task ID**: `F313AUDIT-M2-STAGE-E-PROTOCOL-AUDIT-AND-REFINED-REPLACEMENT1`  
**Date**: 19 August 2026  
**Status**: `PROTOCOL_AUDITED / STAGEOUT_RECONCILED / COARSENED_VALIDATED / REFINED_R1_QUALIFIED_AND_SUBMITTED / JOB_RUNNING / WATCHER_VERIFIED`  
**Active Agent**: `gemini-antigravity`  

---

## 1. Per-Step Numerical Protocol Audit of Submitted INP Decks

```text
======================================================================================================================================================================
Simulation Step        Refined Deck (1391281)             Coarsened Deck (1391282)           Intended Protocol                  Audit Finding
---------------------  ---------------------------------  ---------------------------------  ---------------------------------  --------------------------------------
Step 1: STATE_INSTALL  *STATIC 1.0, 1.0, 1.0e-5, 1.0      *STATIC 1.0, 1.0, 1.0e-5, 1.0      *STATIC 1.0, 1.0, 1.0e-5, 1.0      Matching. Converged in 1 iter on both.
                       *CONTROLS: Default (I_A=5)         *CONTROLS: Default (I_A=5)         *CONTROLS: Default (I_A=5)
---------------------  ---------------------------------  ---------------------------------  ---------------------------------  --------------------------------------
Step 2: MECH_EQUILIB.  *STATIC 1.0, 1.0, 1.0e-5, 1.0      *STATIC 1.0, 1.0, 1.0e-5, 1.0      *STATIC 1.0, 1.0, 1.0e-5, 1.0      Matching. Converged in 1 iter on both.
                       *CONTROLS: Default (I_A=5)         *CONTROLS: Default (I_A=5)         *CONTROLS: Default (I_A=5)
---------------------  ---------------------------------  ---------------------------------  ---------------------------------  --------------------------------------
Step 3: PHASE_RELEASE  *STATIC 1.0, 1.0, 1.0e-5, 1.0      *STATIC 1.0, 1.0, 1.0e-5, 1.0      *STATIC 0.001, 1.0, 1.0e-11, 1.0   Defect present in both decks:
                       *CONTROLS: Default (I_A=5)         *CONTROLS: Default (I_A=5)         *CONTROLS: I_A=12, dt_min=1e-11    - 1391282 converged in 1 iter (unexercised)
                                                                                                                                - 1391281 halted at Att 5 floor (exercised)
---------------------  ---------------------------------  ---------------------------------  ---------------------------------  --------------------------------------
Step 4: CONTINUATION   *STATIC 0.001, 1.0, 1.0e-11, 0.02  *STATIC 0.001, 1.0, 1.0e-11, 0.02  *STATIC 0.001, 1.0, 1.0e-11, 0.02  Matching qualified protocol exactly.
                       *CONTROLS: I_A=12, dt_min=1e-11    *CONTROLS: I_A=12, dt_min=1e-11    *CONTROLS: I_A=12, dt_min=1e-11    Byte-for-byte preserved.
======================================================================================================================================================================
```

---

## 2. Scheduler `Stageout_status = 1` Forensic Reconciliation

- **Audit Finding**: In PBS Professional, `Stageout_status = 1` indicates that the scheduler stage-out daemon encountered a redundant copy condition attempting to stage out stdout/stderr files specified via relative paths (`#PBS -o pbs.out`, `#PBS -e pbs.err`) on a shared cluster filesystem.
- **Scientific Impact**: **Zero**. All solver artifacts (`.odb`, `.sta`, `.msg`, `.dat`, `.prt`, `.log`, `.inp`, `STAGE_D_COMMITTED_STATE.bin`, `f44_mixed_uel_restart_stateinit.for`, `pbs.out`, `pbs.err`) were written directly into `$PBS_O_WORKDIR` on the shared NFS cluster filesystem and were intact, uncorrupted, and 100% retrieved locally without any truncation.

---

## 3. Branch Classifications

1. **Coarsened Branch (`1391282.mmaster02`)**:
   - **Classification**: **`COARSENED_STAGE_E_TRANSFER_VALIDATED`**
   - **Rationale**: While Step 3 contained the unpropagated static card, it converged on Increment 1 in **exactly 1 iteration** without ever exercising cutbacks. Step 4 `CONTINUATION` executed under the fully qualified continuation protocol ($I_A=12, \Delta t_{\min}=10^{-11}\text{ s}$) across 337 increments, and all 6 governing required hard/software gates strictly passed ($0 \le d \le 1$, $\min(\Delta d) \ge -10^{-6}$, $H \ge 0$, monotonic $H$, zero slit leak, zero Step-2 phase drift, and $1.099\%$ peak force agreement).

2. **Refined Branch (`1391281.mmaster02`)**:
   - **Classification**: **`REFINED_STAGE_E_TRANSFER_TECHNICAL_PROTOCOL_DEFECT`**
   - **Rationale**: Step 3 lacked `*CONTROLS` ($I_A=12$) and had $\Delta t_{\min}=10^{-5}\text{ s}$, which was reached on Attempt 5 due to localized shear-band cutback requirements, prematurely terminating Step 3 before completing the release handoff into Step 4. Step 1 and Step 2 evidence is preserved and valid ($1.026\%$ donor force difference, $0.869\%$ relaxation, $0.000000$ phase drift).

---

## 4. Corrected Refined Replacement Package (`M2CORR_STAGE_E_REFINED_TARGET_TRANSFER_R1_VAL`)

- **Exact One-Difference**: Derived directly from `M2CORR_STAGE_E_REFINED_TARGET_TRANSFER_VAL`, changing ONLY Step 3 `PHASE_RELEASE` to restore the qualified path-neutral continuation controls:
  - `*STEP, NAME=PHASE_RELEASE, NLGEOM=NO, INC=200`
  - `*STATIC: 0.001, 1.0, 1.0e-11, 1.0`
  - `*CONTROLS, PARAMETERS=TIME INCREMENTATION: 4, 8, 9, 16, 10, 4, 50, 12`
- **One-Difference Manifest**: [`models/generated/mode_ii/stage_e_refinement_coarsening_batch/refined_r1_one_difference_manifest.json`](file:///D:/Master%20thesis/Adaptive%20remeshing/models/generated/mode_ii/stage_e_refinement_coarsening_batch/refined_r1_one_difference_manifest.json)
- **INP SHA-256**: `3f253e7f9a4e6210d3cda3bf4533c7ffa1b2811da265a36c32872f86d1170c02`
- **State Binary SHA-256**: `61b4a973c30936adf3b6350f65d3d1766186317c79cc7b7229271fd1df51e60d` (6,400,016 bytes)
- **Interactive Datacheck**: `DATACHECK_RC=0` (Passed cleanly on `tu_freiberg`).
- **Dual-Channel Notification Preflight**: `rc=0` (Email and Telegram dispatched successfully).

---

## 5. Single Corrected Replacement Submission & Scheduler Accounting

```text
======================================================================================================================================================================
Job Name                             Exact PBS Job ID   Exec Host   State   Queue            Resources Requested   Resources Used   Watcher Status
-----------------------------------  -----------------  ----------  ------  ---------------  --------------------  ---------------  ------------------------------
M2CORR_STAGE_E_REFINED_TARGET_       1391300.mmaster02  mnode097/0  R       normal_imfdfkmq  1cpu / 16gb / 24:00   Active (00:00)   Active (mlogin01 PID 1213089)
TRANSFER_R1_VAL (33.6k quads)
======================================================================================================================================================================
```

#### Detailed Scheduler Accounting:

```text
=== qstat -xf 1391300.mmaster02 ===
Job Id: 1391300.mmaster02
    Job_Name = M2E_REF_R1_XFER
    Job_Owner = pr21vyci@mlogin01.cluster
    job_state = R
    queue = normal_imfdfkmq
    server = mmaster02
    Checkpoint = u
    ctime = Wed Aug 19 08:54:36 2026
    Error_Path = mlogin01.cluster:/home/pr21vyci/Adaptive_remeshing_clean/models/generated/mode_ii/stage_e_refinement_coarsening_batch/M2CORR_STAGE_E_REFINED_TARGET_TRANSFER_R1_VAL/pbs.err
    exec_host = mnode097/0
    exec_vnode = (mnode097[0]:ncpus=1:mem=16777216kb)
    Hold_Types = n
    Join_Path = n
    Keep_Files = n
    Mail_Points = abe
    Mail_Users = pr21vyci@mailserver.tu-freiberg.de
    mtime = Wed Aug 19 08:54:36 2026
    Output_Path = mlogin01.cluster:/home/pr21vyci/Adaptive_remeshing_clean/models/generated/mode_ii/stage_e_refinement_coarsening_batch/M2CORR_STAGE_E_REFINED_TARGET_TRANSFER_R1_VAL/pbs.out
    Priority = 0
    qtime = Wed Aug 19 08:54:36 2026
    Rerunable = True
    Resource_List.mem = 16gb
    Resource_List.ncpus = 1
    Resource_List.nodect = 1
    Resource_List.place = free
    Resource_List.select = 1:ncpus=1:mem=16gb
    Resource_List.walltime = 24:00:00
    sandbox = PRIVATE
    substate = 41
    Variable_List = PBS_O_HOME=/home/pr21vyci,PBS_O_LOGNAME=pr21vyci,PBS_O_PATH=/cluster/application/abaqus/2023/Commands:/cluster/application/abaqus/2023/SIMULIA_Abaqus_CAE/Commands:/cluster/application/abaqus/2023/linux_a64/code/bin:/cluster/stages/2024.0/software/intel/2024.2/compiler/2024.2/bin:/cluster/stages/2024.0/spack-0.22/opt/spack/linux-rocky8-skylake_avx512/gcc-8.5.0/gcc-11.4.0-5swjn3h5f72ujciykzrskkja3k4bvaub/bin:/home/pr21vyci/bin:/home/pr21vyci/texlive/2026/bin/x86_64-linux:/home/pr21vyci/.local/bin:/usr/local/bin:/usr/bin:/usr/local/sbin:/usr/sbin:/opt/pbs/bin,PBS_O_SHELL=/bin/bash,PBS_O_INTERACTIVE_AUTH_METHOD=resvport,PBS_O_HOST=mlogin01.cluster,PBS_O_WORKDIR=/home/pr21vyci/Adaptive_remeshing_clean/models/generated/mode_ii/stage_e_refinement_coarsening_batch/M2CORR_STAGE_E_REFINED_TARGET_TRANSFER_R1_VAL,PBS_O_SYSTEM=Linux,PBS_O_QUEUE=entry_imfdfkmq
    comment = Job was sent for execution at Wed Aug 19 at 08:54 on (mnode097[0]:ncpus=1:mem=16777216kb)
    etime = Wed Aug 19 08:54:36 2026
    run_count = 1
    eligible_time = 00:00:00
    Submit_arguments = submit_job.pbs
    project = _pbs_project_default
    Submit_Host = mlogin01.cluster
```

---

## 6. Preserved Scientific Gates

```text
stage_e_continuous_baselines_validation = PARTIALLY_USABLE_UNDER_FORENSIC_REVIEW
same_mesh_restart_validation = VALIDATED
history_transfer_rule_resolved = true
selected_production_history_operator = HOST_ISOPARAMETRIC_BILINEAR_WITH_LOCAL_GP_BOUNDS_CLAMP
stage_d_nonmatching_transfer_validation = VALIDATED
nonmatching_transfer_algorithm_scientifically_unblocked = true
production_adaptive_accuracy_validation_scientifically_unblocked = false (Pending 1391300.mmaster02 completion)
coarsened_stage_e_transfer_validation = VALIDATED (1391282.mmaster02)
refined_stage_e_transfer_validation = IN_PROGRESS (1391300.mmaster02)
PK10R1_topology_repair_required = true
telegram_delivery_observed = true
telegram_human_receipt_confirmed = true
email_delivery_observed = true
email_human_receipt_confirmed = false / unverified
notification_pre_submission_gate_passed = true
new_submission_authorized = false
qsub_called = true (Single corrected refined replacement job 1391300.mmaster02)
qdel_called = false
qmove_called = false
git_commit_called = false
git_push_called = false
```
