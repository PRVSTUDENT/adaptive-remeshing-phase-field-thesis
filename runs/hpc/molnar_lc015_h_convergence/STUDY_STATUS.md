# Study Status

Status: `rf_u_h_convergence_decision_recorded_supervisor_1A_2B_accepted`

## Scientific decision (frozen)

```text
Peak and pre-peak RF–U h-convergence: supported
Post-peak h-convergence: not fully demonstrated
Crack-path convergence: deferred (Decision 2B)
Publication agreement: provisional
```

Safest wording:

> The force–displacement response is effectively mesh-independent between H1
> and H2-PUB for the elastic, pre-peak and peak-load regimes. A noticeable
> post-peak mesh dependence remains and must be retained as a limitation.

| Use | Mesh |
|---|---|
| Fine RF–U validation reference | **H2-PUB** (h = 0.001 mm) |
| Production / thesis / report | **H1** (h = 0.0025 mm) |
| Development / testing / debug | **H0** (h ≈ 0.00494 mm) |

Decision document: `docs/decisions/MOLNAR_LC015_H_CONVERGENCE_SCIENTIFIC_DECISION.md`  
Supervisor 1A/2B: `docs/decisions/MOLNAR_GATE_A3_SUPERVISOR_DECISION_1A_2B.md`  
Result freeze: `docs/decisions/MOLNAR_MESH_ROLE_AND_RESULT_FREEZE.md`  
Formal review: `comparison/H_CONVERGENCE_SCIENTIFIC_REVIEW.md`  
Analysis commit: `db4c1fadfb3a4f7b33b6b653c261e6da90036c48`

## Gate A3

| Layer | Status |
|---|---|
| RF–U validation use | **conditionally accepted** (Decisions 1A + 2B) |
| Internal status | `gate_a3_conditionally_accepted_rf_u` |
| Contour | `contour_validation_deferred` |
| Stage C preparation | `stage_c_miseseri_preparation_authorized` |
| HPC submission | **not authorized** without explicit new approval |
| Historical full-closure label | may retain `reference_data_insufficient` for residual Stage A items |
| RF–U benchmark component | complete |
| RF–U reference mesh | **H2-PUB** (accepted) |
| Production mesh | **H1** (accepted) |
| Development mesh | **H0** (accepted) |
| Publication comparison | provisional (lc=0.015 approx. digitization) |
| Contour/crack-path evidence | deferred planned task |

Package (historical request, now answered for 1A/2B):  
`docs/decisions/MOLNAR_GATE_A3_SUPERVISOR_REVIEW.md`  
Status matrix: `docs/decisions/MOLNAR_GATE_A3_STATUS_MATRIX.md`

## Execution history (summary)

| Case | Solver | CAE package |
|---|---|---|
| H0 | 1376154 technical pass | 1376236 pass |
| H1 | 1376185 technical pass | 1376236 pass |
| H2-PUB | 1376186 technical pass | 1376236 pass |

Scientific-input revision: `58d7e3102d76fe0e70e6729457e2c7e90ad131bb`  
Results: **frozen** — do not overwrite.

## Boundary

```text
RF–U h-convergence analysis: complete
H2-PUB fine validation reference: accepted (1A)
H1 production/report mesh: accepted (1A)
H0 development/testing mesh: accepted (1A)
Contour convergence: deferred (2B)
Gate A3 RF–U use: conditionally accepted
Stage C MISESERI preparation: authorized
Further PBS/Abaqus/CAE submission: not authorized without explicit new approval
```
