# Molnar v2 SDV15 Targeted Diagnostic r2 Run Manifest

Status: `completed_with_postprocess_replay`

Classification scope: `infrastructure_corrected_targeted_diagnostic_execution`

## Purpose

Run exactly one infrastructure-corrected serial SDV15 targeted diagnostic
execution to resolve the 817 `insufficient_output_evidence` events. The earlier
job `1375020.mmaster02` remains preserved as
`molnar_v2_sdv15_diagnostic_technical_fail`; it failed before Abaqus launched
because `git` was unavailable inside the PBS batch environment.

## Scientific Model Boundary

The r2 execution uses the already validated diagnostic model without changing:

- diagnostic input deck;
- nodes and connectivity;
- U1/U2/CPS4 layer labels;
- properties and materials;
- boundary conditions;
- amplitudes;
- loading schedule, load increments, and final displacement;
- monitored target set;
- diagnostic Fortran logic;
- postprocessing scientific criteria.

Confirmed retained diagnostics:

- target physical elements: `72`;
- target element/IP pairs: `152`;
- deck comparison: `scientific_keyword_equivalence_pass`;
- static validation: `diagnostic_static_validation_pass`;
- runnable flag: `diagnostic_runnable: true`.

## Infrastructure Corrections

- New PBS script: `scripts/hpc/molnar_paper_matched_single_notch_v2_sdv15_diagnostic_r2.pbs`.
- New login-side wrapper: `scripts/hpc/submit_molnar_v2_sdv15_diagnostic_r2.sh`.
- PBS job name: `molnar_v2_sdv15_diag_r2`.
- Walltime: `16:00:00`.
- The PBS script executes no Git commands.
- The wrapper resolves the commit on the login node, stages required committed
  files to `/scratch/pr21vyci/adaptive-remeshing/prestage/`, writes
  `PROJECT_REVISION.txt`, and passes both `PROJECT_REVISION` and
  `PRESTAGED_ROOT` to PBS.
- PBS verifies the plain-text revision manifest and staged input hashes before
  Abaqus launches.
- PBS stdout is directed to `/scratch/pr21vyci/adaptive-remeshing/pbs_output/`
  rather than the repository root.

## Requested Resources

- Queue: `entry_imfdfkmq` (expected routing: `normal_imfdfkmq`).
- Select: `1:ncpus=1:mem=32gb`.
- Walltime: `16:00:00`.
- Modules: `gcc/11.4.0`, `intel/2024.2.0`, `abaqus/2023`.
- Execution: serial Abaqus, `cpus=1`.
- Email: pass privately with
  `qsub -M "pr21vyci@mailserver.tu-freiberg.de" -m abe`; tracked PBS contains
  `#PBS -m abe`.

## Submission Record

- Preparation commit: `209ad325d2c85532411c13d8290db08ca35b0637`.
- Submitted job: `1375028.mmaster02`.
- Submission time: `20260716T124140+0200`.
- Initial scheduler state: `Q`.
- Routed queue: `normal_imfdfkmq`.
- Requested resources from `qstat -f`: `Resource_List.ncpus = 1`,
  `Resource_List.mem = 32gb`, `Resource_List.select = 1:ncpus=1:mem=32gb`,
  `Resource_List.walltime = 16:00:00`.
- Mail verification from `qstat -f`: `Mail_Users =
  pr21vyci@mailserver.tu-freiberg.de`, `Mail_Points = abe`.
- Scratch pre-stage:
  `/scratch/pr21vyci/adaptive-remeshing/prestage/molnar_v2_sdv15_diag_r2_20260716T124140+0200_209ad325d2c8`.
- PBS output directory:
  `/scratch/pr21vyci/adaptive-remeshing/pbs_output/molnar_v2_sdv15_diag_r2_20260716T124140+0200_209ad325d2c8`.
- Output path is under scratch and `Join_Path = oe`; the scheduler still lists
  the default `Error_Path`, but stderr is joined to stdout by PBS.
- Local evidence:
  `runs/hpc/paper_matched_single_notch_v2_sdv15_diagnostic_r2/evidence/1375028.mmaster02/`.

The job completed the Abaqus solve but the PBS wrapper exited nonzero because
the original postprocessor used Python syntax incompatible with the cluster
postprocessing interpreter. A no-solution replay of the existing trace is
preserved under
`evidence/1375028.mmaster02/postprocessing_completed_increment_replay_time_aligned/`.

## Classifications

Technical:

- `molnar_v2_sdv15_diagnostic_r2_technical_pass`
- `molnar_v2_sdv15_diagnostic_r2_technical_fail`

Diagnostic:

- `sdv15_call_level_nonmonotonicity_observed`
- `sdv15_completed_increment_monotone`
- `sdv15_completed_increment_possible_violation`
- `sdv15_completed_increment_irreversibility_violation`
- `sdv15_completed_increment_numerical_tolerance_effect`
- `sdv15_completed_increment_review_incomplete`
- `diagnostic_instrumentation_intrusive`

Pre-solver failure classes:

- `missing_submission_variable`
- `missing_revision_manifest`
- `revision_manifest_mismatch`
- `staged_input_hash_failure`
- `module_environment_failure`
- `missing_abaqus_executable`

## Authorization Scope

Authorized: exactly one infrastructure-corrected serial r2 submission.

Not authorized: automatic retry, second r2 submission, MISESERI, remeshing,
Stage B, candidate v3, mesh/length/load studies, parameter sweeps, multi-CPU
execution, or changes to the diagnostic scientific model.

Current r2 result after replay: PBS wrapper
`postprocess_python_compatibility_failure_after_successful_solve`; Abaqus
`molnar_v2_sdv15_diagnostic_r2_technical_pass`; diagnostic instrumentation
`non_intrusive_pass`; scientific evidence
`sdv15_call_level_nonmonotonicity_observed`; completed/converged increment
classification `sdv15_completed_increment_possible_violation`. Gate A3 remains
`reference_data_insufficient`. A follow-up no-solution severity audit of the
2184 completed-increment decreasing transitions classifies the SDV15 result as
`sdv15_completed_increment_irreversibility_violation` under the provisional
`1e-6` materiality tolerance. This does not close Gate A3 because RF--U
reference acceptance and supervisor-approved tolerances remain unresolved.
