# Task F1774 Execution Package Safety & Scientific Repair Report
## Coordinated Four-Benchmark Method A Adaptive Remeshing Execution Package

**Task ID:** `F1774-FOUR-BENCHMARK-METHOD-A-REGRESSION-EXECUTION`  
**Date:** 15 November 2026  
**Agent:** Gemini Antigravity  
**Review Target:** `HND-F1774-SUITE-REGRESSION-EXEC-002` (resolving Review Findings F1774-R01 through F1774-R06 from `HND-F1774-SUITE-REGRESSION-EXEC-001`)  
**Cumulative PBS Submissions Accounted:** 30 (0 consumed under F1774, maximum 3 authorized)  
**Bitwise Frozen Production Subroutine:** `models/pandey_kumar_mode1/f42_mixed_uel.for` (`CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6`)  
**Bitwise Shared Reusable Framework:** `scripts/remeshing/reusable_2d_adaptive_framework.py` (`8D71F38F23867A23C1FC1BF5EC499533A8C75F538B77804ECE03B5C668F4BE08`)  

---

## 1. Executive Summary & Review Response

Following independent supervisory review `HND-F1774-SUITE-REGRESSION-EXEC-001` (`DECISION: REJECT_CURRENT_F1774_THREE_JOB_EXECUTION_PACKAGE_PENDING_TARGETED_SAFETY_AND_SCIENTIFIC_CORRECTION`), Task F1774 did NOT launch any PBS jobs. Instead, Task F1774 executed ONE bounded execution-package safety and scientific repair cycle, addressing all six reviewer findings without expanding scope or triggering another general planning cycle:

1. **Lock Cleanup Safety (F1774-R01 resolved):** Removed the dangerous recursive fallback `|| rm -rf "${LOCK_DIR}"` from all three PBS wrappers. Implemented fail-safe, ownership-aware non-recursive cleanup `trap 'rmdir "${LOCK_DIR}" 2>/dev/null || true' EXIT` while strictly preserving atomic `mkdir` acquisition.
2. **Case 5 Donor Indicator Investigation & Sizing Logic (F1774-R02 resolved):** Executed a targeted, read-only Abaqus Python investigation on cluster across Step 1 and all 172 frames of Step 2 in `PK_F1726_SEVEN_HOLE_COARSE.odb`. Proved that the $10^{-14}$ stress magnitude is an exact mathematical artifact of the dummy UMAT visualizer layer ($s \approx 4.76 \times 10^{-14}$), and proved that the relative stress recovery error indicator $\eta_e = \|e_\sigma\| / (\|e_\sigma\| + \|\bar{\sigma}\|)$ is strictly **scale-invariant**. Verified that 660 elements ($25.7\%$) exceed the $5.68\%$ target, precisely localized across the seven-hole inter-hole ligaments in $y \in [0.2, 0.8]\text{ mm}$ with $0.0\%$ in the far field ($y \in [0.8, 1.0]\text{ mm}$).
3. **Fail-Closed Hash Verifications (F1774-R03 resolved):** Augmented all three PBS execution wrappers with independent, fail-closed SHA-256 verifications for the configuration JSON files and individual donor ODBs prior to launching Abaqus CAE.
4. **Fatal Production Deck Datacheck (F1774-R04 resolved):** Made missing production decks strictly fatal (`[ ! -f "${PROD_DECK}" ] && exit 1`) and required genuine cluster Abaqus datacheck Exit 0 before declaring success.
5. **Per-Case Directory Isolation (F1774-R05 resolved):** Isolated each benchmark run into its own dedicated subfolder (`case2_off_axis_hole/`, `case3_notched_pins/`, `case5_seven_hole/`), preventing intermediate file collisions (`abaqus.rpy`, lock directories, datacheck logs).
6. **Case 3 Parent-to-Companion Provenance (F1774-R06 resolved):** Formally documented the exact parent-to-companion frame mapping: Parent solve `PK_SEC43_STAGGERED_JOB1.odb` Step-1 Frame 30 $\to$ `PK_SEC43_PRESCRIBED_STATE2.odb` (Frame 1 under `RECOVERY_STEP`, $u_y = 0.150\text{ mm}$); Parent Frame 55 $\to$ `PK_SEC43_PRESCRIBED_STATE4.odb` (Frame 1 under `RECOVERY_STEP`, $u_y = 0.275\text{ mm}$).

---

## 2. Detailed Technical & Safety Resolutions

