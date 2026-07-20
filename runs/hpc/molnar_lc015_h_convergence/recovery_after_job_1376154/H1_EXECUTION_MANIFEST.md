# H1 Execution Manifest (First Execution)

Status: `prepared_not_submitted`

## Why this is not a scientific retry

Old job `1376155.mmaster02` was `not_executed_dependency_cancelled`. No H1
solver result exists. This submission is the first H1 execution.

## Scientific inputs

Unchanged from revision `58d7e3102d76fe0e70e6729457e2c7e90ad131bb`:

| File | SHA-256 |
|---|---|
| H1_h0025.inp | `90a305ef29714a6ee795e6b2fd9ef53856141f2ef66928665b5640422d12c35b` |
| H1_h0025.for | `745db8fcfb612895e0289f4533c90d204cc9b2ade3678a035614feeb308b5ead` |

## PBS policy

- Solver failure → nonzero PBS exit
- Solver success + CAE success → PBS exit 0
- Solver success + CAE failure → PBS exit 0 with separate CAE failure status
  (`solver_dependency_status=success`) so H2 may proceed

## Resources

1 CPU, 32 GB, 06:00:00
