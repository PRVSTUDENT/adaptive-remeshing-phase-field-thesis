# Pre-Job Anti-Deviation Card: Package 48 (Mode-I Native Adapted Corrected Units Solve)

- **Job Name:** `PK_M1_NATIVE_ADAPTED_CORR`
- **Batch Name:** `MODE1_NATIVE_ADAPTED_CORR`
- **Scientific Objective:** Full-scale Mode-I phase-field fracture simulation on 12,369-element native MISESERI adapted mesh with Young's modulus E = 210.0 kN/mm^2 (correcting the 1000x unit mismatch from Package 47).
- **Physical Mesh:** 12,369 elements (12,033 quads, 336 tris), 12,410 nodes.
- **Layer Architecture:** 3-layer co-located dual UEL + companion UMAT (37,107 total elements).
- **Crack-Tip Resolution:** Near-tip element size h = 1.72 um = 0.23 l0 (> 4 elements across l0).
- **Seam Nodes:** 67 duplicate node pairs along sharp slit y=0.5 mm, x in [0.0, 0.5] mm; shared crack tip node 135 at (0.5, 0.5).
- **Boundary Sets:** N_BOTTOM (150 nodes) wrapped at 12 entries/card (<= 16 keyword limit).
- **User Subroutine:** f42_mixed_uel.for (CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6, 100% BITWISE FROZEN).
- **HPC Resources:** 1 CPU, 16 GB RAM, 08:00:00 walltime, routing queue `entry_imfdfkmq` -> `normal_imfdfkmq`.
- **Predecessor Review:** Package 47 (Job 1415099) converged cleanly across 2,510 increments; initial stiffness K0 = 138.04 kN/mm (+0.054% from reference); peak force was 24.08 N due to E = 210,000 MPa; Package 48 corrects E to 210.0 kN/mm^2 to restore physical peak force ~ 0.75 kN.
