# SDV15 Candidate Explanation Tests

Classification: `sdv15_explanation_tests_complete_from_retained_outputs`

| Explanation | Evidence supporting it | Evidence contradicting it | Events explained | Applies to worst event |
|---|---|---|---:|---|
| A. U1 and U2 are written on different calls within the same increment | Source has separate U1 and U2 UEL branches and U2 reads either `USRVAR(...,15,...)` or `USRVAR(...,14,...)` depending on `STEPITER`. | Retained outputs do not store call-level ordering or `STEPITER` per frame/IP. | `0` conclusively; contributes to output insufficiency for `817` | yes, as a possible but unproven explanation |
| B. SDV14 and SDV15 represent displacement-layer and phase-layer synchronization stages | Source assigns SDV14 in U2 and SDV15 in U1; 480 above-precision events were already explained by local SDV14/SDV15 mismatch. | The remaining 817 have mismatch smaller than the SDV15 drop, so this simple test does not explain them. | `480` from the prior detailed review, not part of the 817 | no for the worst event |
| C. Visualization STATEV contains a copied value from a preceding call | UMAT copies `USRVAR` into `STATEV`, and output timing is not instrumented. | No retained call-level evidence proves a preceding-call copy for a specific event. | `0` conclusively; contributes to output insufficiency for `817` | possible but unproven |
| D. Integration-point ordering differs between one or more layers | UMAT explicitly swaps ODB CPS4 IP 3 and 4 before reading `USRVAR`. | After applying the documented swap, U1/U2/source-storage IPs are consistent; this is not an error. | `0` as an error; mapping resolved for `817` | no |
| E. Visualization label-to-physical offset is incorrect for part of the mesh | Full-deck mapping was tested. | All `N_ELEM` labels and connectivity match one-to-one across U1, U2, and CPS4. | `0` | no |
| F. Phase genuinely decreases between equivalent completed phase-update states | Retained SDV15 output decreases exist above precision. | Equivalent completed phase-update states cannot be constructed from the retained event table/output fields; SDV16 remains monotone at affected locations. | `0` confirmed | no confirmed result |

Worst-event revised category: `insufficient_output_evidence`.
