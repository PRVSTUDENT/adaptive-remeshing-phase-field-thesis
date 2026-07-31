# Evidence and Scratch Inventories Summary

Updated: 2026-07-31

## Tracked Jobs

| Task ID | Job ID | Classification | Scratch Path |
|---|---|---|---|
| F1-J0 | `1378911.mmaster02` | `stage_f_mode_ii_h0_datacheck_pass` | `/scratch/pr21vyci/adaptive-remeshing/runs/mode_ii_h0_dc_1378911.mmaster02` |
| F1-J1 | `1378919.mmaster02` | `stage_f_mode_ii_h0_serial_staging_fail` | `/scratch/pr21vyci/adaptive-remeshing/runs/mode_ii_h0_serial_1378919.mmaster02` |
| F1-J1-R1 | `1378920.mmaster02` | `stage_f_mode_ii_h0_serial_staging_fail` | `/scratch/pr21vyci/adaptive-remeshing/runs/mode_ii_h0_serial_1378920.mmaster02` |
| F1-J1-R2 | `1378942.mmaster02` | `stage_f_mode_ii_h0_second_replacement_fail` | `/scratch/pr21vyci/adaptive-remeshing/runs/mode_ii_h0_serial_1378942.mmaster02` |
| F1-C2-DATACHECK | `1378958.mmaster02` | `stage_f_mode_ii_h0_endpoint_corrected_datacheck_stage_fail` | `/scratch/pr21vyci/adaptive-remeshing/runs/mode_ii_h0_endpoint_corrected_datacheck_1378958.mmaster02` |
| F1-C2-R1-DATACHECK | `1379387.mmaster02` | `stage_f_mode_ii_h0_endpoint_corrected_datacheck_replacement_pass` | `/scratch/pr21vyci/adaptive-remeshing/runs/mode_ii_h0_endpoint_corrected_datacheck_1379387.mmaster02` |
| F1-C2-R1-SOLVER | `1379393.mmaster02` | `stage_f_mode_ii_h0_endpoint_corrected_serial_baseline_pass` | `/scratch/pr21vyci/adaptive-remeshing/runs/mode_ii_h0_endpoint_corrected_serial_1379393.mmaster02` |
| F2-H1-DATACHECK | `1379431.mmaster02` | `stage_f_mode_ii_h1_uniform_datacheck_pass` | `/scratch/pr21vyci/adaptive-remeshing/runs/mode_ii_h1_dc_1379431.mmaster02` |
| F2-H1-SOLVER | `1379433.mmaster02` | `stage_f_mode_ii_h1_uniform_serial_validation_fail` | `/scratch/pr21vyci/adaptive-remeshing/runs/mode_ii_h1_serial_1379433.mmaster02` |
| F2-H1-ENDPOINT-SWEEP-BATCH | `1379481.mmaster02` | `stage_f_mode_ii_h1_technical_pass_postpeak_overshoot_warning` | `/scratch/pr21vyci/adaptive-remeshing/runs/mode_ii_h1_sweep_u015_1379481.mmaster02` |
| F2-H1-ENDPOINT-SWEEP-BATCH | `1379482.mmaster02` | `stage_f_mode_ii_h1_technical_pass_postpeak_overshoot_warning` | `/scratch/pr21vyci/adaptive-remeshing/runs/mode_ii_h1_sweep_u020_1379482.mmaster02` |
| F2-H1-ENDPOINT-SWEEP-BATCH | `1379483.mmaster02` | `stage_f_mode_ii_h1_technical_pass_postpeak_overshoot_warning` | `/scratch/pr21vyci/adaptive-remeshing/runs/mode_ii_h1_sweep_u030_1379483.mmaster02` |
| F2-H1-ENDPOINT-SWEEP-BATCH | `1379484.mmaster02` | `stage_f_mode_ii_h1_technical_pass_postpeak_overshoot_warning` | `/scratch/pr21vyci/adaptive-remeshing/runs/mode_ii_h1_sweep_u040_1379484.mmaster02` |
| F5-H2-COMPILER-DATACHECK-SMOKE-EXECUTE | `1379939.mmaster02` | `stage_f5_h2_compiler_datacheck_smoke_pass` | `/scratch/pr21vyci/adaptive-remeshing/runs/stage_f5/F5CMP_20260730_113544_e8a1d32/h2_compiler_datacheck` |
| F6-H2-FULL-AND-MISESERI-REMESH-API-BATCH | `1379966.mmaster02` | `stage_f_mode_ii_h2_uniform_serial_validation_fail` | `/scratch/pr21vyci/adaptive-remeshing/runs/stage_f6/F6_20260730_122800_2249ec21/h2_u020_full` |
| F6-H2-FULL-AND-MISESERI-REMESH-API-BATCH | `1379967.mmaster02` | `abaqus_cae_start_failure` | `/scratch/pr21vyci/adaptive-remeshing/runs/stage_f6/F6_20260730_122800_2249ec21/miseseri_remesh_api` |

## Summary Notes

