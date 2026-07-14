# Molnar Single-Notch Scientific Check

Date: 2026-07-14

Gate A3 classification: `reference_data_insufficient`

## Reference Status

- RF-U numeric reference available: `False`
- RF-U reference point count: `0`
- Reason: No numeric RF-U reference coordinates are available.
- Crack-path reference: qualitative horizontal ligament `y=0` from Fig. 6 tensile pattern and specimen geometry.

## Simulation RF-U Metrics

| Metric | Value |
|---|---:|
| `initial_tangent_interval_u2` | `[0.0, 0.001]` |
| `initial_tangent_stiffness` | `134.61836741478172` |
| `peak_reaction_force` | `0.7276078462600708` |
| `displacement_at_peak` | `0.006099999882280827` |
| `area_under_rf_u` | `0.0025813742959418418` |
| `post_peak_force_drop` | `0.7262126157293096` |
| `final_residual_force` | `0.0013952305307611823` |
| `final_displacement` | `0.007000000216066837` |

## Bounds and Irreversibility

| Quantity | Min | Max | Below 0 count | Above 1 count |
|---|---:|---:|---:|---:|
| `SDV14` | 0.000000e+00 | 1.010492e+00 | 0 | 57 |
| `SDV15` | 0.000000e+00 | 1.010493e+00 | 0 | 57 |
| `SDV16` | 0.000000e+00 | 3.377802e+02 | n/a | n/a |

- Maximum absolute `SDV14 - SDV15`: `3.744406e-02`
- `SDV16` decrease count: `0`; worst drop `0.000000e+00`
- `SDV15` decrease count: `583`; worst drop `2.278090e-04`
- `SDV15` largest decrease event: `{'drop': 0.00022780895233154297, 'previous_value': 0.9881207346916199, 'current_value': 0.9878929257392883, 'previous_step': 'Step-2', 'previous_frame': 15, 'previous_global_frame': 66, 'previous_step_time': 0.15000000596046448, 'previous_rp_u2': 0.006500000134110451, 'step': 'Step-2', 'frame': 16, 'global_frame': 67, 'step_time': 0.1599999964237213, 'rp_u2': 0.006599999964237213, 'element': 8300, 'integration_point': 1, 'near_step_transition': False, 'smaller_than_odb_precision': False, 'staggered_sync_candidate': False, 'current_abs_sdv14_minus_sdv15': 1.1920928955078125e-07, 'previous_abs_sdv14_minus_sdv15': 6.9141387939453125e-06}`
- `SDV15` decrease categories: `{'same_location_consecutive_frames': 583, 'near_step_transition': 0, 'smaller_than_odb_precision': 364, 'staggered_sync_candidate': 13, 'genuine_healing_candidate': 217}`
- `SDV15` unique overshoot integration points: `11`
- `SDV15` max overshoot event: `{'step': 'Step-2', 'frame': 20, 'global_frame': 71, 'step_time': 0.20000000298023224, 'rp_u2': 0.007000000216066837, 'element': 8196, 'integration_point': 2, 'value': 1.0104930400848389, 'overshoot': 0.010493040084838867}`
- `SDV15` overshoot duration: `{'first_global_frame': 64, 'last_global_frame': 71, 'frame_span': 8, 'first_rp_u2': 0.006300000008195639, 'last_rp_u2': 0.007000000216066837}`
- Overshoot limited to final unstable stage by provisional rule `U2 >= 0.006`: `True`

## Crack Path Diagnostics

Phase threshold: `d_crit = 0.950`.

| Target U2 | Damaged elements | Connected | Extension | Max vertical deviation | Mean deviation |
|---:|---:|---|---:|---:|---:|
| 0.002000 | 0 | `False` | 0.0 | None | None |
| 0.005000 | 0 | `False` | 0.0 | None | None |
| 0.006000 | 0 | `False` | 0.0 | None | None |
| 0.007000 | 136 | `True` | 0.49713271849999996 | 0.01005856843 | 0.004411853957941176 |

## Energy Diagnostics

- External work from trapezoidal RF-U integration: `2.581374295942e-03`
- Global degraded/undamaged elastic energy integration from `SDV12`/`SDV13`: `insufficient_in_current_extraction_requires_integration_weights_or_controlled_output_enabled_run`
- Crack-surface functional integration: `insufficient_current_odb_does_not_provide_a_valid_global_grad_d_integration_contract`

## Tolerance Status

`configs/validation/stage_a_single_notch_tolerances.json` keeps supervisor-approved tolerances pending. No unconditional scientific pass is allowed from this check.
