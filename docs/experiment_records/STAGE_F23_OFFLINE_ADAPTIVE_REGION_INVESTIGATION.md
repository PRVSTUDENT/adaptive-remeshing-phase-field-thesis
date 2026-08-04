# Stage F23 Offline Adaptive Region Investigation Report

Protocol version: 1
Date: 2026-08-03
Task ID: `F23-OFFLINE-ADAPTIVE-REGION-ASSOCIATION-INVESTIGATION`
Starting commit: `8ef3cdddbeb249b90458f27968e505e6de4967d2`

## 1. Overview and Purpose

This task performed a strictly offline forensic investigation of why F20 (`M2RMREG7`, Job `1382428.mmaster02`) classified `native_adaptive_region_contract_qualified` while F21 (`M2RMEXEC1`, Job `1382435.mmaster02`) failed at `Model.adaptiveRemesh(odb)` with:
`AbaqusException: The model contains no adaptive regions for remeshing.`

No SSH, scheduler access, Abaqus execution, datacheck, solver, or candidate generation was performed.

## 2. Workstream A — F20 vs F21 Implementation & Evidence Comparison

Detailed comparison of the F20 and F21 implementations:
- **Model Creation & Deck Import**: Both jobs created models using `mdb.ModelFromInputFile` importing `source_deck.inp` (3,930 CPE4 elements).
- **Part Reconstruction**: Both created a geometry-backed part (`F20_GEOMETRY_BACKED` / `F21_GEOMETRY_BACKED`) using `Part2DGeomFrom2DMesh`.
- **Assembly State**: In both models, `rootAssembly` retained only the original orphan mesh instance (`PART-1-1`). The newly reconstructed geometry part was never instantiated in `rootAssembly`.
- **Rule Definition**: Both created `RemeshingRule(name='F20_MISESERI_RULE', stepName='Step-1', variables=(str('MISESERI'),), region=MODEL)`.
- **Execution Divergence**: F20 evaluated qualification purely via python checks: checking `rule.region is not None` (which returned True for `MODEL`). F20 never called `Model.adaptiveRemesh(odb)`. F21 called `Model.adaptiveRemesh(odb)` on the identical model state. Abaqus raised `AbaqusException: The model contains no adaptive regions for remeshing.`.
- **Conclusion**: The existence of a `RemeshingRule` in `model.remeshingRules` with `region=MODEL` does not create a recognized adaptive region in Abaqus.

## 3. Workstream B — Contract Hypotheses & Evidence Evaluation

Four hypotheses were evaluated against committed evidence:
1. **Hypothesis 1**: Geometry-backed part must replace orphan instance in `rootAssembly`. (Status: Plausible, unproven offline without CAE execution).
2. **Hypothesis 2**: `RemeshingRule` region must target geometry Face/Cell region or Set, not symbolic `MODEL`. (Status: Plausible, unproven offline without CAE execution).
3. **Hypothesis 3**: An `AdaptivityProcess` object must be registered in `mdb.adaptivityProcesses`. (Status: Plausible, unproven offline without CAE execution).
4. **Hypothesis 4**: `RemeshingRule` alone is sufficient. (Status: Rejected by F21 evidence).

Because 3 plausible hypotheses remain unverified without Abaqus CAE execution, **Outcome B (`adaptive_region_association_unresolved_offline`) is selected**.

## 4. Evidence-Retention Repairs

The F21 evidence retention defect was audited and repaired:
- `SOURCE_MESH_SUMMARY.json` was missing in F21 when `adaptiveRemesh` failed prior to mesh export.
- Future wrappers must ensure `SOURCE_MESH_SUMMARY.json`, `compatibility.returncode`, `cae.returncode`, `collector.returncode`, `first_failure.returncode`, `MISSING_EVIDENCE_REPORT.json`, `NATIVE_REMESH_TRACEBACK.txt`, and pre-call adaptive-region audit are retained on all exit paths.
- `collector.returncode` must not mask `cae.returncode`.

## 5. Offline Testing & Verification

All offline tests were implemented in `tests/stage_f/test_f23_adaptive_region_investigation.py` and `scripts/validation/validate_f23_adaptive_region_investigation.py`.

Test suite covers:
- F20/F21 contract comparison
- Zero recognized adaptive-region detection
- Positive pre-call recognition audit specification
- Pre-call failure behavior
- Rule existence not treated as region recognition
- Retention of `SOURCE_MESH_SUMMARY`, collector return codes, missing-file reporting
- Preservation of original CAE return code
- Zero solver/datacheck/state-transfer/refined-analysis calls
- Python-2-compatible Abaqus script structures
- JSON parsing, shell syntax, canonical text, manifest validation, bootstrap validation

## 6. Final State & Classification

- Classification: `f23_adaptive_region_association_unresolved_no_job_prepared`
- `m2rmexec2_prepared`: false
- `execution_authorized`: false
- `submission_approved`: false
- `approved_submissions_now`: 0
- `maximum_jobs_now`: 0
- `qsub_attempts`: 0
