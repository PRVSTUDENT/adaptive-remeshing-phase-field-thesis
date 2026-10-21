# Figure sources and evidence boundaries

Authentic solver outputs, input geometry, offline diagnostics and conceptual figures are separate evidence classes. Actual mesh images come from input connectivity. Conceptual meshes do not represent completed cycles.

## Nomenclature used in this report

Method C1 is the planned sequential forward-refinement strategy. Method C2 is the planned sequential refinement with selective wake-coarsening extension. Neither is qualified. CB-2300 is the report-only alias of the separate historical Candidate C2 crack-band receiver test mesh (2,300 quads). The 840-element intermediate receiver is also not the Method C1 strategy. Original files, identifiers and checkpoints are unchanged. Stable report figure filenames containing candidate_c1_c2 or candidate_c2 refer to those original test artifacts, not to the planned strategies. No external illustrative images from the pasted request are used.

## method_b_workflow.png

**Placement: Main report Figure 1.**

**Type: CONCEPTUAL method explanation.** A and B share one-remesh/two-pass architecture. B parameterizes preliminary loading and field selection; it is not sequential adaptation. The 1-step B case reduces to the same architecture as A at the same controls.

Output SHA-256: `fc7256b5bd54bc632c002d1b0e3f81247132b24f7a918fa336a830946769d5d5`

- `docs/decisions/SUPERVISOR_DECISION_METHOD_B_MODE1_LOAD_PARTITIONING.md` | SHA-256 `229a13bc06882549df179be781820a7afa9e116ef75a7f655ef72e0f33274c8e`

- `docs/methods/MODE1_LOAD_PARTITION_EXPERIMENT_SPECIFICATION.md` | SHA-256 `b5273f0ee7091f61c76f180a2c66940b153fab3ff9389c6e39bf1265570a37f2`

## mesh_artifacts.png

**Placement: Main report Figure 2.**

**Type: AUTHENTIC input-deck geometry.** Coarse mesh, automatically generated native Method B mesh (14,677 FE) and native tip zoom, alongside partition invariance. No retrospective verification mesh is included. This native mesh did not produce the corrected fracture-response curve on page 3.

Output SHA-256: `616a9f6edb40a58b2346f298b19ac76723113cd7ff3bd2ebb1890ad63bd19560`

- `models/pandey_kumar_mode1/method_b_preflight_decks/M1-MB-1S.inp` | SHA-256 `060f4b810bc5e2b3d169a5b83f7694f86fe3ed5067c1a482fa2be64bdfefd1f0`

- `models/pandey_kumar_mode1/38_method_b_native_final_14k/M1_MB_NATIVE_FINAL_1S.inp` | SHA-256 `39cfd486c87a48a72f145919998e4fe698367dda452b0f20c2e8f43ea13b0a6d`

- `runs/mode1/method_b_inf_companion/inf_companion_method_b_results.json` | SHA-256 `79dbb197ef76786c3c130ceb1628ba46757dbf4422cb72e5d1d6aa1978d7fd99`

## method_b_loading_schedules.png

**Placement: Main report Figure 3.**

**Type: VERIFIED DECK-DERIVED diagram, not measured solver history.** Prescribed RP-U2 ramps reconstructed by parsing actual infinitesimal-companion execution decks. Each step duration is 1; accumulated step-times total 1, 2 and 4. End displacements are absolute BC values, not increments to add. Equal displacement partitions are verified, not assumed. Field output is every increment; remesh selection is the last frame of Step-1/2/4 at u=0.005 mm. Increment labels 500/250/125 follow deck time controls and archived zero-cutback completion. Remeshing occurs once after selection. Static pseudo-time is not walltime. Manifest supplies selection rule; archived result supplies endpoint/field comparison; no ODB is opened or new solver execution claimed.

Output SHA-256: `91d027faa05ceaf2e6003580db044482a37236e420f974412df32b85390b3293`

- `models/pandey_kumar_mode1/method_b_inf_companion_decks/M1_MB_INF_1S.inp` | SHA-256 `927c159b5879a0f0db9e6e123cd01b90fc819481818b9971bbf9702751ba0a08`

