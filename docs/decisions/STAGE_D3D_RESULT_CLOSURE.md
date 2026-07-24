# Stage D3D Result Closure

**Classification:** `stage_d3d_active_set_update_required`

**Job:** `1377558.mmaster02`

**Source commit:** `2fd409bfcd555d54af333f1c8dac863b67b83360`

**Date:** 2026-07-24

## Question

Does the accepted 6,446-node D3A5/R4 active set remain valid while the
transferred solution is continued from
\(U_2=0.003000000026077032\) to \(0.0031\) mm?

## Evidence

- Abaqus and postprocessing completed without technical failures.
- PBS exit status `23` is the workflow's scientific
  `stage_d3d_active_set_update_required` exit.
- Eleven Step-4 frames were written: the initial frame plus ten accepted
  solver increments.
- The largest free-node residual was
  \(3.60713084251115\times10^{-12}\), below \(10^{-8}\).
- The minimum active multiplier was
  \(-1.8326844734391126\times10^{-7}\), below the declared
  \(-10^{-8}\) threshold.
- Phase decreases, history-field decreases, and lower-bound violations were
  all zero.
- The endpoint top displacement was
  \(U_2=0.0030999999999999973\) mm.
- The scratch ODB identity is recorded by SHA-256 and filesystem metadata,
  but no ODB was copied into the repository.

## Decision

The D3D solver execution is technically complete, but the bounded segment
does not pass the fixed-active-set scientific gate. The result is accepted as
a scientific outcome:

> The original active set remains irreversible and numerically equilibrated,
> but it cannot remain fixed over the complete requested continuation
> segment. A reviewed active-set update is required before further loading.

The \(U_2=0.0031\) endpoint is not an accepted restart state. D3E, a second
segment, and peak/post-peak continuation remain blocked.

## Consequences

- The exactly-once full-segment authorization is consumed.
- Automatic retry is not authorized.
- D3E is not authorized.
- No tolerance change is authorized.
- Offline identification of the first invalid frame and bounded candidate
  scope is authorized and recorded separately in
  `STAGE_D3D_ACTIVE_SET_UPDATE_SCOPE.md`.
