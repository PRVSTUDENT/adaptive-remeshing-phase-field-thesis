# Task F1772: Case 1 Method A Advancing Adaptive Remeshing Execution Plan & Gate Specification

**Document ID:** `DOC_F1772_CASE1_REMESHING_EXECUTION_PLAN`  
**Classification:** `METHOD_A_PILOT_EXECUTION_PLAN`  
**Task ID:** `F1772-CASE1-METHOD-A-ADVANCING-REMESHING-EXECUTION`  
**Predecessor Tasks:** Task F1771 (`F1771-CASE1-METHOD-A-ADVANCING-REMESHING-SPECIFICATION`), Task F1770 (`F1770-CASE1-ADVANCING-COUPLED-DONOR-REPLACEMENT-EXECUTION`)  
**Assigned Agent:** Gemini Antigravity  
**Date:** 15 November 2026  
**Execution Host:** TU Bergakademie Freiberg HPC Cluster (`entry_imfdfkmq` / `normal_imfdfkmq`, 1 CPU serial, 16 GB RAM, 1h walltime)  
**Prospective PBS Job:** `F1772_C1_REMESH` (Prospective cumulative job 30 upon launch)  
**Accounting Allowance:** Exactly 1 PBS mesh-generation submission authorized under Task F1772; current submissions consumed = 0/1; cumulative historical submissions = 29.  

---

## 1. Context & Review Directive Mandate

Task F1771 established the zero-PBS pre-execution specification for Case 1 (Pandey & Kumar 2025 Section 4.1 Mode-I Edge-Cracked Plate) single-pass Method A adaptive remeshing. Independent scientific supervision (ChatGPT) evaluated the specification under correlation ID `HND-F1771-CASE1-REMESH-AUTH-001` (`DECISION: APPROVE`), issuing specific scientific directives:

- **F1771-R01 (Donor Limitation Disclosure):** The F1770 donor passed 6 of 7 gates, with Gate G3 failing due to unconstrained linear Helmholtz Poisson smoothing oscillations ($\min d = -0.0112$). This finding is explicitly preserved as a documented scientific limitation of the frozen production UEL, without retrospective relaxation.
- **F1771-R02 (Single-Pass Method A.1 Designation):** Case 1 is executed strictly as single-pass Method A.1 (one-shot error-envelope remeshing followed by fracture simulation), maintaining explicit distinction from multi-state Method A.2.
- **F1771-R03 (Distinct Task Registration):** Successor Task F1772 is registered with a dedicated 1-job allowance, preventing unauthorized submission under the zero-PBS predecessor.
- **F1771-R04 (Comprehensive Preflight Hashing):** The execution script `submit_f1772_case1_remesh.pbs` independently validates the SHA-256 hashes of the user subroutine, configuration file, and shared framework script, and confirms donor ODB size before solver launch.
- **F1771-R05 (Bounded Computational Resources):** 1 CPU serial, 16 GB memory, 1-hour walltime limit enforced.
- **F1771-R06 (Empirical Physical Acceptance):** Full post-generation physical INP inspection, Jacobian/aspect-ratio audit, and cluster datacheck required before claiming scientific acceptance.

---

## 2. Configuration & Framework Architecture

- **Shared Framework Module:**  
  `scripts/remeshing/reusable_2d_adaptive_framework.py`  
  SHA-256: `8D71F38F23867A23C1FC1BF5EC499533A8C75F538B77804ECE03B5C668F4BE08` (Bitwise Preserved)
- **Case 1 Configuration:**  
  `configs/remeshing/f1728_case1_mode1_edge_crack.json`  
  SHA-256: `954BE4473EBC79D54E18DA81DF00E6FCEA1E6B9F8430EA4A8DB52D920E5AA7F3`
- **Authentic Advancing Coupled Donor ODB:**  
  `/scratch9/pr21vyci/runs/mode1_pk_f1768_case1_donor_prep/PK_F1769_C1_DONOR.odb` (725 MB, 573 frames)
