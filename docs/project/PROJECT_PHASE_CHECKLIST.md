# Project Phase Checklist

## F24 official adaptive contract & ODB compatibility gate

- [x] Official Abaqus 11-rule adaptive remeshing contract established.
- [x] Workstream A geometry-backed 17-step model-construction order specified.
- [x] Workstream B ODB compatibility audit completed (`M2MISER1.odb` region correspondence invalid for geometry-backed remeshing rule).
- [x] Selected Outcome B (`matching_geometry_backed_provisional_analysis_required`).
- [x] Prepared provisional analysis package `M2RMPROV1` without submission. `M2RMEXEC2` not prepared.
- [x] Classification: `f24_m2rmprov1_clean_linux_qualified_not_authorized`. `execution_authorized = false`.

## F23 offline adaptive-region association investigation gate

- [x] F20 vs F21 contract comparison completed. F20 checked rule existence and non-null region; F21 executed `model.adaptiveRemesh(odb)` and failed with 0 adaptive regions.
- [x] Evaluated 4 adaptive-region association hypotheses offline; Outcome B (`adaptive_region_association_unresolved_offline`) selected due to multiple unresolved hypotheses requiring CAE execution.
- [x] Prepared deterministic pre-call recognition audit specification (`PRECALL_RECOGNITION_AUDIT_SPEC.json`).
- [x] Audited and defined evidence-retention repairs for future wrappers (`EVIDENCE_RETENTION_REPAIR_AUDIT.json`).
- [x] No HPC job prepared (`M2RMEXEC2` is false). Qsub attempts = 0, execution authority = false.

## F21 native-remesh candidate gate

- [!] Job `1382435` failed with no adaptive regions; no candidate or next job.

- [x] M2RMREG7 adaptive-region construction contract qualified.
- [x] Prepare one-call `M2RMEXEC1` native-remesh package without execution.
- [x] Exact M2RMEXEC1 authorization consumed by guarded job `1382435.mmaster02`.
- [ ] Execute and review native-remesh candidate before datacheck preparation.

Updated: 2026-08-04

This is the authoritative living task and phase checklist for the adaptive remeshing thesis workspace. Update this same file after every substantial task, run, validation, failure, retry, decision, gate transition, and phase completion. Do not create duplicate phase checklists.

Status markers:

- `[x]` completed and supported by evidence
- `[ ]` not started
- `[-]` in progress
- `[!]` blocked
- `[?]` awaiting review, approval, or missing evidence
- `[~]` completed provisionally but not scientifically validated

Gate A3 (RF–U validation use): **conditionally accepted** — supervisor Decisions **1A** and **2B**  
Internal status: `gate_a3_conditionally_accepted_rf_u`; `contour_validation_deferred`; `stage_c_miseseri_preparation_authorized`  
HPC submission: **not authorized** without explicit new approval  
Stage A: `frozen_with_residual_scientific_limitations` (conditional Gate-A3
RF–U acceptance does not remove provisional tolerances, post-peak dependence,
or deferred contour/crack-path evidence)

## Overall Phase Dashboard

| Phase | Description | Status | Gate/result | Evidence |
|---|---|---|---|---|
| WP0 | Environment, starter pipeline, and source preservation | `[x]` completed | technical environment passed | `.agent.md`; `models/baseline_original/molnar_gravouil_2017/README.md`; `hpc_access_limits_report.txt` |
| WP1 | One-element verification | `[~]` completed provisionally | source-defined numerical checks passed under provisional tolerances | `runs/molnar_one_element_unchanged/20260714_technical_gate_local/scientific_check/` |
| WP2A | Supplementary Molnar single-notch technical benchmark | `[~]` completed provisionally | technical pass; not exact Fig. 7 comparison | `runs/molnar_single_notch_unchanged/20260714_technical_gate_local/` |
| WP2B | Paper-matched Molnar reconstruction | `[~]` completed provisionally | technical pass; scientific review incomplete | `runs/hpc/paper_matched_single_notch_v2/RUN_MANIFEST.md`; `runs/hpc/paper_matched_single_notch_v2/scientific_review/SCIENTIFIC_DECISION.md` |
| Gate A3 | Uniform RF–U reference scientific justification | `[~]` conditionally accepted for RF–U | 1A mesh roles + 2B contour deferred; H2-PUB validation / H1 production / H0 test | `docs/decisions/MOLNAR_GATE_A3_SUPERVISOR_DECISION_1A_2B.md`; `docs/decisions/MESH_USE_POLICY.md`; `docs/decisions/MOLNAR_MESH_ROLE_AND_RESULT_FREEZE.md` |
| WP3 | MISESERI pre-analysis and remeshing reproduction | `[x]` closed at scoped Stage C result | C2C-v3 frozen; T5 preserved as failed guard evidence | `docs/decisions/STAGE_C_CLOSEOUT_FREEZE.md`; `runs/hpc/stage_c2/STAGE_C_FINAL_STATUS.md` |
| WP4 | Refined phase-field benchmark and efficiency comparison | `[x]` closed at scoped Stage C result | peak/pre-peak supported; post-peak limited; crack-path H1 equivalence not supported | `runs/hpc/stage_c2/closeout/STAGE_C_CLOSEOUT_JOB_SUMMARY.md` |
| WP5 | Evolving remesh and state transfer | `[~]` scoped completion with limitation | bounded pre-peak transfer proven; corrected mechanical restart unproven | `docs/thesis/STAGE_D_STATE_TRANSFER_SYNTHESIS.tex`; `docs/decisions/STAGE_D3D_A1H0_EXECUTION_CLOSURE.md` |
| WP6 | IMFD/ABAQUSER integration | `[!]` externally blocked | interface executable/module/source unavailable; independent extraction retained | `docs/decisions/WP6_ABAQUSER_EXTERNAL_BLOCK_CLOSURE.md` |
| WP7 | Final recommendations and thesis writing | `[~]` faculty-format candidate ready; human/admin gates open | `wp7_faculty_template_integration_candidate`; not ready_for_submission | `docs/decisions/WP7_FACULTY_TEMPLATE_INTEGRATION.md`; `results/final/THESIS_FACULTY_PACKAGE_MANIFEST.json` |
| Stage F | Mode-II mixed-mode benchmark | `[!]` F6 complete_failed | H2 full solve completed but failed irreversibility gate; native remesh API audit did not start | `docs/experiment_records/STAGE_F6_H2_U020_FULL_CLOSEOUT.md`; `docs/experiment_records/STAGE_F6_MISESERI_REMESH_API_QUALIFICATION.md` |



## WP0 - Environment, Starter Pipeline, And Source Preservation

- [x] Repository structure created. Evidence: `README.md`, `WORKSPACE_STRUCTURE.md`, `.agent.md`.
- [x] Original Molnar source and decks preserved with hashes. Evidence: `models/baseline_original/molnar_gravouil_2017/README.md`.
- [x] Local compiler/linker smoke test passed. Evidence: `.agent.md`; `docs/reports/STAGE_A_BASELINE_REPORT.tex`.
- [x] HPC SSH access restored and verified. Evidence: `.agent.md`; `hpc_access_limits_report.txt`.
- [x] HPC home and scratch layout created. Evidence: `.agent.md`; `docs/reports/STAGE_A_EXECUTION_AND_FAILURE_LOG.tex`.
- [x] HPC repository clone synchronized. Evidence: `.agent.md`; `docs/reports/STAGE_A_EXECUTION_AND_FAILURE_LOG.tex`.
- [x] HPC PBS environment smoke passed. Run: `1374531.mmaster02`. Classification: `hpc_environment_smoke_pass`. Evidence: `docs/reports/STAGE_A_EXECUTION_AND_FAILURE_LOG.tex`.
- [x] HPC Abaqus license checkout passed. Run: `1374533.mmaster02`. Evidence: `docs/reports/STAGE_A_EXECUTION_AND_FAILURE_LOG.tex`.
- [x] HPC Fortran compilation passed. Run: `1374533.mmaster02`. Evidence: `docs/reports/STAGE_A_EXECUTION_AND_FAILURE_LOG.tex`.
- [x] HPC user-subroutine linking passed. Run: `1374533.mmaster02`. Evidence: `docs/reports/STAGE_A_EXECUTION_AND_FAILURE_LOG.tex`.
- [x] Deterministic UEXTERNALDB callback test passed. Run: `1374533.mmaster02`. Commit: `c5db808b4c8d9e9bd01a9e5da0bd91b173787b8e`. Classification: `hpc_user_subroutine_smoke_pass`. Evidence: `docs/reports/STAGE_A_EXECUTION_AND_FAILURE_LOG.tex`.
- [x] Successful callback retry evidence committed. Commit: `2022652dd181e55e61ab46d56de7d0463039447a`. Evidence: `.agent.md`.
- [x] Permanent PBS email-notification rule recorded for future submissions. Requirement: keep `#PBS -m abe` in tracked PBS scripts, pass the private recipient with `qsub -M "<verified_recipient>" -m abe`, validate before the first submission with `scripts/hpc/validate_pbs_email_notifications.py`, and verify `Mail_Users`/`Mail_Points` after submission. Boundary: completed job `1374864.mmaster02` remains unchanged. Evidence: `.agent.md`; `scripts/hpc/validate_pbs_email_notifications.py`.
- [x] HPC notification recipient recorded as historically scheduler-verified. Address: `pr21vyci@mailserver.tu-freiberg.de`. Evidence: old-project PBS `qstat` record for job `1362636.mmaster02` reported `Mail_Users = pr21vyci@mailserver.tu-freiberg.de` and `Mail_Points = abe`; inbox delivery not independently documented. Future submissions must pass this address privately with `qsub -M`.

### Preserved Diagnostic Failures

- [x] Environment smoke failure diagnosed: IFX/GCC environment. Run: `1374529.mmaster02`. Evidence: `docs/reports/STAGE_A_EXECUTION_AND_FAILURE_LOG.tex`.
- [x] Environment rerun failure diagnosed: Git unavailable in batch PATH. Run: `1374530.mmaster02`. Evidence: `docs/reports/STAGE_A_EXECUTION_AND_FAILURE_LOG.tex`.
- [x] Initial UEXTERNALDB marker failure investigated. Run: `1374532.mmaster02`. Result: `insufficient_retained_evidence`. Evidence: `docs/reports/STAGE_A_EXECUTION_AND_FAILURE_LOG.tex`.
- [x] Deterministic callback repair prepared and validated. Evidence: `docs/reports/STAGE_A_EXECUTION_AND_FAILURE_LOG.tex`.
- [x] Deterministic callback retry passed. Run: `1374533.mmaster02`. Classification: `hpc_user_subroutine_smoke_pass`. Evidence: `docs/reports/STAGE_A_EXECUTION_AND_FAILURE_LOG.tex`.

## WP1 - One-Element Verification

- [x] Unchanged one-element technical run passed. Evidence: `runs/molnar_one_element_unchanged/20260714_technical_gate_local/RUN_SUMMARY.md`.
- [~] One-element scientific/source-relation checks passed under provisional tolerances. Evidence: `runs/molnar_one_element_unchanged/20260714_technical_gate_local/scientific_check/ONE_ELEMENT_SCIENTIFIC_CHECK.md`. Limitation: final supervisor-approved tolerances pending.
- [?] Final supervisor-approved numerical tolerances remain pending. Next action: obtain approved tolerance policy before final validation claims.

## WP2A - Supplementary Single-Notch Model

- [x] Original source and input hashes verified unchanged. Evidence: `models/baseline_original/molnar_gravouil_2017/README.md`.
- [x] Supplementary single-notch technical run passed. Evidence: `runs/molnar_single_notch_unchanged/20260714_technical_gate_local/RUN_SUMMARY.md`.
- [x] RF-displacement extraction completed. Evidence: `runs/molnar_single_notch_unchanged/20260714_technical_gate_local/extracted/SINGLE_NOTCH_EXTRACTION.md`.
- [x] SDV14, SDV15, and SDV16 diagnostics completed. Evidence: `runs/molnar_single_notch_unchanged/20260714_technical_gate_local/extracted/`.
- [x] Crack-path extraction completed. Evidence: `runs/molnar_single_notch_unchanged/20260714_technical_gate_local/scientific_check/crack_path_comparison.csv`.
- [x] Local irreversibility diagnostics completed. Evidence: `docs/reports/STAGE_A_BASELINE_REPORT.tex`.
- [~] Supplementary model accepted as supporting technical reproducibility evidence. Evidence: `references/derived/molnar_gravouil_2017/single_notch/REFERENCE_APPLICABILITY_MATRIX.md`. Limitation: not exact Fig. 7 comparison target.
- [!] Exact paper-curve validation is not justified for this smaller model. Blocking issue: paper-matched reconstruction and approximate paper reference required.

## WP2B - Paper-Matched Molnar Reconstruction

