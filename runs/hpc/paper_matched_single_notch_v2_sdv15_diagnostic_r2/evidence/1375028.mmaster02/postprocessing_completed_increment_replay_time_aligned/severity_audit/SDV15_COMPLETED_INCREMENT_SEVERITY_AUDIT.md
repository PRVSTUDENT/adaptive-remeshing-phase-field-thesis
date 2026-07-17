# SDV15 Completed-Increment Severity Audit

Decision: `sdv15_completed_increment_irreversibility_violation`

This is a no-solution audit of the completed-increment transition table.
It does not authorize or require a new Abaqus/PBS run.

## Key Counts

- Unique violating transitions: `2184`
- Unique affected element/IP locations: `138`
- Repeated affected locations: `136`
- Before or at peak displacement: `0`
- After peak displacement: `2184`
- Coincident with SDV15 overshoot above one: `773`
- SDV16 decreases over same transitions: `0`

## Magnitudes

- Max decrease: `0.00022384088238425193`
- Mean decrease: `2.8434597987446906e-05`
- Median decrease: `1.3940791172561973e-05`
- Magnitude bins: `{'(1e-6,1e-5]': 769, '(1e-5,1e-4]': 1265, '>1e-4': 97, '(1e-8,1e-6]': 53}`
- Tolerance sensitivity: `{'1e-10': 2184, '1e-08': 2184, '1e-06': 2131, '1e-05': 1362}`

## Largest Transition

```json
{
  "abs_centroid_y": 0.00050000035,
  "after_peak": true,
  "before_or_at_peak": false,
  "centroid_x": 0.0015,
  "centroid_y": -0.00050000035,
  "current_kinc": "144",
  "current_kstep": "2",
  "current_phase_after_u1": "0.9984153700625438",
  "current_sdv16_history": "268.6812257113632",
  "current_time2": "1.8470588235294088",
  "current_u2_mm": 0.006694117647058817,
  "magnitude_bin": ">1e-4",
  "near_crack_axis_abs_y_le_0p02": true,
  "near_notch_left_half_x_le_0": false,
  "phase_drop": "0.00022384088238425193",
  "phase_overshoot_in_transition": false,
  "physical_element": "16428",
  "previous_kinc": "143",
  "previous_kstep": "2",
  "previous_phase_after_u1": "0.998639210944928",
  "previous_sdv16_history": "268.6812257113632",
  "previous_time2": "1.8411764705882323",
  "relative_drop": 0.00022414589766853854,
  "sdv16_drop": "0.0",
  "source_storage_ip": "4"
}
```

## Spatial Proxy

Coordinates are U1 element centroids from the diagnostic input deck.
The crack-corridor proxy is `abs(centroid_y) <= 0.02`; the notch-side proxy is `centroid_x <= 0`.

- Near crack-axis proxy count: `2184`
- Notch-side proxy count: `53`
