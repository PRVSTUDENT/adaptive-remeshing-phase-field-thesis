# Session Report: F43DUALREBUILD1 Offline Dual-Candidate Mixed CPE3/CPE4 Phase-Field UEL Rebuild for MM and PK5

- **Task ID**: `F43DUALREBUILD1`
- **Agent**: `gemini-antigravity`
- **Date**: `2026-08-09`
- **Starting Commit**: `d9221c4fe6a7468f82b9ba4fd3fc2689fcc2cda5`
- **Status**: `complete_pass`
- **Gate C1 Localization**: `PASS`
- **Best Adaptive Candidate**: `F43REM4_MM`
- **Best Resolution/Efficiency Compromise**: `F43REM4_PK5`
- **Final Selected Candidate**: `none`
- **Gate C1 Phase-Field Resolution**: `HOLD`
- **MM Rebuilder**: `PASS`
- **PK5 Rebuilder**: `PASS`
- **Ready for Dual-Candidate Dry Test**: `true`
- **Recommended Next Stage**: `awaiting_human_direction_for_dry_test_execution_authorization`

---

## 1. Executive Summary

This session executed Task `F43DUALREBUILD1`: the offline, deterministic reconstruction of both `F43REM4_MM` and `F43REM4_PK5` physical candidate meshes into 3-layer mixed CPE3/CPE4 Phase-Field UEL input decks.

1. **Rebuild Formulation**:
   - Both candidates were rebuilt using an identical deterministic Python rebuilder (`scripts/model_generation/rebuild_f43_mixed_uel_deck.py`).
   - Physical mesh node coordinates, connectivity, boundary sets, and kinematic shear coupling equations were preserved with zero distortion or conversion.
2. **Rebuilt Decks Generated**:
   - `F43UEL_MM_REBUILT.inp`: **6,618 total layered elements** (2,137 U1, 2,137 U2, 69 U3, 69 U4, 2,137 CPE4, 69 CPE3). SHA256: `b6642e77655f4f953485cba1274dd0aaae220a327ebf2ac334b67e425673af7f`.
   - `F43UEL_PK5_REBUILT.inp`: **14,682 total layered elements** (4,766 U1, 4,766 U2, 128 U3, 128 U4, 4,766 CPE4, 128 CPE3). SHA256: `01b2914ee00717af82d9c8bf4437d4b5aebdc6c0ccd0c76423052ed40606b0d6`.
3. **Static Validation & Fairness**:
   - 100% static validation passed for both candidates (valid element types, unique IDs, positive signed areas, domain area $= 1.00000000\text{ mm}^2$, exact set and equation mapping).
   - Cross-candidate fairness proved: both models share identical material constants ($l_0 = 0.015\text{ mm}$, $G_c = 0.0027\text{ kN/mm}$, $E = 210.0\text{ kN/mm}^2$, $\nu = 0.3$, $k = 1.0\times 10^{-7}$), user subroutine, boundary conditions, and solver controls.
4. **Dry-Test Packages Staged**:
   - Isolated dry-test packages staged under `remesh_sensitivity_batch/dry_test_mm/` and `remesh_sensitivity_batch/dry_test_pk5/`.
   - Zero HPC jobs submitted.

---

## 2. Rebuilt Model Architecture and Counts

| Attribute | Candidate MM (`F43REM4_MM`) | Candidate PK5 (`F43REM4_PK5`) |
| :--- | :--- | :--- |
| **Predecessor Job ID** | `1385575.mmaster02` | `1385574.mmaster02` |
| **Physical Deck SHA-256** | `d404356d5ce9a474...` | `87ab62c411f8d14e...` |
| **Physical Part Nodes** | 2,294 | 4,998 |
| **Physical Elements ($N_{\text{PHYS}}$)** | 2,206 | 4,894 |
| **Physical Quads (CPE4)** | 2,137 | 4,766 |
| **Physical Triangles (CPE3)** | 69 | 128 |
| **Total Domain Area** | 1.00000000 mm² | 1.00000000 mm² |
| **Layer 1: Phase Elements** | 2,206 (2,137 U1 + 69 U3) | 4,894 (4,766 U1 + 128 U3) |
| **Layer 2: Displacement Elements** | 2,206 (2,137 U2 + 69 U4) | 4,894 (4,766 U2 + 128 U4) |
| **Layer 3: Facsimile Elements** | 2,206 (2,137 CPE4 + 69 CPE3) | 4,894 (4,766 CPE4 + 128 CPE3) |
| **Total Layered Elements** | **6,618** | **14,682** |
| **Rebuilt Deck Name** | `F43UEL_MM_REBUILT.inp` | `F43UEL_PK5_REBUILT.inp` |
| **Rebuilt Deck SHA-256** | `b6642e77655f4f953485cba1274dd0aaae220a327ebf2ac334b67e425673af7f` | `01b2914ee00717af82d9c8bf4437d4b5aebdc6c0ccd0c76423052ed40606b0d6` |
| **Static Validation Result** | **`ALL PASS`** | **`ALL PASS`** |

