# Stage Gate-6B: Spatial Fine 58k Discretization Full-Horizon Solver Evaluation (Job 1410504)

**Document ID:** `DOC-EXP-STAGE-GATE6B-JOB-1410504-FULL-HORIZON-EVALUATION`  
**Date:** 06 October 2026  
**Author:** Gemini Antigravity (Protocol v2)  
**Governing Phase:** `MODE1_GATE6B_ACTIVE_EVALUATION_AND_CONTINUATION`  
**Target Discretization:** Spatial Fine Candidate ($57{,}929$ base finite elements, $57{,}491$ FE nodes, $57{,}492$ total nodes including RP 999999)  
**Model Deck:** `models/pandey_kumar_mode1/37_stage14_adaptive_candidate_spatial_fine_8thread/PK_MODE1_STAGE14_ADAPT_SPATIAL_FINE_8T_FRACTURE.inp`  
**User Subroutine:** `f42_mixed_uel.for` (SHA-256: `CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6`)  
**PBS Job ID:** `1410504.mmaster02`  
**Execution Host:** `mnode097` (`normal_imfdfkmq`, 8-thread shared-memory SMP)  
**Scratch Execution Path:** `/scratch9/pr21vyci/projects/adaptive-remeshing/models/pandey_kumar_mode1/37_stage14_adaptive_candidate_spatial_fine_8thread/`  

---

## 1. Executive Summary & Provenance Separation

This document is the dedicated, authoritative experiment record for the **$57{,}929$-element spatial fine full-horizon candidate** solved via 8-thread shared-memory SMP under Job `1410504.mmaster02`.

### Strict Provenance Separation Contract
- **Job `1410179.mmaster02` (Serial Diagnostic)**: Preserved exclusively in [`STAGE_GATE6B_SPATIAL_FINE_58K_JOB_1410179_TERMINAL_EVALUATION.md`](STAGE_GATE6B_SPATIAL_FINE_58K_JOB_1410179_TERMINAL_EVALUATION.md) as `PARTIAL_57929_FE_POSTPEAK_DIAGNOSTIC_EVIDENCE` over $u_y \in [0.0, 0.007429]\,\text{mm}$ ($[0.0, 7.429]\,\mu\text{m}$, 24h walltime SIGTERM).
- **Job `1410504.mmaster02` (8T SMP Full-Horizon Solve)**: Governed exclusively by this record ([`STAGE_GATE6B_SPATIAL_FINE_58K_JOB_1410504_FULL_HORIZON_EVALUATION.md`](STAGE_GATE6B_SPATIAL_FINE_58K_JOB_1410504_FULL_HORIZON_EVALUATION.md)) to capture and evaluate the full uncensored horizon $u_y \in [0.0, 0.0100]\,\text{mm}$ ($[0.0, 10.0]\,\mu\text{m}$) with a 48h scheduler walltime limit.
- **Overwriting Guard**: Results from Job `1410504.mmaster02` can never overwrite, append to, or be mislabeled as Job `1410179.mmaster02`.

---

## 2. Scheduler & Resource Configuration

| Accounting Quantity | Requested / Configured | Actual Used / Recorded | Status / Governance |
| :--- | :--- | :--- | :--- |
| **PBS Job ID** | `1410504.mmaster02` | `1410504.mmaster02` | Matched |
| **Execution Node** | `mnode097` | `mnode097` | Compute node (Scratch9) |
| **PBS Queue** | `normal_imfdfkmq` | `normal_imfdfkmq` | Non-interactive batch |
| **Allocated Cores / Hardware** | `nodes=1:ppn=8` (8 cores) | 8 cores | Shared-memory SMP (1 MPI rank x 8 threads) |
| **Allocated Memory** | `16gb` (16 GB) | TBD upon terminal ingestion | Scratch9-compliant |
| **Walltime Limit** | `48:00:00` ($172{,}800\,\text{s}$) | Solving (checkpoint 10:05:00) | Full horizon permitted |
| **Abaqus Version** | Abaqus 2023 (`abaqus job=... cpus=8`) | Abaqus 2023 | Qualified SMP parallelization |
| **Dual Notifications** | Email + Telegram | `#PBS -m abe`, `job_notifications.sh` | Verified |

---

## 3. Interim Checkpoint Solver Telemetry (F1276 Snapshot)

From the captured `.sta` snapshot at elapsed walltime `10:05:00`:
- **Current Step / Increment:** Step 2, Increment 3,302 ($5{,}302$ total completed increments).
- **Captured Step Time ($t_2$):** $0.6580$ (with constant increment $\Delta t_2 = 2.0 \times 10^{-4}$).
- **Evaluated Prescribed Displacement:** $u_y(t_2) = 0.0050\,\text{mm} + 0.6580 \times 0.0050\,\text{mm} = 0.008290\,\text{mm} = 8.290\,\mu\text{m}$.
- **Numerical Robustness:** Exactly $3$ Newton iterations per increment; **$0$ cutbacks**.
- **Regime Reached:** Complete traversal through peak load ($u_{\text{peak}} = 5.717\,\mu\text{m}$) and progression deep into post-peak softening beyond the serial 24h limit ($7.429\,\mu\text{m}$).
- **Nominal Schedule Projection:** $\sim 1{,}698$ increments remaining to $u = 10.0\,\mu\text{m}$ ($\sim 75.7\%$ complete, nominal estimated remaining walltime $3.0\text{--}3.5\,\text{h}$ under zero-cutback assumption).

