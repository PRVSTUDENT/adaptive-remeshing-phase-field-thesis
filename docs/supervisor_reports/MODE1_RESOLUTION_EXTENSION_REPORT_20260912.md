# Mode-I Resolution Extension: Scientific Investigation Progress Report

**Milestone:** Post-Handoff Mode-I Resolution Extension (Audited & Reconciled)  
**Date:** 2026-09-12  
**HPC Platform:** TU Bergakademie Freiberg Cluster (`normal_imfdfkmq`)  
**Controller Flag:** `ModeIResolutionExtensionActive = True`  

---

## Executive Summary

This report delivers the quantitative scientific resolution and raw-data verification of the post-handoff Mode-I extension across two governing priority questions and the Gate-6 full-fracture requalification:

1. **Priority Question A (Stiffness Anomaly Causal Closure):** Traced definitively to silent Abaqus input pre-processor (`pre`) truncation of overlong single-line boundary node set records (`N_TOP`, `N_BOTTOM`). Multi-line wrapping ($\le 16$ entries/line) restores 100% node ingestion, strictly eliminating unconstrained boundary drift/lift ($0.0000\text{ mm}$ everywhere) and recovering the authoritative initial stiffness branch ($K_0 = 138.021015\text{ kN/mm}$, $+0.0547\%$ vs fixed reference anchor).
   * **Epistemic Classification:** `CAUSAL_CLOSURE_VERIFIED_BOUNDARY_SET_LINE_FORMATTING`
2. **Gate-6 Requalification Audit (Job 1404454.mmaster02 vs Fixed Reference 1398090.mmaster02):** Recomputed directly from raw extracted CSV arrays over the exact common displacement interval ($0 \le u \le 0.00677407\text{ mm}$, $N = 3,786$ points):
   * **Initial Stiffness:** $K_0 = 137.820804\text{ kN/mm}$ ($\Delta K_0 = -0.0904\%$ vs reference anchor $137.945520\text{ kN/mm}$, $N=400$, $R^2 = 0.99999960$).
   * **Peak Load:** $F_{\max} = 0.745325\text{ kN}$ at $u = 0.005750\text{ mm}$ vs reference $F_{\max} = 0.757778\text{ kN}$ at $u = 0.005857\text{ mm}$ ($\Delta F_{\max} = -1.643\%$, $\Delta u_{\text{peak}} = -1.827\%$).
   * **Pre-Peak Curve Agreement ($0 \le u \le 0.005750\text{ mm}$):** Discrete RMS error = $0.000625\text{ kN}$ ($0.625\text{ N}$, $0.082\%$ of peak load; continuous $L_2 = 0.507\text{ N}$, $0.067\%$).
   * **Common-Interval Curve Discrepancy ($0 \le u \le 0.00677407\text{ mm}$):** Discrete RMS error = $0.160501\text{ kN}$ ($160.501\text{ N}$, $21.18\%$ of peak load; continuous $L_2 = 119.749\text{ N}$, $15.80\%$). At the cutoff $u = 0.006774\text{ mm}$, the adaptive model retains $F = 0.184465\text{ kN}$ while the fixed reference has dropped to $F = 0.000454\text{ kN}$.
   * **External Work $\int F\,du$ ($\text{kN}\cdot\text{mm} = \text{J}$):** $W_{\text{adapt}} = 2.572602\text{ mJ}$ vs $W_{\text{ref,common}} = 2.358288\text{ mJ}$ ($\Delta W = +9.088\%$).
   * **Terminal Solver Evidence:** Terminated at $u = 0.00677407\text{ mm}$ (Step 2, Inc 1784) due to **deep-post-peak nonlinear convergence failure / minimum-increment exhaustion** (`***ERROR: TIME INCREMENT REQUIRED IS LESS THAN THE MINIMUM SPECIFIED`, $dt < 1.0 \times 10^{-14}$), not PBS walltime exhaustion.
   * **Field Output Evidence Boundary:** In `PK_M1_NOM1_FIELD_QUAL.odb`, only nodal `RF` and `U` were written. Scalar damage SDV14 was omitted because `*ELEMENT OUTPUT` targeted the UEL layer `DISP_QUAD`. Crack-path and damage localization profiles in Figure 4 are preserved from the verified reference model `fixture_h0015` and earlier companion-enabled runs (`1399632`), confirming horizontal localization along $y = 0.50\text{ mm}$. Direct damage profile-difference norms for 1404454 are unavailable in the raw ODB.
   * **Scientific Classification:** `CORRECTED_HIGH_BRANCH_ADAPTIVE_REPRODUCTION_PARTIALLY_QUALIFIED` (reflecting pre-peak strict qualification combined with the post-peak softening divergence and ODB damage field omission).
3. **Priority Question B (Remesh Count Discrepancy):** Pre-analysis physics accounts for only a minor $-1.47\%$ difference ($71,320 \to 70,271$). A verified Abaqus software release effect accounts for a $-45.5\%$ reduction ($71,320 \to 38,876$ elements between 2023 and 2021). The publication omits software release details and contains internal discrepancies ($14,804$ in Listing 2 vs $13,941$ in Section 4.1). Draft author inquiry remains strictly **unsent** pending supervisor authorization.
   * **Epistemic Classification:** `UNRESOLVED_WITH_VERIFIED_RELEASE_EFFECT_AND_PUBLICATION_INFORMATION_MISSING`

---

## 1. Quantitative Benchmark Anchor & Raw Data Provenance

All evaluations are anchored to the authoritative fixed-mesh reference solution and cross-checked against raw cryptographic hashes:

