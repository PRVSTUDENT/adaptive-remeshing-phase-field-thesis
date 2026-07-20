# Study Status

Status: `rf_u_h_convergence_decision_recorded`

## Scientific decision (frozen)

```text
Peak and pre-peak RF–U h-convergence: supported
Post-peak h-convergence: not fully demonstrated
Crack-path convergence: not assessed
Publication agreement: provisional
```

Safest wording:

> The force–displacement response is effectively mesh-independent between H1
> and H2-PUB for the elastic, pre-peak and peak-load regimes. A noticeable
> post-peak mesh dependence remains and must be retained as a limitation.

| Use | Mesh |
|---|---|
| Conservative RF–U reference | **H2-PUB** (h = 0.001 mm) |
| Intermediate development | **H1** (h = 0.0025 mm) |
| Not recommended as reference | H0 |

Decision document: `docs/decisions/MOLNAR_LC015_H_CONVERGENCE_SCIENTIFIC_DECISION.md`  
Formal review: `comparison/H_CONVERGENCE_SCIENTIFIC_REVIEW.md`  
Analysis commit: `db4c1fadfb3a4f7b33b6b653c261e6da90036c48`

## Gate A3

| Layer | Status |
|---|---|
| Overall | **open** |
| Historical label | `reference_data_insufficient` (still defensible) |
| RF–U internal status | `rf_u_reference_supported_contour_evidence_pending` |
| RF–U benchmark component | complete |
| RF–U reference mesh | provisionally H2-PUB |
| Publication comparison | provisional (lc=0.015 approx. digitization) |
| Supervisor tolerances | pending |
| Contour/crack-path evidence | pending |

## Execution history (summary)

| Case | Solver | CAE package |
|---|---|---|
| H0 | 1376154 technical pass | 1376236 pass |
| H1 | 1376185 technical pass | 1376236 pass |
| H2-PUB | 1376186 technical pass | 1376236 pass |

Scientific-input revision: `58d7e3102d76fe0e70e6729457e2c7e90ad131bb`

## Boundary

```text
RF–U h-convergence analysis: complete
H2-PUB reference recommendation: supported
H1 intermediate recommendation: supported
Contour convergence: pending
Gate A3: open
Further PBS/Abaqus/CAE runs: not authorized
MISESERI/remeshing/state transfer: blocked pending supervisor decision
```
