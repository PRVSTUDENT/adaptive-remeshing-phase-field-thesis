# Scientific Decision - Paper-Matched Single-Notch v2

Date: 2026-07-16

Classification:

```text
paper_matched_v2_scientific_review_incomplete
```

Gate A3:

```text
reference_data_insufficient
```

No new Abaqus solution run, PBS submission, retry, remeshing run, MISESERI run, state-transfer run, parameter sweep, or candidate-v2 deck/source modification is justified by this decision.

## Decision Rationale

Candidate v2 is technically valid and qualitatively promising, but the current retained evidence cannot yet support either a provisional scientific pass or a scientific fail. The peak response is close enough to motivate continued review, the crack direction is qualitatively correct, and `SDV16` is monotone. Contrary evidence remains substantial: the post-peak RF-U mismatch is large, `SDV15` has unresolved late decreases and overshoot, and the Fig. 7 reference is approximate digitized evidence rather than exact author data or a supervisor-approved tolerance basis.

The defensible classification is therefore `paper_matched_v2_scientific_review_incomplete`.

## RF-Displacement Decision

The RF-U mismatch is concentrated mainly post-peak. The pre-peak branch is stiffer than the digitized reference, but its RMSE is much smaller than the post-peak RMSE. Peak force is promising but outside the recorded digitization uncertainty. Peak displacement is also outside the recorded digitization uncertainty. The full-overlap NRMSE alone should not decide the model because it mixes a tolerable-looking pre-peak branch with a much larger post-peak mismatch.

Reference uncertainty from the Fig. 7 digitization metadata:

- displacement: `+/-0.00004 mm`
- reaction force: `+/-0.015 kN`

| Metric | Value | Uncertainty decision |
|---|---:|---|
| Pre-reference-peak RMSE | `0.044136 kN` | outside force uncertainty |
| Pre-reference-peak NRMSE | about `0.062` | no direct uncertainty band; driven by force RMSE outside uncertainty |
| Post-reference-peak RMSE | `0.348093 kN` | outside force uncertainty |
| Post-reference-peak NRMSE | about `0.490` | no direct uncertainty band; clearly dominant mismatch |
| Full-overlap NRMSE | `0.245705` | no direct uncertainty band; not sufficient alone |
| Peak-force error | `+0.046166 kN`, relative `0.064519` | outside force uncertainty |
| Peak-displacement error | `+0.000242 mm`, relative `0.041257` | outside displacement uncertainty |
| Initial tangent-stiffness error | about `+51.4%` | outside the digitization-only explanation |
| Common-domain area error | `+0.193324` relative | outside a small digitization-only explanation |
| Maximum force error | `0.691897 kN` | outside force uncertainty |

Interpretation:

- Pre-peak: model is systematically stiffer than the digitized reference, but the mismatch is moderate compared with post-peak.
- Peak: force and displacement are promising in shape and scale, but both exceed digitization uncertainty.
- Post-peak: mismatch is large and dominates the full-curve error.
- Source of mismatch: cannot be assigned uniquely. It may involve reconstruction assumptions, approximate red-curve digitization/post-peak pixel ambiguity, and/or model response. The evidence does not justify calling it only digitization noise.

## SDV15 Decision

Retained ODB scan summary:

- Total `SDV15` decrease candidates: `6113`
- Tolerance used by the scan: `1e-8`
- ODB precision tolerance recorded by the scan: `1e-6`
- Worst decrease: `0.000425219535828`
- Worst-decrease location: element `84131`, integration point `3`
- Worst-decrease transition: global frame `189` to `190`, Step-2 frame `88` to `89`
- `SDV15` maximum: `1.005600094795227`
- First overshoot above one: `U2 = 0.0063299997709691525 mm`
- Maximum overshoot: `0.005600094795227051` at `U2 = 0.006500000134110451 mm`

Historical retained category counts from the first scan:

