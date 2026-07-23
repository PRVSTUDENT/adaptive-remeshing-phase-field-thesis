# D3A3-R2 Forensic Replay Report

Classification: `stage_d3a3_r2_ingestion_pass_release_not_accepted`

This replay used the preserved `1377396.mmaster02` ODB only. No Abaqus/Standard solve, Fortran compilation, transfer package generation, or mesh generation was performed.

Corrected ingestion findings:

- SDV15 transfer max error: `1.3877787807814457e-17`
- SDV16 transfer max error: `0.0`
- H decrease violations: `0`
- d-healing violations after release: `4651`

Compatibility findings:

- F1 residual L2 norm: `3.173013579358624e-08`
- Maximum residual: `1.0654297154470889e-06` at node `3321`
- Correlation between F1 residual and released d change: `-0.7125040883621269`

No canonical `D3A3.ok` marker was created because released phase healing remains nonzero.
