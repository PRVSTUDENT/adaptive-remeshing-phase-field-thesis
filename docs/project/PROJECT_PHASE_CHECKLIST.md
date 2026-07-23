# Project Phase Checklist

Updated: 2026-07-21

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
Stage A: open (residual historical items may still use `reference_data_insufficient` for full unconditional closure)

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
| WP5 | Evolving remesh and state transfer | `[-]` D0/D1 started | variable map plus analytical local harness | `docs/studies/STAGE_D_STATE_TRANSFER_VARIABLE_MAP.md`; `results/validation/stage_d_analytical_transfer/` |
| WP6 | IMFD/ABAQUSER integration | `[ ]` not started | dependent on D1/D2 transfer evidence | `THESIS_PLAN.md` |
| WP7 | Final recommendations and thesis writing | `[-]` in progress | Stage A living reports active | `docs/reports/STAGE_A_BASELINE_REPORT.tex`; `docs/reports/STAGE_A_EXECUTION_AND_FAILURE_LOG.tex` |

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
- [ ] Test parallel repeatability where scientifically justified.
- [!] No online/evolving-remeshing claim until these checks pass. Evidence: `THESIS_PLAN.md`.
- [!] D3D/D3E blocker: explicit fracture-continuation authorization — not missing `D3A3.ok`.

## WP6 - IMFD/ABAQUSER

- [ ] Define required interface fields.
- [ ] Map variable names, components and units.
- [ ] Verify integration-point ordering.
- [ ] Compare ABAQUSER output with independent extraction.
- [ ] Document visualization procedure.

## WP7 - Final Recommendations And Thesis Writing

- [-] Maintain Stage A baseline report. Evidence: `docs/reports/STAGE_A_BASELINE_REPORT.tex`.
- [-] Maintain Stage A execution/failure report. Evidence: `docs/reports/STAGE_A_EXECUTION_AND_FAILURE_LOG.tex`.
- [-] Maintain this project checklist. Evidence: `docs/project/PROJECT_PHASE_CHECKLIST.md`.
- [x] Prepared thesis-ready Stage A benchmark chapter draft from committed evidence only. Evidence: `docs/thesis/STAGE_A_MOLNAR_BENCHMARK_CHAPTER.tex`.
- [x] Prepared Stage A reproducibility appendix draft with revisions, hashes, job records, trace provenance, and excluded-file policy. Evidence: `docs/thesis/STAGE_A_REPRODUCIBILITY_APPENDIX.tex`.
- [x] Prepared Stage A figure/table plan from existing evidence paths only. Evidence: `docs/thesis/STAGE_A_FIGURE_TABLE_PLAN.md`.
- [x] Prepared route-neutral post-supervisor execution plan. Evidence: `docs/decisions/POST_SUPERVISOR_DECISION_EXECUTION_ROUTES.md`.
- [~] Reviewed LaTeX build-product ignore coverage and added recurring build-artifact patterns. Evidence: `.gitignore`. Limitation: existing untracked generated files were not deleted.
- [x] Prepared Stage B uniform-reference protocol without simulations, deck generation, PBS preparation, or submission. Evidence: `docs/studies/STAGE_B_UNIFORM_REFERENCE_PROTOCOL.md`; `docs/studies/STAGE_B_ACCEPTANCE_METRICS.md`; `docs/studies/STAGE_B_HPC_RESOURCE_ESTIMATE.md`; `configs/studies/molnar_uniform_reference_matrix.yaml`.
- [x] Supervisor approved only the Molnar `lc=0.015 mm` h-convergence subset for execution (H0 exact supplementary, H1 `h=0.0025 mm`, H2-PUB `h=0.001 mm`). Length-scale, increment-sensitivity, MISESERI, remeshing, multi-CPU, and GPU work remain unauthorized. Evidence: `docs/studies/STAGE_B_UNIFORM_REFERENCE_PROTOCOL.md`; `configs/studies/molnar_uniform_reference_matrix.yaml`.
- [ ] Freeze Stage A reports after Stage A closure.
- [ ] Create the Stage B results report.
- [ ] Create the Stage B execution/failure log.
- [ ] Complete final accuracy-cost conclusions.
- [ ] Complete implementation-limitations chapter.
- [ ] Complete recommendations.
- [ ] Archive final reproducibility package.

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

