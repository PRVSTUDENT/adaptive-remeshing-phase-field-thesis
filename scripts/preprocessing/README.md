# Preprocessing Scripts

Deck generation and integrity tools. Scripts that rewrite input decks support `--dry-run` where practical.

## Unified full-generation pipeline (Stage C preparation)

| Script | Role |
|---|---|
| `build_molnar_unified_deck.py` | Config-driven full pipeline: physical mesh → U1 → U2 → CPS4 → sets/BC → outputs → Fortran `N_ELEM` |
| `check_deck_integrity.py` | Lightweight keyword/set token checker |
| `../validation/validate_molnar_unified_deck.py` | Full static layered-deck validator |

Authoritative config:

```text
configs/preprocessing/molnar_h0_h1_unified.yaml
```

### Mesh roles (supervisor 1A)

| Role | Physical mesh source | Use |
|---|---|---|
| H0 | Author supplementary parsed topology | Development / testing / debug |
| H1 | Graded mesh builder | Production / report / Stage C reference |
| H2-PUB | Graded mesh builder | Fine RF–U validation only |

### Commands

```text
# Full H0 generation (scientifically equivalent to frozen H0)
python scripts/preprocessing/build_molnar_unified_deck.py --mesh-role H0

# Gate P1: generate H0 twice, require byte identity
python scripts/preprocessing/build_molnar_unified_deck.py --mesh-role H0 --gate-p1

# H0 + H1 and family compare
python scripts/preprocessing/build_molnar_unified_deck.py --all-default-roles

# MISESERI pre-analysis output profile (separate folder)
python scripts/preprocessing/build_molnar_unified_deck.py --mesh-role H0 --output-profile miseseri_preanalysis

# Static validation
python scripts/validation/validate_molnar_unified_deck.py \
  --deck models/generated/molnar_gravouil_2017/unified_preprocessing/H0_fullgen/H0_fullgen.inp \
  --fortran models/generated/molnar_gravouil_2017/unified_preprocessing/H0_fullgen/H0_fullgen.for \
  --role H0
```

### Outputs

```text
models/generated/molnar_gravouil_2017/unified_preprocessing/
  H0_fullgen/
  H0_fullgen_miseseri_preanalysis/
  H1_fullgen/
  gate_p1_full/GATE_P1_FULL_REPORT.json
  H0_H1_FAMILY_COMPARE.json
```

### Authorization boundary

```text
Stage C preparation: authorized
HPC submission: not authorized from these scripts
```
