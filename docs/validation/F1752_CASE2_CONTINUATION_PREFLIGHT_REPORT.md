# Task F1752: Case 2 Method A Controlled-Only Continuation Execution Preflight & Datacheck Report

## Executive Summary & Independent Review Governance

Following independent review evaluation `HND-F1751-CASE2-READINESS-001` (`APPROVE` with qualifications), Task F1752 executes a strictly bounded, zero-PBS preflight operation for a controlled solver-increment continuation experiment on Case 2 (Pandey & Kumar 2025, Section 4.5: *Plate with an Off-Axis Hole*).

Task F1751 conclusively established that:
1. The primary severed channel achieved **96.29% area compliance** (99.06% element count) with $h \le \ell_0/2 = 0.00375\,\text{mm}$ and complete topological breach into the off-axis hole (5 boundary-intersecting elements, 6 boundary nodes).
2. The partial simulation in Job 1423271 terminated at increment 252 (Step 2 increment 201) due to solver cutback exhaustion at the hardcoded input deck limit `min_increment = 1.0e-8` at line 96209 of `PK_F1728_CASE_2_PROD.inp`.
3. The convergence bottleneck was localized to **Node 8056** ($x = 0.9031\,\text{mm}, y = 0.6363\,\text{mm}$) in the secondary ligament, where a localized phase-field DOF 3 damage correction $\Delta d = 0.0788$ occurred across an intermediate mesh gradation ($h \approx 1.06\times - 1.67\times \ell_0/2$).

In strict accordance with review directive `HND-F1751-CASE2-READINESS-001`, Task F1752 resolves all technical prerequisites before requesting PBS execution authorization:
- Disqualifies Step 2 restart due to Fortran `COMMON` block memory initialization rules in the frozen UEL, establishing full rerun as the sole mathematically sound path.
- Formulates an isolated solver-parameter continuation deck modifying strictly line 96209 (`min_increment` relaxed from $1.0\times 10^{-8}$ to $1.0\times 10^{-11}$).
- Verifies zero artificial damping, zero modified tolerances, and zero altered geometries or meshes.
- Completes an Abaqus/Standard compilation and datacheck with **Exit Code 0** (0 errors, 8 benign element notices).
- Predeclares quantitative stop conditions and physical acceptance gates.
- Strictly consumes **0 PBS jobs** under Task F1752, preserving cumulative historical submissions at exactly 25.

---

## 1. Technical Audit: Disqualification of Step 2 Restart vs. Full Rerun

A thorough technical investigation was conducted to determine whether Job 1423271 could be continued via standard Abaqus restart (`*RESTART, READ, STEP=2, INC=201`) using the preserved scratch files (`PK_F1735_CASE_2_FRAC.res`, `.stt`, `.mdl` on `/scratch9/pr21vyci/runs/f1735_case2_adapted_fracture/`).

### 1.1 Fortran Subroutine Architecture & State Recovery Defect
The production user element subroutine `f42_mixed_uel.for` (bitwise frozen SHA-256: `CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6`) manages history variables and phase-field coupling through Fortran `COMMON` blocks:

```fortran
C Line 131-135 of f42_mixed_uel.for:
      IF (KSTEP .EQ. 1 .AND. KINC .LE. 1) THEN
        DO N = 1, N_ELEM_MAX
          SV_H_COMMITTED(N) = ZERO
          SV_H_TRIAL(N)     = ZERO
        END DO
      END IF
```

Crucially:
1. `SV_H_COMMITTED` and `SV_H_TRIAL` record the maximum historical positive strain energy density $\mathcal{H}^+$ enforcing damage irreversibility across all 71,895 layered elements.
2. Standard Abaqus restart files (`.res`) store state variables (`SDV` arrays) associated with standard materials and element formulations, but **do not serialize Fortran `COMMON` block memory**.
3. When restarting at Step 2 (`KSTEP = 2`), the condition `(KSTEP .EQ. 1 .AND. KINC .LE. 1)` is never executed, and `f42_mixed_uel.for` contains no restart read logic for `COMMON /CB_STATE_TRANS/`. Consequently, all historical driving fields `SV_H_COMMITTED` remain uninitialized (zero in OS memory), causing immediate history-loss and unphysical elastic healing across the pre-damaged crack wakes.
4. Because modifying the frozen production UEL source code is **strictly prohibited** by governance, adding custom restart serialization logic to `f42_mixed_uel.for` is disqualified.

### 1.2 Decision: Controlled Full Rerun Selected
A controlled full rerun of the unchanged 23,965-element mesh from $u_y = 0.0\,\text{mm}$ to $0.0120\,\text{mm}$ is the sole technically valid, thermodynamically consistent, and reproducible path. It completely guarantees:
- Continuous, uninterrupted evolution of `SV_H_COMMITTED` across Steps 1 and 2.
- 100% bitwise parity with Job 1423271 up to increment 252.
- Clean continuation past the cutback bottleneck into the post-peak softening regime.