- [x] Paper-to-model reconstruction audit completed. Evidence: `references/derived/molnar_gravouil_2017/paper_matched_single_notch/PAPER_TO_MODEL_SPECIFICATION.md`.
- [x] Parameter-provenance table created. Evidence: `references/derived/molnar_gravouil_2017/paper_matched_single_notch/PARAMETER_PROVENANCE.csv`.
- [x] Fig. 6 and Fig. 7 audit created. Evidence: `references/derived/molnar_gravouil_2017/paper_matched_single_notch/FIGURE_REFERENCE_AUDIT.md`.
- [x] Digitization plan created. Evidence: `references/derived/molnar_gravouil_2017/paper_matched_single_notch/FIG7_DIGITIZATION_PLAN.md`.
- [x] Non-runnable YAML configuration created. Evidence: `configs/molnar_paper_matched_single_notch.yaml`.
- [x] Fig. 7 target-curve coordinates resolved as approximate published reference. Evidence: `references/derived/molnar_gravouil_2017/paper_matched_single_notch/fig7_lc_0p0075_processed.csv`; `references/derived/molnar_gravouil_2017/paper_matched_single_notch/FIG7_DIGITIZATION_METADATA.md`. Limitation: not exact author data.
- [~] Final loading endpoint and increment schedule resolved for candidate v1. Evidence: `configs/molnar_paper_matched_single_notch.yaml`. Limitation: final displacement measured from Fig. 7 extent, not explicitly stated.
- [~] Contour comparison states resolved as response-based rules. Evidence: `configs/molnar_paper_matched_single_notch.yaml`. Limitation: Fig. 6b has no numerical displacement labels.
- [~] Refined-zone and mesh-transition recipe resolved as adopted reconstruction choice. Evidence: `configs/molnar_paper_matched_single_notch.yaml`; `references/derived/molnar_gravouil_2017/paper_matched_single_notch/PARAMETER_PROVENANCE.csv`. Limitation: not a published mesh parameter.
- [x] Mesh-count estimator created and checks passed. Evidence: `scripts/model_generation/estimate_molnar_paper_mesh.py`; generated result in `models/generated/molnar_gravouil_2017/paper_matched_single_notch_v1/mesh_statistics.csv`.
- [x] Deterministic paper-matched deck generator created. Evidence: `scripts/model_generation/build_molnar_paper_matched_single_notch.py`.
- [~] `paper_matched_candidate_v1` generated. Evidence: `models/generated/molnar_gravouil_2017/paper_matched_single_notch_v1/`. Classification: generated candidate, not runnable.
- [x] Candidate-v1 static failure diagnosed. Evidence: `results/validation/molnar_paper_matched_single_notch_v1/STATIC_VALIDATION.md`; `results/validation/molnar_paper_matched_single_notch_v1/FAILURE_MANIFEST.md`. Classification: `static_validation_fail`; `runnable: false`.
- [x] Review generated parameters against provenance. Evidence: `results/validation/molnar_paper_matched_single_notch_v1/PARAMETER_PROVENANCE_REVIEW.md`.
- [x] Candidate-v2 loading schedule resolved. Evidence: `references/derived/molnar_gravouil_2017/paper_matched_single_notch/LOADING_SCHEDULE_RESOLUTION.md`.
- [x] Candidate-v2 notch implementation documented. Evidence: `references/derived/molnar_gravouil_2017/paper_matched_single_notch/NOTCH_IMPLEMENTATION.md`.
- [x] Candidate-v2 layered UEL/UMAT mapping documented. Evidence: `docs/methods/MOLNAR_LAYERED_DECK_MAPPING.md`.
- [x] Candidate-v2 boundary-condition mapping documented. Evidence: `references/derived/molnar_gravouil_2017/paper_matched_single_notch/BOUNDARY_CONDITION_MAPPING.md`.
- [x] Candidate-v2 generated. Evidence: `models/generated/molnar_gravouil_2017/paper_matched_single_notch_v2/`.
- [x] Candidate-v2 static validation passed. Evidence: `results/validation/molnar_paper_matched_single_notch_v2/STATIC_VALIDATION.md`; `results/validation/molnar_paper_matched_single_notch_v2/VALIDATION_RESULTS.json`. Classification: `static_validation_pass`; `runnable: true`.
- [x] Candidate-v2 generated source copy prepared. Evidence: `models/generated/molnar_gravouil_2017/paper_matched_single_notch_v2/SingleNotch_v2.for`; generated from preserved `SingleNotch.for` with `N_ELEM=33852`; preserved source remains unchanged.
- [x] Final mesh-quality preflight passed. Evidence: `results/validation/molnar_paper_matched_single_notch_v2/MESH_QUALITY_PREFLIGHT.md`. Limitation: high-aspect-ratio elements are documented reconstruction limitations outside the refined fracture corridor.
- [x] Commit and synchronize candidate v2. Evidence: commit `711dd495bdcb830d695f9d7e56283316c9d417d5`; HPC clone synchronized cleanly to the same revision before submission.
- [x] One serial HPC baseline run submitted exactly once. Evidence: PBS job `1374864.mmaster02`; submitted from revision `711dd495bdcb830d695f9d7e56283316c9d417d5`; initial scheduler state `R` on `mnode099`.
- [x] Execute one paper-matched baseline. Result: `paper_matched_v2_technical_pass`; PBS `Exit_status = 0`; Abaqus return code zero; ODB/STA/MSG/DAT present; STA reports successful completion. Evidence: `runs/hpc/paper_matched_single_notch_v2/evidence/TECHNICAL_SUMMARY.txt`; `runs/hpc/paper_matched_single_notch_v2/evidence/qstat_xf_1374864_final.txt`.
- [x] Exact HPC notification address recorded for future private submission. Address: `pr21vyci@mailserver.tu-freiberg.de`; verification status: `historically_scheduler_verified`; pass privately with `qsub -M` and verify `Mail_Users`/`Mail_Points` after submission.
- [x] Extract RF-displacement and response-based phase/SDV contours from the completed ODB without rerunning Abaqus. Evidence: `runs/hpc/paper_matched_single_notch_v2/extracted/`.
- [~] Compare with approximate published Fig. 7 reference. Result: `scientific_review_required`; peak RF2 `0.761702 kN` at `U2=0.006110 mm`; RF-U NRMSE `0.247493` in the original scientific check and `0.245705` in the no-solution forensic overlap audit; relative peak-force error `0.064519`; relative peak-displacement error `0.041257`. Evidence: `runs/hpc/paper_matched_single_notch_v2/scientific_check/SINGLE_NOTCH_SCIENTIFIC_CHECK.md`; `runs/hpc/paper_matched_single_notch_v2/scientific_review/FIG7_COMPARISON_AUDIT.md`.
- [~] Crack-path and SDV diagnostics completed. Result: final element-mean `SDV15 >= 0.95` crack extension about `0.0505 mm`; `SDV16` monotonic; detailed SDV15 review reproduced `6113` decrease events and mapping resolution reclassified the remaining `817` non-staggered events as `insufficient_output_evidence`. Evidence: `runs/hpc/paper_matched_single_notch_v2/scientific_review/CRACK_PATH_AUDIT.md`; `runs/hpc/paper_matched_single_notch_v2/scientific_review/SDV15_IRREVERSIBILITY_AUDIT.md`; `runs/hpc/paper_matched_single_notch_v2/scientific_review/SDV16_MONOTONICITY_AUDIT.md`; `runs/hpc/paper_matched_single_notch_v2/scientific_review/sdv15_detailed_review/SDV15_DETAILED_EVENT_DECISION.md`; `runs/hpc/paper_matched_single_notch_v2/scientific_review/sdv15_mapping_resolution/SDV15_MAPPING_RESOLUTION_DECISION.md`.
- [~] Scientific decision report completed. Result: `paper_matched_v2_scientific_review_incomplete`; post-peak RF-U mismatch dominates, crack path is connected/horizontal but threshold-dependent, SDV15 label/IP mapping is resolved, and retained outputs still leave `817` above-precision non-staggered events as `insufficient_output_evidence`. Evidence: `runs/hpc/paper_matched_single_notch_v2/scientific_review/SCIENTIFIC_DECISION.md`; `runs/hpc/paper_matched_single_notch_v2/scientific_review/sdv15_detailed_review/sdv15_decrease_events_full.csv`; `runs/hpc/paper_matched_single_notch_v2/scientific_review/sdv15_mapping_resolution/sdv15_unresolved_event_mapping.csv`.
- [?] Gate A3 supervisor-review package prepared. Result: no supervisor decision inferred; routes documented as provisional pass, waiver with limitations, keep open, or candidate-v2 scientific fail. Evidence: `docs/decisions/MOLNAR_GATE_A3_SUPERVISOR_REVIEW.md`; `docs/decisions/MOLNAR_TARGETED_OUTPUT_RERUN_REQUIREMENTS.md`; `docs/handoffs/MOLNAR_GATE_A3_MEETING_SUMMARY.md`.
- [x] Perform mesh-size / h-convergence RF–U study (lc=0.015). Solvers H0/H1/H2 technical pass; CAE job `1376236` RF–U pass; formal analysis complete. Peak/pre-peak supported; post-peak not fully demonstrated; contours not assessed. Evidence: `docs/decisions/MOLNAR_LC015_H_CONVERGENCE_SCIENTIFIC_DECISION.md`; `runs/hpc/molnar_lc015_h_convergence/comparison/H_CONVERGENCE_SCIENTIFIC_REVIEW.md`.
- [x] Select provisional RF–U meshes from analysis: H2-PUB / H1 / H0. Evidence: `docs/decisions/MOLNAR_LC015_H_CONVERGENCE_SCIENTIFIC_DECISION.md`.
- [x] Supervisor Decision **1A** recorded: H2-PUB fine RF–U validation; H1 production/report; H0 development/testing. Evidence: `docs/decisions/MOLNAR_GATE_A3_SUPERVISOR_DECISION_1A_2B.md`; `docs/decisions/MESH_USE_POLICY.md`.
- [x] Supervisor Decision **2B** recorded: contour/crack-path deferred; does not block Stage C preparation. Evidence: `docs/decisions/MOLNAR_GATE_A3_SUPERVISOR_DECISION_1A_2B.md`.
- [x] Freeze H0/H1/H2-PUB results, jobs, and source hashes. Evidence: `docs/decisions/MOLNAR_MESH_ROLE_AND_RESULT_FREEZE.md`.
- [!] Perform length-scale study. Not authorized by the current supervisor decision.
- [!] Perform load-increment study. Not authorized by the current supervisor decision.
- [x] Establish justified uniform fine RF–U reference (**H2-PUB**) and production mesh (**H1**). Contour/crack-path deferred (2B). Evidence: `docs/decisions/MOLNAR_GATE_A3_STATUS_MATRIX.md`.
- [~] Gate A3 RF–U use conditionally accepted (1A+2B). Residual historical Stage A items may remain open. Evidence: `docs/decisions/MOLNAR_GATE_A3_SUPERVISOR_DECISION_1A_2B.md`.

## WP3 - MISESERI Pre-Analysis And Remeshing Reproduction

- [x] Stage C preparation authorized after Decisions 1A+2B. Evidence: `docs/studies/STAGE_C_MISESERI_PREPARATION_PLAN.md`.
- [x] Five-job MISESERI campaign plan prepared (no submission). Evidence: `docs/studies/STAGE_C_FIVE_JOB_CAMPAIGN_PLAN.md`.
- [x] Unified H0/H1 preprocessing config created. Evidence: `configs/preprocessing/molnar_h0_h1_unified.yaml`.
- [x] Full automated H0/H1 preprocessing pipeline (geometry/mesh → U1 → U2 → CPS4 → sets/BC → outputs). Evidence: `scripts/preprocessing/build_molnar_unified_deck.py`; `models/generated/molnar_gravouil_2017/unified_preprocessing/H0_fullgen/`; `H1_fullgen/`.
- [x] Generated H0 scientifically equivalent to frozen H0 (nodes, connectivity, layers, sets, props, loading). Evidence: `H0_fullgen/FROZEN_H0_EQUIVALENCE.json`.
- [x] Gate P1 full generation pass (H0 twice, byte-identical deck/fortran/mesh). Evidence: `models/generated/molnar_gravouil_2017/unified_preprocessing/gate_p1_full/GATE_P1_FULL_REPORT.json`.
- [x] H1 full generation + H0/H1 family compare pass. Evidence: `H0_H1_FAMILY_COMPARE.json`; static validation under `results/validation/unified_preprocessing/`.
- [x] Automatic layered deck validators (duplicates, offsets, N_ELEM, sets, outputs, h/lc). Evidence: `scripts/validation/validate_molnar_unified_deck.py`.
- [x] Initial remeshing parameters frozen as proposal (load mode undecided). Evidence: `docs/decisions/MISESERI_REMESHING_PARAMETER_PROPOSAL.md`; `configs/remeshing/miseseri_h0_to_h1_initial.json`.
- [x] Five PBS scripts + static validation prepared (no qsub). Evidence: `scripts/hpc/molnar_h0_miseseri_*.pbs`; `results/validation/stage_c_five_job/STATIC_PBS_VALIDATION.json`.
- [!] HPC submission blocked until: pre-analysis load mode decided, Job 3 CAE remesh implemented, explicit authorization. Evidence: `runs/hpc/stage_c_miseseri/CAMPAIGN_PREPARATION_STATUS.md`.
- [~] Secondary literature / analytical matrices expanded (parallel). Evidence: `references/derived/secondary_validation/`.
- [ ] Reproduce Pandey-Kumar MISESERI extraction (Job 1–2 when authorized).
- [ ] Validate physical-element to visualization-element mapping.
- [ ] Generate locally refined mesh (Job 3 when authorized).
- [ ] Regenerate valid UEL/UMAT layered deck.
- [ ] Run refined elastic dry test (Job 4 when authorized).
- [ ] Validate local target `h/l`.
- [ ] Run refined phase-field candidate vs uniform H1 (Job 5 when authorized).

## WP4 - Refined Phase-Field Benchmark And Efficiency Comparison

- [ ] Run refined phase-field candidate.
- [ ] Compare against uniform fine reference.
- [ ] Calculate peak-force error.
- [ ] Calculate complete-curve error.
- [ ] Calculate crack-path error.
- [ ] Calculate fracture-energy-related metrics using valid integrated data.
- [ ] Compare element count, runtime, CPU time, memory, increments and iterations.
- [ ] Produce accuracy-cost comparison.
- [ ] Complete refinement-parameter sensitivity study.

## WP5 - Evolving Remesh And State Transfer

