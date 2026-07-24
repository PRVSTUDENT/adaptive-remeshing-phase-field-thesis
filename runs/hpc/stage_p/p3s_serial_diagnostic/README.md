# P3-S Serial Diagnostic Lane

Status: prepared and statically validated; submission unauthorized.

`P3S_AUTHORIZATION.json` is fail-closed. The submission wrapper must stop
unless a later reviewed commit changes `p3s_submission_authorized` to `true`
while retaining the one-submission limit and all downstream denials.

Configuration:

- one MPI rank, one thread and one CPU;
- Abaqus `mp_mode=threads`;
- eight physical elements;
- no automatic retry;
- scratch-only ODB; only its path and SHA-256 may be recorded;
- explicit lightweight evidence allowlist;
- no compute-node Git dependency.

Expected evidence after a separately authorized execution is listed in
`scripts/validation/validate_p3s_serial_diagnostic.py`. `P3S_COMPLETION.ok`
may exist only after every technical and scientific gate passes.

Required lightweight outputs are `P3S_STATUS.json`,
`P3S_ENVIRONMENT.txt`, `P3S_JOB_RECORD.txt`,
`P3S_CALLBACK_EVENTS.csv`, `P3S_SHARED_ACCESS_SUMMARY.json`,
`P3S_STATE_OUTPUT.csv`, `P3S_RF_U.csv`, `P3S_ENERGY.csv`,
`P3S_INCREMENT_SEQUENCE.json`, and, only for a full pass,
`P3S_COMPLETION.ok`.

P3-T4, MPI, hybrid, production H1, D3D-A1 reopening and D3E remain blocked.