---

## 4. Terminal Ingestion Protocol & Target Metrics Placeholder

Upon terminal completion of Job `1410504.mmaster02`, the lightweight solver artifacts will be ingested from `/scratch9/pr21vyci/projects/adaptive-remeshing/models/pandey_kumar_mode1/37_stage14_adaptive_candidate_spatial_fine_8thread/`:
1. `PK_MODE1_STAGE14_ADAPT_SPATIAL_FINE_8T.sta`
2. `PK_MODE1_STAGE14_ADAPT_SPATIAL_FINE_8T.dat`
3. `PK_MODE1_STAGE14_ADAPT_SPATIAL_FINE_8T.out` / `.err`
4. `uel_energy_balance.csv`

### Pre-Declared Structural & Energetic Metrics Table (To Be Populated upon Terminal Ingestion)

| Metric Quantity | Governed Extraction Rule | Pre-Analysis Reference ($15{,}192$ FE) | Serial Partial Diagnostic ($1410179$) | Job 1410504 8T Full-Horizon Value | Acceptance Criterion |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **Initial Stiffness $K_0$** | OLS regression ($u \le 0.0010\,\text{mm}$) | $137.9455\,\text{kN/mm}$ | $137.8410\,\text{kN/mm}$ | *Pending Ingestion* | $|\Delta K_0| \le 0.10\%$ vs Ref |
| **Peak Force $F_{\max}$** | Maximum reaction force | $0.7578\,\text{kN}$ | $0.7416\,\text{kN}$ | *Pending Ingestion* | Track ET1 ($0.7437\,\text{kN}$) within $0.5\%$ |
| **Displacement at Peak $u_{\text{peak}}$** | Displacement at $F_{\max}$ | $0.005857\,\text{mm}$ | $0.005717\,\text{mm}$ | *Pending Ingestion* | $u_{\text{peak}} \in [0.0057, 0.0059]\,\text{mm}$ |
| **Terminal Displacement $u_{\text{term}}$** | Last completed state | $0.010000\,\text{mm}$ | $0.007429\,\text{mm}$ (censored) | *Pending Ingestion* | $u_{\text{term}} = 0.010000\,\text{mm}$ (Uncensored) |
| **External Work $W_{\text{ext}}$** | $\int F\,\mathrm{d}u$ over $[0, 0.0100]$ | $2.359329\,\text{mJ}$ | $2.501136\,\text{mJ}$ (at $7.43\,\mu\text{m}$) | *Pending Ingestion* | Monotonic energy trace |
| **Fracture Energy $E_{\text{frac}}$** | UEL SDV17 integral | $2.340220\,\text{mJ}$ | $2.359641\,\text{mJ}$ (at $7.43\,\mu\text{m}$) | *Pending Ingestion* | Energy conversion complete |
| **Stored Elastic Energy $E_{\text{elas}}$** | UEL SDV18 integral | $0.001161\,\text{mJ}$ | $0.040984\,\text{mJ}$ (at $7.43\,\mu\text{m}$) | *Pending Ingestion* | Asymptotic residual $< 0.05\,\text{mJ}$ |
| **Bookkeeping Discrepancy $\Delta_{\text{book}}$** | $W_{\text{ext}} - (E_{\text{elas}} + E_{\text{frac}})$ | $+0.017948\,\text{mJ}$ | $+0.100511\,\text{mJ}$ | *Pending Ingestion* | Bounded energy residual |
| **Normalized Error $\varepsilon_{\text{book}}$** | $|\Delta_{\text{book}}| / W_{\text{ext}} \times 100\%$ | $0.7607\%$ | $4.0186\%$ | *Pending Ingestion* | $\le 5.0\%$ full horizon |

---

## 5. Multi-Quantity Spatial Convergence Role in Gate 6B

Job `1410504.mmaster02` forms the crowning high-density anchor in the 6-level spatial convergence sequence:
1. Adaptive ET5 ($4{,}692$ FE, Job 1410359): $u_{\text{peak}} = 5.926\,\mu\text{m}$, $W_{\text{ext}} = 3.578\,\text{mJ}$, $\varepsilon_{\text{book}} = 12.10\%$.
2. Adaptive ET3 ($5{,}189$ FE, Job 1410358): $u_{\text{peak}} = 5.876\,\mu\text{m}$, $W_{\text{ext}} = 3.158\,\text{mJ}$, $\varepsilon_{\text{book}} = 11.04\%$.
3. Adaptive ET2 ($6{,}112$ FE, Job 1410357): $u_{\text{peak}} = 5.841\,\mu\text{m}$, $W_{\text{ext}} = 2.828\,\text{mJ}$, $\varepsilon_{\text{book}} = 8.65\%$.
4. Canonical Adaptive ET1 Baseline ($14{,}483$ FE, Job 1409982): $u_{\text{peak}} = 5.733\,\mu\text{m}$, $W_{\text{ext}} = 2.267\,\text{mJ}$, $\varepsilon_{\text{book}} = 1.10\%$.
5. Fixed Structured Reference ($15{,}192$ FE, Job 1409734): $u_{\text{peak}} = 5.857\,\mu\text{m}$, $W_{\text{ext}} = 2.359\,\text{mJ}$, $\varepsilon_{\text{book}} = 0.76\%$.
6. **Spatial Fine Candidate ($57{,}929$ FE, Job 1410504)**: Authoritative full-horizon verification establishing the fine-mesh spatial asymptotic limit.
