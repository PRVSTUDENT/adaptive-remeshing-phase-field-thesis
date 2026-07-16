# Molnar v2 SDV15 Targeted Diagnostic r2 Run Summary

Status: `submitted_initial_scheduler_record_preserved`

## Submission

- Job ID: `1375028.mmaster02`.
- Job name: `molnar_v2_sdv15_diag_r2`.
- Submission time: `20260716T124140+0200`.
- Preparation revision: `209ad325d2c85532411c13d8290db08ca35b0637`.
- Initial scheduler state: `Q`.
- Queue: `normal_imfdfkmq`.
- Resources: `1` CPU, `32gb` memory, `select=1:ncpus=1:mem=32gb`,
  `walltime=16:00:00`.
- Mail settings verified by `qstat -f`: `Mail_Users =
  pr21vyci@mailserver.tu-freiberg.de`; `Mail_Points = abe`.
- Scratch pre-stage:
  `/scratch/pr21vyci/adaptive-remeshing/prestage/molnar_v2_sdv15_diag_r2_20260716T124140+0200_209ad325d2c8`.
- PBS output directory:
  `/scratch/pr21vyci/adaptive-remeshing/pbs_output/molnar_v2_sdv15_diag_r2_20260716T124140+0200_209ad325d2c8`.
- PBS output path is in scratch with `Join_Path = oe`.

## Scientific Scope

This job is exactly one infrastructure-corrected serial targeted SDV15
diagnostic execution. It uses the already prepared diagnostic variant with:

- target physical elements: `72`;
- target element/IP pairs: `152`;
- deck comparison: `scientific_keyword_equivalence_pass`;
- static validation: `diagnostic_static_validation_pass`;
- runnable flag: `diagnostic_runnable: true`.

The run is intended only to collect completed U1 phase-update evidence for the
817 candidate-v2 SDV15 events previously classified as
`insufficient_output_evidence`.

## Boundary

This checkpoint records submission and initial scheduler acceptance only. It is
not a technical pass, not a scientific pass, and not a Gate A3 closure.

No second r2 submission, automatic retry, candidate v3, Stage B run, MISESERI,
remeshing, state-transfer run, parameter sweep, multi-CPU execution, or
scientific-model change is authorized by this record.

## Evidence

- `evidence/1375028.mmaster02/SUBMISSION_RECORD.txt`
- `evidence/1375028.mmaster02/QSTAT_INITIAL.txt`
- `evidence/1375028.mmaster02/PROJECT_REVISION.txt`
- `evidence/1375028.mmaster02/STAGING_MANIFEST.txt`

Gate A3 remains `reference_data_insufficient`.
