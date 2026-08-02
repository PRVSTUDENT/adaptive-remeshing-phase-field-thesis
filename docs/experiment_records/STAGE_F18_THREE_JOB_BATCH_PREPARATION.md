# Stage F18 three-job batch preparation

Starting commit: `cb00b40061762d2f9cf6ece12d35cf7f7b983361`.

Prepared exactly `M2IRRROLLCTL4`, `M2IRRROLLFORCE4`, and `M2RMREG5` for
`entry_imfdfkmq`, with at most two future simultaneously running project jobs.
The adaptive job has no scientific dependency on the rollback pair; its future
`afterany` dependency on the control PBS ID is scheduler-only concurrency
control. Telegram START/terminal notification is mandatory and PBS email is
best-effort.

No qsub, Abaqus/Standard, Abaqus/CAE, datacheck, native remesh, candidate, H1,
H2, or refined analysis ran. All execution counters are zero and authority is
false. The repository has no canonical `thesis/` tree, so no thesis file was
invented; this experiment record is the Stage F preparation note.
