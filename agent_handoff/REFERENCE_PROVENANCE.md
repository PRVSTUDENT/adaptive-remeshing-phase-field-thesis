# Molnar Single-Notch Reference Provenance

Date: 2026-07-14

Status: `reference_data_insufficient`

## Source

- Paper: Gergely Molnar and Anthony Gravouil, "2D and 3D Abaqus implementation of a robust staggered phase-field solution for modeling brittle fracture", Finite Elements in Analysis and Design 130 (2017) 27-38.
- Local PDF: `Literature review/1-s2.0-S0168874X16304954-main.pdf`
- Relevant section: Section 3.2, "Single edge notched test"
- Relevant figures:
  - Fig. 6: geometry, tensile crack pattern, shear crack pattern, and crack angle trend.
  - Fig. 7: reaction force for the uniaxial tensile test using different length-scale parameters and Miehe reference symbols.

## Exact Match Assessment

The paper states that the published single-edge-notched tensile result in Fig. 7 uses a finite-element mesh of about 22,000 elements. It also states that, because of input-file size, the supplementary package contains a smaller tensile test with about 4,000 elements and `h = 0.005 mm`.

The repository run uses the supplied supplementary file:

- `models/baseline_original/molnar_gravouil_2017/02_Single_Notch_Tension/SingleNotch.inp`
- copied unchanged to `runs/molnar_single_notch_unchanged/20260714_technical_gate_local/work/SingleNotch.inp`
- local extracted model size: 3,998 nodes and 11,790 layered elements, corresponding to about 3,930 UEL phase/stress layer elements plus visualization elements.

Therefore the current public-paper Fig. 7 curve is not automatically an exact numeric reference for the smaller supplementary example. It is a literature comparison target and qualitative benchmark, but an unconditional quantitative pass/fail against digitized Fig. 7 would be scientifically unsafe unless the curve label and mesh/length-scale case are matched or the supervisor explicitly approves the comparison.

## Digitization Record

- Digitization method: not performed for RF-U in this revision.
- Reason: no reliable machine-readable curve table is available from the supplied PDF, and the exact published curve corresponding to the smaller supplementary `SingleNotch` deck is not identified.
- Digitization date: not applicable.
- Estimated digitization uncertainty: pending.
- Public repository policy: no extracted paper screenshots are committed; only derived numerical coordinates and provenance may be committed.

## Reference Files

- `rf_u_reference.csv`: intentionally contains metadata headers but no numeric reference coordinates in this revision. Validator classification should remain `reference_data_insufficient` for RF-U reference comparison.
- `crack_path_reference.csv`: contains a qualitative horizontal Mode-I ligament reference, `y = 0`, for the tensile case. This is derived from the geometry and Fig. 6 tensile crack-pattern description, not from pixel digitization of a paper screenshot.
- `reference_applicability_matrix.csv` and `REFERENCE_APPLICABILITY_MATRIX.md`: compare the paper case with the supplementary deck and document why exact RF-U comparison remains unresolved.

## Required Next Reference Action

Before Gate A3 can be promoted beyond `reference_data_insufficient`, one of the following must happen:

1. digitize the exact Fig. 7 curve and document curve label, axes, scale, units, and uncertainty, while explicitly accepting any mismatch between the paper mesh and supplementary example;
2. acquire original numerical RF-U reference data from the authors/source package;
3. define a supervisor-approved qualitative-only comparison path for the smaller supplementary example.
