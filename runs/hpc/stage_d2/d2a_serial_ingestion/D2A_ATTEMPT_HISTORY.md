# D2A Attempt History

Stage D2A was the only D2 job submitted. D2B, D2C, and D2D were not submitted.

| Job | Result | Note |
|---|---:|---|
| `1376779.mmaster02` | `Exit_status=10` | Abaqus input preprocessor rejected the first visualization deck because reduced-integration CPS4R elements had zero hourglass stiffness. |
| `1376780.mmaster02` | `Exit_status=10` | Same CPS4R hourglass preprocessor failure after the first stiffness correction. |
| `1376781.mmaster02` | `Exit_status=13` | Abaqus solve completed, but validation failed because nodal phase was sought from Abaqus `U` output and full precision had not yet been enabled. |
| `1376782.mmaster02` | `Exit_status=12` | Abaqus solve completed, but extractor failed on full-precision ODB values until `dataDouble` handling was added. |
| `1376783.mmaster02` | `Exit_status=13` | Abaqus solve completed and IP state matched; validator still treated unavailable UEL nodal `U` output as a hard failure. |
| `1376785.mmaster02` | `Exit_status=0` | Final D2A pass: solver completed, ODB readable, `SDV15` matched transferred phase interpolation, `SDV16` matched transferred history, and `D2A.ok` was written. |

Final accepted classification: `stage_d2a_state_ingestion_pass`.
