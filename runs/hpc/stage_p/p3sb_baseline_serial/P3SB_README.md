# P3-SB guarded serial baseline lane

Preparation only. Submission authorization is false.

Question: does the eight-element P3-S deck complete serially with the accepted uninstrumented D2-derived source?

Frozen execution configuration: Abaqus 2023, Intel 2024.2, queue `entry_imfdfkmq`, one CPU, one MPI rank, one OpenMP thread, `mp_mode=threads`, 16 GB, and 00:30:00.

Only `submit_p3sb_baseline_serial.sh` may perform a future submission after a separately reviewed authorization commit. A valid PBS job ID atomically consumes the single authorization. Failed submission does not consume it. No automatic retry or downstream execution is authorized.