- **Remeshing Rule:**
  - `step_name: "Step-2"`
  - `output_frequency: "ALL_INCREMENTS"`
  - `variable: "MISESERI"`
  - `error_target: 1.85%`
  - `coarsening_factor: "NOT_ALLOWED"`
  - `min_element_size_mm: 0.001 mm`
  - `max_element_size_mm: 0.020 mm`
  - `refinement_factor: 10`

---

## 3. Predeclared Acceptance Gate Matrix (G1–G8)

| Gate | Description | Predeclared Acceptance Requirement | Literature Target / Baseline |
| :---: | :--- | :--- | :--- |
| **G1** | Element Count Parity | $N_{\text{elem}} \in [12,385, 15,138]$ elements ($\pm 10.0\%$) | 13,762 published elements (Pandey & Kumar 2025 Fig. 4) |
| **G2** | Quadrilateral Fraction | $N_{\text{quad}} / N_{\text{total}} \ge 95.0\%$ | High quad dominance for UEL compatibility |
| **G3** | Signed Jacobian Validity | $\min \det(J) > 0$ across 100.0% of elements | Zero distorted or negative Jacobian elements |
| **G4** | Element Aspect Ratio | $\max \text{AR} \le 4.0$, $\text{mean AR} \le 1.50$ | Regular element shapes |
| **G5** | Ligament Spatial Resolution | Along horizontal ligament ($0.50 \le x \le 1.00\,\text{mm}$, $|y - 0.50| \le 0.05\,\text{mm}$): $\ge 90.0\%$ area $h \le \ell_0$ ($0.0075\,\text{mm}$) | Resolves full crack path across ligament |
| **G6** | Proximal Tip Resolution | Along proximal notch tip ($0.50 \le x \le 0.65\,\text{mm}$): $\ge 95.0\%$ count $h \le \ell_0/2$ ($0.00375\,\text{mm}$) | Captures steep phase-field gradient |
| **G7** | Far-Field Mesh Control | Coarse background elements reach $h_{\max} \ge 0.018\,\text{mm}$ ($h/\ell_0 \ge 2.4$) | Preserves selective adaptive efficiency |
| **G8** | Production 3-Layer UEL Deck | Complete 3-layer UEL deck passes cluster datacheck Exit 0 | Bitwise frozen UEL `f42_mixed_uel.for` (SHA-256: `CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6`) |

---

## 4. Execution Script & Cluster Staging Specification

- **Script Path:** `models/pandey_kumar_mode1/239_f1772_case1_remesh/submit_f1772_case1_remesh.pbs`  
  SHA-256: `668F98748F2B5E0FDE3F6C9521132A922D27489F8F86EAB0DA51FD2D05C9F5F5`
- **Cluster Run Directory:** `/scratch9/pr21vyci/runs/mode1_pk_f1772_case1_remesh/`
- **Execution Host:** Cluster compute node (Queue: `entry_imfdfkmq`, 1 CPU serial, 16 GB RAM, 1h walltime)
- **Lock Guard Safety (R2 Protocol):**
  - Atomic directory lock guard: `mkdir "${LOCK_GUARD_DIR}"` with `rmdir` trap.
  - Fail-closed check if pre-existing `${JOB_NAME}.lck` is detected.
  - Zero unconditional lock deletions (`rm -f *.lck` strictly absent).
- **Execution Command:**
  ```bash
  /cluster/application/abaqus/2023/Commands/abaqus cae noGUI="${RUN_DIR}/${FRAMEWORK_SCRIPT}" -- \
      --config "${RUN_DIR}/${CONFIG_FILE}" \
      --run-case \
      --odb "${RUN_DIR}/${DONOR_ODB}" \
      --output-dir "${RUN_DIR}"
  ```
- **Dual-Channel Notifications:** Directives `#PBS -m abe` and `#PBS -M pr21vyci@mailserver.tu-freiberg.de` with `job_notifications.sh` integration.

---

## 5. Submission Accounting & Safety Bounds

- **Submissions Consumed under Task F1772:** 0/1.
- **Current Cumulative Submissions:** **29**.
- **Prospective Cumulative Submissions:** **30** (upon successful PBS submission).
- **Automatic Retries:** Strictly `false`. Any solver failure or timeout will be preserved in records and diagnosed without resubmission.
