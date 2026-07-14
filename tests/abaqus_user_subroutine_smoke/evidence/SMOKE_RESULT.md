# Abaqus User-Subroutine Smoke Test Result

Date: 2026-07-14

## Command

```powershell
abaqus job=smoke_user_subroutine input=smoke_user_subroutine.inp user=smoke_uexternaldb.for cpus=1 interactive
```

Working directory:

```text
tests/abaqus_user_subroutine_smoke
```

## Fixture

- Input deck: `tests/abaqus_user_subroutine_smoke/smoke_user_subroutine.inp`
- User subroutine: `tests/abaqus_user_subroutine_smoke/smoke_uexternaldb.for`
- Purpose: compiler/linker/startup smoke test only; no Molnar source and no phase-field formulation.

## Result

Classification: `compiler_discovery_fail`

Abaqus started, checked out licenses, and began compiling Abaqus/Standard user subroutines. Compilation failed because the configured Intel Fortran command `ifx` was not found on PATH.

Verbatim terminal evidence:

```text
Begin Compiling Abaqus/Standard User Subroutines
7/14/2026 10:14:14 AM
'ifx' is not recognized as an internal or external command,
operable program or batch file.
Abaqus Error: Problem during compilation - smoke_uexternaldb.for
Abaqus/Analysis exited with errors
```

License/startup evidence:

```text
Abaqus/Standard checked out 5 tokens from Flexnet server localhost.
<9994 out of 9999 licenses remain available>.
```

PowerShell observed `ExitCode: 0` despite Abaqus reporting analysis errors, so future automation must parse Abaqus output/status files rather than trusting only the process exit code.

## Generated Evidence

Generated and preserved:

- `terminal_output.txt`
- `terminal_output_utf8.txt`
- `smoke_user_subroutine.com`
- `smoke_user_subroutine.env`

Not generated because compilation failed before solver execution:

- `.log`
- `.dat`
- `.msg`
- `.sta`

## Abaqus Compile/Link Configuration

From `smoke_user_subroutine.env`:

```text
compile_fortran = ['ifx', '/c', '/fpp', '/extend-source', '/DABQ_WIN86_64', '/DABQ_FORTRAN', '/iface:cref', '/recursive', '/Qauto', '/align:array64byte', '/Qpc64', '/Qprec-div', '/Qfma-', '/fp:precise', '/Qimf-arch-consistency:true', '/Qfp-speculation:safe', '/Qprotect-parens', '/reentrancy:threaded', '/QxSSE3', '/QaxAVX', '/include:%I', '/include:C:\\SIMULIA\\EstProducts\\2024', '%P']
link_exe = ['LINK', '/nologo', '/INCREMENTAL:NO', '/subsystem:console', '/machine:AMD64', ...]
link_sl = ['LINK', '/nologo', '/NOENTRY', '/INCREMENTAL:NO', '/subsystem:console', '/machine:AMD64', ...]
```

## Gate Status

The WP0 compiler/linker smoke gate is not passed. Do not run the original Molnar examples until Abaqus can discover a supported Intel Fortran `ifx` environment and this smoke test reaches successful compile, link, and solver startup.
