# Stage D3D Active-Set Update Scope

**Classification:** `stage_d3d_active_set_update_scope_identified`

**Evidence job:** `1377558.mmaster02`

**Date:** 2026-07-24

## Question

Where does the accepted D3A5/R4 fixed active set first become invalid, and
what is the bounded offline candidate scope for a separately reviewed D3D-A1
preparation?

## Evidence and method

The analysis uses the committed D3D frame manifest, per-frame KKT results,
active-multiplier candidates, recovered nodal phase state, and integration-
point state. The declared active-multiplier threshold remains
\(-10^{-8}\); no tolerance was changed.

Candidate percentiles are conditional on nodes already below the threshold,
because the retained candidate table contains violating rows only. Connected
spatial groups are calculated on the unique violating-node union by joining
coincident nodes and orthogonal nearest neighbours on the structured
0.0125 mm Q4 grid.

## Onset and restart boundary

| Quantity | Result |
|---|---:|
| First invalid F4 frame | `F4_segment_initial` |
| First-invalid \(U_2\) | 0.003000000026077032 mm |
| Violating nodes at first invalid frame | 30 |
| Minimum multiplier at first invalid frame | \(-7.758084222140432\times10^{-8}\) |
| Last preceding accepted active-set-valid state | `F1_equilibrated` (accepted D3A5/R4 checkpoint) |
| Last accepted \(U_2\) | 0.003000000026077032 mm |

`F3_release_last` and the identical `F4_segment_initial` state both evaluate
below the threshold. Therefore, no positive Step-4 continuation increment is
active-set-valid. The update interval is the release-hold/segment boundary at
the unchanged checkpoint displacement, not an interval near the endpoint.
The D3D prefix comparison independently confirms exact reproduction of the
accepted R4 phase, SDV15, SDV16, reaction, displacement, and energy state.

## Candidate growth

| Frame | \(U_2\) (mm) | Violating nodes | Minimum multiplier |
|---|---:|---:|---:|
| F4 segment initial | 0.003000000026077032 | 30 | -7.758084222140432e-08 |
| increment 001 | 0.0030100000234693242 | 30 | -7.758115581282239e-08 |
| increment 002 | 0.0030200000208616200 | 63 | -8.692616583631587e-08 |
| increment 003 | 0.0030300000182539254 | 137 | -9.683045817170588e-08 |
| increment 004 | 0.0030400000156462206 | 522 | -1.072570343275791e-07 |
| increment 005 | 0.0030500000130385130 | 1,857 | -1.1786164173074067e-07 |
| increment 006 | 0.0030600000104308088 | 2,571 | -1.2860305333607142e-07 |
| increment 007 | 0.0030700000078231140 | 2,809 | -1.3943126995681987e-07 |
| increment 008 | 0.0030800000052154095 | 2,952 | -1.5351793354959651e-07 |
| increment 009 | 0.0030900000026077017 | 3,083 | -1.683533419667727e-07 |
| segment end | 0.0030999999999999973 | 3,157 | -1.8326844734391126e-07 |

The unique violating-node union contains 3,157 nodes. Its coordinate-neighbour
graph contains 41 groups; the largest contains 3,077 nodes and spans
\(x=-0.0625\) to \(0.5\) mm and \(y=-0.5\) to \(0.5\) mm. The endpoint union
is therefore broad and is a maximum possible release envelope, not the
minimum scientifically justified update.

The first-invalid-frame set contains only 30 nodes distributed across 12
union groups. Its violating-candidate multiplier median is
\(-1.29695420205634\times10^{-8}\); the 1st and 99th percentiles are
\(-7.75152629621322\times10^{-8}\) and
\(-1.01171221108688\times10^{-8}\), respectively. This separates a small
severe tail from many near-threshold candidates while still leaving the
threshold classification unambiguous.

## State coverage

Every F4 frame has complete recovered phase coverage at all 6,601 target
nodes and complete SDV15/SDV16 coverage at all 25,600 target integration
points. Phase decreases, history decreases, and lower-bound violations are
zero. The update-scope finding is therefore not caused by missing phase or
history evidence.

Node labels, coordinates, first-violation frames, per-frame multipliers, and
union group identifiers are retained in
`D3D_ACTIVE_SET_UPDATE_CANDIDATES_BY_FRAME.csv`. Full percentiles, spatial
groups, and coverage counts are retained in
`D3D_ACTIVE_SET_UPDATE_SCOPE.json`.

## Decision

The bounded update scope is identified. Do not define a new release set as
all 3,157 endpoint violators. A D3D-A1 preparation should begin from the
accepted D3A5/R4 checkpoint and review the 30 candidates already invalid at
the release-hold/segment boundary, including their spatial grouping and the
multiplier distribution.

This record authorizes offline review only. It does not authorize a new
Abaqus submission, D3E, a second segment, peak/post-peak continuation, or a
tolerance change.
