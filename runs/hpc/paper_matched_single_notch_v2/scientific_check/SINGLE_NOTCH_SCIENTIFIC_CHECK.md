# Molnar Single-Notch Scientific Check

Date: 2026-07-14

Gate A3 classification: `scientific_review_required`

## Reference Status

- RF-U numeric reference available: `True`
- RF-U reference point count: `91`
- Reason: None
- Crack-path reference: qualitative horizontal ligament `y=0` from Fig. 6 tensile pattern and specimen geometry.

## Simulation RF-U Metrics

| Metric | Value |
|---|---:|
| `final_displacement` | `0.00669999979436` |
| `peak_reaction_force` | `0.761702001095` |
| `post_peak_force_drop` | `0.0125915408134` |
| `final_residual_force` | `0.749110460281` |
| `initial_tangent_stiffness` | `134.265028421` |
| `displacement_at_peak` | `0.00610999995843` |
| `area_under_rf_u` | `0.00288304006002` |
| `initial_tangent_interval_u2` | `[0.0, 0.001]` |

## Bounds and Irreversibility

| Quantity | Min | Max | Below 0 count | Above 1 count |
|---|---:|---:|---:|---:|
| `SDV14` | 0.000000e+00 | 1.005594e+00 | 0 | 723 |
| `SDV15` | 0.000000e+00 | 1.005600e+00 | 0 | 769 |
| `SDV16` | 0.000000e+00 | 1.933705e+03 | n/a | n/a |

- Maximum absolute `SDV14 - SDV15`: `4.149508e-02`
- `SDV16` decrease count: `0`; worst drop `0.000000e+00`
- `SDV15` decrease count: `6113`; worst drop `4.252195e-04`
- `SDV15` largest decrease event: `{'step_time': 0.8941176533699036, 'current_abs_sdv14_minus_sdv15': 0.00021600723266601562, 'previous_frame': 88, 'integration_point': 3, 'smaller_than_odb_precision': False, 'rp_u2': 0.006519999820739031, 'frame': 89, 'drop': 0.0004252195358276367, 'step': 'Step-2', 'global_frame': 190, 'previous_rp_u2': 0.006500000134110451, 'previous_step_time': 0.8823529481887817, 'near_step_transition': False, 'previous_global_frame': 189, 'previous_abs_sdv14_minus_sdv15': 0.0002065896987915039, 'element': 84131, 'current_value': 1.000875473022461, 'previous_step': 'Step-2', 'staggered_sync_candidate': False, 'previous_value': 1.0013006925582886}`
- `SDV15` decrease categories: `{'genuine_healing_candidate': 817, 'staggered_sync_candidate': 1764, 'near_step_transition': 0, 'same_location_consecutive_frames': 6113, 'smaller_than_odb_precision': 4816}`
- `SDV15` unique overshoot integration points: `78`
- `SDV15` max overshoot event: `{'rp_u2': 0.006500000134110451, 'step': 'Step-2', 'step_time': 0.8823529481887817, 'integration_point': 1, 'frame': 88, 'global_frame': 189, 'overshoot': 0.005600094795227051, 'value': 1.005600094795227, 'element': 84677}`
- `SDV15` overshoot duration: `{'first_global_frame': 179, 'last_global_frame': 201, 'first_rp_u2': 0.0063299997709691525, 'frame_span': 23, 'last_rp_u2': 0.0066999997943639755}`
- Overshoot limited to final unstable stage by provisional rule `U2 >= 0.006`: `True`

## Crack Path Diagnostics

Phase threshold: `d_crit = 0.950`.

| Target U2 | Damaged elements | Connected | Extension | Max vertical deviation | Mean deviation |
|---:|---:|---|---:|---:|---:|
| 0.002000 | 0 | `False` | 0.0 | None | None |
| 0.005000 | 0 | `False` | 0.0 | None | None |
| 0.006000 | 0 | `False` | 0.0 | None | None |
| 0.006700 | 193 | `True` | 0.0505 | 0.0015000007 | 0.000966321495596 |

## Energy Diagnostics

- External work from trapezoidal RF-U integration: `2.883040060023e-03`
- Global degraded/undamaged elastic energy integration from `SDV12`/`SDV13`: `insufficient_in_current_extraction_requires_integration_weights_or_controlled_output_enabled_run`
- Crack-surface functional integration: `insufficient_current_odb_does_not_provide_a_valid_global_grad_d_integration_contract`

## Tolerance Status

`configs/validation/stage_a_single_notch_tolerances.json` keeps supervisor-approved tolerances pending. No unconditional scientific pass is allowed from this check.
