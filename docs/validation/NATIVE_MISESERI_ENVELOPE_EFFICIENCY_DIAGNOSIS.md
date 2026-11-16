# Native MISESERI efficiency diagnosis — 16 November 2026

Classification: EVALUATED_OFFLINE; improvement hypothesis prepared, NOT validated.
Master research goal remains OPEN. No framework/config/UEL edits, remeshing,
fracture solves, PBS submissions, or bridge dispatches were made by this task.

## Findings from authentic evidence

The inspected `results/figures/fig_f1813_four_benchmark_unified_synthesis.png`
shows broad fine zones in Cases 2, 3 and 5. A narrow crack line is not itself an
acceptance target: the finite phase-field process zone must remain resolved.

1. The common framework explicitly hardcodes `sizingMethod=UNIFORM_ERROR` in
   `execute_native_remesh`, even though the configurations have a sizing-method
   field. Abaqus describes this method as distributing global error and refining
   less-stressed regions too. Its native minimum/maximum method is a plausible
   alternative for localization, but can be problematic at singularities. This
   is an experiment to review, not a proven correction or a paper-parity claim.
2. `MultiStateRecoveryDonorBuilder.synthesize_envelope_odb` combines elementwise
   **maximum MISESERI with arithmetic-mean MISESAVG**. The pair does not generally
   belong to any physical recovery state. Abaqus sizing uses both fields.
   Native source fields do not make this synthesized pair an untouched native
   state or establish that it reproduces the paper's algorithm.
3. The read-only script opened all seven individual recovery ODBs for Cases 2/3
   and both envelope ODBs, verified matching instance/element support and unique
   field values, and reproduced max error exactly. Mean-stress residuals are
   6.10e-5 (Case 2) and 1.49e-8 (Case 3), consistent with stored precision.
   For the diagnostic proxy `(max E / mean A) / max(E/A)`, 38.13% and 46.32%
   of elements respectively exceed 1.01; 95th percentiles are 2.710 and 1.823.
   Medians are 0.868 and 0.982: mixing can increase **or decrease** this proxy.
   **This local ratio is not the UNIFORM_ERROR global sizing formula. These
   numbers establish altered field pairing, not a causal mesh-width reduction.**
4. Gate 06 is `mean(h_far)/mean(h_process)` using unweighted element means of
   sqrt(area), classified by geometry. Case 2's process label is a hole vicinity;
   Case 3 uses notch-root and hole-boundary vicinities. Other propagation-path
   elements are counted as far field. Consequently 1.55x/1.65x are size-contrast
   metrics under those masks, not measured coarsening versus an earlier mesh or
   actual solver speedups. Preserve their FAIL status and thresholds; supplement
   rather than silently redefine them.
5. Case 5 uses the single-state seven-hole donor. A multi-state maximum-envelope
   explanation does not account for its broad refinement. The common sizing
   method is relevant to investigating all four cases.

Full donor hashes and numerical measurements are in
`results/validation/native_miseseri_envelope_efficiency.json`.

## Selected next scientific experiment

Test whether **native minimum/maximum sizing** reduces unnecessary refined area
while retaining the existing crack-resolution and mesh-quality requirements.
Keep the current F1812 meshes as immutable controls. Change only the sizing
method in the first comparison; hold geometry, donors, seeds, UEL, loading,
global size bounds and rate limits fixed. Because the methods have different
target semantics, predeclare the minimum/maximum target pair and bias in the
independent scientific review; a matching numeric percentage is not equal
accuracy. Do not launch a parameter sweep or tune each case to its known path.
Use one dimensionless policy across all four geometries, with declared physical
length-scale differences. Check the installed Abaqus API before implementation.

After review, implement the option in the **shared framework**, honoring the
configuration rather than forcing UNIFORM_ERROR. Generate Cases 1, 2, 3 and 5
from the same revision. Record all existing gates without weakening them, total
elements/DOFs, area-weighted h/l0 distributions and refined area, and authentic
damage-based posthoc process-zone coverage. Geometry/path labels may be used
only for evaluation, never as refinement input. Push four readable mesh images
and a common-scale 2x2 composite; bridge handoff must include commit-pinned
GitHub image paths and provenance. Inspect images before further instructions.
Do not infer force/energy accuracy or runtime savings from mesh images alone;
those require the existing reviewed Job-2 fracture validation sequence.

Only after isolating sizing-method effects, test a separate multi-state
construction: preserve each authentic state's MISESERI/MISESAVG pair in its own
step and apply overlapping whole-domain native rules, letting Abaqus reconcile
size demands. Abaqus documents this mechanism; its API feasibility, mesh
correspondence and benefit on these cases remain untested. It may preserve a
broad history union and is not guaranteed to reduce cost. Do not substitute
percentile clipping, damage-derived sizes, manually drawn corridors or a
selected-error/selected-stress envelope without separately reviewing its
meaning under global normalization.

Full-history preanalysis is a two-pass/offline method, not evidence of predictive
online remeshing. Sequential causal windows and state transfer remain a later
scientific phase under the current project restrictions.

## Literature and reproducibility

Pandey and Kumar demonstrate a coarse MISESERI-driven preanalysis followed by
refined phase-field analysis. Their reported efficiency does not establish that
our synthesized envelope or Gate 06 reproduces their measures. Compare matched
geometry, material, loading, length scale and convergence criteria before
claiming reproduction:
https://www.techscience.com/CMES/v144n3/63944/html

Abaqus primary documentation on global uniform-error versus minimum/maximum
sizing, paired base fields and overlapping rules:
https://docs.software.vt.edu/abaqusv2026/English/SIMACAEANLRefMap/simaanl-c-adpsizing.htm

MISESERI has no intrinsic accumulated-history record:
https://docs.software.vt.edu/abaqusv2026/English/SIMACAEANLRefMap/simaanl-c-adperrorindicators.htm

Command (completed Exit 0; ODBs readOnly=True):
`C:\SIMULIA\Commands\abaqus.bat python scripts/validation/analyze_miseseri_envelope_efficiency.py`

Framework examined: SHA256
`4276A5DC1AF22A6A117102D8C24492789E8AA4EBFD4AF079C58EE86DBEEC7C8B`.
Frozen UEL and all established numerical acceptance thresholds remain unchanged.
