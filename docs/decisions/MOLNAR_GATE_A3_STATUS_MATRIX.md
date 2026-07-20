# Molnar Gate A3 Status Matrix

Status: `supervisor_decision_pending`
Internal RF–U component status: `rf_u_reference_supported_contour_evidence_pending`
Historical overall label retained: `reference_data_insufficient`
Overall Gate A3: **open** (not passed)

Evidence base for the RF–U h-convergence rows: analysis commit `db4c1fadfb3a4f7b33b6b653c261e6da90036c48`.

| Component | Evidence | Status | Blocker | Required decision | Next action |
|---|---|---|---|---|---|
| Environment / toolchain | HPC smoke 1374531/1374533; modules gcc/intel/abaqus 2023 | complete | none | none | retain stack |
| One-element technical validation | local Molnar one-element technical pass | complete | none | none | none |
| One-element scientific validation | source-defined checks under provisional tolerances | provisional | supervisor tolerances | approve or retain provisional | document tolerances |
| Unchanged benchmark technical run | supplementary single-notch technical pass | complete | not exact Fig.7 target | none for technical | keep as supporting evidence |
| H0 / H1 / H2-PUB technical runs | jobs 1376154 / 1376185 / 1376186 | complete | none for solvers | none | freeze solver ODBs |
| RF–U convergence (peak / pre-peak) | successive metrics table; scientific review | supported | none for this component | Decision 1 on H2-PUB as reference | freeze H2-PUB if accepted |
| RF–U post-peak | full/post-peak NRMSE H1–H2 | limited / not fully demonstrated | post-peak residual ~20% | accept limitation wording | retain as documented limitation |
| Publication comparison (lc=0.015) | digitized Fig.7; publication comparison CSV | provisional | digitization uncertainty; not exact author data | accept approximate reference | do not use lc=0.0075 |
| Crack-path / matched-state SDV15 | CAE contour export failed | not assessed | missing contour package | Decision 2 contour requirement | CAE-only contours or waive/defer |
| Supervisor-approved tolerance | none fixed | supervisor decision pending | no approved thresholds | set or retain provisional | record policy |
| Uniform-reference selection | H2-PUB recommended; H1 intermediate; H0 not reference | provisional (pending Decision 1) | awaiting supervisor | Decision 1 A/B/C | freeze selection or request more evidence |

## Recommended project answers (not supervisor answers)

| Question | Project recommendation |
|---|---|
| Uniform RF–U reference | H2-PUB (h = 0.001 mm) |
| Intermediate mesh | H1 (h = 0.0025 mm) |
| Contours | supervisor must choose; project can support either waiver/deferral or one CAE-only contour job on existing ODBs |

## Explicit non-claims

- No full post-peak mesh independence claimed.
- No crack-path convergence claimed.
- No supervisor approval claimed.
- No MISESERI authorization claimed.
