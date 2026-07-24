# Stage D3D-A1H0 Datacheck R1 Authorization

Date: 2026-07-24  
Owner: thesis researcher

## Question

May one corrected D3D-A1H0 datacheck be submitted after job `1378003.mmaster02` stopped before Abaqus because a Windows working-tree checksum was compared with the synchronized Linux checkout?

## Evidence

- Job `1378003.mmaster02` is permanently preserved as `stage_d3d_a1h0_datacheck_fail`, PBS exit `7`.
- Abaqus compilation, input processing, datacheck, and solver analysis did not start.
- Runtime history passed the 25,600-record structural and checksum gates.
- The candidate and accepted-R4 Fortran files in the synchronized Linux checkout are byte-identical.
- The deck, Fortran content, runtime history, mesh, loading, phase field, tolerances, and scientific inputs are unchanged.
- The predecessor authorization remains consumed at `1/1`.

## Alternatives

1. Stop without a datacheck result.
2. Reset the consumed predecessor authorization.
3. Authorize one isolated R1 lane with checkout-local checksums.

## Decision

Alternative 3 is authorized with classification `stage_d3d_a1h0_datacheck_r1_authorized`. The R1 submitter must compare candidate and accepted-R4 sources in the synchronized Linux checkout, derive both Fortran and runtime-H SHA-256 values there, and pass them to the isolated PBS lane.

Exactly one R1 submission is authorized after committed preparation. It must use the guarded R1 wrapper and the distinct job name `d3d_a1h0_dc_r1`.

## Consequences

- The predecessor evidence and consumed authorization are immutable.
- The R1 evidence is written only to `d3d_a1_checkpoint_hold_datacheck_r1/`.
- A successful R1 datacheck is technical evidence only.
- Full hold, phase release, continuation, D3E, automatic retry, and tolerance changes remain unauthorized.
