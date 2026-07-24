# P3-SM0 minimal-callback serial result

## Result

- Job: `1378099.mmaster02`
- Submitted revision: `572c51eacbf7af79f1ab2ffda93a0ad466fc6eca`
- Classification: `stage_p3sm0_minimal_callback_serial_pass`
- PBS exit: `0`
- Solver exit: `0`
- Completion marker: `P3SM0_COMPLETION.ok` present and validator-created
- Retry: none; authorization consumed `1/1`

## Technical and scientific gates

- Abaqus launched; Fortran compiled and linked; input processing and Abaqus/Standard completed.
- Scratch ODB was readable.
- All 8 CPS4 visualization elements and all 4 integration points per element were present (`32/32` state rows).
- SDV15 and SDV16 were finite.
- Phase-bound, phase-decrease, history-decrease, and transfer-table mismatch counts were all zero.
- RF--U and energy histories each contain 11 finite rows.
- The increment sequence contains 13 records.
- Signal 11 was not observed.

## Callback observations

| Marker | Count |
|---|---:|
| `P3SM0_UEXTERNALDB_LOP0` | 1 |
| `P3SM0_UEL_OBSERVED` | 3 |
| `P3SM0_UMAT_OBSERVED` | 2 |
| `P3SM0_UEXTERNALDB_END` | 1 |

The allowed conclusion is that the accepted eight-element serial model completes with a minimal `UEXTERNALDB` callback and bounded UEL/UMAT observation markers when no rank/thread or mutex utilities are called. This result does not establish GETRANK safety, GETTHREADID safety, COMMON/SAVE thread safety, four-thread repeatability, MPI support, or hybrid support.

## Scratch metadata

- ODB path: `/scratch/pr21vyci/adaptive-remeshing/runs/p3sm0_serial_1378099.mmaster02/p3sm0_serial.odb`
- Size: `673348` bytes
- SHA-256: `36dff4075f1b99916b5ddec319e402c9cb293a50fedf64eb1bfa33787d154771`
- Timestamp: `2026-07-24 15:23:40.464354617 +0200`

The ODB remains scratch-only and is not tracked.
