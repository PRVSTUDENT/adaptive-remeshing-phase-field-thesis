# Stage C2 chain failure diagnosis and fix

## What happened

| Job | ID | Result |
|---|---|---|
| C2A | 1376298 | **PASS** — continuum ODB OK, real stresses (RF2≈625 N, MISESERI O(1)) |
| C2B | 1376299 | **FAIL Exit 14** — tool crash, not scientific inactivity |
| C2C–C2F | 1376300–303 | **Deleted by PBS** via `afterok` after C2B failed |

## Root cause

C2B used system `python3` = **3.6.8**, which cannot import:

```text
from __future__ import annotations
```

in `scripts/remeshing/build_refined_mesh_from_miseseri.py`.

The scientific gate/remesh never completed; dependents were correctly cancelled by `afterok`.

## Fix

1. Prefer `/usr/bin/python3.12` in C2B/C2C (and related postprocess PBS).
2. Remove `from __future__ import annotations` from remesh helper.
3. Resume from **C2B** reusing C2A ODB via `scripts/hpc/stage_c2/submit_c2_from_c2b.sh`.

## Lesson

```text
afterok deletes the whole tail when any gate job fails
C2B must use a modern cluster Python (3.12)
Do not re-run successful C2A continuum unless necessary
```