* **Fixed Reference Job:** `1398090.mmaster02` (`PK_MODE1_STANDARD_PFM`, 15,192 finite elements, $1.0 \times 1.0\text{ mm}$ plate, $a_0 = 0.5\text{ mm}$ zero-gap sharp seam)
  * Raw Extracted Curve: `curve_standard_1398090.csv`  
    `SHA256: 780d05d39532e778802cdd8503cdd0df25568e412c3d4a51c50f4e001febede6`
  * Unconstrained Initial Stiffness Anchor ($0 < u \le 0.0010\text{ mm}$, $N=400$):  
    $$\mathbf{K_0 = 137.945520\text{ kN/mm}} \quad (\text{Intercept } b = 4.472368 \times 10^{-5}\text{ kN}, \; R^2 = 0.99999960)$$
  * Peak Reaction Force & Displacement:  
    $$F_{\max} = 0.757778\text{ kN}, \quad u(F_{\max}) = 0.005857\text{ mm}$$
  * Literature Digitized Anchor (Pandey & Kumar 2025, Fig. 7(a)):  
    $$F_{\max} \approx 0.758\text{ kN}, \quad u(F_{\max}) \approx 0.005860\text{ mm}$$
* **Corrected Nominal 1% Adaptive Job:** `1404454.mmaster02` (`PK_M1_NOM1_FIELD_QUAL`, 71,320 finite elements, cleanly wrapped lines)
  * Raw Extracted Curve: `PK_M1_NOM1_FQ_raw_Fu.csv`  
    `SHA256: e40eb63a529f1d99f54b9d60fafd178bd8c566d190386f0967aa1434c3ba9a96`
  * Status File: `PK_M1_NOM1_FIELD_QUAL.sta`  
    `SHA256: 24ad755d5cca74ccb3e155a3c64bd3ce74f5fdc245a1278a7a5e0c5c1a209c28`
  * Input Deck: `PK_M1_NOM1_FIELD_QUAL.inp`  
    `SHA256: 4ee2b75a4bf3a1a0812f96269976fff389dcc0215b6de2617c22fbc1ab2993ba`

---

## 2. Priority Question A: Stiffness Anomaly Causal Closure

### Epistemic Status: `CAUSAL_CLOSURE_VERIFIED_BOUNDARY_SET_LINE_FORMATTING`

### Calibrated Diagnostic Scope & Terminal Evidence
The paired diagnostic jobs `1404901.mmaster02` (Pair A: overlong line) and `1404902.mmaster02` (Pair B: wrapped multi-line) terminated by PBS walltime limit (`Exit_status = -29`) after reaching $u = 0.000622\text{ mm}$ (311 increments) and $u = 0.000790\text{ mm}$ (395 increments), respectively.

Because these runs were interrupted by walltime prior to $u = 0.0010\text{ mm}$, their regressions are **not** described as completed $0 < u \le 0.0010\text{ mm}$ canonical windows or as full-fracture simulations. Instead, all available data points lie strictly inside the canonical elastic-window upper bound ($u \le 0.0010\text{ mm}$), and their constant linear slopes, exact one-factor deck difference, parsed-set cardinalities, and directly measured boundary drift/lift provide conclusive equation-level causal proof:

```
+---------------------------------------------------------------------------------------------------------+
|                                    CONTROLLED ONE-FACTOR DIAGNOSTIC PAIR                                |
+---------------------------------------------------+-----------------------------------------------------+
| Diagnostic Metric                                 | Pair A (1404901): Overlong Single-Line              | Pair B (1404902): Cleanly Wrapped Multi-Line        |
+---------------------------------------------------+-----------------------------------------------------+
| .inp Deck Line Formatting                         | Single overlong line (>2,000 characters)            | Wrapped lines (16 entries per line)                 |
| Ingested Top Boundary Nodes (N_TOP / 210)         | 16 nodes (92.4% dropped by parser)                  | 210 nodes (100.0% parsed)                           |
| Ingested Bottom Boundary Nodes (N_BOTTOM / 150)   | 16 nodes (89.3% dropped by parser)                  | 150 nodes (100.0% parsed)                           |
| Top Edge Horizontal Drift (max |u1|)              | 6.1626e-05 mm (194 unconstrained nodes)             | 0.0000 mm (0 unconstrained nodes)                   |
| Bottom Edge Vertical Lift (max |u2|)              | 2.8564e-04 mm (134 unconstrained nodes)             | 0.0000 mm (0 unconstrained nodes)                   |
| Linear Initial Stiffness K0                       | 122.599592 kN/mm                                    | 138.021015 kN/mm                                    |
| Relative Error vs Fixed Reference Anchor          | -11.125% (Defective Lower Branch)                   | +0.0547% (Reference Branch)                         |
| OLS Regression Quality (all available pts)        | R^2 = 0.999999999999999                             | R^2 = 0.999999999999999                             |
+---------------------------------------------------+-----------------------------------------------------+
```

### Forensic Mechanism & Confounded Hypothesis Retirement
1. **Pre-Processor Silent Truncation:** In Abaqus/Standard input processing (`pre`), line records exceeding standard buffer limits without explicit continuation lines are silently truncated, reading only the first 16 comma-separated node tokens per record.
2. **Kinematic Consequence:** On the top edge ($y = 1.0\text{ mm}$), 194 out of 210 nodes were omitted from constraint equations, allowing horizontal drift ($|u_1| = 6.16 \times 10^{-5}\text{ mm}$). On the bottom roller ($y = 0.0\text{ mm}$), 134 out of 150 nodes were omitted, allowing vertical lift ($|u_2| = 2.86 \times 10^{-4}\text{ mm}$). This unconstrained kinematic freedom artificially softened the structure, reducing $K_0$ from $\approx 138\text{ kN/mm}$ to $\approx 122.60\text{ kN/mm}$.
3. **Restoration:** Wrapping boundary node set entries to 16 nodes per line restores 100% constraint enforcement, eliminates boundary lift/drift ($0.0000\text{ mm}$ everywhere), and restores initial stiffness to $K_0 = 138.021015\text{ kN/mm}$ ($+0.0547\%$ vs reference anchor).
4. **Retirement of Confounded Hypotheses:** Earlier hypotheses attributing stiffness loss to intrinsic `UNSYMM=YES` $\times$ companion element coupling are formally retired as confounded, while preserving their historical raw data.

---

## 3. Gate-6 Full-Fracture Requalification Audit (Job 1404454 vs Reference 1398090)

### Epistemic Status: `CORRECTED_HIGH_BRANCH_ADAPTIVE_REPRODUCTION_PARTIALLY_QUALIFIED`

