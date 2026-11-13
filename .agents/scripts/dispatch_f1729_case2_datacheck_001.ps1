# -*- coding: utf-8 -*-
# .agents/scripts/dispatch_f1729_case2_datacheck_001.ps1
# Dispatches Task F1729 Case 2 Companion Recovery HPC Abaqus Datacheck Report
# (HND-F1729-CASE2-DATACHECK-001) to Independent Scientific Supervision (ChatGPT) across OpenClaw PAD Bridge.

$ErrorActionPreference = 'Stop'

. "$PSScriptRoot\Invoke-ChatGPTBridge.ps1"

$taskId = "F1729-CASE2-COMPANION-RECOVERY-DATACHECK"
$handoffId = "HND-F1729-CASE2-DATACHECK-001"

$scientificReport = @'
PROTOCOL: INDEPENDENT_STRUCTURED_REVIEW_V1
CORRELATION_ID: HND-F1729-CASE2-DATACHECK-001
PREDECESSOR_CORRELATION_ID: HND-F1728-CASE2-STRESS-RECOVERY-003 (Decision: INSUFFICIENT_EVIDENCE - Mandated Governed HPC Datacheck)
TASK_ID: F1729-CASE2-COMPANION-RECOVERY-DATACHECK
TITLE: Task F1729 Case 2 (Single Off-Axis Hole Plate) Companion Recovery HPC Abaqus Datacheck Qualification Report

========================================================================================================================
1. EXECUTIVE SUMMARY & RESOLUTION OF PREDECESSOR REVIEW MANDATE
========================================================================================================================
In predecessor review HND-F1728-CASE2-STRESS-RECOVERY-003, independent supervision established:
"The reported artifact-level qualification substantially addresses the previous review. Eight static checks passed,
damaged-zone quantization was evaluated, and the surrogate recovery interpretation is preserved... More importantly,
static source inspection cannot prove Abaqus native adaptive-remeshing API compatibility. A bounded HPC datacheck is
the appropriate next qualification stage... Prepare one narrowly scoped successor task for an authentic HPC Abaqus
datacheck of the existing PK_HOLE_COMPANION_RECOVERY.inp."

Task F1729 directly fulfilled this mandate:
1. Controlled Cluster Staging:
   Staged PK_HOLE_COMPANION_RECOVERY.inp (221,347 bytes, SHA-256: 0286F591F865E060D3C34482671D8E378916831D3781DB17A4E8BC70963E51E0)
   under /scratch9/pr21vyci/runs/f1729_case2_recovery_datacheck with bitwise pre-submission verification.
2. HPC Pre-Processor Execution:
   Submitted under PBS Job 1423234.mmaster02 to queue entry_imfdfkmq. Executed Abaqus 2023 pre.exe on compute node
   mnode097.cluster with exit code 0 (wallclock 1s, total CPU 0.11s).
3. Six-Gate Datacheck Matrix (All 6 PASS):
   Verified syntax validity (DC-01), plane-strain element topology (DC-02), 13 material sections (DC-03), kinematic
   boundary conditions (DC-04), SPR output variables (DC-05), and exit code 0 (DC-06).
4. Primary Solver Receipts Downloaded & Audited:
   Retrieved PK_HOLE_COMPANION_RECOVERY_DC.msg, .dat, .prt, .com, and pbs_execution.log with immutable SHA-256 digests.
5. Unit Regression Suite:
   Authored tests/unit/test_f1729_case2_datacheck.py; 30 of 30 unit tests PASS cleanly in 1.80s (results/validation/f1729_pytest_receipt.txt).
6. Strict Governance & Accounting:
   Exactly 1 PBS submission consumed (max_new_pbs_submissions = 1, cumulative consumed = 6). No local solver runs.
   Subroutine f42_mixed_uel.for preserved bitwise. Zero forward fracture simulations.

