# Stage F12 session report

Date: 2026-07-31
Agent: codex
Starting commit: `3f5a5ad71fed21efad0734884dc6bfb117902615`
Preparation commit: `03e544a3df2645b2dc10a5b003dc675ae6c1187e`
Authorization commit: `10048113606b6df035864c5a0b8cbbbf3a198f7c`
Submission commit: `7d0b8e6d8820922ad52eb3a82595762749b89547`
Run ID: `F12_20260731_100123_03e544a`

Exactly three guarded qsub attempts succeeded as jobs `1380971`, `1380972`,
and `1380973`. The 15-minute quiet interval was honored. No retry,
replacement, direct qsub, qdel, or qmove occurred.

Both rollback analyses solved to the prescribed endpoint. The reference used
106 increments and 128 iterations; the aggressive case used two increments
and two iterations. Both had zero cutbacks, explicitly confirmed by Abaqus.
Rollback is therefore `penalty_rollback_not_exercised`. Unit-99 evidence was
not returned from Abaqus scratch and caused post-solve wrapper exits; M-116
records the defect. No retry is authorized.

The CAE-only job imported the official coarse deck, created the native
MISESERI rule on MODEL/Step-1, and wrote a coarse input. Solver, adaptive, and
remesh counts are zero. The H1 pair remains `prepared_not_authorized` and is
not execution-ready because rollback did not qualify.

The integrated thesis closeout build compiled successfully with Tectonic to
39 pages. Existing layout warnings remain non-fatal.
