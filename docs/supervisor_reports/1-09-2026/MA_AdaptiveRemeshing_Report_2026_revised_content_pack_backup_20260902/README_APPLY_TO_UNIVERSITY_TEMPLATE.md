# Revised scientific-content pack - 1 September 2026

This folder contains rewritten thesis/report content aimed at the supervisor feedback received after the 11 August progress report.

## Why this rewrite is different

The scientific narrative is now organised around conventional mechanics/numerical-method interfaces:

1. problem and phase-field formulation;
2. fixed-mesh reference reproduction;
3. Abaqus-native MISESERI pre-refinement;
4. conversion to layered UEL/UMAT representation;
5. nonmatching state transfer and restart;
6. serial/parallel implementation boundary;
7. current Pandey-Kumar Task-5 validation;
8. explicit open questions and next steps.

Internal workflow labels, controller states and operational terminology are deliberately excluded from the main chapters. PBS IDs are moved to the appendix.

## Files intended to replace/update in the university package

- `abstract.tex`
- `chapter01_introduction_theory.tex`
- `chapter02_baseline.tex`
- `chapter03_mesh_refinement.tex`
- `chapter04_state_transfer.tex`
- `chapter05_multiresolution.tex`
- `chapter06_hpc.tex`
- `chapter07_production_validation.tex`
- `chapter08_conclusions.tex`
- `appendix.tex`

Do **not** overwrite the university `preambel.tex` or `abbrvnat_custom.bst`.

The files are deliberately written with standard LaTeX commands so that they can be dropped into the university template. A standalone `draft_main.tex` and `literature_revised.bib` are included only to make this package independently compilable for review.

## Final Task-5 result placeholder

The current production solve `1399632.mmaster02` was still running when this draft was prepared. Chapter 7 therefore reports only verified completed evidence and explicitly leaves the final adaptive force-displacement result open. Update Chapter 7 only after terminal solver evidence and ODB extraction are available.

## Important source correction

The Pandey-Kumar paper explicitly reports `errorTarget=1.0` in Listing 1 and 13,941 elements for the principal Mode-I proposed mesh. The current reconstruction's 2% sensitivity result (~15,396 elements) must **not** be presented as proof that the paper used 2%; it is only diagnostic evidence that mesh density is strongly sensitive to the error target.

## Figures

The generated figures in `figures/generated/` now include both derived review plots and direct Abaqus CAE exports. Captions distinguish the two. Add further result images only when the source ODB/input, frame/displacement and field range are verified; do not infer missing frames or fabricate contours.

The 35-page standalone build now includes qualified simulation evidence already present in the project: direct Molnar one-element and four-state single-notch CAE exports, actual Molnar H0/H1/H2 meshes, the paper/reproduction RF-U comparison, MISESERI pre-analysis evidence, direct coarse/nominal-adaptive Mode-I meshes, state-transfer fields, Mode-II response/damage comparisons, and direct Mode-II H1/H2 meshes. Diagnostic images and the stale 14,235-element adaptive ODB remain excluded from final-result claims.


## Supervisor-feedback changes embodied in this draft

- The report begins from a conventional mechanics problem statement rather than internal workflow states.
- Literature inputs and thesis implementation interfaces are separated explicitly.
- The fixed-mesh Mode-I reproduction is presented before remeshing.
- A geometry schematic and the complete refinement process chain are included.
- Internal job/status language is removed from the scientific body; job IDs remain in the appendix.
- The running production calculation is left open rather than assigning a predicted result.
- A final crack-evolution image sequence should be inserted from the completed production ODB before supervisor submission.