- `1378911.mmaster02`: Stage F Mode-II datacheck passed; scratch retained.
- `1378919.mmaster02`: Stage F Mode-II serial job stopped pre-solver (`abaqus_return_code: -1`); scratch retained.
- `1378920.mmaster02`: Stage F Mode-II replacement serial job stopped pre-solver (`abaqus_return_code: -1`) with inline Python KeyError (`stage_f_mode_ii_h0_serial_staging_fail`); scratch retained.
- `1378942.mmaster02`: Stage F Mode-II second replacement serial job completed Abaqus solver and extraction (`abaqus_rc: 0`, `extractor_rc: 0`) up to $U_1 = 0.007\text{ mm}$, but failed scientific result validation (`validator_rc: 20`, `stage_f_mode_ii_h0_second_replacement_fail`); scratch retained.
- `F1-C0-ENDPOINT-AUDIT`: Proved loading schedule endpoint mismatch ($U_1 = 0.007\text{ mm}$ vs $0.010\text{ mm}$ expected); selected Option A correction (Amp-2 endpoint $0.2$).
- `F1-C1-CORRECTED-H0-PREP`: Offline corrected package generation and fail-closed lane qualification completed (`stage_f_mode_ii_h0_endpoint_corrected_prepared_unauthorized`); no HPC jobs or Abaqus runs executed.
- `1378958.mmaster02`: Stage F Mode-II endpoint-corrected datacheck job stopped preflight (`abaqus_rc: 3`, `stage_f_mode_ii_h0_endpoint_corrected_datacheck_stage_fail`) due to missing `-v PRESTAGED_ROOT` submit wrapper arguments; scratch retained; evidence collected.
- `F1-C2-R1-PREP`: Offline staging contract remediation completed (`stage_f_mode_ii_h0_endpoint_corrected_datacheck_replacement_prepared_unauthorized`); submit wrapper updated to pass required `-v PRESTAGED_ROOT=...,LOGIN_MANIFEST_PATH=...,PROJECT_REVISION=...`; static validator, mocked qsub tests, local staging smoke, and cluster-login smoke passed; 0 HPC jobs executed.
- `1379387.mmaster02`: Stage F Mode-II endpoint-corrected replacement datacheck completed cleanly (`Exit_status: 0`, `abaqus_return_code: 0`, `DATACHECK_ok: true`); scratch retained.
- `F1-C2-R1-SOLVER-PREP`: Offline serial solver staging contract remediation completed (`stage_f_mode_ii_h0_endpoint_corrected_serial_solver_contract_prepared_unauthorized`); submit wrapper updated to prestage package + runtime scripts and pass `-v PRESTAGED_ROOT=...,LOGIN_MANIFEST_PATH=...,PROJECT_REVISION=...,PRESTAGED_RUNTIME_ROOT=...`; static validator, 195 unit tests, and local solver staging smoke passed; 0 HPC jobs executed.
- `1379393.mmaster02`: Corrected Mode-II H0 serial solver completed FE execution cleanly (`abaqus_rc: 0`, `extractor_rc: 0`, 2000 increments, $U_1 = 0.0100\text{ mm}$, $F_{1,\max} = 0.3733\text{ kN}$, $\max(d) = 0.9909 \ge 0.50$); offline validator corrected in task F1-C2-R1-H0-VALIDATOR-FIX (`stage_f_mode_ii_h0_endpoint_corrected_serial_baseline_pass`); scratch retained.
- `F2-H1-BASELINE-PREP`: Stage F Mode-II H1 endpoint-corrected baseline preparation completed offline (`stage_f_mode_ii_h1_endpoint_corrected_prepared`); H1 package ($h_1 = 0.0025\text{ mm}$, `N_ELEM = 12064`, $U_1 = 0.010\text{ mm}$), PBS execution script with Telegram notification traps, H1 validator, and 10 unit tests qualified; 0 HPC jobs executed.
- `1379431.mmaster02`: Stage F Mode-II H1 uniform reference datacheck completed cleanly (`Exit_status: 0`, `abaqus_return_code: 0`, `DATACHECK_ok: true`); scratch retained.
- `1379433.mmaster02`: Stage F Mode-II H1 uniform reference serial solver completed FE execution cleanly (`abaqus_rc: 0`, 2,500 increments, $U_1 = 0.0100\text{ mm}$, $RF_1 = 0.1214\text{ kN}$, $\max(d) = 0.2747 < 0.50$); wrapper exit 12 due to CLI argument mismatch during in-script extraction; scientific classification `stage_f_mode_ii_h1_uniform_serial_validation_fail`; scratch retained.
- `1379481.mmaster02`, `1379482.mmaster02`, `1379483.mmaster02`, `1379484.mmaster02`: Stage F Mode-II H1 4-job endpoint sweep ($U_1 \in \{0.015, 0.020, 0.030, 0.040\}\text{ mm}$) completed FE execution cleanly (`abaqus_rc: 0`, `extractor_rc: 0`). Peak $RF_1 = 0.1398\text{ kN}$ at $U_1 = 0.0120\text{ mm}$ across all 4 jobs; force drops reached 25.22%, 41.89%, 73.99%, and 88.07%; wrapper exit 12 due to validator $\text{SDV15} \le 1.0$ upper bound check ($\text{SDV15} = 1.00498$); scratch retained.
- `1379939.mmaster02`: exact frozen H2 user subroutine compiled and linked with ifort 2021.13.0 under Abaqus 2023 and datacheck passed (`Exit_status: 0`, `abaqus_return_code: 0`); lightweight evidence retained in the repository while ODB and binary databases remain scratch-only.
- `1379966.mmaster02`: full H2 u020 Abaqus solve and extraction passed, but offline validation failed the declared framewise maximum-damage irreversibility gate (11 decreases; largest `-1.0073e-4`). The 943,852,504-byte ODB remains scratch-only; 30 lightweight evidence files were inventoried.
- `1379967.mmaster02`: Abaqus/CAE driver arguments stopped the API script before source/API audit; no solver, native remesh, or candidate deck.
