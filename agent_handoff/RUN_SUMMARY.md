# HPC Abaqus Environment Smoke Test Rerun With GCC

Date: 2026-07-15

Job ID: 1374530.mmaster02

Repository revision before submission:

```text
f508a469e8247565e3df539346c219b413e492b8
```

Repair:

```text
loaded gcc/11.4.0 before intel/2024.2.0
```

Reason:

```text
compute-node ifx initialization failed with Intel error #10417 in job 1374529.mmaster02
```

Scope:

```text
environment-only smoke rerun
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
- PBS exit status: 127
- Scheduler metadata: `Resource_List.ngpus = 1` appeared again, but the script did not request or use a GPU.
- Scratch run directory: /scratch/pr21vyci/adaptive-remeshing/runs/abaqus_environment_smoke_1374530.mmaster02

Acceptance review:

- PBS execution: pass
- Scratch creation: pass
- gcc module load: pass
- Exit status was 0: fail
- compiler diagnostics: not reached
- Abaqus diagnostic: not reached
- failure trigger: `git` unavailable in batch PATH
- Repository revision printed: fail
- `Environment smoke probe completed.` printed: fail

Classification:

```text
hpc_environment_smoke_fail
```

The rerun confirms PBS execution, compute-node assignment, scratch creation, and progression past the repaired module-loading block, but failed before compiler diagnostics because `git` was not available in the compute-node job environment when the script tried to print the repository revision. This is still an HPC batch-metadata dependency failure, not a PBS, Abaqus, repository, model, MISESERI, or remeshing failure. It does not establish whether the GCC-plus-Intel repair fixed compute-node `ifx` initialization.

Next candidate repair is to make the repository revision diagnostic robust on compute nodes, either by loading an appropriate Git module before calling `git` or by passing the revision into the PBS job from the submission environment. No further rerun is approved in this record.
