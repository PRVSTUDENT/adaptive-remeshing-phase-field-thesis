# Diddige, Roth, and Kiefer (2025)

Source file: `Literature review/1-s2.0-S0045782525004153-main.pdf`

## Thesis Role

IMFD multi-field UEL architecture and ABAQUSER post-processing context. The hydrogen-specific formulation is not the baseline fracture model, but the implementation architecture and post-processing discipline are thesis-relevant.

## Extract Before Implementation

- Multi-field primary variable organization.
- UEL interface conventions relevant to IMFD code style.
- ABAQUSER variable exposure, naming, interpolation, and verification practice.
- Post-processing checks that can be reused for phase-field and mechanical quantities.

## Starter Decisions

- Use for ABAQUSER integration planning after the baseline and remeshing scripts are stable.
- Do not import hydrogen-specific physics into the brittle-fracture baseline unless the supervisor explicitly expands scope.

## Open Extraction Items

- Minimal ABAQUSER test case definition.
- Independent extraction quantities for numerical verification.
