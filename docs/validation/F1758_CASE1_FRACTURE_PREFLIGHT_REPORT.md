# Task F1758: Case 1 Mode-I Notched Plate Coupled Phase-Field Fracture Qualification & Production Preflight Report

**Date:** 15 November 2026  
**Status:** **PREFLIGHT QUALIFIED — ALL GATES PASS (ZERO PBS JOBS CONSUMED)**  
**Assigned Agent:** Gemini Antigravity  
**Audit Protocol:** Technical Preflight, Field Output Audit, Cluster Datacheck Exit 0, and Production Script Staging  
**Governance Restrictions Enforced:** Exactly 0 PBS jobs consumed under F1758 (0/0 allowance, cumulative historical submissions preserved at 26), bitwise frozen UEL `f42_mixed_uel.for` (`CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6`) strictly preserved, zero forward fracture runs.  
**Test Suite:** `tests/unit/test_f1758_case1_preflight.py` (5/5 passed in 0.40s)

---

## 1. Executive Summary & Objective

Task F1758 completes the technical preflight for the definitive Case 1 Mode-I single-edge notched plate coupled phase-field fracture simulation. 

In predecessor Task F1739, Job `1423321.mmaster02` achieved complete macroscopic and thermodynamic fracture validation across all 2,050 increments to the full loading endpoint $u_y = 0.0100\,\text{mm}$ (initial stiffness $K_0 = 137.86\,\text{kN/mm}$ [$-0.06\%$], peak load $F_{\max} = 730.72\,\text{N}$ [$-3.57\%$], complete $99.96\%$ post-peak load drop to $0.2562\,\text{N}$, global thermodynamic energy balance $1.185\%$, strictly monotonic fracture dissipation $\dot{E}_{\text{frac}} \ge 0$, Exit Status 0). However, the predecessor production deck `PK_F1739_CASE_1_PROD.inp` requested only `*ELEMENT OUTPUT, ELSET=All_elem: S`, omitting `SDV`. Consequently, integration-point state variables `SDV1` ($d$) and `SDV2` ($\mathcal{H}$) were unwritten to the ODB, precluding 2D spatial damage contour plotting from the ODB.

Task F1758 resolves this technical gap by:
1. Re-generating the 3-layer production deck `PK_F1758_CASE_1_PROD.inp` with explicit `S, SDV` field output requests in both Step 1 and Step 2.
2. Enforcing `FREQUENCY=1` so that every converged increment writes an ODB frame for 2D damage field visualization.
3. Verifying strict 16-item line wrapping for all node sets.
4. Preserving the exact bitwise frozen user subroutine `f42_mixed_uel.for`.
5. Executing an interactive Abaqus datacheck on the cluster, confirming clean Exit 0 (`ANALYSIS DATACHECK COMPLETE`).
6. Staging the production PBS script `submit_f1758_case1_fracture.pbs` with dual-channel notification, storage prechecks, and lock guards.

---

## 2. Technical Preflight Specifications

### A. Production Input Deck (`PK_F1758_CASE_1_PROD.inp`)
- **Source Physical Mesh:** `models/pandey_kumar_mode1/226_f1738_case1_ligament_refinement/PK_F1738_CASE_1_ADAPT_PHYS.inp` (13,960 physical elements, 13,922 nodes, 100.0% area compliance $h \le \ell_0/2 = 3.75\,\mu\text{m}$ across all 10 horizontal corridor stations).
- **Production Deck Path:** `models/pandey_kumar_mode1/227_f1739_case1_adapted_fracture/PK_F1758_CASE_1_PROD.inp`
- **SHA-256:** `C188E955328848EABFFA6FED7D42D9D1EC916548BE8A53361A090BB7A06107AF`
- **Layer Architecture:**
  - **Layer 1 (Phase Field UEL):** 13,611 quads (TYPE=U1) + 349 tris (TYPE=U3). Active degree of freedom is strictly `3` ($d$).
  - **Layer 2 (Mechanical UEL):** 13,611 quads (TYPE=U2) + 349 tris (TYPE=U4). Active degrees of freedom are strictly `1, 2` ($u_x, u_y$).
  - **Layer 3 (Visualizer Companion):** 13,611 quads (TYPE=CPE4) + 349 tris (TYPE=CPE3). Dummy linear elastic material (`E = 210.0`, `nu = 0.3`) with `*DEPVAR = 16`.
  - **Total Elements:** 41,880 layered elements.
  - **Total Nodes:** 13,922 nodes (13,921 mesh nodes + 1 Reference Point node 999999).
- **Field Output Requests:**
  - Step 1 (line 56022): `*ELEMENT OUTPUT, ELSET=All_elem` followed by `S, SDV`.
  - Step 2 (line 56039): `*ELEMENT OUTPUT, ELSET=All_elem` followed by `S, SDV`.
  - Step 1 & 2: `*OUTPUT, FIELD, FREQUENCY=1` guarantees 100% framewise temporal resolution for all converged increments.