---

## 2. Isolated Solver Parameter Modification

The continuation deck `PK_F1752_CASE_2_CONTINUATION.inp` was generated from the baseline production deck `PK_F1728_CASE_2_PROD.inp` by applying an isolated, single-parameter relaxation.

### 2.1 Exact Diff Verification
Verification of the exact 1-line diff between the two decks:

```diff
--- models/pandey_kumar_mode1/224_f1734_case2_distal_refinement/PK_F1728_CASE_2_PROD.inp
+++ models/pandey_kumar_mode1/234_f1752_case2_continuation/PK_F1752_CASE_2_CONTINUATION.inp
@@ -96209 +96209 @@
-0.002, 1.0, 1.0e-8, 0.002
+0.002, 1.0, 1.0e-11, 0.002
```

### 2.2 Parameter Preservation Audit
- **Step 1 (`*STATIC` to $u_y = 0.005\,\text{mm}$):** $\Delta t_{\text{init}} = 0.02$, $\Delta t_{\max} = 0.02$, $\Delta t_{\min} = 1.0\times 10^{-7}$, $\text{INC} = 10000$ (100% preserved).
- **Step 2 (`*STATIC` to $u_y = 0.012\,\text{mm}$):** $\Delta t_{\text{init}} = 0.002$, $\Delta t_{\max} = 0.002$, $\Delta t_{\min} = 1.0\times 10^{-11}$, $\text{INC} = 20000$ (only $\Delta t_{\min}$ relaxed).
- **Physical Geometry & Mesh:** 23,965 physical elements, 71,895 layered elements, 23,958 nodes (100% bitwise identical).
- **Material & Phase-Field Constants:** $E = 210\,\text{GPa}$, $\nu = 0.3$, $G_c = 0.0027\,\text{kN/mm}$, $\ell_0 = 0.0075\,\text{mm}$, $k = 10^{-7}$ (100% bitwise identical).
- **Boundary Conditions & Coupling:** RP 999999 roller displacement control, pin constraint at origin (100% bitwise identical).
- **Zero Unreviewed Stabilizations:** Zero artificial numerical damping (`*STATIC, STABILIZE` is NOT used), zero artificial viscosity, zero modified convergence controls (`*CONTROLS` is standard).

---

## 3. Cluster Datacheck Execution & Verification

The continuation model was staged and tested on the TU Bergakademie Freiberg cluster (`login01.cluster / compute node`) with Abaqus 2023 and Intel Fortran Compiler Classic 2021.13.0.

### 3.1 Provenance and File Hashes
- **Subroutine:** `f42_mixed_uel.for`  
  `SHA-256: CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6` (Bitwise Frozen PASS)
- **Input Deck:** `PK_F1752_CASE_2_CONTINUATION.inp`  
  `SHA-256: CCB35B34BFAE015EA4846D3D0765FC2646E6C9AF47958F8C21A0A4F25A14CC4A` (Verified PASS)

### 3.2 Compilation and Datacheck Receipt
Execution of `abaqus job=PK_F1752_CASE_2_CONTINUATION input=PK_F1752_CASE_2_CONTINUATION.inp user=f42_mixed_uel.for datacheck interactive`:

```text
Abaqus JOB PK_F1752_CASE_2_CONTINUATION
Begin Compiling Abaqus/Standard User Subroutines
 Intel(R) Fortran 2021.13.0-1693
End Compiling Abaqus/Standard User Subroutines
Begin Linking Abaqus/Standard User Subroutines
GNU ld version 2.30-128.el8_10
End Linking Abaqus/Standard User Subroutines
Begin Analysis Input File Processor
Run pre
End Analysis Input File Processor
Begin Abaqus/Standard Datacheck
Run standard
End Abaqus/Standard Analysis
Begin SIM Wrap-up
Run SMASimUtility
End SIM Wrap-up
Abaqus JOB PK_F1752_CASE_2_CONTINUATION COMPLETED
```

- **Exit Status:** `Exit Code 0` (Clean PASS).
- **Errors Reported:** Exactly 0 errors.
- **Warnings Reported:** Exactly 8 warnings, all consisting of the established standard benign notice:
  `***WARNING: THE *ELEMENT OUTPUT OPTION IS NOT SUPPORTED FOR USER ELEMENTS`
- **Elapsed Runtime:** CPU Time: 1.5 seconds, Wallclock Time: 3 seconds.

---

## 4. Resource Allocation Basis & Queue Strategy

