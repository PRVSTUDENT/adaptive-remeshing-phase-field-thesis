# Project Current State

# Current Project State - Stage C Mode-II Adaptive Production Pair Submitted & Running (MM & PK5)

**Active Task**: `F43ADAPT-PROD-SUBMIT1`  
**Date**: 2026-08-10  
**Active Agent**: `gemini-antigravity`  
**Task Status**: `batch_submitted_running`  

---

## 1. Submitted Mode-II Adaptive Production Jobs

Guarded submissions completed successfully on HPC (`mlogin01.hrz.tu-freiberg.de`) after fail-closed read-only tag provenance audit and common preflight checks:

### Job 1: `1386469.mmaster02` (`M2ADAPT_MM_FRACFIX_PROD`)
- **Status**: Running (`R`)
- **Candidate Lineage**: `F43REM4_MM` (Sizing: `MINIMUM_MAXIMUM`, $e^* \in [1.0\%, 5.0\%]$)
- **Mesh Totals**: $N_{\text{phys}} = 2,206$ physical elements ($2,137$ quads, $69$ trias), $2,294$ nodes, $6,618$ layered elements (U1: $2137$, U2: $2137$, U3: $69$, U4: $69$, CPE4: $2137$, CPE3: $69$)
- **Formulation**: $l_0 = 0.015\,\text{mm}$, $G_c = 0.0027\,\text{kN/mm}$, $E = 210.0\,\text{kN/mm}^2$, $\nu = 0.3$, $k = 1.0\times 10^{-7}$, thickness $= 1.0\,\text{mm}$
- **Loading**: Two-Step Pure Shear to $u_1 = 0.0100\,\text{mm}$ (Step-1 to $0.0050\,\text{mm}$, Step-2 to $0.0100\,\text{mm}$)
- **Resources**: `select=1:ncpus=1:mem=8gb`, `walltime=02:00:00`, `queue=entry_imfdfkmq`
- **Raw SHA256 Hashes**:
  - Input (`M2ADAPT_MM_FRACFIX_PROD.inp`): `774c1385c111649b66dcc18e3990cef3b14c76acc64fc6809c586de3f1cfffb7`
  - Subroutine (`f42_mixed_uel.for`): `0bc4378179a35acd9954d20d3e07517f8e1c356ae07a23c40e7715cd7b56dce8`
  - PBS Script (`M2ADAPT_MM_FRACFIX_PROD.pbs`): `6409ff55a3af0b9bfbc8520aacc5b8d492d7f78c5768e308954392f2548e8010`
  - Submit Wrapper (`submit_m2adapt_mm_fracfix_prod.sh`): `3f3711663a97e5a2fc1cf0054464bddeead8213ab130513bf4a30760bef6eb8d`
  - Manifest (`PACKAGE_MANIFEST.json`): `eb44f05282a3c06edc2f0456027ba0ca583ac6e5b451cb0bf7edc0a752e1435d`

### Job 2: `1386470.mmaster02` (`M2ADAPT_PK5_FRACFIX_PROD`)
- **Status**: Running (`R`)
- **Candidate Lineage**: `F43REM4_PK5` (Sizing: `UNIFORM_ERROR`, $e^* = 5.0\%$)
- **Mesh Totals**: $N_{\text{phys}} = 4,894$ physical elements ($4,766$ quads, $128$ trias), $4,998$ nodes, $14,682$ layered elements (U1: $4766$, U2: $4766$, U3: $128$, U4: $128$, CPE4: $4766$, CPE3: $128$)
- **Formulation**: $l_0 = 0.015\,\text{mm}$, $G_c = 0.0027\,\text{kN/mm}$, $E = 210.0\,\text{kN/mm}^2$, $\nu = 0.3$, $k = 1.0\times 10^{-7}$, thickness $= 1.0\,\text{mm}$
- **Loading**: Two-Step Pure Shear to $u_1 = 0.0100\,\text{mm}$ (Step-1 to $0.0050\,\text{mm}$, Step-2 to $0.0100\,\text{mm}$)
- **Resources**: `select=1:ncpus=1:mem=8gb`, `walltime=04:00:00`, `queue=entry_imfdfkmq`
- **Raw SHA256 Hashes**:
  - Input (`M2ADAPT_PK5_FRACFIX_PROD.inp`): `32e67a70cce767c6d2f914f1f121bbfac421a9807a21256a645bf2406a339356`
  - Subroutine (`f42_mixed_uel.for`): `0bc4378179a35acd9954d20d3e07517f8e1c356ae07a23c40e7715cd7b56dce8`
  - PBS Script (`M2ADAPT_PK5_FRACFIX_PROD.pbs`): `316140e61e90f45e506b4eec7d19f921886213da803306acbaadd4b03f8311cb`
  - Submit Wrapper (`submit_m2adapt_pk5_fracfix_prod.sh`): `76fdd18e9809f8a7ca8ef34297b7ad4ba5d0039784364ebe6fd7f237f65084db`
  - Manifest (`PACKAGE_MANIFEST.json`): `f03a73511fd7683a42a9177e82cb277ed26456de5ea80b41028ce0eba0608b70`

---

## 2. Provenance Audit & Governance Summary

- **Read-Only Tag Audit**:
  - `P43ADAPT1-FINAL1`: Created once at commit `99e40bf4ed5e64687cdd41c13ceba7c545a4f237` (Tag object SHA: `c70088af88a950295895774dc6a4335e377effa6`). Created after successful pre-anchor rehearsal; exact-P qualification passed (619 tests OK). Force push = `false`.
  - `Q43ADAPT1-FINAL1`: Created once at commit `39f52934ecff4f64cbf03f6f1c4df2fa5f056ec1` descending from P.
  - $P \to Q$ byte identity: All 10 execution files verified 100% byte-for-byte unchanged.
- **Authorization & Preflight Status**:
  - `direct_human_authorization_found`: `true`
  - `execution_authorized`: `true`
  - `submission_approved`: `true`
  - `maximum_jobs_now`: `2`
  - `remaining_authorized_submissions`: `0` (Authority fully consumed)
  - `running_jobs_final`: `2` (`1386469.mmaster02`, `1386470.mmaster02`)
  - `queued_jobs_final`: `0`
  - `qsub_called`: `true`
  - `HPC_submissions`: `2`