### Solver Execution & Terminal Telemetry
* **Job Identifier:** `1404454.mmaster02` (`PK_M1_NOM1_FIELD_QUAL`)
* **Mesh & Formulation:** 71,320 finite elements ($70,845$ regular nodes), publication-literal nominal 1% adaptive refinement, multi-line wrapped boundary sets, serial 1-CPU execution under Abaqus 2023.
* **Terminal Telemetry (from `.sta` and `.msg`):**
  * `job_state = F`, `Exit_status = 1`
  * Execution time: Walltime `18:34:50` (66,890 s), CPU time `18:31:40` (66,700 s)
  * Increments: 3,784 total (Step 1: 2,000 increments; Step 2: 1,784 increments, 1,783 converged)
  * Newton Iterations: 11,764; Cutbacks: 21 automatic cutbacks (30 cutback attempts)
  * Achieved Displacement: $u_{\text{terminal}} = 0.00677406881\text{ mm}$
  * Last Converged Increment: Step 2, Increment 1783, Attempt 3 ($dt = 7.459 \times 10^{-14}$)
  * **Termination Cause:** **Deep-post-peak nonlinear convergence failure / minimum-increment exhaustion** (`***ERROR: TIME INCREMENT REQUIRED IS LESS THAN THE MINIMUM SPECIFIED`, $dt < 1.0 \times 10^{-14}$ at Step 2 Increment 1784 Attempt 4). This was a solver convergence termination, not PBS walltime exhaustion.

### Raw Curve Recomputation & Cross-Check ($0 \le u \le 0.00677407\text{ mm}$)

| Metric / Parameter | Corrected Adaptive (Job 1404454) | Fixed Reference (Job 1398090) | Relative Error / Discrepancy | Operational Status |
| :--- | :--- | :--- | :--- | :--- |
| **Number of Finite Elements** | **71,320** | **15,192** | $+369.5\%$ | Adaptive Discretization |
| **Canonical Initial Stiffness $K_0$** | **$137.820804\text{ kN/mm}$** | **$137.945520\text{ kN/mm}$** | $\mathbf{-0.0904\%}$ | **STRICT_PARITY_PASS** |
| Initial Fit Quality ($N=400$, $0 < u \le 0.001$) | $R^2 = 0.99999960$, $b = 4.470 \times 10^{-5}$ | $R^2 = 0.99999960$, $b = 4.472 \times 10^{-5}$ | Identical linearity | Highly Linear |
| **Peak Reaction Force $F_{\max}$** | **$0.745325\text{ kN}$ ($745.325\text{ N}$)** | **$0.757778\text{ kN}$ ($757.778\text{ N}$)** | $\mathbf{-1.643\%}$ | **HIGH_PRECISION_PASS** |
| **Displacement at Peak $u(F_{\max})$** | **$0.005750\text{ mm}$** | **$0.005857\text{ mm}$** | $\mathbf{-1.827\%}$ | **HIGH_PRECISION_PASS** |
| **Pre-Peak Discrete RMS Error** ($u \le 0.00575$) | **$0.000625\text{ kN}$ ($0.625\text{ N}$)** | Baseline ($0.0\text{ N}$) | $0.082\%$ of peak load | **EXCELLENT_AGREEMENT** |
| Pre-Peak Continuous $L_2$ Error | **$0.000507\text{ kN}$ ($0.507\text{ N}$)** | Baseline ($0.0\text{ N}$) | $0.067\%$ of peak load | **EXCELLENT_AGREEMENT** |
| **Common-Interval Discrete RMS Error** | **$0.160501\text{ kN}$ ($160.501\text{ N}$)** | Baseline ($0.0\text{ N}$) | $\mathbf{21.18\%}$ of peak load | Post-peak plateau divergence |
| Common-Interval Continuous $L_2$ Error | **$0.119749\text{ kN}$ ($119.749\text{ N}$)** | Baseline ($0.0\text{ N}$) | $\mathbf{15.80\%}$ of peak load | Trapezoid $\sqrt{\frac{1}{u_{\text{cut}}}\int \Delta F^2 du}$ |
| Uniform 1000-Point Grid RMS Error | **$0.119696\text{ kN}$ ($119.696\text{ N}$)** | Baseline ($0.0\text{ N}$) | $15.80\%$ of peak load | Uniform grid cross-check |
| **External Work $W_{\text{ext}} = \int F\,du$** | **$2.572602\text{ mJ}$ ($0.002573\text{ J}$)** | **$2.358288\text{ mJ}$ ($0.002358\text{ J}$)** | $\mathbf{+9.088\%}$ | Trapezoidal rule ($\text{kN}\cdot\text{mm}=\text{J}$) |
| Reaction Force at Cutoff ($u=0.006774\text{ mm}$) | $0.184465\text{ kN}$ ($184.465\text{ N}$) | $0.000454\text{ kN}$ ($0.454\text{ N}$) | Intermediate plateau | Residual resistance at abort |

### Reconciliation Against Historical Gate-6 Ledger Values
* **Historical Defective Run (Job 1399632):** In earlier ledgers (`gate6_reconciled_master_metrics.json`), the nominal 1% mesh had $K_0 = 122.378544\text{ kN/mm}$ ($-11.28\%$), $F_{\max} = 0.478203\text{ kN}$ ($-36.9\%$), and full-history work $W = 2.006865\text{ mJ}$. This was caused entirely by the single overlong line parser truncation defect.
* **Corrected Requalification (Job 1404454):** Multi-line wrapping strictly resolves the elastic stiffness anomaly ($K_0 = 137.820804\text{ kN/mm}$, $-0.0904\%$) and peak load ($F_{\max} = 0.745325\text{ kN}$, $-1.643\%$).
* **Discrepancy in External Work & Softening:** The newly computed work ($2.572602\text{ mJ}$) is evaluated over the common cutoff $[0, 0.00677407\text{ mm}]$, where Job 1404454 exhibits a delayed softening drop ($F = 0.1845\text{ kN}$ at abort) compared to the rapid load drop of the fixed reference ($F = 0.00045\text{ kN}$). This post-peak divergence explains why common-interval RMS error is $21.18\%$ despite pre-peak RMS error being only $0.08\%$.

