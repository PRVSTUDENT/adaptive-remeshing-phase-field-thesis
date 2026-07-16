# SDV15 Mapping Resolution Decision

Decision: `sdv15_mapping_resolution_incomplete`

Revised mutually exclusive category counts for the 817 previously mapped as `insufficient_mapping_evidence`:

| Category | Count |
|---|---:|
| `staggered_sync_effect` | `0` |
| `copied_visualization_state_lag` | `0` |
| `retained_precision_effect` | `0` |
| `possible_irreversibility_violation` | `0` |
| `insufficient_output_evidence` | `817` |
| `mapping_error` | `0` |

Worst-event classification: `insufficient_output_evidence`.

Completed-state monotonicity result:

- affected element/IP locations in the 817-event set: `128`
- completed phase-state sequence constructible from retained event/output evidence: `false`
- completed-state nonmonotone count: `not determined`
- largest retained-output decrease in the 817 set: see `sdv15_completed_phase_state_monotonicity.csv`
- SDV16 matching-location decreases: `0` in the prior detailed review

Consequence for the existing SDV15 detailed decision:

- `sdv15_detailed_review_incomplete` remains appropriate.
- The blocker is now narrower: mapping is resolved, but output frequency/source call timing evidence is insufficient.

Consequence for candidate-v2 scientific classification:

- `paper_matched_v2_scientific_review_incomplete` remains unchanged.

Consequence for Gate A3:

- Gate A3 remains `reference_data_insufficient`.
- Even a future SDV15 resolution would not automatically close Gate A3 because post-peak RF-U mismatch, approximate Fig. 7 reference quality, and supervisor-approved tolerances remain independent blockers.

Whether another solution run would provide necessary new evidence:

- A new solution run is not authorized here.
- If supervisor review requires closure of the 817 events, the missing evidence would be call-level or increment-level instrumentation/output that records U1 completed phase-update states and `STEPITER` timing. The current retained ODB/event table is insufficient for that proof.
