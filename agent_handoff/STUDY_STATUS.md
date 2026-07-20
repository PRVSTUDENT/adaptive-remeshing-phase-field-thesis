# Study Status

Status: `recovery_authorized_prepared_or_submitting`

Scientific convergence: pending.

## First chain (completed outcome)

| Case | Job ID | Classification |
|---|---|---|
| H0 | `1376154.mmaster02` | `solver_pass_cae_postprocess_failure` |
| H1 | `1376155.mmaster02` | `not_executed_dependency_cancelled` |
| H2-PUB | `1376156.mmaster02` | `not_executed_dependency_cancelled` |

Scientific-input revision: `58d7e3102d76fe0e70e6729457e2c7e90ad131bb`

## Recovery (authorized)

| Action | Nature |
|---|---|
| H0 CAE replay | postprocess-only on existing ODB; no solver rerun |
| H1 | first solver execution |
| H2-PUB | first solver execution; afterok H1 only |

See `recovery_after_job_1376154/`.

Mail_Users: `pr21vyci@mailserver.tu-freiberg.de`  
Mail_Points: `abe`

No H0 solver rerun, fourth mesh, or automatic extra retry beyond the authorized recovery trio.
