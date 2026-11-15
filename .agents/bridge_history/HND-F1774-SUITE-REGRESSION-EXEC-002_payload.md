# HND-F1774-SUITE-REGRESSION-EXEC-002 Review Authorization Payload
## Task F1774 Execution Package Safety & Scientific Repair Submission

**Correlation ID:** `HND-F1774-SUITE-REGRESSION-EXEC-002`  
**Predecessor Correlation ID:** `HND-F1774-SUITE-REGRESSION-EXEC-001` (Direct resolution of Findings F1774-R01 to F1774-R06)  
**Task ID:** `F1774-FOUR-BENCHMARK-METHOD-A-REGRESSION-EXECUTION`  
**Classification:** `FOUR_BENCHMARK_REGRESSION_EXECUTION`  
**Assigned Agent:** `gemini-antigravity`  
**Cumulative PBS Submissions Accounted:** 30 (0 consumed under F1774, maximum 3 authorized)  

---

### 1. Direct Resolution of Supervisory Review Findings (F1774-R01 through F1774-R06)

| Finding ID | Severity | Status | Resolution Summary & Provenance Reference |
| :--- | :---: | :---: | :--- |
| **F1774-R01** | HIGH | **RESOLVED** | Removed recursive `|| rm -rf "${LOCK_DIR}"` fallback from all three PBS wrappers. Implemented fail-safe non-recursive cleanup `trap 'rmdir "${LOCK_DIR}" 2>/dev/null || true' EXIT` while strictly preserving atomic `mkdir` acquisition. |
| **F1774-R02** | HIGH | **INVESTIGATED & QUALIFIED** | Executed targeted read-only Abaqus Python investigation on cluster across Step 1 and all 172 frames of Step 2 in `PK_F1726_SEVEN_HOLE_COARSE.odb`. Proved $10^{-14}$ stress magnitude is an exact mathematical artifact of the dummy UMAT visualizer layer ($s \approx 4.76 \times 10^{-14}$). Proved that relative stress-recovery error indicator $\eta_e = \|e_\sigma\| / (\|e_\sigma\| + \|\bar{\sigma}\|)$ is strictly **scale-invariant**. Verified 660 elements ($25.7\%$) exceed $5.68\%$ target, precisely localized across inter-hole ligaments in $y \in [0.2, 0.8]\text{ mm}$ ($0.0\%$ in far-field $y \in [0.8, 1.0]\text{ mm}$). |
| **F1774-R03** | MEDIUM | **RESOLVED** | Added fail-closed SHA-256 verifications for configuration JSON files and donor ODBs prior to CAE launch in all three wrappers. |
| **F1774-R04** | HIGH | **RESOLVED** | Made missing production decks fatal (`[ ! -f "${PROD_DECK}" ] && exit 1`) and required genuine cluster Abaqus datacheck Exit 0 before declaring success. |
| **F1774-R05** | MEDIUM | **RESOLVED** | Isolated each benchmark into dedicated subfolders (`case2_off_axis_hole/`, `case3_notched_pins/`, `case5_seven_hole/`), completely eliminating intermediate file and log collisions. |
| **F1774-R06** | MEDIUM | **RESOLVED** | Formally documented and preserved parent-to-companion frame mapping: Parent solve `PK_SEC43_STAGGERED_JOB1.odb` Step-1 Frame 30 $\to$ `PK_SEC43_PRESCRIBED_STATE2.odb` (Frame 1 under `RECOVERY_STEP`, $u_y = 0.150\text{ mm}$); Parent Frame 55 $\to$ `PK_SEC43_PRESCRIBED_STATE4.odb` (Frame 1 under `RECOVERY_STEP`, $u_y = 0.275\text{ mm}$). |

---

### 2. Immutable Bitwise Hash Verifications (100% Match Between Git Repository and Cluster Staging)

1. **Frozen Production UEL (`models/pandey_kumar_mode1/f42_mixed_uel.for`):**  
   `ce8d5edcd2911dcb018bb15275271f874e7ea62b8fb48cf4a8297469a83acdd6` (100% bitwise match)
