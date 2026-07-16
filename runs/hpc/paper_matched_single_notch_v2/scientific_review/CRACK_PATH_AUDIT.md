# Crack Path Audit

Classification: `crack_path_review_required`

Damaged elements were recomputed from the contour CSVs using the canonical element-mean `SDV15` rule at thresholds `0.50`, `0.80`, `0.90`, `0.95`, and `0.99`. Connectivity uses shared element edges from the candidate deck. A separate aggregation-sensitivity file records min/mean/max integration-point counts.

## SDV15 Element Mean >= 0.95 Summary

|state_file|rp_u2|aggregation_rule|damaged_element_count|connected_component_count|largest_component_count|connected|crack_extension_mm|max_vertical_deviation_mm|
|---|---|---|---|---|---|---|---|---|
|matched_state_01_Step-1_frame_0040_contour_sdv14_sdv15_sdv16.csv|0.0020000000949949026|element_mean_sdv15|0|0|0|False|0||
|matched_state_02_Step-1_frame_0100_contour_sdv14_sdv15_sdv16.csv|0.004999999888241291|element_mean_sdv15|0|0|0|False|0||
|matched_state_03_Step-2_frame_0058_contour_sdv14_sdv15_sdv16.csv|0.0059899999760091305|element_mean_sdv15|0|0|0|False|0||
|matched_state_04_Step-2_frame_0100_contour_sdv14_sdv15_sdv16.csv|0.0066999997943639755|element_mean_sdv15|193|1|193|True|0.051|0.0015|

## Interpretation

The first three response states show no element-mean `SDV15 >= 0.95` crack path. The final state contains a connected damaged band with about `0.0505 mm` extension and small vertical deviation, consistent with a short horizontal propagation from the notch region. Threshold sensitivity is preserved in `crack_path_threshold_metrics.csv`, and integration-point aggregation sensitivity is preserved in `crack_path_aggregation_sensitivity.csv`.
