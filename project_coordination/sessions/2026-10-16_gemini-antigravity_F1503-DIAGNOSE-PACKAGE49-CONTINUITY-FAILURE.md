# Session Report: F1503 Package 49 Numerical Continuity Failure Diagnosis & Resolution

**Agent:** Gemini Antigravity (Protocol v2)  
**Task ID:** `F1503-DIAGNOSE-PACKAGE49-CONTINUITY-FAILURE`  
**Date:** 16 October 2026  
**Starting Commit:** `b10fdc4cd520bf786563678f344ca16bdee0283a`  
**Governing Status:** `STAGE_C1_1_EQUIL_NUMERICALLY_COMPLETED_SCIENTIFIC_CONTINUITY_FAILED`  
**Authoritative Fortran UEL:** `models/pandey_kumar_mode1/49_method_c_stage_c1_1_nonmatching_transfer/f42_mixed_uel.for` (`CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6`)  
**Evaluated Predecessor Job:** `1414235.mmaster02` (`M1_MC_STAGE_C1_1_EQUIL`, Exit 0 in 18s)  
**Authentic Donor Benchmark:** `1413814.mmaster02` (`M1_MB_DONOR`, 2,906 FEs, $u = 0.005000\,\text{mm}$)

---

## 1. Executive Summary & HPC Cluster Status
1. **Cluster Status Verified:**
   - Active user jobs on `normal_imfdfkmq` for user `pr21vyci`: **0 active jobs** (queue clean and idle).
   - Predecessor job `1414235.mmaster02` completed with Exit 0 in 18 seconds (1 increment, 2 equilibrium iterations, 0 cutbacks).
   - Scientific qualification review: **FAIL** (`STAGE_C1_1_EQUIL_REVIEW.json`).
   - Dependent forward continuation job `M1_MC_STAGE_C1_1` remains strictly blocked and unsubmitted.
2. **Core Diagnostic Outcome:**
   - Isolated and demonstrated the mathematical and implementation causes of the 5.631 N reaction force difference, the 0.817% total internal energy discrepancy, and the all-zero state variable outputs in Job 1414235.
   - Identified the smallest justified corrective actions in `scripts/state_transfer/mode1_state_transfer_engine.py` without modifying the frozen production UEL.
   - Verified the entire diagnostic battery with 6/6 unit tests passing cleanly in `tests/unit/test_mode1_f1503_diagnose_package49_continuity_failure.py`.

---

## 2. Investigation Across the Five Prioritized Questions

### Priority 1: Actual Transferred-State Initialization
- **Finding:** Commercial Abaqus/Standard static procedures reject `*INITIAL CONDITIONS, TYPE=DISPLACEMENT` (Error 144). Consequently, all 14,456 mesh nodes in Job 1414235 started from zero displacement ($\mathbf{u} = \mathbf{0}$) and zero phase field ($d = 0$).
- **State Ingestion in UEL:** `*INITIAL CONDITIONS, TYPE=SOLUTION` populated SVARS 1..18 for elements 1..14483 (Phase UEL). In `f42_mixed_uel.for` (lines 248–261), `SV_H_COMMITTED` was ingested from SVARS(8+KPT) for quads and SVARS(6+KPT) for tris. However, `SV_PHASE_COMMITTED` was initialized to 0.0 at `LOP=0` (lines 91–92) and never ingested from SVARS.
- **Companion Material UMAT Constant Defect:** In `M1_MC_STAGE_C1_1_EQUIL.inp`, `*USER MATERIAL, CONSTANTS=1` was emitted with value `1.0e-11`. In `f42_mixed_uel.for` (lines 867–874):
  ```fortran
  IF (NPROPS .GE. 3 .AND. PROPS(3) .GT. 0.D0) THEN
    NPHYS_VAL = INT(PROPS(3))
  ELSE
    NPHYS_VAL = 71320
  ENDIF
  PHYSIDX = NOEL - 2 * NPHYS_VAL
  IF (PHYSIDX .LE. 0) PHYSIDX = NOEL
  ```
  Because `NPROPS = 1 < 3`, `NPHYS_VAL` defaulted to 71,320. For companion elements `NOEL = 28967..43449`, `PHYSIDX = NOEL - 142640 < 0` clamped to `NOEL = 28967..43449`. Because the physical mesh has only 14,483 elements, array indices 28967..43449 in `SV_PHASE_TRIAL` and `SV_H_TRIAL` were zero. This explains 100% of the all-zero SDV values (SDV1, SDV2, SDV14, SDV17, SDV18) extracted from the ODB.
