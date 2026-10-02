# Mode-II Stage-E Numerical Continuation Protocol & Triplet Baseline Submission Record

**Task ID**: `F289PLAN-M2-STAGE-E-NUMERICAL-CONTINUATION-AND-SUBMISSION1`  
**Date**: 18 August 2026  
**Status**: `PROTOCOL_FROZEN / TRIPLET_PACKAGES_QUALIFIED / PREFLIGHT_VERIFIED / JOBS_SUBMITTED_AND_RUNNING / STAGE_E_REMAINS_BLOCKED`  
**Active Agent**: `gemini-antigravity`  

---

## 1. Nonlinear Incrementation Forensics & Root-Cause Synthesis

A detailed comparative audit of `1390447.mmaster02` (Donor Reference), `1390527.mmaster02` (Refined), and `1390528.mmaster02` (Coarsened) established:
1. **Donor Path Traversal**: In `1390447.mmaster02`, traversing the steep snapback load drop between $U_1 = 0.012375\text{ mm}$ and $0.01300\text{ mm}$ required over 400 micro-increments with time step sizes scaling down to $\Delta t \approx 7.3 \times 10^{-7}\text{ s}$. Because each step succeeded in 2–3 attempts, it never exceeded the default 5-attempt limit.
2. **Refined Baseline Abortion (`1390527`)**: With $h = 0.002000\text{ mm}$ ($h/\ell_0 = 0.1333$), the localized damage gradient across the crack face is sharper. At Increment 28 ($U_1 = 0.012584\text{ mm}$), Abaqus attempted 5 cutbacks ($1.88\times 10^{-4} \to 4.69\times 10^{-5} \to 1.17\times 10^{-5} \to 2.93\times 10^{-6} \to 7.33\times 10^{-7}\text{ s}$). Due to the hard-coded default attempt limit ($I_A = 5$), Abaqus terminated at Attempt 6 with `***ERROR: TOO MANY ATTEMPTS MADE FOR THIS INCREMENT` before reaching the converged micro-step regime.
3. **Coarsened Baseline Abortion (`1390528`)**: Traversed 90% of the load drop down to $RF_1 = 0.088173\text{ kN}$ before hitting the same 5-attempt limit at Increment 62.

---

## 2. Frozen Stage-E Numerical Continuation Protocol

To enable standard Newton-Raphson traversal of the post-peak localization branch without altering the physical or phase-field model, the following minimal solver-only continuation protocol is frozen:

```text
======================================================================================================================================================================
Parameter / Field                    Default / Old Value                Frozen Continuation Value          Documented Semantics / Engineering Rationale
-----------------------------------  ---------------------------------  ---------------------------------  -----------------------------------------------------------
*STATIC Line 2 Field 3 (dt_min)      1.0e-9 s                           1.0e-10 s                          Lower minimum increment bound to support 12 geometric cutbacks
*CONTROLS Line 1 Field 1 (I_0)       4 iters                            8 iters                            Equilibrium iteration at which divergence check begins
*CONTROLS Line 1 Field 2 (I_R)       8 iters                            10 iters                           Equilibrium iteration after which alternate residual is used
*CONTROLS Line 1 Field 4 (I_C)       16 iters                           20 iters                           Maximum equilibrium iterations allowed per attempt
*CONTROLS Line 1 Field 8 (I_A)       5 attempts                         12 attempts                        Maximum cutback attempts permitted before error abort
======================================================================================================================================================================
```

### Scientific Model Invariance:
- **No Physical Changes**: Material properties ($E=210\text{ kN/mm}^2, \nu=0.3, G_c=0.0027\text{ kN/mm}, \ell_0=0.015\text{ mm}, k=10^{-7}$), bounded damage $[0,1]$, irreversibility condition, boundary conditions, and mesh discretizations remain completely identical.
- **Pure Numerical Continuation**: This protocol merely permits the equation solver to make additional cutbacks down to $\Delta t \approx 10^{-10}\text{ s}$ to resolve high-gradient equilibrium states rather than aborting prematurely.

---

## 3. Triplet Package Definitions & Qualification Results

Applied identically across all three baseline packages:
1. **`M2CORR_STAGE_E_DONOR_CONTROL_VAL`**: Donor 8,836 quads ($h_{\text{tip}} = 0.003750\text{ mm}$) numerical-control reference.
2. **`M2CORR_STAGE_E_REFINED_TARGET_CONTINUOUS_VAL`**: Refined 33,600 quads ($h_{\text{tip}} = 0.002000\text{ mm}$) baseline.
3. **`M2CORR_STAGE_E_COARSENED_TARGET_CONTINUOUS_VAL`**: Coarsened 8,200 quads ($h_{\text{tip}} = 0.005000\text{ mm}$) baseline.

