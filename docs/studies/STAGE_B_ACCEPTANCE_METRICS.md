# Stage B Acceptance Metrics

Status: `h_convergence_subset_authorized_execution_pending`

These metrics define what Stage B evidence must contain. They do not close
Gate A3 or define final thesis tolerances. The supervisor has authorized only
the Molnar `lc = 0.015 mm` h-convergence subset for execution. Length-scale,
load-increment, MISESERI, and remeshing acceptance work remain unauthorized.

For the authorized subset, provisional descriptive metrics are defined in
`docs/studies/MOLNAR_LC015_H_CONVERGENCE_ACCEPTANCE.md`. No final numerical
convergence tolerance is claimed unless the supervisor later approves one.

## Technical Classification

Use:

- `stage_b_technical_pass`
- `stage_b_technical_fail`
- `stage_b_evidence_incomplete`

Technical pass requires normal Abaqus completion, retained lightweight solver
evidence, extraction success, and complete resource records.

## Scientific Classification

Use:

- `stage_b_mesh_convergence_incomplete`
- `stage_b_mesh_convergence_review_required`
- `stage_b_mesh_convergence_accepted`
- `stage_b_length_scale_review_required`
- `stage_b_load_increment_review_required`
- `stage_b_uniform_reference_selected`
- `stage_b_uniform_reference_rejected`

Scientific labels remain separate from technical completion.

## RF--Displacement Metrics

Required values:

- peak RF2;
- displacement at peak RF2;
- final RF2;
- final displacement;
- pre-peak RMSE;
- post-peak RMSE;
- full-overlap RMSE;
- full-overlap NRMSE;
- maximum absolute force error;
- common-domain area-under-curve error.

Rules:

- interpolate curves onto a common displacement grid;
- split pre-peak and post-peak metrics;
- compare mesh levels against the next finer completed uniform mesh;
- compare to approximate Fig. 7 only as
  `approximate_published_reference_comparison`;
- record digitization uncertainty separately from mesh convergence.

No final acceptance threshold is assigned here. Candidate provisional
thresholds may be proposed only in the run-specific decision note after the
supervisor approves the route.

## Crack-Path Metrics

Use element-mean `SDV15` from the visualization layer.

Required thresholds:

- `SDV15 >= 0.50`
- `SDV15 >= 0.80`
- `SDV15 >= 0.90`
- `SDV15 >= 0.95`
- `SDV15 >= 0.99`

Required values:

- damaged element count;
- connected component count;
- largest connected component count;
- connected extension beyond the notch tip;
- total connected damaged path length;
- furthest connected `x`;
- maximum vertical deviation;
- mean vertical deviation;
- disconnected damaged elements.

Crack-path convergence should be evaluated at matched displacement states and
at final displacement. Final acceptance tolerances remain supervisor pending.

## SDV15 and SDV16 Metrics

Required values:

- SDV15 minimum and maximum;
- SDV15 overshoot above 1;
- SDV15 decrease count in retained frames;
- completed-increment SDV15 decrease count when final-increment data exist;
- SDV15 decrease counts above `1e-8`, `1e-6`, and `1e-5`;
- worst SDV15 decrease and location;
- SDV16 decrease count over the same monitored locations;
- pre-peak versus post-peak occurrence.

Interpretation:

- strict-irreversibility route: completed-increment SDV15 decrease above the
  approved tolerance is a stop;
- accepted-with-limitation or waiver route: SDV15 decreases are allowed only as
  an explicit limitation and must be reported in summaries and captions;
- SDV16 decreases always require review before the next run.

## Runtime and Memory Metrics

Required values:

- requested CPUs, memory, walltime, queue, and modules;
- used walltime, CPU time, CPU percent, memory, and virtual memory;
- Abaqus peak memory if available;
- equation count;
- increment count;
- iteration count;
- matrix decompositions;
- cutbacks;
- warnings and error messages;
- output size and scratch retention path.

Stop and re-estimate before the next run if used walltime or memory exceeds
75 percent of the request, or if the next mesh level is predicted to exceed the
approved resource envelope.

## Uniform Reference Selection

The uniform fine reference can be selected only after:

- the supervisor route permits Stage B;
- each contributing run has technical pass status;
- RF--U convergence is accepted under supervisor-approved metrics;
- crack-path convergence is accepted under supervisor-approved metrics;
- SDV15/SDV16 behavior is compatible with the selected route;
- resource evidence is complete;
- evidence paths and hashes are recorded.
