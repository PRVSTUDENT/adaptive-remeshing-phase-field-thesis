# Mode-II Current State Dashboard

**Phase:** `MODE2_REPRODUCTION_ACTIVE_HUMAN_AUTHORIZED_PREMEETING`  
**Last Updated:** `2026-10-07T21:15:00+02:00`  
**Current Gate Status:**
- **Gate M2-0 (Model Freeze):** `CLOSED_PASSED`
- **Gate M2-1 (Miehe Formulation Qualification):** `CLOSED_PASSED`
- **Gate M2-2 (Coarse Pre-Analysis Reproduction):** `CLOSED_PASSED` (PBS Job `1410790.mmaster02`, Exit 0, 4,000 incs, 8/8 checks PASS)
- **Gate M2-3 (Native Remeshing & Forensic Audit):** `CLOSED_PASSED` (F1308 classified as `REUSED_EXISTING_MESH_DIAGNOSTIC`; OFAT sweep across {1%, 2%, 3%, 5%} completed; ET_2PCT identified as canonical publication match at 22,530 FEs, $+12.86\%$ vs. paper 19,963 FEs, corridor angle $-53.68^\circ$, bottom exit $x = 0.9304\,\text{mm}$, $r = -0.8202$, $98.65\%$ top-10% zone refinement; 8/8 checks PASS)
- **Gate M2-4 (Adapted Fracture Package Preparation):** `READY_FOR_PREPARATION`
- **Gate M2-5 (Adapted Fracture Solver Execution):** `ON_HOLD_PENDING_SUPERVISOR_DECISION` (Job-2_UEL.inp strictly blocked)

---

## Gate M2-3 Remeshing Sensitivity Summary

| Candidate | errorTarget | Total Elements | Total Nodes | $h_{\text{mean}}$ ($\mu$m) | Corridor Angle | Exit $x$ (mm) | Verdict vs. Paper (19,963 FEs) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **ET_1PCT** | 1.0% | 80,200 | 79,923 | 3.24 | $-68.87^\circ$ | 0.8404 | Over-refined ($+301.7\%$, anomaly ceiling tripped) |
| **ET_2PCT** | 2.0% | **22,530** | **22,642** | **5.83** | **$-53.68^\circ$** | **0.9304** | **Canonical Match ($+12.86\%$, Fig. 6b angle/exit match)** |
| **ET_3PCT** | 3.0% | 10,045 | 10,173 | 8.77 | $-47.29^\circ$ | 0.9739 | Under-refined ($-49.68\%$) |
| **ET_5PCT** | 5.0% | 4,823 | 4,923 | 13.57 | $-48.88^\circ$ | 0.7596 | Severely under-refined ($-75.84\%$) |

---

## Governance & Safety Rules
1. Mode-I meeting release tag `v2026.10.08-supervisor-meeting-mode1-freeze` and UEL hash `CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6` 100% untouched.
2. Strictly NO solver submission of `Job-2_UEL.inp` without explicit human authorization.
