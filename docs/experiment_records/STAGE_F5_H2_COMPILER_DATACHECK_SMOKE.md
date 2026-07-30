# Stage F5 H2 compiler/datacheck smoke

Date: 2026-07-30
Task: `F5-H2-COMPILER-DATACHECK-SMOKE-EXECUTE`
Final classification: `stage_f5_h2_compiler_datacheck_smoke_pass`

## Objective and provenance

The job tested whether Abaqus 2023 could compile and link the exact frozen H2
UEL/UMAT source and complete `datacheck` for the exact frozen
$U_1=0.020\,\mathrm{mm}$ H2 deck. It did not authorize or execute a full
analysis.

- runtime/source revision:
  `e8a1d32210261745413c12bfe5e378f7fcc14498`
- authorization revision:
  `eb8d72080a12516a0c197611986fcf0b7699b59a`
- consumed-submission revision:
  `8b3dea5cd4990e6aebea4288b6a2f248418f6945`
- run ID: `F5CMP_20260730_113544_e8a1d32`
- deck SHA-256:
  `fdcd6ee1b1d6cbfb88d59a3edfb7f1c6b35cecde736a427f6b3030b0443b10bf`
- Fortran SHA-256:
  `49c9054ab5faec9e069e0a9149af5058e6f1e11ab164c2a0e318f60282309b37`

An earlier task using the direct hostname stopped before cluster access with
SSH authentication failure. The later execution used the canonical
`tu_freiberg` SSH alias, consumed exactly one newly authorized submission, and
did not retry.

## Scheduler and execution result

PBS job `1379939.mmaster02` (`M2H2CMP1`) routed from
`entry_imfdfkmq` to `normal_imfdfkmq` and ran on `mnode105/0`.
The request was 1 CPU, 8 GB and 30 minutes. PBS reports state `F`,
`Exit_status=0`, walltime 19 seconds, CPU time 12 seconds, memory
957,660 kB and virtual memory 866,276 kB. The job ran once.

The environment was:

```text
gcc/11.4.0 -> intel/2024.2.0 -> abaqus/2023
ifort 2021.13.0
ifx 2024.2.0
Abaqus 2023
```

All four staged-file hash checks passed. Abaqus compiled and linked the user
subroutine, completed input processing and datacheck, printed
`Abaqus JOB M2H2CMP1 COMPLETED`, and returned 0. The model processed 101,556
elements, 34,508 nodes and 103,522 variables. The datacheck memory estimate
was 73 MB minimum and 156 MB to minimize I/O.

## Warnings and evidence quality

The logs contain no fatal error. Recorded warnings are the ifort deprecation
and deprecated `-extend_source` spelling, conversion of exact-time output to
approximate-time output under direct incrementation, unsupported element
output requests for user elements, and an ignored inactive-DOF boundary
condition on node 33961.

The raw `STATUS.json` is preserved but is not valid JSON: the grep-based
`error_count` and `warning_count` expressions emitted one line per searched
file. Classification therefore uses the final PBS record, compiler status,
hash check and Abaqus `.log`, `.dat` and `.msg` evidence. `tracejob` could not
find the job in the one-day server log; its exact diagnostic is preserved.

## Evidence and claim boundary

Canonical evidence:
`runs/hpc/stage_f/h2_u020_compiler_datacheck_smoke/evidence/1379939.mmaster02/`.
The directory contains the final scheduler records, runtime and package
manifests, compiler environment/status, hash check, Abaqus text logs,
validation summary and per-file SHA-256 inventory.

This pass establishes only that the exact frozen H2 source compiles, links and
passes Abaqus 2023 datacheck in the selected cluster environment. It does not
establish solver convergence, post-peak fracture response, scientific
equivalence, mesh convergence, threaded safety or native MISESERI remeshing.
No full analysis, extractor, scientific validator or result figure was
applicable. The scratch ODB and other binary databases were not collected.

Submission authority remains consumed (`1/1`); retries, replacements and
automatic follow-up are false. Closure revision:
`PENDING_CLOSURE_COMMIT`.
