# HPC Abaqus/Standard User-Subroutine Smoke Test

Date: 2026-07-15

Job ID: 1374532.mmaster02

Repository revision:

```text
b2db162ff7a4a8cf034c20884323f3f674999e61
```

Requested resources:

- Queue: testq
- Nodes: 1
- CPUs: 1
- Memory: 8 GB
- Wall time: 00:30:00

Observed execution:

- Compute host: mnode098.cluster
- PBS state: F
- PBS exit status: 1
- Scheduler metadata: `Resource_List.ngpus = 1` appeared again, but the script did not request or use a GPU.
- Work directory: `/scratch/pr21vyci/adaptive-remeshing/runs/abaqus_user_subroutine_smoke_1374532.mmaster02`
- Text stage directory: `/scratch/pr21vyci/adaptive-remeshing/stage/abaqus_user_subroutine_smoke_1374532.mmaster02`

Acceptance review:

- PBS job was scheduled and started: pass
- Abaqus/Standard license checkout: pass
- User-subroutine compilation: pass
- User-subroutine linking: pass
- Abaqus/Standard analysis completion: pass
- ODB creation: pass
- `THE ANALYSIS HAS COMPLETED SUCCESSFULLY` in `.sta`: pass
- `UEXTERNALDB` callback marker file: fail
- Final PBS-script success marker: fail
- PBS exit status was zero: fail

Classification:

```text
hpc_user_subroutine_smoke_fail
```

Failure category:

```text
callback_invocation
```

The job proves that the HPC Abaqus/Standard license checkout, user-subroutine compilation, linking, solver execution, and ODB creation can complete for the trivial model. It does not prove that the submitted `UEXTERNALDB` callback was invoked, because `uexternaldb_smoke.called` was not created anywhere under the scratch work tree before the PBS script reached its marker check.

This is a technical smoke-test failure only. It does not run or validate the Molnar UEL/UMAT, phase-field formulation, Gate A3 benchmark reproduction, MISESERI, remeshing, or state transfer.
