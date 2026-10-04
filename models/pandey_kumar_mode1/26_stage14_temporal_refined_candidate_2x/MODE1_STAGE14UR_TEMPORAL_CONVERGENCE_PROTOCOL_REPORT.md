# Gate-6B Mode-I Stage 14U-R: Temporal-Convergence Discretization Protocol and Candidate Preflight Report

**Protocol Version:** 2  
**Task ID:** `F1201-GATE6B-STAGE14UR-TEMPORAL-CONVERGENCE-PROTOCOL-AND-PREFLIGHT-20261004`  
**Phase:** `MODE1_GATE6B_ACTIVE_EVALUATION_AND_CONTINUATION`  
**Date:** 2026-10-04  
**Author:** Gemini Antigravity  
**Governing Verdict:** `TEMPORAL_CONVERGENCE_CANDIDATE_VALIDATED__BASELINE_TERMINAL_QUALIFICATION_PENDING`  
**Execution Boundary:** Solver Job `1409982.mmaster02` (`PK_M1_ADAPT_14K_FRACTURE`) left running untouched on compute node `mnode097`; candidate execution strictly withheld pending terminal baseline qualification.

---

## 1. Executive Summary & Core Scientific Question

During Gate-6B Stage 14U, the full fracture completion rerun (`Job 1409982.mmaster02`, Package 25) was submitted with enhanced Step-2 solver controls (`*CONTROLS, PARAMETERS=TIME INCREMENTATION: 4, 10, 9, 20, 10, 4, 0, 10`) to eliminate premature Newton cutback exhaustion at $u = 0.007889\,\text{mm}$ and advance through complete unloading to $u = 0.0100\,\text{mm}$.

While this authoritative baseline completion job advances on `mnode097`, the next mandatory scientific question in the Mode-I qualification hierarchy must be addressed:

> **Core Scientific Question:** *"Does refinement of the prescribed displacement/time-increment discretization materially alter the mechanical, spatial, or energetic response of the qualified 14,483-element adaptive mesh?"*

To establish temporal convergence without interfering with the running baseline solve, Stage 14U-R executes an offline protocol freeze and cluster preflight qualification for a **$2\times$ temporally refined candidate** (Package 26: `models/pandey_kumar_mode1/26_stage14_temporal_refined_candidate_2x/`), while strictly withholding PBS solver submission until the baseline job reaches its terminal endpoint and is evaluated.

---

## 2. Temporal Discretization Parameterization

The baseline temporal discretization (Package 25) and the refined candidate (Package 26) are compared below:

| Discretization Parameter | Baseline Discretization (Package 25 / Job 1409982) | Refined Candidate ($2\times$ Temporal, Package 26) | Refinement Ratio |
| :--- | :--- | :--- | :---: |
| **Step 1 Displacement Window** | $u = 0.0000 \to 0.0050\,\text{mm}$ ($5.0\,\mu\text{m}$) | $u = 0.0000 \to 0.0050\,\text{mm}$ ($5.0\,\mu\text{m}$) | $1.0\times$ (Frozen) |
| **Step 1 Initial / Max $\Delta t_1$** | $5.0 \times 10^{-4}$ | $2.5 \times 10^{-4}$ | $\mathbf{2.0\times\ \text{Finer}}$ |
| **Step 1 Nominal $\Delta u_1$** | $2.50 \times 10^{-6}\,\text{mm} = 2.50\,\text{nm}$ | $1.25 \times 10^{-6}\,\text{mm} = 1.25\,\text{nm}$ | $\mathbf{2.0\times\ \text{Finer}}$ |
| **Step 1 Nominal Increment Count** | 2,000 increments | 4,000 increments | $2.0\times$ |
| **Step 1 Max Allowed Incs (`INC`)** | 2,500 increments | 5,000 increments | $2.0\times$ |
| **Step 2 Displacement Window** | $u = 0.0050 \to 0.0100\,\text{mm}$ ($5.0\,\mu\text{m}$) | $u = 0.0050 \to 0.0100\,\text{mm}$ ($5.0\,\mu\text{m}$) | $1.0\times$ (Frozen) |
| **Step 2 Initial / Max $\Delta t_2$** | $2.0 \times 10^{-4}$ | $1.0 \times 10^{-4}$ | $\mathbf{2.0\times\ \text{Finer}}$ |
| **Step 2 Nominal $\Delta u_2$** | $1.00 \times 10^{-6}\,\text{mm} = 1.00\,\text{nm}$ | $0.50 \times 10^{-6}\,\text{mm} = 0.50\,\text{nm}$ | $\mathbf{2.0\times\ \text{Finer}}$ |
| **Step 2 Nominal Increment Count** | 5,000 increments | 10,000 increments | $2.0\times$ |
| **Step 2 Max Allowed Incs (`INC`)** | 6,000 increments | 12,000 increments | $2.0\times$ |
| **Step 2 Time Controls** | `4, 10, 9, 20, 10, 4, 0, 10` ($I_A=10, I_C=20$) | `4, 10, 9, 20, 10, 4, 0, 10` ($I_A=10, I_C=20$) | $1.0\times$ (Frozen) |
| **Total Nominal Increments** | 7,000 increments | 14,000 increments | $2.0\times$ |

