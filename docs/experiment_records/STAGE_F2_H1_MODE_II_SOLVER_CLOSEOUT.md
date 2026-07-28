# Stage F2 H1 Mode-II Uniform Reference Solver Closeout Report

**Date:** 2026-07-28  
**Agent:** gemini-antigravity  
**Task ID:** `F2-H1-SOLVER-CLOSE` (Job Task `F2-H1-SOLVER`)  
**Stage:** Stage F (Mode-II Pure Shear Reference)  
**Job ID:** `1379433.mmaster02`  
**Job Name:** `mode_ii_h1_serial`  

---

## 1. Executive Summary

This report documents the closeout, evidence collection, technical validation, and scientific classification for the Stage F Mode-II H1 uniform reference solver job `1379433.mmaster02`.

- **Scheduler Exit:** `12` (PBS wrapper exit code due to CLI argument mismatch during in-script extraction)
- **Abaqus Solver Code:** `0` (`Abaqus JOB mode_ii_h1_serial COMPLETED` successfully after 2,500 increments)
- **Offline Extractor Code:** `0` (re-extracted successfully using `extract_molnar_single_notch.py`)
- **Scientific Validator Code:** `1` (`stage_f_mode_ii_h1_uniform_serial_validation_fail`)
- **Final Classification:** `stage_f_mode_ii_h1_uniform_serial_validation_fail` (or `stage_f_mode_ii_h1_uniform_solver_fail`)

---

## 2. Job Identification and Provenance

| Property | Value |
|---|---|
| Task ID | `F2-H1-SOLVER` |
| Stage | Stage F |
| Job ID | `1379433.mmaster02` |
| Job Name | `mode_ii_h1_serial` |
| Authorization Revision | `1ed032b6599c7218038d2107ebc6f2dc1c8a1a5a` |
| Submission Revision | `b1d91e95eac1f496350f9db380963d76e7ac34e7` |
| Package Path | `models/generated/mode_ii/h1_uniform_serial` |
| Execution Lane | `runs/hpc/stage_f/mode_ii_h1` |

---

## 3. Scheduler & Hardware Resource Execution

| Resource Parameter | Requested | Actual Used |
|---|---|---|
| Queue | `entry_imfdfkmq` | `normal_imfdfkmq` (routed) |
| Execution Host | `mnode104/0` | `mnode104/0` |
| CPUs / Ranks / Threads | 1 CPU / 1 MPI / 1 OMP | 1 CPU / 1 MPI / 1 OMP |
| Memory | 32 GB | 1,064,056 KB (~1.01 GB) |
| Walltime | 06:00:00 | 00:42:59 |
| CPU Time | N/A | 00:41:26 |

---

## 4. Technical Solver and Extractor Analysis

1. **Abaqus Solver:**
   - Compiled with Intel Fortran 2021.13.0 and linked with GCC 11.4.0 on Abaqus 2023.
   - Completed Step 1 (500 increments) and Step 2 (2,000 increments) for a total of 2,500 increments.
   - Printed `THE ANALYSIS HAS COMPLETED SUCCESSFULLY` in `mode_ii_h1_serial.sta`.

2. **Wrapper Extractor Mismatch:**
   - In `mode_ii_h1_serial.pbs`, `abaqus python extract_molnar_single_notch.py` was invoked with positional ODB path and `--config`, which `extract_molnar_single_notch.py` rejected.
   - The PBS script caught `EXT_RC=2` and exited with `12`.
   - Offline extraction using correct CLI parameters (`--odb`, `--sta`, `--dat`, `--msg`, `--output-dir`, `--displacement-component 1`, `--reaction-component 1`) ran cleanly on the login node.

---

## 5. Scientific Results & Acceptance Evaluation

| Metric | Target / Criterion | Obtained Value | Gate Status |
|---|---|---|---|
| Final $U_1$ Displacement | $0.010\text{ mm}$ | $0.0099999998\text{ mm}$ | PASS |
| Peak Reaction Force $RF_1$ | Monitored | $0.121383\text{ kN}$ @ $U_1 = 0.010\text{ mm}$ | Monitored |
| Maximum Phase Damage $\max(d)$ | $\ge 0.50$ | $0.274662$ (SDV15) | FAIL (Pre-peak) |
| Spatial Crack Path Rows ($d \ge 0.5$) | $> 0$ | 0 | FAIL (Pre-peak) |
| Irreversibility Violations | 0 | 0 | PASS |

### Interpretation
For $h_1 = 0.0025\text{ mm}$ and length scale $\ell_c = 0.015\text{ mm}$, the applied endpoint $U_1 = 0.010\text{ mm}$ is early initiation / pre-peak. The maximum phase-field damage reached $d = 0.2747$, which does not cross the crack-path threshold $d \ge 0.5$.

---

## 6. Primary Figures and Artifacts

- **RF1–U1 Response:** [rf1_u1_response.png](file:///D:/Master%20thesis/Adaptive%20remeshing/results/figures/mode_ii_h1/1379433.mmaster02/rf1_u1_response.png)
- **Phase Field Evolution:** [phase_field_sdv15_evolution.png](file:///D:/Master%20thesis/Adaptive%20remeshing/results/figures/mode_ii_h1/1379433.mmaster02/phase_field_sdv15_evolution.png)
- **Canonical Evidence Directory:** [1379433.mmaster02](file:///D:/Master%20thesis/Adaptive%20remeshing/runs/hpc/stage_f/mode_ii_h1/evidence/1379433.mmaster02/)
- **Evidence Inventory:** [EVIDENCE_FILE_INVENTORY.csv](file:///D:/Master%20thesis/Adaptive%20remeshing/runs/hpc/stage_f/mode_ii_h1/evidence/1379433.mmaster02/EVIDENCE_FILE_INVENTORY.csv)

---

## 7. Claim Boundary & Authorization Constraints

- **Establishes:** Technical completion of 2,500 increments for the 12,064-element $H_1$ uniform reference mesh on HPC node `mnode104/0`.
- **Does Not Establish:** Full crack propagation or post-peak softening (which require an extended loading endpoint).
- **Authorization Boundary:** No automatic retry or extra submission is authorized (`maximum_jobs_now = 0`, `automatic_retry_authorized = false`).
