# Session report: Stage F10 corrected minimal qualification

Starting SHA: `476885c119c6d585fffa5b26d0b902abe4f6d295`
Preparation SHA: `3ca7f4f4dc80cf9c44d090a27394cf1e76d506d8`
Authorization SHA: `1b0c585d83d65433193dda6b90d19a30f21af516`
Submission SHA: `44e9e540b35123fce3694f6fe0a9c7bc97915ccd`
Evidence SHA: `0da604a74929626034907b931a4d4b61b9cc4bde`
Run ID: `F10_20260731_060443_3ca7f4f`

Exactly three orchestrated qsub invocations succeeded:
`1380091.mmaster02`, `1380092.mmaster02`, and `1380093.mmaster02`.
There were zero failed invocations, retries, further replacements, direct
qsubs, qdel calls, and qmove calls.

Both small analyses completed using the corrected 23-element mapping and no
bounds guard fired. The candidate suppressed meaningful fixed-point healing
below `1e-7` without a cutback or material RF--U change, but energy and
penalty diagnostics were absent. Classification:
`irreversibility_candidate_inconclusive`; medium H1 is not eligible.

The CAE-only job passed staged-path/no-solver audits and then stopped before
the type matrix because `__file__` was undefined. Classification:
`remeshing_rule_variables_type_unresolved`; all execution counts are zero.

All submission authority is consumed.

The thesis master compiled successfully with bundled Tectonic. The generated
PDF has 38 pages; only pre-existing layout warnings were emitted.