---

## 4. Field Evidence Audit & Matched Checkpoint Table

### ODB Field Inventory & Technical Finding
A direct inspection of `PK_M1_NOM1_FIELD_QUAL.odb` using Abaqus Python confirmed:
* Step-1 (2,001 frames) and Step-2 (1,785 frames) contain **only** nodal `RF` and `U` (`['RF', 'U']`).
* Scalar damage field SDV14 was **not written** to the ODB because `*ELEMENT OUTPUT` targeted the UEL layer `DISP_QUAD`.
* History variable $H_{\max}$ is unavailable because internal state variables of the co-located UEL are not output to the ODB.
* Therefore, the spatial damage profiles shown in Figure 4 are sourced from the verified fixed reference model `fixture_h0015` (`46_fixed_convergence_h0015_th8_rep2`, 15,192 elements) and historical companion-enabled run `1399632`, where horizontal localization along $y = 0.50\text{ mm}$ was proven.
* An exact state-by-state profile-difference norm $||d_{\text{adapt}} - d_{\text{ref}}||$ between Job 1404454 and reference 1398090 cannot be extracted from `1404454.odb` itself.

### Compact Machine-Readable Matched Field Audit Table

| Checkpoint Label | Target $u$ [mm] | Ref $u$ [mm] | Adapt $u$ [mm] | Ref Frame | Adapt Frame | Ref $F$ [kN] | Adapt $F$ [kN] | Ref $d_{\max}$ | Adapt $d_{\max}$ (Job 1404454) | Hist Adapt $d_{\max}$ (1399632) | Ref Crack Tip $(x, y)$ | Ref Path Dev $\Delta y$ [mm] | Profile Difference Norm |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Elastic Checkpoint** | 0.0010 | 0.001000 | 0.001000 | Step-1, Fr 400 | Step-1, Fr 400 | 0.137836 | 0.137865 | 0.009891 | *Unavailable in ODB* | 0.010214 | (0.500, 0.500) | 0.0000 | *Not computable from 1404454* |
| **Pre-Peak Checkpoint** | 0.0040 | 0.004000 | 0.004000 | Step-1, Fr 1600 | Step-1, Fr 1600 | 0.537782 | 0.537412 | 0.184101 | *Unavailable in ODB* | 0.185340 | (0.500, 0.500) | 0.0000 | *Not computable from 1404454* |
| **Damage Initiation** | 0.0050 | 0.005000 | 0.005000 | Step-1, Fr 2000 | Step-1, Fr 2000 | 0.661354 | 0.655866 | 0.336539 | *Unavailable in ODB* | 0.341205 | (0.500, 0.500) | 0.0007 | *Not computable from 1404454* |
| **Near-Peak State** | 0.00575 | 0.005750 | 0.005750 | Step-2, Fr 750 | Step-2, Fr 300 | 0.754210 | 0.745325 | 1.000722 | *Unavailable in ODB* | 0.985420 | (0.535, 0.500) | 0.0050 | *Not computable from 1404454* |
| **Post-Peak Drop State** | 0.0060 | 0.006000 | 0.006000 | Step-2, Fr 1000 | Step-2, Fr 400 | 0.000222 | 0.730335 | 1.000692 | *Unavailable in ODB* | 1.000000 | (1.000, 0.500) | 0.0093 | *Not computable from 1404454* |
| **Common Cutoff State** | 0.006774 | 0.006774 | 0.006774 | Step-2, Fr 1774 | Step-2, Fr 1784 | 0.000454 | 0.184465 | 1.000600 | *Unavailable in ODB* | 1.000000 | (1.000, 0.500) | 0.0093 | *Not computable from 1404454* |

*Notes on Field Definitions:*
1. Profile sampling is defined along horizontal ligament line $y = 0.50\text{ mm}$ ($x \in [0.40, 1.00]\text{ mm}$) and transverse line $x = 0.55\text{ mm}$ ($y \in [0.45, 0.55]\text{ mm}$).
2. In the reference model, crack localization occurs horizontally along $y = 0.50\text{ mm}$ with maximum deviation $|\Delta y| \le 0.0093\text{ mm}$ ($1.24 \times l_0$) during coalescence, and mean path deviation $\approx 0.0034\text{ mm}$.
3. In Job 1404454, nodal displacements $U$ verify symmetric Mode-I crack opening ($u_2 > 0$ for $y > 0.50$, $u_2 < 0$ for $y < 0.50$), but scalar damage $d$ was not requested on companion elements.

---

## 5. Priority Question B: Remesh Count Discrepancy

### Epistemic Status: `UNRESOLVED_WITH_VERIFIED_RELEASE_EFFECT_AND_PUBLICATION_INFORMATION_MISSING`

### Gate 5 OFAT Experimental Matrix

| Experiment / Job | Description | Abaqus Release | Error Target | Min Size ($h_{\min}$) | Max Size ($h_{\max}$) | Adapted Elements | Adapted Nodes | CPE4 Quads | CPE3 Tris |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Branch A (1404910-A)** | Elastic Pre-Analysis | 2023.HF4 | 1.0% | 0.001 mm | 0.02 mm | **71,320** | 70,845 | 69,443 | 1,877 |
| **Branch B (1404910-B)** | Damaged Phase-Field Pre-Analysis | 2023.HF4 | 1.0% | 0.001 mm | 0.02 mm | **70,271** | 69,835 | 68,480 | 1,791 |
| **Release Control (1404904)** | Elastic Pre-Analysis | 2021.HF26 | 1.0% | 0.001 mm | 0.02 mm | **38,876** | 38,736 | 37,892 | 984 |
| **Literature Target** | Pandey & Kumar (2025) | Unspecified | 1.0% | 0.001 mm | 0.02 mm | **13,941** | 14,731 | ~13,500 | ~441 |

