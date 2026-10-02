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

- Obtain the authentic ABAQUSER software artifact and its license/runtime notes.
- Obtain a minimal UEL input, matching `.fil`, ABAQUSER information file, and
  expected `.odb` for version-compatible verification.

## Public Interface Recovery (2026-09-23)

The interface is no longer classified as wholly unknown. Roth et al. (2012)
documents ABAQUSER as a shell/Python post-processing package controlled by
`abaquser.sh`. The published route is binary `.fil` extraction, reconstruction
of assembly/instance ownership, decomposition of UEL SDVs by integration point
and physical field, mapping to standard-library dummy elements, and ODB
creation/update for Abaqus/Viewer.

The auxiliary information-file grammar includes `*DIM`, `*UEL`, `TYPE`,
`NUMIP`, `NUMSDV`, `NUMSDVPIP`, `ABADUMMY`, and `*SDV`, together with user-to-
dummy node/integration-point ordering and field name/description/rank/component
indices. Roth and Kiefer (2022) confirms CPE8 mappings for quadratic UELs and
CPE4 approximations for cubic UELs when no matching built-in element exists.

No attributable public source or executable package was located in targeted TU
Freiberg, GitHub, GitLab, Zenodo, Qucosa, or archive searches. Detailed record:
`docs/experiment_records/F1080RESEARCH_ABAQUSER_PUBLIC_ARTIFACT_DISCOVERY_RECORD.md`.

Current boundary:

- literature/interface concept: substantially recovered;
- authentic source/executable: not obtained;
- authentic integration/execution: still blocked and on hold.