- **Node Output Restriction:** `*NODE OUTPUT, NSET=N_RP` restricted displacement output in the ODB exclusively to node 999999, omitting all 14,456 mesh nodes.

### Priority 2: History-State Indexing
- **Quad Ingestion (JTYPE=1):** In `f42_mixed_uel.for`, quads read `SVARS(8+KPT)` (KPT=1..4), indexing SVARS 9, 10, 11, 12. In `M1_MC_STAGE_C1_1_EQUIL.inp`, SVARS 9..12 were populated with Gauss-point history ($h_1, h_2, h_3, h_4$). Ingestion verified correct.
- **Tri Ingestion (JTYPE=3):** In `f42_mixed_uel.for`, tris read `SVARS(6+KPT)` (KPT=1..3), indexing SVARS 7, 8, 9. In `M1_MC_STAGE_C1_1_EQUIL.inp`, SVARS 7, 8, 9 were uniformly populated with $h_1$. Ingestion verified correct.
- **Trial-State Coupling:** In `UEXTERNALDB` (`LOP=1`), `SV_H_TRIAL` was populated from `SV_H_COMMITTED`, successfully restoring history across both quad and tri topologies.

### Priority 3: Boundary-Condition Semantics
- **Reload-from-Zero Dynamics:** Step 1 prescribed $u_y = 0.005000\,\text{mm}$ on `N_RP` in a single increment ($\Delta t = 1.0$). Rather than holding an already-established state, the boundary condition pulled the undeformed plate from $u = 0$ to $u = 0.0050\,\text{mm}$ in one step.
- **Iteration 1 Crack-Tip Spike:** In Iteration 1 of Increment 1:
  - Mechanical UEL executed with $d = 0$ (`DEG = 1.0`, undegraded).
  - The elastic stress field around the sharp slit tip ($h \approx 3.75\,\mu\text{m}$) produced an undegraded strain energy density $\psi_0 = \text{POS\_M}$ that exceeded the transferred history ($H_{\max} = 0.05365\,\text{MPa}$).
  - In `f42_mixed_uel.for` (lines 528–531), `POS_M > HIST` triggered `SV_H_TRIAL(PHYSIDX, KPT) = POS_M`, artificially inflating history at the crack tip.
  - In Iteration 2, the phase field solved with this spiked $H$, driving crack-tip damage to $\Delta d = 0.157$ at node 14403 ($x = 0.4979\,\text{mm}, y = 0.5000\,\text{mm}$).
  - This excess damage increased specimen compliance, lowering the reaction force to 647.457 N.

### Priority 4: Energy Discrepancy Decomposition
The observed discrepancies:
$$\Delta RF = 647.457 - 653.089 = -5.631\,\text{N} \quad (-0.862\%)$$
$$\Delta E_{\text{elas}} = 1.618643 - 1.632721 = -0.014078\,\text{mJ} \quad (-0.862\%)$$
$$\Delta E_{\text{frac}} = 0.031146 - 0.030663 = +0.000483\,\text{mJ} \quad (+1.574\%)$$
$$\Delta E_{\text{tot}} = 1.649789 - 1.663384 = -0.013595\,\text{mJ} \quad (-0.817\%)$$
- **Linear Elastic Proportionality:** In linear elasticity under fixed prescribed boundary displacement $u$, $E_{\text{elas}} = \frac{1}{2} F u \implies \frac{\Delta E_{\text{elas}}}{E_{\text{elas}}} = \frac{\Delta F}{F} = -0.8622\%$.
- **Mesh Discretization Compliance Gap:** In the uninterrupted baseline at $u = 0.0050\,\text{mm}$:
  - Coarse 2,906-FE mesh (`1413814.mmaster02`): $RF = 653.089\,\text{N}$, $E_{\text{tot}} = 1.6634\,\text{mJ}$.
  - Refined 14,483-FE mesh (`1412465.mmaster02`): $RF = 661.725\,\text{N}$, $E_{\text{tot}} = 1.6911\,\text{mJ}$.
  - Physical discretization gap: $\Delta RF = +8.636\,\text{N}$ ($+1.32\%$), $\Delta E_{\text{tot}} = +1.67\%$.
  - Therefore, the $0.10\%$ total energy continuity threshold is an order of magnitude smaller than the authentic physical mesh discretization difference between coarse and refined meshes.

