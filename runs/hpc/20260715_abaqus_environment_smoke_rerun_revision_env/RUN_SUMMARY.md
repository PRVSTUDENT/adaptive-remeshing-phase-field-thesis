# HPC Abaqus Environment Smoke Test - Final Rerun

Date: 2026-07-15

Job ID: 1374531.mmaster02

Repository revision:

```text
d2e9e3c0d1e86e5f12772cb3d7e191a5377ea54f
```

Repair history:

1. Initial run failed because compute-node IFX could not resolve the required GCC environment.
2. First rerun loaded gcc/11.4.0 but failed before compiler checks because Git was unavailable in the batch environment.
3. This rerun supplies the revision through PROJECT_REVISION and has no compute-node Git dependency.

Requested resources:

- Queue: testq
- Nodes: 1
- CPUs: 1
- Memory: 8 GB
- Wall time: 00:30:00

Observed execution:

- Compute host: mnode098.cluster
- PBS state: F
- PBS exit status: 0
- Scheduler metadata: `Resource_List.ngpus = 1` appeared again, but the script did not request or use a GPU.
- Scratch run directory: /scratch/pr21vyci/adaptive-remeshing/runs/abaqus_environment_smoke_1374531.mmaster02

Acceptance review:

- PBS state was F: pass
- Exit status was 0: pass
- Repository revision supplied through `PROJECT_REVISION`: pass
- gcc/11.4.0 loaded: pass
- intel/2024.2.0 loaded: pass
- abaqus/2023 loaded: pass
- valid gcc path: pass
- valid gfortran path: pass
- valid ifx path: pass
- valid abaqus path: pass
- `gcc --version` completed: pass
- `gfortran --version` completed: pass
- `ifx --version` completed: pass
- `abaqus information=release` completed: pass
- `Environment smoke probe completed.` printed: pass

Classification:

```text
hpc_environment_smoke_pass
```

Scientific scope:

This job checks PBS execution, module loading, compiler visibility, Abaqus release visibility, scratch setup, and repository revision capture. It does not test Abaqus user-subroutine compilation/linking or validate the phase-field formulation.
