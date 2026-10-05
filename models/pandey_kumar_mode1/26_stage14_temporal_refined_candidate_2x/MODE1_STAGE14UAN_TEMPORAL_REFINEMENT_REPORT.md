# Mode-I Gate-6B Stage 14U-AL: 2x Temporal Refinement Evaluation Report

Protocol Version: 2  
Evaluator: `evaluate_stage14ual_temporal_refinement.py`  
Task ID: `F1221-GATE6B-STAGE14UAL-EVALUATOR-FREEZE-AND-DECISION-PROTOCOLS-20261004`  
Governing Verdict: **`TEMPORAL_REFINEMENT_EARLY_BIFURCATION_DETECTED`**  
Predeclared Decision Branch: **`TEMPORAL_REFINEMENT_CHANGES_FAILURE_PATH`**  
Action Directive: **`HOLD_PACKAGE_28__PERFORM_PATH_BIFURCATION_AUDIT`**  

---

## 1. Temporal Discretization & Parameters

- **Baseline Step 1:** $\Delta t = 5.0\times 10^{-4}$ ($\Delta u = 2.50\,\mathrm{nm}$, 2000 incs)
- **Baseline Step 2:** $\Delta t = 2.0\times 10^{-4}$ ($\Delta u = 1.00\,\mathrm{nm}$, 5000 incs)
- **$2\times$ Refined Step 1:** $\Delta t = 2.5\times 10^{-4}$ ($\Delta u = 1.25\,\mathrm{nm}$, 4000 incs)
- **$2\times$ Refined Step 2:** $\Delta t = 1.0\times 10^{-4}$ ($\Delta u = 0.50\,\mathrm{nm}$, 10000 incs)

---

## 2. Comparison Summary & Advancement

| Metric | Baseline Solve (1409982) | $2\times$ Temporal Diagnostic (1410027) | Discrepancy / Assessment |
| :--- | :---: | :---: | :---: |
| **Completed Increments** | 4890 | 8958 | Progressing |
| **Reached Displacement $u$** | 0.007889 mm | 0.007470 mm | Active Solve |
| **Cutbacks Count** | 0 | 6 | 0 in elastic regime |
| **$K_0$ Structural Stiffness** | 137.9095578493475 kN/mm | 137.90997507354126 kN/mm | `0.0003025346468182303`% |

---

## 3. Predeclared 10-Matched-Displacement States

| Target $u$ [mm] | Baseline $F$ [kN] | $2\times$ Temporal $F$ [kN] | Status Verdict |
| :---: | :---: | :---: | :---: |
| 0.001000 | 0.137888 | 0.137888 | `MATCHED` |
| 0.003000 | 0.408299 | 0.408299 | `MATCHED` |
| 0.005000 | 0.661725 | 0.661725 | `MATCHED` |
| 0.005733 | 0.743701 | 0.743376 | `MATCHED` |
| 0.005857 | 0.068060 | 0.002735 | `MATCHED` |
| 0.006000 | 0.001992 | 0.002779 | `MATCHED` |
| 0.006500 | 0.002062 | 0.002887 | `MATCHED` |
| 0.007000 | 0.002055 | 0.002780 | `MATCHED` |
| 0.007889 | 0.001764 | NOT_REACHED | `NOT_REACHED` |

---

## 4. Decision Branch Protocol & Gated Execution Directive

- **Active Branch:** `TEMPORAL_REFINEMENT_CHANGES_FAILURE_PATH`
- **Governing Directive:** `HOLD_PACKAGE_28__PERFORM_PATH_BIFURCATION_AUDIT`
- **Package 28 ($C_n = 0.50$) Submission Status:** **STRICTLY HELD** while temporal diagnostic is running.