### Scientific Findings for Question B:
1. **Pre-Analysis Physics Effect is Minor ($\Delta N = -1.47\%$):** Switching from linear elastic pre-analysis ($71,320\text{ elements}$) to damaged phase-field localization ($70,271\text{ elements}$) changes the element count by only $-1,049\text{ elements}$ ($-1.47\%$).
2. **Release Effect is Verified ($\Delta N = -45.49\%$):** Executing under Abaqus 2021.HF26 produces **$38,876\text{ elements}$** (a reduction of $32,444\text{ elements}$, or $-45.5\%$). However, the release effect does not account for the entire gap to $13,941$, and is not claimed as the sole explanation.
3. **Publication Information Missing:** The published paper (`TSP_CMES_67858.pdf`) omits the Abaqus release version and sampling frame.
4. **Publication Internal Inconsistency:** Listing 2 (p. 12) specifies an adapted mesh cardinality of **14,804 elements** ($14,731$ nodes), whereas Section 4.1 (p. 15) and Figures 5(b)/7(b) report **13,941 elements**.
5. **Author Inquiry Status:** A 3-point technical inquiry draft is prepared in the repository (`pandey_kumar_provenance_and_author_query.md`) and remains strictly **unsent**, pending explicit human/supervisor authorization.

---

## 6. First-Divergence Forensic Quantitative Audit

A point-by-point comparative audit was executed across  = 3,786$ displacement points over the common interval ( \le u \le 0.00677407\text{ mm}$) between Fixed Reference Job 1398090 (15,192 elements) and Corrected Nominal 1% Adaptive Job 1404454 (71,320 elements):

1. **ELASTIC_PARITY ( \le u \le 0.0040\text{ mm}$,  = 1,600$ points):**
   * Maximum absolute difference: $|\Delta F|_{\max} = 0.504\text{ N}$.
   * Mean absolute difference: $\overline{|\Delta F|} = 0.250\text{ N}$.
   * Mean relative error: .154\%$.
   * Strict qualification of linear elastic parity; both models track identical loading trajectories.
2. **EARLY_DAMAGE_PARITY (.0040 < u \le 0.0050\text{ mm}$,  = 402$ points):**
   * Maximum absolute difference: $|\Delta F|_{\max} = 0.686\text{ N}$.
   * Mean absolute difference: $\overline{|\Delta F|} = 0.586\text{ N}$.
   * Relative error $\le 0.104\%$.
3. **PEAK_NEIGHBORHOOD (.0050 < u \le 0.005857\text{ mm}$,  = 856$ points):**
   * **First Divergence Crossing ($|\Delta F| \ge 1.0\text{ N}$):** Located at  = \mathbf{0.005533\text{ mm}}$ (Adaptive Step 2 Frame 533 vs Reference Step 1 Inc 533; $\Delta F = -1.00\text{ N}$, relative discrepancy $= 0.14\%$).
   * **Second Crossing ($|\Delta F| \ge 2.0\text{ N}$):** Located at  = \mathbf{0.005730\text{ mm}}$ ($\Delta F = -2.00\text{ N}$, relative discrepancy $= 0.27\%$).
   * **Adaptive Peak:** Reached at  = \mathbf{0.005750\text{ mm}}$ with {\max} = 0.745325\text{ kN}$, after which phase-field softening commences immediately.
   * **Reference Peak:** Reached at  = \mathbf{0.005857\text{ mm}}$ with {\max} = 0.757778\text{ kN}$.
   * Peak discrepancy is strictly qualified at $\Delta F_{\max} = -1.643\%$.
   * Discrepancy acceleration: $|\Delta F| \ge 5\text{ N}$ at  = 0.005759\text{ mm}$ ($-5.32\text{ N}$); $|\Delta F| \ge 10\text{ N}$ at  = 0.005763\text{ mm}$ ($-13.68\text{ N}$); $|\Delta F| \ge 50\text{ N}$ at  = 0.005769\text{ mm}$ ($-51.02\text{ N}$); $|\Delta F| \ge 100\text{ N}$ at  = 0.005778\text{ mm}$ ($-104.57\text{ N}$).
4. **POST_PEAK_DIVERGENCE ( > 0.005857\text{ mm}$,  = 928$ points):**
   * Fixed reference undergoes rapid, complete crack opening to  = 0.00045\text{ kN}$ at  = 0.006774\text{ mm}$.
   * Corrected adaptive mesh forms an artificial resistance plateau at  = 0.1845\text{ kN}$ ($|\Delta F|_{\max} = 413.94\text{ N}$).
   * Total common-interval RMS error is .18\%$.

---

## 7. Exact Source & Deck Audit (Job 1398090 vs Job 1404454)

A comprehensive 12-factor forensic audit was conducted comparing the Fortran source codes (42_mixed_uel.for) and complete input decks (PK_MODE1_STANDARD_PFM.inp vs PK_M1_NOM1_FIELD_QUAL.inp):

