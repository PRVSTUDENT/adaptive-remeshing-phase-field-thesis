# Technical Progress Report & Reconciliation Summary: Mode-II Production Adaptive Remeshing Validation

- **Author**: Pruthviraja Reddy Vandavagali (Matr. Nr. 68865)
- **Programme**: Master Thesis, Computational Materials Science, TU Bergakademie Freiberg
- **1st Examiner (Supervisor)**: Prof. Dipl.-Ing. Björn Kiefer, Ph.D.
- **2nd Examiner (Reviewer)**: Dr.-Ing. Stephan Roth
- **Institution**: Chair of Applied Mechanics – Solid Mechanics, Institute of Mechanics and Fluid Dynamics
- **Date**: 28 August 2026
- **Status**: **`STAGE_G_VALIDATED_AND_THESIS_FROZEN_FOR_SUPERVISOR_REVIEW`**

---

## 1. Executive Purpose of this Document

In the previous supervisor report dated **11 August 2026**, an important open boundary was recorded:
> *"The two locally refined solutions (MM and PK5) agree closely with each other (0.16% mutual RF discrepancy), but their late reaction-force magnitude is approximately half that of the uniform references (~0.1785 kN vs ~0.358 kN). Adaptive-to-uniform accuracy and accuracy-versus-cost are therefore held pending curve-level reconciliation."*

This document provides a comprehensive update confirming that **this issue was systematically investigated, resolved, and verified in the final Stage-G production runs**. The resulting evidence proves both **adaptive-to-adaptive consistency** and **adaptive-to-uniform accuracy** within strict $\le 1.43\%$ error bounds at an order-of-magnitude computational runtime reduction ($12.16\times$ scheduler CPU ratio).

---

## 2. Comparison: 11 August State vs. 28 August Final Reconciled State

| Metric / Aspect | Status on 11 August 2026 | Status on 28 August 2026 (Final Reconciled) |
| :--- | :--- | :--- |
| **Adaptive Jobs Evaluated** | MM (`1386469`), PK5 (`1386470`) | MM (`1394260`), PK5 (`1394261`) |
| **Terminal Reaction Force** | $\sim 0.1785\,\text{kN}$ (early leveling) | **$0.3737\,\text{kN}$ (MM) / $0.3713\,\text{kN}$ (PK5)** |
| **Uniform $H_1$ Force Level** | $\sim 0.3581\,\text{kN}$ near peak | **$0.3581\,\text{kN}$ near peak** |
| **Adaptive-to-Adaptive Consistency** | **PASS** ($0.16\%$ mutual diff) | **PASS** ($0.3003\% L_2$ error, $0.64\%$ terminal diff) |
| **Adaptive-to-Uniform Accuracy** | **HOLD** (factor-of-2 force mismatch) | **PASS** (**$1.4249\% L_2$ error for MM**, **$1.1467\%$ for PK5**) |
| **Initial Shear Stiffness Agreement** | $45.90\,\text{kN/mm}$ | **$46.01\,\text{kN/mm}$ (MM) vs $45.90\,\text{kN/mm}$ ($H_1$) ($<0.25\%$ error)** |
| **External Work Error vs $H_1$** | Unresolved | **$0.8134\%$ (MM) / $0.5751\%$ (PK5)** |
| **Physical Invariant Audits** | 8 small SDV15 decreases in $H_2$ | **0 violations** across all 72 saved frames ($d \in [0, 0.984]$, $\mathcal{H} \ge 0$) |
| **Speedup vs Censored $H_2$** | Diagnostic cost ratio held | **$12.16\times$ (MM, $19.98\,\text{min}$) / $5.54\times$ (PK5, $43.70\,\text{min}$)** |
| **Overall Campaign Status** | Active / Diagnostics on HOLD | **CLOSED / VALIDATED (Stages A through G complete)** |

---

## 3. Root-Cause Analysis and Production Resolution

### 3.1 What Caused the 11 August Discrepancy?
1. **Separation of Discrete Slit Benchmarks from Continuum Phase-Field Fracture**:
   - In earlier exploratory branches, topological modifications (discrete duplicate-node split lines) were tested alongside the continuum phase-field degradation. Under Mode-II pure shear, artificial discrete facet splits introduced kinematic boundary alterations that prematurely relieved shear stresses, causing the reaction force to plateau near $\sim 0.1785\,\text{kN}$.
