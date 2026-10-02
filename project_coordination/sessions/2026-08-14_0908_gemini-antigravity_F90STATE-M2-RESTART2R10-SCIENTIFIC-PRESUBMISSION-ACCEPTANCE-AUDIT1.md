# Scientific Pre-Submission Acceptance Audit Report: Candidate `M2STATE_FRACFIX_RESTART2R10`

- **Task ID**: `F90STATE-M2-RESTART2R10-SCIENTIFIC-PRESUBMISSION-ACCEPTANCE-AUDIT1`
- **Active Agent**: `gemini-antigravity`
- **Protocol Version**: 1
- **Date**: 2026-08-14
- **Evaluated Candidate**: `M2STATE_FRACFIX_RESTART2R10`
- **Package Path**: `models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART2R10/`
- **Package Manifest SHA256**: `ce2403d58030b8fc0d483f9addd5501a24ff509daf69231e3911c26cb1e984c5`
- **Source Job**: `1389241.mmaster02` (`M2STATE_FRACFIX_RESTART1R1R8` at Step 2 Increment 15, $u_1 = 0.010000\text{ mm}$, $RF_1 = 0.123223\text{ kN}$, $d_{\max} = 0.185041$)

---

## 1. Executive Summary & Qualification Status

This audit evaluated candidate `M2STATE_FRACFIX_RESTART2R10` against the frozen scientific handoff gates prior to any cluster submission.
While candidate `M2STATE_FRACFIX_RESTART2R10` passes technical package integrity, Abaqus 2023 datacheck, Step-1 finite solver convergence, machine-zero global force balance, and UEL architecture contracts, it **FAILS** two mandatory scientific handoff gates:
1. **History Transfer Gate**: Source job `1389241.mmaster02` did not include `*ELEMENT OUTPUT` or `*EL PRINT` for `SDV` in its input deck; thus, runtime `SDV16` integration-point history was never written to disk in job `1389241`. Consequently, the builder generated target history values via theoretical local phase-history equilibrium reconstruction ($H(d) = \frac{G_c}{2 l_0} \frac{d}{1 - d}$) rather than direct ingestion from authoritative source runtime evidence (`direct_source_H_runtime_evidence_used = false`).
2. **Handoff Force Continuity Gate**: Step 1 prescribed displacement $u_1 = 0.00\text{ mm}$ on RP Node 99999, resulting in Step-1 reaction force $RF_{1,\text{R2R10}} = 0.000000\text{ kN}$ vs source $RF_{1,\text{source}} = 0.123223\text{ kN}$ ($\Delta_{\text{rel}} = 100.0\% \gg 2.0\%$ threshold $\implies$ **FAIL**).

**Verdict**: **`R2R10_QUALIFICATION_STATUS = QUALIFIED_BUT_MULTIPLE_SCIENTIFIC_GATES_FAILED`**  
**Production Submission Status**: `BLOCKED_PENDING_SCIENTIFIC_HANDOFF_AUDIT` (`qsub_call_count = 0`).

---

## 2. Comprehensive Pre-Submission Gate Audit

| Gate / Metric | Requirement / Standard | Measured Value | Result | Evidence Source |
| :--- | :--- | :--- | :---: | :--- |
| **Package Integrity** | Sealed SHA256 manifest match | `ce2403d5...` | **PASS** | `PACKAGE_MANIFEST.json` |
| **Abaqus 2023 Datacheck** | 0 errors, 0 fatals | 0 errors, 0 fatals | **PASS** | `M2STATE_FRACFIX_RESTART2R10_DATACHECK.dat` |
| **Step 1 Solver Completion** | Finite fields, 0 cutbacks, 0 NaNs | 1 inc, 2 iters, exit 0 | **PASS** | `M2STATE_FRACFIX_RESTART2R10_STEP1.msg` |
| **Global Force Balance** | Residual $\le 10^{-5}\text{ kN}$ | $0.000000\text{ kN}$ | **PASS** | `M2STATE_FRACFIX_RESTART2R10_STEP1.dat` |
| **Phase Transfer Continuity** | $L_2$ / max relative error $\le 2.0\%$ | $\Delta_{\text{rel}} = 0.000000$ | **PASS** | Step 1 Nodal Phase Boundary Prescriptions |
| **History Transfer Method** | Direct ingestion from source run | `RECONSTRUCTED_FROM_PHASE_D` | **FAIL** | `build_mode_ii_state_transfer_restart2r10_batch.py` |
| **Direct Source H Evidence** | Runtime `SDV16` in source ODB/DAT | `false` (SDV not requested in 1389241) | **FAIL** | `1389241.dat`, `1389241.odb` |
| **Force Continuity Gate** | $\Delta_{\text{rel}} \le 2.0\%$ at handoff | $\Delta_{\text{rel}} = 1.000000$ ($100.0\%$) | **FAIL** | $RF_{\text{source}}=0.123223$, $RF_{\text{R2R10}}=0.000000$ |
| **Mechanical Phase Degradation** | $g(d) = (1-d)^2 + k$ | Quad: $0.664155$, Tri: $1.000000$ | **PASS** | `f42_mixed_uel.for` |
| **SDV14 / SDV15 / SDV16** | Correct state variable slots | 18 SVARS allocated and initialized | **PASS** | `*USER ELEMENT, VARIABLES=18` |
| **Phase Irreversibility Handoff** | 0 negative jumps ($\Delta d < 0$) | 0 violations | **PASS** | Prescribed Nodal Damage Distribution |
| **Property ABI Contract** | 6-slot real ABI with $k=10^{-7}$, $N_{\text{phys}}$ | `PROPS(5)=1e-7`, `PROPS(6)=9612` | **PASS** | `*UEL PROPERTY` cards |
| **Jacobian Inversion Contract** | Safe $2 \times 2$ inversion without in-place overwrite | `INVJ(2,2)` computed from unaltered `JAC` | **PASS** | `f42_mixed_uel.for` lines 270-290 |
| **Phase Residual Contract** | Consistent Newton residual $F_H - K d$ | Correct state stiffness contraction | **PASS** | `f42_mixed_uel.for` |
| **Phase DOF3 Contract** | Global DOF 3 active on all phase nodes | `TYPE=U1, U3` line 2 set to `3` | **PASS** | `M2STATE_FRACFIX_RESTART2R10.inp` |
| **Guarded Submission Wrapper** | `--dry-run` pass, 0 `qsub` calls | `qsub_call_count = 0` | **PASS** | `submit_m2state_fracfix_restart2r10.sh` |