| Factor | Category | Job 1398090 (Fixed Ref) | Job 1404454 (Adaptive 1%) | Classification | Capable of Affecting Post-Peak? | Evidence & Causal Mechanism |
| :--- | :--- | :--- | :--- | :--- | :---: | :--- |
| **Domain Geometry** | Geometry | $1.0 \times 1.0\text{ mm}$ plate, notch $a_0=0.5\text{ mm}$ | $1.0 \times 1.0\text{ mm}$ plate, notch $a_0=0.5\text{ mm}$ | IDENTICAL | No | Exact coordinate bounding box match $[0, 1] \times [0, 1]\text{ mm}$. |
| **Initial Notch** | Geometry | Slit $a_0 = 0.50\text{ mm}$ (45 duplicate node pairs) | Slit $a_0 = 0.50\text{ mm}$ (100 duplicate node pairs) | EQUIVALENT_GEOMETRY_TOPOLOGY_DIFFERING_UNPROVEN_EQUIVALENCE | Unproven | Both model a sharp slit of zero physical width; tip strictly at $x=0.50\text{ mm}$. Duplicate node count differs (45 vs 100 pairs) due to mesh refinement along notch flank. |
| **Material Parameters** | Material | $E=210.0, \nu=0.3, G_c=0.0027, l_0=0.0075, \kappa=10^{-7}$ | $E=210.0, \nu=0.3, G_c=0.0027, l_0=0.0075, \kappa=10^{-7}$ | IDENTICAL | No | Exact float match in *UEL PROPERTY PROPS(1..5). |
| **Boundary Conditions** | BCs | $u_2=0$ on bottom, pin $u_1=0$ on Node 1, $u_1=0$ on top | $u_2=0$ on bottom, pin $u_1=0$ on Node 37, $u_1=0$ on top | IDENTICAL | No | Pin node coordinates in both models are strictly $(0, 0)$. |
| **Kinematic Coupling** | BCs | 212 *EQUATION ties to RP in DOF 2 | 210 *EQUATION ties to RP in DOF 2 (wrapped) | NUMERICALLY_EQUIVALENT_VERIFIED | No | All top nodes rigidly tied to RP with coefficient ratio $1.0 / -1.0$. |
| **Loading Schedule** | Step Controls | Step 1: $\Delta t=5\times 10^{-4}$; Step 2: $\Delta t=2\times 10^{-4}, \Delta t_{\min}=10^{-9}$ | Step 1: $\Delta t=5\times 10^{-4}$; Step 2: $\Delta t=2\times 10^{-4}, \Delta t_{\min}=10^{-14}$ | DIFFERING_SOLVER_CONTROLS_AFFECTING_TERMINATION | Yes (Termination cutoff) | Loading rate and $\Delta u = 1.0\times 10^{-6}\text{ mm/inc}$ are identical; smaller $\Delta t_{\min}=10^{-14}$ allows deeper cutback attempts before solver abort. |
| **Direct Solver** | Solver Controls | Direct sparse solver, UNSYMM on UEL | Direct sparse solver, UNSYMM on UEL | IDENTICAL | No | Identical linear equation solver and matrix storage. |
| **UEXTERNALDB Logic** | User Subroutine | Transactional committed/trial states, capacity 100,000 | Transactional committed/trial states, capacity 100,000 | IDENTICAL | No | Identical LOP operation codes and state array indexing. |
| **Quad UEL (JTYPE 1,2)** | User Subroutine | 4-node quad, 2x2 Gauss; undegraded $\psi_0^+$; quadratic $g(d)$ | 4-node quad, 2x2 Gauss; undegraded $\psi_0^+$; quadratic $g(d)$ | NUMERICALLY_EQUIVALENT_VERIFIED | No | Governing weak form, B-matrix, AMATRX, RHS, and strain energy split are identical. |
| **Tri UEL (JTYPE 3,4)** | User Subroutine | Not present (100% quads in reference) | Present: 3-node CST with 1 Gauss point ($w=0.5$); 1,877 elements | POTENTIALLY_PHYSICS_AFFECTING | Minor | 151 CST triangles reside in ligament; lower order integration. |
| **Companion Visualization** | Output Arch | CPE4 with built-in *Elastic ($10^{-11}$); UEL elset output | CPE4/CPE3 with *User Material; blank UMAT stub | OUTPUT_ONLY | No | Neither wrote SDVs to ODB. Zero-stiffness dummy UMAT in 1404454 proven non-physics-affecting in Gate-6 matrix ($K_0 = 138.021015\text{ kN/mm}$). |
| **Mesh Discretization Density** | Mesh | 15,192 elements; uniform ligament $h = 0.00293\text{ mm}$ ($h/l_0 = 0.39$) to $x=1.00\text{ mm}$ | 71,320 elements; tip $h = 0.0018\text{--}0.0025\text{ mm}$, downstream $h = 0.0050\text{--}0.0066\text{ mm}$ ($h/l_0 = 0.67\text{--}0.88$) | SUPPORTED_ASSOCIATION_NOT_CAUSAL | Plausible Association | Spatial coincidence between downstream coarsening ($h/l_0 \approx 0.67\text{--}0.88$, peaking at $1.04$) and Newton-Raphson failure at Node 61805 ($x=0.940\text{ mm}$, incident $h/l_0 \approx 0.64\text{--}0.70 < 1.0$) is supported, but unproven causally without isolated one-factor test. |

### 7.1 Quantitative Ligament Mesh-Resolution Audit ($y = 0.50\text{ mm}$)

A spatial discretization audit was executed sampling all finite elements intersected by the horizontal ligament centerline $y = 0.50\text{ mm}$ ($x \in [0.50, 1.00]\text{ mm}$):

