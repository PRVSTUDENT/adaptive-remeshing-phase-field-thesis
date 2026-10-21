# Mode-I adaptive remeshing: validated results

Technical progress report | 22 October 2026

## 1. Method A and Method B: what changes?

Method A: one preliminary simulation, one native adaptive remesh, then a fresh final simulation from zero load. Method B extends that same two-pass approach by partitioning preliminary loading into configurable 1, 2 or 4 steps and selecting/evaluating the relevant MISESERI field before one remesh and a fresh final solve.

B varies the loading schedule and field-selection opportunities. It does not preserve a loaded fracture state across meshes or perform multiple remeshing cycles. With one step and the same controls, its architecture reduces to Method A.

![Conceptual A/B workflow. The shared architecture has two simulation passes and exactly one remesh; only the pre-analysis schedule and field-selection flexibility differ.](figures/method_b_workflow.png)

Conceptual A/B workflow. The shared architecture has two simulation passes and exactly one remesh; only the pre-analysis schedule and field-selection flexibility differ.

![Figure 2. Authentic coarse mesh, automatically generated native Method B mesh (14,677 FE) and tip zoom, and separate retrospectively corrected ligament-resolution verification mesh (14,483 FE). Partition choice did not cause the latter correction.](figures/mesh_artifacts.png)

Figure 2. Authentic coarse mesh, automatically generated native Method B mesh (14,677 FE) and tip zoom, and separate retrospectively corrected ligament-resolution verification mesh (14,483 FE). Partition choice did not cause the latter correction.

Keep two findings separate: A - the partition study produced equivalent native 14,677-element meshes; B - a distinct retrospective ligament-resolution study evaluated the corrected 14,483-element fracture response.

# 2. Finding A: Method B loading-partition study

The executed infinitesimal-companion decks prescribe cumulative RP displacements of 0.005 mm (1 step); 0.0025, 0.005 mm (2 steps); and 0.00125, 0.0025, 0.00375, 0.005 mm (4 steps). Equal divisions are verified from these decks, not assumed.

![Figure 3. Verified deck-derived prescribed histories, not measured solver curves. Each step lasts 1.0 static step-time unit; total times are 1, 2 and 4. Stars mark the selected terminal MISESERI frames; one native remesh follows each complete pre-analysis.](figures/method_b_loading_schedules.png)

Figure 3. Verified deck-derived prescribed histories, not measured solver curves. Each step lasts 1.0 static step-time unit; total times are 1, 2 and 4. Stars mark the selected terminal MISESERI frames; one native remesh follows each complete pre-analysis.

| Partitions | Endpoint [mm] | MISESERI comparison | Native FE | Observed difference |
| --- | --- | --- | --- | --- |
| 1 | 0.005000 | Reference terminal field | 14,677 | Baseline |
| 2 | 0.005000 | Max |difference| = 0 | 14,677 | No field/mesh change |
| 4 | 0.005000 | Max |difference| = 0 | 14,677 | No field/mesh change |

Field output is requested every increment. The compared selections are the last frames of Step-1, Step-2 and Step-4 respectively (increments 500, 250 and 125). The physical displacement increment is 0.000010 mm in every schedule. Archived verification reports identical recovered fields and native mesh identity, with 14,646 nodes in each case.

## What did B add beyond A?

B made preliminary loading and field selection configurable, and tested whether step boundaries alone alter the native mesh. For this common pre-peak endpoint, they did not. This is consistent with linear-elastic companion-layer stress recovery: at the same mesh and endpoint state, subdividing a monotonic load schedule adds no new spatial error information.

This is an observed invariance result, not an accuracy advantage. Companion-layer elasticity does not make the physical phase-field model globally linear. Benefits of selecting intermediate frames were not tested. Different frames, evolving damage, unloading or other controls could change the result. No final fracture-response improvement is attributed to partition count; B remains a one-remesh/two-pass extension, not a demonstrated sequential adaptive algorithm.

# 3. Finding B: corrected ligament-resolution study

