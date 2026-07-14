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
- Fortran compiler and version: Intel `ifx` 2026.0.0 Build 20260331 works when Intel oneAPI environment is loaded; GNU Fortran 13.2.0 is also present but is not the Abaqus toolchain
- Linker/toolchain: Microsoft `LINK` 14.44.35226.0 works when Visual Studio 2022 Build Tools `vcvars64.bat` is loaded before Intel oneAPI
- Precision: pending baseline/source settings
- Solver procedure: pending benchmark deck
- License notes: Abaqus/Standard checked out 5 FlexNet tokens from `localhost` during the smoke test

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
- Compiler/linker warnings: the toolchain works only after loading Visual Studio Build Tools and Intel oneAPI in the shell; do not rely on a plain shell PATH
- Abaqus warnings: none from `abaqus information=release`
- Unsupported assumptions: successful smoke test does not prove official Abaqus 2024 / oneAPI 2026 support and does not validate the Molnar UEL/UMAT formulation

## User-Subroutine Smoke Test

- Fixture: `tests/abaqus_user_subroutine_smoke/`
- Evidence: `tests/abaqus_user_subroutine_smoke/evidence/`
- Command: `abaqus job=smoke_user_subroutine input=smoke_user_subroutine.inp user=smoke_uexternaldb.for cpus=1 interactive`
- Result: `passed_compile_link_solver_startup`
- Required shell setup: load `vcvars64.bat` from Visual Studio 2022 Build Tools, then load Intel oneAPI `setvars.bat intel64`.
- Observed tools: `ifx.exe`, `link.exe`, and `abaqus.bat` were all discoverable in the clean shell.
- Generated evidence: terminal output, `.com`, `.dat`, `.msg`, `.sta`, and `.env` are preserved under `tests/abaqus_user_subroutine_smoke/evidence/attempt_20260714_102744_clean_env_pass/`. No `.log` file was generated.

## Molnar One-Element Technical Run

- Run directory: `runs/molnar_one_element_unchanged/20260714_technical_gate_local/`
- Source/deck: copied unchanged from `models/baseline_original/molnar_gravouil_2017/01_One_Element/`
- Result: `technical_pass`
- Technical status: compile, link, input processing, Abaqus/Standard analysis, SIM wrap-up, and ODB readability passed.
- Evidence: `.com`, `.dat`, `.msg`, `.sta`, `.odb`, `.prt`, terminal output, command script, and ODB read check are preserved under the run `evidence/` folder. No `.log` file was generated.
- Warnings: Abaqus reported unsupported `*ELEMENT OUTPUT` for user elements in the `.dat` file; linker emitted `LNK4210` warnings. These do not block the technical gate but must be reviewed before scientific validation.

## Molnar One-Element Scientific Check

- Script: `scripts/validation/check_molnar_one_element.py`
- Evidence: `runs/molnar_one_element_unchanged/20260714_technical_gate_local/scientific_check/`
- Result: `scientific_pass` for the unchanged one-element ODB under provisional numerical tolerances.
- Passed checks: plane-strain stiffness, undamaged stress, degraded stress using `SDV14`, homogeneous phase relation using `SDV15` and `SDV16`, monotonic history, non-decreasing phase during unloading from `t=0.2` to `t=0.4`, and consistency across four integration points.
- Staggering note: `SDV14` and `SDV15` differ because the displacement and phase-field elements store/update phase values in a staggered sequence. The maximum observed absolute `SDV14 - SDV15` difference is recorded as evidence, not treated automatically as a failure.

## Completion Gate

This record must be complete before any production Abaqus/HPC submission. The next local baseline task is to run an unchanged Molnar notched benchmark and create a reproducible RF-U/phase-field/energy extraction path.
