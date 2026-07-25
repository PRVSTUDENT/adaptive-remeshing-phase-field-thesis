# Mode-II H0 serial technical package

Classification: `stage_f_mode_ii_h0_package_prepared`

## Scope

- Geometry/mesh: accepted Mode-I H0 supplementary single-notch mesh.
- Formulation: accepted Molnar staggered UEL/UMAT (`N_ELEM=3930`).
- Change: pure-shear loading (top U1 via RP; bottom fully fixed; top U2 fixed).
- No MISESERI remeshing in this package.
- No execution authorization.

## Files

- `ModeII_H0_serial.inp`
- `ModeII_H0_serial.for`
- `PACKAGE_MANIFEST.json`
- `input_hashes.sha256`
- `BENCHMARK_DEFINITION.md`

## Next gates

1. Offline static validator pass.
2. Fail-closed lane preparation.
3. Separate datacheck authorization-only commit before any submission.
