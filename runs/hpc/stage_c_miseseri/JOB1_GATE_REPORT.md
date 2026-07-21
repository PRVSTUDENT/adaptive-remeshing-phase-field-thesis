# Stage C Job 1 Gate Report

Job: `1376292.mmaster02`  
Name: `molnar_h0_miseseri_smoke`  
Revision: `2de90fecf93011416356323f299bc9b84f327bc2`  
Host: `mnode100.cluster`

## Queue wait (document vs future entry submissions)

| Instant | Time (cluster) |
|---|---|
| `qtime` / `ctime` / `etime` | 2026-07-21 08:42:08 |
| `stime` | 2026-07-21 08:53:44 |
| Wait | **≈ 11 min 36 s** (696 s) |
| Submit queue (`PBS_O_QUEUE`) | `entry_imfdfkmq` (route) |
| Execution queue | `normal_imfdfkmq` (after routing) |
| Wall used | 00:00:38 |
| Mem used | ≈ 618 MB (632332 kb) |
| Exit_status | **0** |

Job 1 was **not** cancelled or resubmitted.

## Gate checklist

| Check | Result |
|---|---|
| PBS Exit_status = 0 | **pass** |
| Abaqus completed successfully (STA) | **pass** — `THE ANALYSIS HAS COMPLETED SUCCESSFULLY` |
| Abaqus return code | **0** |
| Technical classification | `molnar_h0_miseseri_smoke_technical_pass` |
| ODB readable | **pass** (Abaqus Python openOdb) |
| MISESERI present | **pass** (n=3930) |
| MISESERI finite | **pass** |
| MISESERI nonempty | **pass** (min≈3.05e-19, max≈1.52e-14; smoke load U=0.001 mm → small magnitudes expected) |
| MISESAVG present | **pass** (n=3930) |
| S present | **pass** |
| EVOL present | **pass** |
| U present | **pass** |
| RF present | **pass** |
| Physical/facsimile mapping | **pass** — instance elements 11790 = 3×3930 |

## Overall

```text
Job 1 gate: PASS
Release Job 2: authorized by staged campaign policy
```

Note: MISESERI magnitudes are tiny under the short smoke displacement; field
**availability** and finiteness are confirmed. Job 2 at Upre=0.00464 mm is the
scientific pre-analysis field for remeshing suitability.
