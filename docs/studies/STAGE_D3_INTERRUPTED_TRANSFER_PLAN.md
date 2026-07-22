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

## D3A0/D3A1 Source Audit Outcome

The existing accepted H0 ODB from job `1376154.mmaster02` was audited as a
candidate source. It has the required Molnar single-notch geometry, `0.5 mm`
notch, `lc=0.015 mm`, 3930 physical elements, known deck/source hashes, RF-U
history, and SDV15/SDV16 state output.

The corrected CAE/ODB-only extraction attempt `1376879.mmaster02` selected the
frame at `U2=0.003000000026077032 mm` without state interpolation. It extracted
15720 element/IP rows with `target_ip_coverage=1.0`, `max_d=0.08412302285432816`,
`max_H=0.0512588769197464`, checkpoint `RF2=0.39450356364250183`, and
`RF2/H0_peak=0.5421925638518931`.

D3A is nevertheless not accepted. The original H0 deck did not request
`ALLIE`, `ALLSE`, or `ALLWK`, so checkpoint energy values are absent. The
correct classification is
`stage_d3a_checkpoint_blocked_missing_energy_history`, and no `D3A.ok` marker
exists. D3A2 package construction must not proceed from this non-accepted
checkpoint.
