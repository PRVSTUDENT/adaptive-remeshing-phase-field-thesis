# Molnar Gate A3 Supervisor Decision Package

Status: `supervisor_decision_required`
Package focus: **lc = 0.015 mm RF–U h-convergence and uniform reference selection**
Analysis revision: `db4c1fadfb3a4f7b33b6b653c261e6da90036c48`
No new PBS / Abaqus / CAE run is requested by this package.

Related frozen scientific decision:
`docs/decisions/MOLNAR_LC015_H_CONVERGENCE_SCIENTIFIC_DECISION.md`

---

## A. Study completed

A controlled **serial** h-convergence study was completed for the **exact author-supplied supplementary** single-notch Molnar model at:

```text
lc = 0.015 mm
```

| Layer | Result |
|---|---|
| H0 / H1 / H2-PUB Abaqus solvers | technical pass |
| Consolidated CAE RF–U extraction (`1376236`) | pass for all three |
| Formal RF–U successive-mesh analysis | complete |
| Matched-state SDV15 / crack-path contours | **not assessed** (export incomplete) |

Scientific input revision for the mesh family:
`58d7e3102d76fe0e70e6729457e2c7e90ad131bb`

This package does **not** re-open candidate-v2 SDV15 irreversibility as the primary decision. That remains documented separately under the paper-matched route. The decisions requested here concern **uniform RF–U reference selection** for the **lc = 0.015 mm** supplementary h-convergence chain.

---

## B. Mesh family

| Case | Role | Measured local h | Physical elements | Solver job |
|---|---|---:|---:|---|
| **H0** | Exact author supplementary mesh | ≈ 0.00494 mm | 3930 | `1376154.mmaster02` |
| **H1** | Intermediate refinement | 0.0025 mm | 12064 | `1376185.mmaster02` |
| **H2-PUB** | Publication-scale local resolution | 0.001 mm | 33852 | `1376186.mmaster02` |

H2-PUB targets the **publication-reported local crack-path resolution** h = 0.001 mm. The element count (33852) is generated and is **not** forced to the approximate paper statement of ~22000 elements.

---

## C. Key RF–U results

### Scalar peaks

| Case | peak RF2 [kN] | U_peak [mm] |
|---|---:|---:|
| H0 | 0.727608 | 0.00610 |
| H1 | 0.699604 | 0.00580 |
| H2-PUB | 0.696336 | 0.00580 |

### Successive-mesh differences (finer mesh = denominator)

| Pair | ΔF_peak | ΔU_peak | full NRMSE | pre-peak NRMSE | post-peak NRMSE |
|---|---:|---:|---:|---:|---:|
| H0 → H1 | **4.003%** | **5.172%** | **21.306%** | **0.387%** | **62.904%** |
| H1 → H2-PUB | **0.469%** | **0%** | **6.011%** | **0.106%** | **20.206%** |

Initial stiffness change H1 → H2-PUB ≈ **0.06%**.

### Clear statements

- Peak and **pre-peak** RF–U h-convergence between H1 and H2-PUB are **supported**.
- **Post-peak** mesh dependence **remains** (full-curve NRMSE ≈ 6% is post-peak-driven).
- **Do not** claim unrestricted full-curve mesh independence.
- **Crack-path / matched-state SDV15** convergence is **not assessed**.

**Safest wording:**

> The force–displacement response is effectively mesh-independent between H1 and H2-PUB for the elastic, pre-peak and peak-load regimes. A noticeable post-peak mesh dependence remains and must be retained as a limitation.

Primary overlay figure:
`results/figures/molnar_lc015_h_convergence/01_rf_u_h0_h1_h2.png`
(also: `02_rf_u_with_fig7_lc015.png`, `03_rf_u_peak_zoom.png`)

---

## D. Publication comparison

Reference used: **approximate digitized** Molnar Fig. 7 curve for **lc = 0.015 mm only**
Class: `approximate_digitized_publication_reference` — **not** exact author numerical data.
The **lc = 0.0075** curve was **not** used.

