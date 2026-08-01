# Stage F14 runtime and adaptive-region contract

F13 introduced two generic `GET_ENVIRONMENT_VARIABLE` calls absent from the
qualified F11 source. Intel emitted the unresolved `for_getenv_err` reference.
F14 removes that intrinsic and uses the documented Abaqus/Standard signatures
`CALL GETOUTDIR(OUTDIR,LENOUTDIR)` and
`CALL GETJOBNAME(JOBNAME,LENJOBNAME)`. Governing residual, tangent, penalty,
state, mapping, and energy code remain inherited from F11.

Official Abaqus adaptive remeshing assigns a `RemeshingRule` to native part
geometry faces/cells. It is not the ALE `*ADAPTIVE MESH` domain. The official
coarse input is imported as an orphan mesh, so F14 must determine whether the
installed API can expose a remeshable native region without changing source
geometry. No remesh call is permitted.
