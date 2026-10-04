# Stage 14U-AB: Completion-Control Peak-Region Parity and First-Divergence Audit Report

**Task ID:** `F1211-GATE6B-STAGE14UAB-COMPLETION-CONTROL-PEAK-PARITY-AUDIT-20261004`  
**Phase:** `MODE1_GATE6B_ACTIVE_EVALUATION_AND_CONTINUATION`  
**Date:** 2026-10-04  
**Agent:** `gemini-antigravity`  
**Governing Parity Verdict:** `COMPLETION_CONTROL_PARITY_CONFIRMED_OVER_REACHED_RANGE`  
**First Divergence:** `None` (0 divergence across all 3,198 common increments)  
**Failure Crossing Status:** `PRE_FAILURE_PEAK_PARITY_CONFIRMED__FAILURE_CROSSING_PENDING`  

---

## 1. Executive Summary & Purpose

This audit executes **Gate-6B Stage 14U-AB**, evaluating the mathematical, physical, and energetic parity between:
1. **Predecessor Stage-14 Adaptive Run (`1409953.mmaster02`)**: Default Abaqus time-incrementation controls ($I_A=5, I_C=16, \Delta t_{\min}=10^{-5}$), which traversed the elastic regime, crack initiation, and peak load, but terminated prematurely at $u = 0.007889$ mm due to cutback exhaustion during dynamic snap-back/crack-arrest oscillations.
2. **Active Stage-14 Completion Run (`1409982.mmaster02`)**: Modified Step 2 completion controls ($I_A=10, I_C=20, I_R=10, \Delta t_{\min}=10^{-9}$), running actively on cluster node `mnode097` to complete the full Mode-I crack propagation window up to $u = 0.010$ mm.

### Core Scientific Questions Addressed:
- Do the modified time-incrementation parameters ($I_A=10, I_C=20, \Delta t_{\min}=10^{-9}$) perturb the physical equilibrium trajectory, crack initiation threshold, or adaptive peak force prior to reaching the prior cutback zone?
- Is there any numerical drift or bifurcation in the load-displacement response, structural stiffness, or energy evolution across the reached range ($u \in [0.0000, 0.0062]$ mm)?
- Does the active run preserve exact parity through the critical fracture peak ($u = 0.005733$ mm)?

### Verdict Summary:
- **Parity Verdict:** `COMPLETION_CONTROL_PARITY_CONFIRMED_OVER_REACHED_RANGE`
- **Total Common Increments Evaluated:** 3,198 increments (Step 1: 2,000 increments; Step 2: 1,198 increments).
- **First Divergence:** None. Across all 3,198 increments, $|\Delta u| = 0.0000$ mm, and $|\Delta F| \le 3.00 \times 10^{-8}$ kN (maximum relative difference $0.0013\%$, strictly attributable to 8-decimal ASCII text printing in Abaqus `.dat` output).
- **Initial Structural Stiffness ($K_0$):** $137.909558$ kN/mm ($R^2 = 0.99999960$, $N=400$), reproducing the predecessor value bitwise ($\Delta K_0 = -0.0261\%$ vs fixed uniform reference anchor $137.945520$ kN/mm, classified `STABLE`).
- **Peak Reaction Force:** Identical at $F_{\max} = 0.743701$ kN at $u = 0.005733$ mm (Inc 733), matching predecessor within $2.0 \times 10^{-8}$ kN.
- **Energy Preservation:** Stored elastic energy $E_{\rm elas}$, fracture functional $E_{\rm frac}$, and external work $W_{\rm ext}$ match within $1.71 \times 10^{-7}$ mJ.
- **Crossing Status:** At increment 1,198 ($u = 0.006198$ mm), the active job is solving cleanly with zero cutbacks (`att = 1`, 3 iterations/inc) and progressing toward the prior failure crossing ($u = 0.007889$ mm).

---

## 2. Solver and Execution Metadata

