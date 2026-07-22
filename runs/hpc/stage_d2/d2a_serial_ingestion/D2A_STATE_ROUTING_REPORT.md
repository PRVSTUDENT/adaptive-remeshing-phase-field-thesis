# D2A State Routing Report

Classification: `stage_d2a_state_ingestion_pass`

- Job: `1376785.mmaster02`
- Target-node coverage: `0.0`
- Target element/IP coverage: `1.0`
- Nodal phase ODB output available: `False`
- Maximum nodal d error: `0.0`
- Maximum SDV15 interpolation error: `0.0`
- Maximum SDV16/H error: `6.428999999030793e-09`
- Failures: `0`
- Limitations: `1`

The pass/fail gate verifies phase ingestion through SDV15 because Abaqus does not expose the UEL phase DOF as usable nodal U output in this smoke deck.

D2A verifies transfer ingestion only; it is not a fracture response benchmark.
