# H1 Execution Manifest (First Execution)

Status: `submitted`

## Why this is not a scientific retry

Old job `1376155.mmaster02` was `not_executed_dependency_cancelled`. No H1
solver result exists. This submission is the first H1 execution.

## Scientific inputs (unchanged from 58d7e31)

| File | SHA-256 |
|---|---|
| H1_h0025.inp | `90a305ef29714a6ee795e6b2fd9ef53856141f2ef66928665b5640422d12c35b` |
| H1_h0025.for | `745db8fcfb612895e0289f4533c90d204cc9b2ade3678a035614feeb308b5ead` |

## New job

| Field | Value |
|---|---|
| Job ID | `1376185.mmaster02` |
| Job name | `molnar_h1_h0025` |
| Initial state | R |
| Resources | 1 CPU, 32 GB, 06:00:00 |
| Dependency | none (solver-chain head) |
| Infrastructure revision | `26b7b70832b2e1ae74c54abb7599cbe553aa1bad` |
| Scientific-input revision | `58d7e3102d76fe0e70e6729457e2c7e90ad131bb` |
| Mail_Users | pr21vyci@mailserver.tu-freiberg.de |
| Mail_Points | abe |

PBS policy: solver success + CAE failure still yields PBS exit 0 with separate CAE status so H2 may proceed.
