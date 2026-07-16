# Molnar v2 SDV15 Targeted Diagnostic r2 Run Manifest

Status: `prepared_not_submitted`

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

## Classifications

Technical:

- `molnar_v2_sdv15_diagnostic_r2_technical_pass`
- `molnar_v2_sdv15_diagnostic_r2_technical_fail`

Diagnostic:

- `sdv15_completed_state_monotone`
- `sdv15_completed_state_possible_violation`
- `sdv15_diagnostic_output_incomplete`
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

Gate A3 remains `reference_data_insufficient` after submission unless the
diagnostic result and supervisor decisions later justify a gate update.