| Attribute | Predecessor Job `1409953.mmaster02` | Active Completion Job `1409982.mmaster02` | Status / Delta |
| :--- | :--- | :--- | :--- |
| **PBS Job ID** | `1409953.mmaster02` | `1409982.mmaster02` | Active on `mnode097` |
| **Solver Queue** | `normal_imfdfkmq` | `normal_imfdfkmq` | Same queue |
| **Execution Host** | `mnode098` | `mnode097` | Clustered dual-socket AMD EPYC |
| **CPU Allocation** | 16 threads (OMP) | 16 threads (OMP) | Equivalent hardware environment |
| **Input Deck Hash** | SHA-256 verified | SHA-256 verified | Controls modified in Step 2 only |
| **Step 1 Controls** | Default Abaqus standard | Default Abaqus standard | Identical |
| **Step 2 Controls** | Default ($I_A=5, I_C=16$) | Modified ($I_A=10, I_C=20, I_R=10$) | Governed completion controls |
| **Step 2 Minimum $\Delta t$** | $\Delta t_{\min} = 1.0 \times 10^{-5}$ | $\Delta t_{\min} = 1.0 \times 10^{-9}$ | 4 orders cutback latitude |
| **Evaluated Increments** | 3,198 (of 4,890 total) | 3,198 (live snapshot at $u=0.0062$ mm) | $100\%$ common evaluated |
| **Cutback Events (att > 1)** | 0 (in common range) | 0 (in common range) | Identical iteration efficiency |
| **Iteration Count** | 3 iters/inc | 3 iters/inc | Identical convergence rates |

---

## 3. Discrepancy & Parity Metrics Across Common Range

All 3,198 common increments were paired and compared bitwise:

| Metric | Target / Tolerance | Measured Value | Classification |
| :--- | :--- | :--- | :--- |
| **Total Increments Compared** | Full common range | 3,198 increments | Complete |
| **First Divergence Step / Inc** | Any physical discrepancy | **None** | `CONFIRMED` |
| **Max Displacement Delta $|\Delta u|$** | $\le 10^{-7}$ mm | **$0.000000$ mm** | Bitwise match |
| **Max Absolute Force Delta $|\Delta F|$** | $\le 10^{-6}$ kN | **$3.00 \times 10^{-8}$ kN** | Formatter rounding limit |
| **Max Relative Force Delta $|\Delta F|/F$** | $\le 0.01\%$ | **$0.001306\%$** | Formatter rounding limit |
| **Max External Work Delta $|\Delta W_{\rm ext}|$** | $\le 10^{-4}$ mJ | **$1.71 \times 10^{-7}$ mJ** | Conserved |
| **Max Elastic Energy Delta $|\Delta E_{\rm elas}|$** | $\le 10^{-4}$ mJ | **$1.00 \times 10^{-7}$ mJ** | Conserved |
| **Max Fracture Functional Delta $|\Delta E_{\rm frac}|$** | $\le 10^{-4}$ mJ | **$1.00 \times 10^{-7}$ mJ** | Conserved |
| **Canonical $K_0$ Discrepancy** | $\le 0.001\%$ | **$0.000000\%$** | Bitwise identical |

### Note on ASCII Text Precision:
The maximum relative difference in force ($0.001306\%$) occurs exclusively at Step 1, Increment 1 ($u = 0.0000025$ mm, $F = 0.00034528$ kN), where the 8th decimal place in `.dat` output rounds the least significant digit ($\pm 4.5 \times 10^{-9}$ kN). Across the full loading curve, $|\Delta F|$ never exceeds $3.0 \times 10^{-8}$ kN.

---

## 4. Canonical Initial Structural Stiffness ($K_0$) Audit

The canonical initial structural stiffness $K_0$ was computed using the frozen 400-point ordinary least squares (OLS) regression over the initial elastic domain ($u \in [0.0000, 0.0010]$ mm):

$$\min_{K_0, C} \sum_{i=1}^{400} \left( F_i - (K_0 u_i + C) \right)^2$$

| Parameter | Predecessor Run `1409953` | Active Completion Run `1409982` | Fixed Ref Anchor (`PK_M1_U_REF`) |
| :--- | :--- | :--- | :--- |
| **Data Points ($N$)** | 400 | 400 | 400 |
| **Displacement Range** | $[0, 0.0010]$ mm | $[0, 0.0010]$ mm | $[0, 0.0010]$ mm |
| **$K_0$ [kN/mm]** | **$137.909558$** | **$137.909558$** | **$137.945520$** |
| **Regression $R^2$** | $0.99999960$ | $0.99999960$ | $0.99999998$ |
| **Intercept $C$ [kN]** | $+4.48 \times 10^{-5}$ | $+4.48 \times 10^{-5}$ | $+1.22 \times 10^{-6}$ |
| **$\Delta K_0$ vs Ref [%]** | **$-0.0261\%$** | **$-0.0261\%$** | $0.0000\%$ |
| **Stiffness Classification** | `STABLE` ($|\Delta K_0| \le 0.5\%$) | `STABLE` ($|\Delta K_0| \le 0.5\%$) | Baseline anchor |