- [x] Inventory initial transferable state variables. Evidence: `docs/studies/STAGE_D_STATE_TRANSFER_VARIABLE_MAP.md`.
- [x] Design controlled field-transfer test. Evidence: `docs/studies/STAGE_D_ANALYTICAL_TRANSFER_PROTOCOL.md`.
- [x] Transfer known analytical fields between tiny nonmatching meshes. Evidence: `scripts/state_transfer/analytical_transfer_harness.py`; `results/validation/stage_d_analytical_transfer/D1_ANALYTICAL_TRANSFER_REPORT.md`.
- [x] Calculate L2 and maximum transfer errors. Evidence: `results/validation/stage_d_analytical_transfer/D1_ANALYTICAL_TRANSFER_RESULTS.json`.
- [x] Check field bounds. Evidence: `results/validation/stage_d_analytical_transfer/D1_ANALYTICAL_TRANSFER_REPORT.md`.
- [x] Check history and phase-field irreversibility. Evidence: `results/validation/stage_d_analytical_transfer/D1_ANALYTICAL_TRANSFER_REPORT.md`.
- [x] Measure energy jumps. Evidence: `results/validation/stage_d_analytical_transfer/D1_ANALYTICAL_TRANSFER_REPORT.md`.
- [x] Preserve D1 transfer-error baseline without claiming negligible error. Evidence: `docs/studies/STAGE_D2_MINIMAL_ABAQUS_TRANSFER_PLAN.md`.
- [x] Prepare tiny nonmatching D2 source/target transfer package. Evidence: `models/state_transfer/d2_tiny_transfer/`; `scripts/state_transfer/build_d2_tiny_transfer_package.py`.
- [x] Corrected T5 automation smoke rerun completed. Job: `1376758.mmaster02`; classification: `automation_smoke_pass`; evidence: `runs/hpc/stage_c2/automation_smoke/h0_notch045/`, `runs/hpc/stage_c2/automation_smoke/T5_CORRECTED_RESULTS_SUMMARY.md`.
- [x] Run D2A serial Abaqus/UEL state-ingestion verification. Job: `1376785.mmaster02`; classification: `stage_d2a_state_ingestion_pass`; evidence: `runs/hpc/stage_d2/d2a_serial_ingestion/`.
- [x] D2B serial continuation passed after one bounded step-control correction. Failed attempt: `1376819.mmaster02`, `stage_d2b_solver_fail_increment_limit`, evidence `runs/hpc/stage_d2/d2b_serial_continuation/`. Accepted rerun: `1376825.mmaster02`, `stage_d2b_serial_continuation_pass`, evidence `runs/hpc/stage_d2/d2b_serial_continuation_rerun/`, canonical marker `runs/hpc/stage_d2/d2b_serial_continuation/D2B.ok`.
- [x] Run D2C four-thread repeatability comparison. Job: `1376831.mmaster02`; classification: `stage_d2c_thread_repeatability_pass`; evidence `runs/hpc/stage_d2/d2c_threads4_repeatability/`; confirmed `1 MPI RANK x 4 THREAD` and zero state/mechanical/energy differences versus accepted D2B serial reference.
- [!] D2D ABAQUSER output-route verification is blocked externally. D2D0 audit classification: `stage_d2d_blocked_abaquser_not_found`; evidence `runs/hpc/stage_d2/d2d_abaquser_verification/`; no ABAQUSER executable/module/source/interface found, and no D2D PBS job submitted.
- [x] Prepare D3 interrupted-transfer design only. Evidence: `docs/studies/STAGE_D3_INTERRUPTED_TRANSFER_PLAN.md`, `configs/state_transfer/d3_interrupted_transfer.yaml`, `scripts/state_transfer/extract_d3_checkpoint.py`, `scripts/state_transfer/build_d3_target_transfer.py`, `scripts/validation/validate_d3_transfer_package.py`.
- [x] D3A existing-H0 checkpoint accepted after independent energy reconstruction. D3A0/D3A1 extracted the `U2=0.003000000026077032 mm` checkpoint from source job `1376154.mmaster02`; missing `ALLIE`/`ALLSE`/`ALLWK` global history required the D3A-E route. Evidence: `runs/hpc/stage_d3/interrupted_transfer/source_audit/`, `runs/hpc/stage_d3/interrupted_transfer/checkpoint/`, and `runs/hpc/stage_d3/interrupted_transfer/checkpoint/D3A.ok`.
- [x] D3A-E R1 scope-aware reconstruction passed. Failed predecessor R0 job `1376885.mmaster02` remains classified as `stage_d3a_energy_reconstruction_fail_parser_scope` under `runs/hpc/stage_d3/interrupted_transfer/checkpoint_energy/`. Corrected R1 evidence is under `runs/hpc/stage_d3/interrupted_transfer/checkpoint_energy_r1/` with classification `stage_d3a_energy_reconstruction_pass`, 3930 physical elements, 15720 integration points, non-positive detJ count `0`, minimum detJ `2.829135024804933e-06`, and relative energy residual `0.012586306767288707`.
- [x] Build and validate D3A2 nonmatching target transfer package locally. Classification: `stage_d3a2_transfer_package_pass`; evidence `runs/hpc/stage_d3/interrupted_transfer/package/`; target nodes `6601`, physical elements `6400`, target IPs `25600`, split-notch topology pass with 40 duplicated open-face node pairs, shared tip, notch length `0.5`, zero crossing elements, node/IP coverage `1.0`, non-positive detJ count `0`, predicted energy relative jump `0.015379624558651227`, unmapped state count `0`, and `solver_job_submitted=false`.
- [!] D3A3 first serial full-target ingestion/equilibration/release-hold job failed pre-solver. Job `1377382.mmaster02` was submitted exactly once from commit `d6e2474fcae3d05a4171e23c1c2cc757894a8a43` after static preflight pass; PBS `Exit_status=1` because Abaqus user-subroutine compilation could not find `ifort` after the batch script loaded only `abaqus/2023`. Classification: `stage_d3a3_solver_fail_compiler_environment`; evidence `runs/hpc/stage_d3/interrupted_transfer/target_ingestion/`; no `D3A3.ok`.
- [!] D3A3-R1 compiler-environment correction ran as job `1377383.mmaster02` without changing physics, mesh, transfer values, input deck, Fortran logic, step definitions, or checkpoint displacement. The environment correction passed (`gcc/11.4.0`, `intel/2024.2.0`, `abaqus/2023`, `ifort` recorded), but Abaqus user-subroutine compilation failed before solver analysis because `d3_transfer_table.inc` exceeded the Intel Fortran statement token limit. Classification: `stage_d3a3_solver_fail_transfer_table_compile`; evidence `runs/hpc/stage_d3/interrupted_transfer/target_ingestion_r1/`; no `D3A3_R1.ok` or `D3A3.ok`.
- [!] D3A3-R2 compile/datacheck job `1377389.mmaster02` ran exactly once from commit `aace8f89b5a937a40a2be773d4e76a8da329769c`. R2 replaced the compile-time Fortran DATA include with a headerless runtime `d3_transfer_h.dat` loaded once through `UEXTERNALDB`, while preserving the physical Molnar H0 UEL/UMAT source as the base. The runtime file validated in scratch with 25600 H records, min H `1.0045788889553414e-08`, max H `0.027317036782803523`, SHA256 `4689ea5c10c0972e69ba46f8676a326c8b011b98faa8031c7c26cfb218607cd9`; static validation passed. Abaqus compiled and linked the user subroutine, completed input processing, then failed during Standard datacheck because `UEXTERNALDB` opened relative file `d3_transfer_h.dat` from Abaqus internal `/local/...` workdir where the file was not staged. Classification: `stage_d3a3_r2_datacheck_fail_runtime_h_file_not_in_abaqus_workdir`; evidence `runs/hpc/stage_d3/interrupted_transfer/target_ingestion_compile_r2/`; no `D3A3_R2_COMPILE.ok`, no full D3A3-R2, and D3D/D3E remain blocked.
- [!] D3A3-R2-R1 pathfix compile/datacheck job `1377391.mmaster02` ran exactly once from commit `9136924d367156ac76a4c1a116f28e857f290b3c`. The GETOUTDIR correction resolved and opened the staged runtime H file under `/scratch9/.../d3_transfer_h.dat`, removing the prior `/local/...` missing-file failure. Abaqus compiled and linked the user subroutine, completed input processing, then failed during Standard datacheck with Intel Fortran severe `(24)`, end-of-file during read on unit 99. Classification: `stage_d3a3_r2_r1_datacheck_fail_runtime_h_eof_after_getoutdir_open`; evidence `runs/hpc/stage_d3/interrupted_transfer/target_ingestion_compile_r2_r1/`; no `D3A3_R2_COMPILE.ok`, no full D3A3-R2, and D3D/D3E remain blocked.
- [!] D3A3-R2-R2 counted-read correction was prepared as a compile/datacheck gate only. The generated `UEXTERNALDB` keeps `GETOUTDIR` but replaces the EOF-driven `GOTO 100` loader with an exact `DO IREC=1,N_ELEM*NIP` loop, explicit premature-EOF/read-error branches, post-read `COUNT=25600` and `SEEN` checks, and `D3A3-R2 H LOAD COMPLETE`. Static audit `stage_d3a3_r2_r2_counted_read_audit_pass` records no physics, mesh, input deck, runtime-H, material, weak-form, layer-offset, step, or checkpoint-U2 change. Login-node `ifort -extend-source` counted-reader smoke passed with 25600 records, first key `(1,1)`, last key `(6400,4)`, premature EOF false, read error false, duplicates 0, and missing keys 0. Evidence is under `runs/hpc/stage_d3/interrupted_transfer/target_ingestion_compile_r2_r2/`.
- [!] D3A3-R2-R2 datacheck job `1377393.mmaster02` ran exactly once from commit `9058534a9daa188d2d958f8462b230ec843c545e`. Abaqus compiled and linked the user subroutine, completed input processing and Standard datacheck, and printed `D3A3-R2 H LOAD COMPLETE 25600`; premature EOF and runtime-H read-error tokens are absent. The PBS wrapper still exited `10` because the long GETOUTDIR path was wrapped across two `.msg` lines, so the exact full-path grep did not confirm the staged scratch file. Classification: `stage_d3a3_r2_r2_datacheck_fail_pbs_path_gate_linewrap_false_negative`; this wrapper false negative is preserved as failed PBS evidence and resolved only by the subsequent no-PBS replay.
- [x] D3A3-R2-R3 deterministic postcheck replay closed the compile/datacheck gate without another PBS job. Login-node Python replay reconstructed the wrapped runtime-H path as `/scratch9/pr21vyci/adaptive-remeshing/runs/d3a3_r2_datacheck_r2_1377393.mmaster02/d3_transfer_h.dat`, preserved PBS `Exit_status=10`, verified Abaqus compile/link/input/Standard datacheck completion, verified `D3A3-R2 H LOAD COMPLETE 25600`, verified premature EOF/read-error absence, verified runtime-H records `25600`, duplicates `0`, missing records `0`, and unchanged SHA256 `4689ea5c10c0972e69ba46f8676a326c8b011b98faa8031c7c26cfb218607cd9`. Classification: `stage_d3a3_r2_compile_datacheck_pass_postcheck_replay`; evidence `runs/hpc/stage_d3/interrupted_transfer/target_ingestion_compile_r2_r2_replay/`; `D3A3_R2_COMPILE.ok` exists there. No full D3A3-R2 solver job has been submitted yet, and D3D/D3E remain blocked until full D3A3-R2 creates `D3A3.ok`.
- [!] D3A3-R2 full ingestion/equilibration/release-hold submission lane is prepared but not submitted. New files `scripts/hpc/stage_d3/07_d3a3_r2_full_ingestion_hold.pbs` and `scripts/hpc/stage_d3/submit_d3a3_r2_full_ingestion_hold.sh` require the committed replay `D3A3_R2_COMPILE.ok`, copy runtime `d3_transfer_h.dat`, forbid `d3_transfer_table.inc`, run serial CPU1/16GB/02:00 with `OMP_NUM_THREADS=1` and `mp_mode=threads`, preserve Abaqus outputs, run Abaqus-Python extraction, run strengthened validation, and create `D3A3.ok` only after scientific gates pass. The full-run deck now requests global nodal `U, RF` output so the extractor can reconstruct target Q4 bulk-plus-AT2 fracture energy from selected D3A3 frames. Full D3A3-R2 has not been submitted yet; D3D/D3E remain blocked.
- [!] D3A3-R2 full job `1377396.mmaster02` ran exactly once from commit `7a860f50fe557cd88cd3299dd47b1f260071f3fa`. Abaqus compiled, linked, completed input processing, completed Standard analysis, and produced extraction outputs, but strengthened validation failed with PBS `Exit_status=21`. Failures include transfer max errors (`SDV15=0.018013543321948218`, `SDV16=0.01645326664671945`), checkpoint `U2=0.0014999968154910865` instead of `0.003000000026077032`, RF release jump `1.0292182958543674`, d-healing violations `4651`, maximum phase adjustment `0.013784315224591115`, and missing phase-node values for reconstructed energy. Classification: `stage_d3a3_r2_full_validation_fail`; evidence `runs/hpc/stage_d3/interrupted_transfer/target_ingestion_r2/`; no `D3A3.ok`; D3D/D3E remain blocked.
- [x] Test fracture-relevant state transfer for the bounded pre-peak compatibility/release-hold scope. Completed by D3A3-R4 full hold `1377471.mmaster02` with committed canonical `D3A3.ok` under `runs/hpc/stage_d3/interrupted_transfer/target_ingestion_r4_compatible/` (`stage_d3a3_r4_compatible_release_pass`; gate `stage_d3a3_state_transfer_gate_closed`). Closure: `docs/decisions/STAGE_D3_STATE_TRANSFER_CLOSURE.md`; `runs/hpc/stage_d3/interrupted_transfer/D3A3_ACCEPTED_CLOSURE.json`.
- [ ] Test serial repeatability.
- [~] Stage P0 documentation/version review completed. Current documentation permits parallel user subroutines but requires thread-safe shared-resource handling; exact Abaqus 2022 utility interfaces remain installation/compile-gate verification items. Evidence: `docs/studies/ABAQUS_EXTERNALDB_PARALLELIZATION_REVIEW.md`.
- [x] Stage P1 static parallel-safety audit completed. Classification `stage_p_static_audit_risk_identified`; 365 matched records in 12 files; existing COMMON/SAVE/DATA shared state and file paths are not generally qualified for threads or MPI. Evidence: `docs/studies/PARALLEL_SHARED_STATE_MAP.md`; `results/validation/stage_p_static_audit/`.
- [~] Stage P2 minimal instrumented package prepared, not compiled or executed. The isolated D2-derived model has eight physical elements and bounded rank/thread/routine/call diagnostics. Evidence: `models/parallelization/minimal_externaldb_commonblock_test/`.
- [x] Stage P0--P2 preparation selectively frozen and pushed as commit `9369dfcb05d63cdbdec0b0e910423c9a6cc7bd1c`; unrelated working-tree changes were not staged.
- [~] P3-S serial diagnostic lane prepared and statically validated, not submitted. The bounded lane requires one rank/thread/CPU, produces the declared callback/shared-state/state/RF/energy evidence, and creates `P3S_COMPLETION.ok` only after all serial gates pass. Submission wrapper requires a separate one-shot authorization file and asserts P3-T4 remains unauthorized. Evidence: `scripts/hpc/stage_p/`; `scripts/validation/validate_p3s_serial_diagnostic.py`; classification `stage_p3s_lane_prepared_static_pass`.
- [!] First synchronized P3-S cluster preflight stopped before execution because the default login-node Python rejected future annotations. No PBS/Abaqus job launched. The lane now explicitly binds qualified Python 3.11.7 in the submit and compute workflows; repeat preflight pending. Evidence: M-077 in `docs/project/MISTAKES_AND_FIXES_LOG.md`.
- [!] Qualified-Python repeat preflight passed shell syntax, Python compilation, and the Stage P static gate, but exposed cross-platform CSV line-ending churn in the tracked audit output. No job launched. Platform-native line endings are now enforced; clean synchronized replay pending. Evidence: M-078 in `docs/project/MISTAKES_AND_FIXES_LOG.md`.
- [!] A further replay found that the frozen 365-record P1 audit includes relevant local untracked variants absent from the cluster checkout. P3 preflight must not silently rewrite that evidence; audit refresh is now explicit via `--refresh-audit`. Clean no-refresh synchronized replay pending. Evidence: M-079.
- [x] Final synchronized P3-S preparation preflight passed at commit `7e069915c0f940a2c4e50ae71356909efd9665ab`: Python 3.11.7 bound, both shell scripts passed `bash -n`, all Python files compiled, static classification `stage_p3s_lane_prepared_static_pass`, audit refresh false, and tracked Stage P diff empty. No P3 scheduler job exists or was submitted. Evidence: `.agent.md`.
- [~] P3-S failure-safe hardening prepared: explicit false authorization record, login-side immutable staging/hashes, no compute-node Git, notification integration, exit finalizer, lightweight allowlist, increment-sequence evidence, expanded technical gates, and synthetic failure tests. Execution remains unauthorized until this hardening is committed, synchronized, and reviewed.
- [x] Historical checklist-validator consistency findings were reconciled in
  WP7-F1 without changing Stage-P evidence or scientific classifications.
  Evidence: `docs/decisions/WP7_FINAL_CLOSEOUT_RECONCILIATION.md`;
  `scripts/validation/check_project_phase_checklist.py`.
