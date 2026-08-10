# Project Current State

# Current Project State - Stage C Mode-II Adaptive Production Pair Terminal PASS (MM & PK5)

**Active Task**: `F43ADAPT-PROD-TERMINALCHECK1`  
**Date**: 2026-08-10  
**Active Agent**: `gemini-antigravity`  
**Task Status**: `production_jobs_complete_pass`  

---

## 1. Mode-II Adaptive Production Solve Terminal Results

Both adaptive production runs completed 100% successfully on HPC node `mnode099` to full prescribed endpoint $u_1 = 0.01000\,\text{mm}$ ($10.0\,\mu\text{m}$, 2,500 total increments, 0 cutbacks):

### Job 1: `1386469.mmaster02` (`M2ADAPT_MM_FRACFIX_PROD`)
- **Scheduler Result**: `PASS` (`exit_status = 0`, `job_state = F`)
- **Technical Result**: `PASS` (Abaqus completed successfully, `Step-2` increment `2000`, $u_1 = 0.010000\,\text{mm}$)
- **Scientific Result**: `PENDING_EXTRACTION` (Complete ODB/DAT dataset ready for scientific extraction)
- **Candidate Lineage**: `F43REM4_MM` (Sizing: `MINIMUM_MAXIMUM`, $e^* \in [1.0\%, 5.0\%]$)
- **Mesh Totals**: $N_{\text{phys}} = 2,206$ physical elements ($2,137$ quads, $69$ trias), $2,294$ nodes, $6,618$ layered elements
- **Formulation**: $l_0 = 0.015\,\text{mm}$, $G_c = 0.0027\,\text{kN/mm}$, $E = 210.0\,\text{kN/mm}^2$, $\nu = 0.3$, $k = 1.0\times 10^{-7}$, thickness $= 1.0\,\text{mm}$
- **Runtime Performance**:
  - **CPU Time**: $164.0\,\text{s}$ ($00:02:44$)
  - **Walltime**: $166.0\,\text{s}$ ($00:02:46$)
  - **Peak Memory**: $4.86\,\text{GB}$ ($5,092,040\,\text{KB}$) / VMEM $7.58\,\text{GB}$
  - **Speedup vs Uniform $H_2$**: **$88.1\times$ CPU speedup** ($164\,\text{s}$ vs $14,455\,\text{s}$)
- **Raw Execution Hashes**:
  - Input (`M2ADAPT_MM_FRACFIX_PROD.inp`): `774c1385c111649b66dcc18e3990cef3b14c76acc64fc6809c586de3f1cfffb7`
  - Subroutine (`f42_mixed_uel.for`): `0bc4378179a35acd9954d20d3e07517f8e1c356ae07a23c40e7715cd7b56dce8`
  - PBS Script (`M2ADAPT_MM_FRACFIX_PROD.pbs`): `6409ff55a3af0b9bfbc8520aacc5b8d492d7f78c5768e308954392f2548e8010`
  - Submit Wrapper (`submit_m2adapt_mm_fracfix_prod.sh`): `3f3711663a97e5a2fc1cf0054464bddeead8213ab130513bf4a30760bef6eb8d`
  - Manifest (`PACKAGE_MANIFEST.json`): `eb44f05282a3c06edc2f0456027ba0ca583ac6e5b451cb0bf7edc0a752e1435d`

### Job 2: `1386470.mmaster02` (`M2ADAPT_PK5_FRACFIX_PROD`)
- **Scheduler Result**: `PASS` (`exit_status = 0`, `job_state = F`)
- **Technical Result**: `PASS` (Abaqus completed successfully, `Step-2` increment `2000`, $u_1 = 0.010000\,\text{mm}$)
- **Scientific Result**: `PENDING_EXTRACTION` (Complete ODB/DAT dataset ready for scientific extraction)
- **Candidate Lineage**: `F43REM4_PK5` (Sizing: `UNIFORM_ERROR`, $e^* = 5.0\%$)
- **Mesh Totals**: $N_{\text{phys}} = 4,894$ physical elements ($4,766$ quads, $128$ trias), $4,998$ nodes, $14,682$ layered elements
- **Formulation**: $l_0 = 0.015\,\text{mm}$, $G_c = 0.0027\,\text{kN/mm}$, $E = 210.0\,\text{kN/mm}^2$, $\nu = 0.3$, $k = 1.0\times 10^{-7}$, thickness $= 1.0\,\text{mm}$
- **Runtime Performance**:
  - **CPU Time**: $366.0\,\text{s}$ ($00:06:06$)
  - **Walltime**: $368.0\,\text{s}$ ($00:06:08$)
  - **Peak Memory**: $10.12\,\text{GB}$ ($10,609,204\,\text{KB}$) / VMEM $12.90\,\text{GB}$
  - **Speedup vs Uniform $H_2$**: **$39.5\times$ CPU speedup** ($366\,\text{s}$ vs $14,455\,\text{s}$)
- **Raw Execution Hashes**:
  - Input (`M2ADAPT_PK5_FRACFIX_PROD.inp`): `32e67a70cce767c6d2f914f1f121bbfac421a9807a21256a645bf2406a339356`
  - Subroutine (`f42_mixed_uel.for`): `0bc4378179a35acd9954d20d3e07517f8e1c356ae07a23c40e7715cd7b56dce8`
  - PBS Script (`M2ADAPT_PK5_FRACFIX_PROD.pbs`): `316140e61e90f45e506b4eec7d19f921886213da803306acbaadd4b03f8311cb`
  - Submit Wrapper (`submit_m2adapt_pk5_fracfix_prod.sh`): `76fdd18e9809f8a7ca8ef34297b7ad4ba5d0039784364ebe6fd7f237f65084db`
  - Manifest (`PACKAGE_MANIFEST.json`): `f03a73511fd7683a42a9177e82cb277ed26456de5ea80b41028ce0eba0608b70`

---

## 2. Governance and Active Queue Boundary

- `running_jobs`: `0`
- `queued_jobs`: `0`
- `automatic_retry`: `false`
- `replacement_submission`: `false`
- `execution_authorized`: `false`
- `submission_approved`: `false`
- `maximum_jobs_now`: `0`
- `remaining_authorized_submissions`: `0`
- `qsub_called`: `false`
- `HPC_submissions`: `0`
