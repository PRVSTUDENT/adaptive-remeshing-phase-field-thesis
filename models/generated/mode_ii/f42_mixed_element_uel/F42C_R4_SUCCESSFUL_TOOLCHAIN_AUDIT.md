# F42C-R4 Successful Toolchain Audit: Job 1384666.mmaster02

## 1. Historical Job Inspection

- **Successful Job ID**: `1384666.mmaster02` (`F42TRI1_CORE`)
- **Package Path**: `models/generated/mode_ii/f42_mixed_element_uel/f42tri1_core_uel_only`
- **PBS Script**: `F42TRI1_CORE.pbs`
- **Module Command Used**: `module load abaqus/2023 || true`
- **`module purge` Used**: `false` (No `module purge` was executed).
- **Environment Inheritance**: Standard login environment inherited via `#PBS -V` containing system `gcc` (`/usr/bin/gcc`, GCC 11.4.0).
- **Compiler / Abaqus Pair**: Abaqus 2023 + Intel Fortran Compiler (`ifort`) using system GCC toolchain path.

## 2. Root Cause Analysis of F42TRI2 Failures

1. **Job 1384658**: Wrapper guard failed on compute node due to missing environment variable transfer (`F42TRI2_WRAPPER_AUTHORIZED`).
2. **Job 1384659**: `module load intel/2024.2.0 abaqus/2023 || true` failed because `ifort` was not found on compute node PATH without proper module sequence.
3. **Job 1384660**: `module purge` wiped out system `gcc` environment. When `module load intel/2024.2.0` was executed after `module purge`, `ifort` failed with:
   `ifort: error #10417: Problem setting up the Intel(R) Compiler compilation environment. Requires 'install path' setting gathered from 'gcc'`.

## 3. Proven Toolchain Recipe

To resolve `ifort error #10417` fail-closed:
- **Module Sequence**:
  ```bash
  module load gcc/11.4.0
  module load intel/2024.2.0
  module load abaqus/2023
  ```
- **Validation Requirement**: `gcc`, `ifort`, and `abaqus` must all resolve cleanly and `ifort -c` must compile a Fortran probe without errors.
