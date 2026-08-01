# Stage F14 adaptive-region result

Job `1381369.mmaster02` completed on `mnode106/1` with PBS exit zero, walltime
5 seconds, and peak recorded memory 210,536 kB. Official deck and ODB hashes
matched; the model contains 3,930 CPE4 elements, 3,930 finite MISESERI values,
and records the original 15 true-slit coincident pairs.

The CAE script created repository key `F12_MISESERI_RULE` with region `MODEL`,
step `Step-1`, Python 2 `str` variable `MISESERI`, UNIFORM_ERROR sizing,
target 1.0, sizes 0.001--0.010 mm, NOT_ALLOWED coarsening, and refinement
factor 10. Counts remain zero for solver, adaptivity-process, remesh, and
candidate execution; ALE adaptive meshing was not used.

The raw script self-classified the result as qualified. The declared terminal
gate, however, requires an identified nonempty adaptive-region repository and
object distinct from merely observing a RemeshingRule. The evidence records a
rule repository only and repeats the model-wide rule pattern that preceded the
F13 `no adaptive regions` exception. The installed meaning of that exception
therefore remains unresolved without making the prohibited remesh call.

Fail-closed classification: `native_adaptive_region_api_unresolved`. No future
native-remesh execution package is ready.
