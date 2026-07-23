# D3D datacheck job 1377515 — gate review

**Job:** `1377515.mmaster02`  
**PBS Exit_status:** `10` (wrapper gate, not Abaqus RC)  
**Classification recorded:** `stage_d3d_datacheck_fail`  
**Wrapper failure:** `ANALYSIS DATACHECK COMPLETE token missing`

## Abaqus outcome (scientific / technical)

From preserved logs:

| Check | Result |
|-------|--------|
| Compile complete | Yes (`End Compiling Abaqus/Standard User Subroutines`) |
| Link complete | Yes (`End Linking Abaqus/Standard User Subroutines`) |
| Input processing complete | Yes (`End Analysis Input File Processor`) |
| `Abaqus JOB D3D_DATACHECK COMPLETED` | Present in stdout |
| `ANALYSIS DATACHECK COMPLETE` | Present in **`.dat`** (not stdout/msg) |
| `D3A3-R2 H LOAD COMPLETE 25600` | Present in **`.msg`** |
| EOF / read-error tokens | Absent |
| Runtime-H SHA | `e4e2b277…` unchanged from R4 |

## Root cause

The PBS post-check grepped only stdout / msg / log for
`ANALYSIS DATACHECK COMPLETE`. Abaqus 2023 writes that token to the **`.dat`**
file. The Abaqus process itself completed successfully.

## Corrective action

Update `14_d3d_active_set_segment_datacheck.pbs` to also search `.dat`, and
require the stdout `Abaqus JOB D3D_DATACHECK COMPLETED` token. Preserve this
failed-wrapper evidence, then submit **one** corrected datacheck.

## Authorization note

This is a **wrapper gate correction**, not a model/deck change and not an
automatic second segment. Full D3D segment remains blocked until a committed
`stage_d3d_datacheck_pass`.
