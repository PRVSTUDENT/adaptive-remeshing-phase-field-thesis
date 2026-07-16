# Layer Label Mapping Rules

Classification: `layer_label_mapping_verified`

Derived formulas for candidate v2:

| Quantity | Formula | Range |
|---|---|---|
| physical base element | `p` | `1..33852` |
| U1 phase-field label | `p` | `1..33852` |
| U2 displacement label | `p + N_ELEM` | `33853..67704` |
| CPS4 visualization label | `p + 2*N_ELEM` | `67705..101556` |
| physical from visualization | `visualization - 2*N_ELEM` | `1..33852` |

Verification sources:

- generated input deck element blocks;
- `layer_mapping.csv`;
- Fortran `JELEM-N_ELEM` and `NOEL-TWO*N_ELEM` indexing;
- full connectivity comparison across U1, U2, and CPS4 labels.

Full mapping table:

```text
runs/hpc/paper_matched_single_notch_v2/scientific_review/sdv15_mapping_resolution/layer_label_mapping_verified.csv
```

Verification result:

- physical elements checked: `33852`
- mapping failures: `0`
- overlapping layer ID ranges: `0`
- missing labels: `0`
- off-by-one offset evidence: `none`
- connectivity mismatches: `0`
