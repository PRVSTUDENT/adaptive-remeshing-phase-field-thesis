# F9 diagnostic batch session

Starting SHA: `398010a4727f5d44203d531bbc6e825888d5bdce`

Preparation SHA: `20d65443355110d7a7ffb807ae9aa1bbfaabaea4`

Authorization SHA: `d9617d72da44186c8b14b91f14bff4c5fdd98256`

Submission SHA: `abdc61156f1532614e075df079944863a0e376c6`

Run ID: `F9_20260731_052600_20d6544`

Exactly two qsub commands succeeded, returning `1380088.mmaster02` and
`1380089.mmaster02`. Retries, replacements, direct qsub, qdel, and qmove
counts are zero. All authorization was consumed immediately.

Job A completed five datacheck-only cases. Its debug case isolated
`USRVAR(-33828,...)` inside UEL because runtime `JELEM=24` was reduced-model
contiguous numbering, not the explicit displacement label `33853`.
UMAT-only datacheck passed. No analysis executed.

Job B passed hashes and pre-submission no-solver scanning, then failed before
CAE because the PBS helper filename did not match the staged file. No API
type was attempted and no rule object or candidate deck exists.

All unrelated dirty paths were preserved.