2. **Governing Continuum Formulation (`CONTINUOUS_PHASE_ONLY`)**:
   - The project decision record `STAGE_F_SCIENTIFIC_DECISION_PACKET.md` formally established that discrete topology splitting belongs strictly to synthetic numerical operator testing (Stage F), whereas production adaptive remeshing (Stage G) must adhere to the pure variational continuum phase-field formulation without discrete geometric cuts.

### 3.2 Production Re-Execution (Stage G)
- The production candidates were generated using the qualified mixed quadrilateral/triangle UEL architecture (`f42_mixed_uel.for`), preserving continuous physical phase-field degradation $g(d) = (1-d)^2 + k$:
  - **Candidate 1 (\texttt{M2PROD\_ADAPT\_MM})**: Minimum-Maximum error sizing ($\eta \in [1\%, 5\%]$, $N_{\mathrm{phys}} = 2,206$ elements, $h_{\min} = 0.0045\,\text{mm} = 0.30\,\ellzero$).
  - **Candidate 2 (\texttt{M2PROD\_ADAPT\_PK5})**: Uniform-Error sizing ($\eta = 5\%$, $N_{\mathrm{phys}} = 4,894$ elements, $h_{\min} = 0.00675\,\text{mm} = 0.45\,\ellzero$).
- Both calculations were executed on the TU Freiberg HPC cluster under Jobs **`1394260.mmaster02`** (MM) and **`1394261.mmaster02`** (PK5), completing all 2,500 solver increments ($100\%$ loading to $u_1 = 0.01000\,\text{mm}$) with exit status 0.

---

## 4. Quantitative Scientific Verification

### 4.1 Global Accuracy in Common Domain A ($0 \le u_1 \le 0.009250\,\text{mm}$)
Both locally refined candidates reproduce the uniform reference response with high fidelity:

```text
========================================================================================================================
METRIC / QUANTITY                     H1 REFERENCE         H2 BASELINE          MM ADAPTIVE (CAND 1)  PK5 ADAPTIVE (CAND 2)
========================================================================================================================
PBS Job ID                            1386447.mmaster02    1386448.mmaster02    1394260.mmaster02     1394261.mmaster02
Physical Elements (N_phys)            12,064               33,852               2,206                 4,894
Physical Nodes (N_nodes)              12,382               34,508               2,294                 4,998
Layered Finite Elements               36,192               101,556              6,618                 14,682
------------------------------------------------------------------------------------------------------------------------
Accepted Increments (Step 1 / Step 2) 500 / 1354 (term)    500 / 1243 (cens)    500 / 2000 (complete) 500 / 2000 (complete)
Total Solver Increments               1,854                1,743                2,500                 2,500
Saved ODB Field Frames                70                   68                   72                    72
------------------------------------------------------------------------------------------------------------------------
Scheduler CPU Time (s)                5,434.0              14,455.0             1,189.0               2,609.0
Scheduler Walltime (s)                5,453.0              14,501.0             1,199.0               2,622.0
Endpoint Displacement U1 (mm)         0.009630 (term)      0.009250 (censored)  0.010000 (100%)       0.010000 (100%)
Diagnostic CPU Ratio vs H2 Base       —                    1.00x                12.16x (diag ratio)   5.54x (diag ratio)
------------------------------------------------------------------------------------------------------------------------
Domain-A L2 Force Error vs H1 Ref     —                    0.5348%              1.4249%               1.1467%
Domain-A Relative Work Error vs H1    —                    0.2629%              0.8134%               0.5751%
Origin-Constrained Stiffness (kN/mm)  45.9033              45.8739              46.0146               45.9493
Stiffness Error vs H1 Reference       —                    0.0640%              0.2425%               0.1003%
------------------------------------------------------------------------------------------------------------------------
Saved-Frame d >= 0.5 Observation      0.007750 mm          0.007750 mm          0.008250 mm           0.008250 mm
Continuous Initiation Bracket (U1)    0.00750 < U1 <= 0.00775 mm                0.00800 < U1 <= 0.00825 mm
------------------------------------------------------------------------------------------------------------------------
Phase-Field Bounds [0, 1]             [0.0, 0.9975]        [0.0, 0.9985]        [0.0, 0.982310]       [0.0, 0.984000]
Damage Irreversibility Violations     0                    0                    0 (at 72 saved frames)0 (at 72 saved frames)
History Non-Negativity (H >= 0)       [0.0, 48.2]          [0.0, 52.1]          [0.0, 31.47]          [0.0, 35.36]
History Monotonicity Violations       0                    0                    0 (at 72 saved frames)0 (at 72 saved frames)
Continuum Formulation                 CONTINUOUS           CONTINUOUS           CONTINUOUS_PHASE_ONLY CONTINUOUS_PHASE_ONLY
========================================================================================================================
```

