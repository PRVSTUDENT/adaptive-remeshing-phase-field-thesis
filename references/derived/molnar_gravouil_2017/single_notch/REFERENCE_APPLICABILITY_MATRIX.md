# Reference Applicability Matrix - Molnar Single Notch

Date: 2026-07-14

Current decision: `reference_data_insufficient`

The matrix compares the published Molnar and Gravouil Fig. 6/Fig. 7 single-notch case against the supplied supplementary `SingleNotch` deck. It is intended to prevent treating a nonmatching paper curve as an exact pass/fail reference.

| Criterion | Paper Fig. 6/Fig. 7 case | Supplementary `SingleNotch` deck | Applicability |
|---|---|---|---|
| Geometry | Single edge notched tensile specimen; Fig. 6a and tensile crack pattern Fig. 6b | Single edge notched square plate with horizontal ligament and top RP loading | Close qualitative match |
| Material | `E = 210 kN/mm^2`, `nu = 0.3` | `E = 210`, `nu = 0.3` | Match |
| Fracture toughness | `gc = 2.7e-3 kN/mm` | `gc = 0.0027` | Match |
| Length scale | Paper text states `lc = 0.0075 mm` for the single-notch benchmark | Deck uses `lc = 0.015` | Mismatch or requires selected-curve interpretation |
| Mesh size and `h/l` | Text states the supplementary smaller tensile test has `h = 0.005 mm`; Fig. 7 curve label still needs confirmation | Deck uses `h = 0.005`, `lc = 0.015`, so `h/lc = 0.333` | Requires curve-label confirmation |
| Element count | Published Fig. 7 study uses about 22,000 elements | Deck has 3,930 phase elements, 3,930 displacement elements, and 3,930 UMAT visualization elements, about 4,000 physical elements | Mismatch for exact numeric reference |
| Loading and boundary conditions | Bottom fixed, top moved in tension | Bottom vertical fixed, one bottom/top horizontal constraint, top tied to RP U2 displacement | Close match |
| Load increments | Paper text says tensile step size was reduced to `Delta u = 1e-5 mm` | Step-1 reaches `U2 = 0.005`; Step-2 reaches `U2 = 0.007` in the frozen run | Requires interpretation |
| Fig. 7 curve label | Different length-scale curves plus Miehe reference symbols | Supplementary deck has `lc = 0.015` and smaller mesh | Not identified |

## Resolution Paths

1. `exact_reference_obtained`: acquire original RF-U coordinates from an authoritative source, populate `rf_u_reference.csv`, and rerun the validator.
2. `scientific_comparison_approximate`: digitize a selected Fig. 7 curve and explicitly record curve label, units, digitization uncertainty, and mesh/length-scale mismatch.
3. `qualitative_baseline_approved`: obtain supervisor approval to treat the smaller supplementary example as a qualitative-only baseline using technical reproducibility, horizontal crack propagation, peak/post-peak response, bounds, and irreversibility diagnostics.
