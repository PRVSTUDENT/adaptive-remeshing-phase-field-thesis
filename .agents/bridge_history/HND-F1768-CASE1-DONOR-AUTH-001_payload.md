# Task F1768 Preflight Payload: Case 1 Advancing Coupled Donor Production Deck Preparation & Cluster Datacheck Qualification

**Correlation ID:** `HND-F1768-CASE1-DONOR-AUTH-001`  
**Predecessor Correlation ID:** `HND-F1767-OFFLINE-QUAL-CLOSEOUT-002` (Decision: `APPROVE`, Directing Option B: Case 1 Advancing Coupled Donor Preparation)  
**Task ID:** `F1768-CASE1-ADVANCING-COUPLED-DONOR-PREPARATION`  
**Commit SHA:** (commit-pinned on GitHub `origin/main`)  
**Timestamp:** `2026-11-15T09:18:00+01:00`  
**Author:** `gemini-antigravity`  
**Scope Boundary:** `PREFLIGHT_QUALIFICATION_ZERO_PBS` (Exactly 0 PBS Jobs Consumed; Cumulative Submissions Preserved at 27; Zero Forward Fracture Solves Executed; Bitwise Frozen UEL Preserved)

---

## 1. Executive Summary & Review Directives Addressed

In response to the independent review approval `HND-F1767-OFFLINE-QUAL-CLOSEOUT-002`, Task F1768 executes Option B under strict zero-PBS governance, resolving the critical prerequisite for the user's four-benchmark regression requirement:

1. **Root Defect Addressed:** Previous audits (F1766, F1767) proved that all existing Case 1 donor ODBs (`PK_PREANALYSIS_COARSE.odb`, `PK_F1713_JOB1_COARSE.odb`) are purely static linear elastic models (Step 1 only, zero crack advance, zero damage). Under linear elasticity, singular stresses exist only at the notch tip ($r \to 0$); by $x \ge 0.65\,\text{mm}$, stress gradients decay and `MISESERI` falls below the $1.85\%$ target. Switching `outputFrequency=ALL_INCREMENTS` on an elastic donor cannot refine the distal ligament without coupled crack advance.
2. **3-Layer UEL Production Deck Built:** Built `PK_F1768_CASE_1_COARSE_COUPLED.inp` from the verified 2,906-element coarse physical mesh (2,818 quads + 88 tris, 2,988 nodes, 96.97% quads, zero negative Jacobians, max AR = 3.65):
   - **Layer 1:** Phase-Field User Elements (DOF 3, elements 1–2906, types U1/U3).
   - **Layer 2:** Mechanical Displacement User Elements (DOF 1, 2, elements 2907–5812, types U2/U4).
   - **Layer 3:** Companion Visualizer Elements (CPE4/CPE3, elements 5813–8718) receiving UMAT state variables.
   - Total layered elements: 8,718.
   - NSET line wrapping: strictly $\le 16$ items per line (10 items/line).
3. **Step 2 Coupled Crack Advance Formulation:**
   - Step 1: Linear loading to $u_y = 0.0050\,\text{mm}$ ($\Delta t = 0.02$).
   - Step 2: Fracture propagation to $u_y = 0.0100\,\text{mm}$ (time period 1.0, initial $\Delta t = 0.002$, min $\Delta t = 1.0\times 10^{-8}$, max $\Delta t = 0.002$).
   - Boundary: Bottom pinned ($u_y=0$), origin pinned ($u_x=0$), top edge tied via `*EQUATION` in DOF 2 to RP 999999.