```text
======================================================================================================================================================================
Qualification Gate                   Donor Reference (1390533)          Refined Baseline (1390534)         Coarsened Baseline (1390535)       Status / Evaluation
-----------------------------------  ---------------------------------  ---------------------------------  ---------------------------------  ------------------------
Semantic One-Difference Deck Check   100% Match (Controls Only)         100% Match (Controls Only)         100% Match (Controls Only)         PASS (Two-layer UEL, identical PROPS)
Physical Quads / Nodes               8,836 quads / 9,074 nodes          33,600 quads / 34,028 nodes        8,200 quads / 8,417 nodes          PASS (Positive Jacobians everywhere)
Resolution Ratio (h_tip / l0)        0.2500 (h_tip = 0.003750 mm)       0.1333 (h_tip = 0.002000 mm)       0.3333 (h_tip = 0.005000 mm)       PASS (All non-pathological)
Launcher Exit Propagation Test       Exited 1 on fail, 0 on success     Exited 1 on fail, 0 on success     Exited 1 on fail, 0 on success     PASS (test_launcher_exit_propagation.py)
Remote Compile & Datacheck           Intel Fortran + Datacheck Exit 0   Intel Fortran + Datacheck Exit 0   Intel Fortran + Datacheck Exit 0   PASS (Abaqus JOB COMPLETED)
Dual-Channel Preflight Smoke Test    Telegram rc=0, Email rc=0          Telegram rc=0, Email rc=0          Telegram rc=0, Email rc=0          PASS (Verified on mlogin01)
======================================================================================================================================================================
```

---

## 4. Package Checksums (SHA-256)

### 1. Donor Reference (`M2CORR_STAGE_E_DONOR_CONTROL_VAL`):
- `M2CORR_STAGE_E_DONOR_CONTROL_VAL.inp`: `c20772164cbd04527e2964f04f71f854ff7dbebc463fd5678caf0bb85f24a853`
- `f44_mixed_uel_restart_stateinit.for`: `62e35f74bbeccd3f5b1ac67312b79211f4ccb75648ae20dbb8985cb577fe1aab`
- `submit_job.pbs`: `3047d04f1418b76c8c454e9bccebf3e414c2438ee2e89fa6e5b417c80521e491`

### 2. Refined Baseline (`M2CORR_STAGE_E_REFINED_TARGET_CONTINUOUS_VAL`):
- `M2CORR_STAGE_E_REFINED_TARGET_CONTINUOUS_VAL.inp`: `a86c99beab326fb68be2274351b6653c76f39900b7ae910a108400dcfaf4cdbc`
- `f44_mixed_uel_restart_stateinit.for`: `62e35f74bbeccd3f5b1ac67312b79211f4ccb75648ae20dbb8985cb577fe1aab`
- `submit_job.pbs`: `2d66af2722a9c147607feb1b8a9c04b9b12d93a72607a85024bb070eb5f3768a`

### 3. Coarsened Baseline (`M2CORR_STAGE_E_COARSENED_TARGET_CONTINUOUS_VAL`):
- `M2CORR_STAGE_E_COARSENED_TARGET_CONTINUOUS_VAL.inp`: `1f82ac3989f6e591f24bdc280d4bbb24941cfbd866ca0e5d2c8648bbf203425a`
- `f44_mixed_uel_restart_stateinit.for`: `62e35f74bbeccd3f5b1ac67312b79211f4ccb75648ae20dbb8985cb577fe1aab`
- `submit_job.pbs`: `11e94f52c0dc43a77552d12059a44fc1e6eea7d626c564062bbe562df5919757`

---

## 5. PBS Scheduler Submission Evidence

Submitted under standing 18 August 2026 authorization:
```text
===================================================================================================================================================================
Job Name                                       PBS Job ID        Mesh Type      Nodes   Quads   h_tip (mm)   h_max (mm)  h_tip/l0  Exec Host / Queue    Status
---------------------------------------------  ----------------  -------------  ------  ------  -----------  ----------  --------  -------------------  -------
M2CORR_STAGE_E_DONOR_CONTROL_VAL               1390533.mmaster02 Donor Ref      9,074   8,836   0.003750     0.025000    0.2500    mnode097/0 (normal)  RUNNING
M2CORR_STAGE_E_REFINED_TARGET_CONTINUOUS_VAL   1390534.mmaster02 Refined Target 34,028  33,600  0.002000     0.020000    0.1333    mnode097/1 (normal)  RUNNING
M2CORR_STAGE_E_COARSENED_TARGET_CONTINUOUS_VAL 1390535.mmaster02 Coarse Target  8,417   8,200   0.005000     0.030000    0.3333    mnode097/2 (normal)  RUNNING
===================================================================================================================================================================
```
- **Login-Node Watcher Daemon**: Active (`PID 1213089` on `mlogin01`) actively tracking all 3 jobs.
- **Diagnostic Control Protocol**: `1390533` serves as the direct numerical reference to verify that the continuation protocol does not introduce non-physical drift relative to `1390447`.

---

## 6. Preserved Scientific Gates

```text
same_mesh_restart_validation = VALIDATED
history_transfer_rule_resolved = true
selected_production_history_operator = HOST_ISOPARAMETRIC_BILINEAR_WITH_LOCAL_GP_BOUNDS_CLAMP
stage_d_nonmatching_transfer_validation = VALIDATED
stage_e_continuous_baselines_validation = PARTIALLY_USABLE_UNDER_FORENSIC_REVIEW
nonmatching_transfer_algorithm_scientifically_unblocked = true
production_adaptive_accuracy_validation_scientifically_unblocked = false (Held strictly blocked)
PK10R1_topology_repair_required = true
telegram_delivery_observed = true
email_delivery_observed = true
notification_pre_submission_gate_passed = true
new_submission_authorized = true (Triplet batch submitted: 1390533, 1390534, 1390535)
qsub_called = true (Triplet batch active)
qdel_called = false
qmove_called = false
git_commit_called = false
git_push_called = false
```
