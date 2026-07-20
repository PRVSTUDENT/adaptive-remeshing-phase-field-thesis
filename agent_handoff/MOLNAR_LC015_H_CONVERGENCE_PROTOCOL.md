# Molnar Single-Notch lc = 0.015 mm h-Convergence Protocol

Status: `authorized_for_three_serial_jobs`

Study family: `molnar_single_notch_lc015_h_convergence`

## Authorization Boundary

Supervisor decision: controlled h-convergence study on the exact author-supplied
supplementary single-notch model, including intermediate refinement and the
publication-reported crack-path resolution `h = 0.001 mm`.

User authorization: prepare, validate, commit, push, synchronize, and submit
exactly three serial HPC jobs once:

| Case | Role | Local target h | Target h/lc |
|---|---|---:|---:|
| H0 | exact author-supplied supplementary baseline | 0.005 mm | 0.3333333333 |
| H1 | intermediate refinement | 0.0025 mm | 0.1666666667 |
| H2-PUB | publication spatial resolution | 0.001 mm | 0.0666666667 |

Not authorized:

- changing phase-field formulation, `lc`, materials, loading, or increments;
- candidate-v2 diagnostic instrumentation;
- length-scale sensitivity;
- load-increment sensitivity;
- MISESERI;
- adaptive remeshing or state transfer;
- multi-CPU or GPU execution;
- a fourth mesh, retry, duplicate job, or automatic resubmission.

## Scientific Fixed Settings

All cases use the exact supplementary single-notch scientific settings:

| Quantity | Value |
|---|---|
| Geometry | 1 mm x 1 mm plate; open left-edge notch length 0.5 mm |
| E | 210 kN/mm^2 |
| nu | 0.3 |
| Gc | 2.7e-3 kN/mm |
| lc | 0.015 mm |
| thickness | 1 mm |
| residual stiffness k (U2) | 1.0e-7 |
| UMAT visualization residual | 1.0e-11 |
| architecture | U1 / U2 / CPS4 layered |
| phase convention | d = 0 intact, d = 1 broken |
| loading | exact supplementary Amp-1 / Amp-2 and Step-1 / Step-2 |

Do not use the candidate-v2 `lc = 0.0075 mm` model in this study.

## Case Definitions

### H0

- Exact author-supplied `SingleNotch.inp` and `SingleNotch.for`.
- Physical elements: 3930; layered elements: 11790.
- Source and deck hashes must remain byte-identical to the preserved originals.
- Local target `h = 0.005 mm` is the author/supplementary resolution label; actual
  corridor edge-length statistics are measured from the mesh.

### H1

- Deterministic structured refinement of the crack-path region to local target
  `h = 0.0025 mm`.
- Preserve all non-mesh scientific keywords from H0.
- Physical element count is obtained from generation and recorded, not assumed.
- Fortran `N_ELEM` is the only permitted source change.

### H2-PUB

- Deterministic structured refinement of the same crack-path region to local
  target `h = 0.001 mm`.
- Aim for a physical element count consistent with the publication approximate
  22000-element statement; do not force an exact count or tune the mesh to match
  the digitized curve.
- Physical element count is obtained from generation and recorded.
- Fortran `N_ELEM` is the only permitted source change.

## Mesh Policy

- Preserve the 1 mm x 1 mm specimen and open 0.5 mm left-edge notch.
- Preserve reference-point loading and coupling semantics.
- Use the same refined-corridor definition for H1 and H2-PUB.
- Vary only the target local crack-path resolution between H1 and H2-PUB.
- Use deterministic coordinates and numbering; no randomized meshing.
- Generate matching U1, U2, and CPS4 layers with the exact layer-offset rule
  based on physical `N_ELEM`.

## External Reference

Compare to the approximate digitized Fig. 7 curve for `lc = 0.015 mm` only.
Do not use the previously selected `lc = 0.0075 mm` curve.

Reference class: `approximate_digitized_publication_reference`.

Path:

`references/derived/molnar_gravouil_2017/single_notch/fig7_lc015_corrected_origin/`

Both axes must be calibrated from the published origin. Reports must contain
the origin `(0, 0)`. Do not shift digitized points merely to force agreement.

## Execution

- Serial only: `cpus=1`.
- Queue route: `entry_imfdfkmq`.
- Immutable pre-stage workflow; no Git inside PBS.
- Dependency chain: H0 -> H1 -> H2-PUB with `afterok`.
- Email: `pr21vyci@mailserver.tu-freiberg.de`, points `abe`.

## Successive-Mesh Evidence Rule

Main convergence evidence is successive mesh change:

1. H0 versus H1
2. H1 versus H2-PUB

Publication-curve comparison is external approximate evidence only. Do not claim
convergence automatically because one metric is small. Final numerical
tolerances remain provisional until supervisor approval.

## Paths

| Artifact | Path |
|---|---|
| Config | `configs/studies/molnar_lc015_h_convergence.yaml` |
| Acceptance | `docs/studies/MOLNAR_LC015_H_CONVERGENCE_ACCEPTANCE.md` |
| Generated models | `models/generated/molnar_gravouil_2017/h_convergence_lc015/` |
| Validation | `results/validation/molnar_lc015_h_convergence/` |
| Run evidence | `runs/hpc/molnar_lc015_h_convergence/` |
| Scratch runs | `/scratch/pr21vyci/adaptive-remeshing/runs/` |