- [x] Fail-closed P3-S preparation committed, pushed, and synchronized as `82652680978d39c60125d75b4b9a1d7532c28e77`. Cluster `bash -n`, Python compilation, 12 synthetic tests, and `stage_p3s_lane_prepared_static_pass` passed; the real wrapper stopped with exit `20` because submission authorization is false. Tracked Stage P diff and P3-S/P3-T4 queue search were empty. No Abaqus/PBS job was submitted. Evidence: `.agent.md`; `runs/hpc/stage_p/README.md`.
- [~] P3-S-H1 queue/consumption policy correction prepared: both queue defaults use `entry_imfdfkmq`; valid post-qsub job IDs atomically consume the one-shot record, while failed/invalid qsub results leave it unused. Fifteen unittest cases pass. Local pytest is unavailable (M-080); synchronized cluster pytest remains a pre-authorization check.
- [x] P3-S-H1 policy commit `bd21c45dfd7ec06a038197db159697749dfd0768` synchronized and fully validated: cluster pytest 15/15 passed from a scratch-only install, shell/Python/static/queue/diff checks passed, and no scientific or resource setting changed.
- [x] The sole authorized P3-S serial diagnostic was submitted as `1378028.mmaster02` from revision `a1965a655d193db8d04ad36afa022bbe1c16e0e1`. The wrapper consumed authorization at `1/1`; Abaqus 2023 launched and compiled/linked the instrumented Fortran, then Abaqus/Standard terminated by signal 11 in the element loop. `P3S_ok=false`; no retry is authorized.
- [x] P3-F offline failure forensics completed without Abaqus/PBS execution. The exception stack localizes the immediate failure to `dmpc_getrank` called by `UEXTERNALDB(LOP=0)` before `P2_INIT`, UEL, UMAT, shared-state monitoring, or an element/IP was observed. Classification: `stage_p3s_signal11_cause_localized`. Evidence: `results/validation/stage_p/p3s_signal11_forensics/`.
- [x] P3-SB uninstrumented eight-element baseline prepared but not authorized: its source is byte-identical to accepted D2, its deck is byte-identical to P3-S, and it contains no rank/thread, mutex, or shared-access diagnostics. P3-SM remains a minimal callback design only. Evidence: `docs/decisions/STAGE_P3F_SIGNAL11_ISOLATION_DECISION.md`.
- [x] Guarded P3-SB execution lane prepared with authorization false: queue `entry_imfdfkmq`, CPU/rank/thread `1/1/1`, 16 GB, 00:30:00, Abaqus 2023, Intel 2024.2, immutable login-side hashes, no compute-node repository dependency, failure-safe evidence, CPS4-derived four-IP coverage, monotonic phase/history and transfer gates, and pass-only completion. No Abaqus/PBS job was submitted. Evidence: `runs/hpc/stage_p/p3sb_baseline_serial/`.
- [x] Exactly one P3-SB serial baseline was authorized through the guarded wrapper and consumed `1/1`; no automatic retry, and P3-SM plus all downstream authorities remain false. Evidence: `runs/hpc/stage_p/p3sb_baseline_serial/P3SB_AUTHORIZATION.json`.
- [!] P3-SB job `1378094.mmaster02` consumed authorization `1/1` and closed as `stage_p3sb_baseline_serial_fail_validation` with scheduler exit `12`. Solver exit was `0`; compile/link/input/Standard completed; ODB extraction produced all 32 expected CPS4/IP records, finite RF/energy, and zero phase/history/transfer violations. Validation ran before the finalizer copied stdout/`.sta`, so the technical gates and increment sequence failed and no completion marker exists. No retry is authorized.
- [x] P3-SB-A finalized-evidence audit passed offline in an isolated replay using the unchanged validator: classification `stage_p3sb_finalized_evidence_offline_pass`, all frozen gates true, 32/32 state records, zero violations/mismatches, and 13 increment records. Original status/hash/classification and completion-marker absence remain unchanged; no job was rerun. Evidence: `runs/hpc/stage_p/p3sb_baseline_serial/`.
- [x] P3-SM0 job `1378099.mmaster02` passed from authorization commit `572c51eacbf7af79f1ab2ffda93a0ad466fc6eca`: PBS/solver exit `0`, all compile/link/input/Standard/ODB gates true, four callback markers observed, no signal 11, 32/32 state rows, 11 RF rows, 11 energy rows, 13 increment records, and zero phase/history/transfer violations. Authorization is consumed `1/1`; no retry occurred or is authorized.
- [x] P3-SM1 review boundary prepared in `docs/decisions/STAGE_P3SM1_REVIEW_PREPARATION.md`; no P3-SM1 source, lane, or execution is authorized. P3-T4, MPI, hybrid, P4, H1, D3D-A1 reopening and D3E remain blocked.
- [!] P3-T4 and all downstream thread/MPI/hybrid/production routes remain blocked after the P3-S diagnostic failure.
- [x] Stage P parallelization thesis subsection added and included in the closeout build. Bundled Tectonic rebuilt the 28-page closeout PDF successfully; existing appendix layout warnings remain nonfatal. Evidence: `docs/thesis/EXTERNALDB_COMMONBLOCK_PARALLELIZATION_STUDY.tex`; `results/latex_build_stage_p/THESIS_CLOSEOUT_BUILD.pdf`.
- [!] Stage P3 execution blocked pending committed review and explicit authorization. No P3-S submission, P3-T4, P3-M2, P3-H22, production H1, D3D-A1 reopening, or D3E job is authorized. Evidence: `docs/decisions/STAGE_P_PARALLELIZATION_SCOPE.md`; `runs/hpc/stage_p/README.md`.
- [!] No online/evolving-remeshing claim until these checks pass. Evidence: `THESIS_PLAN.md`.
- [!] D3D/D3E blocker: explicit fracture-continuation authorization — not missing `D3A3.ok`.

## WP6 - IMFD/ABAQUSER

- [ ] Define required interface fields.
- [ ] Map variable names, components and units.
- [ ] Verify integration-point ordering.
- [ ] Compare ABAQUSER output with independent extraction.
- [ ] Document visualization procedure.

## WP7 - Final Recommendations And Thesis Writing

- [x] Freeze the Stage-A baseline report as
  `frozen_with_residual_scientific_limitations`. Evidence:
  `docs/reports/STAGE_A_BASELINE_REPORT.tex`.
- [x] Freeze the Stage-A execution/failure log without removing predecessor
  failures. Evidence: `docs/reports/STAGE_A_EXECUTION_AND_FAILURE_LOG.tex`.
- [x] Reconcile and freeze this project checklist for WP7 closeout. Evidence:
  `docs/decisions/WP7_FINAL_CLOSEOUT_RECONCILIATION.md`.
- [x] Prepared thesis-ready Stage A benchmark chapter draft from committed evidence only. Evidence: `docs/thesis/STAGE_A_MOLNAR_BENCHMARK_CHAPTER.tex`.
- [x] Prepared Stage A reproducibility appendix draft with revisions, hashes, job records, trace provenance, and excluded-file policy. Evidence: `docs/thesis/STAGE_A_REPRODUCIBILITY_APPENDIX.tex`.
- [x] Prepared Stage A figure/table plan from existing evidence paths only. Evidence: `docs/thesis/STAGE_A_FIGURE_TABLE_PLAN.md`.
- [x] Prepared route-neutral post-supervisor execution plan. Evidence: `docs/decisions/POST_SUPERVISOR_DECISION_EXECUTION_ROUTES.md`.
- [~] Reviewed LaTeX build-product ignore coverage and added recurring build-artifact patterns. Evidence: `.gitignore`. Limitation: existing untracked generated files were not deleted.
- [x] Prepared Stage B uniform-reference protocol without simulations, deck generation, PBS preparation, or submission. Evidence: `docs/studies/STAGE_B_UNIFORM_REFERENCE_PROTOCOL.md`; `docs/studies/STAGE_B_ACCEPTANCE_METRICS.md`; `docs/studies/STAGE_B_HPC_RESOURCE_ESTIMATE.md`; `configs/studies/molnar_uniform_reference_matrix.yaml`.
- [x] Supervisor approved only the Molnar `lc=0.015 mm` h-convergence subset for execution (H0 exact supplementary, H1 `h=0.0025 mm`, H2-PUB `h=0.001 mm`). Length-scale, increment-sensitivity, MISESERI, remeshing, multi-CPU, and GPU work remain unauthorized. Evidence: `docs/studies/STAGE_B_UNIFORM_REFERENCE_PROTOCOL.md`; `configs/studies/molnar_uniform_reference_matrix.yaml`.
- [x] Freeze Stage A reports after conditional scientific closure. Evidence:
  `docs/reports/STAGE_A_BASELINE_REPORT.tex`;
  `docs/reports/STAGE_A_EXECUTION_AND_FAILURE_LOG.tex`.
- [x] Create and freeze the Stage-B results report. Evidence:
  `docs/reports/STAGE_B_RESULTS_REPORT.tex`.
- [x] Create and freeze the Stage-B execution/failure log. Evidence:
  `docs/reports/STAGE_B_EXECUTION_AND_FAILURE_LOG.tex`.
- [x] Complete final accuracy-cost conclusions. Evidence:
  `docs/thesis/FINAL_RECOMMENDATIONS_AND_DECISION_TREE.tex`;
  `docs/reports/STAGE_B_RESULTS_REPORT.tex`.
- [x] Complete implementation-limitations chapter. Evidence:
  `docs/thesis/STAGE_D_STATE_TRANSFER_SYNTHESIS.tex`;
  `docs/thesis/EXTERNALDB_COMMONBLOCK_PARALLELIZATION_STUDY.tex`;
  `docs/thesis/FINAL_CLAIM_MATRIX.md`.
- [x] Complete recommendations. Evidence:
  `docs/thesis/FINAL_RECOMMENDATIONS_AND_DECISION_TREE.tex`.
- [x] Archive final reproducibility package. Evidence:
  `docs/reports/FINAL_REPRODUCIBILITY_AUDIT.md`;
  `results/final/FINAL_EVIDENCE_MANIFEST.json`.
- [x] Stage E0 dashboard reconciled: WP5 scoped completion with limitation,
  WP6 externally blocked, and WP7 identified as the final documentation stage.
  Evidence: `docs/project/PROJECT_PHASE_CHECKLIST.md`.
