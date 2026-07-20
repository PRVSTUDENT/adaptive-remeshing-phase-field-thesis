# Curve Validation Report

Overall pass: `True`

| Case | Pass | Points | Origin | U max | RF max | Issues |
|---|---|---:|---|---:|---:|---|
| H0 | True | 73 | True | 0.007 | 0.727608 | none |
| H1 | True | 73 | True | 0.007 | 0.699604 | none |
| H2-PUB | True | 73 | True | 0.007 | 0.696336 | none |

## Rules

- Exactly one explicit origin contribution required (origin label or (0,0)).
- Finite U2/RF2 only.
- Units U2 [mm], RF2 [kN].
- Nondecreasing displacement sequence (no step-boundary reset).
- No comparison to lc=0.0075 reference in this study.
- For interpolation: exact duplicate U retain last frame (deterministic).
