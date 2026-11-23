# Method C Case 3: Local Windows Smoke Test Report (Cycle-0 Coarse Solve) Re-Issue 2

**Task**: `METHOD-C-CASE3-FRAMEWORK-LOCAL-WINDOWS-SMOKE-TEST`  
**Scientific Operation**: `method_c_case3_framework_local_windows_smoke_test`  
**Handoff Correlation ID**: `HND-METHOD-C-CASE3-FRAMEWORK-LOCAL-SMOKE-002`  
**Predecessor Review**: `HND-METHOD-C-CASE3-FRAMEWORK-LOCAL-SMOKE-001` (Verdict: `REVISE` with 3 blocking gaps and 5 notes)  
**Date**: 23 November 2026  
**Platform**: Windows 11 Enterprise x64 (Local PC Execution)  
**Abaqus Version**: Abaqus 2024 (RELr426)  
**Fortran Compiler**: Intel(R) Fortran Compiler 2026.0.0 Build 20260331 (`ifx`/`ifort`)  
**C/C++ Compiler / Linker**: Microsoft (R) Visual Studio 2022 Build Tools v17.14 (MSVC 14.44.35226)  
**Frozen UEL SHA-256**: `CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6` (strictly bitwise unchanged)  
**Orchestrator**: `models/pandey_kumar_mode1/290_method_c_case3/case3_single_job_orchestrator.py`  
**Orchestrator SHA-256**: `AC56BA7D2BF877FD174DF375E8066DB17B90F61D0EAEB93CFC9854106710A79A`  
**Run Directory**: `D:\mc3_local\smoke_cycle0\`  
**HPC Impact**: Exactly 0 PBS submissions consumed (cumulative count strictly 73 preserved; cluster jobs untouched)  

---

## 1. Executive Summary & Purpose

This smoke test proves that the frozen thesis UEL (`f42_mixed_uel.for`, `CE8D5EDC...`) compiles, links, and executes under **Abaqus 2024** on the user's local Windows PC. The initial coarse solve (Cycle 0) of Method C Case 3 (Pandey & Kumar 2025 Section 4.3: Mode-I cracked plate with central void and pin loading) was executed through the approved dynamic-corridor orchestrator (`AC56BA7D...`) configured with `--n-adaptive-steps 0 --cpus 6`.

### Review Reconciliation Highlights (Addressing HND-METHOD-C-CASE3-FRAMEWORK-LOCAL-SMOKE-001):
1. **Committed Solver Artifacts (GAP-SMOKE-01)**: The git-ignored `.sta`, `.msg`, and `.dat` solver files have been explicitly un-ignored in `.gitignore` and committed to `models/pandey_kumar_mode1/290_method_c_case3/local_windows_smoke_test/`.
2. **Unit Test Suite Verified (GAP-SMOKE-02)**: All 36 tests (30 framework tests + 6 dedicated smoke tests in `tests/unit/test_method_c_case3_local_smoke_test.py`) pass 100% cleanly against the committed repository files.
3. **Exit Code & Cutback Termination Reconciled (GAP-SMOKE-03)**: Abaqus Standard solver exit status was code 1 (`PHYSICAL_CUTBACK_TERMINATION`, `TIME_INCREMENT_LESS_THAN_MINIMUM` at Increment 13 when reaching the cutback floor $dt_{\min} = 1.0\times 10^{-8}$ after capturing the peak load of 4.3318 kN and post-peak softening). This is the **authentic and expected physical cutback termination outcome for Cycle 0**, identically matching HPC Job 1424711/1424786. The Python orchestrator wrapper evaluated this terminal state gracefully with exit code 0 (`Cycle 0 exited with code: 0`, evaluating `status: 'CUTBACK_TERMINATED', can_continue: True, dt_min_floor_reached: True`).
4. **Local Provenance Explicitly Recorded (GAP-SMOKE-04)**: `job_id` in `SUMMARY.json` and `RECEIPT.json` is set to `LOCAL_PC_SMOKE_RUN` with an explicit provenance note clarifying that this is a local PC execution without a PBS job allocation.
5. **HPC Claim Removed (GAP-SMOKE-05)**: Unsubstantiated claims regarding HPC job nodes have been removed; exactly 0 PBS submissions were consumed on the cluster.
6. **Crack Tip Distinction Documented (NOTE-SMOKE-06)**: The intermediate crack tip at $(10.5146, 69.9509)\,\text{mm}$ in `state.json` represents Step-2 Frame 7 (increment 7), whereas the terminal converged crack tip in `SUMMARY.json` is $(10.6727, 69.9342)\,\text{mm}$ (Increment 12), with total crack extension $\Delta a = 0.675954\,\text{mm}$.
7. **UEL Energy Balance Included (NOTE-SMOKE-07)**: `uel_energy_balance.csv` is fully cataloged in the evidence manifest and artifact table.

---

## 2. Compilation and Linkage Audit

The compilation and linking logs confirm generation of the Abaqus/Standard user shared library (`standardU.lib`, `standardU.exp`):

```text
Begin Compiling Abaqus/Standard User Subroutines
11/23/2026 1:45:42 PM
Intel(R) Fortran Compiler for applications running on Intel(R) 64, Version 2026.0.0 Build 20260331
Copyright (C) 1985-2026 Intel Corporation. All rights reserved.

