# H-Convergence Scientific Review — Molnar lc = 0.015 mm

Status: `rf_u_analysis_complete_contour_not_assessed`

## 1. Study purpose

Establish successive-mesh RF–displacement convergence for the exact supplementary
Molnar single-notch staggered UEL model at **lc = 0.015 mm**, with H2-PUB at the
publication-reported local crack-path resolution h = 0.001 mm.

## 2. Source provenance

| Case | Solver job | CAE job | Physical N | Measured h [mm] | h/lc |
|---|---|---|---:|---:|---:|
| H0 | 1376154.mmaster02 | 1376236 | 3930 | 0.0049439 | 0.3296 |
| H1 | 1376185.mmaster02 | 1376236 | 12064 | 0.0025 | 0.1667 |
| H2-PUB | 1376186.mmaster02 | 1376236 | 33852 | 0.001 | 0.06667 |

Scientific-input revision: `58d7e3102d76fe0e70e6729457e2c7e90ad131bb`
CAE infrastructure revision: `bd09bc4f33a1415bba70769458d5bbbf218e1592`
CAE completion record: `33aa56fbd68e1ec799d2aece9578bd6471322e62`

H2-PUB reproduces the **publication local resolution**, not an undocumented exact
publication mesh topology (element count 33852 is generated, not forced to ~22000).

## 3. Technical execution summary

| Layer | H0 | H1 | H2-PUB |
|---|---|---|---|
| Abaqus solver | technical pass | technical pass | technical pass |
| First CAE attempts | f-string fail; argv `-cae` fail | argv `-cae` fail | argv `-cae` fail |
| Consolidated CAE 1376236 | **pass** | **pass** | **pass** |
| RF2–U2 package | yes | yes | yes |
| Contour PNG export | failed (viewport API) | failed | failed |

Failed CAE attempts are retained as infrastructure history and are not hidden.

## 4. Curve validation and interpolation

- Units: U2 [mm], RF2 [kN]; sign: positive tension as exported.
- Origin (0,0) included.
- Duplicate U: retain last frame (deterministic).
- Common U interval: **[0, 0.007] mm**
- Grid: **N = 1001** linear points; linear force interpolation.
- Primary pre/post split: **U_split = U_peak(H2-PUB) = 0.0058 mm**
- Initial tangent: least-squares through origin on **0 < U ≤ 0.001 mm** (common).

Curve validation overall: **pass** (see `results/processed/molnar_lc015_h_convergence/CURVE_VALIDATION_REPORT.md`).

## 5. Scalar RF–U metrics

| Case | peak RF2 [kN] | U at peak [mm] | K0 [kN/mm] | area [kN·mm] |
|---|---:|---:|---:|---:|
| H0 | 0.727608 | 0.0061 | 134.72 | 0.00258137 |
| H1 | 0.699604 | 0.0058 | 134.328 | 0.00240049 |
| H2-PUB | 0.696336 | 0.0058 | 134.243 | 0.00235175 |

## 6. Successive-mesh differences (finer = denominator)

| Pair | ΔF_peak | ΔU_peak | full NRMSE | pre-peak NRMSE | post-peak NRMSE |
|---|---:|---:|---:|---:|---:|
| H0 vs H1 | 4.003% | 5.172% | 21.306% | 0.387% | 62.904% |
| H1 vs H2-PUB | 0.469% | 0.000% | 6.011% | 0.106% | 20.206% |

Relative tangent change H0→H1: 0.292%; H1→H2: 0.063%.

**Interpretation:** H1↔H2-PUB peak force (~0.47%) and pre-peak NRMSE (~0.11%)
are very small. Full-curve NRMSE (~6.0%) is dominated by **post-peak** residual
(~20% NRMSE). Therefore RF–U mesh independence is **strongly supported for peak
and pre-peak response**, with a larger post-peak residual that must be stated
when selecting a reference mesh.

## 7. Publication comparison (approximate Fig. 7 lc=0.015 only)

Reference class: `approximate_digitized_publication_reference` (not exact author data).

| Case | full overlap NRMSE | pre NRMSE | post NRMSE | ΔF_peak vs ref |
|---|---:|---:|---:|---:|
| H0 | 25.30% | 11.85% | 114.71% | 5.36% |
| H1 | 18.43% | 12.08% | 72.03% | 1.31% |
| H2-PUB | 15.57% | 12.13% | 51.26% | 0.83% |

Publication agreement is **secondary** to successive-mesh evidence.

## 8. Resource scaling (serial)

| Case | N | walltime | mem | wall/elem [s] |
|---|---:|---|---:|---:|
| H0 | 3930 | 16:29 | 691652 kb | 0.2517 |
| H1 | 12064 | 46:26 | 928364 kb | 0.2309 |
| H2-PUB | 33852 | 02:12:38 | 1802776 kb | 0.2351 |

Empirical log–log slope walltime vs N: **α ≈ 0.968** (serial only; not parallel scalability).

## 9. Scientific classification

| Domain | Classification |
|---|---|
| A. Peak / pre-peak RF–U convergence | **supported** |
| B. Post-peak RF–U convergence | **not fully demonstrated** (full NRMSE ~6%, post-peak ~20%) |
| C. Overall RF–U label | `rf_u_h_convergence_supported` **with post-peak limitation** |
| D. Publication agreement | `publication_agreement_provisional` |
| E. Crack-path / contour | `crack_path_convergence_not_assessed` |

**Safest wording (required in thesis statements):**

> The force–displacement response is effectively mesh-independent between H1
> and H2-PUB for the elastic, pre-peak and peak-load regimes. A noticeable
> post-peak mesh dependence remains and must be retained as a limitation.

Do not claim unrestricted full-curve mesh independence.

## 10. Recommendations

1. **Uniform fine reference (RF–U):** **H2-PUB** (h = 0.001 mm) — conservative publication-scale local resolution.
2. **Intermediate studies:** **H1** (h = 0.0025 mm) — nearly identical peak/pre-peak at ~35% of H2 walltime; not the formal conservative reference.
3. **H0:** not recommended as reference (clear H0→H1 dependence).
4. **Contours:** crack-path h-convergence unassessed until matched-state SDV15 images exist for all three meshes.
5. **Gate A3:** overall **open**. Historical label `reference_data_insufficient` remains defensible. Internal RF–U component status: `rf_u_reference_supported_contour_evidence_pending`.
6. **MISESERI/remeshing:** blocked unless the supervisor accepts or waives missing contour evidence.

Canonical decision record: `docs/decisions/MOLNAR_LC015_H_CONVERGENCE_SCIENTIFIC_DECISION.md`

## 11. Limitations

- Field-output sampling yields 73 RF–U points per case (not every solver increment).
- Contour PNG export failed in CAE job 1376236 (viewport API).
- Publication curve is approximate digitization with uncertainty.
- Thresholds used for wording are provisional descriptive aids, not supervisor-approved gates.
- No multicore scaling claim.

## 12. Current project boundary

```text
Solvers H0/H1/H2: technical pass
Consolidated CAE: complete (authorization consumed)
RF-U h-convergence analysis: complete
Scientific mesh comparison documented: yes
Crack-path convergence: not assessed
PBS/Abaqus/CAE further runs: not authorized without new decision
MISESERI / remeshing / state transfer: blocked
Gate A3: open
```

## 13. Figures and tables

- Tables: `results/tables/molnar_lc015_h_convergence/`
- Figures: `results/figures/molnar_lc015_h_convergence/`
- Processed: `results/processed/molnar_lc015_h_convergence/`