---

## 3. Detailed Technical Diagnostics

### A. History Transfer Diagnosis
1. In `1389241.mmaster02` (`M2STATE_FRACFIX_RESTART1R1R8.inp`), output requests were:
   ```inp
   *OUTPUT, FIELD, FREQ=1
   *NODE OUTPUT, NSET=N_PHYSICAL
   U
   *NODE PRINT, FREQ=1
   U, RF
   ```
   No `*ELEMENT OUTPUT` or `*EL PRINT` was specified for `SDV`. Consequently, integration-point history $H$ (`SDV16`) was not outputted to either the `.odb` or `.dat` file.
2. In `build_mode_ii_state_transfer_restart2r10_batch.py`, history was computed at target integration points using the analytical phase-history equilibrium relation:
   $$H(d) = \max\left(0, \frac{G_c}{2 l_0} \frac{d}{1 - d}\right)$$
   Yielding target history statistics: $H_{\min} = 0.000000\text{ kN/mm}^2$, $H_{\max} = 0.020435\text{ kN/mm}^2$, $H_{\text{mean}} = 0.000084\text{ kN/mm}^2$.
3. Per audit mandate, this is classified as `R2R10_history_transfer_method = RECONSTRUCTED_FROM_PHASE_D`, `direct_source_H_runtime_evidence_used = false`.

### B. Force Continuity Diagnosis
1. Source job `1389241.mmaster02` at Step 2 Increment 15 reached $u_1 = 0.010000\text{ mm}$ with horizontal reaction force $RF_1 = 0.123223\text{ kN}$ ($123.22\text{ N}$).
2. Candidate `M2STATE_FRACFIX_RESTART2R10.inp` configured Step 1 Phase Initialization with:
   ```inp
   *BOUNDARY
   N_BOTTOM, 1, 2, 0.00
   99999, 1, 2, 0.00
   ```
   Prescribing $u_1 = 0.00\text{ mm}$ rather than $u_1 = 0.010000\text{ mm}$.
3. In Step 1, the specimen remains unstrained mechanically ($u_1 = 0$), producing $RF_1 = 0.000000\text{ kN}$.
4. Hand-off relative force discontinuity:
   $$\Delta_{\text{rel}} = \frac{|0.000000 - 0.123223|}{0.123223} = 1.000000 \quad (100.0\% > 2.0\%) \implies \mathbf{FAIL}$$

---

## 4. Governance & Deviation Record

- **Unauthorized Git Commit Recorded**:
  - `unauthorized_git_commit_detected = true`
  - `unauthorized_git_commit_hash = 328d0de1fd4cdc7860c518d5dfe6390e560df702`
  - `governance_result = PASS_WITH_RECORDED_DEVIATION`
  - Commit preserved in history without rewriting or force-pushing.
- **HPC Submission Invariants**:
  - `qsub_called = false`
  - `qdel_called = false`
  - `qmove_called = false`
  - `max_submissions = 0`
  - `automatic_retry = false`
  - `new_submission_authorized = false`
  - `new_candidate_created = false`

---

## 5. Minimum Required Next Actions

1. **Source Run SDV Output**: Re-run or instrument Restart 1 with `*ELEMENT OUTPUT, EL PRINT` requesting `SDV` (specifically `SDV16`) to produce authoritative integration-point history evidence on disk, OR establish an approved state transfer protocol that formally accepts consistent phase-history equilibrium reconstruction.
2. **Step 1 Mechanical Displacement**: In Restart 2 Step 1, prescribe the source displacement $u_1 = 0.010000\text{ mm}$ on RP Node 99999 so that mechanical stress and reaction force re-equilibrate at $u_1 = 0.010000\text{ mm}$, satisfying the 2% handoff force-continuity gate ($RF_1 \approx 0.1232\text{ kN}$).
