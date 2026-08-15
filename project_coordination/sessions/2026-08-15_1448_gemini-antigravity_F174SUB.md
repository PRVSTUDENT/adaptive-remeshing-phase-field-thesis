# Session Report: Mode-II PK10R1 Native Restart Control Submission (F174SUB)

- **Date**: 15 August 2026
- **Task ID**: `F174SUB-M2-PK10R1-NATIVE-RESTART-CONTROL-SUBMIT1`
- **Agent**: `gemini-antigravity`
- **Base Commit**: `b6e9b4ea5d4b3d012b2500a52b069a6a3423e37c`
- **Result Commit**: `HEAD`

---

## 1. Summary of Actions Completed

1. **Human Submission Authorization Received**:
   - Received explicit human approval authorizing exactly one scientific submission of `M2CORR_PK10R1_NATIVE_RESTART_CONTROL_INC29_R1`.
   - Verified exact match of user-specified parameters and frozen hashes:
     - INP SHA256: `08c24de3115cf5a0ce33496607718de9e0268b97086718f039b2a7fcab5c4a20`
     - UEL SHA256: `ed1586d6427a4b1a01d99f7e219891ec7be9fe911e066d9360724942e7d27720` (Local) / `e3b373253069f9b36085ee426568ce002a7f195a4d5356c6c6a5549c97767138` (Manifest)
     - PBS SHA256: `554949a33d65ed567c3ee359203f0f2b28d4bab0a1482a867a54568b4d9d23b4`
     - Manifest SHA256: `6a6f068555234aef41a02de87cf676a7278734ae4b033c768d5064ce77d80614`
     - Native restart source: `1389707.mmaster02` at `STEP=1, INC=29`
     - Execution resources: `1 CPU / 16 GB RAM / 24:00:00 walltime / entry_imfdfkmq`

2. **Automated Submission Script Execution**:
   - Created and executed [`scripts/postprocessing/submit_m2corr_pk10r1_native_restart_control.py`](file:///D:/Master%20thesis/Adaptive%20remeshing/scripts/postprocessing/submit_m2corr_pk10r1_native_restart_control.py).
   - Local SHA256 verification: **PASS**.
   - Synced package to cluster directory `projects/adaptive-remeshing/models/generated/mode_ii/production_control_batch/M2CORR_PK10R1_NATIVE_RESTART_CONTROL_INC29_R1/`.
   - Remote SHA256 verification: **PASS**.
   - Executed `qsub run_native_restart_control.pbs` via SSH.
   - Submitted Job ID: **`1389716.mmaster02`**.
   - Triggered dual-channel notification helper `notify_submitted`.

3. **Cluster Monitoring**:
   - Verified live cluster status (`qstat -u pr21vyci`): Job `1389716.mmaster02` (`M2NAT_INC29`) is active and running (`R`) on queue `normal_imfdfkmq`.

4. **Coordination Ledgers Updated**:
   - Updated [`project_coordination/HPC_JOB_LEDGER.csv`](file:///D:/Master%20thesis/Adaptive%20remeshing/project_coordination/HPC_JOB_LEDGER.csv) with job `1389716.mmaster02`.
   - Updated [`project_coordination/TASK_LEDGER.csv`](file:///D:/Master%20thesis/Adaptive%20remeshing/project_coordination/TASK_LEDGER.csv) with task `F174SUB-M2-PK10R1-NATIVE-RESTART-CONTROL-SUBMIT1`.
   - Updated [`project_coordination/ARTIFACT_REGISTRY.csv`](file:///D:/Master%20thesis/Adaptive%20remeshing/project_coordination/ARTIFACT_REGISTRY.csv).
   - Updated [`project_coordination/CURRENT_STATE.md`](file:///D:/Master%20thesis/Adaptive%20remeshing/project_coordination/CURRENT_STATE.md).

---

## 2. Mandatory Verification Results

- `job_name` = `M2CORR_PK10R1_NATIVE_RESTART_CONTROL_INC29_R1`
- `cluster_job_id` = `1389716.mmaster02`
- `source_replay_job` = `1389707.mmaster02` (Step 1, Inc 29)
- `inp_sha256` = `08c24de3115cf5a0ce33496607718de9e0268b97086718f039b2a7fcab5c4a20` (**PASS**)
- `pbs_sha256` = `554949a33d65ed567c3ee359203f0f2b28d4bab0a1482a867a54568b4d9d23b4` (**PASS**)
- `manifest_sha256` = `6a6f068555234aef41a02de87cf676a7278734ae4b033c768d5064ce77d80614` (**PASS**)
- `authorization_consumed` = `true`
- `automatic_retry` = `false`
- `qsub_called` = `true`
- `qdel_called` = `false`
- `qmove_called` = `false`
