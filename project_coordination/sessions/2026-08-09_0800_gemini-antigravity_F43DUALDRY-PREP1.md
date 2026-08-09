# Session Report: F43DUALDRY-PREP1 Dual-Candidate Mixed-UEL Dry-Test Preparation and Qualification

- **Task ID**: `F43DUALDRY-PREP1`
- **Agent**: `gemini-antigravity`
- **Date**: `2026-08-09`
- **Starting Commit**: `d9221c4fe6a7468f82b9ba4fd3fc2689fcc2cda5`
- **P Commit SHA**: `2b9a9809ad1848c65cbc4b72231e1ebd2abd4df6`
- **P Tag**: `P43DUALDRY1`
- **Status**: `complete_pass`
- **Gate C1 Localization**: `PASS`
- **Best Adaptive Candidate**: `F43REM4_MM`
- **Best Resolution/Efficiency Compromise**: `F43REM4_PK5`
- **Final Selected Candidate**: `none`
- **Gate C1 Phase-Field Resolution**: `HOLD`
- **MM Static Validation**: `PASS`
- **PK5 Static Validation**: `PASS`
- **Cross-Candidate Fairness**: `PASS`
- **MM All Four UEL Branches Present**: `true`
- **PK5 All Four UEL Branches Present**: `true`
- **Uniform Reference Available**: `false`
- **Authorization Ready for Dual Dry Test**: `true`
- **Execution Authorized**: `false`
- **Submission Approved**: `false`
- **Maximum Jobs Now**: `0`
- **Qsub Called**: `false`
- **HPC Submissions**: `0`

---

## 1. Executive Summary

Task `F43DUALDRY-PREP1` performed the technical preparation, static contract qualification, UEL branch coverage audit, and fresh P/Q lineage creation (`P43DUALDRY1` -> `Q43DUALDRY1`) for the upcoming two-job technical dry test of candidate rebuilt decks `F43UEL_MM_REBUILT.inp` and `F43UEL_PK5_REBUILT.inp`.

1. **Frozen Rebuilt Decks & UEL Subroutine**:
   - `MM` Rebuilt Deck: `F43UEL_MM_REBUILT.inp` (SHA256: `b6642e77655f4f953485cba1274dd0aaae220a327ebf2ac334b67e425673af7f`).
   - `PK5` Rebuilt Deck: `F43UEL_PK5_REBUILT.inp` (SHA256: `01b2914ee00717af82d9c8bf4437d4b5aebdc6c0ccd0c76423052ed40606b0d6`).
   - Mixed UEL Subroutine: `f42_mixed_uel.for` (SHA256: `5dc005383773a2923b943024b97dc15590a4f220e319fd289c891b15c30844f3`).
2. **Branch Coverage & Passive Facsimile Contract**:
   - Both models statically exercise all 4 UEL branches: `U1` (quad phase), `U2` (quad disp), `U3` (tri phase), and `U4` (tri disp).
   - Passive facsimile elements (`CPE4` and `CPE3`) with $E_{\text{passive}} = 1.0\times 10^{-11}$, $\nu = 0.3$, Depvar = 18 are present solely for visualization and provide zero parasitic stiffness.
3. **Detached Exact-P Qualification**:
   - Executed on `tu_freiberg` in an isolated detached worktree at exact `P43DUALDRY1` (`2b9a9809ad1848c65cbc4b72231e1ebd2abd4df6`).
   - Toolchains verified: `gcc/11.4.0`, `intel/2024.2.0`, `abaqus/2023`, `python/gcc/11.4.0/3.11.7`.
   - Full repository unit discovery suite: **599 passed, 0 failures, 0 errors, 17 skips (`OK`) in 7.915s**.
   - Natural post-test cleanliness: `git status --porcelain=v1` was completely empty, `git diff` clean.

---

## 2. Package Architecture and PBS Resource Contract

