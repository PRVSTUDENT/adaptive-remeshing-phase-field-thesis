# Fig. 7 Digitization Metadata - lc = 0.0075 mm

Classification: `approximate_published_reference`

- Paper: Molnar and Gravouil (2017), Finite Elements in Analysis and Design 130, 27-38.
- Local source: `Literature review/1-s2.0-S0168874X16304954-main.pdf`.
- Page and figure: journal page 32, local PDF page 6, Fig. 7.
- Selected curve: Molnar `lc = 0.0075 mm`, red dashed line.
- Visual identification: red dashed curve in the legend and plotted curve; separated from blue dotted and black solid curves by color threshold.
- Axis quantities: horizontal displacement `u [mm]`; vertical reaction force `F [kN]`.
- Calibration points: x origin (66.0, 518.0) -> 0.000 mm; x right (842.0, 518.0) -> 0.007 mm; y origin (66.0, 518.0) -> 0.0 kN; y tick (66.0, 61.0) -> 1.2 kN.
- Digitization software/script: `scripts/postprocessing/digitize_molnar_fig7_lc_0p0075.py`; Poppler `pdftoppm` render at 300 dpi; Pillow/numpy red-pixel threshold.
- Raw points: 877.
- Processed points: 91.
- Peak and post-peak treatment: retained red pixels in the steep drop; processed curve uses median bins without smoothing.
- Overlapping-curve regions: pre-peak branch overlaps other Molnar curves and Miehe symbols; red-pixel evidence is sparse there.
- Estimated coordinate uncertainty: approximately +/-0.00004 mm in displacement and +/-0.015 kN in reaction force, increased near the post-peak drop and symbol overlaps.
- Omitted segments: no red-pixel segment was manually omitted, but legend red pixels were rejected by crop-coordinate filtering.
- Important limitation: these coordinates are not exact author data and must not be used as an exact pass/fail reference.