| Population | Count | Decision |
|---|---:|---|
| Smaller than ODB precision | `4816` | `numerical_roundoff` or below retained-precision concern |
| Staggered sync candidates | `1764` | `staggered_sync_effect` candidate |
| Same-location consecutive frames | `6113` | location persistence only; not a physical-healing classification |
| Genuine-healing candidates by current script | `817` | `possible_irreversibility_violation` / unresolved |
| Near step transition | `0` | not a step-transition artifact in the retained summary |

Detailed no-solution reconstruction:

The existing scratch ODB was reopened read-only with Abaqus Python and processed without a new solution run. The detailed review is preserved under `sdv15_detailed_review/`.

| Detailed metric | Value |
|---|---:|
| Reconstructed decrease events | `6113` |
| Unique event keys | `6113` |
| Events greater than ODB precision `1e-6` | `1297` |
| Affected visualization elements | `309` |
| Affected integration-point locations | `613` |
| Median decrease | `3.725290298461914e-08` |
| Mean decrease | `1.0167550329113368e-05` |
| 99th percentile decrease | `0.0001771569252014161` |
| Worst decrease | `0.0004252195358276367` |
| Overshoot rows | `769` |
| Unique overshoot locations | `78` |
| SDV16 decreases at SDV15 > precision event locations | `0` |

Equivalent-state categories for the `1297` events greater than ODB precision:

| Category | Count |
|---|---:|
| `staggered_sync_effect` | `480` |
| `insufficient_mapping_evidence` | `817` |

Follow-up source/deck mapping resolution:

| Mapping-resolution metric | Value |
|---|---:|
| Physical elements checked for U1/U2/CPS4 mapping | `33852` |
| Label/connectivity mapping failures | `0` |
| Previously insufficient-mapping-evidence events reviewed | `817` |
| Reclassified as `insufficient_output_evidence` | `817` |
| Reclassified as `mapping_error` | `0` |
| Affected element/IP locations in the 817-event set | `128` |

The follow-up mapping resolution proves the layer labels, offsets, connectivity equivalence, and UMAT integration-point swap. It does not construct equivalent completed U1 phase-update states because the retained ODB/event-table evidence does not expose the within-increment U1 call sequence or `STEPITER` state at output time.

Detailed SDV15 decision:

```text
sdv15_detailed_review_incomplete
```

The detailed reconstruction resolves the missing raw event table and confirms that the historical count was reproducible. The follow-up mapping resolution removes label/connectivity/IP mismatch as an explanation, but it does not prove equivalent completed phase-update states for the remaining `817` non-staggered events above ODB precision. It therefore cannot convert the SDV15 item into a clean pass. `SDV16` remains monotone at the checked locations.

Decision:

- `4816` events smaller than the ODB precision tolerance should not be treated as physical healing.
- `1764` staggered-sync candidates are plausibly tied to the staggered phase/displacement update sequence.
- `817` events remain unresolved as `insufficient_output_evidence`: their label/IP mapping is resolved, but the retained outputs do not prove equivalent completed phase-update states for those non-staggered decreases.
- The detailed reconstruction retains the raw event table and the follow-up mapping resolution retains a full-element label/connectivity proof, but the `817` non-staggered events remain not proven harmless.
- The current evidence does not support classifying all `6113` decreases as physical healing.
- The current evidence also does not support dismissing all `6113` decreases as harmless.

## Crack-Path Decision

Original notch tip is at approximately `x = 0`. The final state remains connected and approximately horizontal at all retained high-damage thresholds. The measured extension is threshold dependent.

