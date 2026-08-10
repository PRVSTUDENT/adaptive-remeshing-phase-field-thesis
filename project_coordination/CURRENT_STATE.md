# Project Current State

# Current Project State - Stage C Reference Baseline Verification

**Active Task**: `F43MODEREF9-H0SCIENCE-FINAL1`
**Date**: 2026-08-10
**Active Agent**: `gemini-antigravity`
**Task Status**: `complete_pass`

---

## 1. Verified HPC Reference Jobs & Results

- **Candidate Job Name**: `M2REF_H0_NPHYSFIX_REPRO`
- **Candidate Job ID**: `1386372.mmaster02`
- **Reference Job ID**: `1379393.mmaster02`
- **Preparation Tag P**: `P43MODEREF9-FINAL1` (`bc97faf70aae0ae981bcabfcbc528203f677be0a`)
- **Qualification Tag Q**: `Q43MODEREF9-FINAL1` (`9ad3c19ad1cbb7a1518f8e02d6b35d8868735ea5`)
- **Final Audit Classifications**:
  - `scheduler_result`: `PASS`
  - `technical_result`: `PASS`
  - `postprocessing_result`: `PASS`
  - `scientific_result`: `PASS`
  - `governance_result`: `HOLD_protocol_deviating_authorization_and_notification_contract`
- **Scientific Metric Summary**:
  - Peak $RF_1$: $0.371524\text{ kN}$ ($371.52\text{ N}$) vs Reference $0.373271\text{ kN}$ (**$0.468\%$ relative error**, Peak Gate `PASS`)
  - Full Curve Normalized $L_2$ Error: **$0.198\%$** ($0.001977$, Full Curve Gate `PASS`)
  - Peak Damage $d_{\max}$: **$0.990579$** vs Reference $0.990884$ (Absolute error $0.000304$, `PASS`)
  - Damage Initiation Thresholds: $100\%$ exact match at $U_1 = 0.0001, 0.0002, 0.0015, 0.0045\text{ mm}$
  - Irreversibility: Candidate worst decrease $1.38 \times 10^{-5}$ vs Reference $9.31 \times 10^{-6}$ (**`PASS_staggered_numerical_noise`**, 0 decreases $> 10^{-4}$)
  - SDV16 History Monotonicity: **0 negative transitions** on both candidate and reference
  - SDV14/SDV15 Producer Consistency: $\|SDV14 - SDV15\|_1 = 0.000000$ (exact match)
  - `scientifically_ready_for_pair2`: **`true`**
  - `authorization_ready_for_pair2`: **`false`**
- **Execution Hashes**:
  - Input: `e86ad4b439fb93d2a43d3100e19911ed0f2df3ac25dcbe584a3b549830069268`
  - UEL: `0bc4378179a35acd9954d20d3e07517f8e1c356ae07a23c40e7715cd7b56dce8`
  - PBS: `a1af3bc73828e0184fdb272ff2d50985bc00593bb0d905835e81e609e6a5e49b`
  - Wrapper: `f54d9261b7087c16f25533a324d3f4e58e61c4a81700b4bc1fafd947a692e331`
  - Manifest: `44fadd1c882a15a60facffa20202cdb35bca7b316434a6a582d3810b7ad70fdb`

---

## 2. Current Authority Boundary

- `execution_authorized = false` (Submitted job `1386372.mmaster02` in progress; authority consumed)
- `submission_approved = false`
- `maximum_jobs_now = 0`
- `qsub_called = true` (1 submission consumed)
- `HPC_submissions = 1`
- `H1_status = blocked_pending_corrected_H0_scientific_PASS`
- `H2_status = blocked_pending_corrected_H0_scientific_PASS`
