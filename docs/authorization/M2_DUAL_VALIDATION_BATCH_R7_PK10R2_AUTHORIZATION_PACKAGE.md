# Authoritative Mode-II Dual Validation Batch Human-Authorization Package (R7 / PK10R2)

**Batch Name**: `M2_DUAL_VALIDATION_BATCH_R7_PK10R2`  
**Date Prepared**: 17 August 2026  
**Status**: `FROZEN / READY_FOR_HUMAN_AUTHORIZATION / NO_JOBS_SUBMITTED`  
**Authoring Agent**: `gemini-antigravity`  
**Superseded Predecessors**: `M2_DUAL_VALIDATION_BATCH_R6_PK10R2` and all prior draft packages (marked `SUPERSEDED`)  

---

## 1. Executive Summary & Batch Governance

This document constitutes the single active, authoritative human-authorization package for the concurrent execution of two scientifically independent Mode-II validation jobs:

1. **`M2CORR_PK10R1_SAMEMESH_RESTART_VALIDATION_R7`** (Same-mesh restart validation with exact reconstructed committed history and phase state).
2. **`M2CORR_PK10R2_TOPOLOGY_CORRECTED`** (Continuous Mode-II shear benchmark with sharp open slit and uniform quad process-zone mesh topology).

### Governance Rules & Limits
- **Maximum Total Submissions**: Exactly 2 (1 submission per job).
- **Automatic Retries**: `false` (strictly prohibited).
- **Queue Operations**: `qdel` and `qmove` are strictly prohibited.
- **Concurrent Execution Limit**: `maximum_simultaneous_running_jobs = 2` (1 core + 16 GB per job = 2 cores + 32 GB total RAM).
- **Cluster Resource Limits**: Requested Queue: `entry_imfdfkmq` (routes internally to `normal_imfdfkmq`), Walltime: `24:00:00`, Modules: `intel/2024.2.0`, `abaqus/2023`.

---

## 2. Hard Pre-Submission Notification Gate

Before any `qsub` command is issued for either candidate, the submission workflow must verify that both notification channels are fully active:

1. **PBS Email Notifications**:
   - Status: `pbs_email_notification_configured = true`
   - Trigger Events: `#PBS -m abe` (abort, begin, end)
   - Verified Recipients: `Pruthviraja.Reddy-Vandavagali@student.tu-freiberg.de,pr21vyci@mailserver.tu-freiberg.de`
2. **Telegram Webhook Integration**:
   - Status: `telegram_notification_configured = true`
   - Config file verified on cluster: `~/.config/adaptive-remeshing/notifications.env` and `notifications.json`
   - Pre-submission dry-run gate: `notification_pre_submission_gate_passed = true`
3. **Notification State Lifecycle Tracking**:
   - The workflow separately logs: `notification_configured`, `notification_gate_passed`, and `notification_delivery_observed`.

---

## 3. Job 1: Same-Mesh Restart Validation (Revision R7)

- **Job Name**: `M2CORR_PK10R1_SAMEMESH_RESTART_VALIDATION_R7`
- **Predecessor Classification**: `R6_status = SUPERSEDED_INVALID_COMMITTED_STATE_PACKAGE`, `R6_ready_for_human_authorization = false`.
- **Scientific Purpose**: Validate same-mesh restart state initialization under the 4-stage protocol using exact reconstructed Increment-29 committed history and phase state.

### Source-State & Trajectory Provenance
- **Primary State Source Job**: `1389707.mmaster02` (Replay trajectory, Step 1 Inc 29, $U_{1,\text{RP}} = 0.01014330\text{ mm}$)
- **Primary State Fields**: Nodal $U_1, U_2, U_3$ mapped into `PK10R1_INC29_PRIMARY_STATE_BOUNDARY.inp`
- **Committed State Source**: Offline exact reconstruction from accepted replay trajectory frames 0–29
- **Committed State Provenance**: `SCIENTIFICALLY_EQUIVALENT_REPLAY_RECONSTRUCTION` ($H_{\max,\text{expected}} = 98.221423\text{ kN/mm}^2$ originating from transition triangle Element 4788)
- **Original Baseline Comparison Job**: `1389684.mmaster02` (Step 1 Inc 29)
- **Handoff Increment**: 29 ($U_{1,\text{RP}} = 0.010143300518393517\text{ mm}$)
- **Active Reference Handoff $RF_1$**: `0.305426 kN` (Replay `1389707.mmaster02`)
- **Original Baseline Handoff $RF_1$**: `0.305468 kN` (Baseline `1389684.mmaster02`)