### Priority 5: Numerical Execution Evidence
- Abaqus/Standard solved 1 increment with 2 Newton iterations and 0 cutbacks in 3.4s CPU / 18s PBS walltime.
- Iteration 1 residual: $4.065 \times 10^{-4}$ at node 129 (DOF 2); largest $\Delta d = 0.157$ at node 14403 (DOF 3).
- Iteration 2 residual: $-4.970 \times 10^{-16}$ at node 10553 (DOF 2); largest correction $-5.789 \times 10^{-5}$ at node 1639 (DOF 2).
- Newton convergence was genuine and complete (not an empty step or preprocessor exit).

---

## 3. Quantitative Donor-Versus-Target Diagnostic Table

| Quantity | Donor Job 1413814 | Package 49 Job 1414235 | Observed Difference | Required Limit | Status |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Reaction Force $RF$** | $653.089\,\text{N}$ | $647.457\,\text{N}$ | $-5.631\,\text{N}$ ($-0.862\%$) | $\le 5.00\,\text{N}$ | **FAIL** |
| **Elastic Energy $E_{\text{elas}}$** | $1.632721\,\text{mJ}$ | $1.618643\,\text{mJ}$ | $-0.014078\,\text{mJ}$ ($-0.862\%$) | $\le 0.50\%$ | **FAIL** |
| **Fracture Energy $E_{\text{frac}}$** | $0.030663\,\text{mJ}$ | $0.031146\,\text{mJ}$ | $+0.000483\,\text{mJ}$ ($+1.574\%$) | $\le 0.50\%$ | **FAIL** |
| **Total Energy $E_{\text{tot}}$** | $1.663384\,\text{mJ}$ | $1.649789\,\text{mJ}$ | $-0.013595\,\text{mJ}$ ($-0.817\%$) | $\le 0.10\%$ | **FAIL** |
| **Peak Damage $d_{\max}$** | $0.092105$ | $0.157000$ (node 14403) | $+0.064895$ | $\le 0.020$ | **FAIL** |
| **Cutbacks** | $0$ | $0$ | $0$ | $0$ | **PASS** |
| **Exit Status** | $0$ | $0$ | $0$ | $0$ | **PASS** |
| **SDV Outputs (ODB)** | Non-zero | All $0.0$ (UMAT bug) | Unverified in ODB | Verified | **FAIL** |
| **Nodal Displacements** | All 2,989 nodes | RP 999999 only (NSET bug) | Whole mesh missing | Complete | **FAIL** |

---

## 4. Root Cause Analysis & Smallest Justified Corrective Action

### Root Causes
The failure is driven by a combination of three distinct mechanisms:
1. **Implementation Defect in Engine Deck Generation:**
   - COMPANION_MAT passed `CONSTANTS=1` instead of `CONSTANTS=3`, leaving `NPHYS_VAL = 71320` and zeroing all companion SDVs.
   - `*NODE OUTPUT, NSET=N_RP` restricted displacement output to node 999999.
2. **Reload-Induced Tip Damage Evolution:**
   - Single-increment step from $\mathbf{u} = \mathbf{0}$ created an undegraded elastic stress spike in Iteration 1, increasing $H$ at the crack tip and driving $d$ to 0.157, softening the specimen by 5.63 N.
3. **Inherent Mesh Discretization Gap:**
   - The coarse donor ($h \approx 14\,\mu\text{m}$) and refined recipient ($h \approx 3.75\,\mu\text{m}$) have an authentic physical stiffness difference ($+1.32\%$) and energy difference ($+1.67\%$).

### Smallest Justified Corrective Action
Applied to `scripts/state_transfer/mode1_state_transfer_engine.py`:
1. Updated `write_continuation_deck`:
   - `lines.append("*USER MATERIAL, CONSTANTS=3")`
   - `lines.append(f" {E_mod:.1f}, {nu:.1f}, {float(n_phys):.1f}")`
   - `lines.append("*DEPVAR")`
   - `lines.append("20")`
2. Updated all step output blocks to emit whole-mesh `*NODE OUTPUT` (without `NSET=N_RP`).

---

## 5. Next Numerical Action & Master Gate Status
- **Master Gate Status:** `GATE_6B_PASS__STAGE_C1_0_CLOSED_PASSED__STAGE_C1_1_ACTIVE`.
- **Governed Task Status:** `STAGE_C1_1_EQUIL_NUMERICALLY_COMPLETED_SCIENTIFIC_CONTINUITY_FAILED`.
- **Next Numerical Action:**
  1. Regenerate `M1_MC_STAGE_C1_1_EQUIL.inp` using the repaired `mode1_state_transfer_engine.py`.
  2. Perform an Abaqus 2023 Datacheck on cluster scratch to verify syntax and output requests.
  3. Formulate the qualified replacement manifest and submit the corrected equilibrium experiment through `Invoke-Mode1Execution.ps1`.
