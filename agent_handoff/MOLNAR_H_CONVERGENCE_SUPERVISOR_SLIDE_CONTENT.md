# Supervisor Slide Content — Molnar lc = 0.015 mm h-Convergence

Use with figures under `results/figures/molnar_lc015_h_convergence/`.
Do not invent numbers beyond the formal analysis commit `db4c1fa`.

---

## Slide 1 — Mesh family and study setup

**Title:** Controlled h-convergence at lc = 0.015 mm

**Bullets:**

- Exact author-supplied single-notch model (supplementary Molnar deck)
- Three serial meshes, same materials / loading / lc / formulation
- H0: exact supplementary mesh, h ≈ 0.00494 mm, N = 3930
- H1: intermediate, h = 0.0025 mm, N = 12064
- H2-PUB: publication local resolution, h = 0.001 mm, N = 33852
- All three Abaqus solvers: technical pass
- RF–U from consolidated CAE job 1376236 (origin included)

**Visual:** `01_rf_u_h0_h1_h2.png`

**Footer:** No claim of crack-path convergence; contours not assessed.

---

## Slide 2 — RF–U convergence and cost

**Title:** Peak / pre-peak support; post-peak residual

**Table (H1 → H2-PUB):**

| Metric | Change |
|---|---:|
| Peak force | 0.469% |
| Peak displacement | 0% |
| Pre-peak NRMSE | 0.106% |
| Full-curve NRMSE | 6.011% |
| Post-peak NRMSE | 20.206% |

**Also:** H0 → H1 peak force 4.003% (H0 too coarse)

**Cost (serial walltime):** H0 16:29 · H1 46:26 · H2 2:12:38
H1 ≈ 35% of H2 time with nearly same peak/pre-peak.

**Visuals:** `03_rf_u_peak_zoom.png` · `09_walltime_vs_elements.png`

**Safest wording:** effective mesh independence for elastic / pre-peak / peak between H1 and H2-PUB; post-peak dependence remains a limitation.

---

## Slide 3 — Decisions and next route

**Title:** Gate A3 — two decisions requested

**Decision 1 — Reference**
A) Accept H2-PUB · B) Accept H2-PUB provisionally · C) Require more evidence

**Decision 2 — Contours**
A) Mandatory before Gate A3 closes · B) Defer; RF–U enough for conditional MISESERI prep · C) H1+H2 only · D) Other

**If H2 accepted and contours deferred:** freeze H2-PUB; prepare MISESERI plan only (no run yet)
**If contours mandatory:** one CAE-only contour job on existing ODBs (separate authorization)
**If more evidence:** scope only that metric; no auto-submit

**Project recommendation:** H2-PUB = conservative RF–U reference; H1 = intermediate development; H0 not a reference.

**Boundary:** Gate A3 open · no new HPC job today · MISESERI blocked until your decision
