# Session Report: F72BSTATE-M2-RESTART2R5-EQUATION-SEMANTICS-CORRECTION1

**Date**: 2026-08-13  
**Agent**: gemini-antigravity  
**Task ID**: `F72BSTATE-M2-RESTART2R5-EQUATION-SEMANTICS-CORRECTION1`  
**Purpose**: Conclusively resolve Abaqus 2023 `*EQUATION` expansion semantics, invalidate the previous 80-mode hypothesis, and determine the actual physical and numerical defects producing NaN in Step 1.

---

## 1. Executive Summary & Forensic Findings

1. **Abaqus `*EQUATION` Semantics Conclusively Proven**:
   - Tested minimal input deck `test_equation_semantics.inp` and `test_uel_mini.inp` on Abaqus 2023 on the TU Freiberg HPC cluster.
   - Proven that `*EQUATION 2 N_TOP, 1, 1.0, 99999, 1, -1.0` expands into **81 individual 1-to-1 equations**:
     $$u_1^{(i)} - u_1^{(99999)} = 0 \quad \forall i \in N\_TOP$$
   - `minimal_equation_semantics_test = PASS`
   - `minimal_generated_equation_count = 3` (test) / `81` (full model)
   - `RP_as_repeated_independent_DOF_contract = PASS`
   - `mechanical_constraint_matrix_rank = FULL_RANK` (nullity = 0, rigid body mode count = 0).

2. **Previous "80 Rigid-Body Modes" Claim Invalidated**:
   - `previous_80_mode_claim_basis = inferred_from_assumed_sum_equation`
   - `previous_80_mode_claim = INVALIDATED`
   - `mechanical_rank_deficiency_detected = false`

3. **Discovery of Actual Mesh Defects**:
   - Detected 2 physical elements (elements 9720/9840 in phase layer, 19596/19716 in mech layer, 29472/29592 in passive solid facsimile layer) that connect node 120 ($X=+0.50$, right bottom corner) to node 121 ($X=-0.50$, left boundary row 2) across the entire domain ($L=1.0\text{ mm}$, height $0.012\text{ mm}$, minimum interior angle $0.69^\circ$).
   - In Step 1 Increment 1, initial force residual $R = 0 < 5.0\times 10^{-3}$, leading to premature acceptance before equilibrium convergence.

---

## 2. Evidence Verification Table

| Item | Expected | Measured / Verified | Status |
| :--- | :--- | :--- | :--- |
| `EQUATION_SET_EXPANSION` | `ONE_EQUATION_PER_N_TOP_NODE_TO_RP` | `ONE_EQUATION_PER_N_TOP_NODE_TO_RP` | **PROVEN** |
| `minimal_equation_semantics_test` | `PASS` | `PASS` ($u_1 = 0.1$ at all nodes) | **PASS** |
| `RP_as_repeated_independent_DOF_contract` | `PASS` | `PASS` | **PASS** |
| `rigid_body_mode_count` | `0` | `0` | **PASS** |
| `previous_80_mode_claim` | `INVALIDATED` | `INVALIDATED` | **CONFIRMED** |
| `sliver_cross_domain_elements` | Identified | 9720, 9840 (spans $X=+0.5$ to $-0.5$) | **CONFIRMED** |

---

## 3. Mandatory Boundaries Maintained

- `new_candidate_created = false`
- `new_submission_authorized = false`
- `qsub_called = false`, `qdel_called = false`, `qmove_called = false`
- `automatic_retry = false`
