# Worst Event Layer Mapping

Classification: `worst_event_mapping_resolved`

Worst retained SDV15 decrease event:

| Quantity | Value |
|---|---:|
| visualization label | `84131` |
| physical base element | `16427` |
| U1 label | `16427` |
| U2 label | `50279` |
| ODB integration point | `3` |
| source-storage integration point | `4` |
| previous global frame | `189` |
| current global frame | `190` |
| previous SDV15 | `1.0013006925582886` |
| current SDV15 | `1.0008754730224609` |
| decrease magnitude | `0.00042521953582763672` |

Layer connectivity:

| Layer | Label | Connectivity |
|---|---:|---|
| U1 | `16427` | `16457 16458 17051 17050` |
| U2 | `50279` | `16457 16458 17051 17050` |
| CPS4 visualization | `84131` | `16457 16458 17051 17050` |

Source fields:

- `SDV14`: copied from `USRVAR(16427,14,4)`, written by the U2 displacement layer.
- `SDV15`: copied from `USRVAR(16427,15,4)`, written by the U1 phase-field layer.
- `SDV16`: copied from `USRVAR(16427,16,4)`, written by the U1 phase-field layer using history-max logic.

Integration-point conclusion:

The UMAT visualization routine swaps Abaqus CPS4 output points 3 and 4 before reading `USRVAR`; therefore ODB IP `3` maps to source-storage IP `4`. U1 and U2 use the same source-storage `INPT` quadrature convention and the same connectivity. No label, connectivity, or integration-point mismatch explains the worst event.

Scientific consequence:

The worst event remains unresolved from retained outputs because the completed within-increment U1 phase-update sequence is not available. It should be classified as `insufficient_output_evidence`, not as `mapping_error` and not as a confirmed violation.
