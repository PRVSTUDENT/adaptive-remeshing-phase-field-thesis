# D3A-E Attempt History

Classification: stage_d3a_energy_reconstruction_fail

- 1376882.mmaster02: initial CAE-only energy reconstruction attempt. Cancelled after the extractor remained in the old repeated field-scan path without emitting checkpoint files. No Abaqus/Standard solve and no UEL compilation were performed.
- 1376885.mmaster02: corrected CAE-only energy reconstruction attempt using indexed ODB field lookups. Extraction and reconstruction completed; validation failed because five element/IP Jacobian determinants computed from the accepted H0 deck connectivity were non-positive.

No D3A.ok marker was created. D3A2 remains blocked.
