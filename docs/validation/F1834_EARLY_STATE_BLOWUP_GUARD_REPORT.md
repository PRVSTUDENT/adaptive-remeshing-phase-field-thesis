# Task F1834: Quantitative Diagnosis of Early-State Eta Blowup and Evaluation of the Shared Load-Threshold Guard

**Task Identifier:** `F1834-EARLY-STATE-BLOWUP-GUARD`  
**Correlation ID:** `HND-F1834-EARLY-STATE-BLOWUP-GUARD-001`  
**Protocol:** `INDEPENDENT_STRUCTURED_REVIEW_V1`  
**Date:** 17 November 2026  
**Agent:** Gemini Antigravity  
**Predecessor Task:** `F1833-STATE-CONSISTENT-NORMALIZATION` (`decision: APPROVE`)  
**Master Goal Status:** `OPEN`  
**Research Priority Lock:** Reusable Adaptive Remeshing Framework (Method A) Only across Cases 1, 2, 3, and 5.

---

## 1. Executive Summary & Review Directive Mandate

In Task F1833, state-consistent normalization:
$$\eta_{e,k} = \frac{\text{MISESERI}_{e,k}}{\text{MISESAVG}_k}, \quad \eta_{e,\text{env}} = \max_k \eta_{e,k}$$
was introduced into `MultiStateRecoveryDonorBuilder.synthesize_envelope_odb` in [scripts/remeshing/reusable_2d_adaptive_framework.py](file:///D:/Master%20thesis/Adaptive%20remeshing/scripts/remeshing/reusable_2d_adaptive_framework.py).

While this produced a dramatic efficiency breakthrough in **Case 1** (-63.73% elements, from 25,461 down to 9,234 elements, passing Gate 06 with 2.455x far-field coarsening), it led to severe element explosions in **Case 2** (+182.79%, 117,181 elements, Gate 06 FAIL at 1.407x, Gate 07 FAIL) and **Case 3** (+67.42%, 130,218 elements, Gate 06 FAIL at 1.483x, Gate 07 FAIL).

The review directive for Task F1834 mandated:
1. **Quantitative Diagnosis**: Determine per case and per donor state the global domain mean stress $\text{MISESAVG}_k$ relative to peak $\text{MISESAVG}_{\text{peak}}$, and the exact number/fraction of elements whose envelope maximum $\eta_{e,\text{env}}$ is dominated by each state.
2. **Single Shared-Framework Guard**: In `synthesize_envelope_odb`, implement a universal load-threshold guard that excludes any donor state whose global domain mean stress falls below a fixed fraction $\theta$ of the peak-state domain mean stress:
   $$\text{MISESAVG}_k < \theta \cdot \max_m \text{MISESAVG}_m \implies \text{state } k \text{ excluded from envelope}$$
   The guard must be a property of the loading state, with zero per-case forks and zero manually seeded corridors.
3. **Multi-Threshold Parameter Sweep**: Test fractions $\theta \in \{0.10, 0.25, 0.50, 0.80\}$ across all four benchmark cases (Case 1 $\eta_R=4.5\%$, Case 2 $\eta_R=4.0\%$, Case 3 $\eta_R=3.0\%$, Case 5 $\eta_R=5.68\%$) from the revised framework revision.
4. **Honest Reporting & Adoption Criterion**: Evaluate all tested thresholds against F1812 and F1833 baselines. Report all tested fractions honestly, including any that make things worse. If no threshold fraction achieves the goal, report that honestly and do NOT adopt the guard.

---

## 2. Quantitative Early-State & Late-State Diagnosis

Using [scripts/remeshing/diagnose_f1834_early_states.py](file:///D:/Master%20thesis/Adaptive%20remeshing/scripts/remeshing/diagnose_f1834_early_states.py) and spatial breakdown analyzer [scripts/remeshing/spatial_breakdown_f1834.py](file:///D:/Master%20thesis/Adaptive%20remeshing/scripts/remeshing/spatial_breakdown_f1834.py), each donor state was analyzed in its authentic linear recovery step:

### Case 1: Mode-I Edge-Cracked Plate (5 States)
- **State 0 (Initiation)**: $\overline{\text{MISESAVG}} = 981.2\text{ MPa}$ (100.0% of peak). Dominates 581 elements (20.0%).
- **State 1 (Early Prop)**: $\overline{\text{MISESAVG}} = 857.6\text{ MPa}$ (87.4% of peak). Dominates 272 elements (9.4%).
- **State 2 (Mid Prop)**: $\overline{\text{MISESAVG}} = 707.7\text{ MPa}$ (72.1% of peak). Dominates 481 elements (16.6%).
- **State 3 (Outer Prop)**: $\overline{\text{MISESAVG}} = 457.0\text{ MPa}$ (46.6% of peak). Dominates 597 elements (20.5%).
- **State 4 (Terminal Severance)**: $\overline{\text{MISESAVG}} = 149.9\text{ MPa}$ (**15.3% of peak**). Dominates **975 elements (33.6%)**, with $\max \eta = 977,462\%$!
*Diagnosis*: State 4 represents the post-peak severed state where the ligament has fully cleaved. Because the specimen carries almost no load (15.3%), dividing recovered stress error by 149.9 MPa inflated relative error to extreme levels, dominating 33.6% of all elements.

### Case 2: Plate with Off-Axis Hole (4 States)
- **State 0 (Preanalysis)**: $\overline{\text{MISESAVG}} = 554.1\text{ MPa}$ (100.0% of peak). Dominates 664 elements (22.8%).
- **State 1 (Hole Arrest)**: $\overline{\text{MISESAVG}} = 502.9\text{ MPa}$ (90.8% of peak). Dominates 729 elements (25.1%).
- **State 2 (Distal Nucleation)**: $\overline{\text{MISESAVG}} = 400.4\text{ MPa}$ (72.3% of peak). Dominates 342 elements (11.8%).
- **State 3 (Outer Propagation)**: $\overline{\text{MISESAVG}} = 250.2\text{ MPa}$ (**45.1% of peak**). Dominates **1,171 elements (40.3%)**!
*Crucial Spatial Breakthrough*: Of the 1,171 elements dominated by State 3 in Case 2, **1,007 elements are located in the FAR FIELD** ($x < 0.70$ or $y < 0.40$ or $y > 0.80$)! Because load dropped from 554.1 MPa to 250.2 MPa, dividing recovered stress error by 250.2 MPa instead of the peak stress inflated far-field relative error $\eta$ by +70.6% across the entire plate. This single mechanism was the direct cause of the 117,181 element explosion!

### Case 3: Notched Plate with Pins (3 States)
- **State 0 (Initiation)**: $\overline{\text{MISESAVG}} = 0.0911\text{ MPa}$ (100.0% of peak). Dominates 1,782 elements (45.4%, 1,598 in far field).
- **State 1 (Hole Arrest)**: $\overline{\text{MISESAVG}} = 0.0684\text{ MPa}$ (75.1% of peak). Dominates 1,267 elements (32.3%, 1,034 in far field).
- **State 2 (Secondary Prop)**: $\overline{\text{MISESAVG}} = 0.0750\text{ MPa}$ (82.3% of peak). Dominates 874 elements (22.3%).
*Diagnosis*: In Case 3, all three states operate at comparable domain mean stress levels (all $>75\%$ of peak). Because the specimen is loaded under asymmetric pin-driven bending, bending stresses extend throughout the entire domain. Hence, normalizing by the small local state stress rather than the cross-state peak produces far-field refinement across all states.

---

## 3. Parameter Sweep Results Across Tested Thresholds

The complete automated parameter sweep was executed across all four benchmark cases under $\theta \in \{0.10, 0.25, 0.50, 0.80\}$ via [scripts/remeshing/run_f1834_threshold_sweep.py](file:///D:/Master%20thesis/Adaptive%20remeshing/scripts/remeshing/run_f1834_threshold_sweep.py). The results are summarized below:

| Threshold $\theta$ | Metric / Case | Case 1 ($\eta_R=4.5\%$) | Case 2 ($\eta_R=4.0\%$) | Case 3 ($\eta_R=3.0\%$) | Case 5 ($\eta_R=5.68\%$) |
|---|---|---|---|---|---|
| **$\theta = 0.10$** (10%) | Elements | 9,234 (-63.7%) | 117,181 (+182.8%) | 130,218 (+67.4%) | 15,466 (0.0%) |
| | Quad Fraction | 97.14% | 97.58% | 97.38% | 97.90% |
| | Gate 06 Coarsening | **2.455x (PASS)** | 1.407x (FAIL) | 1.483x (FAIL) | **2.117x (PASS)** |
| | Gate 07 Budget | **PASS** | FAIL | FAIL | **PASS** |
| | Scientific Gate | FAIL (96.5% <= l0) | **PASS (100.0%)** | **PASS (99.0%)** | **PASS (99.0%)** |
| **$\theta = 0.25$** (25%) | Elements | **122,532 (+381.3%)** | 117,181 (+182.8%) | 130,218 (+67.4%) | 15,466 (0.0%) |
| | Quad Fraction | 97.56% | 97.58% | 97.38% | 97.90% |
| | Gate 06 Coarsening | 1.338x (FAIL) | 1.407x (FAIL) | 1.483x (FAIL) | **2.117x (PASS)** |
| | Gate 07 Budget | FAIL | FAIL | FAIL | **PASS** |
| | Scientific Gate | **PASS (100.0%)** | **PASS (100.0%)** | **PASS (99.0%)** | **PASS (99.0%)** |
| **$\theta = 0.50$** (50%) | Elements | **84,475 (+231.8%)** | **127,193 (+206.9%)** | 130,218 (+67.4%) | 15,466 (0.0%) |
| | Quad Fraction | 97.43% | 97.52% | 97.38% | 97.90% |
| | Gate 06 Coarsening | 1.521x (FAIL) | 1.419x (FAIL) | 1.483x (FAIL) | **2.117x (PASS)** |
| | Gate 07 Budget | FAIL | FAIL | FAIL | **PASS** |
| | Scientific Gate | **PASS (100.0%)** | **PASS (100.0%)** | **PASS (99.0%)** | **PASS (99.0%)** |
| **$\theta = 0.80$** (80%) | Elements | 17,713 (-30.4%) | 102,987 (+148.5%) | 116,648 (+50.0%) | 15,466 (0.0%) |
| | Quad Fraction | 97.02% | 97.48% | 97.31% | 97.90% |
| | Gate 06 Coarsening | **2.340x (PASS)** | 1.535x (FAIL) | 1.584x (FAIL) | **2.117x (PASS)** |
| | Gate 07 Budget | **PASS** | FAIL | FAIL | **PASS** |
| | Scientific Gate | FAIL (70.1% lig) | **PASS (100.0%)** | **PASS (98.9%)** | **PASS (99.0%)** |

---

## 4. Scientific Discovery & Root-Cause Analysis

### Discovery 1: Why Excluding States Catastrophically Exploded Case 1 at $\theta = 0.25$
In `synthesize_envelope_odb`, the envelope fields written to the donor ODB are:
$$\text{MISESERI}_{e,\text{env}} = \eta_{e,\max} \cdot \overline{\text{MISESAVG}}_{\text{inc}}$$
$$\text{MISESAVG}_{e,\text{env}} = \overline{\text{MISESAVG}}_{\text{inc}}$$
where $\overline{\text{MISESAVG}}_{\text{inc}}$ is the arithmetic mean across the **included** donor states.

When State 4 (149.9 MPa) was excluded at $\theta = 0.25$, the remaining 4 states had higher stress:
$$\overline{\text{MISESAVG}}_{\text{inc}} \text{ jumped from } 630.7\text{ MPa to } 750.9\text{ MPa } (+19.1\%)$$
Because Abaqus CAE native `RemeshingRule` computes its own internal relative error norm:
$$\eta_e^{\text{Abaqus}} \propto \frac{\text{MISESERI}_{e,\text{env}}}{\|\boldsymbol{\sigma}\|_{\text{Abaqus}}}$$
multiplying $\eta_{e,\max}$ by the higher domain mean stress shifted the absolute error field higher everywhere. Abaqus CAE translated this into drastically finer element sizing across the whole plate, causing Case 1 to explode from 9,234 elements to **122,532 elements** (+1227%) and failing Gate 06!

### Discovery 2: Why Excluding State 3 in Case 2 at $\theta = 0.50$ Failed to Prevent the Far-Field Explosion
At $\theta = 0.50$, State 3 (outer propagation, 250.2 MPa, 45.1% of peak) was excluded from Case 2. However, the element count did not decrease—it increased from 117,181 to **127,193 elements**!
Why? Because when State 3 was removed, $\overline{\text{MISESAVG}}_{\text{inc}}$ of the remaining 3 states increased from 426.9 MPa to 485.8 MPa (+13.8%). Exactly as in Case 1, the higher scaling factor inflated the absolute `MISESERI` written into the donor ODB, causing Abaqus native remeshing to refine the far field even further.

### Discovery 3: Over-Filtering at $\theta = 0.80$ Strips Crack-Path Resolution
At $\theta = 0.80$, States 2, 3, and 4 in Case 1 are excluded. While this reduced elements to 17,713, it stripped all late propagation error information: ligament coverage dropped to 70.1%, and corridor fine area dropped from 0.020 mm² to 0.012 mm², failing the scientific crack-path gate. Meanwhile, Cases 2 and 3 remained severely over-refined (102,987 and 116,648 elements), continuing to fail both Gate 06 and Gate 07.

---

## 5. Explicit Recommendation Against Guard Adoption

The review directive established the unambiguous adoption criterion:
> *"The goal is to preserve Case 1's efficiency gain (near 9,234 elements with ligament coverage restored toward the F1812 97.19% <= l0/2) while preventing the Case 2/3 element explosions (toward the F1812 counts of 41,438 and 77,779)... If NO threshold fraction achieves this, report that honestly and do NOT adopt the guard."*

Based on the quantitative parameter sweep across $\theta \in \{0.10, 0.25, 0.50, 0.80\}$:
- **No threshold fraction achieves both goals**:
  - $\theta \le 0.10$ preserves Case 1 (9,234 elements) but leaves Cases 2 and 3 exploded (117k and 130k).
  - $0.25 \le \theta \le 0.50$ catastrophically destroys Case 1 efficiency (84k - 122k elements) while worsening Case 2 (127k elements).
  - $\theta \ge 0.80$ corrupts Case 1 crack-path resolution while failing to resolve Cases 2 and 3.

**Definitive Recommendation**: The load-threshold guard **MUST NOT BE ADOPTED** into the production framework. The root cause of the Case 2/3 explosion is not merely the presence of low-load states, but the dimensional re-scaling by $\overline{\text{MISESAVG}}$ in the envelope synthesis.

---

## 6. Finite-Element Quality & Governance Verification

All generated meshes satisfy all fundamental continuum quality gates:
1. **Gate 01 (Jacobians)**: $\min \det(\mathbf{J}) > 0$ across all 16 meshes (zero inverted elements).
2. **Gate 02 (Quad Fraction)**: $\ge 97.0\%$ across all cases (well above the 90.0% threshold).
3. **Gate 03 (Aspect Ratio)**: $\max \text{AR} \le 2.85$ across all cases (well below 4.0).
4. **Gate 04 (Corner Angles)**: All angles strictly within $[24.4^\circ, 148.6^\circ]$.
5. **Frozen UEL**: Production UEL [f42_mixed_uel.for](file:///D:/Master%20thesis/Adaptive%20remeshing/models/pandey_kumar_mode1/268_f1824_job2_preflight/case1/f42_mixed_uel.for) preserved bitwise (`CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6`).
6. **Zero PBS Submissions**: Strictly 0 new PBS jobs consumed (cumulative 35 preserved; all Abaqus solves run locally).
7. **Master Goal Status**: Strictly `OPEN`.

---

## 7. Artifact Registry, Verification & Governance Sign-Off

### Publication Image Manifest (Commit-Pinned & Hash-Verified)

| Case ID | Image Path | Size [Bytes] | SHA-256 | Description |
|---|---|---|---|---|
| **Case 1** | [results/figures/fig_f1834_case_1_standalone_mesh.png](file:///D:/Master%20thesis/Adaptive%20remeshing/results/figures/fig_f1834_case_1_standalone_mesh.png) | 1,345,437 | `AF105A746DEBC76D63B52FAA4CFDB4A854587E3D8BB00547D99D80310F5D5DF4` | Case 1 Standalone Mesh View (F1834: 9,234 elements, 97.14% quads, Gate 06: 2.455x PASS) |
| **Case 2** | [results/figures/fig_f1834_case_2_standalone_mesh.png](file:///D:/Master%20thesis/Adaptive%20remeshing/results/figures/fig_f1834_case_2_standalone_mesh.png) | 2,882,100 | `78EE2CBA8CA184499CF1121E40D1E0590D9401AAED9C2C5BC98688B6AB8A41CE` | Case 2 Standalone Mesh View (F1834: 117,181 elements, 97.58% quads, outermost distal 100.0% PASS) |
| **Case 3** | [results/figures/fig_f1834_case_3_standalone_mesh.png](file:///D:/Master%20thesis/Adaptive%20remeshing/results/figures/fig_f1834_case_3_standalone_mesh.png) | 2,193,581 | `80E934CB4344AB1C993EF5791946E24E43971FBF00D3FDCB8D61FEAD7BD8D4C4` | Case 3 Standalone Mesh View (F1834: 130,218 elements, 97.38% quads, secondary corridor 98.98% PASS) |
| **Case 5** | [results/figures/fig_f1834_case_5_standalone_mesh.png](file:///D:/Master%20thesis/Adaptive%20remeshing/results/figures/fig_f1834_case_5_standalone_mesh.png) | 1,574,199 | `0EDF48A48654CD2A28DA520C1FF923E873F4401C21ABC525164C9F786D3BB526` | Case 5 Standalone Mesh View (F1834: 15,466 elements, 97.90% quads, Table 6 parity preserved) |
| **Composite** | [results/figures/fig_f1834_four_benchmark_synthesis.png](file:///D:/Master%20thesis/Adaptive%20remeshing/results/figures/fig_f1834_four_benchmark_synthesis.png) | 7,081,644 | `F56B305121279C39B1A0F4659B17E642697A471AD876A555C8A9E8DB46F1F074` | 4-Panel Publication Synthesis Composite under Load-Threshold Guard |

### Primary Verification Artifacts

- **Master Receipt**: [models/pandey_kumar_mode1/PK_F1834_BLOWUP_GUARD_RECEIPT.json](file:///D:/Master%20thesis/Adaptive%20remeshing/models/pandey_kumar_mode1/PK_F1834_BLOWUP_GUARD_RECEIPT.json)
- **Summary JSON**: [results/validation/f1834_blowup_guard_summary.json](file:///D:/Master%20thesis/Adaptive%20remeshing/results/validation/f1834_blowup_guard_summary.json)
- **Diagnosis JSON**: [results/validation/f1834_early_state_diagnosis.json](file:///D:/Master%20thesis/Adaptive%20remeshing/results/validation/f1834_early_state_diagnosis.json)
- **Parameter Sweep Summary**: [models/pandey_kumar_mode1/274_f1834_blowup_guard/threshold_sweep_summary.json](file:///D:/Master%20thesis/Adaptive%20remeshing/models/pandey_kumar_mode1/274_f1834_blowup_guard/threshold_sweep_summary.json)
- **Unit Test Suite**: [tests/unit/test_f1834_early_state_blowup_guard.py](file:///D:/Master%20thesis/Adaptive%20remeshing/tests/unit/test_f1834_early_state_blowup_guard.py) (6/6 PASS, 100%)
- **Dispatch Script**: [.agents/scripts/dispatch_f1834_blowup_guard_auth_001.ps1](file:///D:/Master%20thesis/Adaptive%20remeshing/.agents/scripts/dispatch_f1834_blowup_guard_auth_001.ps1)

### Governance Summary
- **Cumulative PBS Submissions**: Strictly 35 (`max_new_pbs = 0`; all Abaqus solves executed locally).
- **Bitwise Frozen Production UEL**: `CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6`.
- **Shared Framework SHA-256**: `098D005F93138749E80975C4A96F6BDF5EE7C54B98DB0162BDC62188FE76B187`.
- **Master Goal Status**: Strictly `OPEN`.

