# Project Current State

# Current Project State - Stage C Mode-II Overnight State-Transfer Restart Job Submitted & Running (1386471.mmaster02)

**Active Task**: `F43STATE-M2-SUBMIT1`  
**Date**: 2026-08-10  
**Active Agent**: `gemini-antigravity`  
**Task Status**: `batch_submitted_running`  

---

## 1. Submitted Mode-II State-Transfer Restart Job

Guarded submission completed successfully on HPC (`mlogin01.hrz.tu-freiberg.de`) after fail-closed read-only tag provenance audit and common preflight checks:

### Job 1: `1386471.mmaster02` (`M2STATE_FRACFIX_RESTART1`)
- **Status**: Running (`R`)
- **Scientific Purpose**: Demonstrate mechanically re-equilibrated continuation after transfer of a fracture-relevant Mode-II state ($u_1 = 0.005000\,\text{mm}$) onto a nonmatching remeshed mesh using current qualified UEL (`f42_mixed_uel.for`).
- **Source Checkpoint**: `M2ADAPT_MM_FRACFIX_PROD` (`1386469.mmaster02`) at $u_1 = 0.005000\,\text{mm}$ (Step-1 frame 500, $d_{\text{max}} = 0.1245$, $2,206$ physical elements).
- **Target Mesh**: `PK5` nonmatching remeshed mesh ($4,894$ physical elements: $4,766$ quads + $128$ tris, $4,998$ nodes, $14,682$ layered elements).
- **Formulation**: $l_0 = 0.015\,\text{mm}$, $G_c = 0.0027\,\text{kN/mm}$, $E = 210.0\,\text{kN/mm}^2$, $\nu = 0.3$, $k = 1.0\times 10^{-7}$, thickness $= 1.0\,\text{mm}$
- **NPHYS Contract**: $N_{\text{phys}} = 4,894$ carried in 5th property slot of U2/U4 headers ($p \to p$ mapping PASS).
- **Resources**: `select=1:ncpus=1:mem=8gb`, `walltime=08:00:00`, `queue=entry_imfdfkmq`
- **Raw Execution Hashes**:
  - Input (`M2STATE_FRACFIX_RESTART1.inp`): `211bcbc7aeade414818b1127656b054e16c1425d02321a474a8b63d5afdb181b`
  - Subroutine (`f42_mixed_uel.for`): `0bc4378179a35acd9954d20d3e07517f8e1c356ae07a23c40e7715cd7b56dce8`
  - Transfer Artifact (`STATE_TRANSFER_ARTIFACT.json`): `71b62a941abfa702aa7a327789fcbc4ffe158ec3bdba1a1fcbb0c6e9515b238e`
  - Transfer Manifest (`TRANSFER_MANIFEST.json`): `b60ab220605da5a4583149a725a53a7bc79f812b3dccee8e6d2c79f08aa7dfb8`
  - PBS Script (`M2STATE_FRACFIX_RESTART1.pbs`): `e0177e8f80a70aaec263b6b5bd34624b48b7e6b53d9133c4fb26e65dd42b5209`
  - Submit Wrapper (`submit_m2state_fracfix_restart1.sh`): `a2ec9bea11499c60e6eb5b31c00ad5918e77a739054ec8be59c2f441732b709f`
  - Package Manifest (`PACKAGE_MANIFEST.json`): `3893604892e982abc8f188223430dc6d674752a77b8342e117e3949a0b258bc7`

---

## 2. Governance & Lineage Summary

- **Annotated Tag Lineage**:
  - `P43STATE1-FINAL1`: Commit `c4256bc1fc3d1dc1e9576a475a25fa3938b530a3` (Tag object SHA: `b8b79e238d03383246b3f26ab59d09990b66498f`).
  - `Q43STATE1-FINAL1`: Commit `a75f940d80fa69e04f262a6bdf580164b486cb73` (Tag object SHA: `a75f940d80fa69e04f262a6bdf580164b486cb73`).
  - $P \to Q$ byte identity: All 7 execution files verified 100% byte-for-byte identical.
- **Governance State**:
  - `authorization_ready_for_overnight_restart`: `true`
  - `direct_human_authorization_found`: `true`
  - `execution_authorized`: `true`
  - `submission_approved`: `true`
  - `maximum_jobs_now`: `1`
  - `remaining_authorized_submissions`: `0` (Authority fully consumed)
  - `running_jobs_final`: `1` (`1386471.mmaster02`)
  - `queued_jobs_final`: `0`
  - `qsub_called`: `true`
  - `HPC_submissions`: `1`
