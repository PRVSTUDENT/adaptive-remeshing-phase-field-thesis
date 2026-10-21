# Mode-I adaptive remeshing: validated results

Technical progress report | 22 October 2026

## 1. Method A and Method B: what changes?

Method A: one preliminary simulation, one native adaptive remesh, then a fresh final simulation from zero load. Method B extends that same two-pass approach by partitioning preliminary loading into configurable 1, 2 or 4 steps and selecting/evaluating the relevant MISESERI field before one remesh and a fresh final solve.

B varies the loading schedule and field-selection opportunities. It does not preserve a loaded fracture state across meshes or perform multiple remeshing cycles. With one step and the same controls, its architecture reduces to Method A.

![Conceptual A/B workflow. The shared architecture has two simulation passes and exactly one remesh; only the pre-analysis schedule and field-selection flexibility differ.](figures/method_b_workflow.png)

Conceptual A/B workflow. The shared architecture has two simulation passes and exactly one remesh; only the pre-analysis schedule and field-selection flexibility differ.

![Figure 2. Authentic coarse mesh, genuine native 14,677-element Method B mesh and tip zoom, and separate retrospectively refined 14,483-element verification mesh. Partition choice did not produce the latter correction.](figures/mesh_artifacts.png)

Figure 2. Authentic coarse mesh, genuine native 14,677-element Method B mesh and tip zoom, and separate retrospectively refined 14,483-element verification mesh. Partition choice did not produce the latter correction.

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

# 4. Method C: intended sequential adaptation

Method C aims to retain the current fracture state while changing the mesh. The target is four genuine adaptive remeshing cycles, with refinement following the active crack-tip/process-zone region rather than a preselected full propagation ligament.

![Figure 4. Conceptual Step 0 plus four intended remeshing cycles. Every panel is illustrative: no authentic four-cycle solver trajectory has yet been qualified.](figures/method_c_planned_workflow.png)

Figure 4. Conceptual Step 0 plus four intended remeshing cycles. Every panel is illustrative: no authentic four-cycle solver trajectory has yet been qualified.

## Intended sequence: Step 0 and cycles 1-4

Step 0: solve on the coarse mesh and monitor damage and the error indicator. Cycle 1: at a chosen remeshing point, extract displacement, damage and committed history; remesh around the active region; transfer and re-equilibrate; continue loading. Cycles 2, 3 and 4 repeat that sequence from the newly continued solution. Remeshing points must be selected and validated; no cycle displacements are claimed here.

| Building block | Achieved evidence | Remaining target |
| --- | --- | --- |
| Native mesh generation | Authentic refined input meshes | Adapt repeatedly to evolving crack |
| Same-mesh continuation | -0.0264% endpoint force error | Preserve state on a new mesh |
| Nonmatching transfer | Offline components evaluated | Force/energy continuity; no healing |
| Sequential loading cycles | No qualified complete cycle | Four accepted remesh/continue cycles |

## Successful continuation control and current boundary

The experimental same-mesh control reaches 5.2881993 N versus 5.2895973 N at u=0.00270 mm with the guarded predictor: -0.0264% endpoint difference. This is endpoint agreement for a specific same-mesh control, not whole-trajectory or nonmatching-transfer equivalence.

Nonmatching transfer remains unqualified because force continuity, energy and pointwise damage irreversibility must all survive re-equilibration. Separate mesh-generation and continuation controls do not yet form a validated multi-cycle solution. Candidate C2 isolates the current limitation below.

# 5. Method C - Candidate C2: Crack-Band-Resolved Receiver Mesh

Candidate C2 is a small receiver mesh developed for Method C: 2,300 quadrilateral elements, 2,413 physical nodes and 0.001 mm crack-band element size. Its minimum Jacobian is positive (3.125e-7). C1 is a separate intermediate candidate.

![Figure 5. Authentic C1/C2 receiver geometries and common-scale crack-tip close-ups. These are separate offline transfer candidates, not successive remeshing cycles.](figures/candidate_c1_c2_meshes.png)

Figure 5. Authentic C1/C2 receiver geometries and common-scale crack-tip close-ups. These are separate offline transfer candidates, not successive remeshing cycles.

![Figure 6. Authentic passing offline checks: C2 elastic stiffness error 4.58% (limit 5%) and mapped fracture-energy error +0.79% (limit 2%). These do not qualify loaded continuation.](figures/candidate_c2_passing_checks.png)

Figure 6. Authentic passing offline checks: C2 elastic stiffness error 4.58% (limit 5%) and mapped fracture-energy error +0.79% (limit 2%). These do not qualify loaded continuation.

## Remaining limitation: physical state continuity

C2 equilibrated force is 0.366 N versus donor 7.851 N (-95.34%, FAIL). The evaluated C2 prototype also reports maximum damage healing 0.0021837. Thus C2 is a successful mesh-generation and partial verification result, not qualified Method C continuation. Zero healing in the separate constrained 650-element prototype must not be attributed to C2.

## Scientific decision and immediate next work

Retain corrected Method B as the retrospectively refined baseline within 0.007889 mm. For Method C, prioritize one transfer hypothesis preserving the damaged profile and committed history under consistent boundary conditions. Check force, energy, residuals and irreversibility offline before a distinct qualified serial single-handoff test. Require physical acceptance before any four-cycle demonstration.

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

- `docs/reports/MODE1_METHOD_B_EVIDENCE_AUDIT_AND_SUPERVISOR_DECISION_PACKAGE.md`

- `docs/reports/MODE1_METHOD_B_SCIENTIFIC_VALIDATION_AND_ADAPTIVE_LIMITATION_REPORT.md`

- `models/pandey_kumar_mode1/experimental_offset_uel/evidence_f1575/F1575_SAME_MESH_CONTINUATION_RESOLUTION.json`

- `results/validation/mesh_convergence_prototype.json`

- `results/validation/mode1_f1597/correction_prototype.json`

- Figure classes and hashes: [FIGURE_SOURCES.md](FIGURE_SOURCES.md).
