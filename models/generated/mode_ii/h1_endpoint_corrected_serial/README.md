# Mode-II H1 endpoint-corrected serial package

Classification: `stage_f_mode_ii_h1_endpoint_corrected_package_prepared`

## Technical Parameters

- Mesh resolution: $h_1 = 0.0025\text{ mm}$ ($h_1/\ell_c = 0.1667$).
- Elements: 12064 physical, 36192 layered (UEL/UMAT).
- Fortran `N_ELEM`: 12064.
- Target endpoint: $U_1 = 0.010\text{ mm}$ at $t=0.2$ (Step-2 end).
- Boundary conditions: Mode-II pure shear (RP U1 prescribed, bottom U1/U2 fixed).
- Executable boundary: `datacheck_authorized: false`, `solver_authorized: false`.
