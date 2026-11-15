# Task F1773: Four-Benchmark Method A Regression Suite Execution Plan & Reconciled Manifest

**Document ID:** `DOC_F1773_FOUR_BENCHMARK_REGRESSION_PLAN`  
**Classification:** `FOUR_BENCHMARK_REGRESSION_PLAN`  
**Task ID:** `F1773-UNIFIED-METHOD-A-FOUR-BENCHMARK-REGRESSION-PLAN`  
**Predecessor Tasks:** Task F1772 (`F1772-CASE1-METHOD-A-ADVANCING-REMESHING-EXECUTION`), Task F1767 (`F1767-UNIFIED-METHOD-A-OFFLINE-QUALIFICATION-AND-RECONCILIATION`), Task F1766 (`F1766-UNIFIED-METHOD-A-REGRESSION-PLAN-AND-DIAGNOSIS`)  
**Assigned Agent:** Gemini Antigravity  
**Date:** 15 November 2026  
**Execution Host:** TU Bergakademie Freiberg HPC Cluster (`entry_imfdfkmq` / `normal_imfdfkmq`)  
**Accounting Status:** 0 PBS jobs consumed under Task F1773 (Zero-PBS Specification & Reconciliation Phase); Cumulative Historical Submissions = **30**.  

---

## 1. Executive Context & Review Mandate

Under the user-directed development policy (*Unified Method A full-suite regression*, 15 November 2026) and supervisory review directive `HND-F1773-SUITE-REGRESSION-AUTH-001` (`DECISION: INSUFFICIENT_EVIDENCE`), Task F1773 establishes the authoritative, reconciled execution plan for the complete four-benchmark Method A regression suite.

All material findings raised in review `HND-F1773-SUITE-REGRESSION-AUTH-001` are conclusively resolved:
1. **F1773-R01 (Case 2 Geometry Reconciled):** Reconciled strictly to the authoritative committed configuration `configs/remeshing/f1728_case2_off_axis_hole.json`: plate $1.0 \times 1.0\,\text{mm}$, initial notch $a_0 = 0.50\,\text{mm}$ at $y = 0.50\,\text{mm}$, circular hole $r = 0.10\,\text{mm}$ centered at $(0.65, 0.65)\,\text{mm}$, length scale $\ell_0 = 0.0075\,\text{mm}$.
2. **F1773-R02 (Case 2 Donor ODB Reconciled):** Reconciled to the canonical donor `PK_HOLE_COMPANION_RECOVERY.odb` (`RECOVERY_STEP`, `LAST_INCREMENT`, $u_y = 0.0050\,\text{mm}$), matching `canonical_five_case_manifest.json` line 40.
3. **F1773-R03 (Case 3 Multi-State Workflow Reconciled):** Reconciled to the verified 2-pass sequential Method A.2 architecture using `PK_SEC43_STAGGERED_JOB1.odb` (Step-1, State 2 $u = 0.150\,\text{mm}$ and State 4 $u = 0.275\,\text{mm}$), matching `canonical_five_case_manifest.json` line 62.
4. **F1773-R04 (Case 1 Envelope Sizing Classification):** Case 1 is accurately classified as damage-envelope-assisted native mesh generation (inverted sizing relation $d_{\max} \to \hat{\eta}_e$), not bare unmodified recovery error. Its results ($N=20,232$, 97.17% quads, mean AR 1.2637, 100% ligament compliance) and failed gates (G1, G6, G7) are preserved without resubmission.
5. **F1773-R05 (Zero-PBS Planning Boundary):** Task F1773 strictly consumes 0 PBS submissions (max_new_pbs_submissions = 0). Batch execution will be authorized under a distinct reviewed execution task.
6. **F1773-R06 (Case-Specific Gates Retained):** Standardized gates preserve each benchmark's distinct literature thresholds without blurring.
7. **F1773-R07 (Five-Hole Plate Historical Evidence Preserved):** Case 4 (Section 4.5, 12,625 elements from F1763) is preserved bitwise in the repository, documenting why it is omitted from mandatory regression cycles due to structural redundancy with the 7-hole plate.

---

## 2. Reconciled Four-Benchmark Regression Matrix

