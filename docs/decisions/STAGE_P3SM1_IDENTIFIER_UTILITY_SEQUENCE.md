# Stage P3-SM1 identifier-utility sequence

Date: 2026-07-25
Owner: Codex preparation; execution requires later review

## Question and evidence

How should Abaqus identifier utilities be qualified without losing causal
isolation? The earlier signal 11 was localized to `GETRANK()` called from
`UEXTERNALDB(LOP=0)`. P3-SM0 subsequently proved that minimal
`UEXTERNALDB`, UEL, and UMAT callbacks complete serially when identifier
utilities are absent.

## Decision

- P3-SM1T is the first executable test. It calls only `GETTHREADID()`, with
  one MPI rank and one OpenMP thread, inside the controlled UEL condition
  `JELEM=1, KSTEP=1, KINC=1`. It writes markers immediately before and after
  the call. No `GETRANK` call is present.
- P3-SM1R is design-only. It may be considered only after the P3-SM1T result
  is committed and reviewed. It would call `GETRANK` in the same controlled
  element-callback context, never from `UEXTERNALDB`. This preparation creates
  neither an executable P3-SM1R lane nor authorization.
- P3-T4 remains blocked until both utilities are qualified or their
  limitations are explicitly documented.

## Consequences

Changing one utility and one call location at a time preserves causal
isolation. P3-SM1T is prepared but unauthorized; `GETTHREADID` remains
unqualified until a separately authorized execution.
