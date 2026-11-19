# Adaptive Job-2 damage evolution contours

All four cases (1, 2, 3, 5) are available as evolution PNG/PDF panels and four individual state PNGs per case. Extracted from the existing F1859 adaptive Job-2 ODBs; no new solves, remeshing or framework changes.

## Corrected frame selection

The original generic pre-peak / peak / late post-peak / last-frame selection skipped the propagation interval. Cases 1 and 2 effectively sampled 0%, about 0.3%, 100% and 100% of terminal damage content. The corrected selection searches actual recorded frames near 10%, 35%, 65% and 95% of terminal damage content D = sum(element area * max(mean SDV1 - 0.5, 0)). Neighbouring frames are audited; four distinct chronological states with increasing observed D are selected. This is a visualization measure, not an error indicator, crack-length measurement, percentage of fractured material or new adaptive strategy. No field or time interpolation is used.

Exact achieved fractions and old/new comparison: results/validation/adaptive_job2_damage_growth_comparison.json. Frame indices are zero-based; step, frameId, time, actual RP displacement/reaction and SDV1 maxima are retained in results/validation/adaptive_job2_damage_contours_manifest.json and the compressed raw field export.

## Rendering and limitations

Integration-point means are plotted per companion element on the undeformed mesh, without spatial smoothing. The colour scale is fixed at 0-1; numerical overshoot is saturated in colour only and preserved in the data. Black lines in evolution panels show initial notches from the committed geometry config. White holes are absent material, not threshold masks.

Case 2 is the repository off-axis-hole Mode-I specimen, not paper Mode-II. Case 1 completed Exit 0; Cases 2/3/5 terminated Exit 1 according to reconciled F1859 evidence. Available converged fields are shown, not claimed completed fracture solutions. Case 3 only developed partial damage (maximum about 0.67) before termination, so selecting different frames cannot create the paper's full crack path.

The earlier Panasas storage wait cleared. Case 5 has now been extracted and plotted as well. Previous plots and failure evidence remain available in Git history.