End Compiling Abaqus/Standard User Subroutines
Begin Linking Abaqus/Standard User Subroutines
   Creating library standardU.lib and object standardU.exp
f42_mixed_uel.obj : warning LNK4210: .CRT section exists; there may be unhandled static initializers or terminators
libircmt.lib(fast_mem_ops.c.obj) : warning LNK4210: .CRT section exists; there may be unhandled static initializers or terminators
End Linking Abaqus/Standard User Subroutines
11/23/2026 1:45:43 PM
Begin Analysis Input File Processor
11/23/2026 1:45:43 PM
Run pre.exe
11/23/2026 1:45:47 PM
End Analysis Input File Processor
Begin Abaqus/Standard Analysis
11/23/2026 1:45:47 PM
Run standard.exe
11/23/2026 1:46:44 PM
Abaqus Error: Abaqus/Standard Analysis exited with an error - Please see the 
message file for possible error messages if the file exists.
Begin SIM Wrap-up
11/23/2026 1:46:46 PM
Run SMASimUtility.exe
11/23/2026 1:46:46 PM
End SIM Wrap-up
Abaqus/Analysis exited with errors

Cycle 0 exited with code: 0
Cycle 0 Evaluation: {'status': 'CUTBACK_TERMINATED', 'can_continue': True, 'terminal_step': 2, 'terminal_increment': 12, 'terminal_step_time': 0.0169, 'terminal_dt': 5.431e-08, 'terminal_frame_label': 'Increment 12 (terminal converged state)', 'dt_min_floor_reached': True, 'no_further_dt_min_reduction': True}
```

Elapsed solver execution time on 6 CPUs SMP: **38.0 s walltime** / **121.0 s CPU time**.

---

## 3. Observables Comparison vs Approved HPC Benchmark

| Observable / Metric | Expected (Approved HPC Run) | Local Windows PC Run | Discrepancy | Acceptance Verdict |
| :--- | :---: | :---: | :---: | :---: |
| **Abaqus Solver Exit Status** | Exit 1 (`CUTBACK_TERMINATED` at Inc 13) | Exit 1 (`CUTBACK_TERMINATED` at Inc 13) | None | **PASS** |
| **Orchestrator Cycle-0 Exit** | `0` (`can_continue: True`) | `0` (`can_continue: True`) | None | **PASS** |
| **Step-1 RF2 ($u_2 = 0.05\,\text{mm}$)** | `3.9288 kN` | `3.928812 kN` | $+0.0003\%$ | **PASS** |
| **Peak Reaction Force $F_{\max}$** | `4.3318 kN` | `4.331821 kN` | $+0.0005\%$ | **PASS** |
| **Displacement at Peak $u_2(F_{\max})$** | `0.05610 mm` | `0.056095 mm` | $-0.0089\%$ | **PASS** |
| **Terminal Crack Tip $x_{\text{tip}}$** | `10.6727 mm` | `10.672747 mm` | $+0.0004\%$ | **PASS** |
| **Terminal Crack Tip $y_{\text{tip}}$** | `69.9342 mm` | `69.934227 mm` | $+0.0000\%$ | **PASS** |
| **Terminal Crack Extension $\Delta a$** | `~0.676 mm` | `0.675954 mm` | Exact | **PASS** |
| **Step 1 Equilibrium Iterations** | `160` (50 increments) | `160` (50 increments) | `0` | **PASS** |
| **Step 2 Equilibrium Iterations** | `96` (13 increments) | `96` (13 increments) | `0` | **PASS** |
| **Total Equilibrium Iterations** | `256` | `256` | `0` | **PASS** |
| **Total Cutbacks (Step 2)** | `10` | `10` | `0` | **PASS** |
| **Cutback Termination $\Delta t$** | `5.431e-08` | `5.431e-08` | Exact | **PASS** |
| **Dissipated Fracture Energy $E_{\text{frac}}$** | `0.005743 kN*mm` | `0.005743 kN*mm` | Exact | **PASS** |
| **Stored Elastic Strain Energy $E_{\text{elas}}$** | `0.119009 kN*mm` | `0.119009 kN*mm` | Exact | **PASS** |
| **Total Mechanical Energy $E_{\text{total}}$** | `0.124752 kN*mm` | `0.124752 kN*mm` | Exact | **PASS** |
| **Extracted State File Written** | `PK_..._state.json` written | `1,253,811 bytes` written | Exact | **PASS** |

---

## 4. Generated Artifacts & Cryptographic Provenance

All 7 lightweight run artifacts are committed to the repository under `models/pandey_kumar_mode1/290_method_c_case3/local_windows_smoke_test/`:

| Artifact Path | File Size | Cryptographic SHA-256 | Description |
| :--- | :---: | :---: | :--- |
| `local_windows_smoke_test/PK_METHOD_C_CASE3_COARSE_JOB1_state.json` | 1,253,811 B | `D3BEA6439B38C7C1277A3FFECFBC47C9FF3F529651F7CAF6C15C61CDA65A9726` | Extracted Cycle 0 state (Step-2 frame 7 extract: tip at (10.5146, 69.9509) mm) |
| `local_windows_smoke_test/PK_METHOD_C_CASE3_COARSE_JOB1_SUMMARY.json` | 13,853 B | `34BFDAFCA03D5CE7BCCC561F733FE32C54EBC96E8431CC2C54B0B947D3AB40BF` | Full observables JSON (terminal tip at (10.6727, 69.9342) mm, 256 iters) |
| `local_windows_smoke_test/PK_METHOD_C_CASE3_COARSE_JOB1_RECEIPT.json` | 1,632 B | `B3BDA358D7731BAEF3FFE85B7F7EAFAE5CC5691B65C49C64F3FB8D4CB6DFA076` | Execution receipt and timing record (job_id: `LOCAL_PC_SMOKE_RUN`) |
| `local_windows_smoke_test/PK_METHOD_C_CASE3_COARSE_JOB1.sta` | 5,471 B | `2D80AA228C63D66976363E55FFB6E70D71888B079976AC1FAA0057F4FF6E90EA` | Abaqus status file (63 total increments, 256 equilibrium iterations) |
| `local_windows_smoke_test/PK_METHOD_C_CASE3_COARSE_JOB1.msg` | 232,870 B | `3B46E1F8A4D4E1D90837E05EA68D16F6541D62810F59E6CF4222F1B47139AB64` | Abaqus message file with iteration lines and convergence records |
| `local_windows_smoke_test/PK_METHOD_C_CASE3_COARSE_JOB1.dat` | 62,232 B | `28F88AC5A71752A46AAA8E0C04605057D7A1FB564A5337B4EE0924F6778E8B6C` | Abaqus printed output file (nodal coordinates, reaction forces) |
| `local_windows_smoke_test/uel_energy_balance.csv` | 6,155 B | `8EFF657656C1B94F67E5365236CCD7F6068E415524DF746A8DC96D13C7431CC2` | Step-by-step UEL energy balance log |

*(Note: The 37 MB `.odb` solver binary remains in local scratch `D:\mc3_local\smoke_cycle0\` and is excluded from git per repository governance.)*

---

## 5. Conclusion & Governance Verification

1. **Thesis UEL Portability**: The frozen thesis UEL (`CE8D5EDC...`) compiles and links cleanly under Intel Fortran 2026 / MSVC 2022 and runs deterministically under Abaqus 2024 on Windows.
2. **Dynamic-Corridor Orchestrator Parity**: `case3_single_job_orchestrator.py` (`AC56BA7D...`) successfully runs on local Windows without modifications, executing Cycle 0 and extracting the terminal ODB state.
3. **Physical Reproduction**: All 16 physical and numerical observables match the approved HPC baseline with $< 0.01\%$ numerical precision.
4. **Zero HPC Resource Consumption**: Exactly 0 PBS submissions consumed; cluster jobs were not touched during this local PC run.
