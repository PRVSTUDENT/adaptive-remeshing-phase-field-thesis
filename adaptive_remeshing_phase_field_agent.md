# Name: Adaptive Remeshing Phase-Field Thesis Codex Agent

## Summary

- Purpose: workspace-scoped engineering/research agent for the Master's thesis **"Application of Built-in Adaptive Remeshing and Mesh Refinement Features in Abaqus to Fracture Simulations Using Phase-field User Elements."**
- Main objective: reproduce a verified phase-field fracture baseline in Abaqus, implement the Pandey-Kumar MISESERI-driven pre-refinement workflow, preserve the scientific meaning of the UEL/UMAT fields, integrate IMFD/ABAQUSER post-processing, and quantify accuracy versus computational cost.
- Operating principle: **baseline first, one controlled change at a time, quantitative gates before claims.**
- File-handoff principle: every source/text file created or edited by the agent is mirrored into a flat `agent_handoff/` directory with a manifest for easy review and upload.
- Report principle: keep the living LaTeX report pair for the active thesis stage updated after every substantial validation, failure, repair, submission, or result. For current Stage D work, update both `docs/thesis/STAGE_D_STATE_TRANSFER_CHAPTER.tex` and `docs/reports/STAGE_D2_STATE_INGESTION_REPORT.tex` together; do not let one lag the other. For historical Stage A, `docs/reports/STAGE_A_BASELINE_REPORT.tex` and `docs/reports/STAGE_A_EXECUTION_AND_FAILURE_LOG.tex` remain the paired record. Do not create a new report for every run, and do not remove failed attempts from execution/failure logs. Generated PDFs remain local build artifacts and ignored.
- Checklist principle: `docs/project/PROJECT_PHASE_CHECKLIST.md` is the authoritative living task and phase checklist. Update it after every substantial operation and keep technical completion separate from scientific validation.
- Mistakes-ledger principle: `docs/project/MISTAKES_AND_FIXES_LOG.md` is mandatory project memory. Append every failed attempt, diagnosis, correction, rerun, and prevention rule; never overwrite or delete a predecessor failure when a later attempt passes.

## Current thesis handoff - update this block after every substantial work session

Updated: 2026-07-23

Current stage:

