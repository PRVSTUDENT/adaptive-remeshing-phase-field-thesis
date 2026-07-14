# Molnar One-Element Scientific Check

Date: 2026-07-14

Classification: `scientific_pass`

## Scope

This is a quantitative check of the unchanged Molnar and Gravouil one-element run. It reads the technical-gate ODB and compares the UMAT visualization SDVs against relations implemented in the supplied source. It is not a remeshing or full benchmark validation.

ODB: `runs/molnar_one_element_unchanged/20260714_technical_gate_local/evidence/OneElement.odb`

Companion outputs:

- `one_element_sdv_scientific_check.csv`
- `one_element_scientific_check.json`

## Source-Defined Mapping

| ODB variable | Quantity |
|---|---|
| `SDV1`, `SDV2` | Local displacement components |
| `SDV3`-`SDV5` | Strain components `(epsilon11, epsilon22, gamma12)` |
| `SDV6`-`SDV8` | Degraded stresses |
| `SDV9`-`SDV11` | Undamaged elastic stresses |
| `SDV12` | Degraded elastic energy |
| `SDV13` | Undamaged elastic energy / current driving energy |
| `SDV14` | Phase field used by the displacement element |
| `SDV15` | Phase field from the phase-field element |
| `SDV16` | Maximum energy-history field |

## Checks

| Check | Result |
|---|---|
| `degraded_stress_matches_sdv14_degradation` | `True` |
| `initial_plane_strain_stiffness` | `True` |
| `integration_point_consistency_excluding_local_displacements` | `True` |
| `sdv15_matches_homogeneous_phase_relation` | `True` |
| `sdv15_non_decreasing_during_unloading_0p2_to_0p4` | `True` |
| `sdv16_monotonic` | `True` |
| `undamaged_stress_matches_plane_strain` | `True` |

## Undamaged Stress vs Plane-Strain Elasticity

| Quantity | Max abs error | Max rel error | Pass |
|---|---:|---:|---|
| `SDV10` | 1.898179e-06 | 9.339805e-08 | `True` |
| `SDV11` | 0.000000e+00 | 0.000000e+00 | `True` |
| `SDV9` | 9.049590e-07 | 9.129573e-08 | `True` |

## Degraded Stress vs `SDV14` Degradation

| Quantity | Max abs error | Max rel error | Pass |
|---|---:|---:|---|
| `SDV6` | 7.100549e-08 | 3.277641e-06 | `True` |
| `SDV7` | 1.597963e-07 | 3.277641e-06 | `True` |
| `SDV8` | 0.000000e+00 | 0.000000e+00 | `True` |

## Phase Field vs Homogeneous Relation

| Quantity | Max abs error | Max rel error | Pass |
|---|---:|---:|---|
| `SDV15` | 5.979519e-07 | 1.130898e-04 | `True` |

## Irreversibility

- `SDV16` monotonic: `True`; worst drop `0.000000e+00`
- `SDV15` non-decreasing during unloading from `t=0.2` to `t=0.4`: `True`; worst drop `0.000000e+00`

## Integration-Point Consistency

The consistency check excludes `SDV1` and `SDV2` because they are local displacement components and may differ by integration-point position. All strain, stress, energy, phase, and history SDVs are checked across the four integration points in each frame.

| Quantity | Max range across integration points |
|---|---:|
| `SDV10` | 0.000000e+00 |
| `SDV11` | 0.000000e+00 |
| `SDV12` | 0.000000e+00 |
| `SDV13` | 0.000000e+00 |
| `SDV14` | 0.000000e+00 |
| `SDV15` | 0.000000e+00 |
| `SDV16` | 0.000000e+00 |
| `SDV3` | 0.000000e+00 |
| `SDV4` | 0.000000e+00 |
| `SDV5` | 0.000000e+00 |
| `SDV6` | 0.000000e+00 |
| `SDV7` | 0.000000e+00 |
| `SDV8` | 0.000000e+00 |
| `SDV9` | 0.000000e+00 |

## `SDV14` / `SDV15` Staggering Note

`SDV14` is the phase field used by the displacement element when stress and degraded energy are computed. `SDV15` is the phase field stored by the phase-field element. Differences are therefore recorded as staggered-update evidence, not treated automatically as an error.

- Maximum absolute `SDV14 - SDV15`: `4.883736e-03`
- Location: frame `78`, time `0.078000`, integration point `1`
- Signed value at that location: `-4.883736e-03`

## Initial Stiffness Sample

Plane-strain constitutive matrix used by the source:

```text
 2.826923076923e+02   1.211538461538e+02   0.000000000000e+00
 1.211538461538e+02   2.826923076923e+02   0.000000000000e+00
 0.000000000000e+00   0.000000000000e+00   8.076923076923e+01
```

First nonzero-strain frame: `1` at time `0.001000`.

| Quantity | Value | Expected |
|---|---:|---:|
| `SDV9` | 1.211538445204e-02 | 1.211538430932e-02 |
| `SDV10` | 2.826923131943e-02 | 2.826923005509e-02 |
| `SDV11` | 0.000000000000e+00 | 0.000000000000e+00 |
