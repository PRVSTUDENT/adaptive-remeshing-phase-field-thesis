# Evidence and Scratch Inventories Summary

Updated: 2026-07-26

## Tracked Jobs

| Task ID | Job ID | Classification | Scratch Path |
|---|---|---|---|
| F1-J0 | `1378911.mmaster02` | `stage_f_mode_ii_h0_datacheck_pass` | `/scratch/pr21vyci/adaptive-remeshing/runs/mode_ii_h0_dc_1378911.mmaster02` |
| F1-J1 | `1378919.mmaster02` | `stage_f_mode_ii_h0_serial_staging_fail` | `/scratch/pr21vyci/adaptive-remeshing/runs/mode_ii_h0_serial_1378919.mmaster02` |
| F1-J1-R1 | `1378920.mmaster02` | `stage_f_mode_ii_h0_serial_staging_fail` | `/scratch/pr21vyci/adaptive-remeshing/runs/mode_ii_h0_serial_1378920.mmaster02` |
| F1-J1-R2 | `1378942.mmaster02` | `stage_f_mode_ii_h0_second_replacement_fail` | `/scratch/pr21vyci/adaptive-remeshing/runs/mode_ii_h0_serial_1378942.mmaster02` |

## Summary Notes

- `1378911.mmaster02`: Stage F Mode-II datacheck passed; scratch retained.
- `1378919.mmaster02`: Stage F Mode-II serial job stopped pre-solver (`abaqus_return_code: -1`); scratch retained.
- `1378920.mmaster02`: Stage F Mode-II replacement serial job stopped pre-solver (`abaqus_return_code: -1`) with inline Python KeyError (`stage_f_mode_ii_h0_serial_staging_fail`); scratch retained.
- `1378942.mmaster02`: Stage F Mode-II second replacement serial job completed Abaqus solver and extraction (`abaqus_rc: 0`, `extractor_rc: 0`) up to $U_1 = 0.007\text{ mm}$, but failed scientific result validation (`validator_rc: 20`, `stage_f_mode_ii_h0_second_replacement_fail`); scratch retained.
- `F1-C0-ENDPOINT-AUDIT`: Proved loading schedule endpoint mismatch ($U_1 = 0.007\text{ mm}$ vs $0.010\text{ mm}$ expected); selected Option A correction (Amp-2 endpoint $0.2$).
- `F1-C1-CORRECTED-H0-PREP`: Offline corrected package generation and fail-closed lane qualification completed (`stage_f_mode_ii_h0_endpoint_corrected_prepared_unauthorized`); no HPC jobs or Abaqus runs executed.