- Stage C closeout T5 corrected automation smoke job `1376758.mmaster02` completed with PBS `Exit_status=0` and classification `automation_smoke_pass`. Evidence is under `runs/hpc/stage_c2/automation_smoke/h0_notch045/`, final scheduler record `runs/hpc/stage_c2/automation_smoke/T5_CORRECTED_QSTAT_FINAL.txt`, and summary `runs/hpc/stage_c2/automation_smoke/T5_CORRECTED_RESULTS_SUMMARY.md`. This is workflow automation evidence only, not a fracture-reference comparison.
- Stage D2A transferred-state ingestion passed on HPC job `1376785.mmaster02` with PBS `Exit_status=0`, classification `stage_d2a_state_ingestion_pass`, solver exit `0`, readable ODB, `D2A.ok`, `target_ip_coverage=1.0`, maximum `SDV15` interpolation error `0.0`, and maximum `SDV16/H` error `6.428999999030793e-09`. Evidence is under `runs/hpc/stage_d2/d2a_serial_ingestion/`. Abaqus did not expose the UEL phase DOF as usable nodal `U` output in this smoke deck, so D2A verifies transferred phase ingestion through UMAT `SDV15` and transferred history through `SDV16`.
- Stage D2B serial continuation first attempt `1376819.mmaster02` is frozen as `stage_d2b_solver_fail_increment_limit`: Step 1 initialization completed, Step 2 release hold completed, Step 3 continuation partially converged, but the maximum increment count was exhausted. Evidence remains under `runs/hpc/stage_d2/d2b_serial_continuation/`.
- Corrected D2B R1 job `1376825.mmaster02` changed only the D2B release/continuation maximum increments from `2` to `50` and passed with PBS `Exit_status=0`, classification `stage_d2b_serial_continuation_pass`, solver exit `0`, readable ODB, `target_ip_coverage=1.0`, maximum initial `SDV15`/`SDV16` differences vs accepted D2A `0.0`, maximum release `SDV15`/`SDV16` differences `0.0`, observed `U2=1e-05`, finite `RF2=3.46317381026e-07`, and `ALLWK` continuation jump `1.2830926425511091e-11`. Rerun evidence is under `runs/hpc/stage_d2/d2b_serial_continuation_rerun/`; canonical marker `runs/hpc/stage_d2/d2b_serial_continuation/D2B.ok` references accepted rerun job `1376825.mmaster02`.
- Stage D2C four-thread repeatability job `1376831.mmaster02` passed with PBS `Exit_status=0`, classification `stage_d2c_thread_repeatability_pass`, solver exit `0`, readable ODB, confirmed `1 MPI RANK x 4 THREAD`, `target_ip_coverage=1.0`, maximum `SDV15` and `SDV16` thread-vs-serial differences `0.0`, final `U2` difference `0.0`, final `RF2` absolute/relative differences `0.0`, RF-U NRMSE `0.0`, F3 `ALLWK` absolute difference `0.0`, and unchanged increment sequence. Evidence is under `runs/hpc/stage_d2/d2c_threads4_repeatability/`. D2D ABAQUSER verification is next; interrupted Molnar transfer remains unsubmitted.
- Stage D2D0 login-node audit found no ABAQUSER executable, module, source implementation, or documented runnable interface. Classification: `stage_d2d_blocked_abaquser_not_found`. Evidence is under `runs/hpc/stage_d2/d2d_abaquser_verification/`. No D2D PBS job or fracture solver job was submitted. D3 was prepared as design-only under `docs/studies/STAGE_D3_INTERRUPTED_TRANSFER_PLAN.md`, `configs/state_transfer/d3_interrupted_transfer.yaml`, and helper scripts; no D3 solver submission is authorized.
- Stage D3A0/D3A1 audited the existing accepted H0 ODB `1376154.mmaster02` and extracted the `U2=0.003000000026077032 mm` checkpoint in CAE/ODB-only jobs. The final extractor attempt `1376879.mmaster02` produced 15720 element/IP rows, `target_ip_coverage=1.0`, finite `SDV15`/`SDV16`, `max_d=0.08412302285432816`, `max_H=0.0512588769197464`, checkpoint `RF2=0.39450356364250183`, and `RF2/H0_peak=0.5421925638518931`. The original H0 ODB lacked `ALLIE`, `ALLSE`, and `ALLWK`, so D3A required independent energy evidence before acceptance.
- Stage D3A-E R0 independent energy reconstruction job `1376885.mmaster02` is preserved as failed evidence with classification `stage_d3a_energy_reconstruction_fail_parser_scope`: the scope-insensitive parser mixed `Part-1` node labels with the assembly reference-point namespace and produced five false non-positive Jacobian determinants.
- Stage D3A-E R1 corrected the parser scope and passed locally with classification `stage_d3a_energy_reconstruction_pass`: 3930 physical elements, 15720 integration points, non-positive detJ count `0`, minimum detJ `2.829135024804933e-06`, and relative energy residual `0.012586306767288707`. D3A is now closed with classification `stage_d3a_checkpoint_pass_independent_energy_reconstruction`; evidence is under `runs/hpc/stage_d3/interrupted_transfer/checkpoint_energy_r1/`, and `runs/hpc/stage_d3/interrupted_transfer/checkpoint/D3A.ok` exists. D3A2 package construction is next; no fracture solver submission before `D3_PACKAGE.ok`.
- Stage D3A2 built and validated one deterministic nonmatching split-notch target package locally. Classification: `stage_d3a2_transfer_package_pass`; source job `1376154.mmaster02`; checkpoint `U2=0.003000000026077032 mm`; target mesh has 6601 nodes, 6400 Q4 physical elements, 25600 target IPs, 40 duplicated open-notch face-node pairs, shared notch tip, notch length `0.5`, zero crossing elements, node/IP coverage `1.0`, non-positive detJ count `0`, predicted energy relative jump `0.015379624558651227`, and unmapped state count `0`. Evidence is under `runs/hpc/stage_d3/interrupted_transfer/package/`; `D3_PACKAGE.ok` exists with `solver_job_submitted=false`. Next gate is one serial D3A3 ingestion/equilibration/release-hold job; D3D and D3E remain blocked.
- Stage D3A3 first serial ingestion/equilibration/release-hold job `1377382.mmaster02` was submitted exactly once from commit `d6e2474fcae3d05a4171e23c1c2cc757894a8a43` after static preflight pass. PBS finished with `Exit_status=1` before solver analysis because Abaqus user-subroutine compilation could not find `ifort`; the batch script had loaded only `abaqus/2023`. Classification: `stage_d3a3_solver_fail_compiler_environment`; no `D3A3.ok`; D3D and D3E remain blocked. Evidence is preserved under `runs/hpc/stage_d3/interrupted_transfer/target_ingestion/`.
- Stage D3A3-R1 job `1377383.mmaster02` applied the bounded compiler-environment correction: explicit `gcc/11.4.0`, `intel/2024.2.0`, and `abaqus/2023` module loads, `OMP_NUM_THREADS=1`, scratch execution, and `ifort`/Abaqus environment capture. The compiler environment passed, but Abaqus user-subroutine compilation failed before solver analysis because `d3_transfer_table.inc` exceeded the Intel Fortran statement token limit. Classification: `stage_d3a3_solver_fail_transfer_table_compile`; no `D3A3_R1.ok` or `D3A3.ok`; D3D and D3E remain blocked. Evidence is under `runs/hpc/stage_d3/interrupted_transfer/target_ingestion_r1/`.
- Stage D3A3-R2 compile/datacheck job `1377389.mmaster02` compiled and linked after replacing the oversized compiled transfer table with runtime `d3_transfer_h.dat`, but failed Standard datacheck because the UEXTERNALDB loader opened relative `d3_transfer_h.dat` from Abaqus' internal `/local/...` directory. Classification: `stage_d3a3_r2_datacheck_fail_runtime_h_file_not_in_abaqus_workdir`; no `D3A3_R2_COMPILE.ok`; full D3A3-R2, D3D, and D3E remain blocked.
- Stage D3A3-R2-R1 pathfix job `1377391.mmaster02` retained the runtime-H SHA256 `4689ea5c10c0972e69ba46f8676a326c8b011b98faa8031c7c26cfb218607cd9` and used `GETOUTDIR` to resolve the staged `/scratch9/.../d3_transfer_h.dat`, removing the `/local/...` missing-file failure. Datacheck then failed with Intel Fortran severe `(24)`, end-of-file during read on unit 99, caused by the EOF-driven loader issuing a post-last-record read. Classification: `stage_d3a3_r2_r1_datacheck_fail_runtime_h_eof_after_getoutdir_open`; evidence is under `runs/hpc/stage_d3/interrupted_transfer/target_ingestion_compile_r2_r1/`.
- Stage D3A3-R2-R2 counted-read correction ran exactly once as datacheck job `1377393.mmaster02` from commit `9058534a9daa188d2d958f8462b230ec843c545e`. The login-node smoke passed, and Abaqus compiled, linked, completed input processing and Standard datacheck, and printed `D3A3-R2 H LOAD COMPLETE 25600`; premature EOF and runtime-H read-error tokens are absent. The PBS wrapper exited `10` only because Abaqus wrapped the long GETOUTDIR path across two `.msg` lines. D3A3-R2-R3 deterministic no-PBS login-node postcheck replay reconstructed the wrapped path, preserved PBS `Exit_status=10`, verified all compiler/datacheck/runtime-H gates, and created `D3A3_R2_COMPILE.ok` under `runs/hpc/stage_d3/interrupted_transfer/target_ingestion_compile_r2_r2_replay/`. Classification: `stage_d3a3_r2_compile_datacheck_pass_postcheck_replay`; no new PBS datacheck was submitted. The compile/datacheck gate is closed; full D3A3-R2 still must not be submitted until extractor, energy reconstruction, validator, full PBS, static validation, commit, push, and checkout synchronization are complete.
- D3A3-R2 full ingestion/equilibration/release-hold lane was prepared in new R2 scripts: `scripts/hpc/stage_d3/07_d3a3_r2_full_ingestion_hold.pbs` and `scripts/hpc/stage_d3/submit_d3a3_r2_full_ingestion_hold.sh`. They require the committed replay marker, stage runtime `d3_transfer_h.dat`, forbid `d3_transfer_table.inc`, run serial CPU1/16GB/02:00 with `OMP_NUM_THREADS=1`, preserve Abaqus outputs, run Abaqus-Python extraction, run strengthened validation, and create `D3A3.ok` only after gates pass. The deck requests global nodal `U, RF` output; extractor/validator support target Q4 bulk-plus-AT2 energy reconstruction, phase/healing/H/RF/energy jump gates.
- D3A3-R2 full job `1377396.mmaster02` was submitted exactly once from commit `7a860f50fe557cd88cd3299dd47b1f260071f3fa`. Abaqus compiled, linked, completed input processing, completed Standard analysis, and produced ODB/extraction outputs, but the original strengthened validation failed with `Exit_status=21`. Classification of the preserved original directory remains `stage_d3a3_r2_full_validation_fail`. Evidence root: `runs/hpc/stage_d3/interrupted_transfer/target_ingestion_r2/`. No canonical `D3A3.ok` exists.
- D3A3-R2 ODB-only forensic replay used the preserved `1377396` ODB without another Standard solve, Fortran compilation, new transfer package, or new mesh. It corrected visualization IP3/IP4 mapping, TOP-set U/RF extraction, and phase-node recovery from SDV15. Corrected ingestion passes as `stage_d3a3_r2_ingestion_pass_release_not_accepted`: SDV15 transfer max error `1.3877787807814457e-17`, SDV16 transfer max error `0.0`, TOP checkpoint U2 `0.003000000026077032`, 6601 recovered phase nodes, 6400 complete elements, zero missing energy inputs, H decrease violations `0`, and d-healing violations `4651`. Noncanonical marker `runs/hpc/stage_d3/interrupted_transfer/target_ingestion_r2_forensic/D3A3_R2_INGESTION.ok` exists; do not treat it as authorization for D3D/D3E. The next decision is scientific: enforce `d >= d_checkpoint`, modify transfer compatibility, or formally reject unconstrained release of the mapped phase state. No retry or continuation is authorized.
- D3A4 constrained compatibility projection passed offline with no Abaqus job, no Fortran compilation, no new mesh, and no replacement of the original D3A2 package. It assembled the F1-history target phase system, reproduced the forensic F1 residual on all 6601 nodes with max error `2.329340604949326e-21`, and solved the lower-bound obstacle problem in 5 active-set iterations. Classification: `stage_d3a4_constrained_phase_compatibility_pass`; `D3A4.ok` exists under `runs/hpc/stage_d3/interrupted_transfer/compatibility_projection_d3a4/`; separate compatible package exists under `runs/hpc/stage_d3/interrupted_transfer/package_compatible_r1/`. KKT metrics: active nodes `1880`, free nodes `4721`, free residual inf `7.623296525288703e-21`, min active multiplier `3.1903130564656594e-13`, complementarity inf `8.649244021664495e-23`, max d increase `0.011345805575019186`, normalized L2 d increase `0.03901956109385224`, predicted healing violations `0`. Next authorized decision is one bounded D3A3-R3 compatible-state ingestion/equilibration/release-hold test only; D3D/D3E remain blocked.
- D3A3-R3 compatible active-set lane is prepared in `models/state_transfer/d3_interrupted_transfer/executable_r3_compatible/` and `scripts/hpc/stage_d3/08_d3a3_r3_compatible_datacheck.pbs` / `09_d3a3_r3_compatible_hold.pbs` / R1 retry scripts `10_d3a3_r3_compatible_datacheck_staging_r1.pbs` and `submit_d3a3_r3_compatible_datacheck_staging_r1.sh`. The deck fixes all 6601 phase nodes in Steps 1 and 2, then in Step 3 keeps only the 1880 D3A4 active nodes fixed at lower bound and leaves the 4721 free phase nodes unprescribed. Static validation passes with runtime-H SHA256 `ee244da4e87ff0edb1c6e931fe633921aae552785d2d03efb8d18eea555c7173`, 25600 records, no duplicates/missing keys, no `d3_transfer_table.inc`, MPI absent, and R3 Fortran byte-identical to accepted R2.
- D3A3-R3 datacheck job `1377404.mmaster02` was submitted once from commit `2ee6aaaaf364f41e50067dd184445cd04506beae` and failed before Abaqus launched: `executable_r3_compatible/d3_transfer_h.dat` was ignored/untracked and absent from the cluster checkout, so PBS exited `6` during runtime-H staging. Evidence preserved under `target_ingestion_r3_compatible_datacheck/`. M-069 records this staging failure.
- D3A3-R3 staging-correction R1 datacheck job `1377409.mmaster02` ran once from commit `ed622b32781a3e50a77e63699ccb2ca5f87cb76b` in isolated evidence lane `target_ingestion_r3_compatible_datacheck_r1/`. PBS `Exit_status=0`, Abaqus compile/link/input processing/Standard datacheck completed, `D3A3-R2 H LOAD COMPLETE 25600` present, premature EOF/read-error tokens absent, runtime-H SHA unchanged, Step-3 active/free phase BC counts `1880`/`0`. Classification: `stage_d3a3_r3_compatible_datacheck_pass`; `D3A3_R3_DATACHECK.ok` exists only under the R1 evidence directory. M-069 is resolved by the committed staging correction.
- D3A3-R3 full-hold validation lane is strengthened offline: R3 extractor builds active/free/lower-bound phase-node evidence; `analyze_d3a3_r3_fixed_state_kkt.py` reuses D3A4 assembly for Step-2 F1 residual/multiplier KKT; `validate_d3a3_r3_compatible_hold.py` enforces active drift, lower-bound, healing, H decrease, KKT, state-reset, spatial-variation, RF/energy jump and phase-adjustment gates and creates `D3A3_R3.ok`/`D3A3.ok` only on full pass.
- D3A3-R3 postpython environment smoke job `1377416.mmaster02` ran once from commit `0753edb093a679370fd8363eef5e63b3c6c17625`. Under the solver module sequence, baseline `python3` is system 3.6.8; qualified `python/gcc/11.4.0/3.11.7` provides Python 3.11.7, NumPy 2.4.4, SciPy 1.17.1. Synthetic validator tests passed and sparse assembly of the 6601×6601 system with 25600 IPs and zero non-positive detJ passed. Classification: `stage_d3a3_r3_postpython_environment_pass`; marker `runs/hpc/stage_d3/interrupted_transfer/r3_postpython_environment/D3A3_R3_POSTPYTHON.ok`. M-070 records the unqualified-python risk and resolution.
- D3A3-R3 full compatible hold job `1377417.mmaster02` ran exactly once from commit `4bee79e6224ad4acfbeb49d13c51bf7a983e181a` after the ODB-scratch storage patch. Abaqus compiled, linked, completed Standard analysis, and produced a scratch ODB (`odb_preserved=true`, no repository ODB copy). Base ODB extraction completed (`state_rows=102400`), then the R3 active/free state builder failed under Abaqus Python with `TypeError: 'newline' is an invalid keyword argument for this function` in `build_active_free_state`. PBS `Exit_status=20`; classification `stage_d3a3_r3_ingestion_fail`; preserved under `target_ingestion_r3_compatible/`.
- D3A3-R3 deterministic postprocess replay (no solver, no Fortran, no ODB reread) reused committed base-extraction products under Python 3.11.7. Active/free lower-bound audit passed (6601/1880/4721, missing=0). Transfer, TOP RF/U, healing, H, phase adjustment, RF/energy jumps, state-reset, and spatial-variation gates passed. F1 free residual infinity norm was `1.2035463824381645e-08` (> `1e-8`), so classification is `stage_d3a3_r3_fixed_state_needs_reprojection`. Evidence under `target_ingestion_r3_compatible_postprocess_replay/`; no `D3A3_R3_POSTPROCESS_REPLAY.ok` / `D3A3_R3.ok` / `D3A3.ok`. M-071 resolved by architectural separation. New Abaqus solve blocked; D3D/D3E remain blocked until canonical `D3A3.ok`.

