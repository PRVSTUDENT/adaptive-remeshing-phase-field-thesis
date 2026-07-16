# Baseline Diagnostic Deck Diff

Result: `scientific_keyword_equivalence_pass`

- Baseline deck: `models/generated/molnar_gravouil_2017/paper_matched_single_notch_v2/paper_matched_single_notch_v2.inp`
- Diagnostic deck: `models/generated/molnar_gravouil_2017/paper_matched_single_notch_v2_sdv15_diagnostic/paper_matched_single_notch_v2_sdv15_diagnostic.inp`
- Comparison method: remove Abaqus comment lines beginning with `**` and compare the remaining keyword/data stream byte-for-byte.

Only two diagnostic-identification comments are added. Nodes, connectivity,
element layers, materials, properties, boundary conditions, loading amplitudes,
step schedules, solver controls, and output requests are unchanged.