| Case | Full-overlap NRMSE vs approx. Fig. 7 lc=0.015 | ΔF_peak vs ref |
|---|---:|---:|
| H0 | ~25.3% | ~+5.4% |
| H1 | ~18.4% | ~+1.3% |
| H2-PUB | ~15.6% | ~+0.8% |

Publication agreement is **provisional** and secondary to successive-mesh evidence.

---

## E. Computational cost (serial)

| Case | N | Walltime | Peak memory (approx.) |
|---|---:|---|---|
| H0 | 3930 | 00:16:29 | ~0.68 GB |
| H1 | 12064 | 00:46:26 | ~0.91 GB |
| H2-PUB | 33852 | 02:12:38 | ~1.76 GB |

H1 uses about **35% of H2-PUB walltime** while nearly matching H2 peak and pre-peak RF–U response.

---

## F. Remaining limitations

1. Post-peak RF–U residual between H1 and H2-PUB (~20% post-peak NRMSE).
2. Matched-state SDV15 / crack-path contour exports incomplete for all three meshes.
3. Fig. 7 comparison is approximate digitization only.
4. Supervisor-approved numerical tolerances are not yet fixed.
5. Candidate-v2 SDV15 accepted-increment irreversibility remains a **separate** documented issue for the paper-matched route (not the primary request of this package).

---

## G. Decisions requested (exactly two)

### Decision 1 — Uniform RF–U reference

Please choose **one**:

| Option | Meaning |
|---|---|
| **A** | Accept **H2-PUB (h = 0.001 mm)** as the uniform RF–U reference. |
| **B** | Accept **H2-PUB provisionally**, subject to contour evidence. |
| **C** | Do **not** accept; specify additional required evidence. |

**Project recommendation:** Option **A** or **B**, with H2-PUB as the conservative RF–U reference; H1 retained for intermediate development; H0 not a final reference.

### Decision 2 — Contour requirement

Please choose **one**:

| Option | Meaning |
|---|---|
| **A** | Matched-state SDV15 / crack-path contours are **mandatory** before Gate A3 closes. |
| **B** | Contours may be **deferred**; RF–U evidence is sufficient to proceed **conditionally** to MISESERI preparation. |
| **C** | Contours required only for **H1 and H2-PUB**. |
| **D** | Other requirement specified by the supervisor. |

**Do not infer the supervisor answer.** No route is executed by this package alone.

---

## H. Consequences of each route

### Route A — H2-PUB accepted and contours waived/deferred (Decision 1 A/B + Decision 2 B)

- Gate A3 may be **closed** or **conditionally waived** (supervisor wording required).
- Freeze **H2-PUB** as the RF–U uniform reference.
- Allow **preparation only** of Stage C / MISESERI workflow documentation.
- **No solver/MISESERI execution** until a separate submission plan is approved.

### Route B — Contours mandatory (Decision 2 A or C)

- Gate A3 remains **open**.
- Prepare a **contour-only** postprocessing repair using **existing** H0/H1/H2 ODBs.
- **No solver rerun**.
- Request separate authorization for **one CAE-only contour extraction job**.

### Route C — Additional numerical evidence (Decision 1 C or Decision 2 D)

- Document the exact requested metric.
- Prepare a new scoped plan.
- **Do not submit** anything automatically.

---

## Current project boundary

```text
H2-PUB RF–U reference: recommended (awaiting supervisor Decision 1)
H1 intermediate mesh: recommended
Post-peak convergence: limited / not fully demonstrated
Crack-path convergence: not assessed
Gate A3: supervisor decision pending
  overall: open
  historical label: reference_data_insufficient
  RF–U component: rf_u_reference_supported_contour_evidence_pending
New HPC authorization: none
MISESERI / remeshing / state transfer: blocked
```

## Evidence paths

- Review: `runs/hpc/molnar_lc015_h_convergence/comparison/H_CONVERGENCE_SCIENTIFIC_REVIEW.md`
- Tables: `results/tables/molnar_lc015_h_convergence/`
- Figures: `results/figures/molnar_lc015_h_convergence/`
- Frozen scientific decision: `docs/decisions/MOLNAR_LC015_H_CONVERGENCE_SCIENTIFIC_DECISION.md`
