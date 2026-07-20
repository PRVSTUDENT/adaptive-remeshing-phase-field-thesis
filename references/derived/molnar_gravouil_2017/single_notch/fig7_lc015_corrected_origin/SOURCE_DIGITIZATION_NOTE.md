# Fig. 7 Digitization - lc = 0.015 mm

Classification: `approximate_published_reference`

- Paper: Molnar and Gravouil (2017), Finite Elements in Analysis and Design 130, 27-38.
- Local source: `Literature review/1-s2.0-S0168874X16304954-main.pdf`.
- Figure: Fig. 7, rendered from local PDF page 6 at 300 dpi.
- Selected curve: black solid Molnar curve labelled `lc = 0.015 mm`.
- Axis quantities: displacement `u [mm]`; reaction force `F [kN]`.
- Calibration: crop plot origin `(66, 518)` -> `(0 mm, 0 kN)`; x-axis right `(842, 518)` -> `0.007 mm`; y-axis tick `(66, 61)` -> `1.2 kN`.
- Raw points: `fig7_lc_0p015_raw.csv`.
- Processed points: `fig7_lc_0p015_processed.csv`.
- Overlay image: `fig7_lc_0p015_digitization_overlay.png`.

The first processed point is exactly `(0, 0)`. No horizontal or vertical offset was applied to force agreement with the Abaqus curve.

The included `fig7_lc_0p015_digitization_overlay.png` shows the selected points and calibration against the publication image.

The black curve overlaps black axes, text, and Miehe marker outlines, so the trace was selected manually from the rendered crop. Estimated coordinate uncertainty is approximately `+/-0.00005 mm` and `+/-0.02 kN`, with larger uncertainty near the peak/drop where marker outlines are dense. These coordinates are a publication-image digitization, not exact author numerical data.
