# SDV15 Detailed Event Decision

Decision: `sdv15_detailed_review_incomplete`

- SDV15 decrease events reconstructed: `6113`
- Prior legacy count expected: `6113`
- Count match: `True`
- Events greater than ODB precision: `1297`
- Equivalent-state categories: `{'staggered_sync_effect': 480, 'insufficient_mapping_evidence': 817}`
- SDV16 decrease count at all scanned locations: `0`
- SDV16 decrease flags at SDV15 > precision event locations: `0`

Incomplete basis:
- some decreases greater than ODB precision lack equivalent-update-state proof
- follow-up source/deck mapping resolution proved the U1/U2/CPS4 label and IP mapping, but reclassified the 817 non-staggered events as `insufficient_output_evidence` because the retained outputs do not expose the completed within-increment U1 phase-update sequence

This decision applies only to the detailed SDV15 event reconstruction. It does not promote the overall paper-matched candidate-v2 scientific classification; Gate A3 remains `reference_data_insufficient`.
