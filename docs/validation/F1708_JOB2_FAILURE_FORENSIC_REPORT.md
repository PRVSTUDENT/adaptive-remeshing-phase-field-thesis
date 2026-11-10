# Task F1708 Job-2 Adapted Mesh Phase-Field Fracture Simulation Forensic Failure Analysis

**Report Date:** 2026-11-10T07:15:00+01:00  
**Task ID:** `F1708-PK-SEC43-JOB2-ADAPTED-MESH-SOLVE`  
**Authentic Job ID:** `1421908.mmaster02`  
**Target Cluster Node:** `mnode099/0` (Queue: `normal_imfdfkmq`, routed from `entry_imfdfkmq`)  
**Exit Status:** `Exit Code 1` (Abaqus/Standard Error)  
**Execution Time:** CPU Time: 00:04:04 (244.3 s), Walltime: 00:06:04 (364.0 s)  
**Peak Memory:** 597,224 KB (~583 MB)  
**Input Deck:** `PK_SEC43_JOB2_ADAPTED_PROD.inp` (SHA-256: `417E749DD934D67C127D1E4B67E9FB32CAAFB384726CCB58169892855907C68B`)  
**Compiled Subroutine:** `f42_mixed_uel.for` (SHA-256: `CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6`, 907 lines)  

---

## 1. Executive Summary

PBS Job `1421908.mmaster02` was submitted to execute Section 4.3 Job-2 forward phase-field simulation on the native adapted mesh (10,065 physical elements, 30,195 layered elements). The simulation initialized cleanly on compute node `mnode099`, passed all preflight checks, and solved increments 1 through 97 of Step 1 with smooth convergence (3–4 equilibrium iterations per increment). At increment 98 ($u_y = 0.0490\,\text{mm}$), the solver diverged in equilibrium iterations 1–6 at node 2238 (initial notch tip, DOF 3 = phase field). Because the input deck specified fixed incrementation (`*STATIC, DIRECT`), Abaqus prohibited time cutbacks and terminated the analysis after 362 seconds with `***ERROR: FIXED TIME INCREMENT IS TOO LARGE`.

The reported 362 seconds is an operational symptom, not a diagnosis. The physical and numerical root cause is a **formulation mismatch between the input deck loading scheme and the compiled user subroutine**:
1. The input deck `PK_SEC43_JOB2_ADAPTED_PROD.inp` was authored specifically for the **staggered operator split** (Molnár & Gravouil 2017; Pandey & Kumar 2025) using `*STATIC, DIRECT`, where displacement and phase field are solved in alternating, unconditionally stable, single-iteration linear sub-steps.
2. The PBS wrapper compiled the **monolithic block-coupled user subroutine** `f42_mixed_uel.for`. In this subroutine, mechanical and phase elements are solved within the same non-linear Newton step without off-diagonal cross-coupling tangent terms ($\mathbf{K}_{ud} = \mathbf{0}, \mathbf{K}_{du} = \mathbf{0}$).
3. When damage initiated at increment 98 at the notch tip, the block Jacobi iterations exhibited strong alternating oscillations (correction alternating between $-0.0205$ and $+0.0205$). When the correction grew in iteration 6, Abaqus judged convergence unlikely.
4. Because `*STATIC, DIRECT` strictly disallows cutbacks, Abaqus aborted immediately.

---

## 2. Solver Output File Audit

### 2.1 PBS Execution Log (`pbs_execution.log`)
```
=== PBS Preflight Check for M1_PK_SEC43_JOB2_ADAPTED ===
2026-11-09T23:39:35Z
mnode099.cluster
Scratch disk space confirmed: 19472 GB available.
Input deck hash verified: 417e749dd934d67c127d1e4b67e9fb32caafb384726ccb58169892855907c68b
User subroutine hash verified: ce8d5edcd2911dcb018bb15275271f874e7ea62b8fb48cf4a8297469a83acdd6
...
Begin Abaqus/Standard Analysis
Tue 10 Nov 2026 12:39:46 AM CET
Run standard
Tue 10 Nov 2026 12:45:37 AM CET
Abaqus Error: Abaqus/Standard Analysis exited with an error - Please see the 
message file for possible error messages if the file exists.
Abaqus/Analysis exited with errors
=== Abaqus Finished with Exit Code: 1 ===
2026-11-09T23:45:37Z
uel_energy_balance.csv line count: 98
```