- [x] Stage E1 integrated Stage D synthesis and compact claim table completed. Evidence: `docs/thesis/STAGE_D_STATE_TRANSFER_SYNTHESIS.tex`.
- [x] Stage E2 final Stage D figures, tables, frozen metrics, and provenance generated from committed CSV/JSON evidence only. Evidence: `results/final/stage_d/`; `scripts/postprocessing/generate_stage_d_final_synthesis.py`.
- [x] Stage E3 tolerance policy prepared for supervisor review, WP6 ABAQUSER external block closed, and final claim matrix frozen. Evidence: `docs/decisions/FINAL_THESIS_TOLERANCE_POLICY.md`; `docs/decisions/WP6_ABAQUSER_EXTERNAL_BLOCK_CLOSURE.md`; `docs/thesis/FINAL_CLAIM_MATRIX.md`.
- [x] Stage E4 final recommendations and practical decision tree completed. Evidence: `docs/thesis/FINAL_RECOMMENDATIONS_AND_DECISION_TREE.tex`.
- [x] Stage E5 local reproducibility audit passed: figure/table provenance complete, no ODB tracked, no permanent scratch dependency, job IDs/SHAs and withheld claims recorded. The assembled 28-page closeout build passed with bundled Tectonic after correction of one pre-existing math-mode error. Evidence: `docs/reports/FINAL_REPRODUCIBILITY_AUDIT.md`; `results/final/FINAL_EVIDENCE_MANIFEST.json`; `docs/reports/THESIS_LATEX_BUILD_RECORD.md`.
- [x] WP7-F1 final reconciliation completed. Evidence:
  `docs/decisions/WP7_FINAL_CLOSEOUT_RECONCILIATION.md`;
  `results/final/WP7_DOCUMENTATION_GATES.json`;
  `docs/reports/THESIS_LATEX_BUILD_RECORD.md`. Classification:
  `wp7_final_closeout_reconciliation_complete`: Stage-A reports frozen with
  residual limitations, Stage-B report pair created and frozen, checklist
  validator passed, repository unit tests passed 100/100, five standalone
  validation test scripts passed, and the 30-page final build plus both
  three-page Stage-B reports compiled successfully.
- [x] WP7-F2 thesis submission-package review completed. Evidence:
  `docs/decisions/WP7_THESIS_SUBMISSION_PACKAGE_REVIEW.md`;
  `docs/reports/THESIS_SUBMISSION_CHECKLIST.md`;
  `results/final/THESIS_SUBMISSION_PACKAGE_MANIFEST.json`;
  `results/final/THESIS_SUBMISSION_PDF_RECORD.txt`;
  `results/final/THESIS_SUBMISSION_BUILD_WARNINGS.txt`. Classification:
  `wp7_thesis_submission_package_review_complete`: 30-page closeout PDF rebuilt
  and checksummed as a local artifact; claim boundaries preserved; automated
  gates passed; `ready_for_submission` remains false pending faculty-template
  integration, administrative forms, and final human PDF inspection. Next:
  WP7-F3 faculty-template integration.
- [~] WP7-F3 faculty-template integration candidate prepared. Evidence:
  `docs/thesis/THESIS_FACULTY_BUILD.tex`;
  `docs/decisions/WP7_FACULTY_TEMPLATE_INTEGRATION.md`;
  `results/final/THESIS_FACULTY_PACKAGE_MANIFEST.json`;
  `results/final/THESIS_FACULTY_PDF_RECORD.txt`. Classification:
  `wp7_faculty_template_integration_candidate`: official assignment-sheet
  front matter, abstract, bibliography, five embedded figures, main-prose path
  cleanup, and a new 39-page faculty PDF with distinct SHA-256. Remaining
  false gates: human print-scale review, administrative portal forms, and
  supervisor sign-off. `ready_for_submission` remains false.

## Multi-agent coordination

- [x] COORD-0 multi-agent coordination ledger initialized. Evidence:
  project_coordination/; classification
  multi_agent_coordination_layer_initialized.
- [x] COORD-1 mandatory bootstrap entrypoints integrated. Evidence:
  AGENTS.md; GEMINI.md; GROK.md; project_coordination/PROTOCOL_VERSION.json;
  scripts/validation/check_multi_agent_bootstrap.py. Classification:
  multi_agent_bootstrap_entrypoints_integrated. Next: F1-P0 (no submission).

## Stage F - Mode-II Mixed-Mode Benchmark

- [x] F0.1 Mode-II benchmark definition frozen (Molnar pure shear, alpha=0).
  Evidence: `configs/studies/mode_ii_molnar_shear.yaml`;
  `docs/studies/STAGE_F_MODE_II_BENCHMARK_PROTOCOL.md`;
  `models/generated/mode_ii/h0_serial/BENCHMARK_DEFINITION.md`.
- [x] F0.2 Mode-II H0 technical package generated from accepted Molnar H0 mesh
  with pure-shear BC only. Evidence: `models/generated/mode_ii/h0_serial/`;
  `scripts/model_generation/build_mode_ii_h0_serial.py`.
- [x] F0.3 Static validators pass offline. Evidence:
  `scripts/validation/validate_mode_ii_h0_static.py`;
  `models/generated/mode_ii/h0_serial/STATIC_VALIDATION.json`.
- [x] F0.4 Fail-closed HPC lane prepared; all execution flags false. Evidence:
  `runs/hpc/stage_f/mode_ii_h0/MODE_II_H0_AUTHORIZATION.json`;
  `scripts/hpc/stage_f/`. Classification: `stage_f_mode_ii_h0_prepared`.
- [x] F1-J0 Mode-II H0 datacheck passed. Evidence: `runs/hpc/stage_f/mode_ii_h0/1378911.mmaster02/`.
- [!] F1-J1-R2 Mode-II H0 serial run completed solver and extraction (job 1378942.mmaster02; Abaqus rc: 0, extractor rc: 0) but failed scientific acceptance gate (validator rc: 20; U1=0.007mm vs expected 0.010mm; empty crack path). Classification: stage_f_mode_ii_h0_second_replacement_fail. Useful as partial pre-peak response evidence only; H0 baseline unvalidated; F2 blocked. Evidence: `docs/experiment_records/STAGE_F1_J1_R2_MODE_II_SERIAL_SECOND_REPLACEMENT.md`; `runs/hpc/stage_f/mode_ii_h0/replacement_r2/evidence/1378942.mmaster02/`.
- [x] F1-C0 Mode-II H0 endpoint loading audit proved exact mathematical root cause of $U_1 = 0.007\text{ mm}$ endpoint; selected Option A correction (Amp-2 endpoint $0.2$). Evidence: `docs/decisions/STAGE_F_MODE_II_H0_ENDPOINT_CORRECTION.md`; `runs/hpc/stage_f/mode_ii_h0_correction/ENDPOINT_AUDIT.json`.
- [x] F1-C1 Mode-II H0 corrected package and fail-closed lane preparation completed offline. All execution flags false; static validation, unit tests, and local smoke passed cleanly. Classification: `stage_f_mode_ii_h0_endpoint_corrected_prepared_unauthorized`. Evidence: `models/generated/mode_ii/h0_endpoint_corrected_serial/`; `runs/hpc/stage_f/mode_ii_h0_endpoint_corrected/`; `docs/experiment_records/STAGE_F1_C1_MODE_II_H0_ENDPOINT_CORRECTED_PREPARATION.md`.
- [x] F1-C2-R1-H0-VALIDATOR-FIX Mode-II H0 corrected baseline formally passed. Job `1379393.mmaster02` completed all 2000 increments cleanly (`abaqus_rc: 0`, `extractor_rc: 0`, $U_1=0.0100\text{ mm}$, $F_{1,\max}=0.3733\text{ kN}$, $\max(d)=0.9909 \ge 0.50$, 0 history-decrease violations); offline result validator schema corrected. Classification: `stage_f_mode_ii_h0_endpoint_corrected_serial_baseline_pass`. Evidence: `docs/experiment_records/STAGE_F1_C2_R1_MODE_II_H0_VALIDATOR_FIX.md`; `runs/hpc/stage_f/mode_ii_h0_endpoint_corrected/replacement_r1/evidence/1379393.mmaster02/`.
- [x] F2-H1-BASELINE-PREP Mode-II H1 uniform reference package and fail-closed HPC lane prepared offline with integrated Telegram completion traps. Classification: `stage_f_mode_ii_h1_uniform_prepared`. Evidence: `models/generated/mode_ii/h1_uniform_serial/`; `scripts/hpc/stage_f/05_mode_ii_h1_endpoint_corrected_serial.pbs`; `docs/experiment_records/STAGE_F2_H1_MODE_II_BASELINE_PREPARATION.md`.
- [x] F2-H1-DATACHECK Mode-II H1 uniform reference datacheck passed cleanly (job `1379431.mmaster02`; Abaqus rc: 0, walltime `00:00:17`, 334.66 MB RAM, zero errors or warnings). Classification: `stage_f_mode_ii_h1_uniform_datacheck_pass`. Evidence: `docs/experiment_records/STAGE_F2_H1_MODE_II_DATACHECK.md`; `runs/hpc/stage_f/mode_ii_h1/evidence/1379431.mmaster02/`.
- [!] F4 Stage F4 two-job batch closed as a pre-Abaqus infrastructure failure. Jobs `1379615.mmaster02` and `1379616.mmaster02` routed from `entry_imfdfkmq` to `normal_imfdfkmq`, ran for one second on `mnode100`, and exited PBS status 10 because the compute-job Git revision guard obtained `HEAD=unknown`. Neither solver started and no ODB, extraction, validation, H2 nonlinear metrics, or corrected MISESERI field metrics exist. No retry or replacement is authorized. Evidence: `runs/hpc/stage_f/stage_f4/evidence/`; `project_coordination/sessions/2026-07-30_0825_codex_F4-STAGE-F4-MONITOR-AND-VALIDATE.md`.
- [~] F4 authorized runtime-bundle replacements closed with mixed results. MISESERI job `1379893.mmaster02` solved and exported under PBS; its original validator failed only from Abaqus-Python syntax, and isolated offline repaired validation passed as `official_corrected_pbs_validation_pass` with 3,930 rows and all required fields. H2 job `1379892.mmaster02` failed compiling its user subroutine because `ifort` was unavailable, so nonlinear H2 validation remains unresolved. Authorization is consumed and no retry is permitted. Evidence: `runs/hpc/stage_f/stage_f4_replacement/evidence/`; `project_coordination/sessions/2026-07-30_0856_codex_F4-COMPUTE-NODE-RUNTIME-BUNDLE-REPAIR-AND-REPLACEMENT.md`.
- [~] F5 offline readiness prepared. The official job `1379893.mmaster02` MISESERI gate is frozen without rewriting original `VAL_RC=1`; repaired offline validation remains separately passed. An unapproved, datacheck-only H2 compiler smoke package (`M2H2CMP1`, 1 CPU, 8 GB, 00:30:00) uses the exact H2 hashes and the evidence-backed `gcc/11.4.0` -> `intel/2024.2.0` -> `abaqus/2023` candidate. Native remeshing is audit-only: the publication-faithful rule is recorded, diagnostic statistics/figures are generated, and no native remesh or refined deck exists yet. H2 nonlinear convergence and the uniform-reference gate remain unresolved; no execution is authorized. Evidence: `docs/experiment_records/STAGE_F4_OFFICIAL_CORRECTED_MISESERI_PREANALYSIS.md`; `docs/methods/HPC_ABAQUS_FORTRAN_ENVIRONMENT.md`; `models/generated/mode_ii/h2_u020_compiler_datacheck_smoke/`; `results/processed/stage_f/`.
- [!] F5 `M2H2CMP1` one-job authorization was received but not activated: mandatory read-only SSH preflight failed authentication before `qstat` or module inspection. No runtime was staged, no qsub was attempted, no job ID exists, and the H2 compiler environment remains unresolved. A later attempt requires restored SSH access and new authorization. Evidence: `runs/hpc/stage_f/h2_u020_compiler_datacheck_smoke/PREFLIGHT_STATUS.json`; `docs/experiment_records/STAGE_F5_H2_COMPILER_DATACHECK_SMOKE.md`.
- [x] F5 SSH transport recovered read-only through the proven `tu_freiberg` alias. It resolves the correct remote user and existing dedicated identity, while the direct hostname lost those alias-specific settings. `qstat` was accessible and empty. Both candidate module orders expose Abaqus 2023, ifort 2021.13.0 and ifx 2024.2.0; the prior successful `gcc -> intel -> abaqus` order remains selected. No compilation, datacheck, solver or qsub occurred, and new authorization is required. Evidence: `runs/hpc/stage_f/h2_u020_compiler_datacheck_smoke/SSH_TRANSPORT_RECOVERY_PREFLIGHT.json`; `docs/methods/HPC_ABAQUS_FORTRAN_ENVIRONMENT.md`.
- [x] F5 H2 compiler/datacheck smoke `1379939.mmaster02` passed from immutable run `F5CMP_20260730_113544_e8a1d32`: PBS/Abaqus return codes 0, exact input hashes matched, ifort 2021.13.0 compiled and linked the UEL/UMAT, and Abaqus 2023 datacheck completed. Authority remains consumed (`1/1`); no retry, replacement or full analysis occurred. The pass is technical only and does not establish H2 fracture response or remeshing validity. Evidence: `runs/hpc/stage_f/h2_u020_compiler_datacheck_smoke/evidence/1379939.mmaster02/`.
- [~] F6 explicitly authorized two-job batch preparation: `M2H2U20F1` will run the exact frozen H2 u020 full serial analysis; independent `M2RMAPI1` will qualify the Abaqus 2023 native MISESERI RemeshingRule API without a solver launch. Status JSON generation is repaired and tested after M-103. Authorization remains inactive until all offline and cluster preflights pass; maximum two qsub attempts with no retry or replacement.
- [x] F6 guarded batch submitted exactly once from immutable run `F6_20260730_122800_2249ec21`: `M2H2U20F1` = `1379966.mmaster02`, `M2RMAPI1` = `1379967.mmaster02`. Counters are 2 qsub attempts, 2 successes, 0 failures, 0 direct manual qsubs, 0 retries/replacements. Both jobs are terminal and all authority is consumed.
- [!] F6 Job A `1379966.mmaster02` completed Abaqus and extraction at `U1=0.020 mm` (peak `RF1=0.138727 kN`, final `RF1=0.080544 kN`, 41.94% drop), but Python 3.11 offline validation failed the declared irreversibility gate: 11 framewise maximum-damage decreases, largest `-1.0073e-4`. PBS exit 12 also preserves the embedded Python 2.7 validator incompatibility. Classification: `stage_f_mode_ii_h2_uniform_serial_validation_fail`; no retry authorized.
- [!] F6 Job B `1379967.mmaster02` closed as `abaqus_cae_start_failure` (PBS exit 10): CAE started/license checkout succeeded, but Python 2.7 rejected Abaqus driver arguments before source hash/API audit. Rule creation was not reached; native remesh count 0, solver count 0, candidate deck count 0. M-104 records a prevention-only environment-variable correction. No retry is authorized.
- [-] F7 prepares exactly two independent non-solver jobs: a read-only fixed-material-point audit of the retained H2 ODB and a corrected CAE-only native RemeshingRule API qualification. No H2 rerun, datacheck, adaptive analysis, refined solve, retry, replacement, or third job is authorized.
- [!] F2–F5 (H1 solver execution, MISESERI, refined compare, transfer) blocked pending explicit human authorization before job submission.