- **Node Set Wrapping:** All `*NSET` entries (`N_BOTTOM`, `N_TOP`, etc.) strictly wrapped to $\le 16$ entries per line.

### B. User Subroutine Integrity
- **Subroutine Path:** `models/pandey_kumar_mode1/f42_mixed_uel.for`
- **SHA-256:** `CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6`
- **Verification:** Bitwise identical to the frozen production UEL. Zero code changes.

### C. Cluster Datacheck Execution
- **Run Directory:** `/scratch9/pr21vyci/runs/mode1_pk_f1758_case1_preflight/`
- **Job Name:** `PK_F1758_CASE_1_DC`
- **Compiler / Abaqus Environment:** `gcc/11.4.0 intel/2024.2.0 abaqus/2023`
- **Execution Command:** `abaqus job=PK_F1758_CASE_1_DC input=PK_F1758_CASE_1_PROD.inp user=f42_mixed_uel.for datacheck -interactive`
- **Execution Log Receipt:**
  ```text
  Begin Compiling Abaqus/Standard User Subroutines
  Intel(R) Fortran 2021.13.0-1693
  End Compiling Abaqus/Standard User Subroutines
  Begin Linking Abaqus/Standard User Subroutines
  GNU ld version 2.30-128.el8_10
  End Linking Abaqus/Standard User Subroutines
  Begin Analysis Input File Processor
  End Analysis Input File Processor
  Begin Abaqus/Standard Datacheck
  End Abaqus/Standard Analysis
  Begin SIM Wrap-up
  End SIM Wrap-up
  Abaqus JOB PK_F1758_CASE_1_DC COMPLETED
  === Datacheck Finished with Exit Code 0 ===
  ```
- **Datacheck Status:** `ANALYSIS DATACHECK COMPLETE` with 0 errors and Exit Code 0.

---

## 3. Production Script Staging (`submit_f1758_case1_fracture.pbs`)

- **Script Path:** `models/pandey_kumar_mode1/227_f1739_case1_adapted_fracture/submit_f1758_case1_fracture.pbs`
- **SHA-256:** `33BFD0D3F94C18B6E025732D3F51FF40F7135EC79E342CAAA4128906D714FC1F`
- **Execution Target:** Compute node execution on `normal_imfdfkmq` via queue `entry_imfdfkmq`.
- **Resources:** 1 CPU serial, 16 GB RAM, walltime 08:00:00 (Job 1423321 took 3.70 h walltime, well within 8.0 h limit).
- **Directives:**
  - `#PBS -N PK_F1758_C1_FRAC`
  - `#PBS -m abe -M pr21vyci@mailserver.tu-freiberg.de`
  - Duplicate lock guard: `PK_F1758_C1_FRAC.lck`
  - Storage preflight check: $\ge 5\,\text{GB}$ available scratch space verified.
  - Subroutine SHA-256 verification: bitwise check against `CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6`.
  - Notification trap: `notification_install_terminal_trap` integrated.

---

## 4. Preflight Acceptance Gates

| Gate ID | Criterion | Evidence / Measured Value | Status |
| :--- | :--- | :--- | :---: |
| **Gate G1** | Physical Mesh Integrity | 13,960 elements, 100% corridor area compliance $\le \ell_0/2$, 0 negative Jacobians | **PASS** |
| **Gate G2** | Production Deck Architecture | 41,880 layered elements, UEL active DOFs: U1/U3=3, U2/U4=1,2, CPE4/CPE3=Layer 3 | **PASS** |
| **Gate G3** | SDV Field Output Coverage | `*ELEMENT OUTPUT, ELSET=All_elem: S, SDV` present in Step 1 & 2; `FREQUENCY=1` | **PASS** |
| **Gate G4** | Node Set Formatting | All `*NSET` lines strictly wrapped to $\le 16$ entries | **PASS** |
| **Gate G5** | Frozen UEL Integrity | SHA-256 bitwise identical to `CE8D5EDC...` | **PASS** |
| **Gate G6** | Cluster Datacheck | `PK_F1758_CASE_1_DC` executed Exit 0 (`ANALYSIS DATACHECK COMPLETE`) | **PASS** |
| **Gate G7** | PBS Script Staging | `submit_f1758_case1_fracture.pbs` verified with lock guards, notification traps | **PASS** |
| **Gate G8** | PBS Submission Budget | Exactly 0 PBS jobs consumed under F1758 (cumulative preserved at 26) | **PASS** |

---

## 5. Next Steps

With all preflight gates verified and cluster datacheck passed with Exit 0, technical qualification is complete. The bridge packet `HND-F1758-CASE1-PREFLIGHT-001` is staged to seek independent review authorization for exactly 1 bounded PBS production simulation (prospective 27th cumulative submission) to generate the definitive Case 1 phase-field fracture ODB with full 2D damage field visualization.
