# Molnar Gate A3 Meeting Summary (lc = 0.015 mm RF–U)

**Purpose:** two explicit supervisor decisions — (1) RF–U uniform reference, (2) contour requirement.
**Evidence commit:** `db4c1fadfb3a4f7b33b6b653c261e6da90036c48`
**No new job is requested today.**

## Status

```text
Solvers H0/H1/H2-PUB: technical pass
RF–U packages: complete (CAE job 1376236)
Peak / pre-peak h-convergence: supported
Post-peak h-convergence: not fully demonstrated
Crack-path / SDV15 contours: not assessed
Gate A3: open — supervisor decision pending
```

## Mesh family

| Case | h | N | Role |
|---|---:|---:|---|
| H0 | ≈0.00494 mm | 3930 | exact supplementary |
| H1 | 0.0025 mm | 12064 | intermediate |
| H2-PUB | 0.001 mm | 33852 | publication local resolution |

## RF–U successive differences

| Pair | ΔF_peak | ΔU_peak | pre-peak NRMSE | full NRMSE | post-peak NRMSE |
|---|---:|---:|---:|---:|---:|
| H0→H1 | 4.003% | 5.172% | 0.387% | 21.306% | 62.904% |
| H1→H2 | **0.469%** | **0%** | **0.106%** | **6.011%** | **20.206%** |

Peak RF2: H0 0.727608 · H1 0.699604 · H2-PUB 0.696336 kN
U_peak: H0 0.00610 · H1/H2 0.00580 mm

## Cost (serial)

| Case | Walltime | Memory |
|---|---|---|
| H0 | 00:16:29 | ~0.68 GB |
| H1 | 00:46:26 | ~0.91 GB |
| H2-PUB | 02:12:38 | ~1.76 GB |

H1 ≈ **35%** of H2 walltime with nearly the same peak/pre-peak response.

## Figure for the meeting

Primary overlay: `results/figures/molnar_lc015_h_convergence/01_rf_u_h0_h1_h2.png`
Optional peak zoom: `03_rf_u_peak_zoom.png` · vs Fig.7 lc=0.015: `02_rf_u_with_fig7_lc015.png`

## Decisions requested

**1. Uniform RF–U reference**
A) Accept H2-PUB · B) Accept H2-PUB provisionally (contours pending) · C) Do not accept (specify evidence)

**2. Contour requirement**
A) Contours mandatory before Gate A3 closes · B) Contours deferred; proceed conditionally to MISESERI prep · C) Contours only H1+H2 · D) Other

## Recommended conclusion (project)

> The H1 and H2-PUB meshes provide nearly identical elastic, pre-peak and peak-load response. H2-PUB is recommended as the conservative uniform RF–U reference. Post-peak differences and the absence of matched-state contour evidence remain explicit limitations.

## Boundary

```text
No PBS / Abaqus / CAE today
No MISESERI / remeshing / state transfer until Decision 1+2
```

Full package: `docs/decisions/MOLNAR_GATE_A3_SUPERVISOR_REVIEW.md`