4. **Complete Field Output Coverage:** Configured `*OUTPUT, FIELD, FREQUENCY=1` in both steps, outputting `MISESERI, MISESAVG, S, E, SDV` for every increment to ensure full-history envelope capture across crack growth.
5. **Real Cluster Datacheck Exit 0:** Executed `PK_F1768_CASE_1_DC` on cluster scratch under `gcc/11.4.0 intel/2024.2.0 abaqus/2023`. The frozen UEL `f42_mixed_uel.for` (`CE8D5EDC...`) compiled and linked cleanly, and Abaqus pre-processor verified all elements, nodes, and steps with Exit Code 0 and zero errors.
6. **Offline Unit & Regression Test Verification:** Authored `tests/unit/test_f1768_case1_donor_preparation.py` (4/4 PASS in 0.49s). Full regression suite across F1763, F1764, F1766, F1767, and F1768 passes 26/26 tests in 2.01s.

---

## 2. Technical Evidence & Preflight File Hashes

| Artifact | Repository Path | SHA-256 Digest | Status |
| :--- | :--- | :--- | :---: |
| **Physical Coarse Mesh** | `models/pandey_kumar_mode1/02_proposed_adaptive_refined/PK_PREANALYSIS_COARSE.inp` | `37AE41961556C6CD323BD822C0AC6EC62C5B42284CFFC5D30F8712C209A01B05` | Verified (2,906 el) |
| **Coarse Coupled Deck** | `models/pandey_kumar_mode1/237_f1768_case1_donor/PK_F1768_CASE_1_COARSE_COUPLED.inp` | `7B37F167AF520ED2B10C1B4034507F22E923ECABC9CE4F3E7019933D872931C6` | Verified (8,718 layered el) |
| **Frozen Fortran UEL** | `models/pandey_kumar_mode1/f42_mixed_uel.for` | `CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6` | Bitwise Unmodified |
| **PBS Execution Script** | `models/pandey_kumar_mode1/237_f1768_case1_donor/submit_f1768_case1_donor.pbs` | `B01A50AF39083E315EE167C6CE5469EC9F8B0D026E9678DFD75D2AA3B191ADA6` | Verified (1 CPU, 8 GB, 2h) |
| **Datacheck Shell Script** | `models/pandey_kumar_mode1/237_f1768_case1_donor/run_f1768_datacheck.sh` | `E5B4B34F6DE91B87AE713F29AECE83885EDFE814323E723AE936C590E8551609` | Exit Code 0 |
| **Preflight Report** | `docs/validation/F1768_CASE1_DONOR_PREPARATION_REPORT.md` | `7D481718FE3A11F95E65B5CEA51711C3B40D5D41CF1FB061770E99FD2EEF5B5C` | Published |

---

## 3. Real Cluster Datacheck Execution Output

```text
=== Running Abaqus Datacheck for PK_F1768_CASE_1_DC ===
Abaqus JOB PK_F1768_CASE_1_DC
Begin Compiling Abaqus/Standard User Subroutines
 Intel(R) Fortran 2021.13.0-1693
End Compiling Abaqus/Standard User Subroutines
Begin Linking Abaqus/Standard User Subroutines
GNU ld version 2.30-128.el8_10
End Linking Abaqus/Standard User Subroutines
Begin Analysis Input File Processor
Run pre
End Analysis Input File Processor
Begin Abaqus/Standard Datacheck
Run standard
End Abaqus/Standard Analysis
Begin SIM Wrap-up
Run SMASimUtility
End SIM Wrap-up
Abaqus JOB PK_F1768_CASE_1_DC COMPLETED
=== Datacheck Finished with Exit Code 0 ===
```

---

## 4. Execution Request & Governance

- **PBS Submissions Consumed under F1768:** Exactly 0 (0/0 allowance, cumulative historical submissions preserved at 27).
- **Execution Request:** Requesting independent review authorization for **exactly ONE coarse coupled donor PBS solve** (`PK_F1768_C1_DONOR`):
  - Model: 2,906 physical elements / 8,718 layered elements.
  - Resources: 1 CPU serial, 8 GB RAM, walltime limit 02:00:00 (expected runtime ~10–15 minutes).
  - Queue: `entry_imfdfkmq` routing to `normal_imfdfkmq`.
  - Objective: Produce the authentic advancing donor ODB with continuous `MISESERI` and phase-field damage history across crack growth to unblock BM-1 Method A adaptivity.
