# Molnar Gate A3 Status Matrix

Status: `gate_a3_conditionally_accepted_rf_u`  
Internal RF–U component status: `rf_u_reference_accepted_contour_deferred`  
Contour tag: `contour_validation_deferred`  
Stage C: `stage_c_miseseri_preparation_authorized`  
Historical overall label retained for full Stage A narrative: `reference_data_insufficient` (full unconditional closure still not claimed)  
Overall Gate A3 for **RF–U validation use**: **conditionally accepted** (Decisions **1A** and **2B**)

Authority: `docs/decisions/MOLNAR_GATE_A3_SUPERVISOR_DECISION_1A_2B.md`  
Evidence base for the RF–U h-convergence rows: analysis commit `db4c1fadfb3a4f7b33b6b653c261e6da90036c48`.

| Component | Evidence | Status | Blocker | Required decision | Next action |
|---|---|---|---|---|---|
| Environment / toolchain | HPC smoke 1374531/1374533; modules gcc/intel/abaqus 2023 | complete | none | none | retain stack |
| One-element technical validation | local Molnar one-element technical pass | complete | none | none | none |
| One-element scientific validation | source-defined checks under provisional tolerances | provisional | supervisor tolerances for absolute claims | retain provisional for now | document |
| Unchanged benchmark technical run | supplementary single-notch technical pass | complete | not exact Fig.7 target | none for technical | keep as supporting evidence |
| H0 / H1 / H2-PUB technical runs | jobs 1376154 / 1376185 / 1376186 | complete | none | none | **frozen** |
| RF–U convergence (peak / pre-peak) | successive metrics; scientific review | supported | none | Decision 1A recorded | use H2-PUB / H1 / H0 roles |
| RF–U post-peak | full/post-peak NRMSE H1–H2 | limited / not fully demonstrated | post-peak residual ~20% | accept limitation wording | retain limitation |
| Publication comparison (lc=0.015) | digitized Fig.7 | provisional | digitization uncertainty | retain as provisional | do not use lc=0.0075 |
| Crack-path / matched-state SDV15 | CAE contour export failed | deferred (Decision 2B) | deferred planned task | Decision 2B recorded | prepare tools; execute later |
| Supervisor-approved absolute paper tolerances | not fixed for all Stage A claims | partial | not required to start Stage C prep | optional later | do not block preprocessing |
| Uniform-reference selection | H2-PUB fine validation; H1 production; H0 test | **accepted (1A)** | none for RF–U roles | Decision 1A recorded | freeze + Stage C prep |
| MISESERI Stage C preparation | plan + config scaffolding | **authorized** | submission not authorized | remesh params + first campaign | build preprocessor; prepare jobs |
| MISESERI HPC execution | five-job plan only | not authorized | explicit `qsub` approval | meeting / written approval | no submit |

## Frozen mesh roles (Decision 1A)

| Role | Mesh | \(h\) |
|---|---|---|
| Fine RF–U validation reference | **H2-PUB** | 0.001 mm |
| Production / thesis / report | **H1** | 0.0025 mm |
| Development / testing / debug | **H0** | ≈ 0.00494 mm |

## Explicit non-claims

- No full post-peak mesh independence claimed.
- No crack-path convergence claimed.
- No full unconditional Gate A3 pass for every historical Stage A item.
- No MISESERI **execution** authorization (preparation only).
- No multicore qualification authorization.

## Next actions

1. Complete automated H0/H1 preprocessing (Gate P1).  
2. Define and record initial remeshing parameters without seeing final crack.  
3. Prepare five-job campaign scripts.  
4. Request explicit submission authorization before any `qsub`.