### Failed Run History & Environment Diagnosis
- **Failed PBS Job ID**: `1390037.mmaster02`
- **Failure Classification**: `MODULE_COMPILER_FAILURE`
- **Root Cause**: Missing `module load gcc/11.4.0` in compute-node batch environment required by Intel 2024 Fortran compiler.
- **Resolution**: Isolated launcher fix explicitly prepending `module load gcc/11.4.0`. Zero scientific bytes modified.

### Frozen Package Hashes
| Artifact | Relative Path | SHA256 |
| :--- | :--- | :--- |
| **Input Deck** | `models/generated/mode_ii/production_control_batch/M2CORR_PK10R1_SAMEMESH_RESTART_VALIDATION_R7/M2CORR_PK10R1_SAMEMESH_RESTART_VALIDATION_R7.inp` | `d20edf3a13f024b4ccb981dd86ec82fd7e91ba611451694b9cf313d0affcf750` |
| **UEL Subroutine** | `models/generated/mode_ii/production_control_batch/M2CORR_PK10R1_SAMEMESH_RESTART_VALIDATION_R7/f44_mixed_uel_restart_stateinit.for` | `de8326dfd28e66a82ba38496ee63869b86b5959e2cc35b010ebb28ae1dec6438` |
| **Full State Include** | `models/generated/mode_ii/production_control_batch/M2CORR_PK10R1_SAMEMESH_RESTART_VALIDATION_R7/PK10R1_INC29_PRIMARY_STATE_BOUNDARY.inp` | `9bd16f9a27cf7c7aa398af31f7e3c754bfab5e9ecf2825fd835dbd1340bd51e5` |
| **U3 Only Include** | `models/generated/mode_ii/production_control_batch/M2CORR_PK10R1_SAMEMESH_RESTART_VALIDATION_R7/PK10R1_INC29_U3_ONLY_BOUNDARY.inp` | `f54e4fefb92308ec302322cf4183cfa62ae5f89eeb37f1d8727034ea1ce167b8` |
| **Canonical Primary CSV** | `models/generated/mode_ii/production_control_batch/PK10R1_INC29_PRIMARY_STATE_REPLAY_R1.csv` | `5a2313e1ed15834d933e7cd12808681bd554394ad64d58419ad85f6f2bf6cf69` |
| **Reconstructed Binary** | `models/generated/mode_ii/production_control_batch/M2CORR_PK10R1_SAMEMESH_RESTART_VALIDATION_R7/PK10R1_INC29_COMMITTED_STATE_REPLAY_RECONSTRUCTED.bin` | `9ad133d73332fa24e4c35eab9d49505d30232d30ff5b9f49372d361f833cccea` |
| **Launcher (Corrected)** | `models/generated/mode_ii/production_control_batch/M2CORR_PK10R1_SAMEMESH_RESTART_VALIDATION_R7/submit_job.sh` | `ba75bbe2a4f3b6ced22f872d3264e8750eae8304b8d9852b164ac1c300944440` |
| **Package Manifest** | `models/generated/mode_ii/production_control_batch/M2CORR_PK10R1_SAMEMESH_RESTART_VALIDATION_R7/manifest.json` | `198a9a31c8e6f6d1c4ee6c32bbb8c01cd872352d81e1c40d7117853c3340bbf0` |

