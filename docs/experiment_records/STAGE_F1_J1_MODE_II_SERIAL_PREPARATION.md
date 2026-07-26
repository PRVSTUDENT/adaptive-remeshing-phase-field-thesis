# Stage F1-J1 Mode-II H0 Serial Baseline Preparation Record

- **Task ID**: `F1-J1-PREP`
- **Stage**: Stage F (Mode-II mixed-mode benchmark)
- **Classification**: `stage_f_mode_ii_h0_serial_solver_prepared`
- **Operational Revision**: `6b64a3ba05c02c6fd4f9602e735825cacc542203`
- **Scientific Freeze Revision**: `17240f646cf1e382396006ab635976fa22a67890`
- **Datacheck Job ID**: `1378911.mmaster02` (datacheck passed)
- **Solver Authorization**: `false` (unauthorized; preparation only)
- **Jobs Submitted**: 0

## Prepared Execution Pipeline

1. **Unchanged Package**:
   - `models/generated/mode_ii/h0_serial/ModeII_H0_serial.inp` (`32a25380767bbb0e9e76eb55b3bb7a97d78bb75c4f86c7e8585aa2032ce2d33b`)
   - `models/generated/mode_ii/h0_serial/ModeII_H0_serial.for` (`5decf4b1f587019d6bdd904e8ceed22175c113e070e714777cb998da428e4d8c`)

2. **Prepared Resource Envelope**:
   - Queue: `entry_imfdfkmq`
   - Nodes: 1, CPUs: 1, MPI Ranks: 1, OMP Threads: 1
   - Memory: 16 GB
   - Walltime: 04:00:00
   - Abaqus: 2023, Intel: 2024.2, GCC: 11.4.0

3. **Prepared Scripts**:
   - PBS script: `scripts/hpc/stage_f/02_mode_ii_h0_serial.pbs`
   - Guarded submit wrapper: `scripts/hpc/stage_f/submit_mode_ii_h0_serial.sh` (preflight default; submission requires `MODE_II_H0_SOLVER_SUBMIT=1` and `solver_authorized=true`)
   - Extractor: `scripts/postprocessing/extract_molnar_single_notch.py` (component-configurable for Mode I/II)
   - Result validator: `scripts/validation/validate_mode_ii_h0_serial_results.py`

4. **Status & Authorization Boundary**:
   - Preparation complete: `solver_preparation_complete = true`
   - Solver execution: `solver_authorized = false`
   - A separate explicit `F1-J1-AUTH` authorization commit and submission approval is required before solver execution.
