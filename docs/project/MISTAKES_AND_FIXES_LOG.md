# Mistakes And Fixes Log

This file is the consolidated ledger for execution mistakes, solver failures,
and the bounded fixes used to resolve or route around them. Failed attempts stay
recorded; a later fix does not erase the original evidence.

## Current Stage D3 Entries

| Date | Stage/job | Mistake or failure | Evidence | Fix or bounded next action | Status |
|---|---|---|---|---|---|
| 2026-07-23 | D3A3 `1377382.mmaster02` | The first full-target ingestion PBS loaded only `abaqus/2023`, so Abaqus user-subroutine compilation could not find `ifort`. | `runs/hpc/stage_d3/interrupted_transfer/target_ingestion/` | R1 restored the explicit module chain `gcc/11.4.0`, `intel/2024.2.0`, `abaqus/2023` before Abaqus. | Preserved as `stage_d3a3_solver_fail_compiler_environment`; no `D3A3.ok`. |
| 2026-07-23 | D3A3-R1 `1377383.mmaster02` | The compiler environment was fixed, but the generated `d3_transfer_table.inc` encoded 25600 H records as compile-time DATA statements and exceeded the Intel Fortran statement token limit before analysis. | `runs/hpc/stage_d3/interrupted_transfer/target_ingestion_r1/` | R2 removes the compile-time table and loads a headerless runtime `d3_transfer_h.dat` once through `UEXTERNALDB`. | Preserved as `stage_d3a3_solver_fail_transfer_table_compile`; no `D3A3_R1.ok` or `D3A3.ok`. |
| 2026-07-23 | D3A3-R2 local prep | The first R2 local draft still had the old generator call path and a header in `d3_transfer_h.dat`, which would have sent the job back through the R1 compile-time table or caused a runtime read failure. | Local R2 source review before submission. | The generator now calls `generate_fortran_r2`; `d3_transfer_h.dat` is headerless, sorted, and validated with 25600 records and SHA256 `4689ea5c10c0972e69ba46f8676a326c8b011b98faa8031c7c26cfb218607cd9`. | Local compile/datacheck package prepared; cluster datacheck not yet submitted. |

## Maintenance Rule

Update this file whenever a run fails, a mistaken assumption is discovered, or a
fix changes the execution route. Record the job id, evidence directory,
classification, and the exact solution used.
