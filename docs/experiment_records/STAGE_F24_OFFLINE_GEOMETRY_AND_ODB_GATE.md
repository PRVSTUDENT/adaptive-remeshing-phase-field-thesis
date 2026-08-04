# Experiment Record: Stage F24 Offline Geometry and ODB Compatibility Gate

Protocol version: 1
Task ID: `F24-OFFICIAL-ADAPTIVE-CONTRACT-AND-ODB-COMPATIBILITY-GATE`
Date: 2026-08-04
Agent: gemini-antigravity
Starting revision: `9d80dd5a9fb36a99045c7ccd974f7e30562a978a`

## 1. Objective

Resolve the remaining F23 uncertainty by establishing the official Abaqus geometry-backed remeshing contract and auditing source ODB `M2MISER1.odb` compatibility.

## 2. Abaqus Adaptive Remeshing Contract Summary

1. Adaptive remeshing cannot operate on orphan-mesh models.
2. Models must contain native geometry and an initial mesh.
3. `Part2DGeomFrom2DMesh` geometry part must be instantiated in `rootAssembly`.
4. Orphan-mesh instance must be suppressed/removed from active target.
5. `RemeshingRule` must target actual geometry faces or cells.
6. Explicit face `Region` must be used instead of `region=MODEL`.
7. Instance name `Part-1-1` must be preserved on geometry instance.
8. `rootAssembly.regenerate()` must be called.
9. No separate `AdaptivityProcess` for manual remeshing.
10. Single remesh route: `Model.adaptiveRemesh(odb)`.
11. Zero fallback routes.

## 3. ODB Compatibility Audit Results

- **Source ODB**: `M2MISER1.odb` (SHA-256: `bfcdbec08669774a9f80939d67c9c86ffe7df707e760450b08b1f6073fc588ac`)
- **Compatibility Status**: Incompatible for direct remeshing of the geometry-backed model. `M2MISER1.odb` contains orphan mesh element output without native geometry face regions.
- **Scientific Resolution**: Outcome B is selected. `M2RMPROV1` is prepared to execute a provisional Abaqus/Standard analysis on the geometry-backed model, generating a matching ODB.

## 4. Prepared Deliverables

- **Prepared Job**: `M2RMPROV1` (Abaqus/Standard analysis)
- **Input Deck**: `models/generated/mode_ii/f24_geometry_and_odb_compatibility_gate/M2RMPROV1.inp`
- **PBS Script**: `models/generated/mode_ii/f24_geometry_and_odb_compatibility_gate/M2RMPROV1.pbs`
- **Orchestrator**: `scripts/hpc/stage_f/submit_stage_f24_provisional_analysis.sh`
- **Classification**: `f24_m2rmprov1_clean_linux_qualified_not_authorized`

## 5. Execution Boundary Audit

- `execution_authorized = false`
- `submission_approved = false`
- `approved_submissions_now = 0`
- `maximum_jobs_now = 0`
- `qsub_attempts = 0`
- `successful_submissions = 0`
- `m2rmexec2_prepared = false`
