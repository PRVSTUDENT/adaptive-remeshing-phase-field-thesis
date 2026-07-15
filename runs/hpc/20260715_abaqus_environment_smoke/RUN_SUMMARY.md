# HPC Abaqus Environment Smoke Test

Date: 2026-07-15

Job ID: 1374529.mmaster02

Repository revision:

```text
f508a469e8247565e3df539346c219b413e492b8
```

Requested resources:

- Queue: testq
- Nodes: 1
- CPUs: 1
- Memory: 8 GB
- Wall time: 00:30:00

Observed execution:

- Compute host: mnode098.cluster
- PBS state: F
- PBS exit status: 1
- Scratch run directory: /scratch/pr21vyci/adaptive-remeshing/runs/abaqus_environment_smoke_1374529.mmaster02

Acceptance review:

- PBS job was scheduled and started: pass
- One compute host was assigned: pass
- intel/2024.2.0 loaded: pass
- abaqus/2023 loaded: pass
- `which abaqus` returned a valid executable: pass
- `which ifx` returned a valid executable: pass
- `abaqus information=release` completed: pass
- `ifx --version` reported 2024.2.0: fail
- Repository revision matched `f508a469...`: not reached in script output because the compiler-version check failed first
- Script reached `Environment smoke probe completed.`: fail
- PBS exit status was zero: fail

Classification:

```text
hpc_environment_smoke_fail
```

The job confirms PBS execution, compute-node assignment, scratch-directory creation, module loading, Abaqus visibility, and compiler executable visibility up to the compiler-version check. It failed before the final success marker because `ifx --version` returned Intel compiler error `#10417` on the compute node: the compiler environment could not set up the required GCC install-path setting.

This job does not validate Abaqus user-subroutine compilation, linking, licensing, or the phase-field formulation.
