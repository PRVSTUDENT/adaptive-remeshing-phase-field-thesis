# Figure sources and evidence boundaries

All authentic figures are derived from actual project artifacts. Input geometry and offline diagnostics are explicitly distinguished from solver outputs. No synthetic fracture result is used.

## method_b_response.png

Type: **AUTHENTIC simulation outputs**. Replotted recorded force histories and trapezoidal external work; no extrapolation beyond recorded endpoints. Reference is truncated at its available horizon. Corrected run also has a finite recorded horizon; no full-horizon completion claim.

Output SHA-256: `e396810a382c38f8b478b1ff2bab665b338014c0e4e29505f32b916da084a2c6`

- `results/pandey_kumar_mode1/master_fracture_curves/curve_standard_1398090.csv` | SHA-256 `780d05d39532e778802cdd8503cdd0df25568e412c3d4a51c50f4e001febede6`

- `runs/mode1/harvest_results_f1416/m1_mb_native_14k_1s_load_displacement.csv` | SHA-256 `1d9d4948a5c4075c1ecd93dd3e24724a28ad7ead4285f2276b4b008ec3623bc0`

- `models/pandey_kumar_mode1/40_method_b_corrected_propagation_14k/evidence_1412465/corrected_method_b_load_displacement.csv` | SHA-256 `dc1ed0877b6e94c6fb1fc318927a67554c6cf970de042a60567362f72e81a1d9`

## mesh_artifacts.png

Type: **AUTHENTIC input-deck geometry**. Actual mesh geometry. Candidate C2 is a separate small transfer-test mesh, not a later accepted full-plate cycle or a solver result.

Output SHA-256: `73528a24b49222b695835fb75bf2a44d531a11e7c351cf8f865994cc3fc6757a`

- `models/pandey_kumar_mode1/method_b_preflight_decks/M1-MB-1S.inp` | SHA-256 `060f4b810bc5e2b3d169a5b83f7694f86fe3ed5067c1a482fa2be64bdfefd1f0`

- `models/pandey_kumar_mode1/38_method_b_native_final_14k/M1_MB_NATIVE_FINAL_1S.inp` | SHA-256 `39cfd486c87a48a72f145919998e4fe698367dda452b0f20c2e8f43ea13b0a6d`

- `models/pandey_kumar_mode1/candidate_crack_band_mesh_c2.inp` | SHA-256 `257fc6263d63721bdeefe48a43cd504c79a92df61c099ce9481984b625454901`

## candidate_c1_c2_meshes.png

Type: **AUTHENTIC input-deck geometry**. Full receiver meshes and common-scale crack-tip close-ups. Offline geometry, not solver-evolved sequential stages.

Output SHA-256: `dc82c43c14f31a8bf19d8467bad9a109a2c6366ed786b78093151061940991eb`

- `models/pandey_kumar_mode1/candidate_intermediate_mesh_c1.inp` | SHA-256 `527d352a359a899d4024392873a1377cf8b27fa11c3097432b30879ba1a133a6`

- `models/pandey_kumar_mode1/candidate_crack_band_mesh_c2.inp` | SHA-256 `257fc6263d63721bdeefe48a43cd504c79a92df61c099ce9481984b625454901`

## native_crack_tip.png

Type: **AUTHENTIC input-deck geometry**. Existing native adapted crack-tip zoom, copied unchanged.

Output SHA-256: `007744b89ad094b7612dcad94fd9196c4c6506500ec0c49d2f5d24e638096d8a`

- `results/figures/mode1_method_b_mesh/fig_mode1_method_b_native_crack_tip_zoom.png` | SHA-256 `007744b89ad094b7612dcad94fd9196c4c6506500ec0c49d2f5d24e638096d8a`

- `models/pandey_kumar_mode1/38_method_b_native_final_14k/M1_MB_NATIVE_FINAL_1S.inp` | SHA-256 `39cfd486c87a48a72f145919998e4fe698367dda452b0f20c2e8f43ea13b0a6d`

- `scripts/visualization/plot_mode1_method_b_adaptive_mesh.py` | SHA-256 `809eebca1d0256af3a08d2ea2f8c041c0626e6c43ac79ba8100ea3e587a6a423`

## method_c_planned_workflow.png

Type: **CONCEPTUAL planned workflow**. Reporting schematic. Achieved-versus-planned comparison is evidence status, not simulated mesh evolution.

Output SHA-256: `73dbfd05f9b5aff6f0207dcbc86b732f5004e1e21e1652b1597056f816299081`

- `docs/reports/MODE1_METHOD_C1_CONTINUATION_FEASIBILITY_AND_PLAN.md` | SHA-256 `b018b5868faeb3832a5a689498963dc58ba54ab3e575f02608c98f9f812e323d`

- `project_coordination/ACTIVE_TASK.json` | SHA-256 `4c0ae0d0470d0152dbe145bcb1e5ed0abdc4897d6644f163e9f6015c3fb8c9f1`

## candidate_c2_passing_checks.png

Type: **AUTHENTIC offline numerical diagnostics**. Selected passing subchecks. Stiffness is undamaged elastic stiffness, not damaged-state compliance. Energy is mapped-state quadrature, not conservation after solver equilibration.

Output SHA-256: `474f222f4d2152487ea18163a5b500d27015590a0210a97399b1ffdcdceea070`

- `results/validation/mesh_convergence_prototype.json` | SHA-256 `a26f1ce1dd32a48f43e0d995f2f68b1658b034a289f8f232fa181486e591d814`

- `scripts/validation/evaluate_candidate_meshes.py` | SHA-256 `330e441928f37b37f45f9f25b37857d1ffb778779899fbb6e507dfcfae9d859f`

## Rebuild

Run `python docs/supervisor_reports/22-10-2026/build_successful_results_report.py`. This renders existing evidence only and submits no jobs.

## Background reference

The prior 8 October report_main.pdf was checked as a 10-page style/context reference; none of its historical figures was relabeled as new work.