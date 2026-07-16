# SDV Layer and Update Mapping

Classification: `mapping_for_sdv15_detailed_review`

This file documents the source-defined meaning of the candidate-v2 visualization
fields used by the no-solution SDV15 detailed-event reconstruction. The ODB was
opened read-only; no Abaqus solution job was launched.

| ODB field | Source quantity | Writing layer | Source layer | Update timing | Scientific meaning |
|---|---|---|---|---|---|
| `SDV14` | `PHASE` assigned inside the displacement UEL | U2 displacement UEL writes `USRVAR(physical,14,IP)` | U2 reads U1 phase/history through `USRVAR(physical,15/14,IP)` depending on `STEPITER` | Updated during the displacement layer call; can lag or differ from the U1 phase-field update in the same increment | Phase value used for degraded mechanical response |
| `SDV15` | U1 `SDV(1)` phase variable copied into `USRVAR(physical,15,IP)` | U1 phase-field UEL | U1 phase layer | If `STEPITER=0`, stores `PHASE-DPHASE`; otherwise stores `PHASE` after the phase solve call | Phase-field visualization value, not by itself proof of equivalent converged-state irreversibility |
| `SDV16` | U1 `SDV(2)` history field copied into `USRVAR(physical,16,IP)` | U1 phase-field UEL | U1 phase layer | Updated with the source history maximum logic during phase-field calls | Monotone crack-driving history variable |

Layer offsets for candidate v2:

- Physical/U1 labels: `1..33852`
- U2 displacement labels: `33853..67704`
- CPS4 visualization labels: `67705..101556`
- Visualization-to-physical mapping: `physical = visualization - 2*N_ELEM`
- U2 mapping: `u2 = physical + N_ELEM`

Worst recorded SDV15 decrease location:

- ODB visualization element `84131`
- mapped physical/U1 element `16427`
- mapped U2 displacement element `50279`
- ODB integration point `3`
- source storage integration point `4` because the UMAT swaps CPS4 points 3 and 4 before reading `USRVAR`

The UMAT visualization layer maps `NOEL - 2*N_ELEM` back to the physical element
and copies `USRVAR(physical,I,NPT)` into `STATEV(I)`. For CPS4 output, source
points 3 and 4 are swapped relative to ODB integration-point numbering; points 1
and 2 remain unchanged. This reconstruction therefore reports both ODB and
source-storage IP identifiers.

Consecutive ODB frames are retained output states, not guaranteed equivalent
phase-update states. Detailed categories therefore remain conservative when the
retained frame data cannot prove whether a decrease is roundoff, staggered sync,
visualization lag, or a true source-level violation.
