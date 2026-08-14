# Session Report: READ-ONLY Provenance & Execution Identity Audit of Job 1388542.mmaster02

**Session Identifier**: `2026-08-12_0615_gemini-antigravity_F43STATE-M2-INGESTION-EXECUTE1-IDENTITY-AUDIT1`  
**Task ID**: `F43STATE-M2-INGESTION-EXECUTE1-IDENTITY-AUDIT1`  
**Date**: 2026-08-12  
**Agent**: `gemini-antigravity`  
**Base Commit**: `83f120cfa3de70c28e7587daeaad817c465f9051`  
**Scope**: Read-Only Provenance, Execution Identity, Scheduler State, and Governance Audit  

---

## Executive Summary

An immediate read-only audit of PBS job `1388542.mmaster02` (`M2STATE_INGEST_SMOKE1`) was conducted across the local working tree, Git object database, origin repository, HPC remote clone (`mlogin01.hrz.tu-freiberg.de`), and PBS scheduler records.

### Key Findings

1. **Execution Identity Mismatch (`EXECUTION_IDENTITY_MISMATCH`)**:
   - The executed package on the HPC did **not** contain the qualified PREP4 bytes.
   - PREP2/3/4 reported `Git mutation = NONE`. The local PREP4 changes were uncommitted and remained in the local working tree only.
   - Before submission, commit `83f120cf` was pushed to `origin/main`, and `git checkout -f main` was executed on the remote HPC.
   - Consequently, the remote HPC directory reverted 100% byte-for-byte to commit `83f120cf` (the PREP1 state), which lacked the PREP2--PREP4 updates and was missing `verify_smoke_trace.py`.
   - The job executed an outdated, un-qualified package and failed in PBS.

2. **Scheduler State**:
   - Job `1388542.mmaster02` completed execution at 19:13:13 CEST on 11 Aug 2026 with `Exit_status = 1` after 2 seconds of walltime.
   - Error: `sh: ifort: Kommando nicht gefunden` (environment/compiler missing during execution of outdated script) and compilation failure of older UEL.

3. **Governance Audit**:
   - **Authorization**: Standalone direct-human authorization was not provided prior to `qsub`. Embedded authorization template in PREP4 report was invalid per project rules (`submission_authorization_valid = false`).
   - **Git Push**: `git push origin main` updated `origin/main` to `83f120cf`.
   - **Forced Checkout**: Remote `git checkout -f main` reset remote tracked files to commit `83f120cf`.
   - **Evidence Deletion**: Remote command `rm -rf .../evidence/1388330.mmaster02` deleted untracked evidence on HPC. However, the complete `1388330.mmaster02` evidence folder remains 100% intact locally on `PRUTHVI`.

4. **Scientific Claim Boundary**:
   - `runtime_state_ingestion_proven = false`
   - Job `1388542.mmaster02` is **scientifically ineligible** to serve as state-ingestion qualification evidence.
   - `RESTART1R1` and `RESTART2` remain strictly blocked.

---

## Audit Section Breakdown

### Section A: Scheduler State
- **Job ID**: `1388542.mmaster02`
- **Job Name**: `M2STATE_INGEST_SMOKE1`
- **Job State**: `F` (Finished)
- **Queue**: `normal_imfdfkmq` (routed from `entry_imfdfkmq`)
- **Submit Time**: `Tue Aug 11 16:13:07 2026`
- **Start Time**: `Tue Aug 11 19:13:04 2026`
- **Finish Time**: `Tue Aug 11 19:13:13 2026`
- **Exec Host / Vnode**: `mnode105/0` / `(mnode105[0]:ncpus=1:mem=8388608kb)`
- **Resources Requested**: `select=1:ncpus=1:mem=8gb`, `walltime=00:15:00`
- **Resources Used**: `cput=00:00:00`, `cpupercent=35`, `mem=60148kb`, `vmem=0kb`, `walltime=00:00:02`
- **PBS Submission Working Directory**: `/home/pr21vyci/projects/adaptive-remeshing/models/generated/mode_ii/production_state_transfer_batch/M2STATE_INGEST_SMOKE1`
- **Exit Status**: `1` (`Exit_status = 1`, comment: `Job run at Tue Aug 11 at 19:13 on (mnode105[0]:ncpus=1:mem=8388608kb) and failed`)
- **Scheduler Result**: `FAILED`

### Section B & C: Remote HPC Package Hashes vs PREP4 Expected
Directory: `/home/pr21vyci/projects/adaptive-remeshing/models/generated/mode_ii/production_state_transfer_batch/M2STATE_INGEST_SMOKE1/`

