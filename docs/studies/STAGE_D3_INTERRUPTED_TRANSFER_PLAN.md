# Stage D3 Interrupted Fracture-Transfer Plan

Status: `stage_d3_design_prepared_not_submitted`

D3 is design-only until D2D ABAQUSER verification either passes or is formally
accepted as externally blocked. No new fracture solver job is authorized by this
plan.

## Purpose

Test whether a fracture-relevant state can be interrupted before peak load,
transferred to a nonmatching mesh, and continued without introducing artificial
force, energy, phase-field, or history discontinuities.

## Initial Scope

- Model family: small H0 diagnostic Molnar single-notch model.
- Checkpoint: early pre-peak, provisionally `U_checkpoint = 0.003 mm`.
- Transfer fields: phase `d` and history `H`.
- Target mesh: nonmatching diagnostic mesh, smaller than H1/refined-v3.
- First run type: package preparation and validation only.
- Not authorized: H1, refined-v3, peak-load, post-peak, or production fracture
  transfer submissions.

## Proposed Workflow

1. Extract checkpoint state from an existing or future H0 diagnostic ODB.
2. Build a nonmatching target transfer package for `d` and `H`.
3. Validate coverage, bounds, monotonicity, and field continuity before any
   continuation job is submitted.
4. After D2D is resolved, submit one small continuation only if explicitly
   authorized.

## Predeclared Metrics

| Metric | Purpose |
| --- | --- |
| RF jump at transfer | detects mechanical discontinuity |
| RF-U continuity | checks load path continuity through restart/transfer |
| SDV15 L2/max error | phase output transfer accuracy |
| SDV16 L2/max error | history output transfer accuracy |
| no-healing violations | enforces `d_new >= d_old` where comparable |
| history monotonicity violations | enforces `H_new >= H_old` |
| energy jump | detects artificial stored/work energy discontinuity |
| peak-force difference | compares continued transfer against uninterrupted reference |
| peak-displacement difference | compares peak location against uninterrupted reference |
| crack-path distance | checks fracture trajectory distortion |
| unmapped state count | proves transfer coverage |

## Current Boundary

D3 preparation may create configuration, extraction, packaging, and validation
code. It must not submit or run a new fracture Abaqus/Standard job until D2D is
passed or formally documented as externally blocked and the next solver step is
explicitly authorized.