Prepare the scoped D3D/D3E fracture-continuation decision package.  
No continuation submission without explicit authorization.

### Current Stage D Boundary

- [x] D3A3 compatibility-ingestion/release-hold gate closed at R4 (`1377471.mmaster02`; canonical `D3A3.ok`).
- [!] Do not submit D3D or D3E without explicit fracture-continuation authorization.
- [!] Do not claim peak, post-peak, crack-path, production-mesh, or online-remeshing validation from D3A3 alone.
- [!] Do not alter the accepted C2C-v3 mesh or rerun C2F-v3 without new authorization.

- [x] Prepared exactly one authorized serial targeted-output diagnostic run for the unresolved SDV15 completed-update evidence. Classification: `paper_matched_candidate_v2_diagnostic_variant`. Evidence: `models/generated/molnar_gravouil_2017/paper_matched_single_notch_v2_sdv15_diagnostic/`; `runs/hpc/paper_matched_single_notch_v2_sdv15_diagnostic/RUN_MANIFEST.md`; `results/validation/molnar_paper_matched_single_notch_v2_sdv15_diagnostic/STATIC_VALIDATION.md`.
- [x] Submitted the single authorized diagnostic job exactly once. Job: `1375020.mmaster02`; revision: `efd5f60ebb9cc6ea8ce89b508a6e9df4183e5611`; result: `molnar_v2_sdv15_diagnostic_technical_fail`; cause: pre-solver batch PATH failure, `git: Kommando nicht gefunden`, so the revision guard exited before Abaqus launched. Evidence: `runs/hpc/paper_matched_single_notch_v2_sdv15_diagnostic/evidence/1375020.mmaster02/`; `runs/hpc/paper_matched_single_notch_v2_sdv15_diagnostic/RUN_SUMMARY.md`.
- [x] Prepared one infrastructure-corrected r2 diagnostic execution with no compute-node Git dependency, immutable scratch pre-stage, `16:00:00` walltime, and dedicated scratch PBS output. Classification scope: `infrastructure_corrected_targeted_diagnostic_execution`. Evidence: commit `209ad325d2c85532411c13d8290db08ca35b0637`; `scripts/hpc/submit_molnar_v2_sdv15_diagnostic_r2.sh`; `scripts/hpc/molnar_paper_matched_single_notch_v2_sdv15_diagnostic_r2.pbs`; `runs/hpc/paper_matched_single_notch_v2_sdv15_diagnostic_r2/RUN_MANIFEST.md`.
- [x] Reviewed the single authorized infrastructure-corrected r2 diagnostic job. Job: `1375028.mmaster02`; PBS wrapper result: `postprocess_python_compatibility_failure_after_successful_solve`; Abaqus result: `molnar_v2_sdv15_diagnostic_r2_technical_pass`; diagnostic instrumentation: `non_intrusive_pass`; scientific evidence: `sdv15_call_level_nonmonotonicity_observed`; completed/converged increment replay result: `sdv15_completed_increment_possible_violation`; severity-audit result: `sdv15_completed_increment_irreversibility_violation`; SDV16 decreases over the same final-increment sequences: `0`. Evidence: `runs/hpc/paper_matched_single_notch_v2_sdv15_diagnostic_r2/RUN_SUMMARY.md`; `runs/hpc/paper_matched_single_notch_v2_sdv15_diagnostic_r2/evidence/1375028.mmaster02/postprocessing_completed_increment_replay_time_aligned/`.
- [!] Gate A3 remains `reference_data_insufficient`; this run is targeted scientific evidence collection and does not authorize a retry, candidate v3, Stage B, MISESERI, remeshing, state transfer, or any parameter sweep.
