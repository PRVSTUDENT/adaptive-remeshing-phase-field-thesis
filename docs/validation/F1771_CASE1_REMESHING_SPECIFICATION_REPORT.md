# Task F1771: Case 1 Method A Advancing Adaptive Remeshing Specification & Pre-Execution Verification Report

**Document ID:** `DOC_F1771_CASE1_REMESHING_SPECIFICATION_REPORT`  
**Classification:** `ZERO_PBS_METHOD_A_SPECIFICATION`  
**Task ID:** `F1771-CASE1-METHOD-A-ADVANCING-REMESHING-SPECIFICATION`  
**Predecessor Tasks:** Task F1770 (`F1770-CASE1-ADVANCING-COUPLED-DONOR-REPLACEMENT-EXECUTION`), Task F1768 (`F1768-CASE1-ADVANCING-COUPLED-DONOR-PREPARATION`), Task F1766 (`F1766-UNIFIED-METHOD-A-REGRESSION-PLAN-AND-DIAGNOSIS`)  
**Assigned Agent:** Gemini Antigravity  
**Date:** 15 November 2026  
**Target Execution Environment:** TU Bergakademie Freiberg HPC Cluster (Queue: `entry_imfdfkmq`, 1 CPU serial, 16 GB RAM, 1h walltime)  
**Accounting:** Exactly 0 PBS submissions consumed under Task F1771 (0/0 allowance); cumulative historical submissions preserved at 29.  

---

## 1. Executive Summary & Objective

Following the successful generation and verification of the authentic advancing coupled phase-field donor ODB in Task F1770 (`PK_F1769_C1_DONOR.odb`, 725 MB, 573 frames, crack advance $\Delta a = 0.4904\,\text{mm}$ across 98.1% of the ligament, 97.40% post-peak softening drop, Exit 0), Task F1771 establishes the pre-execution technical specification for Case 1 (Pandey & Kumar 2025 Section 4.1 Mode-I Edge-Cracked Plate) single-pass Method A adaptive remeshing.

This milestone directly resolves the core limitation diagnosed in Task F1766 and Task F1760:
1. **Prior Baseline Limitation (Task F1738):** Automated remeshing previously relied on a linear static elastic donor (`PK_MODE1_COARSE_STEP1.odb`, Step-1 LAST_INCREMENT). Because static linear elasticity exhibits a localized $1/\sqrt{r}$ stress singularity at the initial notch tip ($x=0.50\,\text{mm}$), the error indicator decayed into far-field coarseness along the remainder of the ligament ($0.50 < x \le 1.00\,\text{mm}$). To force refinement across the distal ligament, prior work in F1738 utilized an artificial predefined geometric corridor, violating the pure indicator-driven mandate.
2. **Advancing Coupled Donor Strategy (Task F1771):** The new donor ODB captures genuine coupled phase-field crack propagation across 522 increments in Step 2. Configured with `outputFrequency=ALL_INCREMENTS`, Abaqus `adaptiveRemesh` computes the envelope of maximum recovery error (`MISESERI`) across all crack-tip locations from $x = 0.50\,\text{mm}$ to $x = 0.99\,\text{mm}$.
3. **Common Reusable Implementation:** Execution utilizes the frozen, shared Python framework `scripts/remeshing/reusable_2d_adaptive_framework.py` without case-specific geometric partitioning.

---

## 2. Configuration & Remeshing Rule Architecture

The Case 1 remeshing configuration `configs/remeshing/f1728_case1_mode1_edge_crack.json` (SHA-256 `954BE4473EBC79D54E18DA81DF00E6FCEA1E6B9F8430EA4A8DB52D920E5AA7F3`) has been updated to align with the authentic Step-2 ALL_INCREMENTS envelope:

```json
  "remeshing_rule": {
    "error_target": 1.85,
    "min_element_size_mm": 0.001,
    "max_element_size_mm": 0.020,
    "refinement_factor": 10,
    "coarsening_factor": "NOT_ALLOWED",
    "sizing_method": "UNIFORM_ERROR",
    "variable": "MISESERI",
    "step_name": "Step-2",
    "output_frequency": "ALL_INCREMENTS"
  }
```

### Parameter Rationale
- **`step_name: "Step-2"`**: Selects the fracture propagation step containing the 522 increments of advancing crack growth, bypassing the static pre-critical Step 1.
- **`output_frequency: "ALL_INCREMENTS"`**: Instructs the Abaqus remeshing engine to evaluate the union/envelope of error indicator distributions across all frames in Step 2, ensuring that every point traversed by the crack tip generates a refinement request.
- **`error_target: 1.85%`**: Authoritative target calibrated to reproduce the published benchmark element density (~13,762 to 13,941 elements).
- **`coarsening_factor: "NOT_ALLOWED"`**: Prevents Abaqus from de-refining elements where earlier increments had high errors but later increments had relaxed stress.
- **`min_element_size_mm: 0.001 mm`**: Enforces $h_{\min} = 1.0\,\mu\text{m} = \ell_0 / 7.5$ (where $\ell_0 = 0.0075\,\text{mm}$), ensuring dense resolution across the active crack core.
- **`max_element_size_mm: 0.020 mm`**: Controls far-field background elements at $h_{\max} = 0.020\,\text{mm} = 2.67 \ell_0$.

---

## 3. Predeclared Acceptance Gate Matrix (G1–G8)

