# Session Report: F116SUB-M2-UNIFORM-FULL-REFERENCES-H1-H2-REPLACEMENT-SUBMISSION1

- **Session Timestamp**: 2026-08-14 14:50 CEST
- **Agent**: Gemini Antigravity
- **Task ID**: `F116SUB-M2-UNIFORM-FULL-REFERENCES-H1-H2-REPLACEMENT-SUBMISSION1`
- **Scope**: Execute single permitted automatic technical replacement submission for each member of the two-job batch `M2REF_H1_FULL_U050` and `M2REF_H2_FULL_U050` via guarded wrappers.
- **Protocol Version**: 1
- **Status**: `COMPLETED_PASS`

---

## 1. Batch Replacement Execution Summary

1. **`M2REF_H1_FULL_U050`**:
   - Location: `models/generated/mode_ii/production_verification_batch/M2REF_H1_FULL_U050/`
   - Manifest SHA256: `4d74dfc772c5f5af03a65b6770a86e5127951071205036de62b2c25386374950`
   - Replaced Job ID: `1389336.mmaster02`
   - Replacement Job ID: `1389351.mmaster02`
   - Status: `RUNNING` on compute host (`normal_imfdfkmq`, 1 CPU, 8 GB, 12:00:00)
   - Replacement Allowance: `CONSUMED`

2. **`M2REF_H2_FULL_U050`**:
   - Location: `models/generated/mode_ii/production_verification_batch/M2REF_H2_FULL_U050/`
   - Manifest SHA256: `20210378a354616afd5f1887ed03931deab69f7749b9131b7bf9e5753d87c0d6`
   - Replaced Job ID: `1389337.mmaster02`
   - Replacement Job ID: `1389352.mmaster02`
   - Status: `RUNNING` on compute host (`normal_imfdfkmq`, 1 CPU, 16 GB, 24:00:00)
   - Replacement Allowance: `CONSUMED`

---

## 2. Governance and Policy Compliance

- Pre-submission manifest verification: `PASS` on both packages.
- Guarded wrappers executed:
  `./submit_m2ref_h1_full_u050.sh --execute`
  `./submit_m2ref_h2_full_u050.sh --execute`
- Batch replacement `qsub` count: 2.
- Maximum simultaneous jobs: 2 (both currently running).
- `automatic_retry_after_replacement = false`.
- `qdel_called = false`, `qmove_called = false`.
- Coordination ledgers updated: `HPC_JOB_LEDGER.csv` (lines 166-169), `TASK_LEDGER.csv` (line 387), `CURRENT_STATE.md`.
