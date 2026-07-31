# Stage F11 session report

Date: 2026-07-31
Agent: codex
Starting commit: `306cf41668cc37bb5485b2b84b625d892ac55196`
Preparation commit: `fec1165394afb1f0876ae51c8b6ee9125883de1f`
Authorization commit: `4d4e1c812e7caa185883f17ec66be8357bca33a7`
Submission commit: `4b15c2ab91d977ab71eddc63f7b7bcfe7228a96d`

## Execution

The guarded orchestrator made exactly three qsub attempts and obtained jobs
`1380100.mmaster02`, `1380101.mmaster02`, and `1380102.mmaster02`. The
mandatory quiet interval was honored. There were no retries, replacements,
direct qsubs, qdel, or qmove calls.

## Results

The instrumented baseline completed. The penalty candidate qualified on the
minimal model under the declared phase, response, convergence, activation,
and diagnostic-energy policies. Its minimum SDV15 change was
`-5.960464477539063e-08`; its maximum positive incremental imbalance was
`1.1510352576364673e-07`, below the `1.082631349474386e-06` limit. Stored
prior phase matched the preceding converged frame in all 9,200 applicable
checks. No cutback occurred, so rollback was not exercised.

The CAE-only matrix qualified `RemeshingRule.variables=('MISESERI',)` with a
Python 2 byte-string tuple element. It executed no solver, adaptive analysis,
remesh operation, or candidate deck.

## Validation and scope

All 25 targeted F8--F11 tests passed. The full suite produced 276 passes and
44 unrelated pre-existing workstation failures. Both Fortran sources
compiled and linked with the Abaqus 2023 cluster toolchain. Evidence hashes,
runtime manifests, ODB identity, syntax checks, and source allowlists passed.

Only preparation of a future medium-H1 package is eligible. No submission,
H2, refined, adaptive, or production execution is authorized.

Incident M-115 records a remote checksum quoting error; the stray checksum
file was removed and explicit runtime paths regenerated valid manifests.
There was no scheduler or scientific impact.
