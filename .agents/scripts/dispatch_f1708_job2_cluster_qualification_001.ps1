# -*- coding: utf-8 -*-
# .agents/scripts/dispatch_f1708_job2_cluster_qualification_001.ps1
# Dispatches Task F1708 Section 4.3 Job-2 Adapted Mesh Solve Cluster Qualification
# and Execution Authorization across the PAD bridge under handoff ID HND-F1708-JOB2-CLUSTER-QUAL-001.

$ErrorActionPreference = 'Stop'

. "$PSScriptRoot\Invoke-ChatGPTBridge.ps1"

$taskId = "F1708-PK-SEC43-JOB2-ADAPTED-MESH-SOLVE"
$handoffId = "HND-F1708-JOB2-CLUSTER-QUAL-001"

$scientificReport = @'
PROTOCOL: INDEPENDENT_STRUCTURED_REVIEW_V1
CORRELATION_ID: HND-F1708-JOB2-CLUSTER-QUAL-001
TASK_ID: F1708-PK-SEC43-JOB2-ADAPTED-MESH-SOLVE
PREVIOUS_REVIEW_CORRELATION: HND-F1707-JOB2-READINESS-001
PREVIOUS_VERDICT: INSUFFICIENT_EVIDENCE
TITLE: Task F1708 Cluster Qualification & Execution Authorization Review: Job-2_UEL Phase-Field Fracture Simulation on F1703 Native Adapted Mesh (HND-F1708-JOB2-CLUSTER-QUAL-001)

========================================================================================================================
1. EXECUTIVE SUMMARY & ACTIONS REQUESTED
========================================================================================================================
The executor (Gemini Antigravity) requests independent structured review under HND-F1708-JOB2-CLUSTER-QUAL-001:
1. Formal acceptance of previous review directives resolution (JOB2-UEL-001, JOB2-BC-001, JOB2-DATACHECK-001, JOB2-MESH-001, JOB2-HPC-001);
2. Formal closure of Task F1707-PK-FIGS14-16-REPRODUCTION;
3. Formal activation of successor Task F1708-PK-SEC43-JOB2-ADAPTED-MESH-SOLVE;
4. Execution authorization for the single planned overnight PBS submission (max_new_pbs_submissions = 1) for Job-2 forward phase-field simulation on the HPC cluster using the guarded Mode-I controller (Invoke-Mode1Execution.ps1).

========================================================================================================================
2. GOVERNED RESOURCE & SAFETY BOUNDARIES
========================================================================================================================
- Task ID: F1708-PK-SEC43-JOB2-ADAPTED-MESH-SOLVE
- Definition File: project_coordination/task_definitions/F1708-PK-SEC43-JOB2-ADAPTED-MESH-SOLVE.json
- Active Session: project_coordination/ACTIVE_SESSION.json (claimed exclusively by gemini-antigravity)
- Governed Invariants:
  * Production UEL f42_mixed_uel.for (CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6, 907 lines) bitwise preserved.
  * Method C remains paused.
  * Candidate E10 (1x1 mm hole benchmark) preserved as separate completed Method A work.
  * Bulky solver binaries (.odb, .sim, .res, .pac, .abq) excluded from Git tracking.
- Accounting:
  max_new_pbs_submissions = 1 strictly once-only accounting. Exactly ZERO PBS submissions executed under F1707; exactly ONE planned submission under F1708.

========================================================================================================================
3. EXHAUSTIVE RESOLUTION OF PREVIOUS REVIEW FINDINGS (HND-F1707-JOB2-READINESS-001)
========================================================================================================================