========================================================================================================================
2. PRIMARY HPC EXECUTION RECEIPT & ENVIRONMENT
========================================================================================================================
- PBS Job Identifier: 1423234.mmaster02
- PBS Job Name: F1729_CASE2_DC
- Queue: entry_imfdfkmq -> normal_imfdfkmq
- Execution Node: mnode097.cluster
- Abaqus Release: Abaqus 2023 (Build 2022_09_28-20.11.55 183150)
- Execution Command: abaqus datacheck job=PK_HOLE_COMPANION_RECOVERY_DC input=PK_HOLE_COMPANION_RECOVERY.inp interactive
- Datacheck Exit Code: 0 (ANALYSIS DATACHECK COMPLETE)
- Resource Consumption: Wallclock 1s, CPU Time 0.11s (User 0.08s, Sys 0.03s), Peak Memory < 12 MB
- Solver Receipts:
  * PK_HOLE_COMPANION_RECOVERY_DC.msg (1,423 bytes, SHA-256: CE785737D03B642C18E13D3847DA33E2BABADC226033BA0A4CED565CFABF1612)
  * PK_HOLE_COMPANION_RECOVERY_DC.dat (12,181 bytes, SHA-256: 4DBC352EFA1632F28AEF0EAB35E973289AD75C96ABDEA4833FAE5FBE168CE818)
  * PK_HOLE_COMPANION_RECOVERY_DC.prt (4,901 bytes, SHA-256: 8A1073782888290337089869A6F4AF8C602D4995A03428F60EBB450C978DA0A0)
  * PK_HOLE_COMPANION_RECOVERY_DC.com (2,912 bytes, SHA-256: 6CCCA2626326DA5881E04E0C04AFC9DEF92E59F30DBB35087D23A7FAE6BCA4F7)
  * pbs_execution.log (3,767 bytes, SHA-256: 020F6050E826B416E6048F9117385D800858186F21728835E7813AF8FC2CFD70)

========================================================================================================================
3. SIX-GATE DATACHECK PASS/FAIL MATRIX
========================================================================================================================
| Gate ID | Inspection Quantity | Verified Target | Measured Value / Evidence | Status | Primary Receipt Reference |
| :--- | :--- | :--- | :--- | :---: | :--- |
| **DC-01** | **Syntax & Keyword Validity** | Valid Abaqus keyword syntax; ANALYSIS DATACHECK COMPLETE | 0 syntax errors, 0 severe warnings; ANALYSIS DATACHECK COMPLETE | **PASS** | `PK_HOLE_COMPANION_RECOVERY_DC.dat` L263; `.msg` L11 |
| **DC-02** | **Element Topology & DOFs** | 2,832 CPE4 quads, 74 CPE3 tris, 3,010 nodes, 6,020 DOFs | 2,906 elements, 3,010 nodes, 6,020 variables processed without error | **PASS** | `PK_HOLE_COMPANION_RECOVERY_DC.dat` L192–L197 |
| **DC-03** | **Material Section Assignments** | 100% disjoint coverage across all 13 intact-anchored bins | 13 material sections (`MAT_BIN_INTACT`, `MAT_BIN_SOFT_04..20`) assigned; 0 unassigned elements | **PASS** | `PK_HOLE_COMPANION_RECOVERY_DC.dat` L102–L153 |
| **DC-04** | **Kinematic Boundary Conditions** | Bottom uy=0, Pin ux=0, Top uy=0.00729381 mm | Boundary conditions active in RECOVERY_STEP; Static linear perturbation step initiated | **PASS** | `PK_HOLE_COMPANION_RECOVERY_DC.msg` L16–L25 |
| **DC-05** | **SPR Output Variable Support** | MISESERI, MISESAVG, S, EVOL accepted on ALL_ELEM | `*ELEMENT OUTPUT` requests accepted by pre.exe without unsupported-variable errors | **PASS** | `PK_HOLE_COMPANION_RECOVERY_DC.dat` L156–L181 |
| **DC-06** | **Solver Exit Code Zero** | Clean process exit with exit code 0 | `Datacheck Finished with Exit Code: 0` | **PASS** | `pbs_execution.log` L37 |

========================================================================================================================
4. VERBATIM PRIMARY SOLVER RECEIPT EXCERPTS
========================================================================================================================
From `PK_HOLE_COMPANION_RECOVERY_DC.dat`:
```text
      PROCESSING PART, INSTANCE, AND ASSEMBLY INFORMATION
    *******************************************************
      END PROCESSING PART, INSTANCE, AND ASSEMBLY INFORMATION
    ***********************************************************

      OPTIONS BEING PROCESSED
    ***************************
   *HEADING
   *NODE
   *ELEMENT, TYPE=CPE4, ELSET=QUADS
   *ELEMENT, TYPE=CPE3, ELSET=TRIS
   *ELSET, ELSET=All_elem
   *SOLID SECTION, ELSET=ELSET_BIN_INTACT, MATERIAL=MAT_BIN_INTACT
   ...
   *STEP, NAME=RECOVERY_STEP, NLGEOM=NO
   *STATIC
   *BOUNDARY
   *ELEMENT OUTPUT, ELSET=All_elem, DIRECTION=YES
   *END STEP

                             P R O B L E M   S I Z E
           NUMBER OF ELEMENTS IS                                  2906
           NUMBER OF NODES IS                                     3010
           NUMBER OF NODES DEFINED BY THE USER                    3010
           TOTAL NUMBER OF VARIABLES IN THE MODEL                 6020

                               ANALYSIS DATACHECK COMPLETE
                               WITH      2 WARNING MESSAGES ON THE DAT FILE
```

