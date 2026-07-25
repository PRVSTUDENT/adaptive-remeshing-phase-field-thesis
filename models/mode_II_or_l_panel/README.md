# Mode II or L-Panel Benchmark

## Current selection

**Mode-II pure shear** (Molnar single-edge notch, \(\alpha=0^\circ\)) is the active
Stage F second benchmark after the scoped Mode-I pipeline.

- Definition: `configs/studies/mode_ii_molnar_shear.yaml`
- Protocol: `docs/studies/STAGE_F_MODE_II_BENCHMARK_PROTOCOL.md`
- H0 package: `models/generated/mode_ii/h0_serial/`
- HPC lane: `runs/hpc/stage_f/mode_ii_h0/`

L-panel remains a later optional curved-path candidate and is not prepared.

## Boundary

F0 is preparation only. Datacheck and solver submissions require separate
authorization commits. No MISESERI remeshing is included in the H0 technical
package.
