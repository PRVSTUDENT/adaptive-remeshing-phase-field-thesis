# Molnar v2 SDV15 r2 Completed-Increment Replay Provenance

Job: `1375028.mmaster02`

Submitted revision: `209ad325d2c85532411c13d8290db08ca35b0637`

PBS wrapper result: `postprocess_python_compatibility_failure_after_successful_solve`

Abaqus result: `molnar_v2_sdv15_diagnostic_r2_technical_pass`

## Replay Script

- Path: `scripts/postprocessing/analyze_molnar_sdv15_targeted_diagnostic.py`
- Cluster replay copy: `/tmp/analyze_molnar_sdv15_targeted_diagnostic_replay.py`
- SHA-256: `cfcfea9e3df75889e8f8b16633690b216da89954dfd66ce0e2059f4a274726d9`
- Abaqus Python: `2.7.15 (default, Jul 30 2022, 01:33:15) [GCC 8.2.1 20180905 (Red Hat 8.2.1-3)]`

## Raw Trace

- Path: `/home/pr21vyci/projects/adaptive-remeshing/runs/hpc/paper_matched_single_notch_v2_sdv15_diagnostic_r2/evidence/1375028.mmaster02/molnar_v2_sdv15_diagnostic_call_trace.csv`
- Size: `258449576` bytes
- Modified: `2026-07-16T13:24:09+0200`
- SHA-256: `5b4922884ea6ee7af759c469f69e508106aca8e6d14892520abaffe2120dbed3`
- Storage policy: raw trace is retained in the HPC evidence area; it is not duplicated into Git.

## Selection Rule

The completed-increment replay uses the last U1 stage-101 call for every
`(KSTEP, KINC, physical element, source-storage IP)`.

Retained-frame event rows are aligned to trace increments by step time/load
level, not by raw retained frame number.

Decrease tolerance for completed-increment replay: `1e-8`.

Severity-audit decision tolerance: `1e-6`.

## Validation Results

- U1 stage-101 call rows: `209152`
- Final increment states: `101840`
- Monitored element/IP sequences: `152`
- Unique completed-increment decreasing transitions: `2184`
- SDV16 decreases on the same final-increment transitions: `0`
- Original retained-frame event replay: `62` possible violation, `1235` monotone
- Independent RF-U comparison node: `34508`
- RF-U matched frames: `202`
- RF-U maximum normalized difference: `6.54442468760855e-13`

## Severity Audit

- Script: `scripts/postprocessing/audit_molnar_sdv15_completed_increment_severity.py`
- Script SHA-256: `d0a40dfa5da1b84ef21f335a7e88829fb168857f3470c599093af0bf47b08225`
- Transition table SHA-256: `28d144499398bbe6a25c92767b1c75b02b1341917aa5b4f8fea0ff4f352a6949`
- Result: `sdv15_completed_increment_irreversibility_violation`

Gate A3 remains `reference_data_insufficient`.
