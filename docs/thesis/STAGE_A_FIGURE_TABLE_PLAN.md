# Stage A Figure and Table Plan

Status: `draft_from_existing_evidence_only`

Do not regenerate results through Abaqus. Items marked `must_generate_from_existing_data`
may be generated only from committed JSON/CSV/text evidence or retained existing
images.

## Figures

| ID | Figure | Source evidence | Caption draft | Status |
|---|---|---|---|---|
| F-A1 | Paper-matched candidate-v2 geometry and split-notch schematic | `models/generated/molnar_gravouil_2017/paper_matched_single_notch_v2/paper_matched_single_notch_v2.inp`; `references/derived/molnar_gravouil_2017/paper_matched_single_notch/NOTCH_IMPLEMENTATION.md` | Paper-matched single-notch reconstruction showing the 1 mm by 1 mm plate, left-edge split-node notch, and horizontal crack corridor. | `must_generate_from_existing_data` |
| F-A2 | Mesh-size and layer architecture overview | `models/generated/molnar_gravouil_2017/paper_matched_single_notch_v2/mesh_statistics.csv`; `models/generated/molnar_gravouil_2017/paper_matched_single_notch_v2/layer_mapping.csv`; `results/validation/molnar_paper_matched_single_notch_v2/MESH_QUALITY_PREFLIGHT.md` | Candidate-v2 mesh and UEL/UMAT layer architecture, with the refined fracture corridor distinguished from documented high-aspect-ratio regions. | `must_generate_from_existing_data` |
| F-A3 | RF--U curve against approximate Fig. 7 reference | `runs/hpc/paper_matched_single_notch_v2/scientific_review/fig7_comparison_overlay.csv`; `references/derived/molnar_gravouil_2017/paper_matched_single_notch/fig7_lc_0p0075_processed.csv` | Candidate-v2 reaction-force response compared with the approximate digitized Molnar Fig. 7 red dashed `lc=0.0075 mm` reference. | `must_generate_from_existing_data` |
| F-A4 | Pre-peak and post-peak RF--U error split | `runs/hpc/paper_matched_single_notch_v2/scientific_review/fig7_comparison_metrics.json`; `runs/hpc/paper_matched_single_notch_v2/scientific_review/fig7_reference_grid_comparison.csv` | RF--U error split showing moderate pre-peak mismatch and dominant post-peak disagreement. | `must_generate_from_existing_data` |
| F-A5 | Matched response-state phase contours | `runs/hpc/paper_matched_single_notch_v2/extracted/matched_state_*_contour_sdv14_sdv15_sdv16.csv` | Phase-field states at early loading, late pre-peak loading, near peak response, and final post-peak response. | `must_generate_from_existing_data` |
| F-A6 | Final crack-threshold sensitivity | `runs/hpc/paper_matched_single_notch_v2/scientific_review/crack_path_threshold_metrics.csv` | Connected final crack extension for element-mean `SDV15` thresholds 0.80, 0.90, 0.95, and 0.99. | `must_generate_from_existing_data` |
| F-A7 | SDV15 completed-increment decrease histogram | `runs/hpc/paper_matched_single_notch_v2_sdv15_diagnostic_r2/evidence/1375028.mmaster02/postprocessing_completed_increment_replay_time_aligned/severity_audit/sdv15_completed_increment_severity_summary.json`; `.../sdv15_completed_increment_violating_transitions.csv` | Magnitude distribution of completed-increment SDV15 decreases after the non-intrusive targeted diagnostic replay. | `must_generate_from_existing_data` |
| F-A8 | Largest SDV15 completed-increment decrease trace | `runs/hpc/paper_matched_single_notch_v2_sdv15_diagnostic_r2/evidence/1375028.mmaster02/postprocessing_completed_increment_replay_time_aligned/sdv15_completed_increment_violating_transitions.csv`; `.../severity_audit/sdv15_completed_increment_severity_summary.json` | Largest completed-increment SDV15 decrease at physical element 16428, source-storage IP 4, with SDV16 unchanged. | `must_generate_from_existing_data` |
| F-A9 | Evidence provenance flow | `runs/hpc/paper_matched_single_notch_v2/RUN_MANIFEST.md`; `runs/hpc/paper_matched_single_notch_v2_sdv15_diagnostic_r2/RUN_SUMMARY.md`; `docs/decisions/MOLNAR_GATE_A3_SUPERVISOR_REVIEW.md` | Provenance chain from candidate-v2 generation through baseline solve, no-solution review, targeted diagnostic replay, and frozen Gate A3 supervisor decision. | `must_generate_from_existing_data` |

