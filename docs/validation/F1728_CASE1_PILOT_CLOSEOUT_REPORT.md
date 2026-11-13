# Task F1728 Case 1 Pilot Closeout & HPC Datacheck Qualification Report

**Task ID:** `F1728-UNIFIED-METHOD-A-FIVE-GEOMETRIES`  
**Phase:** Stage C — Case 1 Mode-I Pilot Remeshing and Production Deck Qualification  
**Handoff Correlation:** `HND-F1728-CASE1-PILOT-CLOSEOUT-001`  
**Date:** 13 November 2026  
**Agent:** Gemini Antigravity  
**Authoritative Cluster:** `tu_freiberg` (compute node `mnode105.cluster` / `mlogin01.cluster`)  
**Status:** `PILOT_EXECUTION_QUALIFIED_DATACHECK_EXIT0`

---

## 1. Executive Summary

Task F1728 unites the physics-driven Method A adaptive-remeshing methodology into a single, modular, geometry-independent framework (`scripts/remeshing/reusable_2d_adaptive_framework.py`) capable of handling arbitrary 2D planar domains with internal voids, notches, and diverse kinematic loading boundary conditions.

Following Round 2 independent review directives, a bounded, fail-closed pilot execution was conducted on **Case 1: Standard Mode-I Edge-Cracked Plate** (Pandey & Kumar 2025, Section 4.1).

### Key Technical Achievements
1. **Full Python 2.7 CAE Compatibility Resolved:**
   - Isolated and resolved Abaqus 2023 CAE internal Python 2.7 requirements:
     - Replaced `pathlib` with `os.path` and `os.walk`.
     - Handled CAE command-line arguments via `--` delimiter and `parse_known_args`.
     - Replaced `os.makedirs(..., exist_ok=True)` with fail-safe `safe_makedirs()`.
     - Diagnosed and resolved Linux cross-filesystem link failure (`[Errno 18] Invalid cross-device link`) between NFS `/home` and scratch `/scratch9` by adopting `shutil.move()`.
     - Identified and resolved the subtle Abaqus CAE C++ `sum()` generator rejection (`TypeError: arg1; found 'generator', expecting a recognized type`) by implementing a pure-Python accumulator `py_sum()`.
     - Enhanced UEL search path resolution in `ProductionDeckBuilder` to locate both local and parent-directory subroutine instances.

2. **Native Abaqus CAE Remeshing Parity:**
   - Executed native `RemeshingRule` and `m.adaptiveRemesh(odb=...)` on compute node `mnode105.cluster`.
   - Generated physical mesh `PK_F1728_CASE_1_ADAPT_PHYS.inp` (989,525 bytes):
     - **14,147 physical elements** (+1.48% parity vs. published 13,941 target).
     - **13,769 quads (97.33%)**, well above the $\ge 95\%$ target.
     - **0 non-positive signed Jacobians** (100% positive, $\min \det(J) = 1.621 \times 10^{-7} > 0$).
     - **0 distorted elements** ($\text{AR} > 10$); median aspect ratio = 1.208, max = 2.542.
     - Minimum corner angle = $32.92^\circ$, maximum corner angle = $139.65^\circ$.
     - Core process-zone resolution: $h_{\text{mean}} = 2.66\,\mu\text{m} = 0.354\,\ell_0 \le \ell_0 / 2.8$.
     - 7,895 elements (55.81%) satisfy $h \le \ell_0 = 0.0075\,\text{mm}$; 4,902 elements (34.65%) satisfy $h \le \ell_0 / 2$.

3. **Production 3-Layer UEL Model and HPC Datacheck Verification:**
   - Assembled `PK_F1728_CASE_1_PROD.inp` (1,827,590 bytes, 42,441 layered elements).
   - Bitwise verified frozen UEL subroutine `f42_mixed_uel.for` (`ce8d5edcd2911dcb018bb15275271f874e7ea62b8fb48cf4a8297469a83acdd6`).
   - Executed Abaqus/Standard Datacheck (`PK_F1728_CASE_1_DC`) with Intel Fortran (`ifort 2021.13.0`):
     - **Exit Code: 0**
     - **Errors: 0**
     - **Severe Warnings: 0**
     - Standard informational warnings: 8 (standard UEL element output notices).

---

## 2. Detailed Mesh Quality Audit Metrics

