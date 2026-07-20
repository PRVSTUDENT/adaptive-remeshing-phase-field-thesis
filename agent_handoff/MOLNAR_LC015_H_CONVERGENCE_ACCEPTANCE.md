# Molnar lc = 0.015 mm h-Convergence Acceptance Metrics

Status: `provisional_descriptive_metrics`

These metrics define what evidence the authorized three-case study must
produce. They do not close Gate A3 and do not assign final thesis tolerances.

## Technical Classification

| Case | Pass label | Fail label |
|---|---|---|
| H0 | `molnar_h0_exact_technical_pass` | `molnar_h0_exact_technical_fail` |
| H1 | `molnar_h1_h0025_technical_pass` | `molnar_h1_h0025_technical_fail` |
| H2-PUB | `molnar_h2_pub_h001_technical_pass` | `molnar_h2_pub_h001_technical_fail` |

Technical pass requires:

- Abaqus return code zero;
- ODB, STA, MSG, DAT present;
- STA successful-completion statement;
- retained lightweight solver evidence;
- Abaqus/CAE postprocessing attempted after technical solve success;
- resource records retained.

Postprocessing failure must not be reclassified as a solver failure.

## Static Validation Before Submission

| Case | Required classification |
|---|---|
| H0 | `exact_author_inputs_verified` |
| H1 | `h_convergence_static_validation_pass` |
| H2-PUB | `h_convergence_static_validation_pass` and `publication_resolution_verified` |
| All | `runnable: true` |

If any static validation fails, stop without submitting any job.

## Scientific Classification

Use only provisional labels until supervisor-approved tolerances exist:

- `h_convergence_scientific_review_pending`
- `h_convergence_scientific_review_incomplete`
- `h_convergence_review_required`
- `h_convergence_descriptive_trend_only`

Do not automatically claim convergence because one metric is small.

## Required Metrics

For each completed case:

- peak RF2 and U2 at peak;
- final RF2 and final U2;
- initial tangent stiffness;
- area under RF2-U2;
- crack-initiation displacement (documented SDV15 rule);
- final crack extension at documented SDV15 thresholds;
- final crack direction;
- runtime, CPU time, memory;
- physical and layered element counts;
- measured local corridor `h` and `h/lc` statistics.

Successive comparisons at common U2 coordinates:

- H0 versus H1;
- H1 versus H2-PUB;
- full-curve, pre-peak, and post-peak normalized differences;
- force difference at matched U2 states.

External comparison:

- H0, H1, and H2-PUB versus approximate digitized Fig. 7 `lc = 0.015 mm` curve.

Main convergence evidence is successive-mesh change, not the publication curve
alone.

## Provisional Descriptive Thresholds

All numerical thresholds are provisional descriptive aids only. No final
acceptance threshold is claimed here.

Suggested reporting bands for review discussion only:

| Metric | Review discussion band |
|---|---|
| successive peak-force relative change | report absolute and relative values |
| successive peak-displacement relative change | report absolute and relative values |
| successive full-curve NRMSE | report value; do not auto-pass |
| measured H2 local corridor h | 0.001 mm within documented generation tolerance |
| H0 hash identity | exact match required |

## Reference Class

Fig. 7 `lc = 0.015 mm` is:

`approximate_digitized_publication_reference`

not:

`exact_author_data`
