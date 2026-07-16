# RUN_MANIFEST - paper_matched_single_notch_v2

Prepared: 2026-07-16

Status:

```text
prepared_not_submitted
```

## Candidate

- Candidate name: `paper_matched_candidate_v2`
- Reconstruction version: `paper_matched_candidate_v2`
- Static validation: `static_validation_pass`
- Runnable status: `true`
- Gate A3: `reference_data_insufficient`
- Scientific status: `paper_matched_v2_scientific_comparison_pending`

## Repository

- Preparation base revision: `79c2bcc18726ef9bfa34e209044f7cb344ab0af4`
- Candidate commit revision: `pending`
- Generator revision: `pending candidate commit`
- PBS submission revision: `pending`

## Deck And Source

- Candidate deck: `models/generated/molnar_gravouil_2017/paper_matched_single_notch_v2/paper_matched_single_notch_v2.inp`
- Candidate deck SHA-256: `f4d135d6c12d42a94c1874a6453a8865b4806a4e2d3b5018141471ba9245ecf2`
- Preserved Molnar source: `models/baseline_original/molnar_gravouil_2017/02_Single_Notch_Tension/SingleNotch.for`
- Preserved Molnar source SHA-256: `18944e5bb2a3b7973fd0d4bff03f8e078eef667965343d8a29156d093f53f5f1`
- Candidate user subroutine: `models/generated/molnar_gravouil_2017/paper_matched_single_notch_v2/SingleNotch_v2.for`
- Candidate user subroutine SHA-256: `e587c195c50a5c52a000ca54d3ed00e1bf8161ba2f6aa7b3cf5aacec8425913a`
- Source-copy note: `SingleNotch_v2.for` is copied from the preserved Molnar implementation with only `N_ELEM` updated to `33852` for the candidate-v2 physical element count.

## Model Parameters

- Geometry: `1.0 mm x 1.0 mm`
- Notch: left-edge split-node notch, length `0.5 mm`, `y=0`
- Loading angle: `90 deg`
- Plane strain: `true`
- Thickness: `1.0 mm`
- Young's modulus: `210 kN/mm^2`
- Poisson's ratio: `0.3`
- Critical energy release rate: `0.0027 kN/mm`
- Length scale `lc`: `0.0075 mm`
- Local mesh size `h`: `0.001 mm`
- `h/l`: `0.13333333333333333`
- Physical elements: `33852`
- Layered elements: `101556`
- Minimum element size: `0.001 mm`
- Maximum element size: `0.025 mm`
- Maximum neighboring-size ratio: `1.5`
- Maximum aspect ratio: `25.000000000001368`

## Loading Schedule

| Step | Initial displacement | Final displacement | Increment | Count |
|---|---:|---:|---:|---:|
| Step-1 | 0.0 mm | 0.005 mm | 1e-5 mm | 500 |
| Step-2 | 0.005 mm | 0.0067 mm | 1e-5 mm | 170 |

Arithmetic:

```text
500 * 1e-5 mm = 0.005 mm
170 * 1e-5 mm = 0.0017 mm
0.005 mm + 0.0017 mm = 0.0067 mm
```

## Reference

- Selected approximate reference: Molnar Fig. 7 red dashed `lc = 0.0075 mm`
- Processed reference CSV: `references/derived/molnar_gravouil_2017/paper_matched_single_notch/fig7_lc_0p0075_processed.csv`
- Raw digitized point count: `877`
- Processed point count: `91`
- Digitization uncertainty: `+/-0.00004 mm`, `+/-0.015 kN`
- Classification after extraction must be `approximate_published_reference_comparison`, not exact author-data validation.

## Mesh Preflight

- Preflight file: `results/validation/molnar_paper_matched_single_notch_v2/MESH_QUALITY_PREFLIGHT.md`
- Classification: `mesh_quality_preflight_pass`
- High-aspect-ratio limitation: documented reconstruction limitation; high-aspect elements are outside the notch-tip/fracture-process corridor and do not intersect the expected horizontal crack path.
- Elements bridging open notch: `0`

## Requested PBS Resources

- PBS script: `scripts/hpc/molnar_paper_matched_single_notch_v2.pbs`
- Queue: `entry_imfdfkmq`
- Nodes: `1`
- CPUs: `1`
- Memory: `32gb`
- Walltime: `24:00:00`
- Modules: `gcc/11.4.0`, `intel/2024.2.0`, `abaqus/2023`
- Scratch run root: `/scratch/pr21vyci/adaptive-remeshing/runs`
- Lightweight stage root: `/scratch/pr21vyci/adaptive-remeshing/stage`
- ODB retention: scratch only

## Technical Acceptance Criteria

Technical pass classification:

```text
paper_matched_v2_technical_pass
```

Required:

- PBS execution completed.
- Abaqus license checkout succeeded.
- Fortran compilation succeeded.
- Linking succeeded.
- Input processing succeeded.
- Abaqus return code was zero.
- `.sta` exists.
- `.msg` exists.
- `.dat` exists.
- `.odb` exists in scratch.
- `.sta` contains `THE ANALYSIS HAS COMPLETED SUCCESSFULLY`.
- Final PBS success marker printed.

Technical failure classification:

```text
paper_matched_v2_technical_fail
```

Failure categories include `license_failure`, `compilation_failure`, `link_failure`, `input_processing_failure`, `numerical_nonconvergence`, `walltime_exceeded`, `memory_failure`, and `evidence_preservation_failure`.

## Scientific Postprocessing Plan

After a technical pass, extract without rerunning Abaqus:

- top-boundary displacement;
- total reaction force;
- RF-displacement curve;
- peak RF and displacement at peak;
- final RF and displacement;
- area under RF-displacement curve;
- phase-field/SDV fields at response-based states;
- crack-path coordinates;
- SDV16 monotonicity;
- SDV15 local decreases and overshoot;
- final damaged-element count;
- connected crack extension;
- maximum and mean vertical crack-path deviation.

Scientific labels remain separate from technical completion:

```text
paper_matched_v2_scientific_comparison_pending
paper_matched_v2_scientific_provisional_pass
paper_matched_v2_scientific_fail
```

## Submission

- Job ID: `pending`
- Submission time: `pending`
- Synchronized HPC revision: `pending`
- Active-job precheck: `pending`
- HPC working tree precheck: `pending`
