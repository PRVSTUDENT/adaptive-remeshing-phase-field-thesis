# Session report: AUDIT-SIMULATION-ARTIFACTS-20260901

- Agent: `codex`
- Scope: read-only local and cluster audit of simulation and figure artifacts.
- Starting commit: `42762382e8e0f4a8fc87b43eb0ddfba06028bcaf`
- No files outside coordination metadata were changed; no HPC submission occurred.

## Findings

- Local repository inventory: 78 ODBs, 369 PNGs, and 154 PDFs; total ODB size approximately 6.6 GB.
- Molnár/Gravouil CAE evidence exists under `runs/molnar_single_notch_author_supplied_exact/.../cae_exports/` and the verification-package `02_Abaqus_CAE_Evidence/` and `03_Clean_Report_Figures/` directories.
- Accepted Mode-I standard evidence is tied to job `1398090.mmaster02`; its mesh/response artifacts are retained locally and documented in `models/pandey_kumar_mode1/PANDEY_KUMAR_MODE1_REPRODUCTION_REPORT.md`.
- MISESERI evidence exists under `runs/hpc/stage_c_miseseri/...`, `results/figures/miseseri_preanalysis/`, and `results/figures/stage_f/`.
- Mode-II H0/H1/H2 response and phase images exist under `results/figures/mode_ii_*` and `results/figures/molnar_lc015_h_convergence/`.
- State-transfer/restart ODBs and derived evidence exist under `runs/hpc/stage_d3/`, `runs/hpc/mode_ii_state_transfer/`, `models/state_transfer/`, and `results/supervisor_progress_update_detailed/figures/`.
- Cluster `qstat` confirms `1399632.mmaster02` is still running on `mnode097/0`; no matching final ODB was found in the searched cluster project/scratch paths.

## Exact artifact paths

All local paths are relative to repository root `D:\Master thesis\Adaptive remeshing`.

### Molnar/Gravouil single-notch evidence

- ODB: `runs/molnar_single_notch_author_supplied_exact/20260720_abaqus_cae_reproduction/work/Molnar_Author_SingleNotch_Exact.odb`
- CAE export directory: `runs/molnar_single_notch_author_supplied_exact/20260720_abaqus_cae_reproduction/cae_exports/`
- Mesh viewport: `runs/molnar_single_notch_author_supplied_exact/20260720_abaqus_cae_reproduction/cae_exports/cae_model_geometry_mesh.png`
- SDV15 at `U2 ~= 0.0020 mm`: `runs/molnar_single_notch_author_supplied_exact/20260720_abaqus_cae_reproduction/cae_exports/cae_sdv15_u2_0p0020.png`
- SDV15 at `U2 ~= 0.0050 mm`: `runs/molnar_single_notch_author_supplied_exact/20260720_abaqus_cae_reproduction/cae_exports/cae_sdv15_u2_0p0050.png`
- SDV15 at `U2 ~= 0.0060 mm`: `runs/molnar_single_notch_author_supplied_exact/20260720_abaqus_cae_reproduction/cae_exports/cae_sdv15_u2_0p0060.png`
- SDV15 at `U2 ~= 0.0070 mm`: `runs/molnar_single_notch_author_supplied_exact/20260720_abaqus_cae_reproduction/cae_exports/cae_sdv15_u2_0p0070.png`
- Final SDV15/SDV16: `runs/molnar_single_notch_author_supplied_exact/20260720_abaqus_cae_reproduction/cae_exports/cae_final_sdv15_contour.png` and `cae_final_sdv16_contour.png`
- Clean contours: `runs/molnar_single_notch_author_supplied_exact/20260720_abaqus_cae_reproduction/figure_review_v1/contours/`
- Summary panel: `runs/molnar_single_notch_author_supplied_exact/20260720_abaqus_cae_reproduction/figure_review_v1/panels/author_supplied_reproduction_summary_panel.png`
- Provenance/captions: `runs/molnar_single_notch_author_supplied_exact/20260720_abaqus_cae_reproduction/report/verification_package_staging/Molnar_Author_SingleNotch_Verification_Package_20260720/05_Reports/FIGURE_PROVENANCE.md` and `FIGURE_CAPTIONS.md`

### Molnar H-convergence and baseline

- H0/H1/H2 meshes: `models/generated/molnar_gravouil_2017/h_convergence_lc015/H0_exact/mesh_image.png`, `H1_h0025/mesh_image.png`, and `H2_pub_h0010/mesh_image.png`
- H-convergence figures: `results/figures/molnar_lc015_h_convergence/`
- Stage-A phase figures: `results/figures/stage_a_baseline/`
- Stage-A ODB: `runs/molnar_single_notch_unchanged/20260714_technical_gate_local/work/SingleNotch.odb`
- Stage-A extracted contours: `runs/molnar_single_notch_unchanged/20260714_technical_gate_local/extracted/`

### Pandey-Kumar Mode-I

- Job/result mapping: `models/pandey_kumar_mode1/PANDEY_KUMAR_MODE1_REPRODUCTION_REPORT.md`
- Accepted standard job `1398090.mmaster02`: `project_coordination/TASK_LEDGER.csv`, task `F505-SUBMIT-PK-MODE1-STANDARD-PFM-CORRECTED`
- Accepted standard extracted fields: `runs/hpc/paper_matched_single_notch_v2/extracted/`
- Current adaptive directory: `models/pandey_kumar_mode1/02_proposed_adaptive_refined/`
- Current local adaptive ODB: `models/pandey_kumar_mode1/02_proposed_adaptive_refined/PK_MODE1_PROPOSED_PFM.odb`
- `1398865` predecessor: `models/pandey_kumar_mode1/02_proposed_adaptive_refined/predecessor_1398865/`
- Invalidated `1398386` mesh image: `models/pandey_kumar_mode1/02_proposed_adaptive_refined/PK_MODE1_1398386_mesh_refined.png`
- Blunt-notch `1398807` image: `models/pandey_kumar_mode1/02_proposed_adaptive_refined/predecessor_1398807/PK_MODE1_1398807_mesh_distribution.png`
- Adaptivity audit: `models/pandey_kumar_mode1/PK_M1_ADAPTIVITY_FIDELITY_AUDIT/PK_M1_ADAPTIVITY_FIDELITY_REPORT.json`