| Threshold | New extension beyond notch tip (mm) | Total connected damaged path (mm) | Furthest connected x (mm) | Connected damaged elements | Disconnected damaged elements | Max vertical deviation (mm) | Mean vertical deviation (mm) |
|---:|---:|---:|---:|---:|---:|---:|---:|
| `0.80` | `0.0555` | `0.0570` | `0.0555` | `427` | `0` | `0.003500` | `0.001917` |
| `0.90` | `0.0525` | `0.0530` | `0.0525` | `278` | `0` | `0.002500` | `0.001349` |
| `0.95` | `0.0505` | `0.0510` | `0.0505` | `193` | `0` | `0.001500` | `0.000966` |
| `0.99` | `0.0465` | `0.0460` | `0.0465` | `94` | `0` | `0.000500` | `0.000500` |

Decision:

`0.0505 mm` is best interpreted as the connected high-damage core at the provisional `SDV15 >= 0.95` threshold. It is not necessarily the full diffuse crack extension. Because lower thresholds show a longer connected band and no disconnected damage at the final state, the short extension is strongly threshold dependent. The evidence supports a short, horizontal, connected crack, but not a claim that the full diffuse crack is only `0.0505 mm`.

## Response-State Decision

The retained response states cover early loading, late pre-peak loading, near-peak response, and final post-peak response:

| State | U2 (mm) | RF2 (kN) | max SDV15 | Decision |
|---|---:|---:|---:|---|
| early loading | `0.002000` | `0.267289` | `0.038741` | no high-damage crack; low diffuse damage |
| late pre-peak | `0.005000` | `0.646290` | `0.311988` | damage growing, no high-damage crack |
| near peak | `0.005990` | `0.755578` | `0.717876` | phase field has grown strongly; high-damage threshold not yet reached |
| final post-peak | `0.006700` | `0.749110` | `1.004140` | connected horizontal high-damage crack exists |

Response-state conclusions:

- Damage initiates in the expected notch-tip region according to the connected final crack geometry and near-peak damage growth.
- The connected crack path remains approximately horizontal.
- The force response reaches peak near the state where the phase field has grown substantially, then ends with a connected high-damage band.
- The final state is physically plausible for a short post-peak propagation state, but the RF-U post-peak mismatch is too large to call this a scientific pass.
- The retained threshold metrics do not show disconnected high-damage elements outside the expected fracture region at the final state.

## Classification

Assigned classification:

```text
paper_matched_v2_scientific_review_incomplete
```

Supporting evidence:

- Technical execution passed as `paper_matched_v2_technical_pass`.
- Peak force scale is promising: relative peak-force error `0.064519`.
- Crack direction is qualitatively correct and horizontal.
- Final high-damage crack components are connected with no disconnected high-damage elements at thresholds `0.80` to `0.99`.
- `SDV16` decrease count is `0`.
- Solver behavior is technically clean: `0` cutbacks and `0` errors.

Contrary evidence:

- Post-peak RF-U mismatch is large: post-reference-peak RMSE `0.348093 kN`.
- Maximum force error `0.691897 kN` is far outside digitization uncertainty.
- Initial tangent stiffness is about `51.4%` higher than the digitized reference fit.
- `SDV15` has `6113` retained decrease candidates and late overshoot up to `1.005600`.
- Peak force and peak displacement both exceed recorded digitization uncertainty.

Unresolved limitations:

- The Fig. 7 curve is approximate digitized reference data, not exact author data.
- Supervisor-approved tolerances are not yet defined.
- Raw `SDV15` decrease event details are now retained in `sdv15_detailed_review/`, and layer mapping is resolved in `sdv15_mapping_resolution/`, but equivalent completed phase-update-state proof remains unavailable for `817` events above ODB precision.
- Reconstruction choices, post-peak reference ambiguity, and model response are not yet separable.

Consequence for Gate A3:

Gate A3 remains `reference_data_insufficient`. It is not passed.

Future solution-run justification:

No future solution run is scientifically justified from this decision alone. The next justified action is evidence review: retain or regenerate no-solution SDV15 event details from the existing ODB if needed, define supervisor-approved tolerances, and decide whether the approximate Fig. 7 reference is sufficient for a provisional paper-matched baseline claim.
