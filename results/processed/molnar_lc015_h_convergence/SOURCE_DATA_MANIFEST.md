# Source Data Manifest — Molnar lc015 h-convergence RF-U

Status: inventory of retained CAE and reference curves for no-solution analysis.

CAE job: `1376236.mmaster02`
Scientific-input revision: `58d7e3102d76fe0e70e6729457e2c7e90ad131bb`
Analysis script: `scripts/postprocessing/analyze_molnar_lc015_h_convergence.py`

| Case | Job | Points | U range [mm] | RF range [kN] | Origin | SHA-256 |
|---|---|---:|---|---|---|---|
| H0 | `1376154.mmaster02` | 73 | [0, 0.007] | [0, 0.727608] | True | `a0196294625d…` |
| H1 | `1376185.mmaster02` | 73 | [0, 0.007] | [0, 0.699604] | True | `48f2358c1672…` |
| H2-PUB | `1376186.mmaster02` | 73 | [0, 0.007] | [0, 0.696336] | True | `148bfc09d016…` |
| FIG7_lc015 | `n/a` | 18 | [0, 0.00615206] | [0, 0.690591] | True | `915aad72541f…` |

## Units and sign

- Displacement U2: mm
- Reaction RF2: kN
- RF2 sign convention: `positive_tension_as_exported_by_cae`
- lc = 0.015 mm

Source CSV/RPT files are not edited.
