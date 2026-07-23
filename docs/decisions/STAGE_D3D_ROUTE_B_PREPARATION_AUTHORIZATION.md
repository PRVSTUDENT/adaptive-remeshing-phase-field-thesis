# Stage D3D Route B Preparation Authorization

**Classification:** `stage_d3d_route_b_preparation_authorized`  
**Date:** 2026-07-23  
**Route:** `B_one_d3d_active_set_segment`  

## Decision

**Route B is selected.**

This authorizes **preparation** of one bounded D3D active-set-validity segment from

\[
U_2 = 0.003000000026077032\,\mathrm{mm}
\quad\rightarrow\quad
U_2 = 0.0031\,\mathrm{mm}.
\]

The accepted **6446 / 155** active/free set is retained for this diagnostic
segment only.

## What is authorized

| Item | Status |
|------|--------|
| D3D deck / PBS / static validation preparation | **Authorized** |
| D3D datacheck submission | **Authorized after committed static pass** |
| D3D full segment submission | **Blocked** pending committed datacheck review |
| D3E preparation / submission | **Blocked** |
| Peak / post-peak continuation | **Blocked** |
| Automatic second segment | **Prohibited** |
| Parameter sweep | **Prohibited** |

## Constraints

- Reproduce accepted R4 Steps 1–3 unchanged.
- Append exactly one continuation step.
- Per-frame actual-history KKT reconstruction required.
- No automatic second segment.
- ODB stays in scratch only (no repository copy).
- Do not modify R4 executable, package_compatible_r2, or accepted R4 evidence lanes.

## Machine-readable record

`runs/hpc/stage_d3/fracture_continuation_decision/D3D_ROUTE_B_PREPARATION_AUTHORIZATION.json`

## Parent package

`docs/decisions/STAGE_D3D_D3E_FRACTURE_CONTINUATION_DECISION_PACKAGE.md`  
Classification of the parent package remains `stage_d3d_d3e_decision_package_prepared`.