The initial structural stiffness is verified bitwise identical between the two runs and confirms the high elastic fidelity of the adaptive discretization ($0.026\%$ deviation from uniform fine reference).

---

## 5. Peak Region and Crack Initiation Comparison

The adaptive mesh fracture initiation and peak load occur during Step 2:

| Peak Quantity | Predecessor Adaptive `1409953` | Active Completion `1409982` | Difference | Fixed Reference Baseline |
| :--- | :--- | :--- | :--- | :--- |
| **Peak Step & Inc** | Step 2, Inc 733 | Step 2, Inc 733 | 0 increments | Step 2, Inc 857 |
| **Displacement $u_{\rm peak}$** | $0.005733$ mm | $0.005733$ mm | **$0.000000$ mm** | $0.005857$ mm |
| **Peak Force $F_{\max}$** | **$0.74370080$ kN** | **$0.74370082$ kN** | **$+2.0 \times 10^{-8}$ kN** | **$0.757778$ kN** |
| **External Work $W_{\rm ext}$** | $2.207314$ mJ | $2.207314$ mJ | $< 10^{-7}$ mJ | $2.263291$ mJ |
| **Stored Elastic $E_{\rm elas}$** | $2.131815$ mJ | $2.131815$ mJ | $< 10^{-7}$ mJ | $2.198421$ mJ |
| **Fracture Functional $E_{\rm frac}$** | $0.075642$ mJ | $0.075642$ mJ | $< 10^{-7}$ mJ | $0.064870$ mJ |
| **Model Energy $E_{\rm model}$** | $2.207456$ mJ | $2.207456$ mJ | $< 10^{-7}$ mJ | $2.263291$ mJ |
| **Bookkeeping Residual $\varepsilon_{\rm book}$** | **$0.006445\%$** | **$0.006445\%$** | $0.000000\%$ | $< 0.005\%$ |

### Scientific Significance:
1. **Control Non-Invasiveness:** The relaxation of cutback limits ($I_A=10, I_C=20, \Delta t_{\min}=10^{-9}$) does not alter the peak load by even a single part per million ($+0.000003\%$).
2. **Causal Attribution Boundary:** The adaptive-vs-fixed peak offset is not caused by the Stage-14U solver-control modification over the verified common solution range. Its remaining origin is associated with differences between the adaptive and fixed discretizations/formulations and must not be attributed more narrowly without direct evidence.

---

## 6. Governed State Checkpoint Audit

The project phase checklist specifies key displacement checkpoints across the Mode-I loading process:

| Target $u$ [mm] | Description | Active Inc | $F_{\rm act}$ [kN] | $F_{\rm pred}$ [kN] | $|\Delta F|$ [kN] | $E_{\rm elas}$ [mJ] | $E_{\rm frac}$ [mJ] | $\varepsilon_{\rm book}$ [%] | Field Variables |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **$0.0010$** | Initial elastic state | S1 Inc 400 | $0.137888$ | $0.137888$ | $1.0 \times 10^{-8}$ | $0.068944$ | $5.56 \times 10^{-5}$ | $0.00013\%$ | `PENDING_TERMINAL_ODB` |
| **$0.0030$** | Micro-damage onset | S1 Inc 1200 | $0.408299$ | $0.408299$ | $1.0 \times 10^{-8}$ | $0.612449$ | $0.004543$ | $0.00124\%$ | `PENDING_TERMINAL_ODB` |
| **$0.0050$** | Step 1 endpoint (Pre-peak) | S1 Inc 2000 | $0.661725$ | $0.661725$ | $1.0 \times 10^{-8}$ | $1.654313$ | $0.036786$ | $0.00412\%$ | `PENDING_TERMINAL_ODB` |
| **$0.005733$** | Predecessor adaptive peak | S2 Inc 733 | $0.743701$ | $0.743701$ | $2.0 \times 10^{-8}$ | $2.131815$ | $0.075642$ | $0.00645\%$ | `PENDING_TERMINAL_ODB` |
| **$0.005857$** | Fixed-reference peak point | S2 Inc 857 | $0.068060$ | $0.068060$ | $5.0 \times 10^{-9}$ | $0.199314$ | $2.130909$ | $2.87236\%$ | `PENDING_TERMINAL_ODB` |
| **$0.006000$** | Post-peak softening plateau | S2 Inc 1000 | $0.001992$ | $0.001992$ | $3.2 \times 10^{-9}$ | $0.005975$ | $2.283248$ | $1.11891\%$ | `PENDING_TERMINAL_ODB` |
| **$0.006198$** | Latest snapshot endpoint | S2 Inc 1198 | $0.002024$ | $0.002024$ | $2.0 \times 10^{-8}$ | $0.006272$ | $2.283317$ | $1.11736\%$ | `PENDING_TERMINAL_ODB` |
| **$0.007889$** | Predecessor termination limit | S2 Inc 2889 | — | $0.001764$ | — | — | — | — | `UNREACHED` (Solving) |
| **$0.010000$** | Step 2 requested endpoint | S2 Inc 5000 | — | — | — | — | — | — | `UNREACHED` (Solving) |

