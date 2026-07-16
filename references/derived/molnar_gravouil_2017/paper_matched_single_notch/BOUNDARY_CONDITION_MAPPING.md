# Boundary Condition Mapping

Date: 2026-07-16

Candidate: `paper_matched_candidate_v2`

## Supplementary Pattern

The preserved `SingleNotch.inp` defines:

- `bottom`: lower boundary, fixed in vertical displacement;
- `top`: upper boundary, coupled to the reference point through an equation;
- `bottoml`: one lower-left node, constrained in horizontal displacement;
- `topl`: one upper-left node, constrained in horizontal displacement;
- `RP`: reaction-force and displacement extraction point.

The Step-1 supplementary boundary pattern is:

```text
RP, 2, 2, 1.
bottom, 2, 2
bottoml, 1, 1
topl, 1, 1
```

## Candidate-v2 Mapping

Candidate v2 retains the same source-faithful constraint roles:

| Set | Role | Constraint/output |
|---|---|---|
| `bottom` | lower edge support | `U2 = 0` |
| `top` | prescribed-displacement edge | equation-coupled to `RP` in `U2` |
| `bottoml` | horizontal rigid-body removal | `U1 = 0` |
| `topl` | source-faithful supplementary horizontal constraint | `U1 = 0` |
| `RP` | extraction point | `RF, U` |

The validator fails if the horizontal reference constraints are absent, if the full top or bottom edge is horizontally fixed, if the loading set is empty, or if the RF set is absent.

Status:

```text
source_faithful_boundary_mapping_restored
```