---

## 3. Entity Classification Table

| Source Entity | Classification | Treatment in Rebuilt Deck |
| :--- | :--- | :--- |
| `PlatePart` Nodes | `preserved` | Exact $(x, y)$ coordinates written to Part `*Node` block |
| Assembly RP Node | `preserved` | Node 1 at $(0.0, 0.6, 0.0)$ written to Assembly `*Node` block |
| `Nset, nset=RP` | `preserved` | Points to Assembly RP Node |
| `Nset, nset=bottom_nodes` | `preserved` | Preserved Part boundary node list on $y = -0.5$ |
| `Nset, nset=top_nodes` | `preserved` | Preserved Part boundary node list on $y = +0.5$ |
| `Elset, elset=bottom_nodes` | `transformed` | Mapped to facsimile output layer |
| `Elset, elset=top_nodes` | `transformed` | Mapped to facsimile output layer |
| `Equation` (Shear Coupling) | `preserved` | `top_nodes, 1, 1.` coupled to `RP, 1, -1.` |
| `Material, name=Steel` | `not_applicable` | Replaced by UEL formulation and passive UMAT |
| `Solid Section` standard | `not_applicable` | Replaced by `*UEL Property` and facsimile sections |
| `Boundary` bottom_fix | `preserved` | `bottom_nodes, 1, 1` and `bottom_nodes, 2, 2` |
| `Boundary` top_vertical_fix| `preserved` | `top_nodes, 2, 2` |
| `Boundary` RP shear load | `preserved` | `RP, 1, 1, 0.001` in Step-1 |

---

## 4. Cross-Candidate Formulation Fairness

- $l_0 = 0.015\text{ mm}$ (identical)
- $G_c = 0.0027\text{ kN/mm} = 2.7\text{ N/mm}$ (identical)
- $t = 1.0\text{ mm}$ (identical)
- $E = 210.0\text{ kN/mm}^2 = 210,000\text{ MPa}$ (identical)
- $\nu = 0.3$ (identical)
- $k = 1.0\times 10^{-7}$ (identical)
- Passive Facsimile $E_{\text{passive}} = 1.0\times 10^{-11}$, $\nu = 0.3$, Depvar = 18 (identical)
- User Subroutine: `models/generated/mode_ii/f42_mixed_element_uel/f42_mixed_uel.for` (SHA256: `5dc005383773a2923b943024b97dc15590a4f220e319fd289c891b15c30844f3`, identical)
- Step definition, solver controls, output requests: 100% semantically equivalent.

---

## 5. Reference Availability Audit

- `uniform_reference_available = false`
- `future_phase_field_comparison_blocked_by = uniform_reference_not_yet_frozen`
- **Context**: While preliminary uniform fine sweeps exist (e.g. `H1` jobs `1379481`, `1379482`, `1379483`, `1379484` and `H2` job `1379966`), a formal Gate-B1 qualified uniform reference convergence curve and crack-path baseline has not yet been frozen as an accepted comparison benchmark.

---

## 6. Unit Testing Summary

- Test module: `tests/unit/test_f43_dual_candidate_rebuild.py`
- Test count: 9 tests
- Results: **9 passed, 0 failures, 0 errors (0.273s)**
- Full Stage C regression suite: **45 passed, 0 failures, 0 errors (0.851s)**

---

## 7. Required Reporting Extraction

```text
best_adaptive_candidate = MM
best_resolution_efficiency_compromise = PK5
final_selected_candidate = none
Gate_C1_localization = PASS
Gate_C1_phase_field_resolution = HOLD
MM_rebuilder = PASS
PK5_rebuilder = PASS
MM_rebuilt_SHA = b6642e77655f4f953485cba1274dd0aaae220a327ebf2ac334b67e425673af7f
PK5_rebuilt_SHA = 01b2914ee00717af82d9c8bf4437d4b5aebdc6c0ccd0c76423052ed40606b0d6
MM_total_layered_elements = 6618
PK5_total_layered_elements = 14682
uniform_reference_available = false
ready_for_dual_candidate_dry_test = true
next_stage = awaiting_human_direction_for_dry_test_execution_authorization
```

---

## 8. Authority Boundary

- `execution_authorized`: `false`
- `submission_approved`: `false`
- `maximum_jobs_now`: `0`
- `qsub_called`: `false`
- `new_HPC_submissions`: `0`
- `running_jobs`: `0`
- `queued_jobs`: `0`