| Candidate | Package Directory | Rebuilt Deck | Subroutine | PBS Script | Submission Wrapper | Queue / Resources |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **MM** | `dry_test_mm/` | `F43UEL_MM_REBUILT.inp` | `f43_mixed_uel.for` | `F43DRY_MM.pbs` | `submit_f43dry_mm.sh` | `entry_imfdfkmq`, 1 CPU, 8 GB, 00:30:00 |
| **PK5** | `dry_test_pk5/` | `F43UEL_PK5_REBUILT.inp` | `f43_mixed_uel.for` | `F43DRY_PK5.pbs` | `submit_f43dry_pk5.sh` | `entry_imfdfkmq`, 1 CPU, 8 GB, 00:30:00 |

### 2.1 Branch Element Counts
- **MM (`F43DRY_MM`)**:
  - `U1` (Quad Phase): 2,137 elements
  - `U2` (Quad Disp): 2,137 elements
  - `U3` (Tri Phase): 69 elements
  - `U4` (Tri Disp): 69 elements
  - `CPE4` (Facsimile Quad): 2,137 elements
  - `CPE3` (Facsimile Tri): 69 elements
  - **Total Layered Elements**: **6,618**
- **PK5 (`F43DRY_PK5`)**:
  - `U1` (Quad Phase): 4,766 elements
  - `U2` (Quad Disp): 4,766 elements
  - `U3` (Tri Phase): 128 elements
  - `U4` (Tri Disp): 128 elements
  - `CPE4` (Facsimile Quad): 4,766 elements
  - `CPE3` (Facsimile Tri): 128 elements
  - **Total Layered Elements**: **14,682**

---

## 3. Cross-Candidate Formulation Fairness Audit

- **Elastic Modulus**: $E = 210.0\text{ kN/mm}^2$ (identical)
- **Poisson's Ratio**: $\nu = 0.3$ (identical)
- **Fracture Energy**: $G_c = 0.0027\text{ kN/mm} = 2.7\text{ N/mm}$ (identical)
- **Length Scale**: $l_0 = 0.015\text{ mm}$ (identical)
- **Residual Stiffness**: $k = 1.0\times 10^{-7}$ (identical)
- **Thickness**: $t = 1.0\text{ mm}$ (identical)
- **User Subroutine**: `f42_mixed_uel.for` (SHA256: `5dc005383773a2923b943024b97dc15590a4f220e319fd289c891b15c30844f3`, identical)
- **Passive Facsimile**: $E_{\text{passive}} = 1.0\times 10^{-11}$, $\nu = 0.3$, Depvar = 18 (identical)
- **Step / BC / Equations / Load**: Exact semantic equivalence (applied RP shear $u_x = 0.001\text{ mm}$ in Step-1).
- **Scope of Differences**: Strictly confined to mesh topology, node coordinates, and element labels arising from $N_{\text{PHYS}}$ offsets.

---

## 4. Reference Availability & Next Stages

- `uniform_reference_available = false`
- `future_scientific_comparison_blocked_by = uniform_reference_not_yet_frozen`
- **Clarification**: Missing uniform reference does not block the technical dry tests (`F43DRY_MM` and `F43DRY_PK5`). It only blocks final scientific fracture comparison and production mesh selection.

```text
Sequence Ahead:
1. Dual technical dry-test authorization & execution (2 jobs: F43DRY_MM, F43DRY_PK5)
2. Technical closeout (verify UEL branch compilation, loading, initial elastic stiffness)
3. Freeze / qualify Mode-II uniform reference
4. Scientific phase-field production runs
5. Force-displacement, energy, crack path, and runtime comparison
6. Final thesis mesh selection
```

---

## 5. Authority Boundary

- `authorization_ready_for_dual_dry_test`: `true`
- `execution_authorized`: `false`
- `submission_approved`: `false`
- `maximum_jobs_now`: `0`
- `qsub_called`: `false`
- `HPC_submissions`: `0`
- `running_jobs`: `0`
- `queued_jobs`: `0`
