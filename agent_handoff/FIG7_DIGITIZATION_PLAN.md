# Fig. 7 Digitization Plan - Molnar Single-Edge-Notched Tension

Date: 2026-07-15

Status: `completed_for_candidate_v1`

## Selected Curve

Candidate selected curve:

```text
Molnar and Gravouil Fig. 7, Molnar curve lc = 0.0075 mm
```

Justification:

- Section 3.2 states the direct-comparison single-edge-notched benchmark uses `lc = 0.0075 mm`.
- Fig. 7 includes a visible Molnar `lc = 0.0075 mm` red dashed curve.
- This is the proposal-aligned first target for the paper-matched reconstruction, not the smaller supplementary deck.

The curve is now digitized for the v1/v2 paper-matched candidate workflow. The coordinate files remain approximate published-reference data, not exact author data.

## Source Image

- Source PDF: `Literature review/1-s2.0-S0168874X16304954-main.pdf`
- Source page: journal page 32, PDF page 6 in the local file
- Figure: Fig. 7
- Caption: reaction force for the uniaxial tensile test using different length-scale parameters along with Miehe symbols

## Axis Calibration

Required calibration points:

- x-axis origin: `u = 0.000 mm`
- x-axis right tick: preferably `u = 0.007 mm`
- y-axis origin: `F = 0.0 kN`
- y-axis upper tick: preferably `F = 1.2 kN`

Record the exact pixel coordinates used for each calibration point in the raw metadata file.

## Method

Preferred method:

1. Render the PDF page at high resolution from the original local PDF.
2. Crop Fig. 7 without rescaling.
3. Use WebPlotDigitizer or an equivalent scripted pixel-to-data transform.
4. Digitize only the selected red dashed Molnar `lc = 0.0075 mm` curve.
5. Avoid Miehe symbols unless a separate symbol-reference extraction is explicitly required.
6. Export raw clicked points and processed monotonic RF-U coordinates separately.

Point density:

- Use dense points around peak and post-peak drop.
- Use enough pre-peak points to resolve the linear slope without oversampling overlapping symbols.
- Keep raw points unsmoothed; any smoothing must be a separate processed file with metadata.

Vertical/post-peak treatment:

- Preserve multiple points at near-identical displacement if needed to represent a steep force drop.
- Do not force strict monotonic displacement if the visual curve is vertical within digitization uncertainty.
- Store any ordering or duplicate-displacement handling in processed metadata.

## Uncertainty Estimate

Required components:

- pixel calibration uncertainty;
- line-width uncertainty;
- uncertainty from overlap with symbols/other curves;
- uncertainty from antialiasing and color separation;
- estimated RF uncertainty in kN and displacement uncertainty in mm.

Initial expected classification:

```text
approximate_paper_reference
```

The digitized coordinates are not exact published data.

## Candidate v2 Use

Date: 2026-07-16

Candidate v2 uses the same processed digitization:

- raw points: `877`
- processed points: `91`
- displacement uncertainty: `+/-0.00004 mm`
- reaction-force uncertainty: `+/-0.015 kN`

No v2 RF-displacement comparison exists until the one authorized serial run is performed after repository synchronization and clean HPC checks.

## Output Paths

Raw data path:

```text
references/derived/molnar_gravouil_2017/paper_matched_single_notch/fig7_digitized_raw_lc_0p0075.csv
```

Processed data path:

```text
references/derived/molnar_gravouil_2017/paper_matched_single_notch/fig7_digitized_processed_lc_0p0075.csv
```

Metadata path:

```text
references/derived/molnar_gravouil_2017/paper_matched_single_notch/fig7_digitization_metadata_lc_0p0075.md
```

Candidate v1 output paths:

```text
references/derived/molnar_gravouil_2017/paper_matched_single_notch/fig7_lc_0p0075_raw.csv
references/derived/molnar_gravouil_2017/paper_matched_single_notch/fig7_lc_0p0075_processed.csv
references/derived/molnar_gravouil_2017/paper_matched_single_notch/FIG7_DIGITIZATION_METADATA.md
```

The candidate v1 extraction produced 877 raw red-threshold points and 91 processed median-bin points. The classification is `approximate_published_reference`; the points are not exact author data.
