# Environment Record

Status: partially completed from local Windows inspection on 2026-07-14. HPC details remain pending because the intended HPC runtime is under maintenance.

## Runtime Target

- Intended runtime: HPC after current maintenance clears.
- Local role: static validation, manifest checks, input-deck checks, dry-run preprocessing, Abaqus version checks, and small local smoke tests where licensing/toolchain permits.
- Production submissions: not allowed until this record is completed and reviewed.

## Machine and Operating System

- Date: 2026-07-14
- Operator: Codex / PRVSTUDENT local workspace
- Machine/cluster: local Windows machine `PRUTHVI`; HPC pending
- Operating system: Microsoft Windows 11 Home Single Language, version 10.0.26200, 64-bit
- Filesystem location: `D:\Master thesis\Adaptive remeshing`
- Scratch location: local scratch pending; HPC scratch pending
- Home/project quota: pending HPC maintenance clearance
- Logical processors: 12
- Physical memory: 25067094016 bytes, about 23.35 GiB

## Abaqus and Toolchain

- Abaqus release/hotfix: Abaqus 2024, sequence `2023_09_21-14.55.25 RELr426 190762`
- Abaqus command: `abaqus` and `abq2024` both resolve locally via `C:\SIMULIA\Commands`
- Abaqus Python version: 3.10.5, MSC v.1934 64 bit (AMD64)
- Abaqus installation path: `C:\SIMULIA\EstProducts\2024\win_b64`
- Fortran compiler and version: Intel Fortran not found on PATH; GNU Fortran 13.2.0 found at `C:\strawberry\c\bin\gfortran.exe`
- Linker/toolchain: Abaqus 2024 smoke-test environment uses Intel `ifx` for Fortran compilation and Microsoft `LINK` for linking, but `ifx` is not currently discoverable on PATH
- Precision: pending baseline/source settings
- Solver procedure: pending benchmark deck
- License notes: Abaqus/Standard checked out 5 FlexNet tokens from `localhost` during the smoke test, then failed before solver execution

## Compute Layout

- CPUs: local 12 logical processors; HPC pending
- MPI ranks: pending
- Threads: pending
- Memory: local about 23.35 GiB physical memory; HPC request pending
- Walltime: pending
- Queue/partition: pending HPC maintenance clearance
- Module load commands: pending HPC maintenance clearance

## Source Provenance

- Molnar original source location: `models/baseline_original/molnar_gravouil_2017/`
- Molnar source checksum: see `models/baseline_original/molnar_gravouil_2017/README.md`
- Baseline input deck location: `models/baseline_original/molnar_gravouil_2017/01_One_Element/OneElement.inp`
- Baseline input deck checksum: `9b63615bbe335872de197b96ca0253769f4a237c1e2e384294a1d204c462f220`
- UMAT/visualization bridge checksum: pending
- ABAQUSER source checksum: pending
- GitHub repository: public `https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis`
- Current branch: `main`

## Known Warnings

- HPC maintenance status: user reported maintenance currently blocks intended HPC run path
- Compiler/linker warnings: WP0 smoke test failed at compiler discovery/compilation because Abaqus called `ifx` and Windows reported `'ifx' is not recognized as an internal or external command`
- Abaqus warnings: none from `abaqus information=release`
- Unsupported assumptions: local Abaqus version query and license checkout are not successful UEL/UMAT compile, link, or solver validation

## User-Subroutine Smoke Test

- Fixture: `tests/abaqus_user_subroutine_smoke/`
- Evidence: `tests/abaqus_user_subroutine_smoke/evidence/`
- Command: `abaqus job=smoke_user_subroutine input=smoke_user_subroutine.inp user=smoke_uexternaldb.for cpus=1 interactive`
- Result: `compiler_discovery_fail`
- Failure point: Abaqus/Standard license checkout succeeded; compilation began; `ifx` was not found on PATH.
- Generated evidence: terminal output, `.com`, and `.env` were preserved. `.log`, `.dat`, `.msg`, and `.sta` were not generated because compilation failed before solver execution.

## Completion Gate

This record must be complete before any production Abaqus/HPC submission. The next environment task is to make the Abaqus-supported Intel Fortran `ifx` toolchain discoverable, then rerun the smoke test until compile, link, and solver startup pass.
