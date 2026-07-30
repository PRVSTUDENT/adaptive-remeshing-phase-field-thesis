# HPC Abaqus/Fortran environment recovery

Date: 2026-07-30  
Scope: read-only evidence audit and candidate preparation; no compilation,
datacheck, solver execution or submission was performed.

## Evidence-backed candidate

Successful UEL jobs `1379431.mmaster02`, `1379433.mmaster02` and
`1379578.mmaster02` used the Stage F scripts' module order:

```text
module purge
module load gcc/11.4.0
module load intel/2024.2.0
module load abaqus/2023
```

Preserved job `1379431` environment evidence resolves:

```text
abaqus  /cluster/application/abaqus/2023/Commands/abaqus
ifort   /cluster/stages/2024.0/software/intel/2024.2/compiler/2024.2/bin/ifort
ifx     /cluster/stages/2024.0/software/intel/2024.2/compiler/2024.2/bin/ifx
```

This is stronger than assuming a generic Intel module: it is the exact
module family and executable location preserved by a successful H1
datacheck, and the same ordered script contract was used for the successful
H1 and H2 UEL analyses. The archived lightweight evidence does not preserve
the full compiler/link command, linker version, compiler `--version` text,
or site environment-file expansion. Those details remain pending capture by
the proposed smoke job.

## Compiler-environment matrix

| Candidate/order | Compiler found | Abaqus found | Evidence | Status |
|---|---:|---:|---|---|
| `gcc/11.4.0` → `intel/2024.2.0` → `abaqus/2023` | `ifort`, `ifx` at paths above | Abaqus 2023 | jobs 1379431/1379433/1379578 and archived scripts | selected candidate; previously successful |
| `intel/2024.2.0` → generic `abaqus` | no, in job 1379892 | yes | Stage F4 replacement | failed compute environment |
| Abaqus then Intel | not rechecked | not rechecked | none preserved | unresolved module-order sensitivity |
| `abaqus/2022` with Intel 2024.2 | not rechecked | not rechecked | requested discovery only | unqualified |

Direct read-only discovery against `mlogin01.hrz.tu-freiberg.de` was attempted
with non-interactive SSH but authentication was unavailable in this session.
Therefore current module availability, site Abaqus environment files, module
order sensitivity, compiler/linker versions and emitted compile/link commands
are explicitly **not newly verified**.

## Qualification boundary

The proposed `M2H2CMP1` job prints the module list, executable paths, compiler
versions and Abaqus system/release information; verifies the exact deck and
Fortran hashes; and runs only `datacheck interactive`. Compilation must not
be described as verified until that separately authorized PBS job passes.
