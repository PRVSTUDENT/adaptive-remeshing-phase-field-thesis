# Stage F — Mode-II H0 lane

Classification: `stage_f_mode_ii_h0_prepared`

## Scope

Fail-closed HPC lane for the Mode-II pure-shear single-notch H0 technical package.

Package:

```text
models/generated/mode_ii/h0_serial/
```

## Authorization state

`MODE_II_H0_AUTHORIZATION.json` is prepared with:

- `datacheck_authorized: false`
- `solver_authorized: false`
- one maximum datacheck and one maximum solver submission
- no automatic retry, threads, or MPI

Preparation does **not** submit jobs.

## Immediate execution order

1. Offline package + static validator pass (F0)
2. Commit and synchronize the prepared lane
3. Cluster preflight (no authorization)
4. Separate F1-J0 datacheck authorization-only commit
5. Submit exactly one F1-J0 datacheck
6. Close F1-J0
7. Prepare F1-J1 only if F1-J0 passes

## Jobs

| Job | Name | Purpose | Status |
|---|---|---|---|
| F1-J0 | `mode_ii_h0_dc` | compile/link/datacheck only | not authorized |
| F1-J1 | `mode_ii_h0_serial` | serial baseline solve | blocked until F1-J0 pass |

Preliminary F1-J1 envelope (to confirm after F0 element count review): 16 GB, 04:00:00, 1 rank × 1 thread.