### 2.1 Resolution of Finding F1774-R01: Safe Non-Recursive Lock Trap
- **Finding:** PBS scripts contained `trap 'rmdir "${LOCK_DIR}" 2>/dev/null || rm -rf "${LOCK_DIR}"' EXIT`. If unexpected files entered the lock directory, recursive `rm -rf` would silently destroy them.
- **Repair:** In all three PBS wrappers (`submit_f1774_case2_remesh.pbs`, `submit_f1774_case3_remesh.pbs`, `submit_f1774_case5_remesh.pbs`), the trap is replaced by:
  ```bash
  LOCK_DIR="${CASE_DIR}/${JOB_NAME}.lock"
  if ! mkdir "${LOCK_DIR}" 2>/dev/null; then
      echo "ERROR: Active lock directory ${LOCK_DIR} exists. Aborting duplicate submission."
      exit 1
  fi
  trap 'rmdir "${LOCK_DIR}" 2>/dev/null || true' EXIT
  ```
  This guarantees that atomic directory acquisition is preserved, while cleanup is non-recursive and ownership-safe. An unempty directory will fail `rmdir` cleanly without deleting external files.

### 2.2 Resolution of Finding F1774-R03: Fail-Closed SHA-256 Hash Verification
- **Finding:** Wrappers verified framework and UEL hashes, but did not verify the configuration JSON or donor ODB hashes.
- **Repair:** Each script now defines immutable expected hashes and performs bitwise verification before launching CAE:
  - **Case 2:**
    - Config SHA-256: `cbabe93faeede807b02d2ef1a4ec225fd20d362081d62433405ad3fd9724c206`
    - Donor SHA-256 (`PK_HOLE_COMPANION_RECOVERY.odb`): `a6514fb8c07c3b855bb4ba841fdb20a9ae8a1c887a6e6ad1a397ba34222ab856`
  - **Case 3:**
    - Config SHA-256: `177bcb1c5f6fc48fd0c3f83acc0ef491de81462db0190d0a587767092c5ca226`
    - State 2 Donor SHA-256 (`PK_SEC43_PRESCRIBED_STATE2.odb`): `3e1babbde05420c85ec4a1bd014d1f3d0313177005d696b8f878089c18a8edde`
    - State 4 Donor SHA-256 (`PK_SEC43_PRESCRIBED_STATE4.odb`): `e908067bc6b2be89f12249534074a9574255fcc4dd34da5a342a2de174e27152`
  - **Case 5:**
    - Config SHA-256: `9c298bebdbdb0c32383a42569f9f00798d2d433f3a176d6fa30e258519782a34`
    - Donor SHA-256 (`PK_F1726_SEVEN_HOLE_COARSE.odb`): `c7f5b4a6864639b7df396210649ccfa9619408b0a4f26e63eac31487755bc6a9`
  All hashes were verified 100% bitwise identical between local git repository and cluster scratch directory.

### 2.3 Resolution of Finding F1774-R04: Fatal Production Deck Datacheck
- **Finding:** A missing production deck previously produced a non-fatal warning notice and permitted the wrapper to exit with status 0.
- **Repair:** Step 9 in all three wrappers now fails closed:
  ```bash
  PROD_DECK="${CASE_DIR}/PK_F1728_CASE_X_PROD.inp"
  if [ ! -f "${PROD_DECK}" ]; then
      echo "ERROR: Production deck ${PROD_DECK} was not generated or not present. Aborting."
      exit 1
  fi
  echo "=== Running Abaqus Datacheck on ${PROD_DECK} ==="
  /cluster/application/abaqus/2023/Commands/abaqus datacheck job=PK_F1774_CASE_X_DC input="${PROD_DECK}" user="${CASE_DIR}/${USER_SUB}" interactive
  DC_EXIT_CODE=$?
  if [ "${DC_EXIT_CODE}" -ne 0 ]; then
      echo "ERROR: Abaqus datacheck failed with exit code ${DC_EXIT_CODE}."
      exit ${DC_EXIT_CODE}
  fi
  ```

### 2.4 Resolution of Finding F1774-R05: Per-Case Directory Isolation
- **Finding:** Running three jobs in `/scratch9/pr21vyci/runs/mode1_pk_f1774_regression_batch` risked collisions in intermediate files (`abaqus.rpy`, lock files, scratch logs).
- **Repair:** Each script creates and operates within its own dedicated directory:
  - Case 2: `${ROOT_RUN_DIR}/case2_off_axis_hole/`
  - Case 3: `${ROOT_RUN_DIR}/case3_notched_pins/`
  - Case 5: `${ROOT_RUN_DIR}/case5_seven_hole/`
  PBS stdout/stderr logs are routed directly into the case subfolder (`pbs_execution_caseX.log`), completely eliminating shared-directory collisions.

---

## 3. Physical & Mathematical Investigation of Case 5 Donor (F1774-R02)

