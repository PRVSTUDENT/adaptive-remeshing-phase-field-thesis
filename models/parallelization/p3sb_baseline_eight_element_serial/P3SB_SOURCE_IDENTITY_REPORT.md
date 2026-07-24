# P3-SB package identity report

## Hashes

| Artifact | SHA-256 | Identity result |
|---|---|---|
| `P3SB_baseline_serial.inp` | `bd8c487e94636ccf1833a65aa8db40aaecad8baeeda21e4bfe9d3ec29f4922ae` | Byte-identical to the staged P3-S deck |
| `p3sb_baseline_uel.for` | `473f80e8f0f1cba6aa7a7f0c3a49aaa949bac43e03548096d9d6f0c9a6f80306` | Byte-identical to the accepted D2 source |
| `d2_transfer_table.inc` | `d1ccd478d635272215f7e9b1649bfcca3842fd5aa331d1bd3124a85395fc65f2` | Byte-identical to the staged P3-S and accepted D2 transfer table |

## Exact source differences from accepted D2

None. The comparison is byte-for-byte equal. `N_ELEM=8`, `NSTV=18`, `TRANSFER_MODE=1`, the eight-entry include name, UEL/UMAT calculations, and BLOCK DATA are already present in the accepted D2 source; P3-SB introduces no package-local source edit.

## Diagnostic-symbol exclusion

The P3-SB source contains none of:

`UEXTERNALDB`, `GETRANK`, `GETTHREADID`, `MUTEXINIT`, `MUTEXLOCK`, `MUTEXUNLOCK`, `KP2TRACE`, `KP3READ`, `KP3BEGINWRITE`, `KP3ENDWRITE`, `KP2DIAG`, or `KP3ACCESS`.

The input deck is the same eight-element deck used by P3-S. Its visualization layer is eight `CPS4` elements (`17` through `24`). Coverage validation derives those labels from the `umatelem` block and derives the CPS4 full-integration count from the actual element formulation.
