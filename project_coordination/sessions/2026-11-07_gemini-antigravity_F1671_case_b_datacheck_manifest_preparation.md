# Task F1671 Session Report: Case B Abaqus Datacheck Manifest Preparation

## Metadata
- **Session ID**: `f1657-session-001`
- **Task ID**: `F1671-CASE-B-ABAQUS-DATACHECK-MANIFEST-PREPARATION`
- **Agent**: `gemini-antigravity`
- **Timestamp**: `2026-11-07T19:00:00+01:00`
- **Predecessor Review**: `HND-9f8a3ee25bd1` (ChatGPT Independent Review of F1670: `ACCEPTED`)
- **Verified Provenance Commit**: `576ea81c70fde60eeff4faf24a99a95677c3b9c4`
- **Governed Boundary**: Zero new PBS submissions (`max_new_pbs_submissions = 0`), no HPC datacheck or production job executed, frozen UEL untouched (`CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6`).

---

## 1. Executive Summary
In independent review `HND-9f8a3ee25bd1`, ChatGPT accepted the F1670 damage-core reconciliation and authorized Task F1671:
> *"Decision: Authorize offline preparation and verification of the Case B datacheck package. Do not authorize HPC execution yet. Prepare one bounded, read-only/offline datacheck execution package for PK_HOLE_F1668_CASE_B_DAMAGE_ONLY_PROD.inp... Set max_new_pbs_submissions = 0 for this preparation task."*

Antigravity has executed Task F1671 strictly within these offline boundaries:
1. Conducted card-by-card structural verification of `PK_HOLE_F1668_CASE_B_DAMAGE_ONLY_PROD.inp` (32,463 lines).
2. Verified exact $3\times$ layered element parity (8,237 physical elements $\to$ 24,711 layered elements: 6,398 quads + 1,839 tris in each layer).
3. Verified complete slit flank topological disconnection along $x \in [0.0, 0.50]$ (29 top flank nodes at $y = 0.5010\,$mm, 29 bottom flank nodes at $y = 0.4990\,$mm, 0 shared nodes).
4. Verified 51 tying `*EQUATION` constraints connecting each `N_TOP` node to reference node 999999 in vertical displacement (DOF 2).
5. Verified frozen UEL subroutine integrity (`CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6`).
6. Verified PBS job duplication safeguards against `HPC_JOB_LEDGER.csv` (`M1_HOLE_CASE_B_DATACHECK` is completely fresh and unreserved).
7. Formulated authoritative execution manifest `PK_HOLE_F1671_DATACHECK_MANIFEST.json` defining exact Abaqus command syntax, resource estimates, and 7 rigorous acceptance criteria for future solver execution.
8. Extended framework test suite: **16/16 unit tests PASS in 6.13s**.

---

## 2. Technical Verification Matrix

| Verification Item | Specification / Required Value | Verified Manifest Value | Verdict |
| :--- | :--- | :--- | :---: |
| **Physical Elements** | 8,237 (Gmsh Frontal-Delaunay Blossom) | 6,398 quads (77.67%), 1,839 tris (22.33%) | **PASS** |
| **Layer 1 (Phase Field)** | 8,237 elements | 6,398 U1 (quads), 1,839 U3 (tris) | **PASS** |
| **Layer 2 (Displacement)** | 8,237 elements | 6,398 U2 (quads), 1,839 U4 (tris) | **PASS** |
| **Layer 3 (Companion UMAT)** | 8,237 elements | 6,398 CPE4 (quads), 1,839 CPE3 (tris) | **PASS** |
| **Grand Total Elements** | Exact $3\times$ parity: 24,711 elements | 24,711 layered elements | **PASS** |
| **UEL Property Cards** | 4 cards matching `f42_mixed_uel.for` | `(0.0075, 0.0027, 210.0, 0.30, 1.0e-07, 8237.0)` | **PASS** |
| **Companion Material** | `*USER MATERIAL, CONSTANTS=3` | `(210.0, 0.30, 8237.0)` with `*DEPVAR (20)` | **PASS** |
| **Section Assignment** | `*SOLID SECTION, ELSET=All_elem` | Contains only companion elements, 0 UEL elements | **PASS** |
| **Slit Flank Disconnection** | Top: $y=0.5010\,$mm; Bot: $y=0.4990\,$mm | Top: 29 nodes; Bot: 29 nodes; Shared: 0 | **PASS** |
| **RP Tying Equations** | 51 top nodes tied to node 999999 | 51 equations (102 deck lines) in DOF 2 | **PASS** |
| **Boundary Conditions** | Roller (bottom), Pin (corner), Lateral (top) | Fully specified in Step 1 and Step 2 | **PASS** |
| **Frozen UEL SHA-256** | `CE8D5EDC...` | `CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6` | **PASS** |
| **Input Deck SHA-256** | Exact reproducible digest | `D1D71B2033B7172DD8B126D287AFB24772D489622D47910072B92F902733CC32` | **PASS** |
| **PBS Job Name Uniqueness**| Not present in `HPC_JOB_LEDGER.csv` | `M1_HOLE_CASE_B_DATACHECK` (is_duplicate: False) | **PASS** |

---

## 3. Proposed Datacheck Command & Resource Envelope
- **Proposed Command Syntax**:
  ```bash
  abaqus job=M1_HOLE_CASE_B_DATACHECK input=PK_HOLE_F1668_CASE_B_DAMAGE_ONLY_PROD.inp user=f42_mixed_uel.for datacheck interactive
  ```
- **Execution Mode**: 1 CPU, single-rank shared-memory SMP (`mpimode=smp`).
- **Resource Request**:
  - Queue: `entry_imfdfkmq` (routing to `short_imfdfkmq` or `normal_imfdfkmq`)
  - CPUs: 1
  - Memory: 4 GB
  - Walltime: 00:15:00 (estimated walltime: 15–45 seconds)
  - Scratch disk: < 50 MB (preflight databases only)

---

## 4. Acceptance Criteria for Future Solver Execution
Future solver execution of this datacheck will be evaluated against:
1. Abaqus preprocessor terminates with Exit 0 and `"THE ANALYSIS HAS BEEN COMPLETED"` in `.log`.
2. Zero `"***ERROR"` records in `.dat` indicating missing properties, syntax mismatches, or invalid sets.
3. Zero warnings regarding non-positive Jacobians or distorted elements during element assembly in `.msg` / `.dat`.
4. Complete resolution of the 51 `*EQUATION` ties without singular or overconstrained degree-of-freedom warnings.
5. Successful compilation and shared-object linking of `f42_mixed_uel.for` without symbol collisions.
6. Exact memory preallocation logged for the 24,711-element mixed system.
7. Strict zero-increment execution: solver halts immediately after preflight without initiating Newton-Raphson equilibrium iterations or crack propagation.

---

## 5. Artifacts Produced
1. `models/pandey_kumar_mode1/176_method_a_plate_with_hole/PK_HOLE_F1671_DATACHECK_MANIFEST.json` (authoritative execution manifest).
2. `scripts/validation/prepare_f1671_case_b_datacheck_manifest.py` (offline verification script).
3. `tests/unit/test_reusable_2d_adaptive_framework.py` (extended to 16 unit tests).
4. `project_coordination/sessions/2026-11-07_gemini-antigravity_F1671_case_b_datacheck_manifest_preparation.md` (this report).
5. `project_coordination/sessions/2026-11-07_chatgpt_review_f1670.md` (archived review response).
