# Molnar Targeted Output Rerun Requirements

Status: `conditional_future_requirement`

This is a minimal evidence specification for a future targeted-output rerun only if the supervisor decides that the missing SDV15 completed-phase-state evidence is essential for Gate A3. It does not authorize, prepare, or submit a PBS job. It does not modify candidate v2.

## Purpose

The current ODB and event tables prove the U1/U2/CPS4 label, connectivity, offset, and integration-point mapping. They do not retain enough within-increment update-stage information to compare equivalent completed U1 phase-field states for the `817` SDV15 above-precision non-staggered events.

## Minimum Additional Evidence

The minimum additional outputs would need to identify, for each monitored element/IP and update stage:

- exact phase-layer state after completed U1 phase updates;
- displacement-layer copied phase value used by U2;
- U1 history variable at the same integration point;
- update/call-stage indicator, including whether the value is first-call, current-call, copied, or retained from a previous call;
- increment, step time, frame/output identifier, and if possible iteration or call sequence number;
- physical element label, U1 label, U2 label, CPS4 visualization label, ODB IP, and source-storage IP;
- enough temporal density around peak and post-peak propagation to cover the late SDV15 decrease/overshoot region, especially approximately `U2 = 0.00633` to `0.00670 mm`.

## Standard Output Sufficiency

Standard frame output alone is unlikely to resolve the ambiguity. The retained ODB already contains frame-level `SDV14`, `SDV15`, and `SDV16`, but it does not reveal which U1 and U2 calls occurred immediately before the visualization copy or whether a value represents a completed phase update rather than an intermediate/copy state.

## Likely Instrumentation Requirement

If the supervisor requires closure of the 817 events, an additional diagnostic mechanism would likely be needed, such as:

- extra diagnostic SDVs that explicitly record `STEPITER`, source layer, and update-stage state;
- source-side logging for a narrowly selected element/IP set around the crack path and worst event;
- a controlled output request focused on late peak/post-peak propagation states;
- clear separation of U1 completed phase state, U2 copied phase state, and UMAT visualization copy state.

Any such rerun would be a new authorized scientific-evidence run, not a retry of the completed technical baseline. It should be scoped and approved separately before any PBS submission.

## Non-Requirements

- Do not rerun solely to reproduce the existing technical pass.
- Do not copy the ODB into Git.
- Do not start MISESERI, remeshing, state transfer, mesh studies, or parameter studies as part of this evidence request.
- Do not prepare a PBS script or submission command until explicitly authorized.