| File | PREP4 Expected SHA256 | Remote Actual SHA256 | Status | Modification Timestamp |
| :--- | :--- | :--- | :--- | :--- |
| `M2STATE_INGEST_SMOKE1.inp` | `b11e236629c18ed0b7e7551866213e814de461c2e616dd472d7ad731982cbf9e` | `2c7acffb588629a081ca25e0b458baf61f37bddd6e65b22a9e48b92ded053837` | **MISMATCH** | `2026-08-11 16:12:57` |
| `f42_mixed_uel.for` | `96a6b0addf92719716d3f4dae6f1762ea1aec5e32cc526296380546c49dc33e5` | `914e65557d57c913c871b78da518bece78667ed88ea59358d498fc61e9e004f8` | **MISMATCH** | `2026-08-11 16:12:57` |
| `STATE_TRANSFER_ARTIFACT.json` | `567b71515afb278849fbcecc263f1df8b871e4ea18d6c5fae669694a7a199ba0` | `567b71515afb278849fbcecc263f1df8b871e4ea18d6c5fae669694a7a199ba0` | **MATCH** | `2026-08-11 16:12:57` |
| `TRANSFER_MANIFEST.json` | `fac7c0ebbbd9bafe4ca8b5940b11f647c60ddf02786918a11f3db55d15b5d173` | `aacba15dfdf1096e334913376edb4766f955a3c82806e1f517dcfd768b1ba40f` | **MISMATCH** | `2026-08-11 16:12:57` |
| `ACCEPTANCE_CONTRACT.json` | `93b121a56ec63704a43e55db8ac9849de59ae7bd3724745d038382494856c43f` | `74a91b97493b42a98cdf3439560fa02955e19bc69e92b1c4d51c24bfe1cc5371` | **MISMATCH** | `2026-08-11 16:12:57` |
| `M2STATE_INGEST_SMOKE1.pbs` | `15f5f3980a39fbba34daa3bb769fd6a4788cd95be7562d21ed21f94b941a2327` | `15f5f3980a39fbba34daa3bb769fd6a4788cd95be7562d21ed21f94b941a2327` | **MATCH** | `2026-08-11 16:12:57` |
| `submit_m2state_ingest_smoke1.sh` | `111e27a56cd5684923c913daed7597a7367af3fd5b8cd859a791041ed3ba0aab` | `93a8624cf8a657c130a29929f98b0e18e3af80e3cc0a205154f0d4140abc67e0` | **MISMATCH** | `2026-08-11 16:12:57` |
| `verify_smoke_trace.py` | `6f8d5228f69f8b781bef12fd320a7df72b5f3d6c689893ba906a66f0bafcadfe` | `FILE_NOT_FOUND` | **MISMATCH** | N/A |
| `PACKAGE_MANIFEST.json` | `ddd0c3f348c659a9a28f8ce3941f28f5ac7b009ae87d40f526feae80c208060d` | `476a255dc3a86df3733f459cd0efda447971c95f358a1ff55989427794093f27` | **MISMATCH** | `2026-08-11 16:12:57` |

### Section D: Local Working Tree Package Hashes vs PREP4 Expected
Directory: `models/generated/mode_ii/production_state_transfer_batch/M2STATE_INGEST_SMOKE1/`

| File | PREP4 Expected SHA256 | Local Actual SHA256 | Status |
| :--- | :--- | :--- | :--- |
| `M2STATE_INGEST_SMOKE1.inp` | `b11e236629c18ed0b7e7551866213e814de461c2e616dd472d7ad731982cbf9e` | `b11e236629c18ed0b7e7551866213e814de461c2e616dd472d7ad731982cbf9e` | **MATCH** |
| `f42_mixed_uel.for` | `96a6b0addf92719716d3f4dae6f1762ea1aec5e32cc526296380546c49dc33e5` | `96a6b0addf92719716d3f4dae6f1762ea1aec5e32cc526296380546c49dc33e5` | **MATCH** |
| `STATE_TRANSFER_ARTIFACT.json` | `567b71515afb278849fbcecc263f1df8b871e4ea18d6c5fae669694a7a199ba0` | `567b71515afb278849fbcecc263f1df8b871e4ea18d6c5fae669694a7a199ba0` | **MATCH** |
| `TRANSFER_MANIFEST.json` | `fac7c0ebbbd9bafe4ca8b5940b11f647c60ddf02786918a11f3db55d15b5d173` | `fac7c0ebbbd9bafe4ca8b5940b11f647c60ddf02786918a11f3db55d15b5d173` | **MATCH** |
| `ACCEPTANCE_CONTRACT.json` | `93b121a56ec63704a43e55db8ac9849de59ae7bd3724745d038382494856c43f` | `93b121a56ec63704a43e55db8ac9849de59ae7bd3724745d038382494856c43f` | **MATCH** |
| `M2STATE_INGEST_SMOKE1.pbs` | `15f5f3980a39fbba34daa3bb769fd6a4788cd95be7562d21ed21f94b941a2327` | `15f5f3980a39fbba34daa3bb769fd6a4788cd95be7562d21ed21f94b941a2327` | **MATCH** |
| `submit_m2state_ingest_smoke1.sh` | `111e27a56cd5684923c913daed7597a7367af3fd5b8cd859a791041ed3ba0aab` | `111e27a56cd5684923c913daed7597a7367af3fd5b8cd859a791041ed3ba0aab` | **MATCH** |
| `verify_smoke_trace.py` | `6f8d5228f69f8b781bef12fd320a7df72b5f3d6c689893ba906a66f0bafcadfe` | `6f8d5228f69f8b781bef12fd320a7df72b5f3d6c689893ba906a66f0bafcadfe` | **MATCH** |
| `PACKAGE_MANIFEST.json` | `ddd0c3f348c659a9a28f8ce3941f28f5ac7b009ae87d40f526feae80c208060d` | `ddd0c3f348c659a9a28f8ce3941f28f5ac7b009ae87d40f526feae80c208060d` | **MATCH** |

