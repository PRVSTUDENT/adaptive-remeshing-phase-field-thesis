# Molnar v2 SDV15 Targeted Diagnostic r2 Run Summary

Status: `completed_with_postprocess_replay`

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

## Completion Review

Post-completion review was performed without submitting a new PBS/Abaqus job.
PBS history for `1375028.mmaster02` reports `job_state = F`,
`Exit_status = 1`, `Stageout_status = 1`, and walltime `00:42:27` on
`mnode100/0`. The nonzero PBS exit is a wrapper/postprocessing failure after
the successful solve: the staged postprocessor used Python-3.9-style built-in
generic annotations that the cluster postprocessing interpreter could not
parse.

Abaqus itself is a technical pass. The retained evidence records
`abaqus_return_code.txt = 0`, `technical_classification.txt =
molnar_v2_sdv15_diagnostic_r2_technical_pass`, the `.sta` file contains
`THE ANALYSIS HAS COMPLETED SUCCESSFULLY`, and the `.msg` summary reports zero
analysis error messages.

The diagnostic instrumentation is non-intrusive by independent RP-node RF--U
comparison at node `34508`: `202` matched frames, maximum normalized RF2
difference `6.54442468760855e-13`, and maximum U2 difference
`4.992967844730245e-15 mm`.

## Completed-Increment Replay

A no-solution replay of the existing `627304` trace rows was run under Abaqus
Python after replacing the postprocessor logic with a final-increment
classifier. The replay keeps only the last U1 stage-101 call for each
`(KSTEP, KINC, physical element, source-storage IP)`, aligns retained-frame
events by step time/load level, and compares only consecutive final increment
states.

Replay result:

- call-level scientific evidence:
  `sdv15_call_level_nonmonotonicity_observed`;
- completed/converged increment classification:
  `sdv15_completed_increment_possible_violation`;
- U1 stage-101 call rows: `209152`;
- final increment states: `101840`;
- element/IP sequences: `152`;
- unique completed-increment SDV15 violating transitions: `2184`;
- original event-table replay categories: `62`
  `sdv15_completed_increment_possible_violation`, `1235`
  `sdv15_completed_increment_monotone`;
- SDV16 decreases over the same final-increment sequences: `0`;
- largest completed-increment phase drop: `0.00022384088238425193` at
  `(physical_element=16428, source_storage_ip=4, KSTEP/KINC 2/143 -> 2/144)`;
- worst retained visualization event `84131 -> physical 16427` is monotone for
  the inspected converged-increment transitions in
  `worst_event_84131_16427_converged_increment_check.csv`.

## Severity Audit

A no-solution severity audit of the 2184 completed-increment decreasing
transitions classified the SDV15 result as:

```text
sdv15_completed_increment_irreversibility_violation
```

The audit uses a provisional materiality tolerance of `1e-6`. Results:

- maximum decrease: `0.00022384088238425193`;
- mean decrease: `2.8434597987446906e-05`;
- median decrease: `1.3940791172561973e-05`;
- tolerance sensitivity: `2184` transitions above `1e-10`, `2184` above
  `1e-8`, `2131` above `1e-6`, and `1362` above `1e-5`;
- magnitude bins: `53` in `(1e-8,1e-6]`, `769` in `(1e-6,1e-5]`, `1265` in
  `(1e-5,1e-4]`, and `97` above `1e-4`;
- unique affected element/IP locations: `138`;
- all `2184` transitions occur after peak displacement;
- `773` transitions coincide with SDV15 overshoot above one;
- `0` SDV16 decreases occur over the same transitions;
- largest transition: physical element `16428`, source-storage IP `4`,
  `KSTEP/KINC 2/143 -> 2/144`, `U2 = 0.006694117647058817 mm`, centroid
  `(0.0015, -0.00050000035)`, decrease `0.00022384088238425193`.

## Boundary

No second r2 submission, automatic retry, candidate v3, Stage B run, MISESERI,
remeshing, state-transfer run, parameter sweep, multi-CPU execution, or
scientific-model change is authorized by this record.

## Evidence

- `evidence/1375028.mmaster02/SUBMISSION_RECORD.txt`
- `evidence/1375028.mmaster02/QSTAT_INITIAL.txt`
- `evidence/1375028.mmaster02/PROJECT_REVISION.txt`
- `evidence/1375028.mmaster02/STAGING_MANIFEST.txt`
- `evidence/1375028.mmaster02/postprocessing_completed_increment_replay_time_aligned/SDV15_TARGETED_DIAGNOSTIC_DECISION.md`
- `evidence/1375028.mmaster02/postprocessing_completed_increment_replay_time_aligned/sdv15_targeted_diagnostic_metrics.json`
- `evidence/1375028.mmaster02/postprocessing_completed_increment_replay_time_aligned/sdv15_completed_increment_violating_transitions.csv`
- `evidence/1375028.mmaster02/postprocessing_completed_increment_replay_time_aligned/sdv15_event_completed_increment_reclassification.csv`
- `evidence/1375028.mmaster02/postprocessing_completed_increment_replay_time_aligned/worst_event_84131_16427_converged_increment_check.csv`
- `evidence/1375028.mmaster02/postprocessing_completed_increment_replay_time_aligned/PROVENANCE.md`
- `evidence/1375028.mmaster02/postprocessing_completed_increment_replay_time_aligned/severity_audit/SDV15_COMPLETED_INCREMENT_SEVERITY_AUDIT.md`
- `evidence/1375028.mmaster02/postprocessing_completed_increment_replay_time_aligned/severity_audit/sdv15_completed_increment_severity_summary.json`

Gate A3 remains `reference_data_insufficient`.
