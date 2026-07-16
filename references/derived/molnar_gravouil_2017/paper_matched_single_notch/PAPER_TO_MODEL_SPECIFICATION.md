# Paper-To-Model Specification - Molnar Single-Edge-Notched Mode-I Benchmark

Date: 2026-07-15

Status: `reconstruction_audit_incomplete`

Classification:

- Existing supplementary model: `supporting_technical_reproducibility_baseline`
- Future reconstructed model: `paper_matched_scientific_benchmark_candidate`

This specification records what can be reconstructed from the thesis plan, Molnar and Gravouil (2017), the supplied supplementary deck/source, and existing project notes. It is a source-audit artifact only. It does not authorize an Abaqus run, PBS submission, MISESERI workflow, remeshing, state transfer, or parameter study.

## Benchmark Purpose

The thesis plan directs Stage A/WP2 to reproduce a uniform-mesh single-edge-notched Mode-I benchmark before adaptive refinement. Required studies include geometry/material/loading/output reproduction, separate studies of `h/l`, length scale, and load increment, creation of a uniformly fine reference, and force-displacement/crack-path comparison.

The paper-matched model must compare against Molnar and Gravouil's published single-edge-notched tensile benchmark, not against the smaller supplementary deck as if it were the exact Fig. 7 model.

## Confirmed Published Values

| Quantity | Value | Status | Source |
|---|---:|---|---|
| Geometry width | 1.0 mm | `exact_from_figure` | Molnar Fig. 6a |
| Geometry height | 1.0 mm | `exact_from_figure` | Molnar Fig. 6a |
| Initial notch length | 0.5 mm from left edge to midline | `exact_from_figure` | Molnar Fig. 6a |
| Loading case | uniaxial tension, alpha = 90 deg | `exact_from_text` / `exact_from_figure` | Molnar Sec. 3.2 and Fig. 6b |
| Expected Mode-I crack path | horizontal ligament continuation | `exact_from_text` / `exact_from_figure` | Molnar Sec. 3.2 and Fig. 6b |
| Bottom boundary | bottom side fixed | `exact_from_text` / `exact_from_figure` | Molnar Sec. 3.2 and Fig. 6a |
| Top boundary/loading | top side moved | `exact_from_text` / `exact_from_figure` | Molnar Sec. 3.2 and Fig. 6a |
| Plane-strain assumption | all 2D cases are plane strain | `exact_from_text` | Molnar Sec. 3 |
| Physical thickness | 1 mm | `exact_from_text` | Molnar Sec. 3 |
| Young's modulus | 210 kN/mm^2 | `exact_from_text` | Molnar Sec. 3.2 |
| Poisson's ratio | 0.3 | `exact_from_text` | Molnar Sec. 3.2 |
| Critical energy-release rate | 2.7e-3 kN/mm | `exact_from_text` | Molnar Sec. 3.2 |
| Primary paper-text length scale | 0.0075 mm | `exact_from_text` | Molnar Sec. 3.2 |
| Fig. 7 Molnar length scales | 0.015, 0.0075, 0.005 mm | `exact_from_figure` | Molnar Fig. 7 legend |
| Published mesh size | about 22000 elements | `exact_from_text` | Molnar Sec. 3.2 |
| Refined crack-path element size | h = 0.001 mm | `exact_from_text` | Molnar Sec. 3.2 |
| Tensile loading increments | Delta u = 1e-4 mm for 500 steps, then 1e-5 mm | `exact_from_text` | Molnar Sec. 3.2 |
| Fig. 7 axes | displacement u [mm], reaction force F [kN] | `exact_from_figure` | Molnar Fig. 7 |
| Supplementary smaller model | about 4000 elements, h = 0.005 mm | `exact_from_text` | Molnar Sec. 3.2 |

## Confirmed Supplementary Implementation Mechanics