| BM # | Case Identifier | Benchmark Geometry & Configuration | Algorithm Variant | Authoritative Donor ODB & Step | Literature Target Elements | Historical Reference & Predecessor Status |
| :---: | :--- | :--- | :---: | :--- | :---: | :--- |
| **BM-1** | **Case 1** | **Mode-I Edge-Cracked Plate**<br>`configs/remeshing/f1728_case1_mode1_edge_crack.json`<br>$1.0 \times 1.0\,\text{mm}$, notch $a_0 = 0.5\,\text{mm}$, $\ell_0 = 0.0075\,\text{mm}$ | **Method A.1**<br>(Single-Pass Damage Envelope) | `PK_F1772_CASE1_ENVELOPE.odb`<br>(Step-2 envelope from `PK_F1769_C1_DONOR.odb`) | 13,762 elements<br>(Pandey & Kumar Fig. 4a) | **PILOT COMPLETE (REUSED FROM F1772)**<br>$N = 20,232\,\text{el}$, 97.17% quads, $\min\det(J) > 0$, max AR 2.65, mean AR 1.2637, 100% ligament compliant ($h \le \ell_0$), zero coarse barriers. Gates: G2, G3, G4, G5, G8 PASS; G1, G6, G7 FAIL. |
| **BM-2** | **Case 2** | **Plate with an Off-Axis Hole**<br>`configs/remeshing/f1728_case2_off_axis_hole.json`<br>$1.0 \times 1.0\,\text{mm}$, notch $a_0 = 0.5\,\text{mm}$, hole $r = 0.10\,\text{mm}$ at $(0.65, 0.65)$, $\ell_0 = 0.0075\,\text{mm}$ | **Method A.1**<br>(Single-Pass Native Method A) | `PK_HOLE_COMPANION_RECOVERY.odb`<br>(Step: `RECOVERY_STEP`, `LAST_INCREMENT`, $u_y = 0.0050\,\text{mm}$) | 23,618 elements<br>(Pandey & Kumar Fig. 19a) | **READY FOR BATCH EXECUTION**<br>Target: 23,618 $\pm 10\%$. Predecessor F1734: 23,965 elements (+1.47%), 97.2% quads, zero negative Jacobians. Refinement around hole and proximal ligament, coarse background. |
| **BM-3** | **Case 3** | **Rectangular Notched Plate with Hole and Pins**<br>`configs/remeshing/f1728_case3_notched_plate_pins.json`<br>$65 \times 120\,\text{mm}$, notch $a = 10\,\text{mm}$, pin holes $r = 5\,\text{mm}$ at $(20,20)$ and $(20,100)$, void $r = 10\,\text{mm}$ at $(36.5,51)$, $\ell_0 = 0.285\,\text{mm}$ | **Method A.2**<br>(Sequential 2-Pass Method A) | `PK_SEC43_STAGGERED_JOB1.odb`<br>(Step-1, States 2 & 4: frames 30 and 55, $u_y = 0.150$ and $0.275\,\text{mm}$) | 12,168 elements<br>(Pandey & Kumar Fig. 18a) | **READY FOR BATCH EXECUTION**<br>Target: 12,168 $\pm 10\%$. Baseline F192: 12,110 elements (-0.48%). Sequential 2-pass envelope preserving refinement across primary and secondary crack branching corridors. |
| **BM-4** | **Case 5** | **Seven-Hole Plate**<br>`configs/remeshing/f1728_case5_seven_hole.json`<br>$1.0 \times 1.0\,\text{mm}$, notchless, 7 circular holes per Table 6, $\ell_0 = 0.008\,\text{mm}$ | **Method A.1**<br>(Single-Pass Native Method A) | `PK_F1726_SEVEN_HOLE_COARSE.odb`<br>(194.3 MB, Step-2, ALL_INCREMENTS, $u_y = 0.00656\,\text{mm}$) | 15,714 elements<br>(Pandey & Kumar Fig. 25b) | **READY FOR BATCH EXECUTION**<br>Target: 15,714 $\pm 5\%$. Predecessor F1726: 15,708 elements (-0.04%), 97.6% quads, zero negative Jacobians. Continuous refinement across upper inter-hole ligament, coarse inactive lower region. |

