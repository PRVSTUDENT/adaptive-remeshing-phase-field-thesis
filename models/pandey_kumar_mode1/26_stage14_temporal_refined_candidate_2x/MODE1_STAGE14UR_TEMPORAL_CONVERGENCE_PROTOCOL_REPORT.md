# Gate-6B Mode-I Stage 14U-R/S: Temporal-Convergence Discretization Protocol and Candidate Preflight Report

**Protocol Version:** 2  
**Task ID:** `F1202-GATE6B-STAGE14US-TEMPORAL-PROTOCOL-CORRECTION-AND-SOURCE-IDENTITY-AUDIT-20261004`  
**Phase:** `MODE1_GATE6B_ACTIVE_EVALUATION_AND_CONTINUATION`  
**Date:** 2026-10-04  
**Author:** Gemini Antigravity  
**Governing Verdict:** `TEMPORAL_CONVERGENCE_CANDIDATE_VALIDATED__SOURCE_AND_PROTOCOL_CORRECTED__BASELINE_TERMINAL_PENDING`  
**Execution Boundary:** Solver Job `1409982.mmaster02` (`PK_M1_ADAPT_14K_FRACTURE`) left running untouched on compute node `mnode097`; candidate execution strictly withheld pending terminal baseline qualification.

---

## 1. Executive Summary & Core Scientific Question

During Gate-6B Stage 14U, the full fracture completion rerun (`Job 1409982.mmaster02`, Package 25) was submitted with enhanced Step-2 solver controls (`*CONTROLS, PARAMETERS=TIME INCREMENTATION: 4, 10, 9, 20, 10, 4, 0, 10`) to eliminate premature Newton cutback exhaustion at $u = 0.007889\,\text{mm}$ and advance through complete unloading to $u = 0.0100\,\text{mm}$.

While this authoritative baseline completion job advances on `mnode097`, the next mandatory scientific question in the Mode-I qualification hierarchy must be addressed:

> **Core Scientific Question:** *"Does refinement of the prescribed displacement/time-increment discretization materially alter the mechanical, spatial, or energetic response of the qualified 14,483-element adaptive mesh?"*

To establish temporal convergence without interfering with the running baseline solve, Stage 14U-R/S executes an offline protocol freeze and cluster preflight qualification for a **$2\times$ temporally refined candidate** (Package 26: `models/pandey_kumar_mode1/26_stage14_temporal_refined_candidate_2x/`), while strictly withholding PBS solver submission until the baseline job reaches its terminal endpoint and is evaluated.

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

## 3. Strict Controlled Invariances & Production-Source Identity Audit

To isolate pure temporal discretization sensitivity, all spatial, physical, material, and numerical options are locked and verified:

1. **Subroutine Source Identity Audit:**
   - Authoritative Stage-14 production subroutine: `f42_mixed_uel.for` with SHA-256 `CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6` (29,722 bytes, 908 lines, LF line endings).
   - Package 25 local and cluster copy: `CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6`.
   - Package 26 local and cluster copy: `CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6` (exact byte-level match).
   - Lineage Clarification: The historical hash `5CD0D2C0...` corresponds to an earlier Gate-6B build (29,401 bytes, 902 lines) that wrote `uel_energy_balance.csv` to default relative paths. In Stage 14, this was upgraded with `CALL GETOUTDIR(OUTDIR_STR, L_OUTDIR)` to safely route energy telemetry files when executed under HPC scratch directories. Package 26 strictly uses the governed Stage-14 production source.
2. **Spatial Mesh Topology:**
   - Exact node coordinates: 14,456 nodes.
   - Underlying finite elements: 14,483 elements (14,082 quads + 401 triangles).
   - 3-Layer dual-UEL/UMAT structure: 43,449 layered finite elements.
   - Zero-gap crack seam: 54 duplicated node pairs (109 seam nodes, $a_0 = 0.50\,\text{mm}$).
   - Specimen area: $\Omega = 1.00000000\,\text{mm}^2$.
