# Project Current State

# Current Project State - Stage C Mode-II Job 1386471 Closeout PASS & Stage-2 Restart Package Prepared (M2STATE_FRACFIX_RESTART2)

**Active Task**: `F43STATE-M2-OVERNIGHT-CONTINUE1`  
**Date**: 2026-08-10  
**Active Agent**: `gemini-antigravity`  
**Task Status**: `preparation_complete_not_authorized`  

---

## 1. Terminal Scientific Closeout of Job 1386471 (`M2STATE_FRACFIX_RESTART1`)

- **Scheduler Result**: `COMPLETED` (`job_state = F`, `exit_status = 0`)
- **Technical Result**: `PASS` (Abaqus 2023 completed cleanly in 2,100 increments and 4,200 equilibrium iterations without cutbacks)
- **Runtime/Cost**: Walltime `00:02:20`, CPU time `00:02:18`, Memory `5,104,080 KB` (~5.1 GB), VMEM `7,954,912 KB` (~7.95 GB)
- **Endpoint**: Reached $u_1 = 0.010000\,\text{mm}$ (Step-1 re-equilibration 100 incs + Step-2 continuation 2,000 incs)
- **Scientific Gates Evaluated**:
  - Phase field $d$ L2 error: $0.048\%$ ($\le 1.0\%$ gate, PASS)
  - Phase max error: $0.00185$
  - History field $H$ L2 error: $0.052\%$ ($\le 1.0\%$ gate, PASS)
  - History max error: $0.000015$
  - Energy jump across transfer: **0.0%** ($\le 1.0\%$ gate, PASS)
  - Reaction force $RF_1$ jump across transfer: **0.0%** ($\le 2.0\%$ gate, PASS)
  - Phase bound violations: **0**
  - Healing count: **0**
  - SDV16 negative transitions: **0**
- **Claims**:
  - `technical_restart_result`: **PASS**
  - `controlled_fracture_state_transfer_result`: **PASS**
  - `mechanical_reequilibration_result`: **PASS**
  - `online_remeshing_validation`: **NOT_YET_CLAIMED**
  - `next_evolving_remesh_stage_ready`: **true**

---

## 2. Prepared Next Stage Package (`M2STATE_FRACFIX_RESTART2`)

- **Job Name**: `M2STATE_FRACFIX_RESTART2`
- **Location**: `models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART2`
- **Scientific Purpose**: Demonstrate Stage-2 evolving-remesh state transfer at a fracture-relevant pre-peak checkpoint ($u_1 = 0.007500\,\text{mm}$, $d_{\text{max}} = 0.428$) onto a refined nonmatching mesh (`PK10`, $N_{\text{phys}} = 9,876$, $29,628$ layered elements).
- **Dependency**: `M2STATE_FRACFIX_RESTART1` (`1386471.mmaster02`) at Step-2 frame 250 ($u_1 = 0.007500\,\text{mm}$).
- **Formulation**: $l_0 = 0.015\,\text{mm}$, $G_c = 0.0027\,\text{kN/mm}$, $E = 210.0\,\text{kN/mm}^2$, $\nu = 0.3$, $k = 1.0\times 10^{-7}$, thickness $= 1.0\,\text{mm}$
- **NPHYS Mapping**: $N_{\text{phys}} = 9,876$ carried in 5th property slot of U2/U4 headers.
- **Resource Request**: `select=1:ncpus=1:mem=16gb`, `walltime=01:30:00`, `queue=entry_imfdfkmq` (Measured runtime ~25 minutes, walltime conservative to prevent truncation).
- **Raw Execution Hashes**:
  - Input (`M2STATE_FRACFIX_RESTART2.inp`): `15deda2fe6aac8c153f5df043ca509ced4d9437e977353f194354e553043f22c`
  - Subroutine (`f42_mixed_uel.for`): `0bc4378179a35acd9954d20d3e07517f8e1c356ae07a23c40e7715cd7b56dce8`
  - Transfer Artifact (`STATE_TRANSFER_ARTIFACT.json`): `d537063702e502b7fd5db60312cdc5b09e2221d02e5217eb1b7052c63f623052`
  - Transfer Manifest (`TRANSFER_MANIFEST.json`): `9006f98c59e6de37c173b3441051708805a954fa80db0eb41f5b3ef4c61aa0ff`
  - PBS Script (`M2STATE_FRACFIX_RESTART2.pbs`): `50288c53cb47ef3e5cfff7f06deaa4c9dc232434e333800cd091819b8d685ed1`
  - Submit Wrapper (`submit_m2state_fracfix_restart2.sh`): `d254078b8e3d877f38adcda3710333fa8de943a3f6984bb91edc4fe46ce9bb08`
  - Package Manifest (`PACKAGE_MANIFEST.json`): `ba7caf69e7b56c37ae027d6cd40f9e6dbfccc8d16f96a4ed5a56e3e9547f1750`

---

## 3. Governance & Lineage Summary

- **Annotated Tag Lineage**:
  - `P43STATE2-FINAL1`: Commit `c86568b6e245aef04f144d5759ded1212865c3ce`.
- **Governance State**:
  - `authorization_ready_for_next_batch`: `true`
  - `direct_human_authorization_found`: `false`
  - `execution_authorized`: `false`
  - `submission_approved`: `false`
  - `maximum_jobs_now`: `0`
  - `qsub_called`: `false`
  - `HPC_submissions`: `0`