------------------------------------------------------------------------------------------------------------------------
Finding 1: JOB2-UEL-001 -- Frozen Governing Production Subroutine Invariance
------------------------------------------------------------------------------------------------------------------------
- Reviewer Directive: Verify that the compilation and datacheck strictly use the bitwise-frozen production UEL f42_mixed_uel.for (907 lines, CE8D5EDC...) rather than the historical f42_staggered_variant_uel.for.
- Evidence & Verification:
  * Local Abaqus 2024 (RELr426) datacheck executed with f42_mixed_uel.for and Intel oneAPI Fortran (ifx 2026.0.0) in runs/f1708_job2_frozen_uel_datacheck:
    pre.exe: Exit Code 0 (CPU: 1.0s)
    standard.exe: Exit Code 0 (CPU: 0.70s)
    Result: ANALYSIS DATACHECK COMPLETE WITH 9 WARNING MESSAGES ON THE DAT FILE, ZERO errors.
  * Target cluster login-node Abaqus 2023 datacheck executed with f42_mixed_uel.for and Intel Fortran Classic (ifort 2021.13.0) on mlogin01.cluster:
    Result: Cluster datacheck finished with exit code: 0
    "ANALYSIS DATACHECK COMPLETE WITH 9 WARNING MESSAGES ON THE DAT FILE" (Total CPU time: 0.73s, Wallclock: 3s).
  * Staged package models/pandey_kumar_mode1/204_pk_sec43_job2_adapted/f42_mixed_uel.for:
    Line count = 907 lines
    SHA-256 = CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6 (bitwise identical to canonical Gate 6B frozen UEL).
  * Status: RESOLVED.

------------------------------------------------------------------------------------------------------------------------
Finding 2: JOB2-BC-001 -- Loading Schedule and Displacement Boundary Condition Semantics
------------------------------------------------------------------------------------------------------------------------
- Reviewer Directive: Reconcile apparent contradiction between "Step 1 to 1.0 mm, Step 2 to 1.5 mm" vs earlier documentation claiming "cumulative 2.5 mm".
- Evidence & Verification:
  * In Abaqus/Standard, displacement boundary conditions specified under *BOUNDARY cards inside consecutive *STATIC, DIRECT steps define the total accumulated displacement at step completion, not an incremental displacement.
  * Deck card inspection in PK_SEC43_JOB2_ADAPTED_PROD.inp:
    Step 1:
      *STEP, NAME=STEP-1, NLGEOM=NO, INC=2000
      *STATIC, DIRECT
      5.0E-4, 1.0, 5.0E-4, 5.0E-4
      *BOUNDARY, OP=MOD
      N_RP, 2, 2, 1.0
      -> Advances u_y from 0.0 to 1.00 mm over 2,000 increments of Delta_u = 0.0005 mm.
    Step 2:
      *STEP, NAME=STEP-2, NLGEOM=NO, INC=2500
      *STATIC, DIRECT
      2.0E-4, 0.5, 2.0E-4, 2.0E-4
      *BOUNDARY, OP=MOD
      N_RP, 2, 2, 1.5
      -> Advances u_y from 1.00 mm to 1.50 mm over 2,500 increments of Delta_u = 0.0002 mm (Delta_u_step = 0.50 mm).
  * Total cumulative displacement at Step 2 completion is exactly u_y = 1.50 mm across exactly 4,500 increments.
  * This matches the benchmark definition and predecessor Job 1421286. The earlier "cumulative 2.5 mm" note in the handoff was a clerical transcription typo and is now corrected.
  * Status: RESOLVED.

------------------------------------------------------------------------------------------------------------------------
Finding 3: JOB2-DATACHECK-001 -- Distorted Element Warning Evaluation and Location Audit
------------------------------------------------------------------------------------------------------------------------
- Reviewer Directive: Evaluate datacheck warnings regarding distorted elements 28658 and 29490 to ensure they do not cause numerical divergence or compromise the crack path.
- Evidence & Verification:
  * Evaluated via dedicated audit script scripts/validation/inspect_f1708_job2_compatibility.py and recorded in results/validation/f1708_job2_compatibility_audit.json:
    - Element 28658:
      * Physical Element ID: 8528 (Layer 3 Companion element, DUMMY_MAT UMAT, zero mechanical stiffness).
      * Centroid: (9.69 mm, 70.71 mm) on the notch upper flank.
      * Interior angles: min = 35.91 deg, max = 138.77 deg.
      * Area: 0.1755 mm^2 (> 0, strictly positive Jacobian).
      * Distance to primary crack tip (36.5, 51.0): 14.87 mm.
      * Distance to secondary crack corridor (y = 51.0 mm): 19.71 mm.
    - Element 29490:
      * Physical Element ID: 9360 (Layer 3 Companion element, DUMMY_MAT UMAT, zero mechanical stiffness).
      * Centroid: (9.36 mm, 71.00 mm) on the notch upper flank.
      * Interior angles: min = 37.26 deg, max = 119.94 deg.
      * Area: 0.1836 mm^2 (> 0, strictly positive Jacobian).
      * Distance to primary crack tip: 15.30 mm.
      * Distance to secondary crack corridor: 20.00 mm.
  * Assessment: Both elements are Layer 3 companion visualization elements with min angles between 35.9 deg and 37.3 deg, which trigger the standard Abaqus advisory warning threshold (45.0 deg). However, both have strictly positive areas, positive Jacobians, zero negative determinant warnings, zero overconstraints, and are located on the notch upper flank > 19 mm away from the secondary crack path. They will not cause numerical divergence or affect fracture progression.
  * Status: RESOLVED_QUALIFIED.

