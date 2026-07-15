# Environment Record

Status: local Windows inspection completed on 2026-07-14; no-submit HPC access/module/PBS inspection completed on 2026-07-15; final serial `testq` environment smoke passed on 2026-07-15. A minimal Abaqus/Standard trivial `UEXTERNALDB` compile/link/license smoke test is prepared but not submitted. HPC Abaqus user-subroutine compile/link and licensing remain untested.

## Runtime Target

- Intended runtime: HPC after the serial environment smoke pass and the next user-subroutine compile/link/license smoke gate.
- Local role: static validation, manifest checks, input-deck checks, dry-run preprocessing, Abaqus version checks, and small local smoke tests where licensing/toolchain permits.
- Production submissions: not allowed until the environment smoke gate, user-subroutine compile/link smoke gate, and scientific baseline gates are completed and reviewed.

## Machine and Operating System

- Date: 2026-07-14 local inspection; 2026-07-15 HPC no-submit probe
- Operator: Codex / PRVSTUDENT local workspace
- Machine/cluster: local Windows machine `PRUTHVI`; TU Freiberg login node `mlogin01.cluster`
- Operating system: Microsoft Windows 11 Home Single Language, version 10.0.26200, 64-bit
- Filesystem location: `D:\Master thesis\Adaptive remeshing`
- Scratch location: `/scratch/pr21vyci/adaptive-remeshing/`
- Home/project location: `/home/pr21vyci/projects/adaptive-remeshing`
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

## HPC Access and No-Submit Environment Probe

- SSH profile: `$env:USERPROFILE\.ssh\codex_config`
- SSH alias: `tu_freiberg`
- HPC user: `pr21vyci`
- Verified login command: `ssh -F $env:USERPROFILE\.ssh\codex_config tu_freiberg "hostname; whoami; pwd; id; groups"`
- Verified login result: `mlogin01.cluster`, `pr21vyci`, `/home/pr21vyci`
- Relevant groups include `t2-dl-rights-hpc_user`, `t2-dl-rights-hpc_teaching`, `t2-dl-rights-hpc_hw_kieferams`, and `t2-dl-rights-hpc_gaussian`.
- Home/project directory: `/home/pr21vyci/projects/adaptive-remeshing`
- Scratch directories created: `/scratch/pr21vyci/adaptive-remeshing/runs`, `/scratch/pr21vyci/adaptive-remeshing/tmp`, and `/scratch/pr21vyci/adaptive-remeshing/stage`
- HPC Git clone: `https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis.git`
- HPC clone revision verified on 2026-07-15: `eb04bf6fb7beb42eb0098cf2d1cdbd4ab89c7839`
- Local committed revision at the time of cloning: `eb04bf6`
- Local uncommitted documentation was not pushed to HPC during this probe.
- No-submit environment probe evidence: `docs/methods/hpc_environment_probe_20260715.txt`
- Loaded modules in the probe: `intel/2024.2.0` and `abaqus/2023`
- HPC Abaqus command: `/cluster/application/abaqus/2023/Commands/abaqus`
- HPC compiler command: `/cluster/stages/2024.0/software/intel/2024.2/compiler/2024.2/bin/ifx`
- HPC Abaqus result: `abaqus information=release` reported `Abaqus 2023` and completed.
- HPC compiler result: `ifx (IFX) 2024.2.0 20240602`.
- PBS queue inspection completed without submission. `testq` was enabled with `resources_max.walltime = 04:00:00`; `entry_imfdfkmq` routed to `normal_imfdfkmq` and `short_imfdfkmq`.
- Prepared-but-not-submitted PBS script: `scripts/hpc/abaqus_environment_smoke.pbs`
- First submission evidence: `runs/hpc/20260715_abaqus_environment_smoke/`
- First submitted job: `1374529.mmaster02`
- First submitted job classification: `hpc_environment_smoke_fail`
- First submitted job result: PBS scheduled the job on `mnode098.cluster`, loaded `intel/2024.2.0` and `abaqus/2023`, found valid `abaqus` and `ifx` executables, and completed `abaqus information=release`, but `ifx --version` failed with Intel error `#10417` before the repository-revision echo and final success marker.
- Repaired rerun evidence: `runs/hpc/20260715_abaqus_environment_smoke_rerun_gcc/`
- Repaired rerun job: `1374530.mmaster02`
- Repaired rerun classification: `hpc_environment_smoke_fail`
- Repaired rerun result: PBS scheduled the job on `mnode098.cluster`, loaded the repaired module sequence far enough to reach the metadata block, but exited with status `127` when `git -C "${PROJECT_HOME}" rev-parse HEAD` failed because `git` was not available in the compute-node batch PATH. The rerun therefore did not reach the compiler-version, Abaqus-release, or final success-marker diagnostics, and it does not establish whether the GCC-plus-Intel repair fixed compute-node `ifx` initialization.
- Final rerun evidence: `runs/hpc/20260715_abaqus_environment_smoke_rerun_revision_env/`
- Final rerun job: `1374531.mmaster02`
- Final rerun classification: `hpc_environment_smoke_pass`
- Final rerun result: PBS scheduled the job on `mnode098.cluster`; `PROJECT_REVISION` captured `d2e9e3c0d1e86e5f12772cb3d7e191a5377ea54f`; modules `gcc/11.4.0`, `intel/2024.2.0`, and `abaqus/2023` loaded; `gcc`, `gfortran`, `ifx`, and `abaqus` resolved to valid paths; `gcc --version`, `gfortran --version`, `ifx --version`, and `abaqus information=release` completed; the script reached `Environment smoke probe completed.`; PBS `Exit_status = 0`.
- Submission status after environment smoke pass: no benchmark, user-subroutine compile/link job, MISESERI, or remeshing job has been submitted.