### F205-Audited Acceptance Criteria (Registry Sourced)
| Criterion ID | Metric | Operator | Threshold | Units | Provenance | Criterion Type | Description |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `CRIT_R7_HANDOFF_RF1_TOLERANCE` | `step1_diff_pct` | `<=` | `1.0` | `%` | F188 | `FROZEN_SCIENTIFIC` | $RF_1$ at Inc 29 within $1.0\%$ of replay reference ($0.305426\text{ kN}$) |
| `CRIT_R7_MECH_EQUILIBRATION_RF1_JUMP` | `s2_jump_pct` | `<=` | `1.0` | `%` | F188 | `FROZEN_SCIENTIFIC` | $RF_1$ jump upon mechanical boundary release $\le 1.0\%$ |
| `CRIT_R7_PHASE_IRREVERSIBILITY_TOLERANCE` | `min_delta_d` | `>=` | `-1.0e-6` | `dim.` | F188 | `FROZEN_SCIENTIFIC` | Pointwise damage increment $\Delta d \ge -1.0\times 10^{-6}$ |
| `CRIT_R7_TERMINAL_CONTINUATION_RF1_TOLERANCE` | `s4_term_diff_pct`| `<=` | `2.0` | `%` | F188 | `FROZEN_SCIENTIFIC` | Terminal $RF_1$ at $U_1 = 0.050\text{ mm}$ within $2.0\%$ of reference ($0.003639\text{ kN}$) |
| `CRIT_R7_MECH_EQUILIBRATION_U3_DRIFT` | `max_abs_u3_change`| `<=` | `1.0e-6` | `dim.` | F192 | `SOFTWARE_TOLERANCE` | Software clamp check on fixed nodal $U_3$ during Step 2 |
| `CRIT_R7_PHASE_RELEASE_RF1_JUMP` | `s3_jump_pct` | `N/A` | `None` | `%` | F205 | `QUALITATIVE` | Raw $RF_1$ jump upon Step 3 phase unfixing (no invented 2% gate) |

---

## 4. Job 2: Corrected Topology Validation (Revision R2)

- **Job Name**: `M2CORR_PK10R2_TOPOLOGY_CORRECTED`
- **Scientific Purpose**: Continuous Mode-II shear benchmark with uniform quad notch-tip mesh grading and sharp physical slit representation (eliminating transition triangle distortion).

### Failed Run History & Environment Diagnosis
- **Failed PBS Job ID**: `1390038.mmaster02`
- **Failure Classification**: `MODULE_COMPILER_FAILURE`
- **Root Cause**: Missing `module load gcc/11.4.0` in compute-node batch environment required by Intel 2024 Fortran compiler.
- **Resolution**: Isolated launcher fix explicitly prepending `module load gcc/11.4.0`. Zero scientific bytes modified.

### Audited Mesh Properties
- **Physical Nodes**: 6,249 (Auxiliary RP: 1, Total: 6,250)
- **Physical Quad Elements**: 6,048 (Layered elements: 18,144, Triangles: 0)
- **Notch Topology**: 26 split stations on $x \in [-0.5, 0.0], y=0$ ($52$ duplicate nodes), crack tip at Node 3101 ($x=0$), intact ligament continuous across 100 stations.
- **Mesh Sizing**: $h_{\text{local}} = 0.005000\text{ mm}$, $h_{\text{global}} = 0.025000\text{ mm}$, $h_{\text{global}}/h_{\text{local}} = 5.000000$, maximum adjacent neighbor ratio $= 1.224745 \le 1.5$, maximum aspect ratio $= 5.000000$.

### Accepted Ground-Truth References (0.29 kN Lineage)
- **H1 Reference** (`1389686.mmaster02`): $K_0 \approx 529.67\text{ kN/mm}$, Peak $RF_1 \approx 0.29957\text{ kN}$, Peak $U_1 \approx 0.000627\text{ mm}$.
- **H2 Reference** (`1389687.mmaster02`): $K_0 \approx 529.01\text{ kN/mm}$, Peak $RF_1 \approx 0.29483\text{ kN}$, Peak $U_1 \approx 0.000616\text{ mm}$.
- **Defective Baseline** (`1389684.mmaster02`): $K_0 \approx 639.80\text{ kN/mm}$, Peak $RF_1 \approx 0.38324\text{ kN}$, Peak $U_1 \approx 0.000680\text{ mm}$.
- **Superseded Lineage**: Historical $\sim 0.859\text{ kN}$ lineage (`1389351`, `1389352`) is strictly excluded.

