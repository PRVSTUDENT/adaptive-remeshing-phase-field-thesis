# F13 queued-execution session report

- Starting SHA: `d250bab9e2a91cf7436f9aa12e3e91480376a113`
- Final preparation SHA: `51b31f9cecf339e15e5129681036d16d82408819`
- Authorization SHA: `5e380f5e936c95556fdf51a307e17e78827d6cea`
- Submission SHA: `bac92f562e48372701fe0a66f6cedcfedbd4f98c`
- Run ID: `F13_20260731_105412_51b31f9`
- Submitted jobs: `1380981.mmaster02`, `1380982.mmaster02`, `1380983.mmaster02`
- qsub attempts/successes/failures: `3/3/0`
- retries/replacements/direct qsub/qdel/qmove: `0/0/0/0/0`

The first permitted scheduler poll after 15 minutes found all three jobs queued and none running. PBS estimated a start on 2026-08-01 and reported placement/Qlist waiting. No scheduler mutation is authorized.

Preparation resolved three fail-closed runtime/API preflights without qsub use: CRLF checksum routing, the installed `maxIterations` signature, and the `ModelJob` type contract. Abaqus additionally requires at least two adaptivity-process iterations, so Job C uses the documented direct `Model.adaptiveRemesh(odb)` API with the official verified ODB. Its frozen contract is 0 source solves, 0 adaptivity-process submissions, at most 1 remesh call, and 0 refined solves.

The session is released for a later monitoring-only claim. Scientific rollback, H1-readiness, and candidate-datacheck decisions remain pending and must not be inferred from queued state.
