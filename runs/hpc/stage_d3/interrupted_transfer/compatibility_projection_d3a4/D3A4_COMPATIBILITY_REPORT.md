# D3A4 Constrained Phase Compatibility Report

Classification: `stage_d3a4_constrained_phase_compatibility_pass`

This is an offline sparse active-set obstacle solve using committed D3A3-R2 forensic evidence only. No Abaqus job, Fortran compilation, new mesh, or replacement of the original D3A2 package was performed.

Assembly audit:

- Nodes: `6601`
- Elements: `6400`
- Integration points: `25600`
- Maximum F1 residual reconstruction error: `2.329340604949326e-21`

KKT metrics:

- Active nodes: `1880`
- Free nodes: `4721`
- Free residual infinity norm: `7.623296525288703e-21`
- Minimum active multiplier: `3.1903130564656594e-13`
- Complementarity infinity norm: `8.649244021664495e-23`
- Maximum d increase: `0.011345805575019186`
- Normalized L2 d increase: `0.03901956109385224`

Functional:

- Compatible minus F1: `-2.4132803703716662e-08`
- Compatible reduction from F1: `2.4132803703716662e-08`

Compatible package:

- Prepared: `True`
- Directory: `runs/hpc/stage_d3/interrupted_transfer/package_compatible_r1/`

The canonical D3A3 gate remains closed until a separate bounded D3A3-R3 release test is authorized and passes.
