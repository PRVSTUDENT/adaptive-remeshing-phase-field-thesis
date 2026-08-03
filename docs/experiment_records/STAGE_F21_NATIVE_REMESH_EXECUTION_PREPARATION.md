# Stage F21 native-remesh execution preparation

F21 prepares exactly `M2RMEXEC1` from the qualified M2RMREG7 construction
contract. The selected installed route is `Model.adaptiveRemesh(odb)`, invoked
once with the qualified MISESERI rule, followed by at most one deterministic
`M2RMEXEC1_candidate.inp` export.

The package records source/candidate mesh hashes and counts, structural
entities, slit topology, and MISESERI refinement evidence. A successful API
return without mesh change is not accepted as a candidate. This preparation
runs no Abaqus or PBS command and does not prepare datacheck, state transfer,
refined analysis, rollback work, H1, or H2.