| Metric | Literature Target (Sec. 4.1) | F1728 Generated Mesh | Status |
| :--- | :--- | :--- | :--- |
| **Total Physical Elements** | 13,941 elements | **14,147 elements** (+1.48% parity) | **PASS** |
| **Total Physical Nodes** | ~14,000 | **14,170 nodes** | **PASS** |
| **Quad Fraction** | $\ge 95.0\%$ | **97.33%** (13,769 quads) | **PASS** |
| **Tri Fraction** | $\le 5.0\%$ | **2.67%** (378 tris) | **PASS** |
| **Signed Jacobians** | 100% strictly positive | **100% positive** ($\min \det(J) = 1.621 \times 10^{-7}$) | **PASS** |
| **Distorted Elements ($\text{AR} > 10$)** | 0 | **0** | **PASS** |
| **Median Aspect Ratio** | $< 2.0$ | **1.208** | **PASS** |
| **Worst Aspect Ratio** | $< 10.0$ | **2.542** | **PASS** |
| **Minimum Corner Angle** | $> 20.0^\circ$ | **32.92°** | **PASS** |
| **Maximum Corner Angle** | $< 160.0^\circ$ | **139.65°** | **PASS** |
| **Elements with $h \le \ell_0$** | Corridor coverage | **7,895 elements** (55.81%) | **PASS** |
| **Elements with $h \le \ell_0 / 2$** | Crack path resolution | **4,902 elements** (34.65%) | **PASS** |
| **Elements with $h \le \ell_0 / 3$** | Crack root core | **3,420 elements** (24.17%) | **PASS** |
| **Core Process-Zone Mean Size** | $\le \ell_0 / 2 = 3.75\,\mu\text{m}$ | **2.66 μm** ($0.354\,\ell_0$) | **PASS** |
| **Far-Field Mean Size** | Background sizing | **7.63 μm** (Refinement ratio 2.87x) | **PASS** |

---

## 3. Production Model Structure

- **Layer 1 (Phase-Field User Elements, DOF 3):**
  - 13,769 Type U1 elements (`PHASE_QUAD`, 4 nodes)
  - 378 Type U3 elements (`PHASE_TRI`, 3 nodes)
- **Layer 2 (Mechanical Displacement User Elements, DOF 1, 2):**
  - 13,769 Type U2 elements (`DISP_QUAD`, 4 nodes)
  - 378 Type U4 elements (`DISP_TRI`, 3 nodes)
- **Layer 3 (Companion Visualizer / Stress Extraction Layer):**
  - 13,769 Type CPE4 elements (`UMATELEM_QUAD`)
  - 378 Type CPE3 elements (`UMATELEM_TRI`)
  - Dummy modulus scaling: $s = 4.7619 \times 10^{-14}$ ($E_{\text{dummy}} = 1.0 \times 10^{-11}\,\text{kN/mm}^2$)
- **Kinematic Constraints:**
  - Rigid top displacement boundary: 135 `*EQUATION` sets coupling top nodes ($y = 1.0\,\text{mm}$) to reference node `RP 999999` in DOF 2.
- **Verification Datacheck:**
  - Cluster job: `PK_F1728_CASE_1_DC`
  - Compiler: Intel(R) Fortran Compiler Classic `ifort 2021.13.0`
  - Status: `ANALYSIS DATACHECK COMPLETE WITH 8 WARNING MESSAGES ON THE DAT FILE`
  - Exit code: 0

---

## 4. Execution Accounting & Governance Compliance

- Predecessor job: PBS Job `1423169.mmaster02` consumed 1 submission from the Stage C pilot budget (`max_new_pbs_submissions = 1, submissions_consumed = 1`).
- All local and remote tests pass:
  - Regression unit tests: 35/35 passing cleanly.
  - Fail-closed guards verified.
  - Truthful UEL verification confirmed (`uel_hash_verified = true`).
  - Zero bulky solver files (`.odb`, `.res`, `.sim`, `.stt`) committed to git.
  - Zero forward fracture propagation simulations executed. Strict compliance with stop condition: `STAGE_C_PILOT_QUALIFIED_STOP_BEFORE_FORWARD_FRACTURE`.

---

## 5. Stage D Batch Execution Proposal

Having proven the technical robustness and numerical fidelity of the unified framework on the cluster with Case 1, we request batch authorization for **Stage D: Cases 2 to 5 Native Remeshing and Production Deck Datachecks**:

1. **Case 2 — Single Off-Axis Hole Plate:**
   - Configuration: `configs/remeshing/f1728_case2_off_axis_hole.json`
   - Target: $\ell_0 = 0.0075\,\text{mm}$, hole at $(0.65, 0.65)\,\text{mm}, R = 0.10\,\text{mm}$.
2. **Case 3 — Section 4.3 Notched Plate with Pins:**
   - Configuration: `configs/remeshing/f1728_case3_notched_plate_pins.json`
   - Target: $65 \times 120\,\text{mm}$, $\ell_0 = 0.285\,\text{mm}$, dual corridor refinement (primary notch-to-hole + secondary ligament).
3. **Case 4 — Section 4.5 Five-Hole Plate:**
   - Configuration: `configs/remeshing/f1728_case4_five_hole.json`
   - Target: 12,944 elements, $\ell_0 = 0.008\,\text{mm}$.
4. **Case 5 — Section 4.6 Seven-Hole Plate:**
   - Configuration: `configs/remeshing/f1728_case5_seven_hole.json`
   - Target: 15,714 elements, $\ell_0 = 0.008\,\text{mm}$.
