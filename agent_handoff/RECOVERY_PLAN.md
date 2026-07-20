# Recovery Plan After Job 1376154

## Prior chain (authorization fully consumed)

| Case | Job ID | Classification |
|---|---|---|
| H0 | `1376154.mmaster02` | `solver_pass_cae_postprocess_failure` |
| H1 | `1376155.mmaster02` | `not_executed_dependency_cancelled` |
| H2-PUB | `1376156.mmaster02` | `not_executed_dependency_cancelled` |

H0 PBS `Exit_status=11` because CAE postprocessing failed after Abaqus technical
pass. H1 and H2 were cancelled by `afterok` and never executed.

Preserved without overwrite:

- H0 evidence under `H0_exact/evidence/1376154.mmaster02/`
- retained ODB:
  `/scratch/pr21vyci/adaptive-remeshing/runs/molnar_lc015_h0_exact_1376154.mmaster02/molnar_lc015_h0_exact.odb`
- immutable prestage revision `58d7e3102d76fe0e70e6729457e2c7e90ad131bb`
- cancelled H1/H2 PBS history records

## Authorized recovery actions (exactly three)

1. **H0 CAE-only replay** using the existing successful ODB — no Standard rerun.
2. **H1 first solver execution** (not a scientific retry; H1 never ran).
3. **H2-PUB first solver execution** dependent on H1 **solver dependency success**.

Not authorized:

- H0 solver rerun;
- fourth mesh;
- automatic retry;
- duplicate submission beyond these three.

## Infrastructure corrections

- CAE scripts made Abaqus-Python compatible (no f-strings / Py3-only APIs).
- H1/H2 PBS: solver success + CAE failure → PBS exit 0 with
  `solver_dependency_status=success` and separate CAE failure files.
- H0 CAE replay is independent (no dependency link into H1).

## Scientific inputs

H1/H2 decks and Fortran sources remain those prepared at scientific-input
revision `58d7e3102d76fe0e70e6729457e2c7e90ad131bb`. Hash identity is verified
before submission.
