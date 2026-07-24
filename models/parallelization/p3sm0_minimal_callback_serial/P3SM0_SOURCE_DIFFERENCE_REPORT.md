# P3-SM0 source difference report

Base source: accepted uninstrumented D2 source, SHA-256 `473f80e8f0f1cba6aa7a7f0c3a49aaa949bac43e03548096d9d6f0c9a6f80306`.

P3-SM0 source: SHA-256 `0091a4dc3b39829542f718d722bb2129f1bac7491e1f03b4e38ef12394e852d4`.

Exact additions:

1. A bounded unit-7 `P3SM0_UEL_OBSERVED` write when `JELEM=1`, `KSTEP=1`, `KINC=1`.
2. A bounded unit-7 `P3SM0_UMAT_OBSERVED` write when `NOEL=17`, `NPT=1`, `KSTEP=1`, `KINC=1`.
3. A minimal `UEXTERNALDB` containing only constant unit-7 markers for `LOP=0` and `LOP=3`.

No accepted UEL/UMAT calculation, `USRVAR`, `TRANSFER_DONE`, property, state-variable, residual, tangent, stress, history, or BLOCK DATA expression was changed. No `SAVE` flag was added for diagnostic first-call tracking.

Explicitly absent: `GETRANK`, `GETTHREADID`, all mutex utilities, diagnostic COMMON arrays, shared-access monitoring, ownership monitoring, and thread/rank identifiers.
