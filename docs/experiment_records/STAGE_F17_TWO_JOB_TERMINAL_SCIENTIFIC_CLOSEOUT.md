# Stage F17 two-job terminal scientific closeout

Preparation `b4d9fad`, authorization `0e8e501`, and submission `a2d5d5e`
produced jobs `1381483.mmaster02` and `1381484.mmaster02`. Scheduler evidence
matches the user report. The probe exited zero on `mnode106/0` after 2:28;
the adaptive job exited one on `mnode106/1` after three seconds.

All four Telegram START/terminal events passed on their first HTTPS attempts
(HTTP 200, Telegram `ok=true`, matching recipient fingerprint). PBS email is
best-effort and was not independently verified. The lightweight inventory
contains 51 pre-inventory retained files with path, size, SHA-256, timestamp,
and job association; binary solver products are excluded.

The penalty solve completed both steps and retained a 6/6 valid extraction
manifest. Four penalty-active calls were detected. The first deterministic
state is step 2, increment 4, call 1, element 6, IP 1, time 0.08, DTIME 0.02:
committed/trial phase `0.994704402277978`/`0.994699000632349`, healing
`5.401645628899665e-6`, residual `0.97229621320194`, tangent `180000`, and
energy `2.625999795018977e-6`. Classification:
`penalty_activation_probe_passed`. A rollback pair is preparation-eligible,
but is not prepared or authorized here.

The adaptive wrapper passed startup, Telegram START, module loading, and the
compatibility helper. CAE then failed at line 6 before deck import with
`KeyError: 'F17_SOURCE_ODB'`. No model-integrity stage was reached. All solver,
datacheck, adaptivity, remesh, candidate, and refined-analysis counters remain
zero. Classification: `native_adaptive_region_construction_failed`. The
smallest repair is to stage/export the intended source ODB path before the
same zero-execution qualification; native remesh execution is not ready.

No retry, replacement, scheduler mutation, or additional submission occurred.