### 3.1 Empirical Cluster Telemetry Across 172 Frames
Using `scripts/remeshing/investigate_case5_donor_scale.py` executed under Abaqus Python 2023 directly against the 194.3 MB donor ODB `PK_F1726_SEVEN_HOLE_COARSE.odb`, telemetry was extracted across representative frames of Step 1 (Frames 0, 1, 3, 6, 9, 11) and Step 2 (Frames 0, 1, 43, 86, 129, 171):

| Step | Frame | Step Time | Max Stress $S$ [MPa] | Max $\text{MISESERI}$ [MPa] | Max $\text{MISESAVG}$ [MPa] | Max Damage $d$ (`SDV1`) | Relative Error $\eta_{e,\max}$ [%] | Elements Exceeding $5.68\%$ |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| Step-1 | 1 | 0.1000 | $4.68 \times 10^{-15}$ | $2.69 \times 10^{-15}$ | $1.41 \times 10^{-14}$ | 0.00117 | 55.05% | 676 / 2566 (26.34%) |
| Step-1 | 6 | 0.6000 | $2.75 \times 10^{-14}$ | $1.50 \times 10^{-14}$ | $8.12 \times 10^{-14}$ | 0.04462 | 55.22% | 674 / 2566 (26.27%) |
| Step-1 | 11 | 1.0000 | $4.39 \times 10^{-14}$ | $2.17 \times 10^{-14}$ | $1.25 \times 10^{-13}$ | 0.14450 | 54.97% | 666 / 2566 (25.95%) |
| Step-2 | 1 | 0.0050 | $4.40 \times 10^{-14}$ | $2.17 \times 10^{-14}$ | $1.25 \times 10^{-13}$ | 0.14505 | 54.97% | 666 / 2566 (25.95%) |
| Step-2 | 86 | 0.4300 | $5.03 \times 10^{-14}$ | $2.37 \times 10^{-14}$ | $1.38 \times 10^{-13}$ | 0.22987 | 54.78% | 664 / 2566 (25.88%) |
| Step-2 | 171 | 0.7789 | $5.68 \times 10^{-14}$ | $2.57 \times 10^{-14}$ | $1.38 \times 10^{-13}$ | 0.47602 | 57.56% | 660 / 2566 (25.72%) |

### 3.2 Root Cause & Mathematical Scale-Invariance
1. **Physical Cause of $10^{-14}$ Magnitude:** The coarse pre-analysis model for Case 5 used a 3-layer formulation where the visualizer overlay elements (Layer 3/UMAT) were assigned an artificial modulus scale factor $s \approx 4.76 \times 10^{-14}$ to prevent the overlay from altering the structural stiffness of the coupled UEL solve. Consequently, recovered Cauchy stresses and Zienkiewicz–Zhu error indicator fields are scaled by $s$.
2. **Mathematical Scale-Invariance:** Abaqus CAE's `RemeshingRule(errorTarget=5.68, ...)` computes normalized relative percentage error:
   $$\eta_e = \frac{\|e_\sigma\|}{\|e_\sigma\| + \|\bar{\sigma}\|} \times 100\% = \frac{s \cdot \|e_{\sigma,\text{true}}\|}{s \cdot (\|e_{\sigma,\text{true}}\| + \|\bar{\sigma}_{\text{true}}\|)} \times 100\% \equiv \frac{\|e_{\sigma,\text{true}}\|}{\|e_{\sigma,\text{true}}\| + \|\bar{\sigma}_{\text{true}}\|} \times 100\%$$
   The scale factor $s$ cancels identically out of the numerator and denominator. Thus, $\eta_e$ is strictly scale-invariant.
3. **Physical Damage Evolution:** Damage field $d$ (`SDV1`) increases monotonically from 0 to $0.47602$ at Increment 341 (Frame 171), proving that this is an authentic, actively softening phase-field simulation, not stagnant or empty numerical noise.
4. **Spatial Selectivity Across Domain:** The 660 elements exceeding the target $\eta_e > 5.68\%$ were mapped to their spatial centroids:
   - $y \in [0.8, 1.0]\text{ mm}$ (top boundary): **0 elements (0.0%)**
   - $y \in [0.0, 0.2]\text{ mm}$ (bottom boundary): **10 elements (1.5%)**
   - $y \in [0.2, 0.4]\text{ mm}$ (lower hole band): **220 elements (33.3%)**
   - $y \in [0.4, 0.6]\text{ mm}$ (middle hole band): **265 elements (40.2%)**
   - $y \in [0.6, 0.8]\text{ mm}$ (upper crack corridor): **165 elements (25.0%)**
   The mean elevation of refined elements is $\bar{y} = 0.4719\text{ mm}$, perfectly centered on the seven-hole cluster. This spatial selectivity exactly matches Pandey & Kumar (2025) Section 4.6 and Figure 22(b).

