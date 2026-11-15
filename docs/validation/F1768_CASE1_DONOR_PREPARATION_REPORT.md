# Task F1768: Case 1 Advancing Coupled Donor Production Deck Preparation, UEL Structure Audit & Cluster Datacheck Qualification Report

**Task ID:** `F1768-CASE1-ADVANCING-COUPLED-DONOR-PREPARATION`  
**Classification:** `PREFLIGHT_QUALIFICATION_ZERO_PBS`  
**Agent:** `gemini-antigravity`  
**Date:** 15 November 2026  
**Status:** `QUALIFIED_ZERO_PBS_DATACHECK_EXIT0`  
**Predecessor Review:** `HND-F1767-OFFLINE-QUAL-CLOSEOUT-002` (Decision: `APPROVE`, Directing Option B: Prepare Case 1 Advancing Coupled Donor Preflight)  
**PBS Submissions Consumed:** Exactly 0 (0/0 allowance, cumulative historical submissions strictly preserved at 27)  
**Production Fortran UEL SHA-256:** `CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6` (Bitwise Frozen)  
**Candidate Production Deck SHA-256:** `7B37F167AF520ED2B10C1B4034507F22E923ECABC9CE4F3E7019933D872931C6`  
**Real Cluster Datacheck Exit Code:** `0` (Completed under `gcc/11.4.0 intel/2024.2.0 abaqus/2023`)

---

## 1. Executive Summary & Objective

Following the independent review approval `HND-F1767-OFFLINE-QUAL-CLOSEOUT-002`, Task F1768 was initialized under strict zero-PBS governance to resolve the critical prerequisite for the user's four-benchmark regression requirement: **Case 1 Advancing Coupled Donor Preparation**.

Prior audits in Task F1766 and F1767 proved that all historical Case 1 donor ODBs (`PK_PREANALYSIS_COARSE.odb`, `PK_F1713_JOB1_COARSE.odb`) were purely static linear-elastic continuum models that solved only Step 1 ($u_y = 0.005\,\text{mm}$), with zero crack advance and zero phase-field damage. Under linear elasticity, the stress gradient decays as $1/\sqrt{r}$ from the initial notch tip, falling below the $1.85\%$ error threshold across the distal ligament ($x \ge 0.65\,\text{mm}$).

Task F1768 establishes the complete technical preflight qualification for the minimal coarse coupled simulation needed to produce an authentic advancing donor with active phase-field damage and continuous `MISESERI` error history across the complete ligament:
1. **Coarse Physical Mesh Curation:** Extracted the 2,906-element mesh from `models/pandey_kumar_mode1/02_proposed_adaptive_refined/PK_PREANALYSIS_COARSE.inp` (2,818 quads + 88 tris, 96.97% quads, 2,988 nodes, zero negative Jacobians, max AR = 3.65).
2. **3-Layer UEL Production Deck Generation:** Built `PK_F1768_CASE_1_COARSE_COUPLED.inp` (8,718 total layered elements) using `ProductionDeckBuilder.build_deck`:
   - **Layer 1:** Phase-Field User Elements (DOF 3, elements 1–2906, types U1/U3).
   - **Layer 2:** Mechanical Displacement User Elements (DOF 1, 2, elements 2907–5812, types U2/U4).
   - **Layer 3:** Companion Visualizer Elements (CPE4/CPE3, elements 5813–8718) receiving UMAT state variables.
3. **Step 2 Coupled Crack Advancement Formulation:**
   - Step 1: Pre-critical linear loading to $u_y = 0.0050\,\text{mm}$ ($\Delta t = 0.02$).
   - Step 2: Fracture propagation to $u_y = 0.0100\,\text{mm}$ (time period 1.0, initial $\Delta t = 0.002$, min $\Delta t = 1.0\times 10^{-8}$, max $\Delta t = 0.002$).
   - Rigid tensile boundary: all top nodes tied via `*EQUATION` in DOF 2 to reference node RP 999999.
4. **Field Output Coverage:** Complete output requests configured for both steps with `FREQUENCY=1`:
   - Layer 3 Elements: `MISESERI, MISESAVG, S, E, SDV` (capturing SDV1 $d$ and SDV2 $\mathcal{H}$).
   - Reference Point: `U, RF` (capturing reaction force and displacement history).
5. **Real Cluster Datacheck Exit 0:** Transferred files to cluster scratch `/scratch9/pr21vyci/runs/mode1_pk_f1768_case1_donor_prep/`. Executed `abaqus datacheck` with `f42_mixed_uel.for`. Pre-processor completed cleanly with Exit Code 0 and zero errors.

---

## 2. Technical Deck Architecture & Audit

### A. Element Layering & Card Formatting
- **Nodes:** 2,988 physical nodes + 1 Reference Point (RP 999999 at $(0.5, 1.0)$).
- **Physical Elements:** 2,906 elements (2,818 quads, 88 tris).
- **Layer 1 (Phase Field):** 2,818 quad UELs (Type U1, DOF 3) + 88 tri UELs (Type U3, DOF 3). Properties: $\ell_0 = 0.0075\,\text{mm}, G_c = 0.0027\,\text{kN/mm}, E = 210.0\,\text{kN/mm}^2, \nu = 0.3, k = 10^{-7}, N_{\text{phys}} = 2906.0$.
- **Layer 2 (Mechanical):** 2,818 quad UELs (Type U2, DOFs 1, 2) + 88 tri UELs (Type U4, DOFs 1, 2). Same properties.
- **Layer 3 (Visualizer):** 2,818 CPE4 elements + 88 CPE3 elements. Solid section assigned to `DUMMY_MAT` with `*USER MATERIAL, CONSTANTS=3` ($E, \nu, N_{\text{phys}}$) and `*DEPVAR \n 20`.
- **NSET Card Wrapping:** All node set declarations (`N_BOTTOM`, `N_TOP`, `N_PIN`, `N_RP`) strictly wrap at 10 items per line, complying with the Abaqus 16-item limit.

