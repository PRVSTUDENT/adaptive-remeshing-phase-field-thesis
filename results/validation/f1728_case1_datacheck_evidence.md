# Primary Solver and Datacheck Evidence: Task F1728 Case 1 Pilot

**Model:** `PK_F1728_CASE_1_PROD`  
**Datacheck Job:** `PK_F1728_CASE_1_DC`  
**Execution Node:** `mlogin01.cluster` / `mnode105.cluster`  
**Date:** 13 November 2026, 19:37:15 CET  
**Status:** `ANALYSIS DATACHECK COMPLETE - EXIT CODE 0`

---

## 1. File Inventory and SHA-256 Hashes

| Artifact | Cluster Path | Size (Bytes) | SHA-256 Digest |
| :--- | :--- | :--- | :--- |
| **Physical Mesh** | `/scratch9/pr21vyci/runs/f1728_case1_pilot/PK_F1728_CASE_1_ADAPT_PHYS.inp` | 989,525 | `a470a71da5e6a01c2721fef5db7f1f0daa4610a54fc017b5161f6f5f6c145fb5` |
| **Production Deck** | `/scratch9/pr21vyci/runs/f1728_case1_pilot/PK_F1728_CASE_1_PROD.inp` | 1,827,590 | `36c84b6eb7fc4ef6f402b132a8e7ce18f403bc7782ef915661f46b5b9ceef14d` |
| **Mesh Audit JSON** | `/scratch9/pr21vyci/runs/f1728_case1_pilot/PK_F1728_CASE_1_AUDIT.json` | 2,361 | `83fdc5f133807782ffe3b055e6275011d89273a37da5bf962c6f49deddd7fed2` |
| **Datacheck DAT** | `/scratch9/pr21vyci/runs/f1728_case1_pilot/PK_F1728_CASE_1_DC.dat` | 12,666 | `30e5bdff2bf8548a2dcb80cb3ef85499ad2404909d5d84aefbf8119c0ed0fa2f` |
| **Datacheck MSG** | `/scratch9/pr21vyci/runs/f1728_case1_pilot/PK_F1728_CASE_1_DC.msg` | 1,423 | `f9bfbc9738c82eb4b2382da41d655e8d9755fc66380c550ea0eb93ee74f4f5d6` |
| **Datacheck PRT** | `/scratch9/pr21vyci/runs/f1728_case1_pilot/PK_F1728_CASE_1_DC.prt` | 1,714 | `d559e2f694668ba458a4fa14589255a6d36e2f17094eeaa44ddc06154378f99c` |

---

## 2. Complete Verbatim Transcript of `PK_F1728_CASE_1_DC.msg`

```text
1

   Abaqus 2023                                  Date 13-Nov-2026   Time 19:37:13
   For use by TECHNISCHE UNIVERSITAET BERGAKADEMIE FREIBERG under license from Dassault Systemes or its subsidiary.

 Method A Adapted Phase-Field Model: PK_F1728_CASE_1_PROD                        
                                                                                 
 STEP    1     INCREMENT     1     STEP TIME    0.00    


                        A N A L Y S I S    D A T A C H E C K




                        S T E P       1     S T A T I C   A N A L Y S I S


                                                                                          

     AUTOMATIC TIME CONTROL WITH -
          A SUGGESTED INITIAL TIME INCREMENT OF                2.000E-02
          AND A TOTAL TIME PERIOD OF                            1.00    
          THE MINIMUM TIME INCREMENT ALLOWED IS                1.000E-07
          THE MAXIMUM TIME INCREMENT ALLOWED IS                2.000E-02

     LINEAR EQUATION SOLVER TYPE         DIRECT SPARSE

     COLLECTING MODEL CONSTRAINT INFORMATION FOR OVERCONSTRAINT CHECKS

     COLLECTING STEP CONSTRAINT INFORMATION FOR OVERCONSTRAINT CHECKS



     JOB TIME SUMMARY
       USER TIME (SEC)      =     0.75    
       SYSTEM TIME (SEC)    =     0.17    
       TOTAL CPU TIME (SEC) =     0.92    
       WALLCLOCK TIME (SEC) =            1
       MEMORY PEAK (GB)     =            0
```

---

## 3. Verbatim Excerpt of `PK_F1728_CASE_1_DC.dat` (Model Processing & Execution Summary)

