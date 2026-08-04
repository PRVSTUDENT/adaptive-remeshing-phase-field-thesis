# F23 Adaptive-Region Association Decision

Protocol version: 1
Date: 2026-08-03
Task ID: `F23-OFFLINE-ADAPTIVE-REGION-ASSOCIATION-INVESTIGATION`
Starting commit: `8ef3cdddbeb249b90458f27968e505e6de4967d2`

## Executive Summary

Job `1382435` (`M2RMEXEC1`, F21) failed at `Model.adaptiveRemesh(odb)` with:
`AbaqusException: The model contains no adaptive regions for remeshing.`

An offline comparison between F20 (`M2RMREG7`) and F21 (`M2RMEXEC1`) established that F20 classified `native_adaptive_region_contract_qualified` based solely on `RemeshingRule` creation and checking that `rule.region is not None` (`region=MODEL`). F20 never called `Model.adaptiveRemesh(odb)`. When F21 called `Model.adaptiveRemesh(odb)` on the identical model state, Abaqus scanned the model assembly for active geometry regions bound to remeshing rules and found 0 recognized adaptive regions.

Three plausible association hypotheses remain for enabling region recognition in Abaqus:
1. Replaces orphan mesh instance `PART-1-1` in `rootAssembly` with geometry part `F21_GEOMETRY_BACKED` created by `Part2DGeomFrom2DMesh`.
2. Assigning `RemeshingRule` region to specific assembly/part geometry faces (`Region(faces=...)`) rather than symbolic `MODEL`.
3. Registering an `AdaptivityProcess` in `mdb.adaptivityProcesses`.

Under the task decision gate rules, Outcome A requires exactly one proven API route and association supported by positive offline proof. Because Abaqus CAE execution is strictly prohibited in this offline task and multiple plausible hypotheses remain unverified, **Outcome B (`adaptive_region_association_unresolved_offline`) is selected**.

No HPC job (`M2RMEXEC2`) is prepared or authorized.

## Comparative Evidence Matrix

| Property | F20 (`M2RMREG7`) | F21 (`M2RMEXEC1`) | Difference / Finding |
|---|---|---|---|
| Model Construction | `ModelFromInputFile` | `ModelFromInputFile` | Identical import from `source_deck.inp` |
| Geometry Part Creation | `Part2DGeomFrom2DMesh` | `Part2DGeomFrom2DMesh` | Identical uninstantiated part in `m.parts` |
| Assembly Instances | `PART-1-1` (orphan mesh) | `PART-1-1` (orphan mesh) | Neither replaced instance with geometry part |
| RemeshingRule Region | `MODEL` | `MODEL` | Identical symbolic constant `MODEL` |
| `model.adaptiveRemesh(odb)` | Not invoked | Invoked | F20 audited rule; F21 executed call |
| Qualification Result | `contract_qualified` | `execution_failed` | F20 checked rule existence; F21 executed call |

## Pre-Call Recognition Audit & Evidence Retention Requirements

Any future native remeshing implementation MUST:
1. Perform a deterministic pre-call audit verifying `recognized_adaptive_region_count > 0` before calling `Model.adaptiveRemesh(odb)`.
2. Fail closed immediately if `recognized_adaptive_region_count == 0` without invoking fallback routes.
3. Retain `SOURCE_MESH_SUMMARY.json`, `compatibility.returncode`, `cae.returncode`, `collector.returncode`, `first_failure.returncode`, `MISSING_EVIDENCE_REPORT.json`, and `NATIVE_REMESH_TRACEBACK.txt` on every exit path.
4. Ensure `collector.returncode` does not mask `cae.returncode`.

## Authority Status

- `execution_authorized`: false
- `submission_approved`: false
- `m2rmexec2_prepared`: false
- `approved_submissions_now`: 0
- `maximum_jobs_now`: 0
- `qsub_attempts`: 0