---

## 3. Strict Controlled Invariances

To isolate pure temporal discretization sensitivity, all spatial, physical, material, and numerical options are locked and verified:

1. **Spatial Mesh Topology:**
   - Exact node coordinates: 14,456 nodes.
   - Underlying finite elements: 14,483 elements (14,082 quads + 401 triangles).
   - 3-Layer dual-UEL/UMAT structure: 43,449 layered finite elements.
   - Zero-gap crack seam: 54 duplicated node pairs (109 seam nodes, $a_0 = 0.50\,\text{mm}$).
   - Specimen area: $\Omega = 1.00000000\,\text{mm}^2$.
2. **Material Constants & UEL Property ABI:**
   - Elasticity: $E = 210.0\,\text{kN/mm}^2$ ($210\,\text{GPa}$), $\nu = 0.3$.
   - Fracture properties: $G_c = 0.0027\,\text{kN/mm}$ ($2.7\,\text{kJ/m}^2$), $l_0 = 0.0075\,\text{mm}$ ($7.5\,\mu\text{m}$).
   - Numerical regularization: $k = 1.0 \times 10^{-7}$.
   - PROPS card ABI order: `(l0, Gc, E, nu, k, N_elem)` $\to$ `(0.0075, 0.0027, 210.0, 0.3, 1.0e-7, 14483.0)`.
3. **Boundary Conditions & Outputs:**
   - Bottom roller ($y=0$): $u_y = 0$, pinned corner ($x=0, y=0$): $u_x = 0$.
   - Top roller ($y=1$): $u_x = 0$, Reference Point 999999 displacement coupling.
   - Prescribed loading: Step 1 $u_{\text{RP}} = 0.0050\,\text{mm}$, Step 2 $u_{\text{RP}} = 0.0100\,\text{mm}$.
   - Field output frequency: 1 increment.

---

## 4. Pre-Declared Comparison Protocol & Multi-Quantity Metrics

When the $2\times$ refined candidate is executed following baseline completion, it will be evaluated against the baseline using the following pre-declared metrics:

1. **Continuous Reaction Force Discrepancy ($F-u$):**
   - Interpolated onto common displacement grid; continuous $L_2$ and $L_\infty$ norms evaluated.
   - Pre-peak and post-peak segments evaluated independently.
2. **Initial Structural Stiffness ($K_0$):**
   - Evaluated over canonical initial elastic window $u \le 0.0010\,\text{mm}$ ($N=800$ regression points for $2\times$ candidate).
   - Classified `STABLE` if $|\Delta K_0| \le 1.0\%$, else `TEMPORALLY_SENSITIVE`.
3. **Peak Load ($F_{\max}$) and Peak Displacement ($u_{\text{peak}}$):**
   - Maximum reaction force and corresponding displacement.
   - Classified `STABLE` if $|\Delta F_{\max}| \le 3.0\%$ and $|\Delta u_{\text{peak}}| \le 3.0\%$.
4. **Pointwise Force at 10 Matched Displacement States:**
   - Evaluated at $u \in \{0.0010, 0.0030, 0.0050, 0.005857, 0.0060, 0.0065, 0.0070, 0.0080, 0.0090, 0.0100\}\,\text{mm}$.
5. **Continuous Spatial Phase-Field Ligament Profiles ($d(x, y=0.5\,\text{mm})$):**
   - Evaluated on uniform 1001-point grid ($x \in [0.50, 1.00]\,\text{mm}$, $\Delta x = 0.5\,\mu\text{m}$).
   - Relative $L_2$ error and localized peak discrepancy $L_\infty$ evaluated.
