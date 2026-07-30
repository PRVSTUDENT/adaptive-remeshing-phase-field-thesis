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

The separately authorized F5 compiler-smoke submission attempt repeated this
mandatory preflight on 2026-07-30 and again received
`Permission denied (publickey,password,hostbased)`. The stopping rule was
applied before authorization activation: qstat/module inspection was not
reached and qsub attempts remained zero.

## Alias transport recovery

The read-only recovery task identified the transport difference:

- `tu_freiberg` through the dedicated `codex_config` resolves user
  `pr21vyci`, `IdentitiesOnly=yes`, and an existing dedicated identity file.
- the direct hostname resolves local username `pruth`,
  `IdentitiesOnly=no`, and no existing default identity file.

The alias connected successfully to `mlogin01.cluster`; `qstat -u pr21vyci`
was accessible and empty. The Windows SSH-agent service is stopped and
disabled, but the configured identity file works without it.

Both inspected module orders preserved the required executables. Selected
order A matches the previously successful Stage F evidence:

```text
module purge
module load gcc/11.4.0
module load intel/2024.2.0
module load abaqus/2023
```

Verified read-only paths and versions:

```text
ifort  /cluster/stages/2024.0/software/intel/2024.2/compiler/2024.2/bin/ifort
       ifort (IFORT) 2021.13.0 20240602
ifx    /cluster/stages/2024.0/software/intel/2024.2/compiler/2024.2/bin/ifx
       ifx (IFX) 2024.2.0 20240602
abaqus /cluster/application/abaqus/2023/Commands/abaqus
       Abaqus 2023
```

No compilation, datacheck, solver or submission occurred. This verifies
transport and executable visibility, not H2 user-subroutine compilation.

## Qualification boundary

The proposed `M2H2CMP1` job prints the module list, executable paths, compiler
versions and Abaqus system/release information; verifies the exact deck and
Fortran hashes; and runs only `datacheck interactive`.

## H2 compilation and datacheck qualification

PBS job `1379939.mmaster02` completed the proposed qualification on
`mnode105/0`. With the selected module order, Abaqus 2023 invoked ifort
2021.13.0, compiled and linked the exact frozen H2 UEL/UMAT source, and
completed datacheck with Abaqus return code 0. All staged input hashes matched.
The final classification is
`stage_f5_h2_compiler_datacheck_smoke_pass`.

The retained evidence is under
`runs/hpc/stage_f/h2_u020_compiler_datacheck_smoke/evidence/1379939.mmaster02/`.
The raw job `STATUS.json` is malformed only in its multi-file grep counters;
the scheduler record, compiler status, hash check and Abaqus text logs provide
the closure evidence. This qualification does not validate a full H2 solve or
any scientific fracture result.