The separate retrospectively refined 14,483-element verification mesh (serial job 1412465) is compared with canonical fixed reference job 1398090. It uses prior crack-path/ligament information. Its improved brittle fracture response is a mesh-resolution finding, not a benefit caused by choosing 1, 2 or 4 loading partitions.

| Quantity | Corrected Method B | Fixed reference | Difference |
| --- | --- | --- | --- |
| Base elements | 14,483 | 15,192 | -4.67% |
| Initial stiffness [kN/mm] | 137.9096 | 137.9455 | -0.026% |
| Peak force [N] | 743.701 | 757.778 | -1.86% |
| Matched external work [mJ] | 2.2674 | 2.3587 | -3.87% |
| Comparison endpoint [mm] | 0.007889 | 0.007889 | Same horizon |

![Figure 1. Authentic corrected Method B and fixed-reference histories, both ending at 0.007889 mm. Force is in N; work is in mJ; plotted displacement is in micrometres. No corrected data are extrapolated.](figures/method_b_response.png)

Figure 1. Authentic corrected Method B and fixed-reference histories, both ending at 0.007889 mm. Force is in N; work is in mJ; plotted displacement is in micrometres. No corrected data are extrapolated.

## Validated range and interpretation

Initial stiffness and peak-force differences meet the reported 0.5% and 2% criteria. Matched-horizon external work differs by -3.87%. This supports the corrected mesh as a useful pre-refinement baseline within the verified range.

The corrected solve reached 0.007889 mm; the full 0.010 mm horizon was not completed. The reference is deliberately cropped to the same endpoint. Retrospective ligament refinement does not establish that native automatic remeshing independently predicted the whole crack path.

Work provenance: direct CSV re-integration gives 2.267379 mJ and 2.358732 mJ (approximately -3.87%). The earlier summary listed reference 2.3586 mJ; 2.3587 mJ is the reproducible rounded CSV value. Work follows the established first-recorded-row zero convention; see FIGURE_SOURCES.md.

# 4. Method C: shared workflow and current evidence

Step 0 solves on a coarse mesh and monitors the crack region. Each of four proposed cycles then extracts displacement u, damage d and committed history H; remeshes; transfers and re-equilibrates the state; and continues loading. C1/C2 differ in whether earlier refinement is retained or selectively coarsened (Section 5).

## Verified building blocks; nonmatching handoff still unqualified

Native mesh generation and a same-mesh continuation control are demonstrated. At u=0.00270 mm, that control gives 5.2881993 N versus 5.2895973 N (-0.0264% endpoint difference). It establishes neither whole-trajectory agreement nor nonmatching-transfer qualification.

Crack-band receiver test mesh CB-2300 (formerly Candidate C2) is an unrelated offline test: 2,300 quads, 2,413 nodes, 0.1 x 0.1 mm domain, 0.001 mm band spacing and positive minimum Jacobian 3.125e-7. Its equilibrated force is 0.366 N versus donor 7.851 N (-95.34%, FAIL); maximum damage healing is 0.0021837.

![Figure 5. Authentic intermediate receiver and CB-2300 test meshes with actual slit-tip close-ups. Neither mesh is a Method C1/C2 strategy or an accepted adaptive cycle.](figures/candidate_c1_c2_meshes.png)

Figure 5. Authentic intermediate receiver and CB-2300 test meshes with actual slit-tip close-ups. Neither mesh is a Method C1/C2 strategy or an accepted adaptive cycle.

![Figure 6. Authentic offline checks: CB-2300 elastic stiffness discrepancy 4.58% (limit 5%) and fracture-energy discrepancy +0.79% (limit 2%). Passing subchecks do not qualify continuation.](figures/candidate_c2_passing_checks.png)

Figure 6. Authentic offline checks: CB-2300 elastic stiffness discrepancy 4.58% (limit 5%) and fracture-energy discrepancy +0.79% (limit 2%). Passing subchecks do not qualify continuation.

CB-2300 is only a report label; scientific filenames and checkpoints are unchanged. Zero healing in the separate constrained 650-element prototype is not a CB-2300 result. Neither this test nor the continuation control demonstrates wake coarsening. No complete nonmatching remesh-and-continue cycle is qualified.

