# GATE-1 POST-MORTEM EXECUTION RECORD: JOB 1401449
**Document ID:** `GATE1_JOB1401449_FIXED_MESH_REFINEMENT_RECORD_2026-09-04`  
**Date of Execution:** 2026-09-04T15:55:09+02:00  
**Date of Post-Mortem Audit:** 2026-09-05T06:18:00+02:00  
**Candidate Name:** `PK_M1_FIX_H0015`  
**PBS Job ID:** `1401449.mmaster02`  
**Preceding Datacheck PBS Job ID:** `1401447.mmaster02` (Exit Status: 0 / `DATACHECK_PASSED_CLEAN`)  
**Governing Anchor Reference:** Job `1398090.mmaster02` (`PK_M1_FIXED_REF`, $h = 0.0030\,\mathrm{mm}$, $15{,}192$ finite elements)  
**Technical Completion Status:** `PARTIAL_RUN_WITH_CUTBACK_TERMINATION` (Exit status 1 on Step 2 increment 2837 at $u = 0.007836\,\mathrm{mm}$)  
**Scientific Utility Classification:** `PROVISIONAL_SINGLE_REFINEMENT_EVALUATION` (Single refinement level; insufficient for asymptotic convergence)  
**Governing Gate Status:** `GATE_2_OPEN_INSUFFICIENT_MULTI_MESH_EVIDENCE`  

---

## 1. Executive Summary & Forensic Audit
This document records the post-mortem retrieval, telemetry extraction, and strict evidence-based classification of the **Gate-1 Fixed-Mesh Refinement Candidate** (`PK_M1_FIX_H0015`, PBS Job ID `1401449.mmaster02`).

The model tested a $2\times$ spatial mesh refinement in the crack corridor ($h = 0.0015\,\mathrm{mm}$, $41{,}912$ quad finite elements) against the governing reference anchor (`1398090.mmaster02`, $h = 0.0030\,\mathrm{mm}$, $15{,}192$ quad finite elements).

### Key Findings:
1. **Technical Completion:** The solver completed Step 1 cleanly ($2{,}000$ increments to $u = 0.0050\,\mathrm{mm}$) and progressed through $2{,}837$ increments in Step 2 to $u = 0.007836\,\mathrm{mm}$, capturing initial elasticity, peak force ($F_{\max} = 0.73220\,\mathrm{kN}$ at $u = 0.005633\,\mathrm{mm}$), and the major post-peak softening drop down to $F = 0.000168\,\mathrm{kN}$ ($99.98\%$ load drop). At $u = 0.007836\,\mathrm{mm}$, cutback limit was exhausted (5 consecutive cutbacks), resulting in `Exit_status = 1`.
2. **Phase-Field Field Output Limitation:** The companion element layer (`DISP_QUAD`, `CPE4`) was assigned passive elasticity (`MAT_PASSIVE`) without an active UMAT/UVARM state transfer bridge. Consequently, `SDV` (phase-field damage $d$) was not recorded in the ODB. Full ligament separation cannot be inferred from force drop alone without direct $d$-field contours.
3. **Scientific Classification:** As a single isolated refinement level ($h=0.0015\,\mathrm{mm}$ vs baseline $h=0.0030\,\mathrm{mm}$), this run cannot establish asymptotic mesh convergence. It is classified as provisional diagnostic evidence.

---

## 2. Quantitative Evidence Matrix (Common Displacement Interval $u \in [0, 0.007836\,\mathrm{mm}]$)