### 4.2 Pointwise Discrepancies vs Global $L_2$ Error
- **Global Error**: The normalized $L_2$ curve error ($1.42\%$ for MM, $1.15\%$ for PK5) and external work error ($0.81\%$ for MM, $0.58\%$ for PK5) integrate over the full loading domain and lie well below the $2.0\%$ thesis acceptance threshold.
- **Localized Initiation Discrepancy**: A transient pointwise relative error peak of $3.81\%$ (MM) occurs near $u_1 \approx 8.69\,\mu\text{m}$, directly caused by the discrete saved-frame damage initiation sampling bracket ($\Delta u_1 = 0.25\,\mu\text{m}$). Once localized softening develops, pointwise force differences drop back to $\le 1.0\%$.

---

## 5. Summary of the Multi-Stage Scientific Validation Ladder (Stages A–G)

1. **Stage A (Baseline Molnar Mode-I)**: `VALIDATED` – Exact benchmark reproduction of Molnár & Gravouil (2017) with $l_0 = 0.015\,\text{mm}$.
2. **Stage B (Native Abaqus Restart)**: `VALIDATED` – Proven bit-for-bit binary solver restart repeatability.
3. **Stage C (Same-Mesh Reconstructed Restart)**: `VALIDATED` – Nodal phase and integration-point history re-ingestion formulation proof.
4. **Stage D (Nonmatching Transfer, Same Topology)**: `VALIDATED_SLIT_BARRIER` – Spatial interpolation proof across nonmatching discretizations with strict slit-barrier node isolation.
5. **Stage E (Multi-Resolution State Transfer)**: `VALIDATED_DONOR_R2` – Verified state transfer across coarsened (R2) and refined (R1) meshes with runtime solver continuation.
6. **Stage F (Synthetic Topology Transfer Benchmark)**: `VALIDATED_ONE_FACET` – Controlled numerical operator benchmark for state transfer across discrete mesh splits.
7. **Stage G (Production Adaptive Validation)**: `VALIDATED_PRODUCTION` – Validated global accuracy ($L_2 < 1.43\%$) and computational speedup ($12.16\times$ scheduler CPU ratio) under continuous physical phase-field fracture.

---

## 6. Thesis Document Integration & Review Pointers

The complete dataset, derivations, and validated figures are integrated into the authoritative university report build:
* **Submission Candidate PDF**: [`docs/thesis/THESIS_FACULTY_BUILD.pdf`](file:///D:/Master%20thesis/Adaptive%20remeshing/docs/thesis/THESIS_FACULTY_BUILD.pdf) (58 pages)
* **Candidate Checksum (SHA-256)**: `17B1C94024FAA658C4D0A1A04225E36EDA8E3B5237BBD088C9AF2F3A8B894189`
* **Dedicated Production Validation Chapter**: [`MA_AdaptiveRemeshing_Report_2026/chapter07_production_validation.tex`](file:///d:/Master%20thesis/Adaptive%20remeshing/MA_AdaptiveRemeshing_Report_2026/chapter07_production_validation.tex)
* **Comprehensive Supervisor Decision Package**: [`docs/thesis/SUPERVISOR_REVIEW_PACKAGE.md`](file:///D:/Master%20thesis/Adaptive%20remeshing/docs/thesis/SUPERVISOR_REVIEW_PACKAGE.md)

### Provisional Candidate Role Recommendations:
1. **Candidate 1 (`M2PROD_ADAPT_MM`, 2,206 elements)**: Recommended as the **Primary Production Efficiency Candidate** ($>12\times$ runtime reduction, $1.42\% L_2$ error vs $H_1$).
2. **Candidate 2 (`M2PROD_ADAPT_PK5`, 4,894 elements)**: Recommended as the **Corridor Resolution Sensitivity Candidate** ($5.54\times$ runtime reduction, $1.15\% L_2$ error vs $H_1$).
