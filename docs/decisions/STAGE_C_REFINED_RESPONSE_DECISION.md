# Stage C — Refined Response Decision (C2F-v3)

**Status:** supported for elastic, pre-peak, and peak RF–U  
**Date:** 2026-07-21  
**Classification:** `stage_c_refined_response_supported`

## Scope of the claim

> The corrected locally refined model reproduces the uniform H1 elastic, pre-peak, and peak-load response. Residual post-peak differences remain and crack-path convergence has not yet been formally assessed.

```text
pipeline execution: pass
automated refined-mesh generation: pass
four-thread UEL qualification: pass
elastic equivalence: pass
peak/pre-peak RF–U equivalence: pass
post-peak equivalence: limited
crack-path equivalence: not yet formally assessed
```

| Role | Mesh |
| --- | --- |
| **Production / report reference** | **uniform H1** (12 064 physical elements) |
| Refined demonstration mesh | C2C-v3 notch-corrected (10 290 physical) |
| Post-peak validation | limited (NRMSE ≈ 24%) |
| Crack-path validation | pending formal matched-state assessment |

## Supported quantitative claims

| Metric | Value |
| --- | ---: |
| Peak-force difference vs H1 | **0.24%** |
| Initial-stiffness difference | **0.061%** |
| Pre-peak RF–U NRMSE | **0.089%** |
| Peak displacement | **0.0058 mm** (identical) |
| Physical-element reduction | **14.7%** (10 290 vs 12 064) |
| Four-thread H0 qualification | pass (serial H0 reproduction) |
| Developed phase-field corridor | present (SDV15 max ≈ 1, n≥0.5 = 2247) |

## Explicit non-claims

Do **not** claim:

- unrestricted full-curve mesh independence;
- equivalent post-peak behavior;
- formal crack-path convergence;
- a multi-fold computational speedup *caused by* refinement alone;
- native Abaqus adaptive remeshing;
- general validity for arbitrary geometries or loading.

## Workflow description (accurate)

> A custom, auxiliary-continuum, MISESERI-driven offline pre-refinement workflow for the layered UEL phase-field model.

```text
auxiliary continuum analysis
→ MISESERI field extraction
→ normalized error marking (relative_MISESERI_threshold = 0.05)
→ localized graded mesh generation
→ U1/U2/CPS4 layer reconstruction
→ deterministic validation
→ four-thread UEL solution
→ comparison against uniform H1
```

Terminology: `relative_MISESERI_threshold = 0.05` means  
`MISESERI / max(MISESERI) > 0.05` — not an absolute Abaqus `errorTarget` claim without literature for that normalization.

## Failed iteration v2 (retain in thesis discussion)

```text
missing exact y=0 mesh line
→ notch faces not reconstructed
→ continuous plate instead of notched plate
→ stiffness +72%
→ no softening
→ nearly uniform low SDV15
```

Job: `1376444.mmaster02` — preserved as failed-design evidence (not overwritten).

## Correction path to v3

```text
geometry audit
→ exact y=0 restored
→ doubled notch faces reconstructed
→ elastic probe error 0.083% (D1 1376464)
→ spatial phase-field evolution restored (D3 1376467)
→ final RF–U peak/pre-peak agreement (C2F-v3 1376480)
```

## Job and artifact identity

| Item | Value |
| --- | --- |
| C2F-v3 job | **1376480.mmaster02** |
| Diagnostic D1 | 1376464.mmaster02 |
| Diagnostic D3 | 1376467.mmaster02 |
| Failed C2F-v2 | 1376444.mmaster02 (frozen) |
| Commit at freeze | record via `git rev-parse HEAD` at freeze time |
| Deck | `models/generated/.../H0_refined_layered_v3_notchfix/` |
| ODB | `.../molnar_c2f_v3_refined_final_threads4_1376480.mmaster02/*.odb` |
| RF–U / status | `runs/hpc/stage_c2/recovery/c2f_v3_vs_h1/` |

Hashes of deck/Fortran/ODB/CSV are recorded in  
`runs/hpc/stage_c2/STAGE_C_FINAL_STATUS.md` and the freeze JSON under diagnostics.

## Resources (C2F-v3)

| Resource | Value |
| --- | --- |
| Walltime | 00:16:35 |
| CPU time | 00:50:22 |
| Memory | ~600 MB |
| Parallel | cpus=4, mp_mode=threads |

**Fair walltime comparison** requires a four-thread H1 baseline (serial H1 walltime is not comparable).

## Authority

Supervisor mesh policy: H0 development; H1 production/report; H2-PUB fine RF–U reference only.  
Stage C refined mesh is a **demonstration** of offline MISESERI pre-refinement efficiency, not a replacement of H1 as the production reference.
