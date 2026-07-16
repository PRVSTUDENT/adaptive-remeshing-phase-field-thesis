# Scientific Review Summary

Classification: `paper_matched_v2_scientific_review_incomplete`

Technical execution is closed successfully as `paper_matched_v2_technical_pass`. The current scientific review does not justify a new solution run, retry, remeshing run, MISESERI run, state transfer, parameter sweep, or candidate-v2 modification.

## Current Interpretation

- Technical execution: passed.
- Peak-response comparison: promising but provisional.
- Full RF-U comparison: substantial mismatch requiring decomposition.
- Crack propagation: short final connected crack at high SDV15 threshold; threshold sensitivity recorded.
- SDV16 irreversibility: passed.
- SDV15 irreversibility: detailed no-solution event reconstruction completed; still incomplete because 817 non-staggered decreases above ODB precision lack equivalent-update-state proof.
- Scientific result: `paper_matched_v2_scientific_review_incomplete`.
- Gate A3: `reference_data_insufficient`.

## Key Numbers

- Peak RF2: `0.761702 kN` at `U2 = 0.006110 mm`.
- Fig. 7 relative peak-force error: `0.064519`.
- Fig. 7 full-overlap NRMSE: `0.245705`.
- Final `SDV15 >= 0.95` crack extension: about `0.0505 mm`.
- SDV16 decrease count: `0`.
- SDV15 decrease count: `6113`.
- SDV15 detailed decision: `sdv15_detailed_review_incomplete`.
- SDV15 events above ODB precision: `1297` (`480` staggered-sync effects, `817` insufficient-mapping-evidence events).
- SDV16 decreases at SDV15 event locations above ODB precision: `0`.
- Solver cutbacks/errors: `0` cutbacks, `0` errors.
- Scientific decision: `paper_matched_v2_scientific_review_incomplete`.
- Decision report: `SCIENTIFIC_DECISION.md`.

## Artifacts

- `rf_u_verified.csv`
- `fig7_comparison_overlay.csv`
- `fig7_reference_grid_comparison.csv`
- `fig7_comparison_metrics.json`
- `crack_path_threshold_metrics.csv`
- `crack_path_aggregation_sensitivity.csv`
- `response_state_metrics.csv`
- `sdv_irreversibility_metrics.json`
- `sdv15_detailed_review/SDV15_DETAILED_EVENT_DECISION.md`
- `sdv15_detailed_review/sdv15_decrease_events_full.csv`
- `sdv15_detailed_review/sdv15_decrease_distribution.json`
- `sdv15_detailed_review/sdv15_equivalent_state_comparison.csv`
- `solver_resource_metrics.json`
- `SCIENTIFIC_DECISION.md`
- Audit Markdown files in this directory