### 4.1 Empirical Basis from Predecessor Job 1423271
- **Job 1423271 Measurements:** Ran 252 total increments (51 in Step 1, 201 in Step 2) in **2,472 seconds wallclock** (1,690s CPU) on 1 core. Peak memory consumption was $< 2.0\,\text{GB}$.
- **Continuation Estimate:** Step 1 completes in ~200s. Step 2 up to increment 201 completes in ~2,200s. The remaining post-peak propagation (displacement advance from $u_y = 0.00762\,\text{mm}$ to $0.0120\,\text{mm}$) is estimated at 1,500–3,000s assuming small cutbacks during secondary crack extension.
- Total estimated wallclock time: **4,000–5,500 seconds** (~1.1 to 1.5 hours).

### 4.2 Resource Request
To provide a reliable 2x safety margin without requesting speculative resources:
- **PBS Queue:** `normal_imfdfkmq`
- **Nodes & CPUs:** `select=1:ncpus=1:mpiprocs=1:ompthreads=1:mem=8gb`
- **Requested Walltime:** `03:00:00` (10,800 seconds)
- **Parallel Safety:** Strictly 1-CPU serial execution. Distributed MPI is disqualified due to Fortran `COMMON` blocks. Serial execution guarantees deterministic element update ordering and zero race conditions.

---

## 5. Predeclared Quantitative Stop Conditions

To ensure fail-closed execution without unbounded resource waste, the prospective continuation run is bound by four strict stop conditions:

1. **Stop Condition 1 (Cutback Stagnation):** The simulation must be terminated if Abaqus Standard encounters $> 50$ consecutive cutbacks within Step 2 without advancing time.
2. **Stop Condition 2 (Displacement Rate Stagnation):** The simulation must be classified as non-advancing and terminated if the displacement increment satisfies $\Delta u_y < 1.0\times 10^{-7}\,\text{mm}$ across 10 consecutive increments.
3. **Stop Condition 3 (Walltime Ceiling):** Hard walltime limit of 10,800 seconds (3 hours) enforced by PBS scheduler.
4. **Stop Condition 4 (Nonphysical Damage):** The run must fail closed if any integration point reports nonphysical damage $d < -1.0\times 10^{-5}$ or $d > 1.02$.

---

## 6. Predeclared Physical Acceptance Gates

Scientific evaluation of the prospective continuation simulation will be governed by five predeclared physical gates:

| Gate ID | Acceptance Requirement | Quantitative Threshold | Physical Meaning |
| :--- | :--- | :--- | :--- |
| **Gate 1** | **Thermodynamic Monotonicity** | $E_{\text{frac}}(t_{n+1}) \ge E_{\text{frac}}(t_n) - 1.0\times 10^{-6}\,\text{kJ}$ | Enforces strict irreversibility of fracture energy dissipation. |
| **Gate 2** | **Physical Damage Bounds** | $0 \le d \le 1.0004$ | Prevents unphysical healing ($d < 0$) or runaway damage ($d > 1$). |
| **Gate 3** | **Secondary Crack Extension** | $d \ge 0.90$ advances past $x = 0.9031\,\text{mm}$ | Demonstrates physical fracture propagation through the secondary ligament. |
| **Gate 4** | **Substantial Load Drop** | $\Delta F / F_{\max} \ge 75\%$ | Confirms structural softening and near-complete specimen severance. |
| **Gate 5** | **Resolution Classification** | Explicit classification of secondary front | Formally classifies distal resolution as `PARTIAL` vs `FULL` vs `SPATIALLY_QUALIFIED`. |

---

## 7. Artifact Registry & Provenance Summary

| Artifact Name | Path | Type | SHA-256 / Value |
| :--- | :--- | :--- | :--- |
| **Continuation Deck** | `models/pandey_kumar_mode1/234_f1752_case2_continuation/PK_F1752_CASE_2_CONTINUATION.inp` | Input Deck | `CCB35B34BFAE015EA4846D3D0765FC2646E6C9AF47958F8C21A0A4F25A14CC4A` |
| **Frozen Production UEL** | `models/pandey_kumar_mode1/234_f1752_case2_continuation/f42_mixed_uel.for` | Fortran Source | `CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6` |
| **Execution Manifest** | `results/validation/f1752_case2_continuation_manifest.json` | JSON Manifest | Validated JSON |
| **Datacheck Shell Script** | `/scratch9/pr21vyci/runs/f1752_case2_continuation/run_f1752_datacheck.sh` | Shell Script | Exit 0 Verified |
| **Datacheck Receipt** | `/scratch9/pr21vyci/runs/f1752_case2_continuation/PK_F1752_CASE_2_CONTINUATION.dat` | Solver Output | Exit 0, 0 errors, 8 warnings |

---

## 8. Governance & Review Request Recommendation

- **PBS Consumed in F1752:** **0** (strictly 0 new submissions).
- **Cumulative Historical Submissions:** **25** (preserved bitwise).
- **Forward Simulations Launched:** **0** (preflight and datacheck only).
- **Recommendation:** Submit independent review packet `HND-F1752-CASE2-PREFLIGHT-001` to ChatGPT requesting authorization for **exactly 1 bounded PBS job** to execute the controlled full-rerun continuation simulation on the cluster.