- Gate A3 RF–U validation use is **conditionally accepted** (Decisions **1A**/**2B**). Mesh roles: H0 test, H1 production, H2-PUB fine validation.
- Stage C **execution authorized** (user message): staged Jobs 1–5 once each; no automatic retries; no formulation/reference/scope changes without supervisor. Authority: `docs/decisions/STAGE_C_EXECUTION_AUTHORIZATION.md`.
- Fixed remeshing params: errorTarget=0.05, refinementFactor=2.0, min h=0.0025 mm, max h=0.025 mm, 1 pass, no coarsening. Elastic pre-crack `U_pre=0.00464 mm` (=0.8×Upeak_H1).
- Job 3 implemented: ODB extract (`extract_miseseri_from_odb.py`) + remesh (`build_refined_mesh_from_miseseri.py`).
- Job 1 smoke deck + Job 2 preanalysis decks generated and statically validated. Submit Job 1 via `scripts/hpc/submit_stage_c_job1_smoke.sh`.
- Not authorized: automatic retries, parameter sweeps, multicore/GPU, state transfer, online remeshing, formulation/material changes.
- Stage A / WP2 - Molnar baseline reproduction and paper-matched single-notch scientific comparison.
- The unchanged smaller Molnar supplementary single-notch deck has a local technical pass and reproducible first extraction. It remains supporting technical reproducibility evidence, not the exact Fig. 7 numerical comparison target. The paper-matched candidate-v2 serial HPC baseline job `1374864.mmaster02` completed with `paper_matched_v2_technical_pass`; postprocessing against the existing scratch ODB produced RF-U, matched-state contours, crack-path diagnostics, SDV bound/irreversibility diagnostics, and a no-solution decision report. The scientific decision classification is `paper_matched_v2_scientific_review_incomplete`, not a final pass, because post-peak RF-U mismatch and unresolved SDV15 interpretation remain.
- No remeshing result, state-transfer result, or ABAQUSER integration is considered validated yet.
- HPC account access and the upgraded queue/node/software snapshot are documented from `HPC_Upgraded_Resources_and_Software.md` (captured 2026-07-20). The project account can use the normal project route `entryq` in addition to `entry_imfdfkmq`, `testq`, and the teaching route where appropriate. SSH access was restored and verified on 2026-07-15; the HPC clone, home/scratch layout, Abaqus/Intel module probe, PBS queue inspection, and serial `testq` environment smoke attempts are now documented. The final environment rerun job `1374531.mmaster02` passed with `gcc/11.4.0`, `intel/2024.2.0`, `abaqus/2023`, compute host `mnode098.cluster`, repository revision supplied via `PROJECT_REVISION`, and PBS `Exit_status = 0`. The first minimal Abaqus/Standard trivial `UEXTERNALDB` smoke job `1374532.mmaster02` checked out an Abaqus/Standard license, compiled, linked, completed the analysis, and created an ODB, but failed the callback marker check because `uexternaldb_smoke.called` was absent; classification `hpc_user_subroutine_smoke_fail`, failure category `callback_invocation`. The deterministic retry job `1374533.mmaster02` at revision `c5db808b4c8d9e9bd01a9e5da0bd91b173787b8e` passed on `mnode097.cluster` with PBS `Exit_status = 0`, Abaqus return code zero, ODB/STA/MSG present, analysis-success statement present, direct `.msg` callback tokens, and absolute marker file `uexternaldb_smoke.called` containing `UEXTERNALDB_SMOKE_CALLED`; classification `hpc_user_subroutine_smoke_pass`. Gate A3 remains an independent scientific blocker.
- HPC environment smoke: passed.
- HPC Abaqus license checkout: passed.
- HPC user-subroutine compilation: passed for the trivial Abaqus/Standard smoke.
- HPC user-subroutine linking: passed for the trivial Abaqus/Standard smoke.
- HPC Standard analysis completion: passed for the trivial Abaqus/Standard smoke.
- HPC notification rule: from the next HPC submission onward, every tracked PBS script must request email notification points with `#PBS -m abe`, while the private recipient is supplied at submission time with `qsub -M "<verified_recipient>" -m abe`. Verify the recipient address with `python scripts/hpc/validate_pbs_email_notifications.py --email <address> <pbs_files>` before the first submission using that address, then confirm `Mail_Users` and `Mail_Points` with `qstat -f`. Do not assume the cluster account's default email address. Already-submitted job `1374864.mmaster02` remains unchanged.
- HPC notification address: `pr21vyci@mailserver.tu-freiberg.de`. Verification status: `historically_scheduler_verified`. Evidence: PBS `qstat` record for old-project job `1362636.mmaster02` reported `Mail_Users = pr21vyci@mailserver.tu-freiberg.de` and `Mail_Points = abe`. Delivery to the user's inbox was not independently documented, but the address was accepted and stored by the PBS scheduler. Future submissions must pass this address privately with `qsub -M "pr21vyci@mailserver.tu-freiberg.de" -m abe` and immediately verify `Mail_Users`/`Mail_Points`.
- UEXTERNALDB callback invocation: passed in deterministic retry job `1374533.mmaster02`.
- Callback symbol presence in linked library: indirectly exercised by successful compile/link/run and direct callback tokens in job `1374533.mmaster02`; retained binary symbol inspection remains optional evidence, not a blocker for the trivial smoke gate.
- Callback library loading: exercised by job `1374533.mmaster02`, which emitted callback tokens and wrote the absolute marker from inside `UEXTERNALDB`.
- Marker write location: resolved for the deterministic retry through `GETOUTDIR`; marker is `/scratch/pr21vyci/adaptive-remeshing/runs/abaqus_user_subroutine_smoke_retry_1374533.mmaster02/uexternaldb_smoke.called`.
- Callback investigation finding: `insufficient_retained_evidence`.
- Deterministic callback retry: `hpc_user_subroutine_smoke_pass`.
- Overall trivial user-subroutine smoke: passed.
- Failure category: none for the retry; preserved failed attempt `1374532.mmaster02` remains classified as `callback_invocation`.
- Paper-matched candidate v2 technical result: `paper_matched_v2_technical_pass`.
- Paper-matched candidate v2 scientific comparison: `paper_matched_v2_scientific_review_incomplete`.
- Gate A3 RF–U: `gate_a3_conditionally_accepted_rf_u` (Decisions 1A+2B). Contour: deferred. Residual paper-matched/absolute-tolerance items may remain open. Historical package: `docs/decisions/MOLNAR_GATE_A3_SUPERVISOR_REVIEW.md`. Status matrix: `docs/decisions/MOLNAR_GATE_A3_STATUS_MATRIX.md`.
- Stage A: open (RF–U mesh policy frozen; residual narratives may remain).
- MISESERI/remeshing: **preparation authorized**; execution/submission not authorized.
- Evolving remeshing with state transfer is mandatory for the thesis scope, but no online-remesh claim is allowed until controlled field transfer and fracture-relevant transfer tests pass.
- Local environment inspection found Abaqus 2024 (`abaqus`/`abq2024`) and Abaqus Python 3.10.5 available on Windows; Intel Fortran is usable for Abaqus only after the clean-shell Visual Studio Build Tools plus Intel oneAPI setup.
- Molnar and Gravouil (2017) supplementary `.for`/`.inp` files are preserved unmodified under `models/baseline_original/molnar_gravouil_2017/`; checksums are recorded in that folder's `README.md`.
- Local Abaqus user-subroutine smoke test passed after loading Visual Studio 2022 Build Tools `vcvars64.bat` and Intel oneAPI `setvars.bat intel64`: `ifx` 2026.0 compiled, Microsoft `LINK` 14.44 linked, and the trivial Abaqus/Standard analysis completed. This is a local smoke-test result, not an official toolchain-support claim.
- The original Molnar one-element example ran unchanged from a separate run directory and passed the technical gate: compile/link/input/solver/wrap-up and ODB readability passed.
- The unchanged Molnar one-element ODB passed the source-defined scientific check for plane-strain stiffness, degraded stress, homogeneous phase relation, history monotonicity, unloading irreversibility, and integration-point consistency. Evidence is under `runs/molnar_one_element_unchanged/20260714_technical_gate_local/scientific_check/`. Tolerances are provisional working gates only.
- The original Molnar single-notch benchmark ran unchanged from a separate run directory and is classified `technical_pass_scientific_unchecked`. Evidence and extraction outputs are under `runs/molnar_single_notch_unchanged/20260714_technical_gate_local/`.
- The Stage A living LaTeX report is `docs/reports/STAGE_A_BASELINE_REPORT.tex`; generated figures and tables are under `results/figures/stage_a_baseline/` and `results/tables/stage_a_baseline/`.
- The authoritative living task and phase checklist is `docs/project/PROJECT_PHASE_CHECKLIST.md`; validator: `scripts/validation/check_project_phase_checklist.py`.
- Gate A3 reference provenance is under `references/derived/molnar_gravouil_2017/single_notch/`; the current RF-U reference CSV intentionally has no numeric coordinates. The next reference work is to digitize/document the relevant published Molnar curve as an approximate paper reference for a paper-matched reconstructed benchmark, not for the smaller supplementary deck.
- The Gate A3 reference-applicability matrix is `references/derived/molnar_gravouil_2017/single_notch/REFERENCE_APPLICABILITY_MATRIX.md`; it records why the smaller supplementary deck should not be forced into an exact Fig. 7 numerical comparison.
- Paper-to-model reconstruction artifacts are under `references/derived/molnar_gravouil_2017/paper_matched_single_notch/`, with configuration at `configs/molnar_paper_matched_single_notch.yaml` and deck-generation requirements at `docs/methods/MOLNAR_PAPER_MATCHED_DECK_REQUIREMENTS.md`. Candidate v1 is preserved as failed static evidence under `models/generated/molnar_gravouil_2017/paper_matched_single_notch_v1/` and `results/validation/molnar_paper_matched_single_notch_v1/`; classification `static_validation_fail`, `runnable: false`. Candidate v2 is generated under `models/generated/molnar_gravouil_2017/paper_matched_single_notch_v2/` with corrected loading arithmetic, split-node notch topology, source-mapped UEL property blocks, restored `bottoml`/`topl` constraints, and a generated graded mesh. Static validation passed in `results/validation/molnar_paper_matched_single_notch_v2/STATIC_VALIDATION.md`; configuration status is `paper_matched_candidate_v2_static_validation_pass`, `runnable: true`. The generated executable source copy is `models/generated/molnar_gravouil_2017/paper_matched_single_notch_v2/SingleNotch_v2.for`; it is copied from the preserved Molnar source with only `N_ELEM=33852` updated for the candidate mesh. The final mesh-quality preflight passed in `results/validation/molnar_paper_matched_single_notch_v2/MESH_QUALITY_PREFLIGHT.md`; high-aspect-ratio elements are documented outside the refined fracture corridor. The single authorized serial candidate-v2 HPC baseline ran once as `1374864.mmaster02` from revision `711dd495bdcb830d695f9d7e56283316c9d417d5`; PBS finished with `Exit_status = 0`, Abaqus return code zero, ODB/STA/MSG/DAT present, and final classification `paper_matched_v2_technical_pass`.
- Retry authorization: none. Do not submit a retry, second candidate, multi-CPU run, sweep, MISESERI run, remeshing run, state-transfer run, or parameter study under the completed one-run authorization.
- Candidate-v2 scientific diagnostics: peak RF2 `0.761702 kN` at `U2=0.006110 mm`; final RF2 `0.749110 kN` at `U2=0.006700 mm`; RF-U NRMSE against the approximate digitized Fig. 7 `lc=0.0075 mm` curve is `0.247493` in the original scientific check and `0.245705` in the no-solution forensic overlap audit; relative peak-force error is `0.064519`; relative peak-displacement error is `0.041257`; post-peak RMSE is `0.348093 kN`; initial tangent-stiffness error is about `+51.4%`; area error is `+0.193324`. At phase threshold `SDV15 >= 0.95`, the final matched contour has 193 element-mean damaged elements and connected crack extension about `0.0505 mm`; threshold-dependent final extension ranges from `0.0555 mm` at `SDV15 >= 0.80` to `0.0465 mm` at `SDV15 >= 0.99`. `SDV16` is monotonic in the ODB check. The detailed no-solution SDV15 reconstruction reproduced 6113 decrease events with unique keys, found 1297 events above ODB precision (`480` `staggered_sync_effect`, `817` initially `insufficient_mapping_evidence`), confirmed 0 SDV16 decreases at those event locations, and classified the SDV15 item as `sdv15_detailed_review_incomplete`. Follow-up source/deck mapping resolution verified all 33852 U1/U2/CPS4 label/connectivity mappings, found 0 mapping errors, and reclassified the 817 non-staggered events as `insufficient_output_evidence`; the missing evidence is completed within-increment U1 phase-update state output, not layer-label mapping. Late SDV15 overshoot remains recorded up to `1.005600`. The decision report is `runs/hpc/paper_matched_single_notch_v2/scientific_review/SCIENTIFIC_DECISION.md`; detailed SDV15 evidence is under `runs/hpc/paper_matched_single_notch_v2/scientific_review/sdv15_detailed_review/`; mapping-resolution evidence is under `runs/hpc/paper_matched_single_notch_v2/scientific_review/sdv15_mapping_resolution/`; classification remains `paper_matched_v2_scientific_review_incomplete`. These are review diagnostics, not a final scientific pass.
- Decision note `docs/decisions/0002-gate-a3-reference-route.md` is preserved as history but superseded by the proposal-directed route: prepare the paper-matched Molnar Mode-I benchmark, digitize/document the applicable published curve as an approximate paper reference, then compare the reconstructed paper-matched uniform mesh against that reference.

Known source documents:

- `Adaptive_Remeshing_PFF_Rapid_Study_Guide.pdf`
- `1-s2.0-S0168874X16304954-main.pdf` - Molnar and Gravouil (2017)
- `1-s2.0-S0927025614004133-main.pdf` - Msekh et al. (2015)
- `TSP_CMES_67858.pdf` - Pandey and Kumar (2025)
- `1-s2.0-S0045782525004153-main.pdf` - Diddige, Roth, and Kiefer (2025)
- Authorized targeted SDV15 diagnostic run: a separate candidate-v2 diagnostic variant was generated under `models/generated/molnar_gravouil_2017/paper_matched_single_notch_v2_sdv15_diagnostic/` with `72` target physical elements and `152` target element/IP pairs. The single authorized serial job was submitted exactly once as `1375020.mmaster02` from revision `efd5f60ebb9cc6ea8ce89b508a6e9df4183e5611`. PBS accepted `Mail_Users = pr21vyci@mailserver.tu-freiberg.de` and `Mail_Points = abe`, then the job failed pre-solver with `Exit_status = 3` because `git` was unavailable in the batch PATH at the revision guard (`git: Kommando nicht gefunden`; `revision_mismatch current= requested=...`). Abaqus did not launch, no SDV15 diagnostic result exists, and the classification is `molnar_v2_sdv15_diagnostic_technical_fail`. Gate A3 remains `reference_data_insufficient`; no retry, second diagnostic run, candidate v3, Stage B, MISESERI, remeshing, state transfer, or sweep is authorized.
- Infrastructure-corrected r2 authorization: exactly one corrected serial SDV15 diagnostic execution may be prepared and submitted with `16:00:00` walltime, job name `molnar_v2_sdv15_diag_r2`, classification scope `infrastructure_corrected_targeted_diagnostic_execution`, and the same scientific diagnostic deck/source/targets. The r2 PBS must not execute Git; login-side wrapper `scripts/hpc/submit_molnar_v2_sdv15_diagnostic_r2.sh` stages an immutable committed snapshot under scratch, writes `PROJECT_REVISION.txt`, passes `PROJECT_REVISION` and `PRESTAGED_ROOT` to PBS, and directs PBS stdout to scratch. This authorization still excludes automatic retry, second r2 submission, MISESERI, remeshing, Stage B, candidate v3, mesh/length/load studies, parameter sweeps, multi-CPU execution, or scientific model changes.
- Infrastructure-corrected r2 result: the single authorized corrected serial diagnostic job ran exactly once as `1375028.mmaster02` from revision `209ad325d2c85532411c13d8290db08ca35b0637`. PBS history reports `job_state=F`, `Exit_status=1`, `Stageout_status=1`, walltime `00:42:27`, and preserved `Mail_Users = pr21vyci@mailserver.tu-freiberg.de`, `Mail_Points = abe`; the nonzero wrapper result is `postprocess_python_compatibility_failure_after_successful_solve` because the original postprocessor used Python syntax incompatible with the cluster interpreter. Abaqus is a technical pass: return code `0`, `.sta` says `THE ANALYSIS HAS COMPLETED SUCCESSFULLY`, and `.msg` reports zero analysis error messages. Independent RF-U comparison at RP node `34508` is non-intrusive: `202` matched frames and maximum normalized RF2 difference `6.54442468760855e-13`. The no-solution completed-increment replay of the existing `627304` trace rows keeps only the last U1 stage-101 call per `(KSTEP, KINC, physical element, source-storage IP)` and aligns retained-frame events by step time/load level. Result: `sdv15_call_level_nonmonotonicity_observed`; completed/converged increment classification before severity audit `sdv15_completed_increment_possible_violation`; `209152` U1 stage-101 rows, `101840` final increment states, `2184` unique completed-increment SDV15 decreasing transitions, original event-table replay counts `62` possible violations and `1235` monotone, and `0` SDV16 decreases over the same final-increment sequences. Worst retained visualization event `84131 -> physical 16427` is monotone for the inspected converged-increment transitions. Severity audit result under provisional `1e-6` materiality tolerance: `sdv15_completed_increment_irreversibility_violation`; maximum decrease `0.00022384088238425193`, mean `2.8434597987446906e-05`, median `1.3940791172561973e-05`, `2131` transitions above `1e-6`, `1362` above `1e-5`, all after peak displacement, `773` coincident with SDV15 overshoot above one, and `0` SDV16 decreases. Evidence is under `runs/hpc/paper_matched_single_notch_v2_sdv15_diagnostic_r2/evidence/1375028.mmaster02/postprocessing_completed_increment_replay_time_aligned/`. Gate A3 remains `reference_data_insufficient`; candidate-v2 scientific result remains `paper_matched_v2_scientific_review_incomplete`; no second r2 submission or automatic retry is authorized.
- Thesis consolidation: a no-solution Stage A benchmark chapter, reproducibility appendix, figure/table plan, and route-neutral post-supervisor execution-route note were prepared from committed evidence only. Evidence: `docs/thesis/STAGE_A_MOLNAR_BENCHMARK_CHAPTER.tex`; `docs/thesis/STAGE_A_REPRODUCIBILITY_APPENDIX.tex`; `docs/thesis/STAGE_A_FIGURE_TABLE_PLAN.md`; `docs/decisions/POST_SUPERVISOR_DECISION_EXECUTION_ROUTES.md`. Boundary unchanged: Gate A3 remains `reference_data_insufficient`; candidate v2 is not a Gate A3 pass; no Abaqus/PBS/MISESERI/remeshing/state-transfer work is authorized.
- Stage B uniform-reference protocol preparation: route-neutral planning files were prepared and are preserved. Status updated after supervisor decision to `h_convergence_subset_authorized_execution_pending`. Evidence: `docs/studies/STAGE_B_UNIFORM_REFERENCE_PROTOCOL.md`; `docs/studies/STAGE_B_ACCEPTANCE_METRICS.md`; `docs/studies/STAGE_B_HPC_RESOURCE_ESTIMATE.md`; `configs/studies/molnar_uniform_reference_matrix.yaml`. Gate A3 remains `reference_data_insufficient`. Only the three-case h-convergence subset is authorized for execution preparation and submission.
- Local author-supplied exact single-notch Abaqus/CAE reproduction evidence exists under `runs/molnar_single_notch_author_supplied_exact/20260720_abaqus_cae_reproduction/` with Fig. 7 `lc=0.015 mm` digitization including origin `(0,0)`.
- Molnar lc015 h-convergence study prepared and submitted: H0 exact author inputs verified; H1/H2-PUB static validation passed with publication-resolution verified for H2-PUB. Physical elements H0=3930, H1=12064, H2-PUB=33852. Measured corridor h medians approximately 0.00494 / 0.0025 / 0.001 mm. Fig. 7 lc=0.015 corrected-origin reference under `references/derived/molnar_gravouil_2017/single_notch/fig7_lc015_corrected_origin/`.
- Submitted once as serial dependency chain from revision `58d7e3102d76fe0e70e6729457e2c7e90ad131bb`: H0 `1376154.mmaster02`, H1 `1376155.mmaster02`, H2-PUB `1376156.mmaster02`.
- H0 result: `solver_pass_cae_postprocess_failure` (Abaqus RC 0, STA success, ODB retained; CAE f-string parse failure; PBS Exit_status=11). H1/H2: `not_executed_dependency_cancelled` via afterok.
- Authorized recovery submitted once from infrastructure revision `26b7b70832b2e1ae74c54abb7599cbe553aa1bad` with scientific inputs still at `58d7e3102d76fe0e70e6729457e2c7e90ad131bb`: H0 CAE replay `1376184.mmaster02` failed (`OdbError` path `-cae` argv bug); H1 first solve `1376185.mmaster02`; H2-PUB `1376186.mmaster02` afterok H1. Existing H0 ODB hash `01601eff...`.
- Decision: consolidated CAE-only job `1376236.mmaster02` completed successfully for H0/H1/H2-PUB. Solvers remain technical pass with ODBs retained. Scientific h-convergence comparison is now unblocked for RF-U metrics; contour images incomplete (export warning).
- Scheduler: no active h-convergence jobs after CAE completion.

- Formal RF–U analysis: H0→H1 peak force ≈4.00%; H1→H2 peak force ≈0.47%, Upeak change 0%, K0 change ≈0.06%, pre-peak NRMSE ≈0.11%, full NRMSE ≈6.0%, post-peak NRMSE ≈20.2%. Decision frozen in `docs/decisions/MOLNAR_LC015_H_CONVERGENCE_SCIENTIFIC_DECISION.md`.

- Gate A3 supervisor decision package prepared historically (no new runs), then Decisions **1A** and **2B** recorded: `docs/decisions/MOLNAR_GATE_A3_SUPERVISOR_DECISION_1A_2B.md`. Contours deferred; Stage C preparation authorized.
- Mesh roles, H0/H1/H2 results/hashes frozen: `docs/decisions/MOLNAR_MESH_ROLE_AND_RESULT_FREEZE.md`.
- Stage C preparation docs and unified preprocessing config/scaffold created (no HPC jobs).

Immediate next tasks:

1. Job 2 facsimile MISESERI route is **closed** (inactive). Replacement Stage **C2** chain authorized: C2A aux continuum MPI → C2B gate+offline remesh → C2C rebuild → C2D H0 threads4 qual → C2E refined integrity threads → C2F refined final threads.
2. **No MPI for UEL/UMAT.** MPI only for pure continuum C2A. UEL uses `mp_mode=threads` only after C2D passes.
3. Do not use Job 2 ODB for remeshing. Submit once via `scripts/hpc/stage_c2/submit_c2_chain.sh`. No auto-retries / retuning.
4. Policy: `docs/decisions/STAGE_C2_AUX_CONTINUUM_CHAIN.md`.

Unresolved (supervisor only if needed later):

- Formulation/material changes; replacing H1 production reference; new major study axis; accepting unresolved scientific results; thesis scope/conclusion changes.
- Multicore qualification only after serial Stage C workflow is stable.

## HPC access, queues, resources, and operating limits

Source and freshness:

- Evidence source: `HPC_Upgraded_Resources_and_Software.md` together with retained PBS job evidence and the workspace handoff.
- Snapshot date: 2026-07-20.
- This resource snapshot supersedes previous-project resource labels and policies, including “Stage 16N”. Do not copy a previous project's fixed CPU, memory, concurrency, or wall-time defaults into this thesis.
- Queue load, node state, free memory, and availability are dynamic. Never treat this snapshot as a reservation or guaranteed capacity.
- Queue ACLs and group membership show eligibility to submit; they do not guarantee immediate scheduling, software-license availability, or a particular node.
- The filesystem figures below are cluster-wide filesystem capacity/usage values, not personal storage quotas.

Account and access:

- HPC user: `pr21vyci` (`uid=50839`).
- Relevant access roles include general HPC user, teaching, Kiefer/AMS hardware, and Gaussian:
  - `t2-dl-rights-hpc_user`
  - `t2-dl-rights-hpc_teaching`
  - `t2-dl-rights-hpc_hw_kieferams`
  - `t2-dl-rights-hpc_gaussian`
- Windows SSH access is already configured through the user's explicit SSH profile:
  - config file: `$env:USERPROFILE\.ssh\codex_config`
  - host alias: `tu_freiberg`
  - canonical interactive login:
    ```powershell
    ssh -F $env:USERPROFILE\.ssh\codex_config tu_freiberg
    ```
  - canonical one-command form:
    ```powershell
    ssh -F $env:USERPROFILE\.ssh\codex_config tu_freiberg "<remote-command>"
    ```
  - current-job monitoring:
    ```powershell
    ssh -F $env:USERPROFILE\.ssh\codex_config tu_freiberg "qstat -u pr21vyci"
    ```
- Treat this SSH profile and alias as the authoritative access method for this project. Do not create a competing host entry, replace the config file, or assume the default `$env:USERPROFILE\.ssh\config` is being used.
- Before any HPC submission or file transfer, verify the resolved account and cluster context:
  ```powershell
  ssh -F $env:USERPROFILE\.ssh\codex_config tu_freiberg "hostname; whoami; pwd; id; groups"
  ```
- For a persistent interactive session, first establish the login with the canonical command above, then perform module inspection, file staging, and PBS work on the remote shell.
- For scripted checks, prefer the one-command form so the exact SSH profile and host alias remain explicit in logs.
- If the SSH connection fails from an external network, confirm the institutional VPN is active before changing SSH keys or configuration. The existing VPN-service commands remain in the protected user-notes section.

Storage:

- Home: `/home/pr21vyci`.
- Scratch: `/scratch/pr21vyci`.
- Snapshot filesystem status from the upgraded-resource note:
  - `/home`: 17 TB total, 12 TB used, 4.2 TB available, 74% used.
  - scratch backing filesystem shown as `/scratch9`: 28 TB total, 25 TB used, 3.2 TB available, 89% used.
- These values are point-in-time cluster-wide usage figures. Re-run `df -h /home /scratch` before every substantial campaign because scratch pressure is currently high in the recorded snapshot.
- Use home for source, scripts, small inputs, reports, and retained metadata.
- Use scratch for Abaqus work directories, `.odb`, `.sim`, restart, temporary, and other large solver files.
- Every PBS job must stage required inputs to its work directory and copy retained outputs back explicitly.
- Do not infer a personal quota from `df`; query the site quota command or support team before large campaigns.
- Never delete raw results without user approval and a verified retention/stage-out plan.

Submission routes and wall-time ceilings observed in the snapshot:

| Purpose             | Submit queue                           | Scheduler destination / limit                                                                                            | Access interpretation                                                                  |
| ------------------- | -------------------------------------- | ------------------------------------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------- |
| General CPU jobs    | `entryq`                             | routes to`shortq` (12 h), `mediumq` (36 h), `longq` (168 h), `gpuq` (24 h), and configured short fat-node queues | eligible through general HPC-user rights                                               |
| Kiefer/AMS CPU jobs | `entry_imfdfkmq`                     | routes to`short_imfdfkmq` (12 h) or `normal_imfdfkmq` (336 h)                                                        | eligible through`hpc_hw_kieferams` rights; preferred thesis route when appropriate   |
| Teaching jobs       | `entry_teachingq`                    | routes to`teachingq` (24 h)                                                                                            | eligible through teaching rights; use only when the work fits teaching-queue policy    |
| Short test jobs     | `testq`                              | maximum wall time 4 h; queue advertises up to one GPU                                                                    | eligible through general HPC-user rights; suitable for small environment/smoke checks  |
| GPU jobs            | `gpuq` or routing through `entryq` | maximum wall time 24 h                                                                                                   | eligibility exists, but Abaqus GPU benefit/license support must be verified before use |

Queue rules:

- Prefer route queues such as `entryq`, `entry_imfdfkmq`, and `entry_teachingq`.
- Do not submit directly to execution queues marked `from_route_only`.
- Use the Kiefer/AMS route for thesis Abaqus work only when its policy and requested resources match the job.
- Do not request a GPU merely because GPU nodes are visible. The current Molnar UEL/UMAT baseline is CPU-oriented, and GPU acceleration has not been validated.
- Do not request more CPUs, memory, or wall time than justified by a measured smaller run.
- Queue-level maxima are not automatically per-job or per-user entitlements. Confirm effective limits with `qstat -Qf`, the scheduler response, and site documentation.

### Stage C queue-selection policy (mandatory)

Choose the **shortest-wait eligible** queue from live status and resource limits.
**Do not hard-code `normal_imfdfkmq` for small smoke, pre-analysis, CAE, or integrity jobs.**

| Job | Resources | Preferred submit queue |
|---|---:|---|
| Job 1 smoke | 1 CPU, 8 GB, 1 h | `entry_imfdfkmq` |
| Job 2 H0 pre-analysis | 1 CPU, 16 GB, 2 h | `entry_imfdfkmq` when eligible |
| Job 3 CAE remesh | 1 CPU, 16 GB, 1 h | `entry_imfdfkmq` |
| Job 4 integrity | 1 CPU, 16 GB, 2 h | `entry_imfdfkmq` when eligible |
| Job 5 full fracture | 1 CPU, 32 GB, 6 h | `normal_imfdfkmq` unless another eligible queue is faster |

Before every submission:

```powershell
ssh -F $env:USERPROFILE\.ssh\codex_config tu_freiberg "qstat -Qf entry_imfdfkmq | egrep -i 'enabled|started|resources_max|state_count'"
ssh -F $env:USERPROFILE\.ssh\codex_config tu_freiberg "qstat -q"
```

Record `stime - qtime` wait for each job. `entry_imfdfkmq` is a route queue and may land on `short_imfdfkmq` or `normal_imfdfkmq` after routing.

Observed node classes:

| Node class                  | Typical advertised resources                                                                | Relevant queues / notes                                                           |
| --------------------------- | ------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------- |
| Main CPU node               | 40 CPUs, about 190,016,512 KB memory (approximately 181 GiB), no GPU                        | general short/medium/long and related queues                                      |
| Kiefer/AMS extension-2 node | 16 CPUs, about 784,570,368 KB memory (approximately 748 GiB), about 1.48 TiB virtual memory | `normal_imfdfkmq`, `short_imfdfkmq`, `testq`; some nodes also list teaching |
| Fat-memory node             | 40 or 64 CPUs; approximately 748 GiB or approximately 3.0 TiB memory depending on node      | access is queue/scheduler dependent; not guaranteed by visibility                 |
| GPU node                    | 40 CPUs, approximately 181 GiB memory, one GPU                                              | `gpuq`, `testq`, and selected teaching/general routes                         |

### Adaptive-remeshing thesis resource policy

This policy is specific to the current phase-field/adaptive-remeshing thesis and supersedes previous-project “Stage 16N” guidance.

Resource classes:

| Work type                                             | Initial request                                                           | Scaling rule                                                                      |
| ----------------------------------------------------- | ------------------------------------------------------------------------- | --------------------------------------------------------------------------------- |
| Static validation, deck generation, manifest building | 1 CPU, 4-8 GB                                                             | Increase only when the script actually supports parallel work                     |
| Abaqus/CAE ODB extraction or consolidated replay      | 1 CPU, 16 GB                                                              | CAE postprocessing is not treated as a solver-scaling workload                    |
| One-element or environment smoke                      | 1 CPU, 8-16 GB                                                            | Keep serial                                                                       |
| UEL/UMAT scientific reference solve                   | 1 CPU, memory from measured predecessor                                   | Serial reference is mandatory for a new formulation/deck family                   |
| Threaded qualification solve                          | 4, 8, then 16 CPUs; one MPI rank                                          | Proceed only when the previous level is technically and scientifically equivalent |
| Validated production solve                            | Highest validated useful thread count, normally no more than 16 initially | Use the measured fastest scientifically equivalent configuration                  |

Memory and wall-time selection:

- Do not use `90 GB` or `24:00:00` as inherited defaults. Those values belonged to another project.
- Set memory from the largest measured peak of the nearest comparable run, normally with about 50-100% operational headroom and a documented minimum of 8-16 GB.
- Set wall time from measured serial/threaded runtime with sufficient queue headroom; do not request the queue maximum without evidence.
- Current Molnar H0 used far below its 16 GB request, so future memory requests for comparable 2D cases should be evidence-based rather than automatically increased.
- Keep all heavy Abaqus output and temporary files under `/scratch/pr21vyci`.

Threaded qualification evidence:

- identical input-deck, Fortran-source, configuration, and mesh hashes;
- Abaqus technical completion and readable ODB;
- RF2-U2 comparison on a common displacement grid;
- peak force and peak-displacement differences;
- SDV15/SDV16 bounds, crack path, and matched-state contours;
- increment/iteration history and warnings;
- elapsed time, CPU time, parallel efficiency, and peak memory;
- explicit check for COMMON-block races, call-order dependence, label/IP mapping errors, and nondeterministic state updates.

Do not promote a threaded configuration merely because it is faster. It must first be scientifically equivalent under predeclared provisional tolerances. During qualification, run one solver case at a time. Concurrent production jobs require a separate campaign authorization, license check, storage check, and scheduler-capacity check; there is no inherited fixed “two simultaneous jobs” rule for this thesis.

Project-specific threaded PBS pattern, after validation and explicit submission approval:

```bash
#PBS -q entry_imfdfkmq
#PBS -l select=1:ncpus=<validated_threads>:mpiprocs=1:ompthreads=<validated_threads>:mem=<measured_requirement>
#PBS -l walltime=<measured_requirement>
#PBS -j oe
#PBS -m abe

module --force purge
module load gcc/11.4.0
module load intel/2024.2.0
module load abaqus/2023

export OMP_NUM_THREADS=<validated_threads>
export TMPDIR="/scratch/pr21vyci/<run_id>/tmp"
mkdir -p "$TMPDIR"

abaqus job=<job_name> input=<deck.inp> user=<source.for> \
  cpus=<validated_threads> mp_mode=threads interactive
```

Node-selection rules:

- Do not hard-code a hostname from this snapshot; let PBS select a compatible vnode.
- Treat `free`, `offline`, `down`, and `<various>` states as point-in-time scheduler information only.
- Request one node for Abaqus UEL/UMAT work unless a separately validated distributed-memory design requires more.
- The Molnar implementation uses COMMON/shared-memory data transfer. The serial result remains the scientific reference until a threaded repeatability gate passes.
- Future parallel qualification must use one MPI rank with shared-memory threads: `mpiprocs=1`, `ompthreads=<n>`, and Abaqus `mp_mode=threads`. Test the same immutable deck/source at `1`, `4`, `8`, and `16` threads.
- Do not assume MPI processes share COMMON-block data. Distributed-memory or multi-node execution is prohibited until the source is shown process-safe and a separate MPI validation gate is approved.
- A visible 40-core node is not a default 40-core entitlement. First validate up to 16 threads, matching the Kiefer/AMS node class. Requests for 32 or 40 cores require measured 16-thread scaling, a compatible route, and explicit user authorization.

Available software relevant to the thesis:

- Abaqus modules:
  - `abaqus/2021-incomplete` — do not use for thesis runs.
  - `abaqus/2021`
  - `abaqus/2022`
  - `abaqus/2023` — reported as the default Abaqus module in the snapshot.
- Compiler/toolchain modules:
  - `intel/2024.2.0`
  - `gcc/11.4.0` — reported default GCC
  - `llvm/18.1.8`
- Python:
  - `python/gcc/11.4.0/3.11.7`
- Other available tools relevant to preprocessing/post-processing include ParaView, Gmsh, FEniCS/DOLFINx, MATLAB, PETSc, and OpenMPI.

Version boundary:

- The verified local Windows baseline uses Abaqus 2024.
- The HPC snapshot advertises Abaqus 2021, 2022, and 2023, but not Abaqus 2024.
- Therefore an HPC run is a controlled software-version change, not a transparent migration.
- Select one exact Abaqus module and one compiler environment, record both in the run manifest, and repeat the compile/link/solver and scientific regression gates before accepting HPC results.
- Do not claim equivalence between local Abaqus 2024 and an HPC Abaqus 2021/2022/2023 result without quantitative comparison.

Candidate HPC smoke-gate procedure:

1. Log in and capture:
   ```bash
   id
   groups
   qstat -Qf
   module avail abaqus
   module avail intel
   ```
2. Use explicit modules in the PBS script rather than relying on implicit defaults or `.bashrc`:
   ```bash
   module purge
   module load intel/2024.2.0
   module load abaqus/2023
   ```

   This is a candidate stack only; adjust after `module show` and a compile/link test.
3. Submit a serial, single-node, short-wall-time smoke job through `testq` or the approved route queue. After the serial scientific regression passes, use a separately authorized `1/4/8/16`-thread qualification series before any threaded production claim.
4. Preserve module output, environment, terminal log, `.dat`, `.msg`, `.sta`, and ODB-readability evidence.
5. Classify separately:
   - environment/compiler/linker result;
   - technical solver result;
   - scientific regression result.
6. Only after the unchanged one-element result matches the local source-defined checks should the unchanged single-notch benchmark be considered for HPC reproduction.
7. Production jobs still require explicit user approval.

Conservative PBS templates:

General/Kiefer serial smoke test:

```bash
#!/bin/bash
#PBS -N abaqus_uel_smoke
#PBS -q testq
#PBS -l select=1:ncpus=1:mem=8gb
#PBS -l walltime=00:30:00
#PBS -j oe
#PBS -m abe

set -euo pipefail
cd "$PBS_O_WORKDIR"

module purge
module load intel/2024.2.0
module load abaqus/2023

mkdir -p "/scratch/pr21vyci/$PBS_JOBID"
workdir="/scratch/pr21vyci/$PBS_JOBID"
cp OneElement.inp OneElement.for "$workdir/"
cd "$workdir"

abaqus job=OneElement input=OneElement.inp user=OneElement.for cpus=1 interactive
```

Kiefer/AMS routed threaded production candidate, to be used only after serial/threaded equivalence, measured scaling, and explicit approval:

```bash
#PBS -q entry_imfdfkmq
#PBS -l select=1:ncpus=<validated_threads>:mpiprocs=1:ompthreads=<validated_threads>:mem=<measured_requirement>
#PBS -l walltime=<measured_walltime_not_exceeding_queue_limit>
#PBS -m abe
```

The placeholders must be replaced from current-project measurements; they are not defaults. Do not reuse `16 CPUs`, `90 GB`, `24 hours`, or a two-job concurrency rule merely because they appeared in another project's resource note. The private email recipient must be supplied with `qsub -M` and verified after submission.

HPC monitoring and evidence commands:

```bash
qstat -u pr21vyci
qstat -f <job_id>
tracejob <job_id>
pbsnodes -av
module list
```

Record the exact timestamp whenever queue or node state is reported.

## Scientific source hierarchy

Use sources in this order when they disagree:

1. The signed thesis proposal and explicit supervisor instructions.
2. Original supplied source code and its associated paper/tutorial.
3. The original papers listed above.
4. Abaqus documentation for the installed release.
5. The rapid study guide as a synthesis and checklist, not as a substitute for the papers.
6. Secondary literature only when explicitly added to the project bibliography.

Never silently combine equations, phase-field conventions, degradation functions, energy splits, element interpolation, state-variable layouts, or staggered/monolithic algorithms from different sources.

## Non-negotiable scientific boundaries

- The phase-field convention must be recorded for every implementation. In the Molnar convention, `d=0` is intact and `d=1` is fully broken. Do not reverse it in code, plots, or transfer logic.
- `MISESERI` is an Abaqus stress-discretization error indicator based on recovered von Mises stress. It is **not** a mathematical phase-field error estimator.
- The Pandey-Kumar workflow is primarily a coarse pre-analysis followed by targeted mesh refinement and a final phase-field run. Do not describe it as fully online crack-following adaptivity unless the implementation actually remeshes during fracture evolution and transfers all required state.
- A fine mesh should initially target a defensible `h/l` ratio. `h/l <= 0.5` is a starting point from the supplied literature, not a universal convergence proof.
- Phase-field results may be sensitive to mesh size, length scale, load increment, energy split, and solver coupling. Change and study these separately.
- Irreversibility must be verified. A damaged point must not heal during unloading unless the selected formulation explicitly permits it.
- UEL/UMAT/overlay-element labels and integration-point indexing are part of the scientific implementation, not bookkeeping details.
- COMMON-block or other shared-memory transfer is considered fragile until serial/parallel repeatability and element-number mapping are tested.
- Do not claim validation because a job completed. Validation requires comparison against predeclared quantitative and qualitative gates.
- Do not claim computational savings without reporting model size, active degrees of freedom where available, CPU/wall time, memory, increments/iterations, hardware, and solver settings.
- Do not compare crack contours at unmatched load/displacement states.

## Role and privileges

The agent may, when instructed:

- Read project files and the supplied papers.
- Create and edit source code, Abaqus input files, Python scripts, Fortran UEL/UMAT code, documentation, plotting scripts, and tests.
- Run local terminal commands, formatters, parsers, unit tests, small preprocessing jobs, and post-processing scripts.
- Generate reproducible handoff copies of files touched in the current operation.

The agent must not without explicit user approval:

- Submit Abaqus or HPC production jobs.
- Delete raw solver results, source code, reference decks, or experimental data.
- Overwrite a known-good baseline.
- Change the governing formulation while presenting the result as a numerical-only change.
- Queue large parameter sweeps.
- Commit, push, rewrite Git history, or remove branches.

## General behavior

- Before editing, state the planned files and the scientific purpose of the change.
- Prefer small, reversible changes and new versioned files over destructive overwrites.
- Preserve the original reference implementation in a read-only or clearly named `baseline_original/` area.
- For every numerical change, identify the expected effect and the test that can falsify it.
- Log assumptions explicitly. Never hide missing information behind a plausible default.
- Use exact paths, job names, parameter values, timestamps, and software versions in reports.
- When a run fails, preserve the failure evidence and classify it as environment, preprocessing, compilation, solver convergence, post-processing, or scientific mismatch.
- Keep raw data separate from derived plots and tables.
- Prefer configuration-driven scripts over hard-coded benchmark values.
- Make scripts rerunnable and idempotent where practical.

## Recommended workspace structure

```text
.
|-- .agent.md
|-- README.md
|-- THESIS_PLAN.md
|-- WORKSPACE_STRUCTURE.md
|-- references/
|   |-- papers/
|   `-- notes/
|-- src/
|   |-- uel/
|   |-- umat/
|   |-- abaquser/
|   `-- shared/
|-- models/
|   |-- baseline_original/
|   |-- one_element/
|   |-- mode_I/
|   |-- mode_II/
|   |-- hole_plate/
|   |-- l_panel/
|   `-- multi_hole/
|-- scripts/
|   |-- preprocessing/
|   |-- remeshing/
|   |-- postprocessing/
|   |-- validation/
|   `-- sync_agent_handoff.py
|-- configs/
|-- tests/
|   |-- unit/
|   |-- deck_checks/
|   `-- regression/
|-- runs/
|   |-- local/
|   `-- hpc/
|-- results/
|   |-- raw_index/
|   |-- processed/
|   |-- figures/
|   `-- tables/
|-- docs/
|   |-- experiment_records/
|   |-- decisions/
|   |-- methods/
|   `-- handoffs/
`-- agent_handoff/
```

Do not reorganize an existing workspace merely to match this tree. Map existing folders to these roles and document the mapping.

## Thesis execution stages and gates

### Stage A - Freeze and verify the original baseline

Required work:

- Compile and run the original Molnar example unchanged.
- Record environment and solver metadata.
- Reproduce the one-element check.
- Reproduce at least one single-edge-notched benchmark.
- Implement automated extraction of reaction force/displacement, phase field, selected SDVs, energies, element count, timing, and solver status.

Gate A1 - environment:

- Reference source compiles without undocumented source edits.
- Job starts with the intended user subroutine.
- Compiler and linker commands are archived.

Gate A2 - one-element verification:

- Status: passed locally for the unchanged Molnar one-element run using provisional numerical tolerances.
- Elastic response, degradation behavior, phase-field evolution, and history/irreversibility behavior agree with the source-defined analytical relations.
- Residual/tangent sign and DOF ordering are documented in the source notes and validator report.

Gate A3 - benchmark reproduction:

- Force-displacement curve and crack contour are compared at matched displacement states.
- Differences are quantified, not described only visually.
- Any mismatch is classified before proceeding.

Do not modify remeshing logic before Gate A3 is passed or explicitly waived by the user/supervisor.

### Stage B - Build the uniform fine-mesh reference

Required work:

- Choose a benchmark and create a uniformly fine reference mesh.
- Study mesh size, length scale, and load increment independently.
- Establish the reference curve, crack path, fracture energy, and runtime/resource baseline.
- Define the crack-identification threshold and curve-interpolation method.

Gate B1:

- A convergence trend is demonstrated for the selected outputs.
- The chosen reference mesh is justified, not merely the finest affordable case.
- Acceptance metrics are written before adaptive/refined results are evaluated.

### Stage C - Reproduce the Pandey-Kumar pre-refinement pipeline

Required workflow:

1. Generate a coarse model from the same geometry/material/loading source as the final model.
2. Create the layered UEL/UMAT/facsimile arrangement required to expose stress to Abaqus.
3. Ensure `umatelem` and `All_elem` mappings are valid and have matching connectivity where the method requires it.
4. Request at minimum `MISESERI`, `MISESAVG`, `S`, `EVOL`, `U`, `RF`, and required `SDV` outputs.
5. Create and log the remeshing rule, including `errorTarget`, `refinementFactor`, `minElementSize`, `maxElementSize`, coarsening policy, output frequency, and remeshing pass count.
6. Run the coarse pre-analysis.
7. Apply Abaqus native adaptive remeshing using the resulting ODB.
8. Export/regenerate the refined input deck.
9. Rebuild the UEL/UMAT layers on the refined connectivity.
10. Validate sets, sections, properties, element types, node/element labels, boundary conditions, amplitudes, output requests, and UEL DOF ordering.
11. Run an elastic dry test before the full fracture analysis.
12. Run the refined phase-field model and compare with the uniform reference.

Gate C1 - refined deck integrity:

- Automated deck checks pass.
- Refined mesh satisfies the selected local `h/l` requirement.
- No required set or property is lost.

Gate C2 - scientific comparison:

- Peak-force error, curve error, fracture-energy error, crack-path difference, and computational cost are reported.
- The MISESERI-marked zone is shown separately from the final phase-field crack.
- Results are not accepted solely because the crack looks plausible.

### Stage D - State transfer and IMFD/ABAQUSER integration

State-transfer inventory:

- Nodal phase field.
- History field enforcing irreversibility.
- Integration-point state variables.
- Degradation-related variables.
- Stress/strain fields needed for restart or visualization.
- Any coupling or bookkeeping arrays used by UEL, UMAT, or ABAQUSER.

Required tests:

- Transfer a known analytical spatial field between two meshes and measure L2 and maximum error.
- Check physical bounds after mapping.
- Check no-healing/monotonic-history conditions.
- Compare total energies immediately before and after transfer.
- Check element/integration-point ordering.
- Repeat serially and, if parallel execution is intended, compare parallel results.

ABAQUSER/IMFD work:

- Document variable names, dimensions, ordering, units, and intact/broken convention.
- Keep solver fields separate from visualization-only fields.
- Verify 2D/3D/axisymmetric assumptions before reusing generalized routines.
- Produce a minimal visualization test before integrating the complete fracture model.

Gate D1:

- State transfer is demonstrated on a controlled field before a fracture case.
- ABAQUSER output matches independent extraction for selected points/elements.
- Any unsupported state variable is explicitly listed.

### Stage E - Sensitivity, efficiency, and thesis recommendations

Minimum sensitivity axes:

- `h/l`.
- Length scale `l` with `h/l` controlled.
- Load increment strategy.
- Coarse pre-analysis mesh size.
- `errorTarget`.
- `refinementFactor`.
- Minimum and maximum element sizes.
- One versus multiple remeshing passes.
- Serial versus parallel execution if shared data are used.

Minimum outputs per case:

- Force-displacement curve.
- Phase-field contours at matched states.
- Crack path using a declared threshold.
- Peak force and initiation displacement.
- Fracture/dissipated energy as defined by the implementation.
- Element/node count and active DOFs if available.
- Wall time, CPU time, peak memory, increments, and iterations.
- Mesh map and local `h/l` distribution.
- Exact configuration and source-code revision.

Recommended metrics:

```text
e_peak  = abs(Fmax_candidate - Fmax_reference) / abs(Fmax_reference) * 100%
e_curve = ||F_candidate(U) - F_reference(U)||_2 / ||F_reference(U)||_2 * 100%
saving  = (cost_reference - cost_candidate) / cost_reference * 100%
```

Crack-path comparison must state:

- phase-field threshold;
- geometry scaling;
- load/displacement state;
- distance measure, such as sampled centerline distance or Hausdorff distance.

## Provisional validation policy

Until the supervisor approves final tolerances, use the following only as internal working gates:

- Primary scalar outputs: target <= 5% relative error.
- Force-displacement curve: target <= 5% normalized L2 error.
- Crack path: must remain inside a benchmark-specific geometric tolerance defined before viewing the candidate result.
- No unexplained discontinuity in energy or history variables after remeshing/transfer.

Label these as `provisional_working_gate`, not as a thesis-standard acceptance criterion.

Validation classifications:

- `not_run`
- `technical_fail`
- `technical_pass_scientific_unchecked`
- `scientific_fail`
- `provisional_pass`
- `validated_against_declared_gate`
- `feasibility_only`

Never promote `feasibility_only` to validation.

## Abaqus UEL/UMAT implementation rules

- Document UEL type, nodal DOFs, element dimension, interpolation order, integration rule, property-array layout, and state-variable layout.
- Keep a machine-readable or tabular map of every `PROPS`, `JPROPS`, and `SVARS/STATEV` index.
- Add bounds checks and clear diagnostic messages where the Abaqus interface permits them.
- Avoid hidden dependence on element call order.
- Treat overlay/facsimile element numbering as an explicit mapping with validation checks.
- Verify `AMATRX` and `RHS` conventions with the smallest possible test.
- Where practical, compare the analytical tangent with a finite-difference directional derivative.
- Preserve double precision consistently across source files and compiler flags.
- Do not alter fixed/free-form Fortran formatting accidentally.
- Keep physics calculations separate from Abaqus interface plumbing where feasible.
- Any stabilization, residual stiffness, clipping, or numerical tolerance must be named, configurable, and reported.
- For staggered schemes, record whether there is one pass per increment or an inner coupling iteration and its stopping criterion.
- For monolithic schemes, document symmetry/unsymmetry and consistent tangent assumptions.

## Remeshing-specific rules

- Log every remeshing-rule argument in a run manifest.
- Disable coarsening for the first irreversible-fracture baseline unless there is a specific, verified reason to allow it.
- Keep the coarse pre-analysis loading and boundary conditions consistent with the final fracture problem.
- Do not treat a coarse pre-analysis as physically converged unless independently shown.
- Save images/data for the coarse stress field, MISESERI field, refined mesh, and final phase-field crack as separate artifacts.
- After remeshing, run automated comparisons of model keywords and entity counts.
- Verify that the intended local minimum size was actually reached.
- Check mesh-quality and size-transition metrics, not only element count.
- Distinguish mesh regeneration from physical-state transfer in code and documentation.

## Python scripting rules

- Detect and document the Python version embedded in the installed Abaqus release.
- Avoid language/library features unsupported by that interpreter.
- Use a CLI or configuration file for benchmark parameters; do not bury them inside CAE commands.
- Provide `--dry-run` for scripts that rewrite input decks, remesh models, submit jobs, or delete files.
- Validate required files, model names, steps, instances, sets, and output variables before running expensive work.
- Make generated filenames deterministic and include a run identifier.
- Write a manifest containing input paths, parameters, timestamp, software version, and output paths.
- Fail loudly on duplicate element labels, missing sets, inconsistent connectivity, or unknown element types.
- Keep ODB extraction scripts read-only.
- Use interpolation onto a common displacement grid before computing curve error.
- Unit-test pure parsing/transformation functions outside Abaqus where possible.

## Fortran source rules

- Preserve the compiler-compatible source form and line-length rules.
- Use explicit kinds/precision consistently.
- Centralize constants and array-index definitions.
- Comment every shared-data interface and its ownership/lifetime.
- Avoid implicit assumptions about thread/process memory.
- Add a serial reference path before parallel execution.
- Never rename or reorder state variables without updating the mapping documentation, post-processing code, and regression tests.

## Experiment and run management

Each run directory should contain or reference:

- `run_manifest.json` or equivalent configuration.
- Input deck and user-subroutine revision/hash.
- Software/compiler/hardware metadata.
- Submission command and solver command.
- Abaqus status and relevant log excerpts.
- Extracted raw curves/fields.
- Validation metrics.
- `RUN_SUMMARY.md` with classification and next action.

Naming convention example:

```text
<benchmark>__<method>__hOverL-<value>__errTarget-<value>__<YYYYMMDD-HHMM>
```

Do not overwrite a completed run directory. Create a new run identifier.

## Job submission and resource reporting

Before any Abaqus/HPC submission:

- Obtain explicit user approval unless a standing instruction exists in the repository.
- Identify the work class: CAE-only, serial scientific reference, threaded qualification, or validated threaded production.
- Never infer a CPU count from node capacity alone. For UEL/UMAT jobs, use `cpus=1` unless a project-specific threaded qualification has passed for the same formulation/deck family.
- For a validated threaded job, use one MPI rank and the recorded OpenMP thread count; record `ncpus`, `mpiprocs`, `ompthreads`, `OMP_NUM_THREADS`, and Abaqus `mp_mode` in the manifest.
- Choose memory and wall time from measured current-project evidence, not from previous-project defaults.
- Read the current HPC handoff/configuration file if one exists.
- Confirm license availability, queue, CPUs, MPI/OpenMP layout, memory, wall time, scratch path, and stage-out policy.
- Confirm the job uses the intended input deck and subroutine revision.
- Confirm the tracked PBS script has `#PBS -m abe`.
- Pass the private recipient at submission time with `qsub -M "pr21vyci@mailserver.tu-freiberg.de" -m abe`.
- Verify the recipient address before the first submission with `scripts/hpc/validate_pbs_email_notifications.py`; do not assume the cluster account's default email address.
- Immediately after submission, run `qstat -f "$JOB_ID"` and verify `Mail_Users = pr21vyci@mailserver.tu-freiberg.de` and `Mail_Points = abe`.

Future submission pattern:

```bash
REVISION=$(git rev-parse HEAD)

JOB_ID=$(qsub \
  -M "pr21vyci@mailserver.tu-freiberg.de" \
  -m abe \
  -v PROJECT_REVISION="${REVISION}" \
  scripts/hpc/<job-script>.pbs)

echo "${JOB_ID}"
qstat -f "${JOB_ID}" | grep -E 'Mail_Users|Mail_Points|job_state|queue'
```

For a running job, report:

- job ID, state, queue, host/vnode;
- requested CPUs, MPI ranks/threads, memory, wall time;
- used wall time, CPU time/utilization, memory/VMEM when available;
- current increment/step and latest meaningful log lines;
- exact timestamp.

For a finished job, report:

- exit status and whether Abaqus completed normally;
- final resources used;
- start/finish timestamps;
- scientific classification, which is separate from technical completion.

Never delete large results merely to save storage without user approval and a verified retention plan.

## Git and large-file hygiene

- Keep raw `.odb`, restart, scratch, and other large generated Abaqus files out of Git unless explicitly required.
- Prefer targeted Git commands such as `git status --short --untracked-files=no`, `git diff -- <paths>`, and explicit `git add <paths>`.
- Avoid broad hashing, full-tree scans, `git gc`, or recursive diffs in a workspace containing large solver outputs unless the user approves.
- Do not commit the flat `agent_handoff/` mirror by default.
- Preserve reference source archives and record checksums.

## File tracking and handoff mirror - required behavior

For every operation that creates or edits source/text files:

1. Record the workspace-relative paths of all touched files.
2. Run:
   ```bash
   python scripts/sync_agent_handoff.py <file1> <file2> ...
   ```
3. The script clears existing files in `agent_handoff/`, copies only the current operation's files into the flat directory, and writes `MANIFEST.md` with original paths, sizes, timestamps, and SHA-256 hashes.
4. Do not mirror large solver outputs or binary files unless the user explicitly asks.
5. If two touched files have the same basename, stop and resolve the ambiguity rather than silently overwriting one.
6. The mirror is a handoff snapshot, not version history.

Default excluded extensions include large/generated Abaqus outputs such as:

```text
.odb .sim .stt .res .mdl .prt .dat .msg .lck .023 .cax .abq .pac .sel
```

## Documentation rules

Maintain:

- `docs/decisions/` for formulation and workflow decisions.
- `docs/experiment_records/` for one record per meaningful run or comparison.
- `docs/methods/` for stable procedures.
- `docs/handoffs/` for current-status summaries.
- `docs/project/PROJECT_PHASE_CHECKLIST.md` as the single authoritative living task and phase checklist.

Checklist rules:

- Update `docs/project/PROJECT_PHASE_CHECKLIST.md` after every substantial operation.
- Every completed item must link to evidence or identify its commit/run.
- Failed attempts remain recorded.
- Technical completion and scientific validation must remain separate.
- A phase may be marked complete only after its stated gate passes.
- Blocked downstream tasks must remain visibly blocked.
- When a phase closes, record closure date, final commit, passed gate, frozen reports, and remaining limitations.
- Do not create duplicate phase checklists.
- Generated PDFs are not checklist evidence unless their source and generation command are recorded.

Every decision record should state:

- question;
- alternatives;
- evidence;
- decision;
- consequences;
- date and owner.

Every figure intended for the thesis should have:

- source run IDs;
- variable and threshold definitions;
- units;
- matched load/displacement state;
- generation script path;
- no manual edits that change scientific content.

## Common failure triage

Crack path changes after remeshing:

- Check state/history transfer, mesh bias, sets, element orientation, and phase-field convention.

MISESERI marks irrelevant regions:

- Check coarse-mesh adequacy, load stage, boundary conditions, stress exposure through UMAT/facsimile elements, and output frequency.

Peak load is too high:

- Reduce `h/l` and load increment separately; verify energy split and material units.

Healing appears:

- Check history max-update, state storage, transfer interpolation, and initialization.

No phase-field contour in ODB/ABAQUSER:

- Check overlay/visualization layer, SDV mapping, element labels, and output requests.

Parallel and serial results differ:

- Check COMMON/shared data, call-order assumptions, race conditions, and element indexing.

Refined input deck fails:

- Diff keyword blocks; check UEL definitions, sections, property blocks, connectivity, sets, amplitudes, and DOF ordering.

Job finishes but result is wrong:

- Classify as `technical_pass_scientific_unchecked` or `scientific_fail`, never `validated`.

## Agent session closing checklist

At the end of each substantial session:

1. Summarize files changed and commands run.
2. Report tests and their outcomes.
3. State the current scientific classification.
4. List unresolved issues and the next smallest falsifiable task.
5. Update the current thesis handoff block at the top of this file when status changed materially.
6. Refresh `agent_handoff/` with only the files touched in the final operation.
7. Do not edit the user-notes block below.

## User notes - do not edit below this line

- Add supervisor-specific constraints, deadlines, institutional templates, and personal preferences here.

User Notes (don't touch this section):
ssh -F $env:USERPROFILE\.ssh\codex_config tu_freiberg "qstat -u pr21vyci"

VPN service start (first run as administrator)

powershell -Command "Start-Process PowerShell -Verb RunAs"

Start-Service -Name 'eduWGManager$eduVPN'
Start-Service -Name 'OpenVPNServiceInteractive$eduVPN'

ssh -F $env:USERPROFILE\.ssh\codex_config tu_freiberg 'cd ~/software/src && rm -rf install-tl-* && wget -O install-tl-unx.tar.gz https://mirror.ctan.org/systems/texlive/tlnet/install-tl-unx.tar.gz && tar -xzf install-tl-unx.tar.gz && cd "$(find . -maxdepth 1 -type d -name '"'"'install-tl-*'"'"' | sort | tail -n 1)" && perl ./install-tl --no-interaction --scheme=small --no-doc-install --no-src-install --texdir=$HOME/texlive/2026 && echo '"'"'export PATH=$HOME/texlive/2026/bin/x86_64-linux:$PATH'"'"' >> ~/.bashrc && source ~/.bashrc && which pdflatex && pdflatex --version | head -n 2'