## Gate Checklist

| Gate | Acceptance requirement | Current status | Blocking issue |
|---|---|---|---|
| Environment gate | compiler, linker, Abaqus and callback pass | passed | none |
| One-element technical | unchanged model completes and outputs exist | passed | none |
| One-element scientific | source relations and irreversibility checks | provisional pass | tolerances provisional |
| Supplementary benchmark technical | unchanged deck completes | passed | none |
| Gate A3 RF–U | mesh roles + RF–U reference for validation | conditionally accepted | contours deferred; residual Stage A items open |
| Preprocessing Gate P1 | same config → identical H0 deck | not started | pipeline build |
| MISESERI gate | refined deck valid and local size achieved | preparation authorized | qsub not authorized |
| Refined benchmark gate | accepted error and measured benefit | closed at scoped Stage C result | crack-path equivalence not supported; H1 remains production |
| State-transfer gate | closed at D3A3-R4 for the bounded pre-peak compatibility/release-hold scope | Gate closed by accepted job `1377471.mmaster02` (`stage_d3a3_r4_compatible_release_pass` / `stage_d3a3_state_transfer_gate_closed`); canonical `D3A3.ok` committed under `target_ingestion_r4_compatible/`; package `package_compatible_r2`; active/free 6446/155; closure evidence `docs/decisions/STAGE_D3_STATE_TRANSFER_CLOSURE.md` and `runs/hpc/stage_d3/interrupted_transfer/D3A3_ACCEPTED_CLOSURE.json` | D2D blocked by missing ABAQUSER; D3D/D3E blocked by explicit fracture-continuation authorization — not missing `D3A3.ok` |
| ABAQUSER gate | output agrees with independent extraction | blocked | D2D0 found no ABAQUSER executable/module/source/interface |
| Stage F Mode-II H0 | package prepared; baseline run completed solver but failed scientific gate | scientific validation failed (job 1378942.mmaster02, validator rc: 20) | deck endpoint / validator target mismatch; F2 blocked |



## Checklist Update Rules

- `docs/project/PROJECT_PHASE_CHECKLIST.md` is the authoritative living task and phase checklist.
- Update it after every substantial operation.
- Every completed item must link to evidence or identify its commit/run.
- Failed attempts remain recorded.
- Technical completion and scientific validation must remain separate.
- A phase may be marked complete only after its stated gate passes.
- Blocked downstream tasks must remain visibly blocked.
- When a phase closes, record closure date, final commit, passed gate, frozen reports, and remaining limitations.
- Do not create duplicate phase checklists.
- Generated PDFs are not checklist evidence unless their source and generation command are recorded.

## Active Next Item

Review the frozen thesis submission package. Evidence:
`docs/decisions/WP7_FINAL_CLOSEOUT_RECONCILIATION.md`.

No Abaqus/PBS execution, Stage-P reopening, P3-T4C preparation, downstream
production route, or claim expansion is authorized.

Submission-review priority:

1. consolidate Stage C accuracy/cost findings;
2. consolidate Stage D transfer and active-set findings;
3. finalize limitations and claim boundaries;
4. generate thesis figures and tables from committed evidence;
5. perform the final reproducibility and thesis-build audit.

### Current Stage D Boundary

- [x] D3A3 compatibility-ingestion/release-hold gate closed at R4 (`1377471.mmaster02`; canonical `D3A3.ok`).
- [x] D3D Route-B full-segment authorization consumed exactly once by job `1377558.mmaster02`; Abaqus and postprocessing completed, free residual passed, irreversibility passed, and the active-multiplier gate required an update. Evidence: `docs/decisions/STAGE_D3D_RESULT_CLOSURE.md`; `runs/hpc/stage_d3/fracture_continuation/d3d_active_set_segment/`.
- [x] D3D offline update scope identified: first invalid F4 state `F4_segment_initial`, 30 initial candidates, 3,157-node endpoint union retained only as a maximum envelope, complete phase/H coverage, and no tolerance change. Evidence: `docs/decisions/STAGE_D3D_ACTIVE_SET_UPDATE_SCOPE.md`.
- [x] D3D-A1 offline obstacle update authorized and completed at unchanged checkpoint displacement using recovered F3 phase as the lower bound and actual F3 SDV16 as fixed history. Deterministic convergence took 7 iterations; final active/free counts are 6,374/227, free residual `2.117582368135751e-21`, minimum active multiplier `-9.99696348887624e-09`, active-bound error `0`, phase functional change `-1.6759153614843373e-10`, and no H, phase-decrease, lower-bound, detJ, or state-reset violations. Classification: `stage_d3d_a1_checkpoint_obstacle_update_pass`. Evidence: `runs/hpc/stage_d3/fracture_continuation/d3d_a1_checkpoint_update/`.
- [x] D3D-A1 candidate package prepared with corrected nodal phase, unchanged actual F3 history, original F3 lower bound, and converged KKT membership. Classification: `stage_d3d_a1_candidate_package_prepared`. This is not an accepted restart state because mechanical re-equilibration has not been assessed. Evidence: `runs/hpc/stage_d3/fracture_continuation/package_d3d_a1_checkpoint_r1/`.
- [x] D3D-A1H0 fixed-phase mechanical checkpoint-hold preparation authorized and prepared as an isolated two-step lane. All 6,601 phase nodes remain fixed in ingestion and equilibration; runtime H has 25,600 unchanged F3 records; Fortran is byte-identical to accepted R4. Datacheck and solver submitters are committed with explicit false-authorization guards. Classification: `stage_d3d_a1h0_mechanical_hold_preparation_authorized`. Evidence: `docs/decisions/STAGE_D3D_A1H0_MECHANICAL_HOLD_AUTHORIZATION.md`; `models/state_transfer/d3_interrupted_transfer/executable_d3d_a1_checkpoint_hold_r1/`.
- [x] D3D-A1H0 execution lane hardened before submission: datacheck completion/history/source gates added; full-run evidence uses an ODB-safe allowlist and failure-safe preservation; transfer, KKT, reset, finiteness, coverage, detJ, and spatial-variation gates derive from evidence; synthetic/static tests pass. Exactly one datacheck is authorized (`stage_d3d_a1h0_datacheck_authorized`), with submissions used `0/1` before submission. Full hold remains unauthorized.
- [x] D3D-A1H0 datacheck submitted exactly once through the guarded wrapper as job `1378003.mmaster02` from hardened commit `9ecb9b3e2a3d969b31d0546768f96d32e5deae9c`; initial state `Q`, CPU1, 16 GB, walltime `00:45:00`, serial threads, mail `abe`. Authorization consumed immediately after submission (`1/1`); no retry is authorized.
- [x] D3D-A1H0 datacheck job `1378003.mmaster02` preserved as a pre-Abaqus technical failure (`stage_d3d_a1h0_datacheck_fail`, PBS exit `7`, walltime `00:00:02`). Runtime H passed with 25,600 records and SHA `dae747b3715e928d1346d33b27773d1318dc24071e99851a103a3dcc189238f8`. The guard compared a Windows working-tree Fortran SHA against the canonical Linux checkout; the H0 and accepted-R4 cluster files were byte-identical at SHA `5a84a88c04988ebd69705c81ae5d3d1f56f103e3b52883ea3a394dfcdc691fbf`. No compile, Abaqus input processing, or datacheck occurred; no `.ok` marker exists and no retry is authorized. Evidence: `runs/hpc/stage_d3/fracture_continuation/d3d_a1_checkpoint_hold_datacheck/`.
- [x] One isolated D3D-A1H0 corrected datacheck R1 authorized after committed preparation (`stage_d3d_a1h0_datacheck_r1_authorized`). The predecessor remains consumed at `1/1`; R1 derives candidate/R4 Fortran and runtime-H checksums from the synchronized Linux checkout, writes only to its distinct evidence lane, and permits at most one guarded submission. No scientific input, deck, Fortran content, runtime history, or tolerance change is authorized. Evidence: `docs/decisions/STAGE_D3D_A1H0_DATACHECK_R1_AUTHORIZATION.md`; `runs/hpc/stage_d3/fracture_continuation/d3d_a1_checkpoint_hold_datacheck_r1/D3D_A1H0_R1_AUTHORIZATION.json`.
- [x] D3D-A1H0 corrected datacheck R1 submitted exactly once through the guarded R1 wrapper as job `1378004.mmaster02` from revision `c31d4911837bbf13b829a0d484ef86681b954ce0`. Initial state `Q`, job name `d3d_a1h0_dc_r1`, CPU1, 16 GB, walltime `00:45:00`, serial threads, verified `abe` mail, checkout-local Fortran SHA `5a84a88c04988ebd69705c81ae5d3d1f56f103e3b52883ea3a394dfcdc691fbf`, and runtime-H SHA `dae747b3715e928d1346d33b27773d1318dc24071e99851a103a3dcc189238f8`. R1 authorization consumed immediately (`1/1`); no further retry is authorized.
- [x] R1 job `1378004.mmaster02` preserved as `stage_d3d_a1h0_datacheck_r1_fail` with PBS exit `8` and walltime `00:00:01`. Checkout-local checksum audit passed, candidate/R4 sources were byte-identical, and runtime H passed 25,600 records with zero duplicates/missing records. The pre-module inline deck gate then failed under default Python 3.6 because it used assignment-expression syntax; Abaqus did not launch and no pass marker exists. The gate is rewritten compatibly for prevention only; R1 remains consumed and no retry is authorized. Evidence: `runs/hpc/stage_d3/fracture_continuation/d3d_a1_checkpoint_hold_datacheck_r1/`.
- [x] Final isolated D3D-A1H0 datacheck R2 execution workflow prepared and authorized once (`stage_d3d_a1h0_datacheck_r2_authorized`). A shared login/compute preflight loads and binds Python 3.11.7 before any Python validation, verifies tracked byte-identical candidate/R4 Fortran, validates all 25,600 runtime-H records, and calls a committed two-step deck validator. Scientific inputs, deck physics, Fortran content, history, active set, tolerances, full hold, phase release, continuation, and D3E remain unchanged or unauthorized. If R2 fails, D3D-A1H0 execution closes blocked with no R3.
- [x] Exact R2 common preflight passed on the cluster login node with qualified Python `3.11.7`, byte-identical candidate/R4 Fortran, complete 25,600-record runtime H, 6,601 fixed phase nodes in both steps, unchanged checkpoint U2, correct candidate package, and no release/continuation.
- [x] Final R2 datacheck submitted exactly once through its guarded wrapper as job `1378005.mmaster02` from revision `b8e9ef636fa2629b34fbbc81babd00d726662a84`; initial state `Q`, job name `d3d_a1h0_dc_r2`, CPU1, 16 GB, walltime `00:45:00`, serial threads, verified `abe` mail. R2 authorization consumed immediately (`1/1`); no R3 or automatic retry is authorized.
- [x] Final R2 job `1378005.mmaster02` preserved as `stage_d3d_a1h0_datacheck_r2_fail`, PBS exit `8`, walltime `00:00:05`. The login-node common preflight passed, but the compute-node invocation stopped before Abaqus because the module purge/load sequence left `git` unavailable for the tracked-file check. No compile, input processing, or datacheck occurred and no pass marker exists. Under the explicit stopping rule, D3D-A1H0 execution is closed as blocked and no R3 may be created. Evidence: `runs/hpc/stage_d3/fracture_continuation/d3d_a1_checkpoint_hold_datacheck_r2/`.
- [!] New D3D solver submission is not authorized. D3E, a second segment, and peak/post-peak continuation remain blocked.
- [!] Original and R1 D3D-A1H0 datacheck authorizations are consumed by jobs `1378003.mmaster02` and `1378004.mmaster02`, respectively. No further datacheck is authorized. Full-hold solver submission, phase release, continuation, D3E, endpoint-union release, and tolerance changes remain prohibited.
- [!] Final R2 authorization is also consumed by job `1378005.mmaster02`. D3D-A1H0 execution is blocked at datacheck qualification; no R3, full hold, phase release, continuation, or D3E is authorized. The offline D3D-A1 correction remains passed, while the mechanically re-equilibrated checkpoint response remains unknown.
- [x] Stage D3D-A1H0 interpretation closed and consolidated into thesis methodology, results, limitations, and future work. The offline correction is reported as mathematically admissible under frozen F3 history; the candidate is explicitly not an accepted restart; the mechanical checkpoint response is unknown; and the three pre-Abaqus wrapper failures are separated from the scientific result. Evidence: `docs/thesis/STAGE_D3D_A1_CHECKPOINT_CORRECTION_AND_LIMITATION.tex`; `docs/decisions/STAGE_D3D_A1H0_EXECUTION_CLOSURE.md`.
- [!] Do not claim peak, post-peak, crack-path, production-mesh, or online-remeshing validation from D3A3 alone.
- [!] Do not alter the accepted C2C-v3 mesh or rerun C2F-v3 without new authorization.