## Prepared HPC User-Subroutine Smoke Test

- Test directory: `tests/hpc/abaqus_standard_user_subroutine_smoke/`
- PBS script: `scripts/hpc/abaqus_user_subroutine_smoke.pbs`
- Scope: trivial Abaqus/Standard CPS4 elastic model plus `UEXTERNALDB` marker-file callback only.
- Purpose: verify Abaqus/Standard license checkout, Intel Fortran compilation, linker execution, user-subroutine invocation, successful solver completion, and ODB creation.
- Scientific boundary: this does not test the Molnar UEL/UMAT, phase-field behavior, state variables, irreversibility, Gate A3, MISESERI, remeshing, or state transfer.
- Submission status: prepared and syntax-checkable only; no `qsub` has been approved or run for this test.

## Compute Layout

- CPUs: local 12 logical processors; initial HPC smoke candidate requests 1 CPU
- MPI ranks: none for the initial serial smoke candidate
- Threads: 1 for the initial serial smoke candidate
- Memory: local about 23.35 GiB physical memory; HPC request pending
- Walltime: initial HPC smoke candidate requests `00:30:00`
- Queue/partition: initial smoke candidate uses `testq`; production route remains unresolved
- Module load commands: `module purge`, `module load intel/2024.2.0`, `module load abaqus/2023`

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

- HPC maintenance status: user reported SSH restored; no-submit access and module checks succeeded on 2026-07-15.
- HPC compiler warning: the first compute-node smoke failed because `ifx --version` could not set up its required GCC install-path setting. A no-submit login-node diagnostic showed `module load gcc/11.4.0` before `module load intel/2024.2.0` gives a Spack GCC 11.4.0 path and `ifx --version` succeeds on the login node.
- HPC metadata warning: the repaired compute-node rerun failed before compiler diagnostics because `git` was unavailable in the batch job environment. The hardened smoke script no longer runs `git` on the compute node; the final passing rerun captured the repository revision on the login node with `git rev-parse HEAD` and passed it into PBS with `qsub -v PROJECT_REVISION="${REVISION}"`.
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

## Molnar Single-Notch Technical Run

- Run directory: `runs/molnar_single_notch_unchanged/20260714_technical_gate_local/`
- Source/deck: copied unchanged from `models/baseline_original/molnar_gravouil_2017/02_Single_Notch_Tension/`
- Result: `technical_pass_scientific_unchecked`
- Technical status: compile, link, input processing, Abaqus/Standard analysis, SIM wrap-up, `.sta` success, and ODB readability passed.
- Evidence: command script, terminal output, `.com`, `.dat`, `.msg`, `.prt`, `.sta`, and output checksums are preserved under the run `evidence/` folder. The 88 MB ODB is kept locally in the run `work/` folder and is not mirrored into handoff/Git.
- Extraction: `scripts/postprocessing/extract_molnar_single_notch.py` writes RF-U/phase summaries and matched-state `SDV14`/`SDV15`/`SDV16` contour CSVs under the run `extracted/` folder.
- Warnings: one distorted element warning, direct-incrementation exact-time output warnings, unsupported `*ELEMENT OUTPUT` warnings for user elements, and linker `LNK4210` warnings. These do not block the technical gate but must be interpreted during scientific comparison.

## Completion Gate

This record must be complete before any production Abaqus/HPC submission. The next controlled HPC task, only after explicit approval, is one one-CPU `testq` submission of the prepared Abaqus/Standard trivial `UEXTERNALDB` compile/link/license smoke test. The next scientific baseline task remains comparison of the unchanged Molnar single-notch RF-U curve and phase-field/crack evolution against reference behavior.
