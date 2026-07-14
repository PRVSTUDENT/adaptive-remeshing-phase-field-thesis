# Abaqus User-Subroutine Smoke Test

Purpose: test only the local Abaqus compiler/linker/startup path before any Molnar source is run or modified.

Acceptance criterion:

> Abaqus successfully compiles and links a user subroutine and starts a trivial analysis without undocumented source or environment modifications.

The fixture uses a tiny native-elastic input deck plus a physics-free `UEXTERNALDB` subroutine. The subroutine exists only to force Abaqus through the user-subroutine compile/link path.

Run from this directory:

```powershell
abaqus job=smoke_user_subroutine input=smoke_user_subroutine.inp user=smoke_uexternaldb.for cpus=1 interactive
```

Preserve terminal output and generated `.log`, `.dat`, `.msg`, `.sta`, and `.com` files in `evidence/`.