The `1398386` and `1398807` images are diagnostic evidence, not accepted final adaptive results.

### MISESERI/native refinement

- Spatial map and histogram: `results/figures/stage_f/miseseri_official_pbs_spatial_map.png` and `miseseri_official_pbs_histogram.png`
- Marking statistics: `results/tables/stage_f/miseseri_official_pbs_marking_statistics.csv`
- Native-remesh manifest: `results/processed/stage_f/miseseri_native_remesh_audit_manifest.json`
- Stage-C evidence directory: `runs/hpc/stage_c_miseseri/molnar_h0_miseseri_preanalysis/evidence/1376296.mmaster02/`
- Raw and processed fields: `JOB2_MISESERI_ELEMENT_DATA_raw.csv` and `JOB2_MISESERI_ELEMENT_DATA.csv` in that directory
- Compact field panel: `results/supervisor_progress_update_detailed/figures/stage_c_field_evidence.png`
- Threshold image: `results/supervisor_progress_update_detailed/figures/miseseri_threshold_elements.png`

### Mode-II H0/H1/H2

- H0: `results/figures/mode_ii_h0_endpoint_corrected/1379393.mmaster02/`
- H1: `results/figures/mode_ii_h1/1379433.mmaster02/`
- H1 sweeps: `results/figures/mode_ii_h1_endpoint_sweep/`
- H2: `results/figures/mode_ii_h2/`
- H0/H1/H2 comparison: `results/figures/mode_ii_reference_convergence/`
- Crack trajectory: `results/figures/mode_ii_h2/fig_mode2_crack_trajectory.png`
- H1 contour CSV evidence: `runs/hpc/stage_f/mode_ii_h1/evidence/1379433.mmaster02/extracted/`
- H2 full-reference evidence: `runs/hpc/mode_ii_state_transfer/evidence/1389352.mmaster02/`

### State transfer and restart

- Canonical model tree: `models/state_transfer/`
- Donor/receiver meshes: `models/state_transfer/d3_interrupted_transfer/source/` and `models/state_transfer/d3_interrupted_transfer/target/`
- Runtime ingestion: `runs/hpc/stage_d3/interrupted_transfer/target_ingestion_r4_compatible/`
- State by frame: `runs/hpc/stage_d3/interrupted_transfer/target_ingestion_r4_compatible/D3A3_R4_STATE_BY_FRAME.csv`
- Transfer-vs-ODB: `runs/hpc/stage_d3/interrupted_transfer/target_ingestion_r4_compatible/D3A3_R4_TRANSFER_VS_ODB.csv`
- Topology continuation: `runs/hpc/stage_d3/fracture_continuation/d3d_active_set_segment/`
- Stage-F topology ODB: `models/generated/mode_ii/stage_f_topology_batch/M2CORR_STAGE_F_CYCLE2_MULTISTEP_TRANSFER/M2CORR_STAGE_F_CYCLE2_MULTISTEP_TRANSFER.odb`
- Existing graphics: `results/supervisor_progress_update_detailed/figures/checkpoint_phase_history_fields.png`, `fig_c2_damage_localization.png`, and `results/figures/stage_f/fig_stage_f_transfer_continuation.png`

### Cluster paths

- Login command: `ssh -F "$env:USERPROFILE\\.ssh\\codex_config" tu_freiberg`
- Project root: `/home/pr21vyci/projects/adaptive-remeshing`
- Task-5 directory: `/home/pr21vyci/projects/adaptive-remeshing/models/pandey_kumar_mode1/02_proposed_adaptive_refined`
- Expected ODB: `/home/pr21vyci/projects/adaptive-remeshing/models/pandey_kumar_mode1/02_proposed_adaptive_refined/PK_MODE1_PROPOSED_PFM.odb`
- Scratch root searched: `/scratch/pr21vyci`
- Audit-time state: `1399632.mmaster02` running on `mnode097/0`; no terminal classification was made.

## Representative verified image observations

- `cae_sdv15_u2_0p0050.png`: actual Abaqus CAE contour export from the Molnár author-supplied exact ODB, but its legend is not normalized to 0--1 and therefore should not be inserted into the new report without controlled restyling/captioning.
- `miseseri_official_pbs_spatial_map.png`: derived MISESERI spatial evidence, currently a scatter visualization rather than an Abaqus viewport contour.
- `PK_MODE1_1398386_mesh_refined.png`: adaptive mesh visualization from a scientifically invalidated candidate with missing triangle UEL branches; not suitable as final production evidence.
- `stage_c_field_evidence.png`: compact comparison of MISESERI and phase fields at matched displacement, useful as a source/reference but requiring provenance-aware captioning.

## Conclusion

The absence of images in the September pack is packaging/integration failure, not absence of simulation evidence. Existing images must be triaged by source job and qualification status before copying into the pack. The highest-confidence immediate source is the Molnár CAE evidence package; the final adaptive Task-5 images remain blocked by the running job.
