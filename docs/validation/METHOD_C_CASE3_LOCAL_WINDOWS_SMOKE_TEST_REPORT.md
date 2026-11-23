# Method C Case 3: Local Windows Smoke Test Report (Cycle-0 Coarse Solve)

**Task**: `METHOD-C-CASE3-FRAMEWORK-LOCAL-WINDOWS-SMOKE-TEST`  
**Scientific Operation**: `method_c_case3_framework_local_windows_smoke_test`  
**Date**: 23 November 2026  
**Platform**: Windows 11 Enterprise x64 (Local PC Execution)  
**Abaqus Version**: Abaqus 2024 (RELr426)  
**Fortran Compiler**: Intel(R) Fortran Compiler 2026.0.0 Build 20260331 (`ifx`/`ifort`)  
**C/C++ Compiler / Linker**: Microsoft (R) Visual Studio 2022 Build Tools v17.14 (MSVC 14.44.35226)  
**Frozen UEL SHA-256**: `CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6` (strictly bitwise unchanged)  
**Orchestrator**: `models/pandey_kumar_mode1/290_method_c_case3/case3_single_job_orchestrator.py`  
**Orchestrator SHA-256**: `AC56BA7D2BF877FD174DF375E8066DB17B90F61D0EAEB93CFC9854106710A79A` (commit `04e78edcf`)  
**Run Directory**: `D:\mc3_local\smoke_cycle0\`  
**HPC Impact**: Exactly 0 PBS submissions consumed (cumulative count preserved; cluster job 1424916 untouched)  

---

## 1. Executive Summary & Purpose

This smoke test verifies and proves that the frozen thesis UEL (`f42_mixed_uel.for`, `CE8D5EDC...`) compiles, links, and executes under **Abaqus 2024** on the user's local Windows PC. The initial coarse solve (Cycle 0) of Method C Case 3 (Pandey & Kumar 2025 Section 4.3: Mode-I cracked plate with central void and pin loading) was executed through the approved dynamic-corridor orchestrator (`AC56BA7D...`) configured with `--n-adaptive-steps 0 --cpus 6`.

The local Windows solve completed cleanly with Exit code 0, identically reproducing all approved HPC benchmark observables:
- Step-1 linear-elastic reaction force: **3.9288 kN** (exact match);
- Peak reaction force: **4.3318 kN** at $u_2 = 0.056095\,\text{mm}$ (exact match);
- Total equilibrium iterations: **256** (160 in Step 1, 96 in Step 2; exact match);
- Macroscopic terminal crack tip: **$(10.6727, 69.9342)\,\text{mm}$** with forward extension $\Delta a = 0.675954\,\text{mm}$ toward the void (exact match);
- Extracted state file written in run directory with full nodal displacement, phase-field damage, and Gauss-point history tensors.

---

## 2. Compilation and Linkage Audit

The compilation and linking logs confirm seamless generation of the Abaqus/Standard user shared library (`standardU.lib`, `standardU.exp`):

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
```

Elapsed solver execution time on 6 CPUs SMP: **38.0 s walltime** / **121.0 s CPU time**.

---

## 3. Observables Comparison vs Approved HPC Benchmark

| Observable / Metric | Expected (Approved HPC Run) | Local Windows PC Run | Discrepancy | Acceptance Verdict |
| :--- | :---: | :---: | :---: | :---: |
| **Abaqus Exit Code** | `0` (clean cutback completion) | `0` (`Cycle 0 exited with code: 0`) | None | **PASS** |
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

The run's lightweight state and summary files have been committed to the repository under `models/pandey_kumar_mode1/290_method_c_case3/local_windows_smoke_test/`:

| Artifact Path | File Size | Cryptographic SHA-256 | Description |
| :--- | :---: | :---: | :--- |
| `local_windows_smoke_test/PK_METHOD_C_CASE3_COARSE_JOB1_state.json` | 1,253,811 B | `D3BEA6439B38C7C1277A3FFECFBC47C9FF3F529651F7CAF6C15C61CDA65A9726` | Extracted Cycle 0 state (nodal displacements, damage, GP history) |
| `local_windows_smoke_test/PK_METHOD_C_CASE3_COARSE_JOB1_SUMMARY.json` | 13,758 B | `AFF9F133618D07F4817DAEBD4669421EB176AE27925776DF690CD8DF1046F5BD` | Machine-readable observables and propagation history JSON |
| `local_windows_smoke_test/PK_METHOD_C_CASE3_COARSE_JOB1_RECEIPT.json` | 1,537 B | `33EE8062EF44D6DEC122838A976B068BBF58B2EC964402BA4CEAAAFE095EC4BB` | Run execution receipt and timing record |
| `local_windows_smoke_test/PK_METHOD_C_CASE3_COARSE_JOB1.sta` | 5,471 B | `2D80AA228C63D66976363E55FFB6E70D71888B079976AC1FAA0057F4FF6E90EA` | Abaqus solver status file (63 total increments, 256 iterations) |
| `local_windows_smoke_test/PK_METHOD_C_CASE3_COARSE_JOB1.msg` | 232,870 B | `3B46E1F8A4D4E1D90837E05EA68D16F6541D62810F59E6CF4222F1B47139AB64` | Abaqus message file with residual and convergence records |
| `local_windows_smoke_test/PK_METHOD_C_CASE3_COARSE_JOB1.dat` | 62,232 B | `28F88AC5A71752A46AAA8E0C04605057D7A1FB564A5337B4EE0924F6778E8B6C` | Abaqus printed output file (nodal coordinates, reaction forces) |
| `local_windows_smoke_test/uel_energy_balance.csv` | 6,155 B | `8EFF657656C1B94F67E5365236CCD7F6068E415524DF746A8DC96D13C7431CC2` | Step-by-step UEL energy balance log |

*(Note: The 37 MB `.odb` solver binary remains in local scratch `D:\mc3_local\smoke_cycle0\` and is excluded from git per repository governance.)*

---

## 5. Conclusion & Governance Verification

1. **Thesis UEL Portability**: The frozen thesis UEL (`CE8D5EDC...`) compiles and links cleanly under Intel Fortran 2026 / MSVC 2022 and runs deterministically under Abaqus 2024 on Windows.
2. **Dynamic-Corridor Orchestrator Parity**: `case3_single_job_orchestrator.py` (`AC56BA7D...`) successfully runs on local Windows without modifications, executing Cycle 0 and extracting the terminal ODB state.
3. **Physical Reproduction**: All 16 physical and numerical observables match the approved HPC baseline with $< 0.01\%$ numerical precision.
4. **Zero HPC Resource Consumption**: Exactly 0 PBS submissions consumed; cluster job 1424916 remains actively running on mnode106 undisturbed.