3. **Material Constants & UEL Property ABI:**
   - Elasticity: $E = 210.0\,\text{kN/mm}^2$ ($210\,\text{GPa}$), $\nu = 0.3$.
   - Fracture properties: $G_c = 0.0027\,\text{kN/mm}$ ($2.7\,\text{kJ/m}^2$), $l_0 = 0.0075\,\text{mm}$ ($7.5\,\mu\text{m}$).
   - Numerical regularization: $k = 1.0 \times 10^{-7}$.
   - PROPS card ABI order: `(l0, Gc, E, nu, k, N_elem)` $\to$ `(0.0075, 0.0027, 210.0, 0.3, 1.0e-7, 14483.0)`.
4. **Boundary Conditions & Outputs:**
   - Bottom roller ($y=0$): $u_y = 0$, pinned corner ($x=0, y=0$): $u_x = 0$.
   - Top roller ($y=1$): $u_x = 0$, Reference Point 999999 displacement coupling.
   - Prescribed loading: Step 1 $u_{\text{RP}} = 0.0050\,\text{mm}$, Step 2 $u_{\text{RP}} = 0.0100\,\text{mm}$.
   - Field output frequency: 1 increment.

---

## 4. Pre-Declared Comparison Protocol & Multi-Quantity Metrics

When the $2\times$ refined candidate is executed following baseline completion, it will be evaluated against the baseline using the following pre-declared metrics and descriptive physical classifications:

1. **Continuous Reaction Force Discrepancy ($F-u$):**
   - Interpolated onto common displacement grid; continuous $L_2$ and $L_\infty$ norms evaluated across pre-peak and post-peak deformation regimes.
2. **Canonical Initial Structural Stiffness ($K_0$):**
   - Evaluated over the canonical initial elastic window $u \le 0.0010\,\text{mm}$ by **sampling / interpolating the refined force-displacement response onto the standard 400-point displacement grid** ($\Delta u = 2.50\times 10^{-6}\,\text{mm}, 0.5\Delta u < u \le 0.0010 + 0.5\Delta u, N=400$).
   - Ensures identical sample size ($N=400$), identical regression window ($u \le 1.0\,\mu\text{m}$), and identical statistical degrees of freedom.
   - Evaluated using certified OLS linear regression; self-test anchor reproduction preserved ($K_{0,\text{ref}} = 137.945520\,\text{kN/mm}$, intercept $4.472368\times 10^{-5}\,\text{kN}$, $R^2 = 0.99999960$).
3. **Peak Load ($F_{\max}$) and Peak Displacement ($u_{\text{peak}}$):**
   - Maximum reaction force and corresponding prescribed displacement evaluated from full trajectory data.
4. **Pointwise Force at 10 Matched Displacement States:**
   - Evaluated at $u \in \{0.0010, 0.0030, 0.0050, 0.005857, 0.0060, 0.0065, 0.0070, 0.0080, 0.0090, 0.0100\}\,\text{mm}$.
5. **Continuous Spatial Phase-Field Ligament Profiles ($d(x, y=0.5\,\text{mm})$):**
   - Evaluated on uniform 1001-point grid ($x \in [0.50, 1.00]\,\text{mm}$, $\Delta x = 0.5\,\mu\text{m}$).
   - Relative $L_2$ error and localized peak discrepancy $L_\infty$ evaluated across dissimilar meshes.
6. **Macro-Crack Tip Coordinate ($x_{\text{tip}}$):**
   - Identified using governed threshold $d \ge 0.90$.
7. **Energetic Balance Integrals:**
   - External work $W_{\text{ext}}$, elastic strain energy $E_{\text{elas}}$, crack-surface functional $E_{\text{frac}}$, residual $\Delta_{\text{book}}$, and relative error $\varepsilon_{\text{book}}$.
8. **Solver Telemetry & Cost:**
   - Total increments, total iterations, cutback attempts, CPU time, and walltime recorded for cost scaling.