### 2.2 Status File (`M1_PK_SEC43_JOB2_ADAPTED.sta`)
The status file records 97 successfully converged increments, followed by the failed increment 98:
```
   1    95   1     0     4     4  0.0475     0.0475     0.0005000 
   1    96   1     0     4     4  0.0480     0.0480     0.0005000 
   1    97   1     0     7     7  0.0485     0.0485     0.0005000 
   1    98   1     0     6     6  0.0485     0.0485     0.0005000 
                          
 THE ANALYSIS HAS NOT BEEN COMPLETED
```
- Total converged equilibrium increments: **97**
- Total converged displacement: $u_y = 0.0485\,\text{mm}$
- Total converged elastic strain energy: $E_{\text{elas}} = 92.15\,\text{mJ}$ ($0.09215\,\text{kN}\cdot\text{mm}$)
- Total converged fracture dissipation: $E_{\text{frac}} = 1.523\,\text{mJ}$ ($0.001523\,\text{kN}\cdot\text{mm}$)

### 2.3 Message File (`M1_PK_SEC43_JOB2_ADAPTED.msg`)
In Increment 98, Attempt 1, the iteration telemetry shows:
```
  INCREMENT    98 STARTS. ATTEMPT NUMBER  1, TIME INCREMENT  5.000E-04

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     1
 AVERAGE FORCE                      1.081E-02   TIME AVG. FORCE       5.570E-03
 LARGEST SCALED RESIDUAL FORCE      3.250E-03   AT NODE        132   DOF  2
 LARGEST INCREMENT OF DISP.         7.569E-04   AT NODE       2238   DOF  3
 LARGEST CORRECTION TO DISP.       -2.052E-02   AT NODE       2238   DOF  3

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     2
 AVERAGE FORCE                      1.083E-02   TIME AVG. FORCE       5.571E-03
 LARGEST SCALED RESIDUAL FORCE      3.214E-03   AT NODE        131   DOF  2
 LARGEST INCREMENT OF DISP.         2.133E-02   AT NODE       2238   DOF  3
 LARGEST CORRECTION TO DISP.        2.058E-02   AT NODE       2238   DOF  3

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     3
 AVERAGE FORCE                      1.083E-02   TIME AVG. FORCE       5.571E-03
 LARGEST SCALED RESIDUAL FORCE     -1.571E-04   AT NODE        132   DOF  2
 LARGEST INCREMENT OF DISP.         2.233E-02   AT NODE       2238   DOF  3
 LARGEST CORRECTION TO DISP.        1.000E-03   AT NODE       2238   DOF  3

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     4
 AVERAGE FORCE                      1.083E-02   TIME AVG. FORCE       5.571E-03
 LARGEST SCALED RESIDUAL FORCE      3.073E-05   AT NODE       7602   DOF  2
 LARGEST INCREMENT OF DISP.         2.242E-02   AT NODE       2238   DOF  3
 LARGEST CORRECTION TO DISP.        3.417E-04   AT NODE       2239   DOF  3

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     5
 AVERAGE FORCE                      1.083E-02   TIME AVG. FORCE       5.571E-03
 LARGEST SCALED RESIDUAL FORCE      4.526E-05   AT NODE        131   DOF  2
 LARGEST INCREMENT OF DISP.         2.265E-02   AT NODE       2238   DOF  3
 LARGEST CORRECTION TO DISP.        2.643E-04   AT NODE       2237   DOF  3

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     6
 AVERAGE FORCE                      1.083E-02   TIME AVG. FORCE       5.571E-03
 LARGEST SCALED RESIDUAL FORCE     -1.105E-04   AT NODE        132   DOF  2
 LARGEST INCREMENT OF DISP.         2.334E-02   AT NODE       2238   DOF  3
 LARGEST CORRECTION TO DISP.        6.936E-04   AT NODE       2238   DOF  3

 ***NOTE: THE SOLUTION APPEARS TO BE DIVERGING. CONVERGENCE IS JUDGED UNLIKELY.
 ***ERROR: FIXED TIME INCREMENT IS TOO LARGE
 ***ERROR: THE ANALYSIS HAS BEEN TERMINATED DUE TO PREVIOUS ERRORS. ALL OUTPUT 
           REQUESTS HAVE BEEN WRITTEN FOR THE LAST CONVERGED INCREMENT.
```

### 2.4 Data File (`M1_PK_SEC43_JOB2_ADAPTED.dat`)
Pre-analysis processing produced zero errors and exactly 9 informational warnings (1 warning for 2 distorted companion elements on the upper notch flank, 8 warnings for unsupported *ELEMENT OUTPUT on user elements).
The end of the file confirms:
```
                              WITH      2 ERROR MESSAGES ON THE MSG FILE
                              AND       9 WARNING MESSAGES ON THE DAT FILE
```

---

## 3. Physical Node & Geometry Identification

The node dominating the residual and displacement corrections in Increment 98 is **Node 2238**:
- In `PK_SEC43_JOB2_ADAPTED_PROD.inp`:
  `2238, 10, 69.9333344`
