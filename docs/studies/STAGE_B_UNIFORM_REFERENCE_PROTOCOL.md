# Stage B Uniform-Reference Study Protocol

Status: `h_convergence_subset_authorized_execution_pending`

Gate A3 remains `reference_data_insufficient`. The route-neutral Stage B
planning package is preserved. The supervisor has approved only a controlled
**h-convergence subset** for execution. Length-scale sensitivity,
load-increment sensitivity, MISESERI, adaptive remeshing, and state transfer
remain unauthorized.

## Current Boundary

```text
Candidate v2: paper_matched_v2_technical_pass
Scientific status: paper_matched_v2_scientific_review_incomplete
Irreversibility: sdv15_completed_increment_irreversibility_violation
Gate A3: reference_data_insufficient
Supervisor decision: controlled h-convergence study authorized
Authorized subset: H0 exact supplementary; H1 h=0.0025 mm; H2-PUB h=0.001 mm
Study family: molnar_single_notch_lc015_h_convergence
lc for authorized subset: 0.015 mm (exact supplementary model)
Not authorized: length-scale study; load-increment study; MISESERI;
adaptive remeshing; state transfer; multi-CPU; GPU; formulation changes;
automatic retries; fourth mesh level
```

## Supervisor-Approved Execution Subset

Supervisor decision: proceed with a controlled h-convergence study including:

1. the exact author-supplied supplementary model (H0);
2. intermediate mesh refinement (H1, local target `h = 0.0025 mm`);
3. the publication-reported crack-path resolution (H2-PUB, local target
   `h = 0.001 mm`).

User authorization: prepare, validate, commit, push, synchronize, and submit
exactly three serial HPC jobs for H0, H1, and H2-PUB once. No fourth mesh,
retry, duplicate job, or automatic resubmission is authorized.

Detailed executable protocol:

- `docs/studies/MOLNAR_LC015_H_CONVERGENCE_PROTOCOL.md`
- `docs/studies/MOLNAR_LC015_H_CONVERGENCE_ACCEPTANCE.md`
- `configs/studies/molnar_lc015_h_convergence.yaml`

## Purpose

Stage B establishes a uniform fine reference before any MISESERI
pre-refinement or adaptive-remeshing claim. The study must answer:

- which uniform mesh is sufficiently converged for the selected benchmark;
- how sensitive the result is to length scale;
- how sensitive the result is to load increment;
- whether RF--displacement, crack-path, SDV, runtime, and memory evidence are
  complete enough to become the comparison target for later refined meshes.

## Required Study Sequence

1. Mesh convergence.
2. Length-scale sensitivity.
3. Load-increment sensitivity.
4. Uniform fine-reference selection.
5. MISESERI pre-refinement comparison.
6. Evolving remeshing only after the earlier stages pass.

The uniform fine reference must be selected before any MISESERI or
adaptive-remeshing result is described as accurate.

## Supervisor Decision Routes

| Route | Stage B mesh convergence | Length-scale study | Load-increment study | MISESERI/remeshing |
|---|---|---|---|---|
| Candidate v2 accepted with limitation | permitted after explicit run authorization | permitted after mesh trend is reviewed | permitted after mesh trend is reviewed | blocked until uniform fine reference is selected |
| Gate A3 waiver granted | permitted, but reports must state the irreversibility limitation | permitted under the waiver scope | permitted under the waiver scope | blocked until uniform fine reference is selected |
| Corrected formulation required | not permitted for candidate v2 | not permitted for candidate v2 | not permitted for candidate v2 | blocked |
| Candidate v2 rejected | not permitted | not permitted | not permitted | blocked |

Each future HPC run still requires explicit user authorization.

## Study Factors

### Mesh Levels

Mesh levels are named now, but final numerical sizes must be approved after the
supervisor decision. The only committed mesh value available today is the
candidate-v2 local refined-zone size `h = 0.001 mm` with `l = 0.0075 mm`,
giving local `h/l = 0.1333333333`; candidate v2 is graded, not a uniform
Stage B mesh.

| Level | Meaning | Numerical policy |
|---|---|---|
| `U0` | current candidate-v2 reference reconstruction and extraction baseline | existing committed evidence only; not a new uniform run |
| `U1` | moderately refined uniform mesh | provisional size to be selected from geometry, cost estimate, and supervisor-approved `h/l` target |
| `U2` | fine uniform mesh | provisional size to be selected after `U1` technical/resource review |
| `U3` | optional confirmation mesh | run only if `U1 -> U2` changes do not establish convergence |

Candidate provisional planning targets are recorded in
`configs/studies/molnar_uniform_reference_matrix.yaml`, but they are not final
mesh sizes or run authorization.

### `h/l` Values

Use `h/l` as the primary mesh-resolution label. The current committed
candidate-v2 local value is:

```text
h/l = 0.001 / 0.0075 = 0.1333333333
```

For Stage B, proposed `h/l` values must be labeled provisional until the
supervisor confirms whether candidate v2, a waiver route, or a corrected
formulation is used.

### Length-Scale Cases

| Case | Meaning | Permission |
|---|---|---|
| `L0` | current length scale `l = 0.0075 mm` | only after Stage B is authorized |
| `L1` | smaller supervisor-approved alternative | only after mesh convergence at `L0` is reviewed |
| `L2` | larger supervisor-approved alternative | only after mesh convergence at `L0` is reviewed |

