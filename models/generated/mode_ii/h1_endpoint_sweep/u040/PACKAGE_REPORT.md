# Mode-II H1 Endpoint Sweep Package Report: u040

Classification: `stage_f_mode_ii_h1_endpoint_sweep_package_report`
Variant: `u040`
Job Name: `m2h1_u040`

## Technical Specification

- **Target Displacement:** $U_1 = 0.040\text{ mm}$
- **Step 1:** Linear loading to $U_1 = 0.005\text{ mm}$, period $0.5\text{ s}$, 500 max increments
- **Step 2:** Shear propagation to $U_1 = 0.040\text{ mm}$, period $1.4\text{ s}$, 14000 max increments
- **Displacement Increment:** $\Delta U_1 \le 2.5 \times 10^{-6}\text{ mm/inc}$
- **Mesh:** $h_1 = 0.0025\text{ mm}$, 12064 physical elements, 36192 layered elements, 12382 nodes
- **Fortran `N_ELEM`:** 12064
- **Deck SHA-256:** `42102cc3b632c2234335f9176ec5d9708679333fd9bb6b749e1825578a024550`
- **Fortran SHA-256:** `745db8fcfb612895e0289f4533c90d204cc9b2ade3678a035614feeb308b5ead`