2. **Shared Reusable Framework (`scripts/remeshing/reusable_2d_adaptive_framework.py`):**  
   `8d71f38f23867a23c1fc1bf5ec499533a8c75f538b77804ece03b5c668f4be08` (100% bitwise match)
3. **Repaired PBS Execution Wrappers:**  
   - Case 2 (`submit_f1774_case2_remesh.pbs`): `7e298a1653e632bc4be14163c984124eee1befd75b3982745d6b78cd4dcdb339`  
   - Case 3 (`submit_f1774_case3_remesh.pbs`): `998e2b61328e8937b7768560fa56d5e0ec87a4c156b6faa79ac47020c70d5d2a`  
   - Case 5 (`submit_f1774_case5_remesh.pbs`): `925b135488279fbf081b64fab1f1c0c12ee7636b12fa102cfb9acfe56bd0c427`  
4. **Configuration JSON Files:**  
   - Case 2 (`f1728_case2_off_axis_hole.json`): `cbabe93faeede807b02d2ef1a4ec225fd20d362081d62433405ad3fd9724c206`  
   - Case 3 (`f1728_case3_notched_plate_pins.json`): `177bcb1c5f6fc48fd0c3f83acc0ef491de81462db0190d0a587767092c5ca226`  
   - Case 5 (`f1728_case5_seven_hole.json`): `9c298bebdbdb0c32383a42569f9f00798d2d433f3a176d6fa30e258519782a34`  
5. **Donor ODB Files:**  
   - Case 2 (`PK_HOLE_COMPANION_RECOVERY.odb`, 922 KB): `a6514fb8c07c3b855bb4ba841fdb20a9ae8a1c887a6e6ad1a397ba34222ab856`  
   - Case 3 State 2 (`PK_SEC43_PRESCRIBED_STATE2.odb`, 1.75 MB): `3e1babbde05420c85ec4a1bd014d1f3d0313177005d696b8f878089c18a8edde`  
   - Case 3 State 4 (`PK_SEC43_PRESCRIBED_STATE4.odb`, 1.75 MB): `e908067bc6b2be89f12249534074a9574255fcc4dd34da5a342a2de174e27152`  
   - Case 5 (`PK_F1726_SEVEN_HOLE_COARSE.odb`, 194.3 MB): `c7f5b4a6864639b7df396210649ccfa9619408b0a4f26e63eac31487755bc6a9`  

---

### 3. Explicit Per-Case Readiness Status & Execution Options

- **Case 1 (BM-1, Mode-I Edge-Cracked Plate):** `REUSED_FROM_F1772`  
  Physical adapted mesh `PK_F1728_CASE_1_ADAPT_PHYS.inp` (20,232 elements, 97.17% quads, min det(J) > 0, mean AR 1.2637) reused without rerun; G1, G6, G7 FAIL and donor G3 Helmholtz oscillation documented and retained.
- **Case 2 (BM-2, Plate with Off-Axis Hole):** `READY_FOR_EXECUTION`  
  Single-pass Method A.1; donor ODB verified with active MISESERI up to 1357 MPa; wrapper fully repaired with fail-closed hash verification and directory isolation.
- **Case 3 (BM-3, Notched Plate with Pins):** `READY_FOR_EXECUTION`  
  Multi-state Method A.2 sequential 2-pass; companion donors verified; parent-to-companion provenance explicitly mapped; wrapper fully repaired.
- **Case 5 (BM-4, Seven-Hole Plate):**  
  - *Status:* `READY_FOR_EXECUTION_UNDER_SCALE_INVARIANCE` (Abaqus relative error $\eta_e$ strictly scale-invariant, 25.7% elements refined, 0% in far field).  
  - *Alternative Decision:* If supervisory review requires an unscaled donor solve ($s = 1.0$), mark Case 5 `BLOCKED_PENDING_UNSCALED_COARSE_DONOR` and approve Option B (Cases 2 and 3 only).

**Authorization Requested:**
- **Option A (3 PBS Submissions):** Authorize launch of Jobs 31 (Case 2), 32 (Case 3), and 33 (Case 5).
- **Option B (2 PBS Submissions):** Authorize launch of Jobs 31 (Case 2) and 32 (Case 3); hold Case 5.
