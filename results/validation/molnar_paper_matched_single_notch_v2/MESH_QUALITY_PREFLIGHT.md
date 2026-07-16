# Mesh Quality Preflight - Molnar Paper-Matched Single-Notch v2

Date: 2026-07-16

Classification: `mesh_quality_preflight_pass`

## Summary

- Physical elements checked: `33852`
- Maximum aspect ratio: `25.000000000001368`
- Maximum neighboring-size ratio: `1.5`
- Minimum signed area/Jacobian indicator: `9.999999999994822e-07`
- Elements bridging the open notch: `0`

## High Aspect-Ratio Groups

| Threshold | Count | Coordinate bounds | Min distance from notch tip | Inside refined strip | Intersects expected crack path | Min signed area | Max aspect | Max neighbor ratio |
|---:|---:|---|---:|---:|---:|---:|---:|---:|
| > 5.0 | 23428 | x=-0.5..0.5, y=-0.5..0.5 | 0.013125 | 0 | 0 | 5.062499999998991e-06 | 25.000000000001368 | 1.5 |
| > 10.0 | 21228 | x=-0.5..0.5, y=-0.5..0.5 | 0.02578125 | 0 | 0 | 1.1390624999996213e-05 | 25.000000000001368 | 1.5 |
| > 20.0 | 18972 | x=-0.5..0.5, y=-0.5..0.5 | 0.0542578125 | 0 | 0 | 2.3867187499999366e-05 | 25.000000000001368 | 1.5 |

## Maximum Aspect-Ratio Element

- Element ID: `9610`
- Aspect ratio: `25.000000000001368`
- Connectivity: `[9627, 9628, 10175, 10174]`
- Coordinate bounds: `x=0.281..0.282, y=-0.0792578132..-0.0542578132`
- Centroid: `(0.2815, -0.0667578132)`
- Minimum distance from notch tip: `0.28619033927308957`
- Inside refined fracture strip: `False`
- Intersects expected horizontal crack path: `False`
- Signed area/Jacobian indicator: `2.499999999999898e-05`

## Decision

- High-aspect-ratio elements are acceptable only as a documented reconstruction limitation when confined outside the notch-tip/fracture-process corridor.
- Preflight pass: `True`
