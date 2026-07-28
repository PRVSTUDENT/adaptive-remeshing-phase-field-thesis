# Current project state

Updated: 2026-07-28
Protocol version: 1
Classification: `stage_f_mode_ii_h0_endpoint_corrected_serial_solver_contract_prepared_unauthorized`

## Git

| Item | Value |
|---|---|
| Solver contract preparation main revision | `f7e44ae55977fb0ee93d3950efd0ea5a8e0d49ea` |
| Solver authorization revision | `8cec3dbde56b08f8924d8298c05052da430dd4ba` |
| Datacheck closeout revision | `91d6fad0b972687380759c30a3a268515a733339` |
| Datacheck replacement submission tracking revision | `aaec1b8bb4d8e8c4232dbb99c204596c76450eec` |
| Datacheck replacement submission operational approval revision | `51b01ea6540663bab5a2b07b5f2b3e76cde3e23b` |
| Datacheck replacement authorization main revision | `38ab45b0afe2404ad72ccfde00039f3712001543` |
| Datacheck staging remediation main revision | `3c070ec40f5c609eb1ae91a6729ea2146680e3ed` |
| Datacheck staging remediation parent revision | `20cad4f94133635076da48eda821b50dd53a050a` |
| Active job ID | none |
| Datacheck authorization parent revision | `6a4fc72beb62a6bc247f200f9ee883ba3c5751af` |
| Corrected package preparation main revision | `e2e40b08fee23799da9518c118232af756610e0b` |
| Corrected package preparation parent revision | `71751047bbb05bdb1561e250c62a890989cdd349` |
| Endpoint audit revision | `49d7d4f1a941a09fbfd3aca147fd612a0a9a6a4c` |
| Endpoint audit parent revision | `b65839552727f3d1242bbde1e4d24f7fb7a8087b` |
| Active agent | none |
| Active task | **F1-C2-R1-SOLVER-PREP** complete (`stage_f_mode_ii_h0_endpoint_corrected_serial_solver_contract_prepared_unauthorized`) |

## Submission boundary (critical)

```text
Current task: F1-C2-R1-SOLVER-PREP complete
Status: stage_f_mode_ii_h0_endpoint_corrected_serial_solver_contract_prepared_unauthorized
active_job_id: none
datacheck_authorized: false (replacement datacheck passed; authorization consumed)
solver_authorized: false (contract repaired and qualified; reauthorization pending)
submission_approved: false
execution_authorized: false
maximum_jobs_now: 0
automatic_retry_authorized: false
```

Both initial solver run `1378919.mmaster02` (F1-J1) and replacement solver run `1378920.mmaster02` (F1-J1-R1) consumed their single authorized submissions and failed before Abaqus launch due to staging validation defects.
Task `F1-J1-R2` was executed on cluster under job ID `1378942.mmaster02`. The Abaqus FE solver completed cleanly (exit code 0) and standalone extraction completed cleanly (exit code 0), providing a partial pre-peak shear response up to $U_1 = 0.0070\text{ mm}$ ($RF_1 = 0.3063\text{ kN}$ maximum observed force at final point).
However, the run **failed the scientific acceptance gate** (`validator_return_code: 20`, `stage_f_mode_ii_h0_second_replacement_fail`) because the target displacement $U_1 = 0.0100\text{ mm}$ was not reached (Step-2 reached its 2000 increment limit) and the damage field reached $\max(d) = 0.29923 < 0.50$ (producing an empty crack path).
The R2 authorization record `runs/hpc/stage_f/mode_ii_h0/replacement_r2/MODE_II_H0_R2_AUTHORIZATION.json` is fully consumed (`solver_submissions_used: 1`). No further submissions or retries are permitted.
Downstream task F2 remains **blocked**.

## Stage F package (R2 replacement solver complete_failed, job 1378942.mmaster02)

- Package: `models/generated/mode_ii/h0_serial`
- Completed PBS Job ID: `1378942.mmaster02`
- Queue: `entry_imfdfkmq` (routed to `normal_imfdfkmq`)
- Staging Verifier Script: `scripts/validation/verify_mode_ii_h0_runtime_staging.py`
- Pre-Solver Smoke Script: `scripts/validation/run_pre_solver_smoke.py`
- Local Evidence Bundle: `runs/hpc/stage_f/mode_ii_h0/replacement_r2/evidence/1378942.mmaster02/`
- Local Smoke Bundle: `runs/hpc/stage_f/mode_ii_h0/replacement_r2/smoke_evidence_r3/local/EVIDENCE_BUNDLE_MANIFEST.json`
- Cluster Smoke Bundle: `runs/hpc/stage_f/mode_ii_h0/replacement_r2/smoke_evidence_r3/cluster_login/EVIDENCE_BUNDLE_MANIFEST.json`
- R2 Authorization Record: `runs/hpc/stage_f/mode_ii_h0/replacement_r2/MODE_II_H0_R2_AUTHORIZATION.json`
- Deck SHA-256: `32a25380767bbb0e9e76eb55b3bb7a97d78bb75c4f86c7e8585aa2032ce2d33b`
- Source SHA-256: `5decf4b1f587019d6bdd904e8ceed22175c113e070e714777cb998da428e4d8c`

## Next actions

1. Serial solver execution contract repaired and qualified (`PRESTAGED_ROOT`, `LOGIN_MANIFEST_PATH`, `PROJECT_REVISION`, `PRESTAGED_RUNTIME_ROOT`).
2. Static solver contract validator, 195 unit tests, and local solver staging smoke passed.
3. Await explicit human reauthorization under task `F1-C2-R1-SOLVER-REAUTH`.
4. Downstream tasks (F2+) remain blocked until corrected H0 baseline lane completes cleanly.

## Dirty paths

Pre-existing local porcelain remains preserved; not cleaned.
