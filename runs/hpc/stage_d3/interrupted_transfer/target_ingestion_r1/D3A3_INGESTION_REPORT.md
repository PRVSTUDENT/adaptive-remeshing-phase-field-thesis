# D3A3-R1 Target Ingestion Hold

Classification: `stage_d3a3_solver_fail_transfer_table_compile`

- Job: `1377383.mmaster02`
- Source commit: `4710fa4a412a3af6914040f5578529c2c0e33214`
- Failed predecessor: `1377382.mmaster02`
- Correction applied: explicit `gcc/11.4.0`, `intel/2024.2.0`, and `abaqus/2023` modules with `OMP_NUM_THREADS=1`
- Compiler environment: pass; `ifort` path and version recorded in `D3A3_COMPILER_ENVIRONMENT.txt`
- PBS exit status: `1`
- Solver analysis started: `false`
- Failure: Intel Fortran aborted while compiling `d3_transfer_uel.for` because `d3_transfer_table.inc` exceeded the statement token limit.

No `D3A3_R1.ok` or canonical `D3A3.ok` marker was created. D3D and D3E remain blocked.
