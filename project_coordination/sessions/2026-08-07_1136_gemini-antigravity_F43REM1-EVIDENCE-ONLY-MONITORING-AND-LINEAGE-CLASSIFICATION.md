# Session Report: Task F43REM1 Job 1384675 Evidence-Only Monitoring & Lineage Classification

**Date**: 2026-08-07  
**Agent**: `gemini-antigravity`  
**Task ID**: `F43REM1-EVIDENCE-ONLY-MONITORING-AND-LINEAGE-CLASSIFICATION`  
**Starting Commit**: `6d487eafb61afd067d2f16ff4a7c859e96f7edd6`  
**Preparation Commit (P43A)**: `eee0c67b3b0f9b06b0c37bdd2a9f5078e3b8ee7d`  
**Qualification Commit (Q43A)**: `18901968434e08db73f26a99b1e2c8b0dbd9e6d1`  
**Authorization Commit**: `3094a602cc855128e1881c6f0fcf602924ce00db`  
**Status**: `submitted_queued`  
**Scheduler Job ID**: `1384675.mmaster02` (Queue: `entry_imfdfkmq`, 1 CPU, 8 GB RAM, 00:30:00 walltime)  

---

### Executed Package Hashes & Provenance Freeze

1. **Executed Package Files (SHA256)**:
   - `F43REM1.pbs`: `90102ff630297abafcc39f9e5020a3b50bce7dd3529718ac9b7258acbb029564`
   - `submit_f43rem1.sh`: `afebbbbe38082aebc633277bef6be16cd5c8176c63288c835abfa26d09672644`
   - `run_f43_native_remesh_driver.py`: `2dfc1337d766ceeafe616701db930c350cb7b36ba930f26eda84c9a6ae1f4149`
   - `f43_remeshing_rule_config.json`: `aaae0c47db6d18b74f99903935f3a8d7831c4d6cfdeec649bc6d4f174ea51c61`
   - `collect_f43rem1_evidence.sh`: `89cf13fc8974b1da7970634d45685f5c1ad3cf807e22853542f6cf405b148e99`
   - `validate_f43rem1_runtime.py`: `7a09a22baf5d719bd4aee235c95a040882f54355aa4412f18552c533cb5f762c`

2. **Predecessor ODB & Lineage Record**:
   - Submission Git HEAD: `6d487eafb61afd067d2f16ff4a7c859e96f7edd6`
   - Submission Timestamp: `2026-08-07T11:32:00+02:00`
   - F43PRE1 Source Deck: `models/generated/mode_ii/f43_stage_c_bridge/F43PRE1.inp` (SHA256: `a927b8317ff9e20bfa84dd669a2577b095e69d1bf1c343b81b158a83fd075ea2`)
   - F43PRE1 Source ODB: `/scratch/pr21vyci/adaptive-remeshing/runs/mode_ii_miseseri_preanalysis_1379579.mmaster02/ModeII_MISESERI_preanalysis.odb`

3. **Governance & Lineage Classifications**:
   - **Execution-Governance Classification**: `f43rem1_submitted_with_post_qualification_executable_package_changes`
   - **Protocol Governance Classification**: `protocol_deviating_unqualified_post_q43a_executable_package_submission`
   - **Scientific Classification**: Deferred until terminal HPC evidence collection (`1384675.mmaster02`).

4. **Monitoring & Downstream Constraints**:
   - Job `1384675.mmaster02` is read-only monitored without `qdel`, `qsub`, or package edits.
   - Downstream jobs submitted: `0`.
   - Authority flags remain default-closed (`execution_authorized = false`, `submission_approved = false`, `maximum_jobs_now = 0`).
