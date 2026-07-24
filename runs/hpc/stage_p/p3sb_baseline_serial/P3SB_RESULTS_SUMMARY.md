# P3-SB serial baseline result

Job `1378094.mmaster02` is closed as `stage_p3sb_baseline_serial_fail_validation`. The one-shot authorization is consumed (`1/1`) and no retry is authorized.

## What completed

- Abaqus 2023 launched.
- The accepted uninstrumented D2 Fortran compiled and linked.
- Input processing completed.
- Abaqus/Standard completed successfully with solver exit `0`.
- The scratch ODB was readable.
- Extraction produced 32 state rows: eight CPS4 visualization elements times four integration points.
- Eleven RF-U rows and eleven energy rows are finite.
- Phase-bound, phase-decrease, history-decrease, and transfer-table mismatch counts are all zero.
- The finalized `.sta` contains 13 increment/attempt records.

## Why the lane failed validation

The validator ran before the exit finalizer copied `p3sb_baseline.abaqus_stdout.log` and `p3sb_baseline.sta` from scratch into the evidence directory. It therefore recorded those two files as missing, set the compile/link/input/completion gates false, and generated an empty increment sequence. The finalizer copied the files only after the validator exited with status `12`.

The committed status is not rewritten and `P3SB_COMPLETION.ok` remains absent. Thus the lane is a technical validation-order failure even though the solver and extracted state evidence completed.

## Decision boundary

This result is not promoted to `stage_p3sb_baseline_serial_pass`. It does not authorize P3-SM execution, P3-T4, MPI, hybrid, P4, production H1, D3D-A1 reopening, or D3E. No retry is authorized or submitted.

Scratch ODB metadata:

```text
path=/scratch/pr21vyci/adaptive-remeshing/runs/p3sb_baseline_1378094.mmaster02/p3sb_baseline.odb
size=673348
sha256=56ac633c178ff4e8207e879f3fc2c090834ca53b287aeae21f7c025bbf8677ef
mtime=2026-07-24T14:26:14.955947133+02:00
```