| Quantity | Value | Status | Source |
|---|---:|---|---|
| Supplementary node count | 3998 | `derived` | Parsed from preserved `SingleNotch.inp` |
| Supplementary coordinate extents | x,y in [-0.5, 0.5] mm | `derived` | Parsed from preserved `SingleNotch.inp` |
| Physical elements per layer | 3930 | `exact_from_supplementary` | `SingleNotch.inp` element sets; `SingleNotch.for` `N_ELEM=3930` |
| Layered total elements | 11790 | `derived` | Three layers times 3930 |
| Phase UEL layer | U1, 4 nodes, properties lc, gc, thickness | `exact_from_supplementary` | `SingleNotch.inp` `*User element`, `*Uel property` |
| Displacement UEL layer | U2, 4 nodes, properties E, nu, thickness, k | `exact_from_supplementary` | `SingleNotch.inp` `*User element`, `*Uel property` |
| Visualization layer | CPS4 `umatelem` | `exact_from_supplementary` | `SingleNotch.inp` `*Element, TYPE=CPS4` |
| Layer numbering rule | second and third element layers offset by `N_ELEM` | `exact_from_text` / `exact_from_supplementary` | Molnar Appendix B; `SingleNotch.for` comments |
| Reaction-force extraction set | `RP` with `RF,U` | `exact_from_supplementary` | `SingleNotch.inp` `*Node Output, nset=RP` |
| Phase-field output carrier | `SDV` on `umatelem` | `exact_from_supplementary` | `SingleNotch.inp` `*element output, elset=umatelem` |
| Plane-strain stiffness implementation | explicit plane-strain material stiffness | `exact_from_supplementary` | `SingleNotch.for` material-stiffness block |

## Paper-Matched Target

The first reconstructed target should use the paper-text single-notch tensile parameters:

- geometry: 1.0 mm by 1.0 mm plate, left-edge notch length 0.5 mm at mid-height;
- loading: pure tension, alpha = 90 deg, top moved, bottom fixed;
- material: E = 210 kN/mm^2, nu = 0.3;
- fracture: Gc = 2.7e-3 kN/mm, initial target lc = 0.0075 mm;
- mesh: about 22000 physical elements with h = 0.001 mm near the expected crack path;
- increments: Delta u = 1e-4 mm for 500 steps, then Delta u = 1e-5 mm;
- output: RP reaction force/displacement and UMAT-layer phase-field SDVs.

This target is not yet runnable because critical deck-construction details remain unresolved.

## Unresolved Critical Values

| Quantity | Status | Why it remains unresolved |
|---|---|---|
| Exact mesh topology | `unresolved` | Fig. 6 does not provide a mesh; text gives approximate count and local h only. |
| Refined-zone dimensions | `unresolved` | Text says region around crack path is refined but does not give zone extents. |
| Global element size | `unresolved` | Not stated for the single-edge-notched test. |

## Candidate v2 Repair Update

Date: 2026-07-16

Candidate v1 is preserved as failed static evidence. Candidate v2 corrects the no-run structural blockers by using:

- corrected Step-1 arithmetic: `500 * 1e-5 mm = 0.005 mm`;
- split duplicated nodes on the open left-edge notch segment;
- source-mapped U1 and U2 `*Uel property` blocks;
- source-faithful `bottoml` and `topl` horizontal constraints;
- a physically generated graded coordinate set with local `h=0.001 mm`, global cap `h=0.025 mm`, and maximum neighboring-size ratio `1.5`.

Candidate v2 static result:

```text
paper_matched_candidate_v2
static_validation_pass
runnable: true
```

