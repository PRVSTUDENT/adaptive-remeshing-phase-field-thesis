# Current project state

Updated: 2026-07-28
Protocol version: 1
Classification: `stage_f_mode_ii_h0_endpoint_corrected_serial_fail`

## Git

| Item | Value |
|---|---|
| Active job ID | `1379393.mmaster02` (closed) |
| Submitted project revision | `4d3de793e8ed37d650a0d83d9906afd0b313e661` |
| Solver contract preparation correction main revision | `0a7e72a25a06428dd97e9ad1f1d134bea4404289` |
| Solver contract preparation main revision | `f7e44ae6e7df7dcf1b7eb468eaa946b2eec9caae` |
| Solver authorization revision | `8cec3dbde56b08f8924d8298c05052da430dd4ba` |
| Datacheck closeout revision | `91d6fad0b972687380759c30a3a268515a733339` |
| Datacheck replacement submission tracking revision | `aaec1b8bb4d8e8c4232dbb99c204596c76450eec` |
| Datacheck replacement submission operational approval revision | `51b01ea6540663bab5a2b07b5f2b3e76cde3e23b` |
| Datacheck replacement authorization main revision | `38ab45b0afe2404ad72ccfde00039f3712001543` |
| Datacheck staging remediation main revision | `3c070ec40f5c609eb1ae91a6729ea2146680e3ed` |
| Datacheck staging remediation parent revision | `20cad4f94133635076da48eda821b50dd53a050a` |
| Datacheck authorization parent revision | `6a4fc72beb62a6bc247f200f9ee883ba3c5751af` |
| Corrected package preparation main revision | `e2e40b08fee23799da9518c118232af756610e0b` |
| Corrected package preparation parent revision | `71751047bbb05bdb1561e250c62a890989cdd349` |
| Endpoint audit revision | `49d7d4f1a941a09fbfd3aca147fd612a0a9a6a4c` |
| Endpoint audit parent revision | `b65839552727f3d1242bbde1e4d24f7fb7a8087b` |
| Active agent | none |
| Active task | **F1-C2-R1-SOLVER-CLOSE** completed (`stage_f_mode_ii_h0_endpoint_corrected_serial_fail`) |

## Submission boundary (critical)

```text
Current task: F1-C2-R1-SOLVER-CLOSE completed
Status: stage_f_mode_ii_h0_endpoint_corrected_serial_fail
active_job_id: 1379393.mmaster02 (closed)
datacheck_authorized: false (replacement datacheck passed; authorization consumed)
solver_authorized: false (solver job 1379393.mmaster02 completed; submission consumed 1/1)
submission_approved: true
execution_authorized: false
maximum_jobs_now: 0
automatic_retry_authorized: false
```

Corrected Mode-II H0 serial solver job `1379393.mmaster02` completed Abaqus solver execution (2000 increments, $U_1 = 0.0100\text{ mm}$, $F_{1,\max} = 0.3733\text{ kN}$, $\max(d) = 0.9909$). Wrapper validation returned exit status 12 due to validator script schema bugs. Single authorized solver submission is consumed (`solver_submissions_used: 1`).
No further submissions or retries are permitted.
Downstream task F2 remains **blocked**.

## Stage F corrected package (closed job 1379393.mmaster02)

- Package: `models/generated/mode_ii/h0_endpoint_corrected_serial`
- Closed PBS Job ID: `1379393.mmaster02`
- Queue: `entry_imfdfkmq` (routed to `normal_imfdfkmq`)
- Operational Authorization: `/scratch/pr21vyci/adaptive-remeshing/authorizations/F1-C2-R1-SOLVER_4d3de793e8ed37d650a0d83d9906afd0b313e661.json`
- Deck SHA-256: `c9160d50c944de7037a9f05dc1dbccfa9718f69b198bb48659f784bac220ddef`
- Source SHA-256: `5decf4b1f587019d6bdd904e8ceed22175c113e070e714777cb998da428e4d8c`

## Next actions

1. Wait for explicit human decision regarding validator schema fix vs solver results.


## Dirty paths

Pre-existing local porcelain remains preserved; not cleaned.
