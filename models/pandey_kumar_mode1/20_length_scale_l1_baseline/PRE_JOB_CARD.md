# Pre-Job Anti-Deviation Card: PK_MODE1_L1_BASELINE_ENERGY

- **Candidate ID**: L1 (1.0x_baseline (l0=7.5 um))
- **Model Package**: `models/pandey_kumar_mode1/20_length_scale_l1_baseline/`
- **Scientific Role**: Mode-I Gate-6B Phase-Field Length-Scale Sensitivity / Characterization Candidate
- **Status**: DATACHECK_PASSED_REUSED_AS_S3_REFERENCE
- **Authorization**: `authorized: false` (Must await S1 energy qualification and explicit supervisor authorization)
- **Governing Terminology**: Phase-Field Length-Scale Sensitivity / Characterization (NOT "length-scale convergence")

---

## 1. Single Intended Physical / Formulation Difference
- **Length-Scale Characterization Role**: Baseline reference ($l_0 = 0.0075\,	ext{mm} = 7.5\,\mu	ext{m}$, $h/l_0 = 0.200$)
- **Equivalence Status**: Mathematically identical to Candidate S3 (`PK_MODE1_FIX_H0015_ENERGY.inp`). Reused as anchor.
- **Cluster Submission Action**: `OMIT_FROM_CLUSTER_SUBMISSIONS_REUSE_S3`

---

## 2. Frozen Scientific & Numerical Quantities
- **Mesh Topology**:
  - Total Physical Elements: `41,912` (Layer 1: Phase UEL 1..41912, Layer 2: Mech UEL 41913..83824, Layer 3: Companion CPE4 83825..125736)
  - Total Nodes: `42,364`
  - Geometry: 1.0 x 1.0 mm square with initial horizontal sharp slit at y=0.5 mm ($a_0 = 0.5\,	ext{mm}$)
  - Process Zone Resolution: $h = 0.0015\,	ext{mm}$ ($1.5\,\mu	ext{m}$)
- **Material & Fracture Constants**:
  - Young's Modulus: $E = 210.0\,	ext{kN/mm}^2$ ($210\,	ext{GPa}$)
  - Poisson's Ratio: $\nu = 0.3$
  - Fracture Toughness: $G_c = 0.0027\,	ext{kN/mm}$ ($2700\,	ext{J/m}^2$)
  - Residual Stiffness: $k = 1.0\times 10^{-7}$
  - Companion Scale Factor NPHYS: $41,912.0$
- **Boundary Conditions & Kinematic Coupling**:
  - Bottom edge: $u_y = 0.0$ (`N_BOTTOM`)
  - Bottom-left corner pin: $u_x = 0.0$ (`N_PIN`)
  - Top edge horizontal restraint: $u_x = 0.0$ (`N_TOP`)
  - Top edge vertical displacement tied via kinematic equations to Reference Point RP (Node 999999)
- **Loading Schedule & Solver Controls**:
  - Step 1: $\Delta t = 5.0\times 10^{-4}\,\text{s}$, $2,500$ increments ($u = 0 \to 0.0050\,	ext{mm}$)
  - Step 2: $\Delta t = 2.0\times 10^{-4}\,\text{s}$, $6,000$ increments ($u = 0.0050 \to 0.0100\,	ext{mm}$)
  - Solver: `*Static`, direct sparse solver, `nlgeom=NO`
- **Reference Thickness Convention**:
  - Unit thickness $t_{\text{ref}} = 1.0\,	ext{mm}$ (explicit project baseline convention; not literature-attributed)

---

## 3. Cryptographic Provenance & File Hashes
- **Input Deck**: `PK_MODE1_L1_BASELINE_ENERGY.inp`
  - SHA-256: `1EDC670D587CBBCE2ACB98F215CFFF4AE9DA0C84633BD832A6241B530AB90AC4`
- **User Subroutine**: `f42_mixed_uel.for`
  - SHA-256: `CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6`
- **Dual-Channel Notification**: `job_notifications.sh`
  - SHA-256: `96756A681D2D36C11B36B89288F631F8ECC9537543C2C745A4BAE1B425984B47`
- **Datacheck Launcher**: `submit_datacheck.pbs`
  - SHA-256: `14359B0936C679CE5F489835231150466D523E5D1F9A11CDA731BB54BA8CDAC4`
- **Solver Launcher**: `submit_solver.pbs`
  - SHA-256: `9DA2A8D2CB035B51B9F932075ACCA5976F37DB5C7023F433A1A5DDB5301F2CBA`
- **Historical Source**:
  - Job ID: `1406017.mmaster02`
  - Deck: `PK_M1_S3_H0015.inp`

---

## 4. Expected Output Channels & Instruments
1. **Working-Directory Energy Balance**:
   - Written directly by Fortran UEL via `CALL GETOUTDIR` to `uel_energy_balance.csv`
   - Records at every converged increment: step, increment, time, u, F, E_elas, E_frac, E_model, W_ext, Delta_book, rel_diff
2. **SDV Field Output on Visualization Layer (`All_elem`)**:
   - `SDV17`: E_frac (integrated fracture energy per element in $\text{kN}\cdot\text{mm} = \text{J}$)
   - `SDV18`: E_elas (integrated elastic strain energy per element in $\text{kN}\cdot\text{mm} = \text{J}$)
   - `SDV19`: psi_f (local fracture surface energy density in $\text{kN/mm}^2 \equiv \text{J/mm}^3$)
   - `SDV20`: psi_e (local elastic strain energy density in $\text{kN/mm}^2 \equiv \text{J/mm}^3$)
3. **Reference Point Reaction & Displacement**:
   - `U2` and `RF2` at Node 999999 (RP) recorded at every increment.

---

## 5. Matched-Displacement Comparison Targets
- **Target Comparison Baseline**: Candidate S3 Reference ($l_0 = 0.0075\,	ext{mm}$ baseline)
- **Methodology**: Strict 1D monotonic piecewise linear interpolation on displacement $u \in [0, 0.0100]\,	ext{mm}$
- **Extrapolation Policy**: ZERO extrapolation. Common displacement domain only.
- **Audited Metrics**:
  - Initial structural stiffness $K_0$ ($\text{kN/mm}$) and $R^2$ linearity
  - Peak reaction force $F_{\max}$ ($\text{kN}$) and peak displacement $u(F_{\max})$ ($\text{mm}$)
  - Post-peak softening slope and residual response
  - Energy trajectories $E_{\text{elas}}(u)$, $E_{\text{frac}}(u)$, $E_{\text{model}}(u)$, $W_{\text{ext}}(u)$
  - Global energy conservation bookkeeping error $\Delta_{\text{book}}(u)$
  - Matched-displacement damage field distribution $d(x, y)$
  - Ligament profile along symmetry line $d(x, y=0.5\,	ext{mm})$
  - Transverse damage localization profile across crack path $d(x=0.75\,	ext{mm}, y)$
  - Crack path centerline trajectory $y(x)$
  - Increment and cutback history
  - No synthetic or arbitrary tolerance bands. Pure scientific characterization audit.