- [x] Prepared exactly one authorized serial targeted-output diagnostic run for the unresolved SDV15 completed-update evidence. Classification: `paper_matched_candidate_v2_diagnostic_variant`. Evidence: `models/generated/molnar_gravouil_2017/paper_matched_single_notch_v2_sdv15_diagnostic/`; `runs/hpc/paper_matched_single_notch_v2_sdv15_diagnostic/RUN_MANIFEST.md`; `results/validation/molnar_paper_matched_single_notch_v2_sdv15_diagnostic/STATIC_VALIDATION.md`.
- [x] Submitted the single authorized diagnostic job exactly once. Job: `1375020.mmaster02`; revision: `efd5f60ebb9cc6ea8ce89b508a6e9df4183e5611`; result: `molnar_v2_sdv15_diagnostic_technical_fail`; cause: pre-solver batch PATH failure, `git: Kommando nicht gefunden`, so the revision guard exited before Abaqus launched. Evidence: `runs/hpc/paper_matched_single_notch_v2_sdv15_diagnostic/evidence/1375020.mmaster02/`; `runs/hpc/paper_matched_single_notch_v2_sdv15_diagnostic/RUN_SUMMARY.md`.
- [x] Prepared one infrastructure-corrected r2 diagnostic execution with no compute-node Git dependency, immutable scratch pre-stage, `16:00:00` walltime, and dedicated scratch PBS output. Classification scope: `infrastructure_corrected_targeted_diagnostic_execution`. Evidence: commit `209ad325d2c85532411c13d8290db08ca35b0637`; `scripts/hpc/submit_molnar_v2_sdv15_diagnostic_r2.sh`; `scripts/hpc/molnar_paper_matched_single_notch_v2_sdv15_diagnostic_r2.pbs`; `runs/hpc/paper_matched_single_notch_v2_sdv15_diagnostic_r2/RUN_MANIFEST.md`.
- [x] Reviewed the single authorized infrastructure-corrected r2 diagnostic job. Job: `1375028.mmaster02`; PBS wrapper result: `postprocess_python_compatibility_failure_after_successful_solve`; Abaqus result: `molnar_v2_sdv15_diagnostic_r2_technical_pass`; diagnostic instrumentation: `non_intrusive_pass`; scientific evidence: `sdv15_call_level_nonmonotonicity_observed`; completed/converged increment replay result: `sdv15_completed_increment_possible_violation`; severity-audit result: `sdv15_completed_increment_irreversibility_violation`; SDV16 decreases over the same final-increment sequences: `0`. Evidence: `runs/hpc/paper_matched_single_notch_v2_sdv15_diagnostic_r2/RUN_SUMMARY.md`; `runs/hpc/paper_matched_single_notch_v2_sdv15_diagnostic_r2/evidence/1375028.mmaster02/postprocessing_completed_increment_replay_time_aligned/`.
- [!] Gate A3 remains `reference_data_insufficient`; this run is targeted scientific evidence collection and does not authorize a retry, candidate v3, Stage B, MISESERI, remeshing, state transfer, or any parameter sweep.

## Stage F7 closeout (2026-07-31)

- [x] Exactly two authorized non-solver jobs submitted: `1380084.mmaster02`
  and `1380085.mmaster02`; two qsub attempts, no retry or replacement.
- [x] H2 fixed-material-point audit extracted 102 frames and found 1,120
  strict SDV15 decreases, minimum `-5.8532e-4`; irreversibility fails.
- [x] Corrected CAE qualification reached `RemeshingRule`; source hashes
  matched, but `variables[0]` rejected a Unicode string.
- [x] Verified zero solver executions for Stage F7, zero native-remesh
  executions, and no candidate refined deck.
- [!] H2 is not an accepted converged fracture reference; MISESERI native
  remeshing remains unqualified. No further HPC job is authorized.

## Stage F8 preflight closeout (2026-07-31)

- [x] Repaired M-106 offline using explicit numeric CSV schemas; the F7
  classification remains `h2_irreversibility_true_local_violation`.
- [x] Audited the frozen source: SDV15 is the interpolated nodal phase,
  SDV16 is the maximum-energy history, and no obstacle is enforced.
- [x] Prepared a governing-equation penalty candidate with consistent phase
  residual and tangent; no output-only clamp.
- [!] Both paired sources compiled and linked, but the common minimal patch
  datacheck failed with signal 11 during initial-stress processing.
- [x] Stopped before qsub: requested/actual submissions `3/0`; qsub attempts,
  retries, replacements, direct qsub, qdel and qmove all zero.
- [!] No candidate qualification or RemeshingRule type result exists. No HPC
  execution is authorized.

## Stage F9 diagnostic closeout (2026-07-31)

- [x] Exactly two diagnostic jobs submitted: `1380088.mmaster02` and
  `1380089.mmaster02`; two qsub attempts/successes and no retry, replacement,
  direct qsub, qdel, or qmove.
- [x] Job A isolated a UEL bounds violation: runtime `JELEM=24` for the first
  displacement element makes frozen `JELEM-N_ELEM` equal `-33828`.
- [x] Nominal deck labels map to `1..23`; the defect is the reduced model's
  runtime UEL numbering contract. UMAT-only datacheck passed.
- [!] Job B failed before CAE because its no-solver-audit filename did not
  match the staged file. The native variables type remains unresolved.
- [!] No baseline, penalty, H1, H2, refined, or adaptive analysis ran.
# P3-SM1T preparation update (2026-07-25)

- [x] P3-SM0 reference remains passed and closed. Evidence:
  `docs/decisions/STAGE_P_FINAL_SCIENTIFIC_CLOSURE.md`. Job
  `1378099.mmaster02`, solver exit 0, all four callback categories, 32/32
  state records, 13 increments, no signal 11, authorization consumed 1/1.
- [x] Prepare isolated P3-SM1T `GETTHREADID()` package and guarded 1/1/1 lane.
  Evidence: `runs/hpc/stage_p/p3sm1t_threadid_serial/`.
- [!] P3-SM1T job `1378239.mmaster02` consumed its only authorization (1/1)
  and closed as `stage_p3sm1t_threadid_serial_fail_identifier`. Compile,
  link, and input processing passed. The controlled UEL wrote the before
  marker, then runtime symbol resolution failed for `getthreadid_`; after
  count was 0, unmatched count 1, returned IDs empty, and signal 11 absent.
  No retry is authorized.
- [ ] `GETTHREADID` remains unqualified: the Abaqus 2023 runtime did not
  resolve the function-form `getthreadid_` symbol.
- [x] P3-I1 installed-interface audit classified. Evidence:
  `docs/decisions/STAGE_P3_IDENTIFIER_INTERFACE_DECISION.md`.
  `stage_p3_identifier_interface_partially_confirmed`: the installed Fortran
  header confirms `get_thread_id()` but not `GETTHREADID()`.
- [x] Prepare P3-SM1TC as a new corrected documented-interface lane based on
  P3-SM0. Execution is unauthorized at 0/1 with no retry.
  Evidence: `runs/hpc/stage_p/p3sm1tc_thread_id_serial/`.
- [x] Qualify installed `get_thread_id()` after separate review and
  authorization. Evidence:
  `runs/hpc/stage_p/p3sm1tc_thread_id_serial/P3SM1TC_RESULTS_SUMMARY.md`.
- [x] P3-SM1TC job `1378240.mmaster02` passed from authorization revision.
  Evidence:
  `runs/hpc/stage_p/p3sm1tc_thread_id_serial/P3SM1TC_RESULTS_SUMMARY.md`.
  Authorization revision
  `b072e32f322b440729318e06f2c2ab72d041fc12`: scheduler/solver exit 0,
  compile/link/input/Standard and readable ODB passed, before/after counts
  3/3, returned IDs `[0, 0, 0]`, unique IDs `[0]`, no signal 11 or unresolved
  symbol, 32/32 state records, and 13 increments. Authorization consumed 1/1;
  no retry.
- [x] Select the documented-call P3-SM1R route and prepare it offline using
  `CALL GETRANK(KPROCESSNUM)` only inside controlled UEL. Authorization remains
  false at 0/1, retry is disabled, and no Abaqus/PBS job has been submitted.
  Evidence: `docs/decisions/STAGE_P3_GETRANK_ROUTE_DECISION.md`.
- [x] P3-SM1R job `1378241.mmaster02` passed from authorization revision.
  Evidence:
  `runs/hpc/stage_p/p3sm1r_getrank_serial/P3SM1R_RESULTS_SUMMARY.md`.
  Authorization revision
  `4e941ffa7740a4c8050277351f25bcf392f8cd98`: PBS/solver exit 0, compile/link,
  input/Standard and readable ODB passed, GETRANK markers matched 3/3, returned
  IDs `[0,0,0]` with unique `[0]`, state coverage was 32/32, and all baseline
  gates passed. Authorization is consumed 1/1 with no retry.
- [!] P3-T4 job `1378242.mmaster02` closed as
  `stage_p3t4_threaded_fail_compile` with scheduler/solver exits `10/1`.
  The aggregate utility header was outside a Fortran scoping unit, so Intel
  rejected the first UEL declaration; linking, callbacks, diagnostics, ODB,
  and scientific comparison were not reached. Authorization is consumed 1/1
  with no retry. All downstream routes remain blocked.
- [x] Threaded-safety evidence interpretation is scientifically closed as
  technically inconclusive. Evidence:
  `docs/decisions/STAGE_P_FINAL_SCIENTIFIC_CLOSURE.md`. P3-SM0 supports the accepted serial callback baseline;
  P3-SM1TC and P3-SM1R qualify only their identifier interfaces at one rank
  and one thread; P3-T4 produced no threaded evidence. D2C remains positive,
  case-specific repeatability evidence rather than general COMMON/SAVE
  thread-safety proof. MPI and hybrid safety are unqualified.
- [x] Record the P3-T4 header-scope failure and future prevention offline. Evidence:
  `docs/decisions/P3T4_HEADER_SCOPE_FORENSIC_CORRECTION.md`.
  The failed source and evidence remain unchanged. Preprocessing alone is not
  a compile gate; any future solver authorization requires a real
  Intel/Abaqus compile-only and link gate.
- [!] No Stage P or downstream job is authorized. P3-T4-J2, an unchanged
  retry, a corrected threaded replacement, MPI, hybrid, P4, production H1,
  D3D-A1 reopening, and D3E are prohibited. A possible P3-T4C would require a
  distinct compile-only package, decision, fail-closed authorization, and
  one-shot limit and would support no callback or thread-safety claim.

## Stage F10 qualification closeout (2026-07-31)

- [x] Corrected compact UEL mapping qualified at runtime: U1 1--23, U2
  24--46, CPE4 47--69, with `N_ELEM=23` in UEL and UMAT and no bounds guard.
- [!] Baseline job `1380091.mmaster02` completed. Minimum fixed-point SDV15
  change was `-5.7817e-6`; SDV16 was monotone; energy evidence was unavailable.
- [!] Candidate job `1380092.mmaster02` completed. Minimum fixed-point SDV15
  change was `-5.9605e-8`, below the `1e-7` precision policy, with zero
  cutbacks and baseline-matching response. Classification remains
  `irreversibility_candidate_inconclusive` because energy and explicit
  penalty histories were not captured.
- [!] CAE-only job `1380093.mmaster02` passed staged-path audits but failed
  before the type matrix because `__file__` was undefined under Abaqus
  `execfile`. Native RemeshingRule type remains unresolved; solver, adaptive,
  remesh, and candidate-deck counts are zero.
- [x] Exactly three qsub attempts and successes; zero retry, further
  replacement, direct qsub, qdel, or qmove. All authority consumed.

## Stage F11 qualification closeout (2026-07-31)

- [x] Instrumented baseline `1380100.mmaster02` completed with the frozen
  minimal geometry, mapping, loading, and formulation.
- [x] Candidate `1380101.mmaster02` qualified on the minimal model: minimum
  SDV15 change `-5.9605e-8`, response agreement passed, diagnostic energy
  imbalance passed the predeclared two-percent limit, and penalty activity
  was observed after peak load.
- [x] Prior phase matched the preceding converged frame in all 9,200
  non-initial checks. No cutback occurred, so rollback remains unexercised.
- [x] CAE-only job `1380102.mmaster02` qualified the Abaqus 2023 native
  contract as a tuple containing Python 2 byte string `MISESERI`. It made no
  solver, adaptive, remesh, or candidate-deck call.
- [x] Exactly three qsub attempts and successes; no retry, replacement,
  direct qsub, qdel, or qmove. All authority consumed.
- [!] Only preparation of a future medium-H1 verification package is
  eligible. Submission, H2, refined, adaptive, and production runs remain
  unauthorized.

## Stage F12 preparation (2026-07-31)

- [x] Freeze complete Stage F11 candidate, generator, extractor, analyzer,
  energy-contract, and diagnostic-map identities.
- [x] Prepare conservative and aggressive automatic-increment rollback
  packages with identical physics, endpoint, output, and instrumentation.
- [x] Predeclare direct rollback, RF--U, final-field, phase-monotonicity, and
  diagnostic-energy acceptance policies.
- [x] Prepare CAE-only construction of the official corrected 3,930-element
  MISESERI coarse model with the qualified Python 2 byte-string tuple.
- [x] Verify canonical H1 N_ELEM=12064 and prepare guarded baseline/candidate
  packages as `prepared_not_authorized`.
- [!] Only the three named Stage F12 jobs may be submitted. Medium H1, H2,
  refined, native-adaptive, remesh, datacheck, restart, and continuation
  execution remain prohibited.

## Stage F12 closeout (2026-07-31)

- [x] Exactly three guarded qsub attempts succeeded: `1380971`, `1380972`,
  and `1380973`; no retry, replacement, direct qsub, qdel, or qmove.
- [!] Reference and aggressive candidate solves reached U1=0.006, but both
  had zero cutbacks. The aggressive case used two increments/two iterations;
  rollback is `penalty_rollback_not_exercised`.