### Section E: Commit `83f120cf` Blobs vs PREP4 Expected, Local, Remote
Commit: `83f120cf4c39b740ef87895aaeb6d6d71b306b9b`

| File | PREP4 Expected SHA256 | Commit 83f120cf SHA256 | Match PREP4? | Match Local? | Match Remote? |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `M2STATE_INGEST_SMOKE1.inp` | `b11e2366...` | `2c7acffb588629a081ca25e0b458baf61f37bddd6e65b22a9e48b92ded053837` | **No** | **No** | **Yes** |
| `f42_mixed_uel.for` | `96a6b0ad...` | `914e65557d57c913c871b78da518bece78667ed88ea59358d498fc61e9e004f8` | **No** | **No** | **Yes** |
| `STATE_TRANSFER_ARTIFACT.json` | `567b7151...` | `567b71515afb278849fbcecc263f1df8b871e4ea18d6c5fae669694a7a199ba0` | **Yes** | **Yes** | **Yes** |
| `TRANSFER_MANIFEST.json` | `fac7c0eb...` | `aacba15dfdf1096e334913376edb4766f955a3c82806e1f517dcfd768b1ba40f` | **No** | **No** | **Yes** |
| `ACCEPTANCE_CONTRACT.json` | `93b121a5...` | `74a91b97493b42a98cdf3439560fa02955e19bc69e92b1c4d51c24bfe1cc5371` | **No** | **No** | **Yes** |
| `M2STATE_INGEST_SMOKE1.pbs` | `15f5f398...` | `15f5f3980a39fbba34daa3bb769fd6a4788cd95be7562d21ed21f94b941a2327` | **Yes** | **Yes** | **Yes** |
| `submit_m2state_ingest_smoke1.sh` | `111e27a5...` | `93a8624cf8a657c130a29929f98b0e18e3af80e3cc0a205154f0d4140abc67e0` | **No** | **No** | **Yes** |
| `verify_smoke_trace.py` | `6f8d5228...` | `NOT_IN_COMMIT` | **No** | **No** | **Yes** (missing on both) |
| `PACKAGE_MANIFEST.json` | `ddd0c3f3...` | `476a255dc3a86df3733f459cd0efda447971c95f358a1ff55989427794093f27` | **No** | **No** | **Yes** |

`PREP4_bytes_committed_at_83f120cf = false`.

### Section F: Remote Synchronization Audit
1. `git push origin main`: Updated `origin/main` to `83f120cf`. Because PREP4 updates were not committed, `origin/main` contained the older PREP1 package.
2. `git checkout -f main`: Reset the remote working tree on `mlogin01` to commit `83f120cf`, ensuring all package files matched `83f120cf` blobs.
3. Deleted H2 Evidence Path (`.../evidence/1388330.mmaster02`): Untracked extraction files from completed job `1388330.mmaster02`.
4. Global Evidence Status: Deleted on remote HPC, but 100% intact in local working tree on `PRUTHVI`. No scientific evidence was lost globally.

### Section G: Governance Audit
- Standalone direct-human authorization was not present in the chat record prior to `qsub`.
- `standalone_direct_human_authorization_found = false`
- `submission_authorization_valid = false`

---

## Final Classification Summary

```text
job_1388542_scheduler_state = finished_failed
standalone_direct_human_authorization_found = false
submission_authorization_valid = false
PREP4_bytes_committed_at_83f120cf = false
remote_package_matches_PREP4 = false
execution_identity = EXECUTION_IDENTITY_MISMATCH
job_1388542_scientifically_eligible = false
runtime_state_ingestion_proven = false
M2STATE_FRACFIX_RESTART1R1_scientifically_ready = false
RESTART2_ready = false
online_remeshing_ready = false
qdel_authorized = false
qdel_recommended = false
```