To maintain strict scientific discipline without retrospective threshold relaxation, the adapted physical mesh generated under Task F1771 will be evaluated against the following quantitative gates:

| Gate | Description | Predeclared Requirement | Literature Reference / Target |
| :---: | :--- | :--- | :--- |
| **G1** | Target Element Count Parity | $N_{\text{elem}} \in [12,385, 15,138]$ elements ($\pm 10.0\%$) | Published: 13,762 elements (Pandey & Kumar 2025 Fig. 4) |
| **G2** | Quadrilateral Element Fraction | $N_{\text{quad}} / N_{\text{total}} \ge 95.0\%$ | High quad dominance for UEL compatibility |
| **G3** | Signed Jacobian Validity | $\min \det(J) > 0$ across 100.0% of elements | Zero inverted or distorted elements |
| **G4** | Element Aspect Ratio | $\max \text{AR} \le 4.0$, $\text{mean AR} \le 1.50$ | Regular quad aspect ratios |
| **G5** | Ligament Spatial Resolution | Along $0.50 \le x \le 1.00\,\text{mm}$, $|y - 0.50| \le 0.05\,\text{mm}$: $\ge 90.0\%$ area $h \le \ell_0$ ($0.0075\,\text{mm}$) | Resolves full crack path across ligament |
| **G6** | Process Zone Tip Resolution | Proximal tip region $0.50 \le x \le 0.65\,\text{mm}$: $\ge 95.0\%$ count $h \le \ell_0/2$ ($0.00375\,\text{mm}$) | Captures steep phase-field gradient |
| **G7** | Far-Field Mesh Control | Coarse background elements reach $h_{\max} \ge 0.018\,\text{mm}$ ($h/\ell_0 \ge 2.4$) | Verifies selective adaptive efficiency |
| **G8** | Production 3-Layer UEL Deck | Complete deck with 3 layers passes cluster datacheck Exit 0 | Bitwise frozen UEL `f42_mixed_uel.for` (`CE8D5EDC...`) |

---

## 4. PBS Execution Script & Resource Specification

The cluster execution wrapper `models/pandey_kumar_mode1/238_f1771_case1_remesh/submit_f1771_case1_remesh.pbs` (SHA-256 `ED9B2B715F79A269602E5EFA8DB74CBC68465568C4C131D76770D3AD5B57D843`) has been staged:

- **Cluster Scratch Directory:** `/scratch9/pr21vyci/runs/mode1_pk_f1771_case1_remesh/`
- **Resource Request:** 1 CPU, 16 GB RAM, 1 hour walltime, queue `entry_imfdfkmq`.
- **Lock Guard Safety (R2 Protocol):**
  - Atomic directory lock guard: `mkdir "${LOCK_GUARD_DIR}"` with `rmdir` trap.
  - Fail-closed check if pre-existing `${JOB_NAME}.lck` is detected.
  - Zero unconditional lock file deletions (`rm -f *.lck` strictly absent).
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

## 5. Immutable Code, Data, and Model Provenance

- **Bitwise Frozen Production UEL:**  
  `models/pandey_kumar_mode1/f42_mixed_uel.for`  
  SHA-256: `CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6`
- **Shared 2D Adaptive Framework:**  
  `scripts/remeshing/reusable_2d_adaptive_framework.py`  
  SHA-256: `8D71F38F23867A23C1FC1BF5EC499533A8C75F538B77804ECE03B5C668F4BE08`
- **Updated Case 1 Configuration:**  
  `configs/remeshing/f1728_case1_mode1_edge_crack.json`  
  SHA-256: `954BE4473EBC79D54E18DA81DF00E6FCEA1E6B9F8430EA4A8DB52D920E5AA7F3`
- **Staged Cluster PBS Script:**  
  `models/pandey_kumar_mode1/238_f1771_case1_remesh/submit_f1771_case1_remesh.pbs`  
  SHA-256: `ED9B2B715F79A269602E5EFA8DB74CBC68465568C4C131D76770D3AD5B57D843`
- **Authentic Advancing Coupled Donor ODB:**  
  `/scratch9/pr21vyci/runs/mode1_pk_f1768_case1_donor_prep/PK_F1769_C1_DONOR.odb` (725 MB, 573 frames)

---

## 6. Verification and Unit Testing

The standalone unit test suite `tests/unit/test_f1771_case1_remeshing_specification.py` was authored and verified:
- `test_frozen_uel_immutability`: PASS
- `test_shared_framework_immutability`: PASS
- `test_case1_remeshing_config_alignment`: PASS
- `test_canonical_manifest_case1_concordance`: PASS
- `test_submit_f1771_script_directives_and_atomic_lock_guard`: PASS
- `test_f1770_donor_audit_data_availability`: PASS

**Result:** 6/6 tests pass cleanly in 0.36s. The full multi-task regression suite across F1763–F1771 passes **43/43 tests** in 2.85s.

---

## 7. Submission Accounting & Forward Plan

- **Submissions Consumed under Task F1771:** Exactly 0 (0/0 allowance).
- **Cumulative Historical Submissions:** Permanently preserved at **29**.
- **Review Dispatch:** Staging review authorization payload `HND-F1771-CASE1-REMESH-AUTH-001` across OpenClaw PAD bridge to ChatGPT requesting formal execution authorization for exactly 1 bounded PBS mesh-generation pilot (prospective Job 30 upon launch).
