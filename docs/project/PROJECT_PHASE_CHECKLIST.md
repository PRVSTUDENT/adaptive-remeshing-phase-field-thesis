# Project Phase Checklist

Updated: 2026-07-16

This is the authoritative living task and phase checklist for the adaptive remeshing thesis workspace. Update this same file after every substantial task, run, validation, failure, retry, decision, gate transition, and phase completion. Do not create duplicate phase checklists.

Status markers:

- `[x]` completed and supported by evidence
- `[ ]` not started
- `[-]` in progress
- `[!]` blocked
- `[?]` awaiting review, approval, or missing evidence
- `[~]` completed provisionally but not scientifically validated

Gate A3: reference_data_insufficient
Stage A: open

## Overall Phase Dashboard

| Phase | Description | Status | Gate/result | Evidence |
|---|---|---|---|---|
| WP0 | Environment, starter pipeline, and source preservation | `[x]` completed | technical environment passed | `.agent.md`; `models/baseline_original/molnar_gravouil_2017/README.md`; `hpc_access_limits_report.txt` |
| WP1 | One-element verification | `[~]` completed provisionally | source-defined numerical checks passed under provisional tolerances | `runs/molnar_one_element_unchanged/20260714_technical_gate_local/scientific_check/` |
| WP2A | Supplementary Molnar single-notch technical benchmark | `[~]` completed provisionally | technical pass; not exact Fig. 7 comparison | `runs/molnar_single_notch_unchanged/20260714_technical_gate_local/` |
| WP2B | Paper-matched Molnar reconstruction | `[~]` completed provisionally | technical pass; scientific review required | `runs/hpc/paper_matched_single_notch_v2/RUN_MANIFEST.md`; `runs/hpc/paper_matched_single_notch_v2/scientific_check/` |
| Gate A3 | Uniform reference scientific justification | `[!]` blocked | open; tolerances and uniform-reference justification pending | `configs/molnar_paper_matched_single_notch.yaml`; `references/derived/molnar_gravouil_2017/paper_matched_single_notch/`; `runs/hpc/paper_matched_single_notch_v2/scientific_check/` |
| WP3 | MISESERI pre-analysis and remeshing reproduction | `[!]` blocked | blocked by Gate A3 | `THESIS_PLAN.md` |
| WP4 | Refined phase-field benchmark and efficiency comparison | `[ ]` not started | dependent on WP3 | `THESIS_PLAN.md` |
| WP5 | Evolving remesh and state transfer | `[ ]` not started | mandatory later thesis task | `THESIS_PLAN.md` |
| WP6 | IMFD/ABAQUSER integration | `[ ]` not started | dependent on stable fields | `THESIS_PLAN.md` |
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
- [x] Permanent PBS email-notification rule recorded for future submissions. Requirement: explicit `#PBS -M <verified_recipient>` and `#PBS -m abe`, validated before the first submission with `scripts/hpc/validate_pbs_email_notifications.py`. Boundary: current running job `1374864.mmaster02` remains unchanged. Evidence: `.agent.md`; `scripts/hpc/validate_pbs_email_notifications.py`.

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
- [?] Replace the PBS email placeholder with the exact verified HPC notification address before any new submission.
- [x] Extract RF-displacement and response-based phase/SDV contours from the completed ODB without rerunning Abaqus. Evidence: `runs/hpc/paper_matched_single_notch_v2/extracted/`.
- [~] Compare with approximate published Fig. 7 reference. Result: `scientific_review_required`; peak RF2 `0.761702 kN` at `U2=0.006110 mm`; RF-U NRMSE `0.247493`; relative peak-force error `0.064519`; relative peak-displacement error `0.041257`. Evidence: `runs/hpc/paper_matched_single_notch_v2/scientific_check/SINGLE_NOTCH_SCIENTIFIC_CHECK.md`.
- [~] Crack-path and SDV diagnostics completed. Result: final `SDV15 >= 0.95` crack extension about `0.0505 mm`; `SDV16` monotonic; `SDV15` decrease/overshoot candidates require review. Evidence: `runs/hpc/paper_matched_single_notch_v2/scientific_check/crack_path_comparison.csv`; `runs/hpc/paper_matched_single_notch_v2/scientific_check/single_notch_scientific_check.json`.
- [ ] Perform mesh-size study.
- [ ] Perform length-scale study.
- [ ] Perform load-increment study.
- [ ] Establish justified uniform fine reference.
- [!] Gate A3 closure blocked until supervisor-approved tolerances and uniform-reference justification are resolved. Evidence: `configs/molnar_paper_matched_single_notch.yaml`; `runs/hpc/paper_matched_single_notch_v2/scientific_check/`.

## WP3 - MISESERI Pre-Analysis And Remeshing Reproduction

- [!] Blocked until Gate A3 passes. Evidence: `THESIS_PLAN.md`; current Gate A3 status above.
- [ ] Reproduce Pandey-Kumar MISESERI extraction.
- [ ] Validate physical-element to visualization-element mapping.
- [ ] Generate locally refined mesh.
- [ ] Regenerate valid UEL/UMAT layered deck.
- [ ] Run refined elastic dry test.
- [ ] Validate local target `h/l`.

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

- [ ] Inventory all transferable state variables.
- [ ] Design controlled field-transfer test.
- [ ] Transfer known analytical fields.
- [ ] Calculate L2 and maximum transfer errors.
- [ ] Check field bounds.
- [ ] Check history and phase-field irreversibility.
- [ ] Measure energy jumps.
- [ ] Test fracture-relevant state transfer.
- [ ] Test serial repeatability.
- [ ] Test parallel repeatability where scientifically justified.
- [!] No online/evolving-remeshing claim until these checks pass. Evidence: `THESIS_PLAN.md`.

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
| Gate A3 | justified uniform reference and fixed metrics | blocked | paper-matched reconstruction incomplete |
| MISESERI gate | refined deck valid and local size achieved | not started | Gate A3 |
| Refined benchmark gate | accepted error and measured benefit | not started | MISESERI |
| State-transfer gate | controlled and fracture transfer pass | not started | later stage |
| ABAQUSER gate | output agrees with independent extraction | not started | later stage |

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

Exact next checklist item: `[-] Commit and synchronize candidate v2, then perform clean local/HPC revision checks before using the dormant one-run authorization`.