| Quantity / Metric | Literature Target (Pandey & Kumar 2025 Fig. 7a) | Governing Anchor (`1398090.mmaster02`) | Candidate Refinement (`1401449.mmaster02`) | Discrepancy ($\Delta_{\text{anchor}}$) | Status / Classification |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Mesh Resolution ($h_{\min}$)** | $\approx 0.0030\,\mathrm{mm}$ | $h = 0.0030\,\mathrm{mm}$ ($h/l_0 = 0.40$) | $h = 0.0015\,\mathrm{mm}$ ($h/l_0 = 0.20$) | $2\times$ Refinement | Isolated numerical factor |
| **Finite Element Count** | $15{,}192$ (Standard PFM) | $15{,}192$ quad elements | $41{,}912$ quad elements | $+175.9\%$ ($2.76\times$) | Verified count |
| **Node Count** | Not reported | $15{,}521$ nodes ($15{,}522$ with RP) | $42{,}492$ nodes ($42{,}493$ with RP) | $+173.8\%$ | Verified count |
| **Linear Stiffness $K_0$ ($u \le 0.0010\,\mathrm{mm}$)** | $\approx 138.1\,\mathrm{kN/mm}$ | $138.088\,\mathrm{kN/mm}$ (regress: $137.95$) | $137.858\,\mathrm{kN/mm}$ (secant: $137.84$) | $-0.07\%$ | **Identical compliance** |
| **Early Softening $K_0$ ($u \in [0.0005, 0.0035]$)** | N/A | $135.166\,\mathrm{kN/mm}$ | $135.068\,\mathrm{kN/mm}$ | $-0.07\%$ | Sub-critical damage softening |
| **Peak Force ($F_{\max}$)** | $\approx 0.7580\,\mathrm{kN}$ | $0.757778\,\mathrm{kN}$ | $0.732196\,\mathrm{kN}$ | $-3.38\%$ | Single-level shift |
| **Peak Displacement ($u(F_{\max})$)** | $\approx 0.005860\,\mathrm{mm}$ | $0.005857\,\mathrm{mm}$ | $0.005633\,\mathrm{mm}$ | $-3.82\%$ | Pre-peak shift |
| **Common Interval Endpoint ($u_{\max}$)**| N/A | $0.007836\,\mathrm{mm}$ (truncated) | $0.007836\,\mathrm{mm}$ (terminal) | Identical | Truncated for evaluation |
| **Normalized $L_2$ Curve Error on Common Interval**| N/A | Reference baseline ($0.0\%$) | $36.31\%$ | Shift in steep drop | Peak shift artifact |
| **Max Force Difference on Common Interval** | N/A | Baseline | $0.75755\,\mathrm{kN}$ at $u = 0.005857\,\mathrm{mm}$| Post-peak offset | At anchor peak position |
| **External Work on Common Interval ($W_{\text{ext}}$)**| N/A | $2.3587\times 10^{-3}\,\mathrm{J}$ ($2.3587\,\mathrm{mJ}$)| $2.1902\times 10^{-3}\,\mathrm{J}$ ($2.1902\,\mathrm{mJ}$)| $-7.14\%$ | Area under $F-u$ curve |
| **Total Converged Increments** | $7{,}000$ | $7{,}000$ increments | $4{,}837$ increments | $-30.9\%$ | Terminated at $u=0.007836$ |
| **Total Solver Iterations** | $21{,}120$ | $21{,}120$ iterations | $14{,}678$ iterations | $-30.5\%$ | 14,672 linear solves |
| **Total Cutbacks** | $0$ | $0$ cutbacks | $5$ cutbacks (at increment 2837) | All in final inc | Cutback exhaustion |
| **Wallclock Execution Time** | $\approx 6.5\,\mathrm{h}$ | $6\text{h } 31\text{m } 02\text{s}$ | $13\text{h } 21\text{m } 08\text{s}$ | $+105.0\%$ | HPC runtime |

---

## 3. Epistemic Classification of Hypotheses vs. Numerical Facts

1. **Stiffness Definition & Reconciliation (NUMERICALLY VERIFIED):**
   - The reported anchor value of $K_0 \approx 138\,\mathrm{kN/mm}$ represents the true initial linear-elastic structural stiffness ($u \le 0.0010\,\mathrm{mm}$), before phase-field damage initiates at the crack tip.
   - The $135.166\,\mathrm{kN/mm}$ value arose from an automated regression window $u \in [0.0005, 0.0035]\,\mathrm{mm}$, which includes non-linear sub-critical degradation.
   - Both models exhibit identical initial linear stiffness ($138.088\,\mathrm{kN/mm}$ vs $137.858\,\mathrm{kN/mm}$, diff $<0.1\%$).
2. **Peak Force Shift (SCIENTIFIC HYPOTHESIS):**
   - The $-3.38\%$ drop in $F_{\max}$ ($0.7578\,\mathrm{kN} \to 0.7322\,\mathrm{kN}$) and $-3.82\%$ drop in $u(F_{\max})$ are hypothesized to result from improved discrete resolution of the phase-field gradient term $\frac{l_0}{2}|\nabla d|^2$ at $h/l_0 = 0.20$ vs $0.40$.
   - **Hypothesis status:** Unproven. This cannot be stated as a proven physical mechanism until at least three mesh levels ($h=0.0030, 0.0020, 0.0015, 0.0010\,\mathrm{mm}$) demonstrate asymptotic scaling.
3. **Solver Negative Eigenvalue Message (SOLVER OBSERVATION):**
   - Step 2 produced 1 negative eigenvalue diagnostic in the Abaqus message file. This indicates loss of positive-definiteness of the tangent stiffness matrix during softening, but cannot be classified as a physical bifurcation mode without explicit spectral analysis of the operator.
4. **Damage Field and Crack Path (UNRESOLVED):**
   - Because `SDV` was not transferred to companion elements in this input deck, direct contour plots of $d(x,y)$ and crack tip tracking are unverified from the ODB.

---

## 4. Gate-2 Status & Next Controlled Action

- **Gate 2 Evaluation:** Gate 2 cannot be closed with only two mesh levels ($h=0.0030\,\mathrm{mm}$ and $h=0.0015\,\mathrm{mm}$) and without companion visualization transfer for $d(x,y)$.
- **Single Smallest Controlled Next Step:**
  1. Implement and verify a coupled visualization state-transfer bridge for standard fixed-mesh models so that $d(x,y)$ and $H(x,y)$ are exported to the ODB.
  2. Perform a controlled three-point mesh study ($h=0.0030, 0.0020, 0.0015\,\mathrm{mm}$) with identical solver controls and time-stepping to evaluate asymptotic convergence.
  3. No new simulations are launched until authorized.
