# Session Report: F1389 — Mode-II Nonlinear Failure Resolution, Mesh Topology Audit, and Fine-Mesh Spatial Convergence Synthesis

- **Task ID:** `F1389-MODE2-RESOLVE-NONLINEAR-FAILURE-AND-VERIFY-FINE-CONVERGENCE`
- **Agent:** `gemini-antigravity`
- **Date:** `2026-10-10T06:30:00+02:00`
- **Starting Commit:** `580f43bb`
- **Active Gate:** `GATE_M2_1B_FIXED_MESH_CONVERGENCE_STUDY_AUDITING_AND_SOLVING` / `MODE2_GATE_M2_4_ADAPTED_FRACTURE_SIMULATION_COMPLETED_PASSED_WITH_LIMITATIONS`

---

## 1. Executive Summary & Scientific Findings

Task F1389 performed a root-cause investigation into the post-peak nonlinear convergence failures (Exit 1) affecting fine and adapted discretizations in the Mode-II shear fracture benchmark (Pandey & Kumar, 2024; Miehe et al., 2010), resolved the mesh topology node-count discrepancy, audited the active 71,824-element fine-mesh companion solves, and formulated a single-parameter numerical diagnostic.

### Key Outcomes:

1. **Active Fine 72k Solver Telemetry (`1411545.mmaster02` and `1411557.mmaster02`):**
   - **Primary Fine Solve (`1411545.mmaster02`, $71{,}824$ FEs, $h=3.73\,\mu\text{m}$, 24h walltime):** Actively solving on `mnode097/4` at Increment 1831 ($u_x = 9.155\,\mu\text{m}$), with **0 cutbacks**, exactly 3 Newton iterations per increment, and reaction force $RF_1 = 405.72\,\text{N}$, approaching the peak regime.
   - **Safeguard Fine Solve (`1411557.mmaster02`, $71{,}824$ FEs, $h=3.73\,\mu\text{m}$, 72h walltime):** Actively solving on `mnode097/0` at Increment 1387 ($u_x = 6.935\,\mu\text{m}$), with **0 cutbacks**, exactly 3 Newton iterations per increment, and reaction force $RF_1 = 312.76\,\text{N}$.
   - **Bitwise Numerical Parity:** 100% bitwise parity verified across the complete common displacement range ($u_x \le 6.935\,\mu\text{m}$, $\max \Delta u_x = 0.00\,\text{mm}$, $\max \Delta RF_1 = 0.00\,\text{N}$).

2. **Root Cause Analysis of the Three Exit 1 Failures:**
   - Detailed inspection of `.msg` files for Intermediate 40k (`1411544.mmaster02` & `1411558.mmaster02`) and Adapted ET2 (`1411414.mmaster02`) reveals:
     * Failure is caused by **DOF 3 (Phase field $d$) local Newton divergence** at crack-tip nodes (e.g. Nodes 19597 and 19397 in 40k; Nodes 4681 and 7033 in ET2) during the steep post-peak localized damage transition ($d \to 1$).
     * The default Abaqus automatic incrementation cutback limit ($I_A = 5$) is exceeded after 5 consecutive cutbacks without line search.
     * The actual prescribed displacement increment is $\Delta u_x = 10.0\,\mu\text{m} \times 0.0005 = 0.005\,\mu\text{m} = 5.0\,\text{nm}$ per increment (confirming correct nanometer scaling).
     * Crucially, **all simulations traversed the initial elastic branch, crack initiation, and true peak reaction force before encountering localization cutbacks**.

3. **Resolution of the Mesh Node Count Discrepancy (40,481 vs. 40,501):**
   - The structured $200 \times 200$ grid has $(200+1) \times (200+1) = 40,401$ base grid nodes.
   - The initial sharp slit at $y = 0.5\,\text{mm}$ ($x \in [0.0, 0.5]\,\text{mm}$, $a_0 = 0.5\,\text{mm}$) has $0.5 / 0.005 = 100$ element intervals, which duplicates exactly 100 nodes along the lower crack flank (nodes 40402 to 40501).
   - Thus, the physical mesh has $40,401 + 100 = 40,501$ mesh nodes (+1 Reference Point node 999999 = 40,502 total user nodes).
   - The number "40,481" was a reporting typo ($40,401 + 80 = 40,481$ as if $a_0 = 0.4\,\text{mm}$), while the actual input decks for both 40k runs have always contained exactly 40,501 mesh nodes (SHA-256: `622C59A4D760CBEA9D2C810932C8B4B03153805CF8141FF1E4B3059D24878366`).

