# Parallel Shared-State Map

Date: 2026-07-24
Evidence: `results/validation/stage_p_static_audit/`

| State/resource | Writers | Readers | Update point | Scope | Risk |
|---|---|---|---|---|---|
| `USRVAR(:,15,:)` | phase UEL | UEL, UMAT | element call | COMMON in one process | concurrent read/write; layer ordering not guaranteed |
| `USRVAR(:,16,:)` | initialization UEL, UMAT/history paths | UEL, UMAT | first increment and material calls | COMMON in one process | non-atomic max/check/update |
| `TRANSFER_DONE(:)` | UEL | UEL | first increment | COMMON in one process | check-then-write race |
| COMMON/SAVE/DATA storage | BLOCK DATA and routines | multiple routines | load and runtime | process-local | separate copies under MPI; thread sharing under threads |
| external files | UEXTERNALDB and diagnostic variants | external consumers/routines | callback/runtime | filesystem | rank collision or interleaved thread writes |

## Required audit answers

1. **Can two calls write the same `USRVAR` location?** Yes. Repeated layer or
   integration-point calls can map to the same physical-element slot, and the
   source contains no ownership guard around all updates.
2. **Can a thread read while another writes?** The source permits it; no
   synchronization proves otherwise.
3. **Are phase, mechanical, and visualization layers guaranteed on the same
   thread?** No such guarantee is established by source or retained evidence.
4. **Are they guaranteed in the same MPI partition?** No. The mapping assumes
   process-local COMMON state and contains no rank communication.
5. **Is initialization exactly once?** `TRANSFER_DONE` intends once per
   physical element, but its check-then-write is not atomic. BLOCK DATA is
   process-local under MPI.
6. **Are file operations restricted to one thread/process?** Not generally.
   Preserved variants contain OPEN/READ/WRITE without a universal rank/thread
   ownership rule.

## Static scan boundary

The machine-readable scan found 365 matched records in 12 files. A match is a
review lead, not proof that every occurrence is unsafe. Conversely, absence
of a textual match cannot prove scheduling or call-order safety.
