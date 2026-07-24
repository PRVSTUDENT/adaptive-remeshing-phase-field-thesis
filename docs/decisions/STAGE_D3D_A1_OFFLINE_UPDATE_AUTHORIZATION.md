# Stage D3D-A1 Offline Update Authorization

**Classification:** `stage_d3d_a1_offline_update_preparation_authorized`

**Date:** 2026-07-24

## Question

May the invalid D3D release-hold checkpoint be corrected by one deterministic
offline phase-field obstacle solve before any further Abaqus work?

## Decision

One offline checkpoint update is authorized at
\(U_2=0.003000000026077032\) mm. The source is job
`1377558.mmaster02`, frame `F3_release_last`.

The F3 recovered phase is the irreversibility lower bound. Actual F3 SDV16 is
the fixed history field. The prior 155 free nodes plus the 30 first-invalid
active nodes form only the initial free set; the converged KKT solution decides
the final membership.

## Boundaries

- Abaqus deck preparation: not authorized.
- PBS preparation or submission: not authorized.
- D3E and further continuation: blocked.
- Releasing the 3,157-node endpoint union: prohibited.
- Automatic retry or tolerance adjustment: prohibited.
- A passing offline package remains a candidate until a separately authorized
  mechanical checkpoint-hold run re-equilibrates and validates it.
