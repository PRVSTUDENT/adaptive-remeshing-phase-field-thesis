# Stage P3-T4 preparation release

P3-SM1TC qualified `get_thread_id()` under one thread, and P3-SM1R qualified
`CALL GETRANK(KPROCESSNUM)` under one MPI rank. This decision releases only
offline preparation of the bounded P3-T4 characterization:

`1 MPI rank x 4 OpenMP threads`, one node, four CPUs, 16 GB, 00:30:00,
Abaqus 2023, `mp_mode=threads`, queue `entry_imfdfkmq`.

The accepted P3-SM0 source remains the scientific reference. P3-T4 adds only
diagnostic instrumentation. Identifier calls use the qualified forms in UEL,
UMAT, or their diagnostic helpers; UEXTERNALDB contains no identifier call.
The diagnostic mutex protects counters and ownership metadata only. Scientific
USRVAR and TRANSFER_DONE accesses remain outside the mutex so the
characterization cannot hide concurrency.

Execution is not released. P3-T4 authorization is false at `0/1`; automatic
retry is false. MPI, hybrid, P4, production H1, D3D-A1 reopening, and D3E
remain unauthorized.

The frozen classifications are:

- `stage_p3t4_threaded_characterization_pass`
- `stage_p3t4_threaded_fail_pre_abaqus`
- `stage_p3t4_threaded_fail_compile`
- `stage_p3t4_threaded_fail_link`
- `stage_p3t4_threaded_fail_identifier`
- `stage_p3t4_threaded_fail_mutex`
- `stage_p3t4_threaded_fail_deadlock`
- `stage_p3t4_threaded_fail_callback`
- `stage_p3t4_threaded_fail_validation`
- `stage_p3t4_threading_not_exercised`
- `stage_p3t4_shared_state_conflict_observed`
- `stage_p3t4_scientific_mismatch`