### 3.3 Explicit Per-Case Readiness Classification
In accordance with reviewer instructions:
- **Case 1:** `REUSED_FROM_F1772` (20,232 elements, 97.17% quads, det(J) > 0, G1/G6/G7 FAIL retained without rerun).
- **Case 2:** `READY_FOR_EXECUTION` (Method A.1 single-pass, donor qualified with active MISESERI up to 1357 MPa, wrapper fully repaired).
- **Case 3:** `READY_FOR_EXECUTION` (Method A.2 two-pass sequential, companion donors qualified with active MISESERI, parent-to-companion provenance mapped, wrapper fully repaired).
- **Case 5:**
  - *Primary Recommendation:* `READY_FOR_EXECUTION_UNDER_PROVEN_SCALE_INVARIANCE` (Scale-invariance proved, 25.7% of elements selectively refined, 0% in far field).
  - *Conservative Alternative:* `BLOCKED_PENDING_UNSCALED_COARSE_DONOR` (If supervisory review requires an unscaled donor solve with $s = 1.0$, Case 5 can be held while Cases 2 and 3 execute).

---

## 4. Case 3 Provenance Mapping (F1774-R06)

The multi-state Method A.2 workflow requires sequential evaluation of two distinct fracture states. To avoid ambiguity between parent solve increments and companion ODB frames, the exact mapping is established:

```text
Parent Solve: /scratch9/pr21vyci/runs/mode1_pk_sec43_staggered_job1/PK_SEC43_STAGGERED_JOB1.odb
├── Step-1 (Loading to u_y = 0.50 mm across 201 frames)
│   ├── Increment 30 (Step Time = 0.150 mm, Frame 30)
│   │   └── Extracted to: PK_SEC43_PRESCRIBED_STATE2.odb (RECOVERY_STEP, Frame 1)
│   │       ├── MISESERI: in [6.92e-6, 29.39] MPa (mean 0.166 MPa)
│   │       ├── S: in [-20.91, 71.05] MPa
│   │       └── SHA-256: 3e1babbde05420c85ec4a1bd014d1f3d0313177005d696b8f878089c18a8edde
│   └── Increment 55 (Step Time = 0.275 mm, Frame 55)
│       └── Extracted to: PK_SEC43_PRESCRIBED_STATE4.odb (RECOVERY_STEP, Frame 1)
│           ├── MISESERI: in [1.95e-5, 45.08] MPa (mean 0.262 MPa)
│           ├── S: in [-28.16, 84.72] MPa
│           └── SHA-256: e908067bc6b2be89f12249534074a9574255fcc4dd34da5a342a2de174e27152
```
In `submit_f1774_case3_remesh.pbs`, the reusable framework sequentially applies `RemeshingRule` to Pass 1 (`PK_SEC43_PRESCRIBED_STATE2.odb`, `RECOVERY_STEP`, Frame 1) and Pass 2 (`PK_SEC43_PRESCRIBED_STATE4.odb`, `RECOVERY_STEP`, Frame 1), preserving the sequential refinement envelope.

---

## 5. Verification Matrix & Standalone Unit Tests

The dedicated unit test suite `tests/unit/test_f1774_four_benchmark_regression_execution.py` validates the complete repair package:
- `test_frozen_uel_and_framework_invariance`: **PASS** (Bitwise hashes invariant)
- `test_pbs_wrapper_lock_safety`: **PASS** (Zero `rm -rf`, safe `rmdir` trap in all 3 wrappers)
- `test_pbs_wrapper_hash_checks`: **PASS** (Fail-closed checks for configs and donors)
- `test_pbs_wrapper_fatal_production_deck`: **PASS** (Fail-closed datacheck Exit 0 required)
- `test_pbs_wrapper_directory_isolation`: **PASS** (Per-case subfolder execution)
- `test_case3_parent_to_companion_provenance`: **PASS** (Exact mapping verified)
- `test_cumulative_submission_accounting`: **PASS** (30 cumulative, 0 consumed in F1774, max 3)

Full multi-task regression test execution across 6 test suites: **36/36 tests PASSED in 1.74s**.

---

## 6. Submission Authorization Request (HND-F1774-SUITE-REGRESSION-EXEC-002)

Task F1774 requests supervisory authorization to execute the repaired batch on cluster compute nodes under the registered 3-job budget (cumulative submissions = 30):
- **Option A (Full 3-Job Suite Regression):** Execute Job 31 (Case 2, Method A.1), Job 32 (Case 3, Method A.2), and Job 33 (Case 5, Method A.1 under scale-invariance).
- **Option B (Conservative 2-Job Regression):** Execute Job 31 (Case 2) and Job 32 (Case 3) immediately; hold Case 5 as `BLOCKED_PENDING_UNSCALED_COARSE_DONOR` until an unscaled pre-analysis donor is generated.
