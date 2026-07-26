# Stage F1-J1 Mode-II H0 Serial Baseline Preparation Record

- **Task ID**: `F1-J1-PREP-R2` (Runtime Chain Requalified)
- **Stage**: Stage F (Mode-II mixed-mode benchmark)
- **Classification**: `stage_f_mode_ii_h0_serial_runtime_chain_requalified`
- **Preparation Parent Revision**: `309e65c09ead47659c26e6b03f0cf9f410755bd5`
- **Scientific Freeze Revision**: `17240f646cf1e382396006ab635976fa22a67890`
- **Datacheck Job ID**: `1378911.mmaster02` (datacheck passed)
- **Solver Authorization**: `false` (unauthorized; preparation only)
- **Jobs Submitted**: 0
- **Runtime Dependencies Prestaged**: `true` (staged PBS script, `extract_molnar_single_notch.py`, `validate_mode_ii_h0_serial_results.py`)
- **Unit Tests Status**: `pass` (18/18 unit tests passing in `tests/unit/test_validate_mode_ii_h0_serial_results.py`)

## Hardened Execution & Provenance Pipeline

1. **Unchanged Scientific Package**:
   - `models/generated/mode_ii/h0_serial/ModeII_H0_serial.inp` (`32a25380767bbb0e9e76eb55b3bb7a97d78bb75c4f86c7e8585aa2032ce2d33b`)
   - `models/generated/mode_ii/h0_serial/ModeII_H0_serial.for` (`5decf4b1f587019d6bdd904e8ceed22175c113e070e714777cb998da428e4d8c`)

2. **Prepared Resource Envelope**:
   - Queue: `entry_imfdfkmq`
   - Nodes: 1, CPUs: 1, MPI Ranks: 1, OMP Threads: 1
   - Memory: 16 GB
   - Walltime: 04:00:00
   - Abaqus: 2023, Intel: 2024.2, GCC: 11.4.0, Python: 3.11.7

3. **Prestaged Runtime Dependencies & Provenance**:
   - `<STAGE_ROOT>/MODE_II_H0_LOGIN_MANIFEST.json`
   - `<STAGE_ROOT>/runtime/scripts/hpc/stage_f/02_mode_ii_h0_serial.pbs`
   - `<STAGE_ROOT>/runtime/scripts/postprocessing/extract_molnar_single_notch.py`
   - `<STAGE_ROOT>/runtime/scripts/validation/validate_mode_ii_h0_serial_results.py`
   - Hashes recorded in login manifest and compared pre-solver against runtime manifest via `MODE_II_H0_RUNTIME_STAGING_CHECK.json`.

4. **Hardened Validation Gates**:
   - Fail-closed Python 3.10+ module load requirement before execution.
   - Staged PBS script submitted to `qsub` rather than mutable checkout.
   - Result evidence written outside git clone to `EVIDENCE_ROOT` (`/home/pr21vyci/adaptive-remeshing-evidence/`).
   - Strict validation checks for finite RF/energies, final displacement `|U1|` within `1e-6` of `0.010` mm, zero phase healing violations, zero history decrease violations, nonempty crack path, mandatory log evidence, and matching deck/source/runtime hashes across login & runtime manifests.

5. **Status & Authorization Boundary**:
   - Runtime chain requalification complete: `solver_preparation_complete = true`
   - Solver execution: `solver_authorized = false`
   - A separate explicit `F1-J1-AUTH` authorization commit and submission approval is required before solver execution.