- `models/pandey_kumar_mode1/method_b_inf_companion_decks/M1_MB_INF_2S.inp` | SHA-256 `eaed20ac43d48b2e1b8540293b30ae27bc88e792d1bfdc1a491d0bc016878403`

- `models/pandey_kumar_mode1/method_b_inf_companion_decks/M1_MB_INF_4S.inp` | SHA-256 `2169db8436542b8dd4a76829c2c2755a6316a5cb17339c32f695da58e67a569f`

- `runs/mode1/method_b_inf_companion/01_pre_1s/submit_M1_PRE_INF_1S.pbs` | SHA-256 `a4a406028c36751743123067d9529fcf2ba200bc4c802466d910528927aaf6ce`

- `runs/mode1/method_b_inf_companion/02_pre_2s/submit_M1_PRE_INF_2S.pbs` | SHA-256 `209af42bcd144cc4b29bb25d371d8c61b6385a4fe997c72553817d9622b26917`

- `runs/mode1/method_b_inf_companion/03_pre_4s/submit_M1_PRE_INF_4S.pbs` | SHA-256 `1d12c0d29ef961c03931a0d29c343bc6963046636b11bb64b69013f508618a2c`

- `models/pandey_kumar_mode1/method_b_preflight_manifest.json` | SHA-256 `c297600517ffadba3778f0a8f8fb5ad599aaad9ef4e03481e5641727d85abe5a`

- `runs/mode1/method_b_inf_companion/inf_companion_method_b_results.json` | SHA-256 `79dbb197ef76786c3c130ceb1628ba46757dbf4422cb72e5d1d6aa1978d7fd99`

- `docs/decisions/SUPERVISOR_DECISION_METHOD_B_MODE1_LOAD_PARTITIONING.md` | SHA-256 `229a13bc06882549df179be781820a7afa9e116ef75a7f655ef72e0f33274c8e`

## corrected_verification_mesh.png

**Placement: Main report Figure 4.**

**Type: AUTHENTIC input-deck geometry.** Page 3 corrected verification geometry. The 14,483-element mesh and its tip zoom are paired with the fracture-response evaluation of job 1412465. Retrospective ligament refinement used knowledge of the crack path; it is separate from the native 14,677-element partition result and not caused by partition count.

Output SHA-256: `75ab2e3eb3ae465879ec6628136c17951c63cb7374c6bc583cd5842195057fdb`

- `models/pandey_kumar_mode1/40_method_b_corrected_propagation_14k/M1_MB_CORRECTED_PROPAGATION_14K.inp` | SHA-256 `1209f716971719b1a740ff92c8b5503ba9784f10d5eedd3c5035c81d40a066e9`

- `models/pandey_kumar_mode1/40_method_b_corrected_propagation_14k/evidence_1412465/corrected_method_b_evaluation.json` | SHA-256 `8820553ccf3db5c3b41743e0553d3be4f25a3c68e027a628ba4e479b932f11f1`

## method_b_response.png

**Placement: Main report Figure 5.**

**Type: AUTHENTIC simulation outputs.** Only corrected Method B and canonical fixed reference. Both end at 0.007889 mm. Reference endpoint is interpolated within its recorded range, not extrapolated. Work uses trapezoidal integration of kN versus mm multiplied by 1000 to mJ. Zero is at the first recorded row, u=0.0000025 mm, matching the established evaluation convention. Reintegrated work: 2.267379222 versus 2.358731686 mJ (-3.87295%). Prior summary reference 2.3586 mJ differs by about 0.0001 mJ; the CSV value rounds to 2.3587 mJ.

Output SHA-256: `2fb72c5cb9c2c58a2bc7d5c36c07cac0f2ec302351379c73982171e92cf5becc`

- `results/pandey_kumar_mode1/master_fracture_curves/curve_standard_1398090.csv` | SHA-256 `780d05d39532e778802cdd8503cdd0df25568e412c3d4a51c50f4e001febede6`

- `models/pandey_kumar_mode1/40_method_b_corrected_propagation_14k/evidence_1412465/corrected_method_b_load_displacement.csv` | SHA-256 `dc1ed0877b6e94c6fb1fc318927a67554c6cf970de042a60567362f72e81a1d9`