No final numerical `L1` or `L2` value is assigned here.

### Load-Increment Cases

| Case | Meaning | Permission |
|---|---|---|
| `I0` | current candidate-v2 schedule: `1e-5 mm` increments, 500 increments in Step 1 and 170 in Step 2 | only after Stage B is authorized |
| `I1` | smaller-increment confirmation level | only after mesh convergence is reviewed |
| `I2` | optional stricter increment confirmation level | only if `I1` changes the post-peak or SDV result materially |

No final numerical `I1` or `I2` value is assigned here.

## Run Order After Authorization

1. `U0_L0_I0`: no new run; collect current candidate-v2 evidence as the
   reference reconstruction baseline.
2. `U1_L0_I0`: first authorized uniform mesh.
3. Review `U1` technical status, RF--U curve, crack path, SDV checks, walltime,
   and memory before proceeding.
4. `U2_L0_I0`: second authorized uniform mesh.
5. Decide whether `U3_L0_I0` is needed. Run it only if convergence remains
   unclear and resources permit.
6. Run `L1` and `L2` length-scale cases only after the uniform mesh policy at
   `L0` is selected.
7. Run `I1` and optional `I2` only after length-scale decisions are stable.
8. Select the uniform fine reference.
9. Only after reference selection, design the MISESERI pre-refinement
   comparison.

## Convergence Metrics

Every completed Stage B run must report:

- technical status and solver completion;
- peak RF2 and displacement at peak;
- final RF2 and displacement;
- pre-peak, post-peak, and full-overlap RF--U errors against the selected
  comparison curve;
- area-under-curve difference;
- crack extension and connected-component metrics at declared `SDV15`
  thresholds;
- SDV15 bound and monotonicity results;
- SDV16 monotonicity result;
- walltime, CPU time, memory, virtual memory, equation count, increments, and
  iterations.

Acceptance thresholds remain provisional until supervisor-approved. The
selected reference should be the coarsest uniform mesh whose changes relative
to the next finer accepted mesh are small under the approved metrics.

## RF--Displacement Comparison Rules

- Extract top reference-point `U2` and total `RF2`.
- Preserve sign convention and units.
- Interpolate candidate and comparison curves onto a common displacement grid.
- Report pre-peak and post-peak metrics separately.
- Do not treat approximate digitized Molnar Fig. 7 data as exact author data.
- Keep comparisons between Stage B mesh levels separate from comparisons to
  the published figure.

## Crack-Path Comparison Rules

Compute crack metrics using visualization-layer element-mean `SDV15`.

Required thresholds:

```text
0.50, 0.80, 0.90, 0.95, 0.99
```

Report damaged element count, connected component count, largest component
count, connected extension beyond the notch tip, total connected damaged path,
furthest connected `x`, maximum vertical deviation, mean vertical deviation,
and disconnected high-damage elements.

## SDV15 and SDV16 Checks

Required checks:

- `0 <= SDV15 <= 1` bound check, with overshoot reported separately;
- retained-frame SDV15 decrease scan;
- completed-increment SDV15 monotonicity check when targeted/final-increment
  data are available;
- counts above `1e-8`, `1e-6`, and `1e-5`;
- worst SDV15 decrease and location;
- SDV16 decrease count over the same locations/sequences.

If the supervisor requires strict pointwise irreversibility, any
completed-increment SDV15 decrease above the approved materiality tolerance is
a scientific stop. If candidate v2 is accepted with limitation or waived, the
SDV15 limitation must remain visible in every report.

## Runtime and Memory Estimates

Use candidate-v2 job `1374864.mmaster02` as the current calibration point:

- physical elements: `33852`;
- layered elements: `101556`;
- equations: `102975`;
- increments: `670`;
- walltime: `00:38:38`;
- CPU time: `00:35:52`;
- used memory: `2970760kb`;
- virtual memory: `3565868kb`;
- Abaqus peak memory: about `2 GB`.

Future uniform meshes may scale differently from candidate-v2 because the
candidate mesh is graded. Estimates must be updated after each completed run.

## Stop Criteria

Stop before the next run if:

- Abaqus does not complete normally;
- PBS exit/stage-out or evidence preservation is ambiguous;
- required extraction artifacts are missing;
- solver errors are nonzero;
- SDV16 decreases;
- SDV15 violates the selected supervisor route;
- post-peak RF--U behavior changes implausibly;
- walltime or memory exceeds 75 percent of the request;
- predicted next-level resources exceed the approved compute envelope.

## Evidence Directory and Naming

Use deterministic run IDs:

```text
runs/hpc/stage_b_uniform_reference/
  molnar_sn__uniform__U1__L0__I0__<YYYYMMDD-HHMM>/
```

Each run directory should contain:

- `RUN_MANIFEST.md`
- `RUN_SUMMARY.md`
- input and source hashes;
- initial and final scheduler records;
- technical summary;
- lightweight solver logs;
- extracted RF--U data;
- response-state contour CSVs;
- RF--U, crack-path, SDV, and resource review files.

Large ODB, restart, scratch, and raw trace files remain out of Git unless the
user explicitly approves a retention plan.
