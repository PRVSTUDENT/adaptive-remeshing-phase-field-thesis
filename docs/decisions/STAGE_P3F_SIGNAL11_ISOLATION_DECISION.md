# Stage P3-F signal-11 isolation decision

Date: 2026-07-24

Owner: thesis project

Job: `1378028.mmaster02`

## Question

Which new technical isolation test should be considered first after the closed P3-S failure: P3-SB or P3-SM?

## Evidence

The Abaqus exception stack is `dmpc_getrank -> uexternaldb -> openfs -> std_main`. The exact staged source calls `MUTEXINIT(91)` and then `GETRANK()` inside `UEXTERNALDB(LOP=0)`. No `P2_INIT`, first UEL, first UMAT, `P2_FIRST`, `P3_ACCESS`, element, integration point, or shared-state access was observed.

The immediate signal-11 location is therefore localized to the diagnostic `GETRANK()` call at UEXTERNALDB initialization in this package/environment. The underlying eight-element deck with the accepted D2 source was never exercised.

## Alternatives

| Candidate | What it isolates | Advantages | Limitations |
|---|---|---|---|
| P3-SB | Eight-element deck plus accepted D2 source, with all new diagnostics removed | Establishes the missing serial baseline and cleanly separates model/package behavior from instrumentation | Produces no callback/rank/thread evidence |
| P3-SM | Minimal callback ordering and identifier utilities | Could isolate callback timing and utility availability | Still introduces diagnostic behavior before the baseline is known; must be designed to avoid the failed LOP=0 `GETRANK` sequence |

## Decision

If a future execution is separately authorized, P3-SB should be the first test. P3-SM should remain design-only until the P3-SB result is reviewed.

This is a recommendation, not an authorization. P3-SB, P3-SM, P3-T4, MPI, hybrid, production H1, D3D-A1 reopening, and D3E remain blocked.

## Consequences

- P3-S remains a technical execution failure, not a parallelization result.
- The current evidence does not support claims about COMMON/SAVE serial safety, thread races, or MPI.
- P4 refactoring is not selected.
- Any future run must be a newly authorized isolation test, not an unchanged retry.
