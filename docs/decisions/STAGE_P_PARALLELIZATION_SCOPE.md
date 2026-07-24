# Stage P Parallelization Scope

Date: 2026-07-24
Decision: preparation only

Authorized and completed in this operation:

- P0 documentation/version review;
- P1 static source audit;
- P2 isolated minimal instrumented package preparation.

No Abaqus job or HPC submission was performed.

The preserved Molnar sources, scientific formulation, material parameters,
meshes, state-transfer evidence, and Stage D closure are unchanged. The P2
source is an experimental copy of the eight-physical-element D2 tiny model.
Its instrumentation does not establish correctness until the Abaqus 2022
interfaces compile and the bounded tests pass.

Blocked pending a committed review and new explicit execution authorization:

- P3-S and P3-T4 execution;
- P3-M2 and P3-H22;
- source refactoring (P5/P6);
- production H1 parallel execution;
- reopening D3D-A1 mechanical restart;
- D3E.

Update 2026-07-24: P0--P2 was selectively frozen and pushed as commit
`9369dfcb05d63cdbdec0b0e910423c9a6cc7bd1c`. A guarded P3-S lane has been
prepared but not submitted. Its wrapper requires a separate one-shot
authorization record and explicitly requires P3-T4 to remain unauthorized.

Any future P3 authorization is one submission per named configuration, with
no automatic retry. MPI and hybrid branches require separate authorization
and an explicit inter-process state design.