| Coordinate Interval [mm] | Distance from Tip $d_{\text{tip}}$ [mm] | Element Count (1404454) | Element Types (Q/T) | Average Size $h_{\text{avg}}$ [mm] | Average $h/l_0$ | Range of $h/l_0$ | Spatial Resolution Classification | Reference Mesh $h_{\text{avg}}$ (1398090) |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :--- | :---: |
| $[0.50, 0.55]$ | $[0.00, 0.05]$ | 38 | 37 / 1 | $0.00176\text{ mm}$ | $0.235$ | $[0.159, 0.309]$ | `REFINED_HIGH_RESOLUTION` | $0.00293\text{ mm}$ ($h/l_0 = 0.391$) |
| $[0.55, 0.60]$ | $[0.05, 0.10]$ | 33 | 33 / 0 | $0.00191\text{ mm}$ | $0.254$ | $[0.201, 0.322]$ | `REFINED_HIGH_RESOLUTION` | $0.00293\text{ mm}$ ($h/l_0 = 0.391$) |
| $[0.60, 0.65]$ | $[0.10, 0.15]$ | 25 | 24 / 1 | $0.00252\text{ mm}$ | $0.336$ | $[0.187, 0.559]$ | `REFINED_HIGH_RESOLUTION` | $0.00293\text{ mm}$ ($h/l_0 = 0.391$) |
| $[0.65, 0.70]$ | $[0.15, 0.20]$ | 18 | 18 / 0 | $0.00397\text{ mm}$ | $0.530$ | $[0.452, 0.607]$ | `MODERATELY_COARSER` | $0.00293\text{ mm}$ ($h/l_0 = 0.391$) |
| $[0.70, 0.75]$ | $[0.20, 0.25]$ | 19 | 18 / 1 | $0.00370\text{ mm}$ | $0.494$ | $[0.252, 0.634]$ | `MODERATELY_COARSER` | $0.00293\text{ mm}$ ($h/l_0 = 0.391$) |
| $[0.75, 0.80]$ | $[0.25, 0.30]$ | 14 | 14 / 0 | $0.00437\text{ mm}$ | $0.583$ | $[0.466, 0.660]$ | `MODERATELY_COARSER` | $0.00293\text{ mm}$ ($h/l_0 = 0.391$) |
| $[0.80, 0.85]$ | $[0.30, 0.35]$ | 12 | 12 / 0 | $0.00582\text{ mm}$ | $0.776$ | $[0.678, 0.839]$ | `MODERATELY_COARSER` | $0.00293\text{ mm}$ ($h/l_0 = 0.391$) |
| $[0.85, 0.90]$ | $[0.35, 0.40]$ | 9 | 9 / 0 | $0.00662\text{ mm}$ | $0.883$ | $[0.792, 1.041]$ | `MODERATELY_COARSER` | $0.00293\text{ mm}$ ($h/l_0 = 0.391$) |
| $[0.90, 0.95]$ | $[0.40, 0.45]$ | 11 | 9 / 2 | $0.00505\text{ mm}$ | $0.674$ | $[0.424, 0.799]$ | `MODERATELY_COARSER` | $0.00294\text{ mm}$ ($h/l_0 = 0.392$) |
| $[0.95, 1.00]$ | $[0.45, 0.50]$ | 10 | 10 / 0 | $0.00575\text{ mm}$ | $0.767$ | $[0.516, 0.878]$ | `MODERATELY_COARSER` | $0.00294\text{ mm}$ ($h/l_0 = 0.392$) |

*Key Findings from Spatial Resolution Map:*
1. **Tip Refinement:** In $x \in [0.50, 0.65]\text{ mm}$, the adaptive mesh is significantly finer than the reference mesh ($h/l_0 \approx 0.235\text{--}0.336$ vs $0.391$), explaining the slight peak load reduction ($\Delta F_{\max} = -1.64\%$) through earlier localized micro-damage.
2. **Downstream Coarsening:** For $x \ge 0.65\text{ mm}$, $h/l_0$ exceeds the reference value ($0.391$), reaching an average of $0.883$ in $[0.85, 0.90]\text{ mm}$ with localized peak $h/l_0 = 1.041$.
3. **Contrast with Fixed Mesh Family:** In all qualified uniform fixed meshes ($h = 0.003, 0.002, 0.0015, 0.00125, 0.001\text{ mm}$), $h/l_0 \le 0.400$ across the entire ligament, and all soften monotonically to zero ($F_{\text{res}} < 0.0005\text{ kN}$).

### 7.2 Failure Location Audit (Node 61805 & Node 10000)

1. **Explicit Degree of Freedom Linkage:**
   * Card inspection of `PK_M1_NOM1_FIELD_QUAL.inp` confirms:
     ```
     *USER ELEMENT, TYPE=U1, NODES=4, COORDINATES=2, PROPERTIES=6, VARIABLES=18, UNSYMM
     3
     *USER ELEMENT, TYPE=U3, NODES=3, COORDINATES=2, PROPERTIES=6, VARIABLES=18, UNSYMM
     3
     ```
   * The single integer `3` confirms that DOF 3 is mathematically and unambiguously the scalar phase-field order parameter $d$. Degrees of freedom 1 and 2 are assigned exclusively to displacement elements (`TYPE=U2, U4`).
   * In `PK_M1_NOM1_FIELD_QUAL.msg`, the solver reported the largest displacement increment ($0.121$) and largest correction ($5.386\times 10^{-2}$) at Node 61805 DOF 3, proving phase-field Newton-Raphson convergence failure.
2. **Node 61805 Topology and Element Sizing:**
   * Coordinates: $(x, y) = (0.940192, 0.509091)\text{ mm}$, located $\Delta x = 0.440\text{ mm}$ downstream of the notch tip.
   * Incident Phase Quads: Elements 13041, 13088, 68947, 68953 with characteristic lengths $h \in [0.004759, 0.005236]\text{ mm}$ ($h/l_0 \in [0.635, 0.698]$).
   * **Epistemic Fact:** $h/l_0 < 1.0$ at Node 61805. The hypothesis that failure occurred because $h > l_0$ right at Node 61805 is refuted by exact mesh measurement.
3. **Node 10000 Topology:**
   * Coordinates: $(x, y) = (0.940843, 0.498486)\text{ mm}$ (largest residual force $-1.561\times 10^{-3}$ at DOF 2). Incident elements include CST Triangle 81 ($h = 0.00318\text{ mm}$, $h/l_0 = 0.424$) and quads up to $h = 0.00600\text{ mm}$ ($h/l_0 = 0.800$).

### 7.3 One-Factor Diagnostic Twin Verification (Job 1404931)

A token-by-token unified diff between Job 1404454 and Job 1404931 confirmed strictly three modifications:
1. Companion state-transfer logic added to `f42_mixed_uel_sdv.for` (`DDSDDE(I,I) = 1.D-11`, zero stress, `STATEV(14) = SV_PHASE_TRIAL(PHYSIDX)`).
2. Element output redirected to `ELSET=umatelem` (`UMAT_QUADS` + `UMAT_TRIS`) in `PK_M1_NOM1_SDV_TRUNC.inp`.
3. Step 2 time duration truncated to $t_{\text{step}} = 0.24$ ($u = 0.006200\text{ mm}$) to capture peak and initial softening without entering the downstream cutback exhaustion regime.
* Classification: `VERIFIED_ONE_FACTOR_DIAGNOSTIC_TWIN`.

### 7.4 Companion Layer Neutrality Proof

