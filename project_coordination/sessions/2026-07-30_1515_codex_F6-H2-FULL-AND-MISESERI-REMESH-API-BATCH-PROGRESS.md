# Stage F6 guarded batch progress handoff

- Task: `F6-H2-FULL-AND-MISESERI-REMESH-API-BATCH`
- Starting main: `97b48adf1141a650c2b3995867277d310ebb2c3b`
- Preparation: `2249ec21fe92c6c7348d1cff653a84901828e117`
- Authorization: `5b5c2f4c596e419d4dcfca9cc1e80ba343f5cb82`
- Submission/consumption: `7a859ceeaa0e9e7477d3abcdfcdb7a0d358b0d9c`
- Run ID: `F6_20260730_122800_2249ec21`

The only guarded orchestrator invocation made exactly two qsub calls and both
succeeded. Direct manual qsub, retry, replacement, qdel and qmove counts are
zero. All authority is consumed.

Job A `1379966.mmaster02` (`M2H2U20F1`) was healthy and running on
`mnode105/0` at the last 15-minute observation: 44:30 walltime, 40:44 CPU,
1,376,604 kB memory. The `.sta` record was at Step 2 increment 413 of the
fixed 6,000-increment schedule. Leave it to terminate naturally.

Job B `1379967.mmaster02` (`M2RMAPI1`) is terminal with PBS exit 10 and
classification `abaqus_cae_start_failure`. Abaqus/CAE checked out a license
but Python 2.7 strict argument parsing rejected CAE driver arguments before
the in-script hash/API audit. Native remesh executions, solver executions and
candidate decks are all zero. Evidence is preserved under the canonical F6
evidence directory. M-104 records the cause and prevention-only correction.
No retry is authorized.

The combined scientific closeout remains pending Job A terminal completion.