- `models/pandey_kumar_mode1/40_method_b_corrected_propagation_14k/evidence_1412465/corrected_method_b_evaluation.json` | SHA-256 `8820553ccf3db5c3b41743e0553d3be4f25a3c68e027a628ba4e479b932f11f1`

## method_c_planned_workflow.png

**Placement: Main report Figure 6.**

**Type: CONCEPTUAL C1/C2 strategy comparison and future mesh progression.** Side-by-side Step 0 plus four proposed cycles for Method C1 (accumulating forward refinement) and Method C2 (moving active fine zone with conditional selective coarsening). Every strip and crack position is conceptual. The blue damaged corridor stays protected; amber regions illustrate potential coarsening outside it, not blanket coarsening of damaged wake or a qualified rule. No physical dimensions, counts, measured savings, cycle displacements or accepted solver trajectory are implied. Both strategies remain unqualified; coarsening is an additional proposed extension after a physically accepted refinement handoff.

Output SHA-256: `fd48a695e98d2e434c94b84c609ebd44d70ecda4ba41d6fa3566f0830447fb3f`

- `docs/reports/MODE1_METHOD_C_CONTINUATION_ARCHITECTURE_VALIDATION.md` | SHA-256 `fbbdfb147fd61b2b21717c02a465e473e169527625cede952b40720bef9ae263`

- `docs/reports/MODE1_METHOD_C_EXPERIMENTAL_PREFLIGHT_AND_GATE_6C_READINESS.md` | SHA-256 `624cf82a8e2bfb7a89d42eb7e90ba77fc7ce6d5bbdfaa21c82f9ba20778aacc4`

- `docs/reports/MODE1_METHOD_C1_CONTINUATION_FEASIBILITY_AND_PLAN.md` | SHA-256 `b018b5868faeb3832a5a689498963dc58ba54ab3e575f02608c98f9f812e323d`

## candidate_c1_c2_meshes.png

**Placement: Preserved companion research image; excluded from main report.**

**Type: AUTHENTIC input-deck geometry.** Actual intermediate 840-element receiver and crack-band receiver test mesh CB-2300 (formerly Candidate C2), with common-scale tip close-ups. Both are offline test meshes, not Method C1/C2 strategies. Slit y=0.050 mm ends at x=0.040 mm; dark line/dot mark input geometry, not a simulated evolving crack. Original input filenames and scientific identifiers are unchanged.

Output SHA-256: `0ca6cbc9a6fc2221dc056ac01e0dac885f54e82ef7739f931338cbfb6c2138ce`

- `models/pandey_kumar_mode1/candidate_intermediate_mesh_c1.inp` | SHA-256 `527d352a359a899d4024392873a1377cf8b27fa11c3097432b30879ba1a133a6`

- `models/pandey_kumar_mode1/candidate_crack_band_mesh_c2.inp` | SHA-256 `257fc6263d63721bdeefe48a43cd504c79a92df61c099ce9481984b625454901`

- `scripts/remeshing/generate_crack_band_mesh.py` | SHA-256 `2cea823585d0b208e77f865de90ad1fe3d96a8b2ea5f336c1756b60245810ca4`

- `scripts/validation/evaluate_candidate_meshes.py` | SHA-256 `330e441928f37b37f45f9f25b37857d1ffb778779899fbb6e507dfcfae9d859f`

## candidate_c2_passing_checks.png

**Placement: Preserved companion research image; excluded from main report.**

**Type: AUTHENTIC offline numerical diagnostics.** Passing undamaged elastic-stiffness and mapped fracture-energy checks of offline receiver meshes. CB-2300 is the report-only alias of historical Candidate C2, not the Method C2 coarsening strategy. These checks are not damaged-state compliance or solver continuation conservation. Force and healing failures are retained.

Output SHA-256: `01219a1b52215ba2ad613f8cb19190d06a39227b5027d776cf3b677742d63b06`

- `results/validation/mesh_convergence_prototype.json` | SHA-256 `a26f1ce1dd32a48f43e0d995f2f68b1658b034a289f8f232fa181486e591d814`

- `scripts/validation/evaluate_candidate_meshes.py` | SHA-256 `330e441928f37b37f45f9f25b37857d1ffb778779899fbb6e507dfcfae9d859f`

## native_crack_tip.png

**Placement: Preserved companion research image; excluded from main report.**

