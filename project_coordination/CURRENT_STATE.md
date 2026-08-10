# Project Current State

# Current Project State - Stage C Mode-II Adaptive Production Pair Prepared (MM & PK5)

**Active Task**: `F43ADAPT-PROD-PREP1`  
**Date**: 2026-08-10  
**Active Agent**: `gemini-antigravity`  
**Task Status**: `preparation_complete_not_authorized`  

---

## 1. Mode-II Adaptive Production Packages Prepared & Validated

Deterministic production packages have been generated and validated under the frozen censoring-corrected comparison contract:

### Production Package 1: `M2ADAPT_MM_FRACFIX_PROD`
- **Candidate Lineage**: `F43REM4_MM` (Sizing: `MINIMUM_MAXIMUM`, $e^* \in [1.0\%, 5.0\%]$)
- **Mesh Totals**: $N_{\text{phys}} = 2,206$ physical elements ($2,137$ quads, $69$ trias), $2,294$ nodes, $6,618$ layered elements (U1: $2137$, U2: $2137$, U3: $69$, U4: $69$, CPE4: $2137$, CPE3: $69$)
- **Formulation**: $l_0 = 0.015\,\text{mm}$, $G_c = 0.0027\,\text{kN/mm}$, $E = 210.0\,\text{kN/mm}^2$, $\nu = 0.3$, $k = 1.0\times 10^{-7}$, thickness $= 1.0\,\text{mm}$
- **Loading**: Two-Step Pure Shear to $u_1 = 0.0100\,\text{mm}$ (Step-1 to $0.0050\,\text{mm}$, Step-2 to $0.0100\,\text{mm}$)
- **Output Sufficiency**: Field output `time interval=0.01`, node `U, RF`, RP `RF, U`, `UMATELEM SDV, S, EVOL`, global energy `ALLAE, ALLCD, ALLIE, ALLKE, ALLPD, ALLSE, ALLWK, ETOTAL`
- **Resources**: `select=1:ncpus=1:mem=8gb`, `walltime=02:00:00`, `queue=entry_imfdfkmq`
- **Raw SHA256 Hashes**:
  - Input (`M2ADAPT_MM_FRACFIX_PROD.inp`): `774c1385c111649b66dcc18e3990cef3b14c76acc64fc6809c586de3f1cfffb7`
  - Subroutine (`f42_mixed_uel.for`): `0bc4378179a35acd9954d20d3e07517f8e1c356ae07a23c40e7715cd7b56dce8`
  - PBS Script (`M2ADAPT_MM_FRACFIX_PROD.pbs`): `6409ff55a3af0b9bfbc8520aacc5b8d492d7f78c5768e308954392f2548e8010`
  - Submit Wrapper (`submit_m2adapt_mm_fracfix_prod.sh`): `3f3711663a97e5a2fc1cf0054464bddeead8213ab130513bf4a30760bef6eb8d`
  - Manifest (`PACKAGE_MANIFEST.json`): `eb44f05282a3c06edc2f0456027ba0ca583ac6e5b451cb0bf7edc0a752e1435d`

### Production Package 2: `M2ADAPT_PK5_FRACFIX_PROD`
- **Candidate Lineage**: `F43REM4_PK5` (Sizing: `UNIFORM_ERROR`, $e^* = 5.0\%$)
- **Mesh Totals**: $N_{\text{phys}} = 4,894$ physical elements ($4,766$ quads, $128$ trias), $4,998$ nodes, $14,682$ layered elements (U1: $4766$, U2: $4766$, U3: $128$, U4: $128$, CPE4: $4766$, CPE3: $128$)
- **Formulation**: $l_0 = 0.015\,\text{mm}$, $G_c = 0.0027\,\text{kN/mm}$, $E = 210.0\,\text{kN/mm}^2$, $\nu = 0.3$, $k = 1.0\times 10^{-7}$, thickness $= 1.0\,\text{mm}$
- **Loading**: Two-Step Pure Shear to $u_1 = 0.0100\,\text{mm}$ (Step-1 to $0.0050\,\text{mm}$, Step-2 to $0.0100\,\text{mm}$)
- **Output Sufficiency**: Field output `time interval=0.01`, node `U, RF`, RP `RF, U`, `UMATELEM SDV, S, EVOL`, global energy `ALLAE, ALLCD, ALLIE, ALLKE, ALLPD, ALLSE, ALLWK, ETOTAL`
- **Resources**: `select=1:ncpus=1:mem=8gb`, `walltime=04:00:00`, `queue=entry_imfdfkmq`
- **Raw SHA256 Hashes**:
  - Input (`M2ADAPT_PK5_FRACFIX_PROD.inp`): `32e67a70cce767c6d2f914f1f121bbfac421a9807a21256a645bf2406a339356`
  - Subroutine (`f42_mixed_uel.for`): `0bc4378179a35acd9954d20d3e07517f8e1c356ae07a23c40e7715cd7b56dce8`
  - PBS Script (`M2ADAPT_PK5_FRACFIX_PROD.pbs`): `316140e61e90f45e506b4eec7d19f921886213da803306acbaadd4b03f8311cb`
  - Submit Wrapper (`submit_m2adapt_pk5_fracfix_prod.sh`): `76fdd18e9809f8a7ca8ef34297b7ad4ba5d0039784364ebe6fd7f237f65084db`
  - Manifest (`PACKAGE_MANIFEST.json`): `f03a73511fd7683a42a9177e82cb277ed26456de5ea80b41028ce0eba0608b70`

---

## 2. Scientific Comparison Contract & Gate Provenance

- **Domain A**: $0 \le u_1 \le 0.009250\,\text{mm}$ (Common pre-peak / uniform domain)
- **Domain B**: $0.009250 < u_1 \le 0.0100\,\text{mm}$ (Adaptive-only continuation domain)
- **Uniform Roles**: $H_1$ = minimum pre-peak global response reference; $H_2$ = fine spatial resolution diagnostic
- **Classifications**:
  - `pre_peak_mesh_refinement_consistency`: `PASS`
  - `damage_initiation_mesh_consistency`: `PASS`
  - `initial_stiffness_mesh_consistency`: `PASS`
  - `matched_state_crack_path_convergence`: `FAIL` (Hausdorff $0.005443\,\text{mm} > 0.00375\,\text{mm}$)
  - `global_peak_force_convergence`: `UNRESOLVED_CENSORED`
  - `complete_uniform_fracture_reference`: `NONE`
- **Gate Provenance Audit**:
  - `work_area_gate_value`: `2.0%`
  - `work_area_gate_source`: `inherited_from_established_2pct_curve_difference_gate`
  - `RF_U_L2_gate`: `2.0%`
  - `energy_gate`: `1.0%` (when comparable energy values exist)
  - `crack_path_hausdorff_gate`: `0.00375 mm`

---

## 3. Governance and Authority Boundary

- `authorization_ready_for_adaptive_production`: `true`
- `direct_human_authorization_found`: `false`
- `execution_authorized`: `false`
- `submission_approved`: `false`
- `maximum_jobs_now`: `0`
- `remaining_authorized_submissions`: `0`
- `running_jobs_final`: `0`
- `queued_jobs_final`: `0`
- `qsub_called`: `false`
- `HPC_submissions`: `0`
