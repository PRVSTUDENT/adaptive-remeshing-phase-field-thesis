# Scientific Evaluation Report: F129EVAL Corrected Virgin Baselines

- **Task ID**: `F129EVAL-M2-CORRECTED-VIRGIN-BASELINES-EVALUATION1`
- **Date**: 2026-08-15
- **Agent**: `gemini-antigravity`
- **Evaluated Baseline Jobs**:
  - `M2CORR_PK10R1_CONTINUOUS_U050` (`1389684.mmaster02`) -> **`COMPLETED_PASS_SCIENTIFIC_PASS`**
  - `M2CORR_H2_FULL_U050` (`1389683.mmaster02`) -> **`FINISHED_FAILED_INITIALIZATION`** (Pre-solver exit code 1 due to missing dummy `UMAT` stub)

---

## 1. Executive Summary & Core Scientific Findings

The evaluation of the first corrected continuous baseline job (`M2CORR_PK10R1_CONTINUOUS_U050`, `1389684.mmaster02`), executed with un-degraded strain energy driving formulation $POS_M = \psi_+(\boldsymbol{\varepsilon})$ and transactional `UEXTERNALDB` state management, reveals a **profound, fundamental shift in the scientific baseline**:

1. **Peak Reaction Force & Early Crack Initiation**:
   - Under the corrected formulation ($POS_M = \psi_+$), crack initiation occurs at $U_1 = \mathbf{0.000680\text{ mm}}$ with a peak reaction force of **$RF_{1,\max} = \mathbf{0.383237\text{ kN}}$** ($383.24\text{ N}$).
   - In stark contrast, historical runs (e.g. `1389677.mmaster02`) using the buggy degraded driving energy formulation ($POS_M = g(d)\psi_+$) artificially suppressed driving energy as damage grew ($g(d) \to 0$), preventing crack propagation and producing an artificial late peak of **$0.798816\text{ kN}$** at $U_1 = 0.0461\text{ mm}$!

2. **Softening Trajectory**:
   - Following peak load at $U_1 = 0.000680\text{ mm}$, the reaction force monotonically softens down to **$0.016108\text{ kN}$** ($16.11\text{ N}$) at $U_1 = 0.002500\text{ mm}$.

3. **Status of `M2CORR_H2_FULL_U050` (`1389683.mmaster02`)**:
   - Failed at 07:12:10 AM CEST during pre-solver input processing with `***ERROR: USER SUBROUTINE UMAT IS MISSING` because the 3rd passive visualizer element layer (`TYPE=CPE4`, `*USER MATERIAL`) in the H2 INP deck required a dummy `SUBROUTINE UMAT` stub, which was omitted from the candidate file.
   - The UEL file has been repaired locally by attaching the passive visualizer `SUBROUTINE UMAT` stub (`f42_mixed_uel_transactional.for` SHA256 `ed1586d6427a4b1a01d99f7e219891ec7be9fe911e066d9360724942e7d27720`).
   - The single permitted technical replacement submission (`M2CORR_H2_FULL_U050`) is prepared for human authorization.

---

## 2. Quantitative Metric Comparison

| Metric | Historical PK10R1 (`1389677`) | Corrected PK10R1 (`1389684`) |
| :--- | :--- | :--- |
| **Driving Energy Formulation** | $POS_M = g(d)\psi_+$ (**BUG**) | $POS_M = \psi_+$ (**CORRECTED**) |
| **State Storage Architecture** | Module Array (Unmanaged) | Transactional `UEXTERNALDB` |
| **Total Increments** | 109 | 148 |
| **Peak Force $RF_{1,\max}$ (kN)** | **0.798816** | **0.383237** |
| **Displacement at Peak $U_{1,\text{peak}}$ (mm)** | **0.046143** | **0.000680** |
| **Terminal Force at $U_1=0.050\text{ mm}$ (kN)** | 0.789073 | **0.016108** |
| **Un-degraded History Consistency** | **`FAIL`** ($79.5\%$ IPs fail $H \ge \psi_+$) | **`PASS`** ($100\%$ IPs consistent) |
| **Solver Status** | `COMPLETED` | `COMPLETED` |