No Abaqus result exists for candidate v2 yet. Gate A3 remains open until the candidate is run and compared with the approximate Fig. 7 reference.
| Transition law from refined to coarse mesh | `unresolved` | Not stated for the single-edge-notched test. |
| Exact element count target | `unresolved` | Paper states approximate 22000 elements; exact count absent. |
| Step termination displacement | `unresolved` | Text gives increment sequence; final displacement for Fig. 7 is visible only approximately from the axis. |
| Number of fine increments after first 500 steps | `unresolved` | Not stated. |
| Exact Fig. 7 curve to digitize first | `unresolved` | The Molnar lc=0.0075 mm curve is visible, but digitization metadata and curve isolation are not complete. |
| Matched displacement contour states | `unresolved` | Fig. 6b shows the final tensile crack pattern but no explicit displacement state. |
| Exact RP/coupling implementation for the paper model | `unresolved` | The supplementary deck provides one valid implementation; the paper describes top movement generically. |
| Supervisor-approved tolerances | `unresolved` | Not yet defined. |

## Supplementary Versus Paper-Matched Comparison

| Category | Same or compatible | Different or unresolved |
|---|---|---|
| Geometry | Both are single-edge-notched 1 mm by 1 mm tensile specimens. | Paper geometry comes from Fig. 6; supplementary deck is the smaller supplied case and must remain preserved. |
| Material | E = 210, nu = 0.3, Gc = 0.0027 match. | Units must be carried as kN/mm-based paper units. |
| Length scale | Both use Molnar source conventions. | Paper text target lc = 0.0075 mm; supplementary deck uses lc = 0.015 mm. |
| Mesh | Both refine near the ligament. | Paper model about 22000 elements with h = 0.001 mm; supplementary model about 4000 physical elements with h = 0.005 mm. |
| Loading | Both use vertical top displacement in tension. | Paper final displacement and exact fine-step count are not fully specified; supplementary deck has two explicit Abaqus steps. |
| Outputs | Both need RF-U and phase-field SDVs. | Paper Fig. 7 is a plotted approximate reference, not machine-readable coordinates. |

## Candidate v1 Reconstruction Update

Date: 2026-07-16

The first versioned reconstruction candidate is now recorded as `paper_matched_candidate_v1`, but it remains non-runnable. Fig. 7 has been digitized for the Molnar `lc = 0.0075 mm` red dashed curve using a scripted 300 dpi PDF render and red-pixel threshold. The raw digitization has 877 threshold points and the processed median-bin curve has 91 points. The digitized curve is classified only as `approximate_published_reference`.

Candidate v1 uses the paper values \(l_c=0.0075\ \mathrm{mm}\), \(h=0.001\ \mathrm{mm}\), \(h/l=0.133333\), \(\Delta u=10^{-4}\ \mathrm{mm}\) for 500 increments, and \(\Delta u=10^{-5}\ \mathrm{mm}\) afterward. The final displacement is measured from the visible Fig. 7 horizontal-axis/curve extent as \(u=0.0067\ \mathrm{mm}\), giving 170 derived fine increments after \(u=0.005\ \mathrm{mm}\). This is not an exact textual paper value.

The mesh recipe is an `adopted_reconstruction_choice`, not a published parameter: refined strip \(x=-0.02..0.5\ \mathrm{mm}\), \(y=-0.005..0.005\ \mathrm{mm}\), local \(h=0.001\ \mathrm{mm}\), global size 0.025 mm, linear size-growth transition, maximum neighbouring-size ratio 1.5, full-domain structured quadrilateral skeleton, U1/U2/CPS4 layering with offsets of \(N_\mathrm{elem}\). The estimator reports 21,760 physical elements and 65,280 layered elements, close to the paper's approximate 22,000 physical-element statement.

Generated candidate files are under `models/generated/molnar_gravouil_2017/paper_matched_single_notch_v1/`. Static validation currently classifies the state as `reconstruction_inputs_incomplete`; therefore `configs/molnar_paper_matched_single_notch.yaml` keeps `runnable: false`.

## Non-Selection Rules

- Do not choose a visually similar mesh as a published parameter.
- Do not treat the smaller supplementary deck as the exact Fig. 7 reference model.
- Do not digitize a curve whose identity or axis calibration is unresolved.
- Do not mark the configuration runnable while any critical field is null.
- Do not submit a run until the deck is versioned, statically verified, and explicitly approved.
