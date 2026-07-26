# Stage F1-J0 Mode-II H0 Abaqus Datacheck Experiment Record

- **Task ID**: `F1-J0`
- **Stage**: Stage F (Mode-II mixed-mode benchmark)
- **Job ID**: `1378911.mmaster02`
- **Classification**: `stage_f_mode_ii_h0_datacheck_pass`
- **Authorization Revision**: `cddf916c8422f5f87152205f078e5e8f019e1afd`
- **Submission Revision**: `4ff884c23b3b7bcefbffd0605fd8d2bf5f1b400b`
- **Queue**: `entry_imfdfkmq` (routed to `normal_imfdfkmq`)
- **Compute Host**: `mnode098/0`
- **Execution Date**: 2026-07-26

## Resource Specification

- **CPUs**: 1
- **MPI Ranks**: 1
- **OMP Threads**: 1
- **Memory**: 16 GB
- **Walltime**: 00:30:00 (actual walltime: 00:00:13)
- **Notification Email**: `pr21vyci@mailserver.tu-freiberg.de` (`-m abe`)

## Validation Results

| Gate / Metric | Value | Result |
|---|---|---|
| Scheduler Exit Status | `0` | PASS |
| Abaqus Datacheck Return Code | `0` | PASS |
| `MODE_II_H0_DATACHECK.ok` Marker | Present | PASS |
| Deck SHA-256 | `32a25380767bbb0e9e76eb55b3bb7a97d78bb75c4f86c7e8585aa2032ce2d33b` | PASS |
| Source SHA-256 | `5decf4b1f587019d6bdd904e8ceed22175c113e070e714777cb998da428e4d8c` | PASS |
| Fortran Compilation & Linking | Successful | PASS |
| Input Processing | Successful | PASS |
| Jacobian & Geometry Checks | Zero negative/zero Jacobians | PASS |
| Solver Analysis Started | `false` | PASS |

## Retained Evidence Files

Local evidence path: `runs/hpc/stage_f/mode_ii_h0/evidence/1378911.mmaster02/`

- `MODE_II_H0_DATACHECK_STATUS.json`: Pass record
- `MODE_II_H0_DATACHECK.ok`: Completion marker
- `mode_ii_h0_dc.abaqus_stdout.log`: Standard output log
- `mode_ii_h0_dc.dat`: Data file
- `mode_ii_h0_dc.msg`: Message file
- `mode_ii_h0_dc.prt`: Part file
- `executables.txt` & `input_hash_check.txt`: Provenance verification

## Next Steps

- F1-J0 completed successfully.
- F1-J1-PREP (preparation of serial Mode-II H0 baseline) is now permitted. Full solver execution remains unauthorized until a separate explicit authorization commit and submission approval.
