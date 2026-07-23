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

D3A required independent energy evidence because the original H0 deck did not
request `ALLIE`, `ALLSE`, or `ALLWK`, so checkpoint global energy history is
absent. That absence is preserved as the original D3A blocker, but it is now
resolved by the scope-corrected D3A-E R1 reconstruction described below.

## D3A-E Energy Reconstruction Outcome

D3A-E authorized independent quadrature-based energy reconstruction rather than
rerunning the H0 fracture model merely to request global Abaqus energy output.
R0 job `1376885.mmaster02` is preserved as failed evidence with classification
`stage_d3a_energy_reconstruction_fail_parser_scope`: the first parser read
`Part-1` mesh nodes and assembly reference-point nodes into one namespace.

R1 corrected the parser scope and passed with classification
`stage_d3a_energy_reconstruction_pass`. It retains 3930 physical elements and
15720 integration points, reports non-positive detJ count `0`, minimum detJ
`2.829135024804933e-06`, and relative energy residual
`0.012586306767288707`.

D3A is now closed as
`stage_d3a_checkpoint_pass_independent_energy_reconstruction`. Evidence is
under `runs/hpc/stage_d3/interrupted_transfer/checkpoint_energy_r1/`, and the
accepted marker is `runs/hpc/stage_d3/interrupted_transfer/checkpoint/D3A.ok`.
D3A2 package construction may proceed locally; no fracture solver job may be
submitted before `D3_PACKAGE.ok`.

## D3A2 Nonmatching Package Outcome

D3A2 built one deterministic nonmatching split-notch target package locally
without PBS submission. The accepted package classification is
`stage_d3a2_transfer_package_pass` from source job `1376154.mmaster02` at
checkpoint `U2=0.003000000026077032 mm`.

The target has 6601 nodes, 6400 Q4 physical elements, and 25600 target
integration points. The split-notch topology audit passed: the open notch runs
from `x=-0.5` to `x=0.0` on `y=0`, has 40 duplicated coincident open-face node
pairs, keeps the notch tip shared, has notch length `0.5`, and has zero
elements crossing the open notch faces. The target mesh has non-positive detJ
count `0`.

The transfer package reports target-node coverage `1.0`, target-IP coverage
`1.0`, predicted energy relative jump `0.015379624558651227`, unmapped state
count `0`, and `solver_job_submitted=false`. Evidence is under
`runs/hpc/stage_d3/interrupted_transfer/package/`, with marker `D3_PACKAGE.ok`.
D3A3-R2 is now prepared only as a compile/datacheck gate. R2 preserves the R0
and R1 evidence directories unchanged and uses
`runs/hpc/stage_d3/interrupted_transfer/target_ingestion_compile_r2/` for the
compile/datacheck evidence. It replaces the oversized compile-time
`d3_transfer_table.inc` path with a headerless runtime `d3_transfer_h.dat`
loaded once through `UEXTERNALDB`. Local validation passed for 25600 H records
with SHA256 `4689ea5c10c0972e69ba46f8676a326c8b011b98faa8031c7c26cfb218607cd9`.

The R2 compile/datacheck submission was job `1377389.mmaster02`. Abaqus
compiled and linked the user subroutine and completed input processing, so the
R1 compile-token problem was removed. Standard datacheck then failed when
`UEXTERNALDB` opened relative file `d3_transfer_h.dat` from Abaqus' internal
`/local/...` work directory where that file had not been staged. The preserved
classification is
`stage_d3a3_r2_datacheck_fail_runtime_h_file_not_in_abaqus_workdir`; evidence
is under `runs/hpc/stage_d3/interrupted_transfer/target_ingestion_compile_r2/`.
Full D3A3-R2, D3D, and D3E remain blocked until a follow-up compile/datacheck
creates and commits `D3A3_R2_COMPILE.ok`.
