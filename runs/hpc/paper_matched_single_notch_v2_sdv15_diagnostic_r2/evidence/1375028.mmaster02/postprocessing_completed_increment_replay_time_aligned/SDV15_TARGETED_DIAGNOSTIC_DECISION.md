# SDV15 Targeted Diagnostic Decision

PBS wrapper classification: `postprocess_python_compatibility_failure_after_successful_solve`

Abaqus classification: `molnar_v2_sdv15_diagnostic_r2_technical_pass`

Diagnostic instrumentation: `non_intrusive_pass` if the RF-U comparison remains
within the documented limit; see `sdv15_targeted_diagnostic_metrics.json`.

Scientific evidence: `sdv15_call_level_nonmonotonicity_observed`

Completed/converged increment classification: `sdv15_completed_increment_possible_violation`

This decision is generated from a no-solution replay of the existing diagnostic
trace. It keeps only the last U1 stage-101 call for each `(KSTEP, KINC,
physical element, source-storage IP)` before checking monotonicity. Gate A3
remains `reference_data_insufficient`; this diagnostic does not authorize a
new PBS/Abaqus submission.

## Counts

- Trace rows: `627304`
- U1 stage-101 call rows: `209152`
- Final increment states: `101840`
- Element/IP sequences: `152`
- Unique completed-increment SDV15 violating transitions: `2184`
- Event reclassification counts: `{'sdv15_completed_increment_possible_violation': 62, 'sdv15_completed_increment_monotone': 1235}`
- SDV16 decreases over completed-increment sequences: `0`
- RF-U max normalized difference: `6.54442468761e-13`
