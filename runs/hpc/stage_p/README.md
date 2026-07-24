# Stage P HPC Lane

Reserved for bounded parallelization qualification evidence.

P0--P2 preparation was committed and pushed as
`9369dfcb05d63cdbdec0b0e910423c9a6cc7bd1c`.

The P3-S serial lane is prepared under `scripts/hpc/stage_p/`. Its submission
wrapper refuses to call `qsub` while
`p3s_serial_diagnostic/P3S_AUTHORIZATION.json` retains
`p3s_submission_authorized: false`. Any later reviewed authorization must
retain the one-submission limit and all downstream denials.

No job has been submitted. P3-S execution, P3-T4, P3-M2 and P3-H22 remain
blocked pending review and explicit execution authorization.