```text
          NUMBER OF ELEMENTS IS                                 42441
          NUMBER OF NODES IS                                    14171
          NUMBER OF NODES DEFINED BY THE USER                   14171
          TOTAL NUMBER OF VARIABLES IN THE MODEL                42511
          (DEGREES OF FREEDOM PLUS MAX NO. OF ANY LAGRANGE MULTIPLIER
           VARIABLES. INCLUDE *PRINT,SOLVE=YES TO GET THE ACTUAL NUMBER.)

                              END OF USER INPUT PROCESSING

     JOB TIME SUMMARY
       USER TIME (SEC)      =     0.98    
       SYSTEM TIME (SEC)    =     0.10    
       TOTAL CPU TIME (SEC) =      1.1    
       WALLCLOCK TIME (SEC) =            2

    Abaqus 2023                                  Date 13-Nov-2026   Time 19:37:13
    For use by TECHNISCHE UNIVERSITAET BERGAKADEMIE FREIBERG under license from Dassault Systemes or its subsidiary.

      Method A Adapted Phase-Field Model: PK_F1728_CASE_1_PROD                                  STEP    1  INCREMENT    1
                                                                                           TIME COMPLETED IN THIS STEP   0.00    

                        A N A L Y S I S    D A T A C H E C K

                   M E M O R Y   E S T I M A T E
  
 PROCESS      FLOATING PT       MINIMUM MEMORY        MEMORY TO
              OPERATIONS           REQUIRED          MINIMIZE I/O
             PER ITERATION           (MB)               (MB)
  
     1          7.69E+08               35                 69

 ***WARNING: THE *ELEMENT OUTPUT OPTION IS NOT SUPPORTED FOR USER ELEMENTS
 ***WARNING: THE *ELEMENT OUTPUT OPTION IS NOT SUPPORTED FOR USER ELEMENTS
 ***WARNING: THE *ELEMENT OUTPUT OPTION IS NOT SUPPORTED FOR USER ELEMENTS
 ***WARNING: THE *ELEMENT OUTPUT OPTION IS NOT SUPPORTED FOR USER ELEMENTS
 ***WARNING: THE *ELEMENT OUTPUT OPTION IS NOT SUPPORTED FOR USER ELEMENTS
 ***WARNING: THE *ELEMENT OUTPUT OPTION IS NOT SUPPORTED FOR USER ELEMENTS
 ***WARNING: THE *ELEMENT OUTPUT OPTION IS NOT SUPPORTED FOR USER ELEMENTS
 ***WARNING: THE *ELEMENT OUTPUT OPTION IS NOT SUPPORTED FOR USER ELEMENTS

                              ANALYSIS DATACHECK COMPLETE
                              WITH      8 WARNING MESSAGES ON THE DAT FILE

     JOB TIME SUMMARY
       USER TIME (SEC)      =     0.75    
       SYSTEM TIME (SEC)    =     0.17    
       TOTAL CPU TIME (SEC) =     0.92    
       WALLCLOCK TIME (SEC) =            1
```

---

## 4. Compute Node Preflight & Compiler Transcript (`pbs_execution.log`)

```text
=== PBS Preflight Check for F1728_CASE1_PILOT ===
2026-11-13T16:17:34Z
mnode105.cluster
Scratch disk space confirmed: 19419 GB available.
User subroutine hash verified: ce8d5edcd2911dcb018bb15275271f874e7ea62b8fb48cf4a8297469a83acdd6
Donor ODB confirmed: /scratch9/pr21vyci/runs/mode1_package46_coarse_fine_preanalysis/PK_M1_COARSE_FINE_CONT.odb (68M)
/cluster/stages/2024.0/software/intel/2024.2/compiler/2024.2/bin/ifort
/cluster/application/abaqus/2023/Commands/abaqus
=== Executing Unified Method A Framework Remeshing Pipeline (Case 1 Mode-I) ===
2026-11-13T16:17:35Z
Abaqus License Manager checked out the following license:
"cae" from Flexnet server license4.imfd.tu-freiberg.de
<15 out of 20 licenses remain available>.
```

---

## 5. CAE Native Remeshing and Production Deck Build Log (`abaqus.rpy`)

```python
from abaqus import *
from abaqusConstants import *
session.Viewport(name='Viewport: 1', origin=(1.36719, 1.36719), width=201.25, height=135.625)
session.viewports['Viewport: 1'].makeCurrent()
from driverUtils import executeOnCaeStartup
executeOnCaeStartup()
execfile('/scratch9/pr21vyci/runs/f1728_case1_pilot/reusable_2d_adaptive_framework.py', __main__.__dict__)
#: Loaded Benchmark: Pandey & Kumar (2025) Section 4.1 Mode-I Edge-Cracked Plate (Case: case_1, Type: STRAIGHT_NOTCH_PLATE)
#: 
#: Executing Unified Method A Pipeline for case_1 (FAIL-CLOSED)...
#: The model "Model_MethodA_case_1" has been created.
#: Model: /scratch9/pr21vyci/runs/mode1_package46_coarse_fine_preanalysis/PK_M1_COARSE_FINE_CONT.odb
#: Number of Assemblies:         1
#: Number of Assembly instances: 0
#: Number of Part instances:     1
#: Number of Meshes:             1
#: Number of Element Sets:       2
#: Number of Node Sets:          6
#: Number of Steps:              1
#: Pipeline Status: SUCCESS
#:   Physical Mesh:   /scratch9/pr21vyci/runs/f1728_case1_pilot/PK_F1728_CASE_1_ADAPT_PHYS.inp
#:   Production Deck: /scratch9/pr21vyci/runs/f1728_case1_pilot/PK_F1728_CASE_1_PROD.inp
#:   Audit Summary:   /scratch9/pr21vyci/runs/f1728_case1_pilot/PK_F1728_CASE_1_AUDIT.json
print 'RT script done'
#: RT script done
```