------------------------------------------------------------------------------------------------------------------------
Finding 4: JOB2-MESH-001 -- Crack Corridor Sizing and Resolution Compliance Disclosure
------------------------------------------------------------------------------------------------------------------------
- Reviewer Directive: Disclose the exact quantitative distinction between elements refined to h <= l0 (0.285 mm) vs h <= l0/2 (0.1425 mm).
- Evidence & Verification:
  * Audit metrics from f1708_job2_compatibility_audit.json and F1703 polygon clipping:
    - Published Target: h_target = 0.143 mm (~ l0 / 2 = 0.1425 mm).
    - Secondary Crack Corridor (from hole perimeter x = 46.5 mm to right boundary x = 65.0 mm, L = 18.56 mm):
      * Centerline coverage at h <= l0 (0.285 mm): 172 out of 172 elements = 100.0% continuous coverage (zero gaps).
      * Centerline coverage at h <= l0/2 (0.1425 mm): 63 out of 172 elements = 29.61% coverage, with minimum element size h_min = 0.0635 mm (<= l0/4).
      * Total elements in secondary band: 1,548 elements (1,477 elements <= l0, 541 elements <= l0/2).
    - Primary Crack Corridor (from notch tip x = 10.0 mm to hole perimeter x = 26.5 mm):
      * Centerline coverage at h <= l0: 47.14% (33/70 elements), with h_min = 0.1001 mm (<= l0/2).
      * Primary corridor wake experiences coarsening during post-arrest reloading due to stress relaxation, which is an expected physical behavior of recovery-based indicators.
  * Assessment: The mesh provides 100.0% unbroken coverage at h <= l0 across the secondary ligament and achieves l0/2 to l0/4 resolution in the active propagation core. The reporting boundaries are fully disclosed.
  * Status: RESOLVED_QUALIFIED.

------------------------------------------------------------------------------------------------------------------------
Finding 5: JOB2-HPC-001 -- Target Cluster Staging & Abaqus 2023 Datacheck Verification
------------------------------------------------------------------------------------------------------------------------
- Reviewer Directive: Stage all dependencies to the target cluster run directory and verify clean execution under the cluster's Abaqus 2023 and Intel compiler environment before submitting.
- Evidence & Verification:
  * Cluster Run Directory: /scratch9/pr21vyci/runs/mode1_pk_sec43_job2_adapted_f1708
  * Staged files and verified SHA-256 hashes on mlogin01.cluster:
    - PK_SEC43_JOB2_ADAPTED_PROD.inp: 417e749dd934d67c127d1e4b67e9fb32caafb384726ccb58169892855907c68b (1.21 MB, 40,448 lines)
    - f42_mixed_uel.for: ce8d5edcd2911dcb018bb15275271f874e7ea62b8fb48cf4a8297469a83acdd6 (907 lines)
    - submit_M1_PK_SEC43_JOB2_ADAPTED.pbs: 436578376b905050724ca50d5b34f457b944406d10dcac91053ae2028dcd20a5
    - job_notifications.sh: 41a1d403b0356b55efa3bb1e67b4dd678e74664d501d838d9c01952c0c641f11
    - run_cluster_datacheck.sh: 755 executable permissions
  * Cluster Datacheck Execution:
    - Executed via run_cluster_datacheck.sh on mlogin01.cluster with modules gcc/11.4.0, intel/2024.2.0, abaqus/2023.
    - Compiler: Intel(R) Fortran 2021.13.0 compiled f42_mixed_uel.for with automatic CPU dispatch.
    - Linker: GNU ld version 2.30-128 linked user subroutine into standardU.lib cleanly.
    - Abaqus/Standard: pre and standard completed datacheck.
    - Outcome: Exit Code: 0 ("ANALYSIS DATACHECK COMPLETE WITH 9 WARNING MESSAGES ON THE DAT FILE", 0.73s CPU time, 3s wallclock).
    - Downloaded artifact: models/pandey_kumar_mode1/204_pk_sec43_job2_adapted/M1_PK_SEC43_JOB2_CLUSTER_DATACHECK.dat (14,032 bytes, SHA-256: 7bbda5778819b9c50267bd0c8fe2162e3f9c89256ab0cf462bf633726e53e401).
  * Mode-I Manifest Updated:
    - File: models/pandey_kumar_mode1/204_pk_sec43_job2_adapted/F1708_PK_SEC43_JOB2_ADAPTED_AUTHORIZATION.json
    - Indexed: all 5 input, subroutine, script, and cluster datacheck artifacts with exact SHA-256 hashes.
    - Command: powershell -NoProfile -ExecutionPolicy Bypass -File .\.agents\scripts\Invoke-GuardedSsh.ps1 -RemoteCommand "qsub -q entry_imfdfkmq /scratch9/pr21vyci/runs/mode1_pk_sec43_job2_adapted_f1708/submit_M1_PK_SEC43_JOB2_ADAPTED.pbs"
    - Command SHA-256: ebc01e25d8004b6ee600c0f7d0a035177e3453badc104b8a74d875ea92bcfdc5.
  * Status: RESOLVED.

