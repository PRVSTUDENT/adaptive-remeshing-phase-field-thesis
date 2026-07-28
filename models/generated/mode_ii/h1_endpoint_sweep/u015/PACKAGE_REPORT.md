# Mode-II H1 Endpoint Sweep Package Report: u015

Classification: `stage_f_mode_ii_h1_endpoint_sweep_package_report`
Variant: `u015`
Job Name: `m2h1_u015`

## Technical Specification

- **Target Displacement:** $U_1 = 0.015\text{ mm}$
- **Step 1:** Linear loading to $U_1 = 0.005\text{ mm}$, period $0.5\text{ s}$, 500 max increments
- **Step 2:** Shear propagation to $U_1 = 0.015\text{ mm}$, period $0.4\text{ s}$, 4000 max increments
- **Displacement Increment:** $\Delta U_1 \le 2.5 \times 10^{-6}\text{ mm/inc}$
- **Mesh:** $h_1 = 0.0025\text{ mm}$, 12064 physical elements, 36192 layered elements, 12382 nodes
- **Fortran `N_ELEM`:** 12064
- **Deck SHA-256:** `3a3e549db6f4a457079ac1a661bd1b0bb0179fc139e00bd8b2137de95bf2f227`
- **Fortran SHA-256:** `745db8fcfb612895e0289f4533c90d204cc9b2ade3678a035614feeb308b5ead`
