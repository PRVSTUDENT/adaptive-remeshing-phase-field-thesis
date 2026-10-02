# Pre-Job Anti-Deviation Card: PK_MODE1_T1_COARSE_ENERGY

- **Candidate ID**: T1 (2x_coarse)
- **Model Package**: `models/pandey_kumar_mode1/17_temporal_convergence_t1_coarse/`
- **Scientific Role**: Mode-I Gate-6B Temporal Discretization Convergence Evaluation Candidate
- **Status**: DATACHECK_PASSED_READY_AFTER_CORRECTED_S1_ENERGY_QUALIFICATION (Strictly Unsubmitted)
- **Authorization**: `authorized: false` (Must await S1 energy qualification and explicit supervisor authorization)

---

## 1. Single Intended Numerical Difference
- **Temporal Discretization Ratio**: `2x_coarse`
- **Step 1 (Elastic Pre-Peak, u in [0, 0.0050] mm)**:
  - Nominal Time: 1.0 s
  - Time Increment dt: `1.000000e-03 s`
  - Nominal Increments: `1000`
  - Bounds: dt_min = 1.0e-9 s, dt_max = `1.000000e-03 s`
- **Step 2 (Fracture & Propagation, u in [0.0050, 0.0100] mm)**:
  - Nominal Time: 1.0 s
  - Time Increment dt: `4.000000e-04 s`
  - Nominal Increments: `2500`
  - Bounds: dt_min = 1.0e-9 s, dt_max = `4.000000e-04 s`
- **Total Intended Step Count**: `3500` increments

---

## 2. Frozen Scientific & Numerical Quantities
- **Mesh Topology**:
  - Total Physical Elements: `15,192` (Layer 1: Phase UEL 1..15192, Layer 2: Mech UEL 15193..30384, Layer 3: Companion CPE4 30385..45576)
  - Total Nodes: `15,521`
  - Geometry: 1.0 x 1.0 mm square with initial horizontal sharp slit at y=0.5 mm (a0 = 0.5 mm)
  - Process Zone Resolution: h = 0.0030 mm (l0/h = 2.5)
- **Material & Phase-Field Constants**:
  - Young's Modulus: E = 210.0 kN/mm^2 (GPa)
  - Poisson's Ratio: nu = 0.3
  - Fracture Toughness: Gc = 0.0027 kN/mm (kJ/m^2)
  - Phase-Field Length Scale: l0 = 0.0075 mm
  - Residual Stiffness: k = 1.0e-7
  - Companion Scale Factor NPHYS: 15,192.0
- **Boundary Conditions & Kinematic Coupling**:
  - Bottom edge: u_y = 0.0 (N_BOTTOM)
  - Bottom-left corner pin: u_x = 0.0 (N_PIN)
  - Top edge horizontal restraint: u_x = 0.0 (N_TOP)
  - Top edge vertical displacement tied via kinematic equations to Reference Point RP (Node 999999)
- **Reference Thickness Convention**:
  - Unit thickness t_ref = 1.0 mm (explicit project baseline convention; not literature-attributed)

---

## 3. Cryptographic Provenance & File Hashes
- **Input Deck**: `PK_MODE1_T1_COARSE_ENERGY.inp`
  - SHA-256: `33183ADA17DA6712F93DA5648D1D4C9B41C27398DA472EE6619E0839E96ACCFF`
- **User Subroutine**: `f42_mixed_uel.for`
  - SHA-256: `CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6`
- **Dual-Channel Notification**: `job_notifications.sh`
  - SHA-256: `96756A681D2D36C11B36B89288F631F8ECC9537543C2C745A4BAE1B425984B47`
- **Datacheck Launcher**: `submit_datacheck.pbs`
- **Solver Launcher**: `submit_solver.pbs`

---

## 4. Expected Output Channels & Instruments
1. **Working-Directory Energy Balance**:
   - Written directly by Fortran UEL via `CALL GETOUTDIR` to `uel_energy_balance.csv`
   - Records at every converged increment: step, increment, time, u, F, E_elas, E_frac, E_model, W_ext, Delta_book, rel_diff
2. **SDV Field Output on Visualization Layer (`All_elem`)**:
   - `SDV17`: E_frac (integrated fracture energy per element)
   - `SDV18`: E_elas (integrated elastic strain energy per element)
   - `SDV19`: psi_f (fracture energy density)
   - `SDV20`: psi_e (elastic energy density)
3. **Reference Point Reaction & Displacement**:
   - `U2` and `RF2` at Node 999999 (RP) recorded at every increment.

---

## 5. Matched-Displacement Comparison Targets
- **Target Comparison Baseline**: Corrected S1 Reference (`PK_M1_REF15K_ENERGY`, Job 1409734)
- **Methodology**: Strict 1D monotonic piecewise linear interpolation on displacement u in [0, 0.0100] mm
- **Extrapolation Policy**: ZERO extrapolation. Common displacement domain only.
- **Audited Metrics**:
  - Initial structural stiffness K0 (kN/mm) and R^2 linearity
  - Peak reaction force F_max (kN) and peak displacement u(F_max) (mm)
  - Energy trajectories E_elas(u), E_frac(u), E_model(u), W_ext(u)
  - Global energy conservation bookkeeping error varepsilon_book(u)
  - No synthetic or arbitrary tolerance bands. Pure scientific matched-state audit.
