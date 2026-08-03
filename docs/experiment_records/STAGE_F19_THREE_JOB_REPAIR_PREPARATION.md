# Stage F19 three-job repair preparation

Date: 2026-08-03

Prepared exactly `M2IRRROLLCTL5`, `M2IRRROLLFORCE5`, and `M2RMREG6`. The rollback packages preserve the F18 scientific deck, loading, mesh, material/fracture parameters, penalty formulation, state layout, increment controls, outputs, extractor, analyzer, trigger, and tolerances. Their source/deck/runtime scientific files are byte-identical; wrappers differ only in job identity and required force-mode value.

The adaptive package fixes the evidence lifecycle identified in the F18 source audit: the compatibility helper now writes its JSON, work and final evidence directories are distinct, partial evidence is staged after commands, and first command return codes have priority over missing-manifest failures.

Local WSL validation used gfortran to compile and link the standalone harness, exercised modes 0 and 1 plus persisted state 1, and compiled the actual UEL source to an object followed by relocatable link with an empty local Abaqus parameter stub. Intel Fortran and installed Abaqus headers were unavailable locally, so each future rollback wrapper recompiles and executes the harness after loading the cluster Intel module and before Abaqus/Standard.

No qsub, Abaqus/Standard, Abaqus/CAE, native remesh, datacheck, H1, H2, candidate, or refined analysis ran. Execution authorization and submission approval remain false. Clean-Linux qualification is required before any authorization request.
