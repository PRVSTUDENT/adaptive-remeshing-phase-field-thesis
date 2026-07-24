# P3-SM0 minimal callback serial package

Preparation only; execution is unauthorized.

This package preserves the accepted D2 eight-element scientific source and P3-SB deck while adding four constant callback categories:

- `P3SM0_UEXTERNALDB_LOP0`
- `P3SM0_UEL_OBSERVED`
- `P3SM0_UMAT_OBSERVED`
- `P3SM0_UEXTERNALDB_END`

It contains no rank/thread utility, mutex, shared-access database, diagnostic COMMON storage, or ownership monitor. P3-SM0 is intended only to test minimal callback availability and order after a separate authorization decision.
