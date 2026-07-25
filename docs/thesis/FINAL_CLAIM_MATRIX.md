# Final Thesis Claim Matrix

| Claim | Classification | Evidence boundary |
|---|---|---|
| Molnar workflow is technically reproducible in the tested Abaqus environment | validated | baseline and callback technical passes |
| H2-PUB/H1/H0 mesh roles support RF--U use | conditionally supported | supervisor Decisions 1A/2B; contours deferred |
| Stage C refined workflow supports peak/pre-peak response | validated within scoped Stage C gate | committed Stage C closeout |
| Stage C reproduces post-peak crack path equivalently to H1 | not supported / withheld | committed crack-path and post-peak limitation |
| MISESERI is useful for locating a pre-peak refinement corridor | conditionally supported | tested Stage C parameter set only |
| Controlled nonmatching field transfer preserves bounded fields with quantified error | validated | D1 analytical transfer |
| Abaqus ingests transferred phase/history state | validated | D2A |
| Serial continuation after tiny transfer is possible | validated | D2B accepted rerun |
| One-rank/four-thread result matches serial in the tested case | validated | D2C; no broader scalability claim |
| `get_thread_id()` and `CALL GETRANK` work in controlled UEL callbacks | validated only at one rank and one thread | P3-SM1TC and P3-SM1R |
| The dedicated P3-T4 run characterizes threaded shared-state safety | not supported / technically inconclusive | compilation stopped before linking or callback execution |
| General COMMON/SAVE thread safety, MPI safety, or hybrid safety is established | not supported / withheld | D2C is case-specific; P3-T4 produced no threaded evidence; MPI/hybrid were not tested |
| Nonmatching pre-peak checkpoint transfer and R4 release hold are valid | validated | D3A3-R4 bounded scope |
| A fixed active set remains valid through further loading | not supported / withheld | disproven by D3D |
| D3D-A1 correction is KKT-admissible under frozen F3 history | validated | deterministic offline solve |
| D3D-A1 candidate is an accepted mechanical restart | not supported / withheld | mechanical equilibration never executed |
| D3E, post-peak continuation, and online adaptive remeshing are validated | not supported / withheld | not performed |
| ABAQUSER agrees with independent extraction | not supported / withheld | interface externally unavailable |
| Numerical tolerances are universally supervisor-approved | provisional | consolidated policy awaits review |

This matrix governs the abstract, conclusions, presentation, and figure
captions. Narrower wording must be used whenever a claim is conditional or
withheld.
