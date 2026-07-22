# T5 automation smoke failure and fixed guard

Original job: `1376598.mmaster02`

PBS result: `F`, `Exit_status=12`

Classification: `automation_smoke_static_guard_failed`

## What failed

The mesh generator and layered deck builder completed far enough to create a
valid-looking H0 notch-length variation mesh and nested layered output. The
failure occurred before Abaqus solver execution.

The PBS script searched only:

```bash
"${LAYERED}"/*fullgen.inp
"${LAYERED}"/*fullgen.for
```

but `build_molnar_unified_deck.py` writes the generated files below a role
subdirectory, for example:

```text
runs/hpc/stage_c2/automation_smoke/h0_notch045/layered/H0_refined_layered/H0_refined_fullgen.inp
runs/hpc/stage_c2/automation_smoke/h0_notch045/layered/H0_refined_layered/H0_refined_fullgen.for
```

Therefore `DECK` and `FOR` were empty. The validation call then effectively
validated `.` as the deck path, producing:

```text
IsADirectoryError: [Errno 21] Is a directory: '.'
```

The final inline guard wrote `static_validation: null` and exited with status
`12`.

## Fix

`scripts/hpc/stage_c2/t5_h0_automation_smoke.pbs` now discovers generated
artifacts recursively with `find`, sorts deterministically, and exits with an
explicit `generated_fullgen_deck_or_fortran_not_found` status if either file is
missing.

The general unified-deck validator now also has an explicit
`--allow-h0-refined-smoke` mode for this tiny 1600-element H0 refined smoke. This
keeps production `H0_refined` checks unchanged while allowing the smoke to pass
static validation without requiring the production refined-mesh size/corridor
assumptions.

Local static verification after the fix:

```text
python scripts/validation/validate_molnar_unified_deck.py \
  --config configs/preprocessing/molnar_h0_h1_unified.yaml \
  --deck tmp/t5_h0_notch045_static_check/layered/H0_refined_layered/H0_refined_fullgen.inp \
  --fortran tmp/t5_h0_notch045_static_check/layered/H0_refined_layered/H0_refined_fullgen.for \
  --role H0_refined \
  --allow-h0-refined-smoke \
  --out-dir tmp/t5_h0_notch045_static_check/static_validation_smoke
```

Result: `{"status": "pass", "failed": []}`.

## Rerun policy

T5 is preserved as failed guard evidence and does not invalidate Stage C. One
small T5 smoke rerun is permitted after the static verification above. Do not
alter the accepted C2C-v3 mesh and do not rerun C2F-v3 for this repair.