9. **Descriptive Classification Scheme:**
   - In adherence to scientific reporting discipline, newly invented arbitrary percentage pass thresholds are rejected.
   - Quantities are classified from complete physical evidence into governed categories:
     - `STABLE`: Variations within numerical discretization truncation and roundoff precision.
     - `TEMPORALLY_SENSITIVE`: Meaningful physical sensitivity to temporal incrementation.
     - `NOT_YET_QUALIFIED`: Incomplete or pending evaluation.

---

## 5. Preflight Verification Results

The Package 26 candidate has undergone comprehensive preflight verification:

1. **Deck Diff Invariance:**
   - Programmatic comparison between `PK_MODE1_STAGE14_ADAPT_14K_FRACTURE.inp` (Pkg 25) and `PK_MODE1_STAGE14_ADAPT_14K_TEMPORAL_2X.inp` (Pkg 26) confirms **exactly 4 lines differ**, strictly restricted to `*STEP, ... INC=` and `*STATIC` time increments.
2. **Subroutine Source Identity:**
   - Bitwise identity between Package 25 and Package 26 Fortran source confirmed (SHA-256 `CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6`).
3. **Unit Test Suite (`test_stage14ur_temporal_convergence_preflight.py`):**
   - 7/7 unit tests passed ($100\%$).
   - Full Stage-14 unit test suite: 23/23 tests passed ($100\%$).
4. **Cluster Abaqus Datacheck (`PK_M1_14K_TEMPORAL_2X_DATACHECK.inp`):**
   - Subroutine compilation (`ifort` 2021.13.0): **PASS**
   - Subroutine linking (`GNU ld`): **PASS**
   - Abaqus/Standard input file processor & pre-check: **PASS**
   - Execution Exit Code: **`0`** (0 errors, 16 standard informational warnings, CPU time 0.84 s).

---

## 6. Package Manifest & Cryptographic Hashes

The sealed Package 26 files and SHA-256 hashes are recorded below:

| File Name | SHA-256 Checksum | Description |
| :--- | :--- | :--- |
| `PK_MODE1_STAGE14_ADAPT_14K_TEMPORAL_2X.inp` | `9AC284E6A65E59042E9588DB628F9B15D5CBE345D62D164B477304D4813BC526` | $2\times$ Temporally Refined Full Fracture Deck |
| `PK_M1_14K_TEMPORAL_2X_DATACHECK.inp` | `D4A99C3A40E35419F7088F3EF517CE237DE6942543363DA545BA26C7BE2361D7` | Preflight Verification Datacheck Deck |
| `f42_mixed_uel.for` | `CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6` | Governed Mixed UEL Fortran Subroutine |
| `job_notifications.sh` | `96756A681D2D36C11B36B89288F631F8ECC9537543C2C745A4BAE1B425984B47` | Dual-Channel Notification Library |
| `submit_datacheck.pbs` | `4F399D9293F14730D968CEB05BEBFED17ACF5D8F2F9DB7CB88603EC2E813A384` | PBS Datacheck Execution Script |
| `submit_solver.pbs` | `172FB6905BBBBFF1EADA15E5C4EA0936D854B39F8F125E8108808419E25B73AC` | PBS Solver Execution Script (Withheld) |
| `PACKAGE_MANIFEST.json` | Recorded in Package Directory | Sealed Package Manifest |

---

## 7. Governance Conclusion & Next Actions

1. **Preparatory Verdict Assigned:**
   `TEMPORAL_CONVERGENCE_CANDIDATE_VALIDATED__SOURCE_AND_PROTOCOL_CORRECTED__BASELINE_TERMINAL_PENDING`
2. **Solver State:**
   Job `1409982.mmaster02` (`PK_M1_ADAPT_14K_FRACTURE`) is advancing normally in the pre-failure regime on `mnode097` with zero cutbacks and 3 iterations per increment.
3. **Execution Gate:**
   Zero new solver submissions are performed. Submission of Package 26 solver script is strictly contingent upon terminal qualification and scientific review of baseline Job 1409982.
