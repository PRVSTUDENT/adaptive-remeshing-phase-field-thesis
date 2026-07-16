# Figure Reference Audit - Molnar Fig. 6 and Fig. 7

Date: 2026-07-15

Status: `figure_reference_audit_incomplete`

Source: Molnar and Gravouil (2017), Section 3.2, Fig. 6 and Fig. 7.

## Fig. 6: Geometry and Crack Pattern

Confirmed visible geometry:

- Rectangular single-edge-notched specimen, 1.0 mm wide and 1.0 mm high.
- Left-edge notch reaches the mid-width location, giving notch length 0.5 mm.
- Notch lies at mid-height, splitting the height into 0.5 mm upper and lower halves.
- Loading vector `u` is drawn on the top side with angle alpha.
- Pure tension is labelled alpha = 90 deg.
- Pure shear is labelled alpha = 0 deg.

Boundary-condition symbols:

- Bottom edge is fixed in the figure and text.
- Top edge is moved by prescribed displacement.
- The paper-level statement does not prescribe the exact Abaqus RP/coupling implementation; the supplementary deck provides one implementation that must be documented if reused.

Mode-I crack direction:

- For alpha = 90 deg, the paper states and shows a horizontal crack pattern continuing from the notch through the ligament.
- This supports only a qualitative horizontal crack-path reference until matched displacement states and digitized contour criteria are declared.

Contour states:

- Fig. 6b shows the tensile fracture pattern but does not label the displacement state.
- The contour color scale is not printed in the extracted figure.
- Matched contour states for validation remain unresolved.

## Fig. 7: Reaction Force Reference

Axes:

- x-axis: displacement, `u [mm]`.
- y-axis: reaction force, `F [kN]`.

Identifiable Molnar curves:

| Curve | Legend text | Visual style | Identifiability |
|---|---|---|---|
| Molnar lc=0.015 mm | `lc = 0.015 mm` | black solid line | identifiable |
| Molnar lc=0.0075 mm | `lc = 0.0075 mm` | red dashed line | identifiable |
| Molnar lc=0.005 mm | `lc = 0.005 mm` | blue dotted line | identifiable |

Identifiable Miehe symbols:

| Symbol series | Legend text | Identifiability |
|---|---|---|
| Square symbols | Miehe et al. (2010a), lc = 0.0075 mm | identifiable |
| Circle symbols | Miehe et al. (2010b), lc = 0.0075 mm | identifiable |
| Down-triangle symbols | Miehe et al. (2010b), lc = 0.015 mm | identifiable |

Selected target curve status:

- The paper-text first reconstruction value is lc = 0.0075 mm.
- The Fig. 7 Molnar lc = 0.0075 mm curve is visually identifiable as the red dashed curve.
- It should become the first digitization target only after axis calibration, curve-isolation settings, and metadata paths are written.
- The config remains non-runnable and keeps `reference.curve_label: null` until digitization actually starts.

Legibility and uncertainty:

- The peak and post-peak propagation interval are visible, but several curves and symbols overlap around the pre-peak linear region.
- Line width, color antialiasing, overlapping Miehe symbols, and rasterization resolution introduce digitization uncertainty.
- The post-peak drop is steep, so vertical portions need explicit treatment during digitization.
- The figure provides plotted reference behavior only, not exact numerical RF-U coordinates.

## Candidate v1 Digitization Result

Date: 2026-07-16

The Molnar `lc = 0.0075 mm` red dashed Fig. 7 curve was digitized from the local PDF render. The curve identity is sufficiently distinguishable by color and line style, but the pre-peak branch overlaps other curves and Miehe symbols. The resulting files are:

- `fig7_lc_0p0075_raw.csv`: 877 red-threshold pixel-derived raw points.

## Candidate v2 Reference Status

Date: 2026-07-16

Candidate v2 keeps the same approximate published reference:

```text
Molnar Fig. 7 red dashed curve, lc = 0.0075 mm
```

The corrected deck has no Abaqus result yet. The digitized curve remains an approximate comparison target, not exact author data.
- `fig7_lc_0p0075_processed.csv`: 91 median-bin processed points without smoothing.
- `FIG7_DIGITIZATION_METADATA.md`: calibration, uncertainty, omitted/ambiguous-region, and classification record.

Classification: `approximate_published_reference`. These points are not exact author data.

Fig. 6b remains unlabeled by displacement. Candidate v1 therefore uses response-based contour states: final converged state, peak force, and first post-peak frame at or below 50 percent of peak force. No invented numerical displacement is assigned to Fig. 6b.

## Audit Decision

Fig. 7 target curve: `candidate_identified_not_digitized`

Do not treat Fig. 7 as exact reference coordinates. Use it only after a documented approximate digitization workflow creates derived coordinates with uncertainty metadata.