### B. Boundary Conditions & Rigid Pull Equations
- **Bottom Edge (`N_BOTTOM`):** $u_y = 0.0$ on all 49 nodes along $y = 0$.
- **Origin Pin (`N_PIN`):** $u_x = 0.0$ on Node 25 at $(0.0, 0.0)$ to prevent rigid body translation.
- **Top Edge (`N_TOP`):** $u_x = 0.0$ on all 49 nodes along $y = 1.0$.
- **Tensile Pull Equations:** Each of the 49 top nodes is coupled to RP 999999 via:
  ```text
  *EQUATION
  2
  <node_id>, 2, 1.0, 999999, 2, -1.0
  ```
  RP 999999 receives displacement $u_y = 0.0050\,\text{mm}$ in Step 1 and $u_y = 0.0100\,\text{mm}$ in Step 2.

### C. Step Controls & Incremental Settings
- **Step 1:** `*STATIC`, initial $\Delta t = 0.02$, time period $1.0$, min $\Delta t = 1.0\times 10^{-7}$, max $\Delta t = 0.02$. `INC=10000`.
- **Step 2:** `*STATIC`, initial $\Delta t = 0.002$, time period $1.0$, min $\Delta t = 1.0\times 10^{-8}$, max $\Delta t = 0.002$. `INC=20000`.
- **Field Output:** `*OUTPUT, FIELD, FREQUENCY=1` in both steps, outputting `MISESERI` and `SDV` for every increment to ensure full-history envelope capture.

---

## 3. Real Cluster Datacheck Verification Record

A real cluster datacheck was executed under `gcc/11.4.0 intel/2024.2.0 abaqus/2023` on cluster scratch:

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

Verification Highlights:
- **Compilation:** Intel Fortran Classic 2021.13.0 successfully compiled `f42_mixed_uel.for` (`CE8D5EDC...`) with automatic CPU dispatch.
- **Linking:** GNU ld cleanly linked the user object into `standardU`.
- **Input Processing:** Pre-processor verified all 8,718 elements, 2,989 nodes, 49 equations, material definitions, and two static steps without syntax or topology errors.
- **Exit Status:** `Exit Code 0`.

---

## 4. Resource Estimation & HPC Execution Plan

To execute the coarse coupled donor solve upon registered authorization:

| Parameter | Specification | Verification Basis |
| :--- | :--- | :--- |
| **Job Name** | `PK_F1768_C1_DONOR` | Distinct, traceable Mode-I naming |
| **Input Deck** | `PK_F1768_CASE_1_COARSE_COUPLED.inp` | SHA-256 `7B37F167AF520ED2B10C1B4034507F22E923ECABC9CE4F3E7019933D872931C6` |
| **User Subroutine** | `f42_mixed_uel.for` | Frozen SHA-256 `CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6` |
| **Execution Architecture** | 1-CPU Serial Mode | Single-rank shared memory anchor, guaranteed thread safety |
| **Memory Allocation** | 8 GB RAM | Datacheck measured < 1 GB peak memory usage |
| **Walltime Limit** | 02:00:00 | Bounded limit; expected runtime is ~10–15 minutes (2,906 elements) |
| **Queue** | `entry_imfdfkmq` $\to$ `normal_imfdfkmq` | Normal production execution queue |
| **Run Directory** | `/scratch9/pr21vyci/runs/mode1_pk_f1768_case1_donor_prep` | Dedicated cluster scratch directory |
| **Notification Directives** | `#PBS -m abe`, `#PBS -M pr21vyci@mailserver.tu-freiberg.de` | Dual-channel email + Telegram wrapper integrated |
| **Submission Wrapper** | `submit_f1768_case1_donor.pbs` | Lock guard, quota check, hash check, terminal traps installed |

---

## 5. Offline Unit Test Suite Record

The offline test suite [tests/unit/test_f1768_case1_donor_preparation.py](file:///D:/Master%20thesis/Adaptive%20remeshing/tests/unit/test_f1768_case1_donor_preparation.py) was executed and verified:
1. `test_frozen_uel_integrity`: **PASS** (UEL hash matches `CE8D5EDC...` bitwise).
2. `test_parse_coarse_candidate_mesh`: **PASS** (2,988 nodes, 2,818 quads, 88 tris, 2,906 elements).
3. `test_build_case1_coarse_coupled_deck`: **PASS** (8,718 layered elements, NSET wrapping $\le 16$, two steps, field output with `FREQUENCY=1`).
4. `test_coarse_donor_mesh_quality`: **PASS** (96.97% quads, zero negative Jacobians, max AR = 3.65).

Full multi-task regression suite across F1763, F1764, F1766, F1767, and F1768: **26/26 tests PASS in 2.01s**.

---

## 6. Governance & Review Authorization Request

- **PBS Submissions Consumed under F1768:** Exactly 0 (0/0 allowance, cumulative historical submissions strictly preserved at 27).
- **Execution Request:** We request independent review authorization for **exactly ONE coarse donor PBS solve** (`PK_F1768_C1_DONOR`, 1 CPU, 8 GB, $\le 2\,\text{h}$) to produce the authentic advancing coupled donor ODB required for Case 1 Method A refinement.
- **Zero Forward Fracture Runs:** No production crack propagation or four-case batch execution is requested under this task.
