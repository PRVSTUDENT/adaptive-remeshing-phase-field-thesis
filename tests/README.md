# Starter Tests

The first test layer is pure Python and does not require Abaqus:

```powershell
python scripts/validation/check_literature_index.py --dry-run
python scripts/validation/validate_manifest.py configs/run_manifest.example.json --dry-run
python scripts/preprocessing/check_deck_integrity.py --dry-run
```

Future tests should add sample invalid manifests, deck fixtures, and postprocessing fixtures before production Abaqus runs.