6. **Macro-Crack Tip Coordinate ($x_{\text{tip}}$):**
   - Identified using governed threshold $d \ge 0.90$.
7. **Energetic Balance Integrals:**
   - External work $W_{\text{ext}}$, elastic strain energy $E_{\text{elas}}$, crack-surface functional $E_{\text{frac}}$, residual $\Delta_{\text{book}}$, and relative error $\varepsilon_{\text{book}}$.
8. **Solver Telemetry & Cost:**
   - Total increments, total iterations, cutback attempts, CPU time, and walltime.

---

## 5. Preflight Verification Results

The Package 26 candidate has undergone comprehensive preflight verification:

1. **Deck Diff Invariance:**
   - Programmatic comparison between `PK_MODE1_STAGE14_ADAPT_14K_FRACTURE.inp` (Pkg 25) and `PK_MODE1_STAGE14_ADAPT_14K_TEMPORAL_2X.inp` (Pkg 26) confirms **exactly 4 lines differ**, strictly restricted to `*STEP, ... INC=` and `*STATIC` time increments.
2. **Unit Test Suite (`test_stage14ur_temporal_convergence_preflight.py`):**
   - 7/7 unit tests passed ($100\%$).
   - Full Stage-14 unit test suite: 23/23 tests passed ($100\%$).
3. **Cluster Abaqus Datacheck (`PK_M1_14K_TEMPORAL_2X_DATACHECK.inp`):**
   - Subroutine compilation (`ifort` 2021.13.0): **PASS**
   - Subroutine linking (`GNU ld`): **PASS**
   - Abaqus/Standard input file processor & pre-check: **PASS**
   - Execution Exit Code: **`0`** (0 errors, 16 standard informational warnings).

---

## 6. Package Manifest & Cryptographic Hashes

The sealed Package 26 files and SHA-256 hashes are recorded below:

| File Name | SHA-256 Checksum | Description |
| :--- | :--- | :--- |
| `PK_MODE1_STAGE14_ADAPT_14K_TEMPORAL_2X.inp` | `9AC284E6A65E59042E9588DB628F9B15D5CBE345D62D164B477304D4813BC526` | $2\times$ Temporally Refined Full Fracture Deck |
| `PK_M1_14K_TEMPORAL_2X_DATACHECK.inp` | `D4A99C3A40E35419F7088F3EF517CE237DE6942543363DA545BA26C7BE2361D7` | Preflight Verification Datacheck Deck |
| `f42_mixed_uel.for` | `5CD0D2C015C9EAD91C99D7A744156CC86F5B5EA26473BBED7D6E5515FE30FA46` | Governed Mixed UEL Fortran Subroutine |
| `job_notifications.sh` | `E5D77B8FB6AE7BDCF2C8A84AC50DA138B42416CA90CEE1BBE30BA9509C2AE74E` | Dual-Channel Notification Library |
| `submit_datacheck.pbs` | `A8DE6DA1F89ED60B5B9E7804BE96366CA0BF48E66FB24B70CEBF88ACF0E700BE` | PBS Datacheck Execution Script |
| `submit_solver.pbs` | `FBE770D6C1AE872BCF64736DFEE5A834166299CDE13A7FE0F4BD9DB7BA8A9DBE` | PBS Solver Execution Script (Withheld) |
| `PACKAGE_MANIFEST.json` | `1D33FEFF816B27481C11EA88210E3BC78887ADE6789DE02B1976E0C965970167` | Sealed Package Manifest |

---

## 7. Governance Conclusion & Next Actions

1. **Preparatory Verdict Assigned:**
   `TEMPORAL_CONVERGENCE_CANDIDATE_VALIDATED__BASELINE_TERMINAL_QUALIFICATION_PENDING`
2. **Solver State:**
   Job `1409982.mmaster02` (`PK_M1_ADAPT_14K_FRACTURE`) is advancing normally in the pre-failure regime on `mnode097` with zero cutbacks and 3 iterations per increment.
3. **Execution Gate:**
   Zero new solver submissions are performed. Submission of Package 26 solver script is strictly contingent upon terminal qualification and scientific review of baseline Job 1409982.