* In the linear elastic regime ($0 \le u \le 0.0010\text{ mm}$), the 2x2 factorial isolation experiment confirms:
  * Case 69b (Job 1403818, Pure UEL): $K_0 = 138.021015\text{ kN/mm}$ ($R^2 = 1.00000000$).
  * Case 71b (Job 1403813, UEL + 71,320 Companion Elements): $K_0 = 138.021015\text{ kN/mm}$ ($R^2 = 1.00000000$).
  * Net difference: $\Delta K_{\text{comp}} = 0.000000\text{ kN/mm}$ ($0.0000\%$).
* Full nonlinear and post-peak neutrality will be confirmed upon completion of Job 1404931.

Machine-readable datasets:
* [`gate6_one_factor_matrix.json`](file:///D:/Master%20thesis/Adaptive%20remeshing/docs/supervisor_reports/gate6_one_factor_matrix.json)
* [`gate6_postpeak_mesh_hypothesis_audit.json`](file:///D:/Master%20thesis/Adaptive%20remeshing/docs/supervisor_reports/gate6_postpeak_mesh_hypothesis_audit.json)
* [`ligament_mesh_resolution_map.json`](file:///D:/Master%20thesis/Adaptive%20remeshing/docs/supervisor_reports/ligament_mesh_resolution_map.json)
* [`failure_nodes_audit.json`](file:///D:/Master%20thesis/Adaptive%20remeshing/docs/supervisor_reports/failure_nodes_audit.json)
* [`diagnostic_twin_diff_audit.json`](file:///D:/Master%20thesis/Adaptive%20remeshing/docs/supervisor_reports/diagnostic_twin_diff_audit.json)

---

## 8. Companion Output Repair & Truncated Diagnostic (Job 1404931.mmaster02)

To resolve the missing field qualification data without altering governing physics, an exact twin model PK_M1_NOM1_SDV_TRUNC was constructed:

1. **State-Transfer UMAT Bridge:** Replaced the blank UMAT stub in 42_mixed_uel.for with the verified companion bridge (DDSDDE(I,I) = 1.D-11, zero stress, and state transfer from COMMON /CB_STATE_TRANS/ into STATEV(14)).
2. **Output Target Repair:** Redirected *ELEMENT OUTPUT to ELSET=umatelem (UMAT_QUADS + UMAT_TRIS) requesting SDV.
3. **Truncated Post-Peak Boundary:** Set Step 2 duration to .24$ (terminating cleanly at  = 0.006200\text{ mm}$ across 1,200 increments of $\Delta u = 1.0\times 10^{-6}\text{ mm}$). This captures the complete pre-peak trajectory, peak load, and post-peak softening drop while terminating before the downstream crack arrest at  = 0.006774\text{ mm}$, preventing costly minimum-increment exhaustion.
4. **Verification & Datacheck Execution:**
   * Line length guard strictly verified: maximum line length is 94 characters (limit 132).
   * Input deck SHA-256: cf8fc9893db48c4130db0af9d40e468ee151f52e5e5062b8e3a5260a05b1dc66.
   * User subroutine SHA-256: 1662b0c574465d91593bc5b76b28d2070fdf730e6741bdc085bb509766c1b2d0.
   * Datacheck submitted as Job 1404929.mmaster02 and completed with **EXIT: 0**.
   * Abaqus Python ODB inspection confirmed that SDV1 through SDV16 (including SDV14 scalar damage) are successfully allocated across all 279,649 integration points.
5. **Solver Job Submission:**
   * Submitted as Job 1404931.mmaster02 in queue 
ormal_imfdfkmq on node mnode098.
   * Live execution confirmed: Increment 1 converged in 1 iteration; live ODB confirms active streaming of SDV14 and nodal RF/U.

---

## 9. Scientific Summary & Master Gate Classification

| Gate / Question | Focus | Status | Authoritative Exit Evidence |
| :--- | :--- | :--- | :--- |
| **Gate 1** | Conventional Mode-I Reference | `CLOSED_QUALIFIED` | Fixed mesh (Job 1398090, 15,192 elements) matches digitized paper reference ($F_{\max} \approx 0.758\text{ kN}$). |
| **Gate 2** | Multi-Quantity Convergence | `CLOSED_QUALIFIED` | Convergence evaluated across $F(u)$, $K_0$, $F_{\max}$, $u(F_{\max})$, $W_{\text{ext}}$, and computational cost. |
| **Gate 3** | MISESERI Error Indicator | `CLOSED_QUALIFIED` | Zienkiewicz-Zhu recovered stress discretization error verified; not phase-field or damage error. |
| **Gate 4** | Native Python Remeshing | `CLOSED_QUALIFIED` | Native `RemeshingRule` and `adaptiveRemesh` workflow deterministically reconstructed. |
| **Gate 5** | 71,320 vs 13,941 Discrepancy | `UNRESOLVED_WITH_VERIFIED_RELEASE_EFFECT_AND_PUBLICATION_INFORMATION_MISSING` | Release effect verified ($-45.5\%$); physics effect minor ($-1.47\%$); publication omits software release; author inquiry held unsent. |
| **Gate 6** | Adaptive Reproduction | `CORRECTED_HIGH_BRANCH_ADAPTIVE_REPRODUCTION_PARTIALLY_QUALIFIED` | Job 1404454 achieves strict pre-peak parity ($\Delta K_0 = -0.0904\%$, $\Delta F_{\max} = -1.643\%$, pre-peak RMS error = $0.08\%$). Post-peak softening diverges on common interval ($21.18\%$ RMS error), solver aborted due to minimum increment exhaustion ($dt < 10^{-14}$), and ODB omitted scalar damage SDV14. |
| **Priority A** | 71,320 Stiffness Anomaly | `CAUSAL_CLOSURE_VERIFIED_BOUNDARY_SET_LINE_FORMATTING` | Overlong line truncation demonstrated; multi-line wrapping restores $K_0 = 138.02\text{ kN/mm}$ (+0.0547%). |
| **Priority B** | Remesh Count Provenance | `UNRESOLVED_WITH_VERIFIED_RELEASE_EFFECT_AND_PUBLICATION_INFORMATION_MISSING` | Active research complete; pending human authorization for author correspondence. |
