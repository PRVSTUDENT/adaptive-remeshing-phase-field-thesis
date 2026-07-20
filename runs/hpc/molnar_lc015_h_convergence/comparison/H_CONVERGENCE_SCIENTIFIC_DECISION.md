# H-Convergence Scientific Decision Record

This file freezes the decision wording accepted after formal RF–U analysis.

Canonical expanded decision:
`docs/decisions/MOLNAR_LC015_H_CONVERGENCE_SCIENTIFIC_DECISION.md`

## Classification package

```text
Peak and pre-peak RF–U h-convergence: supported
Post-peak h-convergence: not fully demonstrated
Crack-path convergence: not assessed
Publication agreement: provisional
Overall RF–U classification: rf_u_h_convergence_supported
  (with explicit post-peak limitation)
Internal Gate A3 component status: rf_u_reference_supported_contour_evidence_pending
Historical Gate A3 label retained: reference_data_insufficient
```

## Mesh selection

- **Conservative RF–U reference:** H2-PUB (h = 0.001 mm)
- **Intermediate development:** H1 (h = 0.0025 mm)
- **Not recommended as reference:** H0

## Safest thesis wording

The force–displacement response is effectively mesh-independent between H1 and
H2-PUB for the elastic, pre-peak and peak-load regimes. A noticeable post-peak
mesh dependence remains and must be retained as a limitation.

## Boundary

```text
Further PBS/Abaqus/CAE: not authorized
MISESERI/remeshing/state transfer: blocked pending supervisor decision
```