### Frozen Package Hashes
| Artifact | Relative Path | SHA256 |
| :--- | :--- | :--- |
| **Input Deck** | `models/generated/mode_ii/production_control_batch/M2CORR_PK10R2_TOPOLOGY_CORRECTED/M2CORR_PK10R2_TOPOLOGY_CORRECTED.inp` | `667897fc42ee134be434cb5bc543796ce47ffd2024ec4d6c01d20e0abbd987be` |
| **UEL Subroutine** | `models/generated/mode_ii/production_control_batch/M2CORR_PK10R2_TOPOLOGY_CORRECTED/f42_mixed_uel.for` | `e0865b5eba43c14d21a733e72717e157d65c778319e6556e5eca8ab222364e58` |
| **Launcher (Corrected)** | `models/generated/mode_ii/production_control_batch/M2CORR_PK10R2_TOPOLOGY_CORRECTED/submit_job.sh` | `c0dc769e9a21488e8dd9b6e315ac7a5b9b1ba0ee684dd32a4633798940c14ed3` |
| **Package Manifest** | `models/generated/mode_ii/production_control_batch/M2CORR_PK10R2_TOPOLOGY_CORRECTED/manifest.json` | `dbf20366ab9ad5aed4f5fc67c1d646d1480376e787b819098666d7fdbfa3f426` |

### F205-Audited Scientific Evaluation Policy
- No frozen numerical scientific acceptance threshold exists for topology accuracy.
- **Qualitative Evidence**: Initial stiffness $K_0$, peak $RF_1$, peak $U_1$, $RF_1-U_1$ curve, and crack path are evaluated as qualitative/diagnostic evidence (`QUALITATIVE/NO_FROZEN_NUMERIC_THRESHOLD`).
- **Diagnostic Error Reduction**:
  $$\text{red\_frac}_{K_0} = 1.0 - \frac{|K_{0,\text{PK10R2}} - 529.01|}{|639.80 - 529.01|}$$
  $$\text{red\_frac}_{RF_1} = 1.0 - \frac{|RF_{1,\text{PK10R2}} - 0.29483|}{|0.38324 - 0.29483|}$$
- Output status is `QUALIFIED_FOR_SCIENTIFIC_REVIEW` without manufactured binary pass/fail gates.

---

## 5. Proof of Scientific Independence & Resource Concurrency

1. **Scientific Independence**: R7 and PK10R2 share zero runtime files, state binaries, or execution dependencies. R7 validates restart state recovery; PK10R2 validates mesh topology improvement.
2. **Resource Concurrency**:
   - Total cores requested: 2 (1 per job)
   - Total RAM requested: 32 GB (16 GB per job)
   - Total walltime requested: 24:00:00 per job
   - Simultaneous running limit: 2 (100% compliant with HPC policy)

---

## 6. Deterministic Future Authorized Submission Sequence

When explicit human authorization is granted, the execution workflow must execute exactly in this order:

```text
Step 1: Verify all 12 frozen package SHA256 hashes against this document.
Step 2: Verify pre-submission notification gate on cluster (PBS email & Telegram).
Step 3: Verify resources and queue directives (entry_imfdfkmq, 1 CPU, 16 GB, 24:00:00).
Step 4: Verify maximum submission allowance (max_total_submissions = 2).
Step 5: Submit Job 1: qsub M2CORR_PK10R1_SAMEMESH_RESTART_VALIDATION_R7/submit_job.sh.
Step 6: Capture and preserve exact returned R7 PBS Job ID.
Step 7: Submit Job 2: qsub M2CORR_PK10R2_TOPOLOGY_CORRECTED/submit_job.sh.
Step 8: Capture and preserve exact returned PK10R2 PBS Job ID.
Step 9: Issue zero further submissions (await terminal execution and automatic ingestion).
```

---

## 7. Result Ingestion Pipeline Qualification Status

The postprocessing and ingestion pipeline has been fully qualified offline:
- **Criterion Registry**: `scripts/postprocessing/criterion_registry.json` (`0b0351e2...`)
- **R7 Evaluator**: `scripts/postprocessing/evaluate_m2corr_pk10r1_samemesh_r7.py` (`74c8ca34...`)
- **PK10R2 Evaluator**: `scripts/postprocessing/evaluate_m2corr_pk10r2_topology.py` (`5a5c8f02...`)
- **Terminal Ingestion Tool**: `scripts/postprocessing/ingest_validation_job_results.py` (`b2f4cfc1...`)
- **Unit Test Suite**: `tests/unit/test_validation_evaluators.py` (`a8a35c80...`, 6/6 tests passing)
- **Pipeline Runner**: `scripts/postprocessing/offline_qualify_pipeline.py` (4/4 historical benchmarks passing)
