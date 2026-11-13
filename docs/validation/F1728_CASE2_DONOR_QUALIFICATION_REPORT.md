# Task F1728 Case 2 (Single Off-Axis Hole Plate) Donor Qualification Report

**Task ID:** `F1728-UNIFIED-METHOD-A-FIVE-GEOMETRIES`  
**Subtask ID:** `F1728-CASE2-OFF-AXIS-HOLE-DONOR-QUALIFICATION`  
**Classification:** `CASE2_DONOR_QUALIFICATION_OFFLINE_AUDIT_PASS`  
**Date:** 13 November 2026  
**Protocol Version:** 1  
**Agent:** `gemini-antigravity`  
**Review Correlation:** `HND-F1728-CASE2-DONOR-QUAL-001`  

---

## 1. Executive Summary and Scope Boundary

In strict compliance with the independent review approval for Task F1728 Stage C Closeout ([`HND-F1728-CASE1-PILOT-CLOSEOUT-002`](file:///D:/Master%20thesis/Adaptive%20remeshing/.agents/bridge_history/response_HND-F1728-CASE1-PILOT-CLOSEOUT-002.md)), this report establishes the **bounded, read-only scientific qualification of donor fields for Case 2: Single Off-Axis Hole Plate**.

### Strict Scope Boundary
- **Zero Forward Fracture Rule:** Under NO circumstances is forward phase-field fracture simulation performed on adapted meshes in Task F1728.
- **Zero PBS Submissions Consumed:** `max_new_pbs_submissions = 0`, `submissions_consumed = 0` for this subtask. Cumulative historical submissions remain permanently reconciled at 5 (`1423095`, `1423101`, `1423102`, `1423103`, `1423169`).
- **Read-Only Inspection:** Data extraction and audits were conducted offline on verified lightweight JSON summaries downloaded via non-interactive guarded SSH from high-speed cluster scratch (`/scratch9/pr21vyci/runs/`). Zero Abaqus solver or CAE commands were executed locally.

---

## 2. Geometry and Benchmark Specification

Case 2 represents the classical thesis benchmark: a square plate with an initial horizontal edge crack and an off-axis circular hole.

| Parameter | Notation | Numerical Value | Physical Unit |
| :--- | :--- | :--- | :--- |
| Domain Width $\times$ Height | $W \times H$ | $1.0 \times 1.0$ | $\text{mm}$ |
| Initial Crack Length | $a_0$ | $0.50$ | $\text{mm}$ |
| Notch Root Coordinates | $(x_{\text{notch}}, y_{\text{notch}})$ | $(0.50, 0.50)$ | $\text{mm}$ |
| Hole Center Coordinates | $(x_{\text{hole}}, y_{\text{hole}})$ | $(0.65, 0.65)$ | $\text{mm}$ |
| Hole Radius | $R_{\text{hole}}$ | $0.10$ | $\text{mm}$ |
| Shortest Distance to Hole Boundary | $d_{\text{min}}$ | $0.1121$ | $\text{mm}$ ($14.95\,\ell_0$) |
| Physical Clearance to Hole Lower Flank | $\Delta x_{\text{lig}}$ | $0.1581$ | $\text{mm}$ ($21.08\,\ell_0$) |
| Phase-Field Regularization Length | $\ell_0$ | $0.0075$ | $\text{mm}$ ($7.5\,\mu\text{m}$) |
| Target Element Resolution | $h_{\text{target}} \le \ell_0/2$ | $\le 0.00375$ | $\text{mm}$ ($\le 3.75\,\mu\text{m}$) |
| Benchmark Element Target | $N_{\text{elem}}$ | ~11,000–14,000 | Physical quads |

---

## 3. Evaluation of Candidate Donor 1: Linear-Elastic Pre-Analysis

### 3.1 Dataset Provenance and Topology
- **Source ODB:** `/scratch9/pr21vyci/runs/mode1_hole_method_a_test/PK_HOLE_METHOD_A_PREANALYSIS.odb`
- **File Size & Hash:** 2,883,480 bytes, SHA-256: `0A108C6A8404F1AF9D8F5DDC03223E9D8D051AB08587F841D9F5799970AE93B1`
- **Mesh Topology:** 2,906 physical elements (2,818 CPS4R quads, 88 CPS3 triangles), 3,010 nodes, single instance `PLATE-1`.
- **Loading State:** Step-1, Frame 10 (Time = 1.0, prescribed tensile displacement $u_y = 0.0050\,\text{mm}$ on top boundary $y = 1.0\,\text{mm}$).
- **Available Field Outputs:** `EVOL`, `MISESAVG`, `MISESERI`, `RF`, `S`, `U`.

### 3.2 Error Indicator Field Distribution ($\text{MISESERI}$)
Abaqus native relative error $\text{MISESERI}$ was extracted element-by-element across all 2,906 elements and segmented by physical region:

| Region | Element Count | $\text{MISESERI}_{\min}$ ($\text{MPa}$) | $\text{MISESERI}_{\text{mean}}$ ($\text{MPa}$) | $\text{MISESERI}_{\max}$ ($\text{MPa}$) | Contrast vs. Bulk |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Notch Root Core** ($r \le 0.05\,\text{mm}$) | 23 | $81.04$ | **$385.55$** | **$1,430.27$** | **$101.5\times$** |
| **Notch-to-Hole Ligament** | 63 | $41.15$ | **$120.46$** | $301.26$ | $8.5\times$ |
| **Hole Flank Boundary** | 43 | $37.14$ | **$139.52$** | $284.67$ | $9.9\times$ |
| **Far-Field Bulk Domain** | 2,777 | $0.42$ | **$14.09$** | $197.59$ | $1.0\times$ (Anchor) |
| **Global Plate Domain** | 2,906 | $0.42$ | $21.19$ (Median: $8.54$) | $1,430.27$ | — |

### 3.3 Spatial Concentration Analysis
The peak error indicator strictly concentrates at the singular sharp notch tip:
1. **Element 1184 (CPS4R):** Centroid $(0.5093, 0.5021)\,\text{mm}$ ($9.5\,\mu\text{m}$ from notch tip) reaches $\text{MISESERI} = 1,430.27\,\text{MPa}$.
2. **Element 402 (CPS4R):** Centroid $(0.5259, 0.5017)\,\text{mm}$ ($26.0\,\mu\text{m}$ from notch tip) reaches $\text{MISESERI} = 771.95\,\text{MPa}$.
3. **Element 647 (CPS4R):** Centroid $(0.4908, 0.4894)\,\text{mm}$ ($14.0\,\mu\text{m}$ from notch tip) reaches $\text{MISESERI} = 685.83\,\text{MPa}$.

**Key Scientific Finding for Donor 1:**  
While Donor 1 exhibits a healthy $10\times$ error contrast at the hole boundary ($139.52\,\text{MPa}$ vs. $14.09\,\text{MPa}$ bulk), the notch tip error is **more than an order of magnitude higher** ($1,430.27\,\text{MPa}$, $101.5\times$ bulk). Consequently, native Abaqus `UNIFORM_ERROR` remeshing targeting the singular notch tip will absorb nearly all allocated element degrees of freedom into the notch singularity, leaving the oblique ligament connecting the crack tip to the hole under-refined ($h > \ell_0/2$).

---

## 4. Evaluation of Candidate Donor 2: Coarse Phase-Field Simulation

### 4.1 Dataset Provenance and Topology
- **Source ODB:** `/scratch9/pr21vyci/runs/mode1_method_a_hole_coarse/PK_HOLE_COARSE_JOB1.odb`
- **File Size:** 518,169,932 bytes (~518.2 MB)
- **Solver & User Subroutine:** Abaqus/Standard with `f42_mixed_uel.for` (`CE8D5EDC...`).
- **Total Frames Solved:** 389 increments across 2 steps.
- **Physical Mesh:** 2,906 physical elements (8,718 layered elements: Layer 1 PF, Layer 2 Disp, Layer 3 Visualizer).

### 4.2 Deformation Checkpoints and Damage Evolution
Three objective deformation checkpoints were extracted and audited:

| Checkpoint | Step & Time | $u_y$ ($\text{mm}$) | $F_y$ ($\text{kN}$) | $d_{\max}$ | Softening Elements ($d \ge 0.10$) | Broken Elements ($d \ge 0.90$) | Physical Damage Topology |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Step 1 End** | Step 1, $t=1.0$ | $0.00500$ | $0.5843$ | $0.1691$ | 4 | 0 | Purely elastic precritical regime; damage confined to notch root |
| **Step 2 Peak** | Step 2, $t=0.3277$ | **$0.00729$** | **$0.7310$** | **$0.5798$** | **48** | **0** | **Peak load; active softening corridor nucleated toward lower hole flank** |
| **Step 2 End** | Step 2, $t=0.6558$ | $0.00959$ | $0.2164$ | $0.9976$ | 169 | 20 | Complete crack penetration into hole boundary; secondary crack initiated |

### 4.3 Physical Localization Along the Oblique Fracture Corridor
At the **Step 2 Peak Checkpoint** ($u_y = 0.00729\,\text{mm}$, $F = 0.7310\,\text{kN}$):
- Peak damage $d = 0.5798$ is reached at the crack tip.
- Exactly 48 elements satisfy $d \ge 0.10$, forming an **unbroken, continuous band of degrading material** extending diagonally from the notch tip $(0.50, 0.50)\,\text{mm}$ toward the lower flank of the off-axis hole $(0.65, 0.55)\,\text{mm}$.
- This damage localization introduces steep Cauchy stress gradients ($|\nabla \boldsymbol{\sigma}|$) and severe stress jump discontinuities across element boundaries in the UEL Cauchy stress field.

---

## 5. Falsifiable Scientific Hypothesis (`HYPOTHESIS F1728-H2-CASE2`)

Based on the quantitative contrast between Donor 1 and Donor 2, we formulate the following falsifiable hypothesis:

> **HYPOTHESIS F1728-H2-CASE2 (Donor State Governs Fracture Corridor Spatial Resolution):**  
> 1. Native Abaqus `UNIFORM_ERROR` remeshing driven strictly by linear-elastic pre-analysis (Step-1, Donor 1) will reproduce the negative ligament result observed in Case 1: elements at the notch root will refine to $h \le \ell_0/2$, but the uncracked oblique ligament connecting the crack tip to the hole flank will remain coarse ($h > \ell_0/2$) because linear elasticity lacks the localized stress gradients necessary to drive error along an uncracked path.  
> 2. Conversely, driving native remeshing from an authentic coarse phase-field donor checkpoint at peak load (Step-2 Peak, $u_y \approx 0.00729\,\text{mm}$, $d_{\max} \approx 0.58$, Donor 2) provides the physical stress redistribution and steep inter-element Cauchy stress jumps required for SPR to allocate $h \le \ell_0/2$ continuously along the entire oblique trajectory into the hole boundary without manual corridor seeding.

---

## 6. Execution Accounting and Ledger Reconciliation

To maintain absolute accounting integrity under the zero-submission policy:
- **New PBS Submissions for Subtask:** `0` (`max_new_pbs_submissions = 0`, `submissions_consumed = 0`).
- **Total Historical Task Submissions:** Permanently reconciled at `5` in all ledgers:
  1. `1423095.mmaster02` (FAILED - Python 2.7 import issue)
  2. `1423101.mmaster02` (FAILED - Argparse CAE syntax issue)
  3. `1423102.mmaster02` (FAILED - Python 2.7 makedirs issue)
  4. `1423103.mmaster02` (FAILED - Part/region mismatch in RemeshingRule)
  5. `1423169.mmaster02` (COMPLETED - 14,147 elements, datacheck Exit 0)

All records agree across [`project_coordination/ACTIVE_TASK.json`](file:///D:/Master%20thesis/Adaptive%20remeshing/project_coordination/ACTIVE_TASK.json), [`project_coordination/TASK_LEDGER.csv`](file:///D:/Master%20thesis/Adaptive%20remeshing/project_coordination/TASK_LEDGER.csv), and [`project_coordination/HPC_JOB_LEDGER.csv`](file:///D:/Master%20thesis/Adaptive%20remeshing/project_coordination/HPC_JOB_LEDGER.csv).

---

## 7. Recommended Next Governed Step

1. **Submit Review Packet `HND-F1728-CASE2-DONOR-QUAL-001` to Independent Review:**
   - Present the quantitative donor contrast, the physical damage evolution data, and `HYPOTHESIS F1728-H2-CASE2`.
   - Request formal independent review sign-off on Donor Qualification before initiating native remeshing for Case 2.
2. **Post-Review Action (Once Approved):**
   - Author a bounded, qualified native remeshing manifest for Case 2 using the unified framework (`reusable_2d_adaptive_framework.py`), evaluating both Donor 1 (baseline parity) and Donor 2 (physics-driven crack corridor resolution).
