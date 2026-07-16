# Molnar Paper-Matched Deck Requirements

Date: 2026-07-15

Status: `requirements_before_deck_generation`

The future Molnar paper-matched single-edge-notched Mode-I deck may be generated only after all critical source-to-model fields are traceable. A visually similar geometry is insufficient.

## Required Before Deck Generation

- Geometry dimensions are source-traceable.
- Notch length and position are source-traceable.
- Target Fig. 7 curve is identified and documented.
- Length scale is fixed.
- Local `h/l` is fixed.
- Local element size and mesh-transition rule are fixed.
- Refined-zone dimensions are fixed or explicitly justified.
- Loading increments and final displacement/step count are fixed.
- Material parameters and fracture parameters are fixed.
- Residual-stiffness convention is fixed and source-traceable.
- UEL/UMAT layer counts, offsets, and `N_ELEM` values are defined.
- Reaction-force extraction set or equivalent top resultant is defined.
- Phase-field/SDV output mapping is declared.
- Matched contour-comparison states are declared.
- All critical fields in `configs/molnar_paper_matched_single_notch.yaml` are non-null.

## Static Deck Acceptance Criteria

Before any Abaqus run is requested, the generated deck must pass static checks:

- preserved Molnar source files remain unmodified;
- generated input deck is versioned separately from the supplementary deck;
- physical element count equals the Fortran `N_ELEM` value used for the reconstructed source copy;
- phase, displacement, and visualization layers have identical connectivity and consistent element offsets;
- all expected element and node sets exist;
- boundary conditions reproduce bottom support and top prescribed displacement without overconstraint;
- output requests include RF/U and phase-field SDVs;
- units match the kN/mm convention used by the paper;
- comments or metadata record every reconstruction assumption.

## Run Boundary

Passing static checks does not authorize execution. A single serial HPC baseline run requires a separate explicit approval after the reconstructed deck, source copy, config, and reference plan have been reviewed.

Gate A3 remains:

```text
reference_data_insufficient
```

until the paper-matched benchmark is run and compared against a documented approximate paper reference or other approved reference route.

## Candidate v1 Static Reconstruction Status

Date: 2026-07-16

Candidate v1 now has a deterministic configuration, digitized approximate Fig. 7 reference, generated deck skeleton, generation manifest, mesh statistics, source hashes, and static validation report. The key outputs are:

- `configs/molnar_paper_matched_single_notch.yaml`
- `models/generated/molnar_gravouil_2017/paper_matched_single_notch_v1/`
- `results/validation/molnar_paper_matched_single_notch_v1/STATIC_VALIDATION.md`

Static classification was superseded by the no-run provenance review as `static_validation_fail`. Candidate v1 remains preserved and must not be submitted.

## Candidate v2 Static Reconstruction Status

Date: 2026-07-16

Candidate v2 generated a versioned deck and diagnostics under:

- `models/generated/molnar_gravouil_2017/paper_matched_single_notch_v2/`
- `results/validation/molnar_paper_matched_single_notch_v2/`

Static classification:

```text
static_validation_pass
runnable: true
```

This status only authorizes the next repository synchronization and clean-revision checks. It does not by itself record an Abaqus result. The previously authorized one serial HPC run remains dormant until commit/push/local-HPC revision alignment and clean working-tree checks pass.
