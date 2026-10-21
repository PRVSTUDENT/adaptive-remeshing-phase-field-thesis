# Figure sources and evidence boundaries

Authentic solver outputs, input geometry, offline diagnostics and conceptual figures are separate evidence classes. Actual mesh images come from input connectivity. Conceptual meshes do not represent completed cycles.

## method_b_response.png

**Type: AUTHENTIC simulation outputs.** Figure 1. Only corrected Method B and canonical fixed reference. Both end at 0.007889 mm. Reference endpoint is interpolated within its recorded range, not extrapolated. Work uses trapezoidal integration of kN versus mm multiplied by 1000 to mJ. Zero is at the first recorded row, u=0.0000025 mm, matching the established evaluation convention. Reintegrated work: 2.267379222 versus 2.358731686 mJ (-3.87295%). Prior summary reference 2.3586 mJ differs by about 0.0001 mJ; the CSV value rounds to 2.3587 mJ.

Output SHA-256: `2fb72c5cb9c2c58a2bc7d5c36c07cac0f2ec302351379c73982171e92cf5becc`

- `results/pandey_kumar_mode1/master_fracture_curves/curve_standard_1398090.csv` | SHA-256 `780d05d39532e778802cdd8503cdd0df25568e412c3d4a51c50f4e001febede6`

- `models/pandey_kumar_mode1/40_method_b_corrected_propagation_14k/evidence_1412465/corrected_method_b_load_displacement.csv` | SHA-256 `dc1ed0877b6e94c6fb1fc318927a67554c6cf970de042a60567362f72e81a1d9`

- `models/pandey_kumar_mode1/40_method_b_corrected_propagation_14k/evidence_1412465/corrected_method_b_evaluation.json` | SHA-256 `8820553ccf3db5c3b41743e0553d3be4f25a3c68e027a628ba4e479b932f11f1`

## method_b_workflow.png

**Type: CONCEPTUAL method explanation.** Method B schematic, not solver imagery. Fresh refined-mesh solve without state transfer. The corrected configuration uses retrospective ligament information; this does not establish fully predictive native automatic crack tracking.

Output SHA-256: `c3a98434faa3dda65de7738f77cd9d13b80e55c15d7571b1facc9b7f203b4dac`

- `docs/reports/MODE1_METHOD_B_SCIENTIFIC_VALIDATION_AND_ADAPTIVE_LIMITATION_REPORT.md` | SHA-256 `3926101e2b661d8ce4ab6e4e6ff03a33852a629961a9ddaf5311ca8f44ea4eee`

- `models/pandey_kumar_mode1/40_method_b_corrected_propagation_14k/evidence_1412465/corrected_method_b_evaluation.json` | SHA-256 `8820553ccf3db5c3b41743e0553d3be4f25a3c68e027a628ba4e479b932f11f1`

## mesh_artifacts.png

**Type: AUTHENTIC input-deck geometry.** Figure 2. Coarse pre-analysis and final corrected Method B mesh with actual tip zoom. Before/after includes retrospective ligament refinement, not a purely automatic native remesh transition or loaded state-preserving handoff.

Output SHA-256: `52a85cfb3b61ab20693a92000cef6ab277330a0323d558c1bd164d8e6002e905`

- `models/pandey_kumar_mode1/method_b_preflight_decks/M1-MB-1S.inp` | SHA-256 `060f4b810bc5e2b3d169a5b83f7694f86fe3ed5067c1a482fa2be64bdfefd1f0`

- `models/pandey_kumar_mode1/40_method_b_corrected_propagation_14k/M1_MB_CORRECTED_PROPAGATION_14K.inp` | SHA-256 `1209f716971719b1a740ff92c8b5503ba9784f10d5eedd3c5035c81d40a066e9`

## native_crack_tip.png

**Type: AUTHENTIC input-deck geometry.** Companion close-up of corrected 14,483-FE configuration; filename retained. Not evidence for predictive native crack tracking.

Output SHA-256: `9f7a83fc292c515a7e1cb008f59c2ea40f724a3f398726133276c50d61c4563d`

- `models/pandey_kumar_mode1/40_method_b_corrected_propagation_14k/M1_MB_CORRECTED_PROPAGATION_14K.inp` | SHA-256 `1209f716971719b1a740ff92c8b5503ba9784f10d5eedd3c5035c81d40a066e9`

## method_c_planned_workflow.png

**Type: CONCEPTUAL intended workflow and mesh progression.** Figure 3. User-requested target of Step 0 plus four future cycles. All five meshes, refinement boxes and crack positions are conceptual. No accepted multi-mesh trajectory or cycle displacement is asserted. No wake coarsening is represented.

Output SHA-256: `593c07382415da05c9f6c80d380355fd5d0400dcb13bca5fd497b59c4dfd79cb`