**Type: AUTHENTIC input-deck geometry.** Companion close-up of genuine native 14,677-FE Method B geometry. Separate from retrospective 14,483-FE verification mesh.

Output SHA-256: `718acdc49449f30bede8fc8323a4032adf0677514ffd18cc05124495e157e584`

- `models/pandey_kumar_mode1/38_method_b_native_final_14k/M1_MB_NATIVE_FINAL_1S.inp` | SHA-256 `39cfd486c87a48a72f145919998e4fe698367dda452b0f20c2e8f43ea13b0a6d`

## Numerical claim sources

- `models/pandey_kumar_mode1/40_method_b_corrected_propagation_14k/evidence_1412465/corrected_method_b_evaluation.json` | SHA-256 `8820553ccf3db5c3b41743e0553d3be4f25a3c68e027a628ba4e479b932f11f1`

- `results/pandey_kumar_mode1/master_fracture_curves/curve_standard_1398090.csv` | SHA-256 `780d05d39532e778802cdd8503cdd0df25568e412c3d4a51c50f4e001febede6`

- `models/pandey_kumar_mode1/40_method_b_corrected_propagation_14k/evidence_1412465/corrected_method_b_load_displacement.csv` | SHA-256 `dc1ed0877b6e94c6fb1fc318927a67554c6cf970de042a60567362f72e81a1d9`

- `runs/mode1/method_b_inf_companion/inf_companion_method_b_results.json` | SHA-256 `79dbb197ef76786c3c130ceb1628ba46757dbf4422cb72e5d1d6aa1978d7fd99`

- `models/pandey_kumar_mode1/method_b_preflight_manifest.json` | SHA-256 `c297600517ffadba3778f0a8f8fb5ad599aaad9ef4e03481e5641727d85abe5a`

- `docs/decisions/SUPERVISOR_DECISION_METHOD_B_MODE1_LOAD_PARTITIONING.md` | SHA-256 `229a13bc06882549df179be781820a7afa9e116ef75a7f655ef72e0f33274c8e`

- `models/pandey_kumar_mode1/method_b_inf_companion_decks/M1_MB_INF_1S.inp` | SHA-256 `927c159b5879a0f0db9e6e123cd01b90fc819481818b9971bbf9702751ba0a08`

- `models/pandey_kumar_mode1/method_b_inf_companion_decks/M1_MB_INF_2S.inp` | SHA-256 `eaed20ac43d48b2e1b8540293b30ae27bc88e792d1bfdc1a491d0bc016878403`

- `models/pandey_kumar_mode1/method_b_inf_companion_decks/M1_MB_INF_4S.inp` | SHA-256 `2169db8436542b8dd4a76829c2c2755a6316a5cb17339c32f695da58e67a569f`

- `runs/mode1/method_b_inf_companion/01_pre_1s/submit_M1_PRE_INF_1S.pbs` | SHA-256 `a4a406028c36751743123067d9529fcf2ba200bc4c802466d910528927aaf6ce`

- `runs/mode1/method_b_inf_companion/02_pre_2s/submit_M1_PRE_INF_2S.pbs` | SHA-256 `209af42bcd144cc4b29bb25d371d8c61b6385a4fe997c72553817d9622b26917`

- `runs/mode1/method_b_inf_companion/03_pre_4s/submit_M1_PRE_INF_4S.pbs` | SHA-256 `1d12c0d29ef961c03931a0d29c343bc6963046636b11bb64b69013f508618a2c`

- `docs/reports/MODE1_METHOD_C_CONTINUATION_ARCHITECTURE_VALIDATION.md` | SHA-256 `fbbdfb147fd61b2b21717c02a465e473e169527625cede952b40720bef9ae263`

- `docs/reports/MODE1_METHOD_C_EXPERIMENTAL_PREFLIGHT_AND_GATE_6C_READINESS.md` | SHA-256 `624cf82a8e2bfb7a89d42eb7e90ba77fc7ce6d5bbdfaa21c82f9ba20778aacc4`

- `docs/reports/MODE1_METHOD_C1_CONTINUATION_FEASIBILITY_AND_PLAN.md` | SHA-256 `b018b5868faeb3832a5a689498963dc58ba54ab3e575f02608c98f9f812e323d`

