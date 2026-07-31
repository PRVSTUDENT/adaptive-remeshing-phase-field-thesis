# Stage F9 minimal-patch datacheck root cause

PBS job `1380088.mmaster02` completed the five-case bounded matrix with exit
status zero and no analysis execution. The exact reproduction returned 1
with signal 11. The diagnostic compiler case returned 1 with signal 6 and
captured the decisive Intel bounds diagnostic:

`Subscript #1 of the array USRVAR has value -33828 which is less than the lower bound of 1`.

The call stack places the access in `uel_`. The value is exactly
`24 - 33852`: Abaqus supplies contiguous user-element numbering to this
minimal UEL population, so the first displacement UEL is `JELEM=24`, not the
deck label `33853`. The frozen source then evaluates `JELEM-N_ELEM` and
accesses outside `USRVAR`.

The static deck-label audit still passes. It is the runtime UEL `JELEM`
contract, not the written deck labels, that invalidates the offset assumption
in this reduced model. The UMAT-only initialization control passed
datacheck. The generated UEL-only controls stopped during input processing
because residual output requests were not removed completely; they are
preserved as invalid controls.

Classification: `minimal_patch_debug_bounds_violation_identified`.

No corrected baseline or penalty package was prepared automatically.
