# HPC Abaqus User-Subroutine Smoke Retry

Date: 2026-07-15

Job ID:

```text
1374533.mmaster02
```

Repository revision:

```text
c5db808b4c8d9e9bd01a9e5da0bd91b173787b8e
```

Purpose:

This deterministic retry verifies direct `UEXTERNALDB` callback invocation and
marker creation after the first trivial Abaqus/Standard user-subroutine smoke
job compiled, linked, and completed the analysis but did not retain callback
marker evidence.

Requested resources:

- Queue: testq
- Nodes: 1
- CPUs: 1
- Memory: 8 GB
- Wall time: 00:30:00

Observed execution:

- Compute host: mnode097.cluster
- PBS state: F
- PBS exit status: 0
- Abaqus return code: 0

Acceptance evidence:

- ODB existed in the scratch work directory and was not copied into this
  repository evidence directory.
- `.sta` contains `THE ANALYSIS HAS COMPLETED SUCCESSFULLY`.
- `.msg` contains `UEXTERNALDB_CALLBACK_ENTERED`.
- `.msg` contains `UEXTERNALDB_MARKER_WRITTEN`.
- `.msg` contains `UEXTERNALDB_ANALYSIS_END`.
- `uexternaldb_smoke.called` exists and contains `UEXTERNALDB_SMOKE_CALLED`.
- `acceptance_checks.txt` records all checks as `PASS`.
- `final_classification.txt` records `hpc_user_subroutine_smoke_pass`.

Classification:

```text
hpc_user_subroutine_smoke_pass
```

Boundary:

This closes only the trivial HPC technical toolchain gate: PBS execution,
Abaqus/Standard license checkout, Fortran compilation, user-subroutine linking,
`UEXTERNALDB` invocation, deterministic marker creation, trivial
Abaqus/Standard analysis completion, and ODB creation. It does not run or
validate the Molnar benchmark, Gate A3, MISESERI, remeshing, state transfer,
multi-CPU execution, production execution, or any parameter study.