*(Case 4 Five-Hole Benchmark Status: Pandey & Kumar Section 4.5 5-hole plate with edge cutouts is preserved in historical records with its 12,625-element mesh [F1763] and 13,017-element mesh [F1725]. It is omitted from active regression cycles due to structural redundancy with the 7-hole benchmark, as authorized under the user development policy).*

---

## 3. Invariant Bitwise Hashes

Every benchmark in the suite is strictly bound to the identical shared framework and user subroutine:

| Component | Path / Identifier | Bitwise Frozen SHA-256 | Verification Status |
| :--- | :--- | :--- | :---: |
| **Reusable Framework** | `scripts/remeshing/reusable_2d_adaptive_framework.py` | `8D71F38F23867A23C1FC1BF5EC499533A8C75F538B77804ECE03B5C668F4BE08` | **MATCH** |
| **Production UEL** | `models/pandey_kumar_mode1/f42_mixed_uel.for` | `CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6` | **MATCH** |
| **Case 1 Config** | `configs/remeshing/f1728_case1_mode1_edge_crack.json` | `954BE4473EBC79D54E18DA81DF00E6FCEA1E6B9F8430EA4A8DB52D920E5AA7F3` | **MATCH** |
| **Case 2 Config** | `configs/remeshing/f1728_case2_off_axis_hole.json` | `0B2F2A8E...` | **MATCH** |
| **Case 3 Config** | `configs/remeshing/f1728_case3_notched_plate_pins.json` | `DE2A707B...` | **MATCH** |
| **Case 5 Config** | `configs/remeshing/f1728_case5_seven_hole.json` | `6966CD45...` | **MATCH** |
| **Canonical Manifest** | `configs/remeshing/canonical_five_case_manifest.json` | `9480C930...` | **MATCH** |

---

## 4. Predeclared Acceptance Gate Matrix for the Four-Benchmark Suite

| Gate | Description | Benchmark Thresholds | Literature Concordance |
| :---: | :--- | :--- | :--- |
| **G1** | Element Count Parity | Case 1: [12,385, 15,138] (20,232 el preserved FAIL)<br>Case 2: [21,256, 25,980] (23,618 published)<br>Case 3: [10,951, 13,385] (12,168 published)<br>Case 5: [14,928, 16,500] (15,714 published) | Literature benchmarks: Fig. 4a, Fig. 19a, Fig. 18a, Fig. 25b |
| **G2** | Quadrilateral Fraction | $N_{\text{quad}} / N_{\text{total}} \ge 95.0\%$ across all four meshes | High quad dominance for 3-layer UEL compatibility |
| **G3** | Signed Jacobian Validity | $\min \det(J) > 0$ across 100.0% of elements; 0 distorted elements | Geometric admissibility for finite element solution |
| **G4** | Element Aspect Ratio | $\max \text{AR} \le 4.0$, $\text{mean AR} \le 1.50$ (Case 1 actual: mean = 1.2637, max = 2.6533: PASS) | Regular element shapes |
| **G5** | Critical Ligament Resolution | $\ge 90.0\%$ area with $h \le \ell_0$ across prospective crack paths | Fully resolves active fracture process zones |
| **G6** | High-Gradient Tip Resolution | $\ge 90.0\%$ count with $h \le \ell_0/2$ near notches/stress concentrations | Captures steep phase-field gradients |
| **G7** | Far-Field Mesh Efficiency | Background elements reach coarse sizing ($h_{\max} \ge 2.0\,\ell_0$) | Preserves selective computational efficiency |
| **G8** | Production 3-Layer UEL Datacheck | Exit 0 under frozen UEL `f42_mixed_uel.for` across all four production decks | Full compatibility with coupled phase-field solver |

---

## 5. Submission Accounting & Resource Governance

- **Submissions Consumed under Task F1773:** **0 / 0** (Zero-PBS specification task).
- **Current Cumulative Submissions:** **30**.
- **Prospective Execution Batch Allowance:** Exactly **3 bounded PBS submissions** (Job 31 for Case 2, Job 32 for Case 3, Job 33 for Case 5). Case 1 will NOT be resubmitted.
- **Resource Limits per Job:** 1 CPU serial, 16 GB RAM, 1-hour walltime limit, atomic POSIX directory lock guards, independent hash preflight, dual-channel notifications.
- **Automatic Retries:** Strictly `false`. Any failure will be preserved in records and diagnosed without blind repetition.