- [!] The aggressive two-increment path also failed response and diagnostic
  energy agreement. It supplies no rollback qualification evidence.
- [x] CAE-only construction created the real coarse-model MISESERI rule and
  wrote an input deck with zero solver, adaptive, or remesh execution.
- [!] The medium-H1 pair remains preparation-only and is not ready for a
  separate execution authorization because rollback did not qualify.

## Stage F13 closeout (2026-08-01)

- [x] Jobs `1380981`, `1380982`, and `1380983` are terminal after exactly
  three accepted submissions; retries, replacements, direct qsub, qdel, and
  qmove remain zero.
- [!] Both rollback analyses failed before increment 1 on unresolved symbol
  `for_getenv_err`; PNEWDT did not trigger and rollback is not qualified.
- [!] Native execution reached `model.adaptiveRemesh(odb)` but failed because
  the model contained no adaptive region. No remesh completed and no candidate
  was generated.
- [!] Medium H1 is not ready for authorization, and no remeshed candidate is
  available for datacheck or indicator validation.

## Stage F14 closeout (2026-08-01)

- [x] Runtime job `1381368` loaded the repaired library, entered UEL, retained
  its job/output-directory log, reached the endpoint and exited zero.
- [x] `for_getenv_err` is absent; GETOUTDIR and GETJOBNAME resolve at runtime.
- [~] A future rollback pair is preparation-eligible but not authorized.
- [!] CAE-only job `1381369` verified source integrity and rule construction,
  but the adaptive-region repository/object remains unresolved; native remesh
  execution is not ready.

## F15/F16 conditional batch preparation (2026-08-01)

- [x] User-confirmed direct Telegram delivery recorded separately from
  independently published facts; direct sendmail remains unqualified.
- [x] Native PBS 2024.1 documentation confirms comma-separated `-M` users;
  both literal TU Freiberg aliases are frozen with mail points `abe`.
- [x] Prepared Wave A shell-only `M2NOTIFY1` with Telegram start/terminal
  hooks and native PBS email; no Abaqus or scientific execution.
- [x] Prepared byte-identical F16 rollback control/forced deck and source;
  only runtime `F16_FORCE_CUTBACK` differs.
- [x] Prepared zero-execution `M2RMREG2` to distinguish orphan mesh,
  geometry-backed ownership, rule, region, ALE and adaptivity contracts.
- [!] All four packages are `prepared_not_authorized`; qsub attempts remain
  zero and Wave B is blocked by Wave A technical and human delivery gates.

## F15 Wave A notification qualification (2026-08-01)

- [x] `M2NOTIFY1` job `1381373.mmaster02` completed with exit status 0.
- [x] Telegram START and COMPLETED passed technically on first attempts.
- [x] Native PBS BEGIN and END email were configured with mail points `abe`.
- [x] No Abaqus, scientific workload, nested qsub, retry, or replacement ran.
- [!] Wave B remains blocked pending personal confirmation of all four deliveries.

## F16 Wave B submission (2026-08-01)

- [x] User explicitly waived only the human PBS-email receipt gate; Telegram
  remains operational and PBS email remains best-effort/unconfirmed.
- [!] Both rollback qsub calls were rejected with return code 174 because
  access to `normal_imfdfkmq` was denied; no PBS IDs exist.
- [x] `M2RMREG2` was withheld because its `afterany` concurrency dependency
  could not be constructed without the control PBS ID.
- [x] No scientific, CAE, remesh, datacheck, retry, or replacement ran.
- [!] All Wave B authority is consumed; a future attempt requires new explicit authorization.

## F16 R3 routed-queue preparation (2026-08-01)

- [x] Installed PBS evidence classifies `entry_imfdfkmq` as the required Route
  queue and `normal_imfdfkmq` as a `from_route_only` Execution destination.
- [x] Prepared unique R3 job names and corrected all three wrappers to submit
  through `entry_imfdfkmq` without changing scientific artifacts.
- [x] Corrected orchestrator counts only actual qsub calls and records a
  dependency-withheld lane separately.
- [x] Resources remain 1 CPU/8 GB with 01:00:00 rollback and 00:30:00 CAE limits.
- [!] R3 execution is not authorized; qsub attempts in this preparation are zero.

## F16 R3 routed-queue closeout (2026-08-01)

- [x] Exactly three authorized qsub calls produced jobs `1381444`-`1381446`; no retry or replacement occurred.
- [x] Both rollback analyses reached their endpoints; the forced run exercised one controlled cutback and restored committed phase/SVARS state.
- [!] Penalty rollback remains inconclusive because the rejected trial did not activate penalty residual or energy, and response-equivalence tables were not retained.
- [!] Native adaptive-region construction failed on an Abaqus-Python generator incompatibility before any solver or remeshing execution.
- [x] Mandatory Telegram START and terminal delivery passed technically for all three jobs; PBS email remains best-effort.
- [!] Execution authority is consumed; medium H1, H2, native remesh, candidate datacheck, and refined analysis remain forbidden.

## F17 preparation (2026-08-01)

- [x] Prepared independent `M2IRRPENACT1` and `M2RMREG4` packages for the route queue.
- [x] Penalty scout uses the preserved 0.003/0.001/0.006 mm load-unload/reload history with forced PNEWDT disabled.
- [x] Penalty activation requires healing tendency plus nonzero residual and energy, finite tangent, and no bounds guard.
- [x] Response, phase, energy, accepted-increment tables and a SHA-256 extraction manifest are mandatory stage-out artifacts.
- [x] Corrected the Abaqus-Python generator incompatibility with explicit loops and a zero-model helper self-test.
- [!] Both jobs are preparation-only; qsub attempts are zero and no future rollback pair or native remesh is authorized.

## F17 authorized execution preflight (2026-08-02)

- [x] Explicit two-job authorization was recorded and pushed as `b6f3478`.
- [x] The scheduler was empty and the user-listed scientific/runtime hashes matched.
- [!] Submission failed closed because ten additional entries across the two committed `F17_SHA256SUMS` manifests did not match the clean Linux checkout.
- [x] No qsub, solver, CAE, datacheck, adaptivity, remesh, retry, replacement, qdel, qmove, or rerun occurred.
- [!] Authorization is invalidated. A separate manifest repair and new explicit authorization are required before either F17 job can be submitted.

## F17 Linux manifest repair proof (2026-08-02)

- [x] Diagnosed all ten stale entries as CRLF working-tree hashes versus canonical LF Git/Linux bytes.
- [x] Candidate `76addd7` corrected only the two manifests and added deterministic allowlists, tooling, and reports; scientific/runtime hashes were unchanged.
- [!] The mandatory second clean Linux proof stopped because frozen `M2RMREG4.pbs` lacks a final LF.
- [x] No silent repair iteration or frozen PBS modification was made.
- [!] Reproducibility is not qualified and no F17 execution authorization exists.

## F17 final-LF repair qualification (2026-08-02)

- [x] Published the exact one-byte `M2RMREG4.pbs` LF repair as `a44c2b6`.
- [x] Confirmed 1,167 bytes, final byte 10, and SHA-256 `6375b8c5...`.
- [!] Clean Linux validation stopped on another missing final LF in frozen `M2IRRPENACT1.pbs`.
- [x] No second validation, authorization request, scheduler call, or scientific execution followed.

## F17 probe-LF conditional execution preflight (2026-08-02)

- [x] Exact one-byte trial produced the expected repaired probe PBS hash `10451ed7...`.
- [!] Declared checksum-file hashes did not match the deterministic files produced by the sole authorized entry change.
- [x] Restored all trial package edits and stopped before commit, clean-Linux proof, authorization activation, or qsub.

## F17 canonical probe-LF preparation (2026-08-02)

- [x] Published exact Linux probe-PBS LF repair as `b68fae8`.
- [x] Second Linux checkout passed probe manifests 12/12 and adaptive F17 manifest 11/11.
- [!] Adaptive legacy `SHA256SUMS` failed five metadata entries; reproducibility remains unqualified.
- [x] No authorization activation, qsub, Abaqus, or CAE operation occurred.

## F17 final Linux qualification (2026-08-02)

- [x] Adaptive legacy manifest is byte-identical to adaptive `F17_SHA256SUMS`.
- [x] Second Linux proof passed probe 12/12 twice and adaptive 11/11 twice.
- [x] All 23 manifest-listed files matched their committed Git blobs.
- [!] Batch is qualified but not authorized; qsub attempts remain zero.

## F17 terminal closeout (2026-08-02)

- [x] `1381483` completed and qualified penalty activation with complete hash-valid evidence.
- [!] `1381484` failed before deck import because `F17_SOURCE_ODB` was unset.
- [x] All adaptive execution counters remain zero; native remesh is not ready.
- [x] Four Telegram START/terminal events passed technically; no retry occurred.
## Stage F18 preparation (2026-08-02)

- [x] Prepare byte-identical penalty-active rollback control/forced source and deck.
- [x] Keep the one-shot latch outside rollback-controlled SVARS.
- [x] Verify and freeze the source ODB path and SHA-256 for `M2RMREG5`.
- [x] Repair ODB lifetime, model inspection, environment, and zero-execution assertions.
- [x] Prepare guarded order and `afterany:M2IRRROLLCTL4` concurrency dependency.
- [!] Preparation only: no execution authority and no HPC job submitted.

## Stage F18 terminal closeout and F19 preparation (2026-08-03)

- [x] Preserve F18 accounting at three successful submissions with no retry or replacement.
- [!] Both rollback jobs failed before penalty activation on absent-file `STATUS='OLD'` runtime error 29; rollback remains unqualified.
- [!] Adaptive evidence is incomplete because the compatibility helper never generated its required JSON and exit 11 masked command status.
- [x] Prepare exactly `M2IRRROLLCTL5`, `M2IRRROLLFORCE5`, and `M2RMREG6` with checked flag I/O and repaired evidence lifecycle.
- [x] Run local WSL gfortran harness compile/link and actual UEL compile/relocatable-link checks; Intel Fortran unavailable locally.
- [!] Clean-Linux qualification and a fresh exact execution authorization remain pending. No F19 job is authorized.

## Stage F19 authorized execution preflight (2026-08-03)

- [x] Received exact three-job authorization and verified the frozen PBS and manifest hashes.
- [!] Guarded orchestrator does not export required `F19_PACKAGE_DIR` and `F19_EVIDENCE_DIR` variables with `qsub -v`.
- [x] Failed closed before cluster access or qsub; attempts/successes/failures remain 0/0/0.
- [!] Corrected clean-Linux-qualified preparation and fresh exact authorization are required.

## Stage F19 guarded-orchestrator repair (2026-08-03)

- [x] Export exactly `F19_PACKAGE_DIR` and `F19_EVIDENCE_DIR` with explicit `qsub -v`; broad `-V` is absent.
- [x] Mock success, failure, unsafe-path, PBS-ID, dependency, no-retry, and three-call-cap tests pass.
- [x] Detached Linux proof passed 12/12 tests, six manifests, 19 frozen hashes, and 47 checkout-to-blob checks.
- [x] All three frozen package trees are unchanged from `f1769b6`; real qsub attempts remain zero.
- [!] Preparation `d63181c` is qualified but not authorized; fresh exact three-job authorization is required.

## Stage F19 corrected execution authorization (2026-08-03)

- [x] Fresh exact authorization received for `M2IRRROLLCTL5`, `M2IRRROLLFORCE5`, and `M2RMREG6` from `d63181c`.
- [x] Order, route queue, two-variable export, adaptive dependency, three-call cap, and no-retry rules recorded.
- [-] Frozen-hash and read-only cluster/scheduler preflight pending; qsub attempts remain zero.

## Stage F19 corrected submission (2026-08-03)

- [x] Remote clean checkout, orchestrator hash, six manifests, notification config, route queue, and empty-user-queue preflight passed.
- [x] Exactly three guarded qsub calls succeeded: `1381758`, `1381759`, and `1381760`.
- [x] Adaptive job uses `afterany:1381758`; all jobs carry both required F19 variables.
- [x] Authority consumed with attempts/successes/failures 3/3/0 and no retry, replacement, direct qsub, qdel, qmove, or rerun.

## Stage F19 terminal closeout (2026-08-03)

- [x] Jobs `1381758`--`1381760` are terminal and lightweight evidence is inventoried.
- [~] Both rollback solvers completed and penalty activation was observed; forced exercised one cutback.
- [!] Rollback remains unqualified because extractor/analyzer table names did not match, leaving response-equivalence and accepted-state evidence incomplete.
- [!] Adaptive-region construction failed on an Abaqus Python 2 generator incompatibility before any solver, remesh, candidate, or datacheck call.
- [x] Authority remains consumed at 3/3; no retry or downstream execution is authorized.

## Stage F20 evidence recovery and adaptive R7 preparation (2026-08-03)

- [x] Recover both raw F19 rollback-call logs read-only and derive five canonical tables per lane.
- [x] Prove forced rejected-state restoration and exactly one deliberate cutback event.
- [!] Control/forced response comparison fails RF--U NRMSE and relative-energy limits; classification `penalty_rollback_response_mismatch`.
- [x] Do not prepare an unchanged rollback repeat; Medium H1 remains blocked.
- [x] Prepare only `M2RMREG7` with Python-2 loops and computed slit connectivity/topology audits.
- [x] Detached clean Linux proof `f877b81` passes; execution remains unauthorized with zero new qsub/Abaqus/CAE calls.

## Stage F20 M2RMREG7 submission (2026-08-03)

- [x] Exact one-job authorization recorded and all frozen hashes/preflight gates passed.
- [x] Guarded orchestrator made one qsub call; `1382428.mmaster02` entered queued state.
- [x] Required F20 package/evidence variables and 1 CPU/8 GB/00:30:00 resources verified in PBS.
- [x] Authority consumed 1/1; no retry, replacement, direct qsub, qdel, qmove, rerun, or other job.
