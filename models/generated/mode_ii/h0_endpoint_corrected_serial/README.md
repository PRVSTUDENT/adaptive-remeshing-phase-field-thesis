# Mode-II H0 endpoint-corrected serial package

Classification: `stage_f_mode_ii_h0_endpoint_corrected_package_prepared`
Endpoint Audit Revision: `49d7d4f1a941a09fbfd3aca147fd612a0a9a6a4c`

## Scope

- Geometry/mesh: accepted Mode-I H0 supplementary single-notch mesh (unchanged).
- Formulation: accepted Molnar staggered UEL/UMAT (`N_ELEM=3930`, byte-identical Fortran).
- Correction: Amp-2 endpoint time changed from 0.5 to 0.2 (`0.0, 0.005 -> 0.2, 0.010`).
- Target endpoint: $U_1 = 0.010\text{ mm}$ at Step-2 end ($t=0.2$, 2000 increments).
- Executable boundary: `datacheck_authorized: false`, `solver_authorized: false`.

## Files

- `ModeII_H0_endpoint_corrected_serial.inp`
- `ModeII_H0_endpoint_corrected_serial.for`
- `PACKAGE_MANIFEST.json`
- `input_hashes.sha256`
- `HISTORICAL_PARENT_HASHES.json`
- `ENDPOINT_CORRECTION_PROVENANCE.json`
