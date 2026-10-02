# Mode-II Automated Evaluation & Result Ingestion Pipeline Preparation Record (R7 / PK10R2)

**Task ID**: `F204PREP-M2-R7-PK10R2-AUTOMATED-EVALUATION-AND-RESULT-INGESTION1`  
**Date**: 16 August 2026  
**Status**: `PIPELINE QUALIFIED / R7 SUPPORT INTEGRATED / HARMONIZED EVALUATION ESTABLISHED`  
**Active Agent**: `gemini-antigravity`  

---

## 1. Executive Summary

This record establishes the final automated postprocessing, scientific evaluation, and result-ingestion pipeline for `M2CORR_PK10R1_SAMEMESH_RESTART_VALIDATION_R7` and `M2CORR_PK10R2_TOPOLOGY_CORRECTED`. The evaluator completely replaces legacy R6 placeholder handling with exact R7 reconstructed state verification ($H_{\max} = 98.221423\text{ kN/mm}^2$) and integrates error reduction diagnostics for PK10R2 relative to accepted H2 (`1389687.mmaster02`).

---

## 2. Pipeline Architecture & Tool Inventory

| Tool / Script | Location | Purpose & Scientific Scope |
| :--- | :--- | :--- |
| **R7 Restart Evaluator** | `scripts/postprocessing/evaluate_m2corr_pk10r1_samemesh_r7.py` | Evaluates 4-stage restart protocol, handoff $RF_1$ ($\le 1\%$), mechanical release jump ($\le 1\%$), phase preservation ($\le 10^{-6}$), phase release jump ($\le 2\%$), non-negative damage healing ($\Delta d \ge 0$), and continuation trajectory alignment with replay `1389707.mmaster02`. |
| **PK10R2 Topology Evaluator** | `scripts/postprocessing/evaluate_m2corr_pk10r2_topology.py` | Evaluates elastic stiffness $K_0$, peak $RF_1$, peak $U_1$, relative L2 trajectory errors vs accepted H1 (`1389686.mmaster02`) / H2 (`1389687.mmaster02`), and calculates exact error reduction fractions $\text{red\_frac} = 1 - \text{err}_{\text{PK10R2}} / \text{err}_{\text{PK10R1}}$. |
| **Unified Dispatcher** | `scripts/postprocessing/dual_validation_pipeline.py` | Automatically routes job directories to R7 or PK10R2 evaluators based on directory name or flag. |
| **Terminal Result Ingestion** | `scripts/postprocessing/ingest_validation_job_results.py` | Automated retrieval of `.dat`, `.msg`, `.sta`, `.odb`, `.out`, `.err`, `STATUS.json`, and `ENVIRONMENT.json` from cluster to local evidence folder and immediate pipeline execution. |

---

## 3. Evaluator Configurations & Acceptance Rules

### A. R7 Evaluation Rules
- **Committed State Provenance**: `SCIENTIFICALLY_EQUIVALENT_REPLAY_RECONSTRUCTION`
- **Reconstructed History $H_{\max}$**: `98.221423 kN/mm²`
- **Stage 1 (STATE_INSTALL)**: $RF_1$ matches $0.305468\text{ kN}$ within $\le 1.0\%$.
- **Stage 2 (MECH_EQUILIBRATION)**: $RF_1$ jump $\le 1.0\%$, max $|\Delta U_3| \le 1.0\times 10^{-6}$.
- **Stage 3 (PHASE_RELEASE)**: $RF_1$ jump $\le 2.0\%$, $\Delta d \ge 0.0$ pointwise.
- **Stage 4 (CONTINUATION)**: Curve trajectory follows replay `1389707.mmaster02`.

### B. PK10R2 Evaluation Rules
- **Mesh Properties**: 6,249 physical nodes, 6,048 physical quads, 18,144 layered elements, $h_{\text{local}} = 0.005\text{ mm}$, $h_{\text{global}} = 0.025\text{ mm}$, 26 split stations.
- **Ground Truth**: H1 (`1389686.mmaster02`, $K_0 \approx 529.67$, $RF_1 \approx 0.29957\text{ kN}$) and H2 (`1389687.mmaster02`, $K_0 \approx 529.01$, $RF_1 \approx 0.29483\text{ kN}$).
- **Diagnostic Metrics**:
  $$\text{red\_frac}_{K_0} = 1.0 - \frac{|K_{0,\text{PK10R2}} - 529.01|}{|639.80 - 529.01|}$$
  $$\text{red\_frac}_{RF_1} = 1.0 - \frac{|RF_{1,\text{PK10R2}} - 0.29483|}{|0.38324 - 0.29483|}$$
- **Classification Output**: `TOPOLOGY_DEFECT_CLEARLY_REDUCED` if both reduction fractions $> 0.50$, `TOPOLOGY_DEFECT_NOT_REDUCED` if $\le 0.0$, `TOPOLOGY_RESULT_AMBIGUOUS` otherwise.