- `docs/reports/MODE1_METHOD_C1_CONTINUATION_FEASIBILITY_AND_PLAN.md` | SHA-256 `b018b5868faeb3832a5a689498963dc58ba54ab3e575f02608c98f9f812e323d`

## candidate_c1_c2_meshes.png

**Type: AUTHENTIC input-deck geometry.** Figure 4. Actual C1/C2 receiver geometries with common-scale tip close-ups. The slit is y=0.050 mm, ending at x=0.040 mm as defined in the mesh generator and evaluator; dark line/dot identify this geometry, not a simulated evolving crack. Coordinates in mm. Distinct transfer-test candidates, not successive full-plate Method C cycles.

Output SHA-256: `0d63e70a5b8fd4d1d868498d9d59cd6264948d37c17396ae733ec6547b54eb5b`

- `models/pandey_kumar_mode1/candidate_intermediate_mesh_c1.inp` | SHA-256 `527d352a359a899d4024392873a1377cf8b27fa11c3097432b30879ba1a133a6`

- `models/pandey_kumar_mode1/candidate_crack_band_mesh_c2.inp` | SHA-256 `257fc6263d63721bdeefe48a43cd504c79a92df61c099ce9481984b625454901`

- `scripts/remeshing/generate_crack_band_mesh.py` | SHA-256 `2cea823585d0b208e77f865de90ad1fe3d96a8b2ea5f336c1756b60245810ca4`

- `scripts/validation/evaluate_candidate_meshes.py` | SHA-256 `330e441928f37b37f45f9f25b37857d1ffb778779899fbb6e507dfcfae9d859f`

## candidate_c2_passing_checks.png

**Type: AUTHENTIC offline numerical diagnostics.** Figure 5. Passing undamaged elastic-stiffness and mapped fracture-energy checks. Not damaged-state compliance or solver continuation conservation. C2 healing and force-continuity failures are retained in report text.

Output SHA-256: `033bb575dd628e1ee44deb82b612ab1163667abc23f884a4de37651be08cc292`

- `results/validation/mesh_convergence_prototype.json` | SHA-256 `a26f1ce1dd32a48f43e0d995f2f68b1658b034a289f8f232fa181486e591d814`

- `scripts/validation/evaluate_candidate_meshes.py` | SHA-256 `330e441928f37b37f45f9f25b37857d1ffb778779899fbb6e507dfcfae9d859f`

## Numerical claim sources

- `models/pandey_kumar_mode1/40_method_b_corrected_propagation_14k/evidence_1412465/corrected_method_b_evaluation.json` | SHA-256 `8820553ccf3db5c3b41743e0553d3be4f25a3c68e027a628ba4e479b932f11f1`

- `results/pandey_kumar_mode1/master_fracture_curves/curve_standard_1398090.csv` | SHA-256 `780d05d39532e778802cdd8503cdd0df25568e412c3d4a51c50f4e001febede6`

- `models/pandey_kumar_mode1/40_method_b_corrected_propagation_14k/evidence_1412465/corrected_method_b_load_displacement.csv` | SHA-256 `dc1ed0877b6e94c6fb1fc318927a67554c6cf970de042a60567362f72e81a1d9`

- `docs/reports/MODE1_METHOD_B_EVIDENCE_AUDIT_AND_SUPERVISOR_DECISION_PACKAGE.md` | SHA-256 `d5d7a5daf2c63d94581e3dc1a67989438f8dbf155bdb51c09fbe89f09fb8cb47`

- `docs/reports/MODE1_METHOD_B_SCIENTIFIC_VALIDATION_AND_ADAPTIVE_LIMITATION_REPORT.md` | SHA-256 `3926101e2b661d8ce4ab6e4e6ff03a33852a629961a9ddaf5311ca8f44ea4eee`

- `models/pandey_kumar_mode1/experimental_offset_uel/evidence_f1575/F1575_SAME_MESH_CONTINUATION_RESOLUTION.json` | SHA-256 `3ffcd33f1c0213dc281033af2cd77983ebcdc8a8d3633587b7bcc8638ce926fb`

- `results/validation/mesh_convergence_prototype.json` | SHA-256 `a26f1ce1dd32a48f43e0d995f2f68b1658b034a289f8f232fa181486e591d814`

- `results/validation/mode1_f1597/correction_prototype.json` | SHA-256 `617bcd8f31c3752871c206b5416b386e7e59dda3a0275ea265fa18a551b2faef`

## Rebuild and scope

Run `python docs/supervisor_reports/22-10-2026/build_successful_results_report.py`. No solver, scheduler or controller execution. Stable output names are reused; native_crack_tip.png is a companion corrected-mesh close-up. All other generated figures are embedded.

## Comparison convention

Both curves are cropped to 0.007889 mm without extrapolation. The reference has authentic later records to 0.010 mm, excluded here. Corrected Method B does not complete 0.010 mm. kN-mm work is converted to mJ with factor 1000. Retrospective ligament refinement is not equated with fully predictive native automatic refinement.