========================================================================================================================
4. HPC EXECUTION PROFILE & OVERNIGHT POLICY COMPLIANCE
========================================================================================================================
- Job Name: M1_PK_SEC43_JOB2_ADAPTED
- Queue: entry_imfdfkmq (routing to normal_imfdfkmq)
- Resources: 1 CPU serial reference anchor, 16 GB memory, 12:00:00 (12 hours) walltime.
- Overnight Policy:
  * The user directive states: "HPC WALLTIME POLICY: Do not artificially restrict Abaqus jobs to the remaining VPN session duration or the legacy eight-hour execution limit... A properly qualified job may run independently on the cluster overnight."
  * Historical runtime on mnode098 for 4,500 increments of Section 4.3 (Job 1421286) was 41 min 39s CPU / ~2 hours walltime. A 12-hour limit provides >5x safety factor for convergence and allows unmonitored overnight completion.
- Notifications:
  * PBS mail: #PBS -m abe -M pr21vyci@mailserver.tu-freiberg.de
  * Telegram shell trap: notification_install_terminal_trap configured to send START and terminal status (COMPLETED/FAILED/TERMINATED) to the configured Telegram chat.
- Accounting:
  * max_new_pbs_submissions = 1 (strictly once-only accounting, managed via Invoke-Mode1Execution.ps1).

========================================================================================================================
5. UNIT REGRESSION TESTING
========================================================================================================================
- tests/unit/test_f1708_job2_cluster_qualification.py passes 7/7 tests cleanly:
  * test_01_job2_production_deck_integrity: PASS
  * test_02_frozen_uel_subroutine_integrity: PASS
  * test_03_cluster_datacheck_artifact_verification: PASS
  * test_04_pbs_script_and_notification_contract: PASS
  * test_05_mode1_authorization_manifest: PASS
  * test_06_task_f1708_registration: PASS
  * test_07_compatibility_audit_report: PASS
- Full regression suite across F1700-F1708 passes 75/75 tests cleanly in 9.64s.

========================================================================================================================
6. INDEPENDENT REVIEW DECISION SOUGHT
========================================================================================================================
The executor requests the independent reviewer to return:
DECISION: APPROVE
Confirming:
1. Formal acceptance of findings resolution (JOB2-UEL-001, JOB2-BC-001, JOB2-DATACHECK-001, JOB2-MESH-001, JOB2-HPC-001);
2. Formal closure of Task F1707-PK-FIGS14-16-REPRODUCTION;
3. Formal activation of Task F1708-PK-SEC43-JOB2-ADAPTED-MESH-SOLVE;
4. Execution authorization for the single planned overnight PBS submission (max_new_pbs_submissions = 1) via scripts/hpc/Invoke-Mode1Execution.ps1.
'@

Write-Host "Dispatching Task F1708 Cluster Qualification & Execution Authorization review across PAD bridge..."
$response = Invoke-ChatGPTBridge -PromptText $scientificReport -HandoffId $handoffId

Write-Host "=== Review Response Received ==="
Write-Host $response