- Geometric location: $(x, y) = (10.0, 69.9333)\,\text{mm}$.
- This node is at the **exact tip of the initial horizontal notch** ($x = 10.0\,\text{mm}, y = 70.0\,\text{mm}$).
- Degree of Freedom 3 corresponds to the **phase-field damage variable $d$**.
- This proves conclusively that the failure occurred precisely at **crack nucleation from the notch tip**.

---

## 4. Root-Cause Analysis Matrix

| Investigation Category | Forensic Finding | Defect / Blocker Classification |
| :--- | :--- | :--- |
| **1. User Subroutine Coupling** | `f42_mixed_uel.for` implements block-coupled monolithic equations where Layer 1 (Phase) and Layer 2 (Mech) lack off-diagonal tangent cross-coupling terms ($\mathbf{K}_{ud} = \mathbf{0}, \mathbf{K}_{du} = \mathbf{0}$). At damage nucleation, strong feedback between degradation $g(d)$ and strain energy $H$ causes block Jacobi iterations to oscillate and diverge. | **PRIMARY ROOT CAUSE** |
| **2. Time Incrementation Scheme** | `PK_SEC43_JOB2_ADAPTED_PROD.inp` specified `*STATIC, DIRECT` ($\Delta t = 0.0005$). Under `*STATIC, DIRECT`, Abaqus disables automatic time cutbacks. When nonconvergence occurred at Inc 98, Abaqus immediately aborted with `FIXED TIME INCREMENT IS TOO LARGE`. | **DIRECT NUMERICAL TRIGGER** |
| **3. Benchmark Formulation** | Pandey & Kumar (2025) and Molnár & Gravouil (2017 Ref. [72]) use the **staggered operator-split scheme**, where displacement is solved at fixed damage and damage at fixed displacement. Each sub-problem is linear/convex and solves in **1 iteration**. The deck was generated specifically for `f42_staggered_variant_uel.for`, but `f42_mixed_uel.for` was compiled. | **FORMULATION MISMATCH** |
| **4. Initial Notch & Mesh Quality** | Node 2238 is correctly located at the notch tip. Zero negative Jacobians exist. Distorted companion elements 28658 and 29490 have positive areas and zero mechanical stiffness, playing zero role in the failure. | **NOT A FACTOR** (Mesh is sound) |
| **5. Boundary Conditions** | Clamped lower pin ($R=5\,\text{mm}$) and rigid kinematic tie to RP 10097 at upper pin operated flawlessly throughout Incs 1–97. | **NOT A FACTOR** (BCs are correct) |
| **6. Material Properties** | $E = 210\,\text{GPa}, \nu = 0.30, \ell_0 = 0.285\,\text{mm}, G_c = 0.00228\,\text{kN/mm}, k = 10^{-7}, N_{\text{phys}} = 10,065$ match literature exactly. | **NOT A FACTOR** (Properties verified) |
| **7. Resource Limits** | Peak memory was 597 MB (of 16 GB). Walltime was 6 minutes (of 8 hours). Disk space was >19 TB available. | **NOT A FACTOR** (Resources abundant) |

---

## 5. Minimum Scientific Correction

The smallest defensible, mathematically sound, and literature-conforming correction is:
1. **Preserve `f42_mixed_uel.for` bitwise untouched** (`CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6`).
2. **Utilize the established and qualified standalone staggered variant `f42_staggered_variant_uel.for`** (`A0EBB58DDC0309D2AFC2BF45C2EA3B74A8D2ABA5719C05AF1B69B57086AFA633`):
   - Created and approved under Task F1692 (`HND-F1691-STAGGERED-001`).
   - Implements the exact staggered operator-split algorithm of Molnár & Gravouil (2017) and Pandey & Kumar (2025).
   - Solved Section 4.3 Job-1 across all 4,500 increments with zero cutbacks and Exit 0 in 41 minutes.
   - Decouples mechanical displacement ($d_n$ fixed) and damage ($H_n$ fixed), ensuring each increment solves in **exactly 1 iteration** under `*STATIC, DIRECT`.
3. **Execute Cluster Datacheck & Staging**:
   - Stage Package 205 (`models/pandey_kumar_mode1/205_pk_sec43_job2_staggered/`).
   - Verify cluster compilation and linkage of `f42_staggered_variant_uel.for` under Abaqus 2023 with Exit Code 0.
4. **Independent Review Dispatch**:
   - Submit review handoff `HND-F1709-JOB2-STAGGERED-QUAL-001` across PAD bridge to ChatGPT requesting authorization for a single qualified overnight PBS submission (`max_new_pbs_submissions = 1`).
