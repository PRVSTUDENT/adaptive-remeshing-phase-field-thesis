# Equation and Variable Convention Map

Status: starter map; complete from original papers before code changes.

| Quantity | Molnar/Gravouil | Msekh et al. | Pandey/Kumar | Diddige/Roth/Kiefer | Project decision |
|---|---|---|---|---|---|
| Phase-field variable | `d`, `0` intact, `1` broken | pending extraction | pending extraction | pending extraction | Use source-specific convention; never silently reverse |
| Displacement DOFs | pending extraction | pending extraction | pending extraction | pending extraction | Record per element type |
| Phase-field DOF | pending extraction | pending extraction | pending extraction | pending extraction | Record UEL DOF index |
| Degradation function | pending extraction | pending extraction | pending extraction | pending extraction | Choose from baseline source first |
| Crack density functional | pending extraction | pending extraction | pending extraction | pending extraction | Do not mix without decision record |
| Energy split | pending extraction | pending extraction | pending extraction | pending extraction | Hold fixed in baseline |
| History/irreversibility | pending extraction | pending extraction | pending extraction | pending extraction | Must pass no-healing check |
| State variables | pending extraction | pending extraction | pending extraction | pending extraction | Inventory before transfer |
| Output variables | pending extraction | pending extraction | `MISESERI`, `MISESAVG`, `S`, `EVOL`, `U`, `RF`, `SDV` | pending extraction | Include minimum requested outputs in manifests |

## Rules

- Every implementation run must name its convention, degradation law, energy split, and state layout.
- Transfer tests must define the source and target location of each field.
- Visualization transfer is not physical state transfer.
