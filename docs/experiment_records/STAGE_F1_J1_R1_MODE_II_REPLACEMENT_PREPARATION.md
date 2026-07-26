# Stage F1-J1-R1 Mode-II Replacement Preparation Record

- **Task ID**: `F1-J1-R1-PREP`
- **Stage**: Stage F (Mode-II mixed-mode benchmark)
- **Classification**: `stage_f_mode_ii_h0_serial_replacement_prepared_unauthorized`
- **Preparation Parent Revision**: `d569775f7c5b4ce109260ff3892499476ccd7b5d`
- **Source Failure Task**: `F1-J1` (job `1378919.mmaster02`, `stage_f_mode_ii_h0_serial_staging_fail`)
- **Source Failure Consumed**: `true` (original authorization 1/1 consumed)
- **Source Failure Solver Started**: `false` (halted before Abaqus solve)
- **Staging Defect Repaired**: `true` (dual-deck scratch staging and 64-char SHA validation implemented)
- **Staging Contract Tests**: `pass` (`tests/unit/test_validate_mode_ii_h0_serial_staging_contract.py`)
- **Replacement Authorized**: `false` (unauthorized; preparation only)
- **Jobs Submitted**: 0

## Repair Strategy & Infrastructure Requalification

1. **Dual-Deck Scratch Staging**:
   - In `02_mode_ii_h0_serial.pbs`, both `ModeII_H0_serial.inp` (`${ORIGINAL_DECK}`) and `mode_ii_h0_serial.inp` (`${ABAQUS_DECK}`) are explicitly staged in scratch.
   - Hashes are computed from explicit paths and verified equal (`${DECK_SHA} = ${ABAQUS_DECK_SHA}`).

2. **Strict Hash Validation**:
   - Every hash variable (`${DECK_SHA}`, `${ABAQUS_DECK_SHA}`, `${SOURCE_SHA}`, `${EXTRACTOR_SHA}`, `${VALIDATOR_SHA}`, `${PBS_SHA}`) is validated against `^[0-9a-f]{64}$` before writing `MODE_II_H0_RUNTIME_MANIFEST.json`. Empty or invalid hashes trigger fail-closed exit `7`.

3. **Offline Staging Contract Validator & Tests**:
   - Added `scripts/validation/validate_mode_ii_h0_serial_staging_contract.py` for offline contract verification.
   - Added unit test suite `tests/unit/test_validate_mode_ii_h0_serial_staging_contract.py` reproducing M-090 failure and asserting dual-deck staging behavior.

4. **Authorization Boundary**:
   - Original F1-J1 authorization remains consumed (`solver_submissions_used: 1`, `solver_authorized: false`).
   - Replacement solver execution remains unauthorized (`replacement_authorized: false`).
   - Downstream Stage F tasks (F2+) remain **blocked** until a separate explicit human decision and replacement authorization record are provided.
