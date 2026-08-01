# Stage F15/F16 conditional batch preparation record

- Published base: `86d54a17c4a71bd2ac07b46e9b36393862df6439`
- Direct Telegram receipt: user-confirmed at `2026-08-01T07:31:56Z`
- Direct sendmail receipt: not confirmed
- PBS email: untested
- PBS multiple-recipient syntax: supported by installed PBS 2024.1.3 docs
- Wave A: `M2NOTIFY1`
- Wave B: `M2IRRROLLCTL2`, `M2IRRROLLFORCE2`, `M2RMREG2`
- Maximum future qsub attempts: 4
- Maximum simultaneous running jobs: 2
- Current qsub attempts: 0
- Execution/submission authority: false

## Wave A terminal evidence (2026-08-01)

`M2NOTIFY1` (`1381373.mmaster02`) completed on `mnode100.cluster` with exit
status 0. Telegram START and COMPLETED passed technically on their first
attempts (HTTP 200, `ok=true`), and native PBS BEGIN/END mail was configured.
The shell-only job ran no Abaqus or scientific workload and made no nested
qsub call. Classification remains
`notification_smoke_technically_passed_awaiting_human_confirmation`; Wave B
is blocked pending personal confirmation of all four deliveries.

## Wave B submission result (2026-08-01)

The user waived the unobserved PBS-email delivery gate while retaining
Telegram as mandatory. Under authorization `37b9c30`, both rollback qsub
invocations were rejected with return code 174 because queue access was
denied. No PBS ID was issued. `M2RMREG2` was not invoked because the required
`afterany` concurrency dependency could not be formed without the control
job ID. Consequently there are no terminal scientific metrics: rollback
remains unqualified, medium H1 remains not ready, and native adaptive-region
qualification remains unresolved. No retry or replacement is authorized.
