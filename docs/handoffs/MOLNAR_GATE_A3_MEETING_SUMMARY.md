# Molnár Gate A3 Meeting Summary (lc = 0.015 mm RF–U)

**Purpose:** (1) accept H2-PUB as the uniform RF–U reference mesh for later work; (2) decide whether matched-state SDV15/crack-path contours are mandatory before the benchmark-reproduction stage, Gate A3, can be accepted.
**Evidence commit:** `db4c1fadfb3a4f7b33b6b653c261e6da90036c48`
**No additional simulations are requested at this stage.**

## Definitions used in this summary

- **H0:** original author-supplied supplementary mesh, with local element size \(h \approx 0.00494\,\mathrm{mm}\).
- **H1:** intermediate refined mesh, with \(h = 0.0025\,\mathrm{mm}\).
- **H2-PUB:** finest mesh, generated using the publication-reported local resolution \(h = 0.001\,\mathrm{mm}\). It uses the published resolution, but not necessarily the exact published mesh topology.
- **\(N\):** number of physical finite elements in the model. It does not include the additional layered visualization/solution elements.
- **\(h\):** local element size in the expected crack-propagation region.
- **\(l_c\):** phase-field regularization length scale; here \(l_c=0.015\,\mathrm{mm}\).
- **RF2 and U2:** reaction force and prescribed displacement in the loading direction.
- **NRMSE:** normalized root-mean-square difference between two force–displacement curves.
- **SDV15:** phase-field fracture variable, where \(0\) represents intact material and \(1\) represents fully broken material.
- **Pre-peak:** response before the maximum reaction force.
- **Post-peak:** response after the maximum reaction force.
- **Gate A3:** the project’s benchmark-reproduction acceptance gate.
- **MISESERI:** the Abaqus stress-discretization error indicator intended for the later mesh-refinement workflow.

## Status

```text
Solvers H0/H1/H2-PUB: technical pass
RF–U packages: complete
Peak / pre-peak h-convergence: supported
Post-peak h-convergence: not fully demonstrated
Crack-path / SDV15 contours: not assessed
Gate A3: open — supervisor decision pending
```

## Mesh family

| Mesh | Local element size h [mm] | Physical elements N | Description |
|---|---:|---:|---|
| H0 | 0.00494 | 3,930 | Original author-supplied supplementary mesh |
| H1 | 0.00250 | 12,064 | Intermediate refined mesh |
| H2-PUB | 0.00100 | 33,852 | Fine mesh using the publication-reported local resolution |

## RF–U successive differences

| Pair | ΔF_peak | ΔU_peak | pre-peak NRMSE | full NRMSE | post-peak NRMSE |
|---|---:|---:|---:|---:|---:|
| H0→H1 | 4.003% | 5.172% | 0.387% | 21.306% | 62.904% |
| H1→H2 | **0.469%** | **0%** | **0.106%** | **6.011%** | **20.206%** |

Peak RF2: H0 0.727608 · H1 0.699604 · H2-PUB 0.696336 kN
U_peak: H0 0.00610 · H1/H2 0.00580 mm

## Cost (serial)

| Mesh | Walltime | Memory |
|---|---|---|
| H0 | 00:16:29 | ~0.68 GB |
| H1 | 00:46:26 | ~0.91 GB |
| H2-PUB | 02:12:38 | ~1.76 GB |

H1 ≈ **35%** of H2 walltime with nearly the same peak/pre-peak responses.

## Figure for the meeting

Primary overlay: `results/figures/molnar_lc015_h_convergence/01_rf_u_h0_h1_h2.png`

## Decisions requested

**1. Uniform RF–U reference**

- □ A Accept H2-PUB as the uniform RF–U reference
- □ B Accept H2-PUB provisionally (subject to contour evidence)
- □ C Do not accept; specify additional required evidence

**2. Contour requirement**

- □ A Contours mandatory before the benchmark-reproduction stage, Gate A3, can be accepted
- □ B Contours deferred; RF–U evidence sufficient for conditional preparation of the later MISESERI-based mesh-refinement workflow
- □ C Contours required only for H1 and H2-PUB
- □ D Other (please specify)

## Recommended conclusion (project)

> The intermediate mesh H1 and the fine mesh H2-PUB produce nearly identical elastic, pre-peak and peak-load force–displacement responses. H2-PUB is recommended as the conservative uniform reference because it uses the publication-reported local crack-path resolution of \(h=0.001\,\mathrm{mm}\). H1 may be used for intermediate development studies at lower computational cost. Noticeable differences remain after peak load, and convergence of the crack path has not yet been assessed.

## Boundary

```text
No additional simulations are requested at this stage
No MISESERI / remeshing / state transfer until Decision 1+2
```

A detailed review is available on request.
Professor-facing PDF: `docs/handoffs/MOLNAR_GATE_A3_MEETING_SUMMARY.pdf`