# 5. Planned Method C1 and Method C2 strategies

Both strategies target four state-preserving cycles following the evolving crack. C1 - Sequential forward refinement generally retains earlier fine regions. C2 - Sequential refinement with selective wake coarsening investigates removing unnecessary wake resolution while protecting active and damaged regions, potentially limiting mesh growth.

![Figure 4. Side-by-side conceptual progressions: C1 accumulates refinement; C2 could limit mesh growth through conditional coarsening while protecting the damaged corridor. All ten panels are illustrative, not completed solver cycles.](figures/method_c_planned_workflow.png)

Figure 4. Side-by-side conceptual progressions: C1 accumulates refinement; C2 could limit mesh growth through conditional coarsening while protecting the damaged corridor. All ten panels are illustrative, not completed solver cycles.

| Comparison | Method C1 | Method C2 |
| --- | --- | --- |
| Earlier fine regions | Generally retain refinement | Selective coarsening only after physical checks |
| Qualification | Not validated for complete nonmatching cycles | Not validated; coarsening not verified |

Coarsening must preserve damage irreversibility, fracture energy, displacement compatibility, crack opening and mechanical compliance. The active process zone and damaged regions need sufficient resolution; a relaxed wake is not automatically safe to coarsen. No cost saving is claimed.

## Scientific decision and immediate next work

First qualify one physically continuous C1 nonmatching handoff, then sequential refinement. Method C2 coarsening is an additional proposed extension after that dependency passes. Preserve the validated Method B findings; do not treat CB-2300 as a Method C2 implementation.

## Evidence references

- `models/pandey_kumar_mode1/40_method_b_corrected_propagation_14k/evidence_1412465/corrected_method_b_evaluation.json`

- `results/pandey_kumar_mode1/master_fracture_curves/curve_standard_1398090.csv`

- `models/pandey_kumar_mode1/40_method_b_corrected_propagation_14k/evidence_1412465/corrected_method_b_load_displacement.csv`

- `runs/mode1/method_b_inf_companion/inf_companion_method_b_results.json`

- `models/pandey_kumar_mode1/method_b_preflight_manifest.json`

- `docs/decisions/SUPERVISOR_DECISION_METHOD_B_MODE1_LOAD_PARTITIONING.md`

- `models/pandey_kumar_mode1/method_b_inf_companion_decks/M1_MB_INF_1S.inp`

- `models/pandey_kumar_mode1/method_b_inf_companion_decks/M1_MB_INF_2S.inp`

- `models/pandey_kumar_mode1/method_b_inf_companion_decks/M1_MB_INF_4S.inp`

- `runs/mode1/method_b_inf_companion/01_pre_1s/submit_M1_PRE_INF_1S.pbs`

- `runs/mode1/method_b_inf_companion/02_pre_2s/submit_M1_PRE_INF_2S.pbs`

- `runs/mode1/method_b_inf_companion/03_pre_4s/submit_M1_PRE_INF_4S.pbs`

- `docs/reports/MODE1_METHOD_C_CONTINUATION_ARCHITECTURE_VALIDATION.md`

- `docs/reports/MODE1_METHOD_C_EXPERIMENTAL_PREFLIGHT_AND_GATE_6C_READINESS.md`

- `docs/reports/MODE1_METHOD_C1_CONTINUATION_FEASIBILITY_AND_PLAN.md`

- `docs/reports/MODE1_METHOD_B_EVIDENCE_AUDIT_AND_SUPERVISOR_DECISION_PACKAGE.md`

- `docs/reports/MODE1_METHOD_B_SCIENTIFIC_VALIDATION_AND_ADAPTIVE_LIMITATION_REPORT.md`

- `models/pandey_kumar_mode1/experimental_offset_uel/evidence_f1575/F1575_SAME_MESH_CONTINUATION_RESOLUTION.json`

- `results/validation/mesh_convergence_prototype.json`

- `results/validation/mode1_f1597/correction_prototype.json`

- Figure classes and hashes: [FIGURE_SOURCES.md](FIGURE_SOURCES.md).
