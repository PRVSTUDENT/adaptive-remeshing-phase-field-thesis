# Pre-Job Anti-Deviation Card: PK_MODE1_T2_NOMINAL_ENERGY

- **Candidate ID**: T2 (1x_nominal)
- **Model Package**: `models/pandey_kumar_mode1/18_temporal_convergence_t2_nominal/`
- **Scientific Role**: Mode-I Gate-6B Temporal Discretization Convergence Evaluation Candidate
- **Status**: `DATACHECK_PASSED_REUSED_AS_CORRECTED_S1_REFERENCE` (Omitted from Cluster Solver Submissions)
- **Authorization**: `authorized: false` (Omitted from cluster solver submissions; S1 reference solve Job 1409734 provides nominal anchor)
- **Governing Classification**: `T2_NOMINAL = REUSE_CORRECTED_S1_REFERENCE`
- **Action**: `OMIT_FROM_CLUSTER_SUBMISSIONS_REUSE_S1`

---

## 1. Equivalence Audit & Solver Omission Rationale
- **Equivalence Findings**:
  A comprehensive semantic, geometric, constitutive, solver-control, and output audit was performed comparing `PK_MODE1_T2_NOMINAL_ENERGY.inp` against corrected reference deck `PK_MODE1_REF15K_ENERGY.inp`:
  - **Scientific/Model Differences**: Strictly 0.
    - Geometry: 100% identical ($1.0 \times 1.0\,\text{mm}$ square with $0.5\,\text{mm}$ sharp slit at $y=0.5\,\text{mm}$).
    - Discretization: 100% identical 15,192 physical elements and 15,521 nodes.
    - Material & Phase-Field Properties: 100% identical ($E = 210.0\,\text{kN/mm}^2$, $\nu = 0.3$, $G_c = 0.0027\,\text{kN/mm}$, $l_0 = 0.0075\,\text{mm}$, $k = 1.0 \times 10^{-7}$, $N_{\text{phys}} = 15192.0$).
    - Boundary Conditions: 100% identical (`N_BOTTOM` $u_y=0$, `N_PIN` $u_x=0$, `N_TOP` $u_x=0$, RP 999999 $u_y$ kinematic coupling).
  - **Solver-Control Differences**: Strictly 0.
    - Step 1: Initial $dt = 5.0 \times 10^{-4}\,\text{s}$, period $1.0\,\text{s}$, $dt_{\min} = 1.0 \times 10^{-9}\,\text{s}$, $dt_{\max} = 5.0 \times 10^{-4}\,\text{s}$, 2,500 max incs (2,000 nominal).
    - Step 2: Initial $dt = 2.0 \times 10^{-4}\,\text{s}$, period $1.0\,\text{s}$, $dt_{\min} = 1.0 \times 10^{-9}\,\text{s}$, $dt_{\max} = 2.0 \times 10^{-4}\,\text{s}$, 6,000 max incs (5,000 nominal).
    - Solver: Direct sparse solver, `nlgeom=NO`.
  - **Output/Instrumentation Differences**: Strictly 0.
    - `*Depvar 20`, `*Element Output, elset=All_elem` (`SDV17-20`), `*Node Output, nset=N_RP` (`U, RF`), `*Node Print, freq=1, nset=N_RP` (`U2, RF2`).
    - User Subroutine: Production `f42_mixed_uel.for` (`CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6`) with working-directory CSV tracking via `CALL GETOUTDIR`.
  - **Non-Scientific Metadata Differences**: Deck comments, line-wrapping of node sets, and package directory naming.
- **HPC Efficiency Conclusion**:
  Executing an independent solver job on the cluster would strictly duplicate the authoritative corrected S1 reference run (`PK_M1_REF15K_ENERGY`, Job `1409734.mmaster02`), consuming 24–48 hours of CPU time with zero information gain.
  Therefore, T2 is formally classified as `T2_NOMINAL = REUSE_CORRECTED_S1_REFERENCE` and omitted from future cluster solver submissions.
  The future temporal execution set consists strictly of:
  - $T_1$ Coarse Time (2x nominal dt, 3,500 incs, package `17_temporal_convergence_t1_coarse/`)
  - $T_3$ Fine Time (0.5x nominal dt, 14,000 incs, package `19_temporal_convergence_t3_fine/`)

---

## 2. Frozen Scientific & Numerical Quantities
- **Mesh Topology**:
  - Total Physical Elements: `15,192` (Layer 1: Phase UEL 1..15192, Layer 2: Mech UEL 15193..30384, Layer 3: Companion CPE4 30385..45576)
  - Total Nodes: `15,521` (15,522 including RP 999999)
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
- **Input Deck**: `PK_MODE1_T2_NOMINAL_ENERGY.inp`
  - SHA-256: `4A0302C60FB47D59FF024BCD40EBADC4B2F036FE155F1C632F6D8874665CD6F1`
- **User Subroutine**: `f42_mixed_uel.for`
  - SHA-256: `CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6`
- **Dual-Channel Notification**: `job_notifications.sh`
  - SHA-256: `96756A681D2D36C11B36B89288F631F8ECC9537543C2C745A4BAE1B425984B47`
- **Datacheck PBS**: `submit_datacheck.pbs` (Datacheck passed on cluster with Exit 0)
- **Solver PBS**: `submit_solver.pbs` (Omitted from submission)

---

## 4. Matched-Displacement Comparison Targets
- **Nominal Trajectory Anchor**: Reused directly from Corrected S1 Reference (`PK_M1_REF15K_ENERGY`, Job `1409734.mmaster02`).
- **Evaluation Pipeline**: `scripts/validation/temporal_convergence_pipeline.py` enforcing strict matched-displacement interpolation with ZERO extrapolation.
- **Audited Metrics**:
  - Initial structural stiffness K0 (kN/mm) and R^2 linearity
  - Peak reaction force F_max (kN) and peak displacement u(F_max) (mm)
  - Energy trajectories E_elas(u), E_frac(u), E_model(u), W_ext(u)
  - Global energy conservation bookkeeping residual Delta_book(u)
  - Successive relative differences delta_n(phi) under TREND_ONLY governance