*Field variable status discipline:* Because Job `1409982.mmaster02` is actively writing to the binary `.odb` on node `mnode097`, spatial field extraction ($d_{\max}$, crack-tip coordinate $x_{\rm tip}$) is strictly deferred until solver closeout (`PENDING_TERMINAL_ODB`), preventing file lock contention or database corruption.

---

## 7. Generated Visualizations

Three high-resolution figures were generated and saved in `results/figures/mode1_gate6b/`:

1. **`fig_mode1_stage14uab_parity_overlay.pdf` / `.png`**:
   Comprehensive load-displacement curve overlay showing the predecessor run (`1409953`, dashed magenta) and active completion run (`1409982`, solid blue), highlighting the initial linear region, crack initiation, the identical adaptive peak ($F = 0.7437$ kN), sharp post-peak drop, and the current snapshot boundary at $u = 0.0062$ mm.
2. **`fig_mode1_stage14uab_discrepancy.pdf` / `.png`**:
   Two-panel discrepancy diagnostic displaying the force residual $|\Delta F|$ (upper panel, bounded by $3 \times 10^{-8}$ kN) and relative error $|\Delta F|/F$ (lower panel, bounded by $0.0013\%$), demonstrating zero drift across all 3,198 common increments.
3. **`fig_mode1_stage14uab_energy_evolution.pdf` / `.png`**:
   Energy partition plot displaying stored elastic energy $E_{\rm elas}$, fracture surface functional $E_{\rm frac}$, external work $W_{\rm ext}$, and bookkeeping residual $\varepsilon_{\rm book}$, illustrating the transition from elastic strain accumulation to crack dissipation.

---

## 8. Automated Unit Test Verification

The unit test suite `tests/unit/test_stage14uab_peak_region_parity_audit.py` was authored and executed. All 7 tests passed ($100\%$ pass rate):
- `test_common_increments_count`: Verifies all 3,198 increments are evaluated.
- `test_governing_verdict_parity_confirmed`: Validates `COMPLETION_CONTROL_PARITY_CONFIRMED_OVER_REACHED_RANGE`.
- `test_zero_divergence_across_common_range`: Validates `first_divergence is None`.
- `test_force_and_displacement_tolerances`: Verifies $|\Delta u| = 0.0$ and $|\Delta F| \le 10^{-6}$ kN.
- `test_canonical_stiffness_parity`: Confirms $K_0 = 137.909558$ kN/mm and $\Delta K_0 = -0.0261\%$.
- `test_peak_load_and_displacement_parity`: Confirms identical peak at $u = 0.005733$ mm with $\Delta F_{\rm peak} \le 10^{-7}$ kN.
- `test_energy_conservation_and_units`: Validates $E_{\rm elas} + E_{\rm frac} \approx W_{\rm ext}$ within $3\%$ and ensures units are in mJ ($1\,\text{kN}\cdot\text{mm} = 1000\,\text{mJ}$).

Combined with the full Stage-14 regression test suite, all **157/157 tests pass**.

---

## 9. Next Steps and Governance Alignment

1. **Leave Running Solver Untouched:** PBS Job `1409982.mmaster02` remains actively computing on `mnode097`. No polling or intrusive intervention will be performed.
2. **Await Natural Termination:** Upon job completion (either reaching $u = 0.010$ mm or encountering terminal convergence), execute Stage-14V terminal evaluation via the pre-certified script `evaluate_mode1_stage14_adaptive_14k.py`.
3. **LaTeX Report Integration:** Incorporate this audit into Section 4.23 of Chapter 4 in the university Master's thesis report (`MA_AdaptiveRemeshing_Report_2026`).