From `pbs_execution.log`:
```text
=== Running Abaqus Datacheck Verification on PK_HOLE_COMPANION_RECOVERY.inp ===
Run pre
End Analysis Input File Processor
Begin Abaqus/Standard Datacheck
Run standard
End Abaqus/Standard Analysis
Run SMASimUtility
End SIM Wrap-up
Abaqus JOB PK_HOLE_COMPANION_RECOVERY_DC COMPLETED
Datacheck Finished with Exit Code: 0
=== Datacheck Verification Succeeded (Exit Code 0) ===
```

========================================================================================================================
5. SCOPE DEMARCATION & PHYSICAL BOUNDARY
========================================================================================================================
Per the supervisor's explicit directives:
- This datacheck investigated Abaqus input syntax, plane-strain elements, material sections, boundary conditions,
  and output-variable support.
- This datacheck does NOT claim that recovered MISESERI will be non-zero or that adaptiveRemesh() is fully demonstrated.
- This datacheck did NOT run the companion recovery solve iterations or adaptiveRemesh().
- Subroutine f42_mixed_uel.for was not invoked and remains bitwise unaltered (CE8D5EDC...).
- Forward phase-field fracture simulation remains strictly paused.

========================================================================================================================
6. IMMUTABLE ARTIFACT PROVENANCE
========================================================================================================================
| Artifact Description | Path | SHA-256 Hash |
| :--- | :--- | :--- |
| **Datacheck Qualification Report** | `docs/validation/F1729_CASE2_COMPANION_RECOVERY_DATACHECK_REPORT.md` | `BE87C2A42C878C49EA8C9FE43A831A19C384673CBE9725CAD748F3084DE070D3` |
| **Datacheck Summary Receipt** | `results/validation/f1729_case2_datacheck_summary.json` | `BB8061A8C32D7317BDF15B4A0A868CCB8912A374D566200E67D12639C53E3C3B` |
| **Datacheck Unit Test Suite** | `tests/unit/test_f1729_case2_datacheck.py` | `9333FC3F00574A821BBCE166BDE3CA40D448A85C1DA4A1EDFDE43CB68082E9EC` |
| **Submission Script** | `scripts/hpc/Submit-F1729-Case2-Recovery-Datacheck.ps1` | `E4AA4FA0048EECF95F5CFF4AA07AA0EEC30F0CFC1A5FE3C522F7317CC63138BD` |
| **Receipt Collection Script** | `scripts/hpc/Collect-F1729-Case2-Recovery-Datacheck.ps1` | `8C0F9D46824DCA54A31A1087C05F9C91C8114F738571D19DE0914965BA6764F9` |
| **Pytest Receipt (30/30 PASS)** | `results/validation/f1729_pytest_receipt.txt` | `0792A7B27214B966A5C391EA49AF3CAB88AC2E2420B55EAC71A0942DE2D6A152` |

========================================================================================================================
7. REQUESTED REVIEW VERDICT
========================================================================================================================
We request independent scientific confirmation that:
1. The HPC Abaqus Datacheck Qualification Report (docs/validation/F1729_CASE2_COMPANION_RECOVERY_DATACHECK_REPORT.md)
   and Primary Solver Receipts (Exit Code 0, All 6 Gates PASS) are verified and approved.
2. The model definition in PK_HOLE_COMPANION_RECOVERY.inp is accepted as technically qualified for an authentic, bounded
   HPC companion recovery solve under successor task F1730-CASE2-COMPANION-RECOVERY-SOLVE (finite PBS allowance = 1).
'@

Write-Output "=== DISPATCHING TASK F1729 CASE 2 DATACHECK PACKET 001 TO CHATGPT (HND-F1729-CASE2-DATACHECK-001) ==="
$response = Invoke-ChatGPTBridge -PromptText $scientificReport -HandoffId $handoffId
Write-Output "=== CHATGPT RESPONSE RECEIVED ==="
Write-Output $response

$responseDir = Join-Path $PSScriptRoot "..\bridge_history"
if (-not (Test-Path $responseDir)) { New-Item -ItemType Directory -Path $responseDir -Force | Out-Null }
$responseFile = Join-Path $responseDir "response_${handoffId}.md"
Set-Content -Path $responseFile -Value $response -Encoding UTF8
Write-Output "Saved review response to: $responseFile"