## Tables

| ID | Table | Source evidence | Caption draft | Status |
|---|---|---|---|---|
| T-A1 | Model parameters and reconstruction assumptions | `runs/hpc/paper_matched_single_notch_v2/RUN_MANIFEST.md`; `references/derived/molnar_gravouil_2017/paper_matched_single_notch/PARAMETER_PROVENANCE.csv`; `configs/molnar_paper_matched_single_notch.yaml` | Geometry, material, length-scale, loading, and reconstruction assumptions for candidate v2. | `exists_in_chapter_text` |
| T-A2 | Deck/source hashes and revisions | `runs/hpc/paper_matched_single_notch_v2/RUN_MANIFEST.md`; `runs/hpc/paper_matched_single_notch_v2_sdv15_diagnostic_r2/evidence/1375028.mmaster02/postprocessing_completed_increment_replay_time_aligned/PROVENANCE.md` | Committed revisions and SHA-256 hashes required to reproduce the Stage A evidence chain. | `exists_in_appendix_text` |
| T-A3 | Technical execution resources | `runs/hpc/paper_matched_single_notch_v2/scientific_review/solver_resource_metrics.json`; `runs/hpc/paper_matched_single_notch_v2_sdv15_diagnostic_r2/RUN_SUMMARY.md` | CPU, memory, walltime, and solver status for the baseline and diagnostic r2 jobs. | `exists_in_appendix_text` |
| T-A4 | RF--U comparison metrics | `runs/hpc/paper_matched_single_notch_v2/scientific_review/fig7_comparison_metrics.json`; `runs/hpc/paper_matched_single_notch_v2/scientific_review/FIG7_COMPARISON_AUDIT.md` | Peak response, RMSE split, NRMSE, tangent-stiffness error, and area error against the approximate Fig. 7 reference. | `exists_in_chapter_text` |
| T-A5 | Crack extension by SDV15 threshold | `runs/hpc/paper_matched_single_notch_v2/scientific_review/crack_path_threshold_metrics.csv`; `runs/hpc/paper_matched_single_notch_v2/scientific_review/SCIENTIFIC_DECISION.md` | Final connected crack extension and vertical deviation for high-damage thresholds. | `exists_in_chapter_text` |
| T-A6 | SDV15 and SDV16 irreversibility metrics | `runs/hpc/paper_matched_single_notch_v2/scientific_review/sdv_irreversibility_metrics.json`; `runs/hpc/paper_matched_single_notch_v2_sdv15_diagnostic_r2/RUN_SUMMARY.md`; `.../severity_audit/sdv15_completed_increment_severity_summary.json` | Retained-frame and completed-increment SDV15 decreases, overshoot, and SDV16 monotonicity. | `exists_in_chapter_text` |
| T-A7 | Supervisor decision routes | `docs/decisions/POST_SUPERVISOR_DECISION_EXECUTION_ROUTES.md` | Route-neutral execution consequences after the supervisor's Gate A3 decision. | `exists_as_decision_table` |
| T-B1 | lc015 h-convergence case metrics | `results/tables/molnar_lc015_h_convergence/h_convergence_case_metrics.csv` | Peak RF2, Upeak, tangent, N, h, walltime for H0/H1/H2-PUB. | `generated_from_existing_data` |
| T-B2 | Successive mesh RF-U differences | `results/tables/molnar_lc015_h_convergence/h_convergence_successive_differences.csv` | H0–H1 and H1–H2 peak and full/pre/post NRMSE. | `generated_from_existing_data` |
| T-B3 | Fig.7 lc015 publication comparison | `results/tables/molnar_lc015_h_convergence/h_convergence_publication_comparison.csv` | Overlap NRMSE vs approximate digitized lc=0.015 curve. | `generated_from_existing_data` |
| F-B1–F-B10 | lc015 h-convergence figure set | `results/figures/molnar_lc015_h_convergence/` | RF-U family, publication overlay, peak zoom, differences, resource plots. | `generated_from_existing_data` |

## Existing Images or Plot Data

- `runs/hpc/paper_matched_single_notch_v2/scientific_review/fig7_comparison_overlay.csv`
- `runs/hpc/paper_matched_single_notch_v2/extracted/matched_state_*_contour_sdv14_sdv15_sdv16.csv`
- `references/derived/molnar_gravouil_2017/paper_matched_single_notch/fig7_lc_0p0075_crop_300dpi.png`

No item in this plan requires a new Abaqus solve, PBS submission, candidate v3,
uniform-reference run, MISESERI run, remeshing run, or state-transfer run.
