# Corrected T5 automation smoke result

Job `1376758.mmaster02` (`t5_h0_smoke`) completed on 2026-07-22 with PBS
`Exit_status=0`.

## Scheduler result

- Queue: `normal_imfdfkmq`, submitted through `entry_imfdfkmq`.
- Host: `mnode103/0*4`.
- Requested resources: 4 CPUs, 16 GB, walltime 01:00:00.
- Used resources: walltime 00:00:16, CPU time 00:00:14, memory 225000 KB,
  virtual memory 857752 KB.
- Timing: queued at Wed Jul 22 05:30:29 2026, started at Wed Jul 22
  09:04:20 2026, finished at Wed Jul 22 09:04:42-09:04:43 2026.
- Notifications: manual login-side Telegram `SUBMITTED` was sent while queued;
  in-job completion reached `T5_PASS`.

## Technical result

- Classification: `automation_smoke_pass`.
- Scope: workflow smoke only; not a thesis fracture reference comparison.
- Solver executed: true.
- Notch length: 0.45 mm.
- Static validation: pass.
- Physical elements: 1600.
- Layered elements: 4800.
- Notch topology: exact `y=0` line present, split notch faces present.
- Notch free-face nodes: 18 lower and 18 upper.
- Elastic probe: `U_probe=9.9999997e-05`, `RF2=0.0147068165243`,
  `K_probe=147.0681696550451`.

## Evidence files

- `runs/hpc/stage_c2/automation_smoke/T5_CORRECTED_QSTAT_FINAL.txt`
- `runs/hpc/stage_c2/automation_smoke/T5_CORRECTED_SUBMISSION_RECORD.txt`
- `runs/hpc/stage_c2/automation_smoke/pbs_output/stage_d_t5_corrected_20260722T053028/t5_corrected.out`
- `runs/hpc/stage_c2/automation_smoke/h0_notch045/AUTOMATION_SMOKE_REPORT.md`
- `runs/hpc/stage_c2/automation_smoke/h0_notch045/AUTOMATION_SMOKE_STATUS.json`
- `runs/hpc/stage_c2/automation_smoke/h0_notch045/DECK_VALIDATION.json`
- `runs/hpc/stage_c2/automation_smoke/h0_notch045/ELASTIC_PROBE_RF_U.csv`
- `runs/hpc/stage_c2/automation_smoke/h0_notch045/static_validation/STATIC_VALIDATION.md`
- `runs/hpc/stage_c2/automation_smoke/h0_notch045/static_validation/STATIC_VALIDATION.json`