- `docs/reports/MODE1_METHOD_B_EVIDENCE_AUDIT_AND_SUPERVISOR_DECISION_PACKAGE.md` | SHA-256 `d5d7a5daf2c63d94581e3dc1a67989438f8dbf155bdb51c09fbe89f09fb8cb47`

- `docs/reports/MODE1_METHOD_B_SCIENTIFIC_VALIDATION_AND_ADAPTIVE_LIMITATION_REPORT.md` | SHA-256 `3926101e2b661d8ce4ab6e4e6ff03a33852a629961a9ddaf5311ca8f44ea4eee`

- `models/pandey_kumar_mode1/experimental_offset_uel/evidence_f1575/F1575_SAME_MESH_CONTINUATION_RESOLUTION.json` | SHA-256 `3ffcd33f1c0213dc281033af2cd77983ebcdc8a8d3633587b7bcc8638ce926fb`

- `models/pandey_kumar_mode1/72_method_c_coupled_state_transfer/PACKAGE72_STATE_TRANSFER_AUDIT.json` | SHA-256 `05047da6e223c58834ac775dc492bc2f3ab2bd93551f37e01a950049680ffa82`

## Verified schedule and field selection

The build parses the actually executed M1_MB_INF_1S/2S/4S decks, verifies their input filenames against PBS wrappers, reads *STATIC and absolute N_RP U2 boundary values, and verifies MISESERI output every increment. No amplitude override is present. The preflight manifest specifies LAST_INCREMENT of Step-1/2/4; its endpoint matches the executed deck and archived result. Decision record Section 8.6 reports 500 total increments and zero cutbacks per case, supporting terminal increment labels 500/250/125. These are step-local increments, not guessed global ODB frame indices. The build does not reopen the historical ODBs or recompute absent cross-partition arrays. Mesh/field identity is the archived verified observation, not a new three-ODB comparison.

- 1S: total static step-time 1; select Step-1 last frame (step-local increment 500); one remesh after the pre-analysis.

  - Step-1: time 0 to 1; prescribed U2 0.000000 to 0.005000 mm; initial/max dt=0.002000; 500 nominal increments; field frequency=1.

- 2S: total static step-time 2; select Step-2 last frame (step-local increment 250); one remesh after the pre-analysis.

  - Step-1: time 0 to 1; prescribed U2 0.000000 to 0.002500 mm; initial/max dt=0.004000; 250 nominal increments; field frequency=1.

  - Step-2: time 1 to 2; prescribed U2 0.002500 to 0.005000 mm; initial/max dt=0.004000; 250 nominal increments; field frequency=1.

- 4S: total static step-time 4; select Step-4 last frame (step-local increment 125); one remesh after the pre-analysis.

  - Step-1: time 0 to 1; prescribed U2 0.000000 to 0.001250 mm; initial/max dt=0.008000; 125 nominal increments; field frequency=1.

  - Step-2: time 1 to 2; prescribed U2 0.001250 to 0.002500 mm; initial/max dt=0.008000; 125 nominal increments; field frequency=1.

  - Step-3: time 2 to 3; prescribed U2 0.002500 to 0.003750 mm; initial/max dt=0.008000; 125 nominal increments; field frequency=1.

  - Step-4: time 3 to 4; prescribed U2 0.003750 to 0.005000 mm; initial/max dt=0.008000; 125 nominal increments; field frequency=1.

## Rebuild and scope

Run `python docs/supervisor_reports/22-10-2026/build_successful_results_report.py`. No solver, scheduler or controller execution. Stable output names are reused; native_crack_tip.png is a companion genuine native 14,677-element mesh close-up. CB-2300 receiver/subcheck images and native_crack_tip.png are preserved companion images, not embedded in the four-page presentation. Main report figures are numbered automatically by appearance, 1 through 6.

## Comparison convention

Both response curves are cropped to 0.007889 mm without extrapolation. The reference has authentic later records to 0.010 mm, excluded here. The corrected 14,483-element study does not complete 0.010 mm. kN-mm work is converted to mJ with factor 1000. Partition invariance (native 14,677 FE) and retrospective ligament resolution (14,483 FE) are separate findings; no fracture-response advantage is attributed to loading partition count.
