# SDV Source Assignment Trace

Classification: `sdv_source_assignment_trace_complete_for_retained_source`

This trace is based on the preserved Molnar single-notch Fortran source and the generated candidate-v2 source copy. Candidate v2 changes only the hard-coded `N_ELEM` value; the SDV assignment logic is otherwise preserved.

| ODB field | Source assignment | Source timing and meaning |
|---|---|---|
| `SDV14` | U2 displacement UEL writes `SDV(14)=PHASE`, then uploads it to `USRVAR(physical,14,INPT)`; UMAT later copies `USRVAR(physical,14,NPT)` to `STATEV(14)` | Displacement-layer phase value used for stiffness degradation. It can be copied from U1 `USRVAR(...,15,...)` on the first U1 call of a new time value, or from U2's own retained `USRVAR(...,14,...)` on later iterations. It is therefore a synchronization-stage value, not automatically identical to U1 `SDV15`. |
| `SDV15` | U1 phase UEL writes `SDV(1)` and uploads it to `USRVAR(physical,15,INPT)`; UMAT copies `USRVAR(physical,15,NPT)` to `STATEV(15)` | Phase-layer value. On the first U1 call at a new time value it stores `PHASE-DPHASE`, i.e. the previous increment value. On later calls at the same time value it stores `PHASE`. Retained ODB output does not expose which U1 call was last before visualization. |
| `SDV16` | U1 phase UEL writes `SDV(2)=HIST` and uploads it to `USRVAR(physical,16,INPT)`; UMAT copies `USRVAR(physical,16,NPT)` to `STATEV(16)` | History-maximized crack-driving energy. The source uses `max(ENGN,HISTN)` logic; the retained detailed review found zero SDV16 decreases at SDV15 above-precision event locations. |

Stable source markers:

| Marker | Generated source line | Generated code | Preserved source line | Preserved code |
|---|---:|---|---:|---|
| U1 time/iteration reset | 76 | `TIMEZ=USRVAR(JELEM,17,1)` | 76 | `TIMEZ=USRVAR(JELEM,17,1)` |
| U1 first-call phase copy | 180 | `SDV(1)=PHASE-DPHASE` | 180 | `SDV(1)=PHASE-DPHASE` |
| U1 current phase copy | 182 | `SDV(1)=PHASE` | 182 | `SDV(1)=PHASE` |
| U1 reads displacement energy | 199 | `ENGN=USRVAR(JELEM,13,INPT)` | 199 | `ENGN=USRVAR(JELEM,13,INPT)` |
| U1 reads previous history | 204 | `HISTN=USRVAR(JELEM,16,INPT)` | 204 | `HISTN=USRVAR(JELEM,16,INPT)` |
| U1 writes history | 210 | `SDV(2)=HIST` | 210 | `SDV(2)=HIST` |
| U1 uploads SDV15/16 | 242 | `USRVAR(JELEM,I+NSTVTT,INPT)=SVARS(NSTVTO*(INPT-1)+I)` | 242 | `USRVAR(JELEM,I+NSTVTT,INPT)=SVARS(NSTVTO*(INPT-1)+I)` |
| U2 gets source iteration | 252 | `STEPITER=USRVAR(JELEM-N_ELEM,18,1)` | 252 | `STEPITER=USRVAR(JELEM-N_ELEM,18,1)` |
| U2 reads U1 first-call phase | 387 | `PHASE=USRVAR(JELEM-N_ELEM,15,INPT)` | 387 | `PHASE=USRVAR(JELEM-N_ELEM,15,INPT)` |
| U2 reads U2 stored phase | 389 | `PHASE=USRVAR(JELEM-N_ELEM,14,INPT)` | 389 | `PHASE=USRVAR(JELEM-N_ELEM,14,INPT)` |
| U2 writes SDV14 | 392 | `SDV(14)=PHASE` | 392 | `SDV(14)=PHASE` |
| U2 writes elastic energy | 433 | `SDV(13)=ENG` | 433 | `SDV(13)=ENG` |
| U2 uploads SDV1-14 | 465 | `USRVAR(JELEM-N_ELEM,I,INPT)=SVARS(NSTVTT*(INPT-1)+I)` | 465 | `USRVAR(JELEM-N_ELEM,I,INPT)=SVARS(NSTVTT*(INPT-1)+I)` |
| UMAT maps visualization label | 572 | `NELEMAN=NOEL-TWO*N_ELEM` | 572 | `NELEMAN=NOEL-TWO*N_ELEM` |
| UMAT swaps IP 3 to 4 | 573 | `IF (NPT.EQ.3) THEN` | 573 | `IF (NPT.EQ.3) THEN` |
| UMAT swaps IP 4 to 3 | 575 | `ELSEIF (NPT.EQ.4) THEN` | 575 | `ELSEIF (NPT.EQ.4) THEN` |
| UMAT copies USRVAR to STATEV | 580 | `STATEV(I)=USRVAR(NELEMAN,I,NPT)` | 580 | `STATEV(I)=USRVAR(NELEMAN,I,NPT)` |

Timing conclusion:

- The label/IP mapping is source-resolved.
- The within-increment call sequence is not retained in the ODB field outputs or CSV event table.
- Therefore the 817 non-staggered above-precision events cannot be promoted to confirmed physical healing or dismissed as harmless solely from the retained outputs.
