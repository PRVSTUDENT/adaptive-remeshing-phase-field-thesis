# Mode-II H1 Uniform-Reference Benchmark Definition

Classification: `stage_f_mode_ii_h1_uniform_benchmark_definition`

## Scientific Specification

- **Geometry:** $1.0\text{ mm} \times 1.0\text{ mm}$ square plate with left-edge notch ($a=0.5\text{ mm}$).
- **Formulation:** Accepted Molnar staggered UEL/UMAT formulation.
- **Mesh size:** $h_1 = 0.0025\text{ mm}$ ($h_1/\ell_c = 0.1667$).
- **Elements:** 12064 physical, 36192 layered (phase U1, displacement U2, visualization CPS4).
- **Fortran `N_ELEM`:** 12064.
- **Boundary Conditions:** Mode-II pure shear ($U_1$ prescribed via RP DOF1, bottom $U_1/U_2$ fixed, top $U_2$ fixed).
- **Target Endpoint:** $U_1 = 0.0100\text{ mm}$ at $t=0.2\text{ s}$ (Step 2, 2000 increments).
- **Execution Boundary:** `datacheck_authorized: false`, `solver_authorized: false`.
