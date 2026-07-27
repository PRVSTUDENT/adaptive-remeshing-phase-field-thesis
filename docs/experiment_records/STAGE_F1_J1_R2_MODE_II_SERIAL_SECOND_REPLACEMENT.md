# Stage F1-J1-R2 Mode-II H0 Serial Second Infrastructure Replacement Record

- **Stage**: Stage F (Mode-II mixed-mode benchmark)
- **Task ID**: `F1-J1-R2`
- **Job ID**: `1378942.mmaster02`
- **Operational Submission Revision**: `69d4d0a6ade66f4c0a1ea47020eb6e8916c11abd`
- **Authorization Revision**: `93fcad353693ca6348b2d683317c7da86d34d493`
- **Evidence Verifier Revision**: `7f61c182aaa480b20647410546007d0ee20a3132`
- **Package Path**: `models/generated/mode_ii/h0_serial`
- **Execution Host**: `mnode097/0`
- **Queue**: `entry_imfdfkmq` (routed to `normal_imfdfkmq`)
- **Resources**: 1 CPU, 16 GB RAM, walltime 04:00:00 requested
- **Actual Runtime**: Wallclock 16m 17s (919s), CPU time 835s (USER: 816s, SYS: 19s)
- **Abaqus Solver Exit Code**: `0` (clean solver completion)
- **Extractor Exit Code**: `0` (clean extraction completion)
- **Result Validator Exit Code**: `20` (`stage_f_mode_ii_h0_serial_validation_fail`)
- **Classification**: `stage_f_mode_ii_h0_second_replacement_baseline_characterized`

---

## Executive Summary

Job `1378942.mmaster02` executed the Mode-II H0 serial baseline package on cluster node `mnode097`. Unlike the earlier F1-J1 and F1-J1-R1 attempts which failed prior to Abaqus launch due to staging validation defects, job `1378942.mmaster02` completed the full Abaqus FE solver analysis cleanly (`abaqus_return_code: 0`) and ran the standalone extractor (`extractor_return_code: 0`).

The run successfully characterized the pre-peak Mode-II pure-shear load-displacement response across 72 curve points up to $U_1 = 0.0070\text{ mm}$ and a peak shear force of $RF_1 = 0.3063\text{ kN}$. The automatic result validator returned exit code 20 because:
1. The analysis reached Step-2 increment 2000 ($U_1 = 0.0070\text{ mm}$) which was the maximum step count defined in the H0 serial deck, whereas the general validator checks for $U_1 = 0.0100\text{ mm}$.
2. The damage field reached $\max(d) = 0.2992$, which is below the threshold of $d \ge 0.50$ required for crack-path extraction.

The runtime staging contract and pre-solver evidence chain passed with zero errors (`stage_f_mode_ii_h0_runtime_staging_pass`).

---

## Key Extracted Numerical Results

- **Load-Displacement Points**: 72 curve points extracted (`rf1_u1_curve.csv`).
- **Maximum Shear Force Reached**: $RF_1 = 0.3063\text{ kN}$ at $U_1 = 0.0070\text{ mm}$.
- **Matched States Extracted**:
  - **State 01 (Step 1, Inc 200)**: $U_1 = 0.0020\text{ mm}$, $RF_1 = 0.0921\text{ kN}$, $\max(d) = 0.0182$
  - **State 02 (Step 1, Inc 500)**: $U_1 = 0.0050\text{ mm}$, $RF_1 = 0.2253\text{ kN}$, $\max(d) = 0.1269$
  - **State 03 (Step 2, Inc 1000)**: $U_1 = 0.0060\text{ mm}$, $RF_1 = 0.2670\text{ kN}$, $\max(d) = 0.1972$
  - **State 04 (Step 2, Inc 2000)**: $U_1 = 0.0070\text{ mm}$, $RF_1 = 0.3063\text{ kN}$, $\max(d) = 0.2992$
- **Phase Bounds**: Min $d = 0.0$, Max $d = 0.2992$ (strictly irreversible, no phase-healing or history-decrease violations).
- **Distortion / Warnings**: 1 element distortion warning logged in `.msg` (`***WARNING: 1 elements are distorted`), 1 negative eigenvalue warning logged.

---

## Artifact & Evidence Inventory

- **Local Evidence Bundle**: `runs/hpc/stage_f/mode_ii_h0/replacement_r2/evidence/1378942.mmaster02/`
- **Key Status Records**:
  - [MODE_II_H0_SERIAL_STATUS.json](file:///D:/Master%20thesis/Adaptive%20remeshing/runs/hpc/stage_f/mode_ii_h0/replacement_r2/evidence/1378942.mmaster02/MODE_II_H0_SERIAL_STATUS.json)
  - [MODE_II_H0_SERIAL_VALIDATION.json](file:///D:/Master%20thesis/Adaptive%20remeshing/runs/hpc/stage_f/mode_ii_h0/replacement_r2/evidence/1378942.mmaster02/MODE_II_H0_SERIAL_VALIDATION.json)
  - [MODE_II_H0_RUNTIME_STAGING_CHECK.json](file:///D:/Master%20thesis/Adaptive%20remeshing/runs/hpc/stage_f/mode_ii_h0/replacement_r2/evidence/1378942.mmaster02/MODE_II_H0_RUNTIME_STAGING_CHECK.json)
- **Key Extracted CSVs**:
  - [rf1_u1_curve.csv](file:///D:/Master%20thesis/Adaptive%20remeshing/runs/hpc/stage_f/mode_ii_h0/replacement_r2/evidence/1378942.mmaster02/extracted/rf1_u1_curve.csv)
  - [matched_states.csv](file:///D:/Master%20thesis/Adaptive%20remeshing/runs/hpc/stage_f/mode_ii_h0/replacement_r2/evidence/1378942.mmaster02/extracted/matched_states.csv)
  - [single_notch_extraction_summary.json](file:///D:/Master%20thesis/Adaptive%20remeshing/runs/hpc/stage_f/mode_ii_h0/replacement_r2/evidence/1378942.mmaster02/extracted/single_notch_extraction_summary.json)
- **Scratch ODB Location**: `/scratch/pr21vyci/adaptive-remeshing/runs/mode_ii_h0_serial_1378942.mmaster02/mode_ii_h0_serial.odb` (110.55 MB)

---

## Conclusion & Boundary Status

The F1-J1-R2 replacement submission completed solver execution without staging or launch failures. The R2 authorization is now fully consumed (`solver_submissions_used: 1`). No further replacements or retries are permitted (`maximum_jobs_now: 0`). Downstream Stage F tasks (F2+) remain **blocked** pending review.
