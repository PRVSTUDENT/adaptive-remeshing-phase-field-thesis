# P3-SB uninstrumented eight-element serial baseline

Preparation only. No execution or submission is authorized.

Purpose: determine whether the P3-S eight-element deck completes with the accepted D2-derived source and without P2/P3 diagnostics.

The package deliberately contains:

- the byte-identical P3-S input deck;
- the byte-identical accepted D2 UEL/UMAT source;
- the byte-identical eight-record D2 transfer table;
- no UEXTERNALDB callback;
- no GETRANK or GETTHREADID call;
- no mutex instrumentation;
- no diagnostic COMMON/BLOCK DATA;
- no shared-access monitor.

This is a new future isolation test, not an unchanged P3-S retry. A future execution would require a separate explicit authorization and guarded submission lane.
