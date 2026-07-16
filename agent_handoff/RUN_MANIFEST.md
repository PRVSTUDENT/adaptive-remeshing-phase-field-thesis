# Molnar Candidate v2 SDV15 Targeted Diagnostic Run Manifest

Status: `finished_technical_fail`

Classification: `paper_matched_candidate_v2_diagnostic_variant`

## Relationship To Candidate v2

This run is a targeted scientific-evidence collection run derived from
candidate v2. It is not a benchmark retry, candidate v3, Stage B run, MISESERI
run, remeshing run, state-transfer run, mesh/length/load study, or parameter
sweep.

The candidate-v2 directory is preserved unchanged. The diagnostic variant lives
under `models/generated/molnar_gravouil_2017/paper_matched_single_notch_v2_sdv15_diagnostic/`.

## Unchanged Scientific Parameters

Geometry, mesh, node and element connectivity, U1/U2/CPS4 layer labels,
material properties, phase-field length, fracture energy, thickness,
stabilization, boundary conditions, loading amplitudes, Step 1/Step 2 schedules,
solver controls, and established output requests are identical to candidate v2.

## Diagnostic Modifications

- Source-side target-gated logging in `SingleNotch_v2_sdv15_diagnostic.for`.
- Deterministic monitored target list in `diagnostic_targets.csv` and
  `diagnostic_targets.inc`.
- Abaqus input deck contains only diagnostic-identification comments beyond the
  candidate-v2 deck.
- Postprocessing script classifies completed U1, copied U2, and visualization
  states after the run.

## Target Counts

- Target physical elements: `72`
- Target element/IP pairs: `152`
- Prior insufficient-output event rows covered: `817`
- Prior staggered-sync event rows covered: `480`

## Requested Resources

- Queue: `entry_imfdfkmq`
- Select: `1:ncpus=1:mem=32gb`
- Walltime: `24:00:00`
- Modules: `gcc/11.4.0`, `intel/2024.2.0`, `abaqus/2023`
- PBS notification points: `#PBS -m abe`; recipient supplied privately with
  `qsub -M "pr21vyci@mailserver.tu-freiberg.de" -m abe`.

## Technical Acceptance

`molnar_v2_sdv15_diagnostic_technical_pass` requires Abaqus return code zero,
ODB/STA/MSG/DAT present, and `THE ANALYSIS HAS COMPLETED SUCCESSFULLY` in the
STA file. Otherwise classify `molnar_v2_sdv15_diagnostic_technical_fail` and do
not submit a retry.

## Diagnostic And Non-Intrusiveness Criteria

Possible diagnostic classifications are `sdv15_completed_state_monotone`,
`sdv15_completed_state_possible_violation`,
`sdv15_diagnostic_output_incomplete`, and
`diagnostic_instrumentation_intrusive`.

The diagnostic evidence is scientifically usable only if the physical response
matches candidate v2 within the documented RF-U and crack-path limits.

## Authorization Scope

Authorized: exactly one serial targeted-output SDV15 diagnostic HPC submission
after passing preflight.

Not authorized: retry, second diagnostic run, candidate v3, multi-CPU execution,
mesh-size/length-scale/load-increment studies, MISESERI, remeshing, state
transfer, or parameter sweeps.

## Submitted Run 1375020.mmaster02

- Submission time: `2026-07-16T12:21:59+0200`.
- Repository revision: `efd5f60ebb9cc6ea8ce89b508a6e9df4183e5611`.
- PBS job: `1375020.mmaster02`.
- Scheduler state: `F`.
- Queue: `normal_imfdfkmq`.
- Execution host: `mnode098/0`.
- Requested resources: `select=1:ncpus=1:mem=32gb`, `walltime=24:00:00`.
- Mail settings verified by PBS: `Mail_Users = pr21vyci@mailserver.tu-freiberg.de`; `Mail_Points = abe`.
- PBS exit status: `3`.
- Classification: `molnar_v2_sdv15_diagnostic_technical_fail`.
- Failure point: pre-solver revision guard; `git` was unavailable in the batch
  job PATH, so `CURRENT_REVISION` was empty and the script exited with
  `revision_mismatch current= requested=efd5f60ebb9cc6ea8ce89b508a6e9df4183e5611`.
- Abaqus status: not launched; no ODB/STA/MSG/DAT diagnostic solver outputs were
  produced.
- Retry authorization: none.

Evidence is under
`runs/hpc/paper_matched_single_notch_v2_sdv15_diagnostic/evidence/1375020.mmaster02/`.
