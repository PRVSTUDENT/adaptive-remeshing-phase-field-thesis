# D3A0 Existing H0 ODB Source Provenance

Classification: `stage_d3a0_existing_h0_source_ineligible`

No new Abaqus solve was performed. CAE/ODB-only D3A extraction later proved that
the source ODB lacks the energy history required by the D3A acceptance gate.

## Selected Source

The selected checkpoint source is the accepted H0 exact Molnar single-notch ODB
from the `lc=0.015 mm` h-convergence campaign:

```text
/scratch/pr21vyci/adaptive-remeshing/runs/molnar_lc015_h0_exact_1376154.mmaster02/molnar_lc015_h0_exact.odb
```

This is not the T5 `0.45 mm` notch smoke, not a C2 auxiliary continuum ODB, and
not H1/H2-PUB.

| Field | Value |
| --- | --- |
| Source job | `1376154.mmaster02` |
| CAE replay job | `1376236.mmaster02` |
| ODB size | `88827548` bytes |
| ODB SHA-256 | `01601effd2a110dc7124356cb3d9baf6d772d55f4fb344414ad219ba9b78e07b` |
| Input deck | `models/generated/molnar_gravouil_2017/h_convergence_lc015/H0_exact/SingleNotch.inp` |
| Input deck SHA-256 | `82c80c03c1b0b25131e9e0352502fb393bd593f9f07035c311f164ee9311f92e` |
| Fortran source | `models/generated/molnar_gravouil_2017/h_convergence_lc015/H0_exact/SingleNotch.for` |
| Fortran source SHA-256 | `516e5ce9a405c30e9d4b45f919f8c22e39cd36bcce102ca065837b81a1405088` |
| Git commit | `58d7e3102d76fe0e70e6729457e2c7e90ad131bb` |
| Abaqus release | Abaqus 2023 |
| Geometry | Molnar single notch |
| Notch length | `0.5 mm` |
| `lc` | `0.015 mm` |
| Physical elements | `3930` |
| Layered elements | `11790` |
| Maximum U2 | `0.007000000216066837 mm` |
| H0 peak RF2 | `0.7276078462600708` |
| U2 at H0 peak | `0.006099999882280827 mm` |

## Eligibility Decision

The provisional D3 checkpoint target is `U2 = 0.003 mm`, which lies before the
accepted H0 peak displacement. The deck requests RP `U`/`RF` and UMAT `SDV`
output, including the D3 routing fields `SDV15=d` and `SDV16=H`.

However, the original H0 deck does not request `ALLIE`, `ALLSE`, or `ALLWK`.
The corrected D3A extraction selected an exact checkpoint frame at
`U2=0.003000000026077032 mm` and extracted 15720 element/IP rows with finite
`SDV15` and `SDV16`, but validation failed because energy values were not
available. Therefore this existing H0 ODB is not eligible for accepted D3A
checkpoint extraction under the current gate.

Abaqus/Standard solving and UEL compilation were not performed.
