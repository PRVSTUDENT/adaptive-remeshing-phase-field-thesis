# Session report: SUPERVISOR-REPORT-FINAL-SCIENTIFIC-AUDIT-AND-FIX1

- Agent: codex
- Starting commit: `ccb4355e104f805993cdd27a4c36cde6bbcb9819`
- Scope: reporting artifacts, the two report-owned H2 figures, and coordination closeout only
- HPC submissions: 0

## Outcome

- Audited adaptive and uniform input/extraction definitions: RP RF1/U1, sign, units, and loading amplitude are consistent.
- Found no scientifically justified constant normalization factor. Similar initial stiffness also rules out a factor-of-two correction.
- MM/PK5 mutual agreement remains valid, but adaptive-to-uniform global accuracy and accuracy-versus-cost are held because the late adaptive force is about half the uniform-reference level and primary adaptive curves were unavailable for exact L2/work computation.
- Reframed H2 as a scientific trajectory/termination result, removed internal debugging chronology, defined MM/PK5/FRACFIX/test IDs, neutralized state-transfer language, and added a glossary.
- Corrected pure-thread/MPI/hybrid text and Figure 6. The hybrid COMMON/DATA/SAVE limitation is explicit and supported by official SIMULIA documentation.
- Redrew Figures 1 and 2 with micrometre axes, distinct line styles, and separated callouts.

## Verification

- Tectonic PDF build: PASS (13 pages).
- All-page rendered visual audit: PASS.
- Figure 1 readability: PASS.
- Figure 2 readability: PASS.
- Figure 6 overlap audit: PASS.
- Forbidden/stale claim text search: PASS.
- PDF SHA-256: `515fb4b02b5e60c65971dbcdc9721926a7e5c7225228a810f29e02b7174778f7`.

## Remaining gate

Retrieve the primary MM and PK5 RF-U curves and compute exact MM/PK5-versus-H1 L2 and work differences. Until then, the report correctly marks adaptive-to-uniform accuracy and accuracy-versus-cost as HOLD and is not supervisor-send-ready.