4. **Formulation and Cluster Datacheck of Single-Parameter Diagnostic (`M2_FIX_INT_40K_LS`):**
   - Prepared package `03_intermediate_40k_h5um_diagnostic_ls/` modifying only ONE justified numerical parameter: enabling Line Search (`*CONTROLS, PARAMETERS=LINE SEARCH / 4`) to prevent Newton overshoot along the non-monotonic damage landscape.
   - Preserved exact mesh, nodes, elements, material constants, phase-field parameters ($l_0 = 15\,\mu\text{m}, G_c = 2.7\,\text{N/mm}$), boundary conditions, and Fortran UEL SHA-256 (`699B05D6C430FCE6242F8C603B45BB0783CF376451EFD52C56BC984B0CE71188`).
   - Cluster Datacheck executed successfully: **DATACHECK_EXIT_CODE: 0** with zero errors.

5. **Epistemological Discipline & Spatial Convergence Corrections:**
   - Acknowledged substantial mesh sensitivity across the fixed-mesh sequence: $525.70\,\text{N} \,(2.5\text{k}) \to 436.99\,\text{N} \,(18\text{k}) \to 420.66\,\text{N} \,(40\text{k})$.
   - Corrected unsupported claims: the close agreement of ET3 ($412.21\,\text{N}$) and ET2 ($411.80\,\text{N}$) is an observed adaptive agreement, not a proven continuum limit. The fine fixed mesh is currently solving and has not yet established its peak.
   - Initial elastic stiffness is invariant across all 7 discretizations: $K_0 = 45.79 \pm 0.16\,\text{kN/mm}$ ($< 0.65\%$ spread).

6. **Unit Tests & Artifacts:**
   - Authored unit test suite `tests/unit/test_mode2_f1389_diagnostics_and_convergence_synthesis.py` (**7/7 PASS**, 100%).
   - Updated master publication figure `fig_mode2_fixed_mesh_spatial_convergence.pdf` and `.png`.

---

## 2. Cluster Job Status Table

| PBS Job ID | Discretization / Case | Elements | Active State | Reaction Force | Status |
| :--- | :--- | :---: | :---: | :---: | :---: |
| `1411545.mmaster02` | Fixed Fine 72k (24h) | $71{,}824$ | $u_x = 9.155\,\mu\text{m}$ (Inc 1831) | $405.72\,\text{N}$ | `RUNNING` (0 cutbacks) |
| `1411557.mmaster02` | Fixed Fine 72h (72h) | $71{,}824$ | $u_x = 6.935\,\mu\text{m}$ (Inc 1387) | $312.76\,\text{N}$ | `RUNNING` (0 cutbacks) |
| `1411544.mmaster02` | Fixed Int 40k (24h) | $40{,}000$ | $u_x = 9.635\,\mu\text{m}$ (Inc 1928) | $412.78\,\text{N}$ | `TERMINAL_EVALUATED` ($F_{\max}=420.66\,\text{N}$) |
| `1411558.mmaster02` | Fixed Int 48h (48h) | $40{,}000$ | $u_x = 9.635\,\mu\text{m}$ (Inc 1928) | $412.78\,\text{N}$ | `TERMINAL_EVALUATED` ($F_{\max}=420.66\,\text{N}$) |
| `1411543.mmaster02` | Fixed Med 18k | $17{,}956$ | $u_x = 20.00\,\mu\text{m}$ (Inc 4000) | $408.41\,\text{N}$ | `COMPLETED` ($F_{\max}=436.99\,\text{N}$) |
| `1411542.mmaster02` | Fixed Coarse 2.5k | $2{,}500$ | $u_x = 20.00\,\mu\text{m}$ (Inc 4000) | $489.25\,\text{N}$ | `COMPLETED` ($F_{\max}=525.70\,\text{N}$) |
| `1411414.mmaster02` | Adapted ET2 | $37{,}575$ | $u_x = 9.415\,\mu\text{m}$ (Inc 1884) | $403.56\,\text{N}$ | `TERMINAL_EVALUATED` ($F_{\max}=411.80\,\text{N}$) |
| `1411267.mmaster02` | Adapted ET3 | $21{,}063$ | $u_x = 20.00\,\mu\text{m}$ (Inc 4024) | $380.42\,\text{N}$ | `COMPLETED` ($F_{\max}=412.21\,\text{N}$) |

---

## 3. Mode-I Baseline Freeze Integrity

The Mode-I baseline remains 100% frozen and untouched:
- Git Tag: `v2026.10.08-supervisor-meeting-mode1-freeze`
- UEL SHA-256: `CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6`
