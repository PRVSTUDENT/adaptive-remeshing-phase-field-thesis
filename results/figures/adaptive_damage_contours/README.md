# Adaptive Job-2 damage contours

Status: Cases 1, 2 and 3 exported and plotted; Case 5 extraction remains in cluster filesystem I/O wait. Existing F1859 Job-2 results only; no new simulation or adaptive remeshing.

Each evolution panel includes the existing adaptive mesh followed by four
recorded SDV1 states: approximately 90% of peak displacement on the ascending
branch, the recorded state closest to peak displacement from the reaction-force
history, the midpoint of the remaining recorded frames, and the last available
converged state. Individual state PNGs are also supplied. Frame indices are
zero-based; frameId, step time, displacement, force and maximum SDV1 are recorded
in `results/validation/adaptive_job2_damage_contours_manifest.json`.

Values are integration-point means within each companion element, plotted on
the undeformed mesh without spatial smoothing. The fixed colour scale is 0-1;
any numerical overshoot is saturated in colour only and preserved in raw data.
White holes are actual missing material, not a damage threshold mask.

Case 2 is the repository's off-axis-hole Mode-I specimen. It is not the paper's
Mode-II shear specimen. Case 1 completed with Exit 0; Cases 2, 3 and 5 terminated
with Exit 1 according to the reconciled F1859 solver evidence. Their available
converged frames are useful contours but do not establish completed simulations.
In particular, Case 3's incomplete damage evolution must not be represented as
a fully developed paper crack path.
