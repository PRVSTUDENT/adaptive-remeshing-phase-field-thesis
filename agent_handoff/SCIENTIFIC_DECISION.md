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

Retained category counts:

| Population | Count | Decision |
|---|---:|---|
| Smaller than ODB precision | `4816` | `numerical_roundoff` or below retained-precision concern |
| Staggered sync candidates | `1764` | `staggered_sync_effect` candidate |
| Same-location consecutive frames | `6113` | location persistence only; not a physical-healing classification |
| Genuine-healing candidates by current script | `817` | `possible_irreversibility_violation` / unresolved |
| Near step transition | `0` | not a step-transition artifact in the retained summary |

Magnitude-distribution limitation:

The committed scientific-review artifacts preserve category counts and the largest event, but they do not preserve the raw 6113-event table. Therefore the median decrease, tolerance-bin counts for `1e-12`, `1e-10`, `1e-8`, and `1e-6`, exact number of affected integration points, full spatial concentration map, frame histogram, and equivalent phase-update-state comparison cannot be reconstructed from the retained local evidence alone.

Decision:

- `4816` events smaller than the ODB precision tolerance should not be treated as physical healing.
- `1764` staggered-sync candidates are plausibly tied to the staggered phase/displacement update sequence.
- `817` events remain possible irreversibility violations or unresolved until their raw event table and equivalent-update-state comparison are retained.
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
- Raw `SDV15` decrease event table is not retained locally, so the median, tolerance-bin counts, affected integration-point count, frame histogram, and equivalent phase-update-state comparison are unavailable.
- Reconstruction choices, post-peak reference ambiguity, and model response are not yet separable.

Consequence for Gate A3:

Gate A3 remains `reference_data_insufficient`. It is not passed.

Future solution-run justification:

No future solution run is scientifically justified from this decision alone. The next justified action is evidence review: retain or regenerate no-solution SDV15 event details from the existing ODB if needed, define supervisor-approved tolerances, and decide whether the approximate Fig. 7 reference is sufficient for a provisional paper-matched baseline claim.
