# Study Status

Status: `solvers_active_or_pending_consolidated_cae_prepared`

Scientific convergence: pending.

## First chain (historical)

| Case | Job ID | Classification |
|---|---|---|
| H0 | `1376154.mmaster02` | `solver_pass_cae_postprocess_failure` |
| H1 | `1376155.mmaster02` | `not_executed_dependency_cancelled` |
| H2-PUB | `1376156.mmaster02` | `not_executed_dependency_cancelled` |

Scientific-input revision: `58d7e3102d76fe0e70e6729457e2c7e90ad131bb`

## Recovery submissions (authorized trio)

| Action | Job ID | Initial state | Dependency |
|---|---|---|---|
| H0 CAE replay | `1376184.mmaster02` | Q | none |
| H1 first solve | `1376185.mmaster02` | R | none (head) |
| H2-PUB first solve | `1376186.mmaster02` | H | afterok:H1 |

Infrastructure revision: `26b7b70832b2e1ae74c54abb7599cbe553aa1bad`  
Prestage: `/scratch/pr21vyci/adaptive-remeshing/prestage/molnar_lc015_hconv_recovery_20260720T141120+0200_26b7b70832b2`

Mail_Users: `pr21vyci@mailserver.tu-freiberg.de`  
Mail_Points: `abe`

Authorization for the recovery trio is fully consumed.

Additional authorization (not yet submitted):

- Exactly **one** consolidated CAE-only PBS job after H1/H2 leave the active queue.
- No H0-only CAE resubmit now; no solver retries; no extra meshes.

Prepared: env-var CAE I/O + `molnar_lc015_hconv_cae_replay_all.pbs` + eligibility builder.
See `recovery_after_job_1376154/CONSOLIDATED_CAE_REPLAY_PLAN.md`.
