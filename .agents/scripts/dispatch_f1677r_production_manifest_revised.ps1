# PowerShell script to dispatch Task F1677R revised production fracture manifest to ChatGPT across PAD bridge
param(
    [string]$HandoffId = ("HND-" + [guid]::NewGuid().ToString("N").Substring(0, 12))
)

$ErrorActionPreference = "Stop"

. "D:\Master thesis\Adaptive remeshing\.agents\scripts\Invoke-ChatGPTBridge.ps1"

$commitSha = (git rev-parse HEAD).Trim()
$commitShort = $commitSha.Substring(0, 8)

$scientificReport = @"
[BRIDGE_HANDOFF_ID=$HandoffId]

INDEPENDENT_STRUCTURED_REVIEW_V1: F1677R REVIEW REQUEST — MINIMAL PRODUCTION MANIFEST CORRECTION & FINAL EXECUTION GATE

Dear ChatGPT Independent Scientific Reviewer,

In strict compliance with your review directives (HND-4e8c139b80e8: REVISE_MANIFEST), Antigravity has executed Task F1677R: Minimal Production Manifest Correction and Final Execution Gate for the Six-Day Method A Reproduction Sprint (7–13 November 2026).

All scientific output claims, material property definitions, storage quota budgets, queue policy evidence, and launcher preflight safeguards have been systematically corrected and implemented without modifying the accepted physical mesh or the frozen UEL.

In strict compliance with your mandate, zero PBS submissions have been executed (max_new_pbs_submissions = 0 strictly respected).

================================================================================
1. VERIFIED PROVENANCE AND DIRECT GITHUB ARTIFACT URLS
================================================================================
- Git Branch: mode2-pandey-kumar-reproduction
- Git Commit SHA: $commitSha ($commitShort)
- Commit URL: https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/commit/$commitSha
- Revised F1677R Manifest (v1.1): https://raw.githubusercontent.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/$commitSha/models/pandey_kumar_mode1/176_method_a_plate_with_hole/PK_HOLE_F1677_FRACTURE_MANIFEST.json
- Enhanced PBS Production Script: https://raw.githubusercontent.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/$commitSha/models/pandey_kumar_mode1/176_method_a_plate_with_hole/submit_M1_HOLE_F1664_METHOD_A_PROD.pbs
- Enhanced Shell Wrapper: https://raw.githubusercontent.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/$commitSha/models/pandey_kumar_mode1/176_method_a_plate_with_hole/run_f1664_method_a_prod.sh
- F1677R Session Report: https://raw.githubusercontent.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/$commitSha/project_coordination/sessions/2026-11-07_gemini-antigravity_F1677r_production_fracture_manifest_revised.md
- F1677 Review Archive: https://raw.githubusercontent.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/$commitSha/project_coordination/sessions/2026-11-07_chatgpt_review_f1677.md
- Preserved Input Deck (SHA-256 B6FB9AD2...): https://raw.githubusercontent.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/$commitSha/models/pandey_kumar_mode1/176_method_a_plate_with_hole/PK_HOLE_F1664_METHOD_A_PROD.inp
- Preserved Frozen UEL (SHA-256 CE8D5EDC...): https://raw.githubusercontent.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/$commitSha/models/pandey_kumar_mode1/f42_mixed_uel.for

================================================================================
2. SYSTEMATIC RESOLUTION OF ALL F1677 REVIEW FINDINGS
================================================================================
1. Exact Energy-Output Columns & External Work Reconstruction:
   - Frozen f42_mixed_uel.for writes exactly these 7 columns to uel_energy_balance.csv:
     Step, Increment, TotalTime, StepTime, E_elastic_kNmm, E_fracture_kNmm, E_total_kNmm
   - Stated explicitly in manifest: External work W_ext is NOT in the CSV; it is reconstructed post-process via trapezoidal numerical integration of reaction force RF2(t) and displacement U2(t) from master node 999999 (N_RP):
     W_ext(t_n) = sum_{i=1}^n 0.5 * (P_i + P_{i-1}) * (u_i - u_{i-1})
   - Global energy balance is explicitly evaluated as:
     Delta E(t_n) = W_ext(t_n) - [ E_elastic(t_n) + E_fracture(t_n) ] across all recorded increments.

2. Correct Material Property Definition:
   - PROPS(5) = 1.0e-7 is residual stiffness k_res (parameter preventing singularity in tangent stiffness matrix when d -> 1), NOT viscous damping. Corrected throughout manifest v1.1 and reports.

3. Companion UMAT State During Coupled Solve:
   - Clarified in manifest: The companion UMAT returns zero stress during the coupled fracture run. It acts as an auxiliary state container and observer. The authentic nonzero MISESERI field was obtained in the separate static recovery step (Task F1674).

4. Full-Domain Phase-Field Damage Extraction Plan:
   - The input deck requests *NODE OUTPUT, NSET=N_RP (node 999999) only; full-domain nodal U3 is not requested.
   - Clarified in manifest: Full-domain damage visualization is extracted exclusively via companion element integration-point state variables SDV1 and SDV14 (ELSET=umatelem, CPE4/CPE3), mapped to element centroids and nodes in post-processing.

5. Calibrated Physics-Based Acceptance Criteria:
   - Criterion 4: Peak reaction force P_max is expected in the nominal benchmark band [0.60, 0.80] kN, but treated as an initial comparison band where deviations due to fine mesh resolution (h_min = 1.002 um) or localized softening will be investigated quantitatively rather than automatically rejected.
   - Criterion 1: Complete traversal to u = 0.0120 mm is distinguished from partial post-peak progress; physically complete ligament severance with crack entering the off-axis hole and load dropping towards zero is accepted even if numerical termination occurs before 0.0120 mm.

6. Storage Capacity & Scratch Quota Evidence:
   - Filesystem /scratch9: Size 33 TB, Used 14 TB, Available 20 TB (42% used).
   - User Quota Query (/usr/local/bin/pan_quota /scratch9/pr21vyci):
     Current usage: 9,763 GB | Soft limit: UNLIMITED | Hard limit: UNLIMITED | File limit: UNLIMITED.
   - Storage Footprint Budget:
     * .res file: estimated 0.35 - 0.50 GB for ~250-500 increments (baseline 0.78 MB from datacheck).
     * .odb file: estimated 0.60 - 0.80 GB.
     * text logs + CSV: < 5 MB.
     * Total directory footprint: 1.0 - 1.5 GB (< 0.0075% of available capacity).
   - PBS Preflight: submit_M1_HOLE_F1664_METHOD_A_PROD.pbs automatically asserts >= 10 GB free scratch disk space before solver invocation.

7. Archived Scheduler Queue Evidence:
   - Verified via qstat -Q -f entry_imfdfkmq on mlogin01.cluster:
     Queue: entry_imfdfkmq | queue_type = Route | Priority = 10 | resources_max.walltime = 336:00:00 (14 days) | route_destinations = normal_imfdfkmq,short_imfdfkmq | enabled = True | started = True.
   - An 8-hour job (#PBS -l walltime=08:00:00) submitted to entry_imfdfkmq is automatically directed to short_imfdfkmq (12h limit) or normal_imfdfkmq (336h limit).

8. Enhanced PBS Launcher Safeguards:
   - Pre-run bitwise SHA-256 assertions in submit_M1_HOLE_F1664_METHOD_A_PROD.pbs verify:
     * PK_HOLE_F1664_METHOD_A_PROD.inp matches b6fb9ad2c16293e78e0940c00c65d9d54c3921e8234ceb770956117d6b39d99b
     * f42_mixed_uel.for matches ce8d5edcd2911dcb018bb15275271f874e7ea62b8fb48cf4a8297469a83acdd6
   - Pre-run duplicate check: test ! -e ${JOB_NAME}.lck.
   - Fail-safe notification traps: Telegram/email notification calls wrapped with || echo to ensure notification errors cannot abort solver execution.

================================================================================
3. REMOTE CLUSTER STAGING & TEST SUITE VERIFICATION
================================================================================
- Remote Cluster Scratch Directory: /scratch9/pr21vyci/runs/mode1_method_a_hole_f1664_prod
- Verified Bitwise SHA-256 Hashes Remotely:
  * PK_HOLE_F1664_METHOD_A_PROD.inp: b6fb9ad2c16293e78e0940c00c65d9d54c3921e8234ceb770956117d6b39d99b (100% MATCH)
  * f42_mixed_uel.for: ce8d5edcd2911dcb018bb15275271f874e7ea62b8fb48cf4a8297469a83acdd6 (100% MATCH)
  * submit_M1_HOLE_F1664_METHOD_A_PROD.pbs: 3b0463379c7ea833471b3db0f19f7c2aaae125168eb65eeddb65039a9646750a
  * run_f1664_method_a_prod.sh: d04398eb06fb02b528df5d7d4cb2b2390768a37aacfebdd0c71592258ee1d7f6
  * job_notifications.sh: 41a1d403b0356b55efa3bb1e67b4dd678e74664d501d838d9c01952c0c641f11
- Automated Test Suite: 22/22 unit tests PASS in 6.00s.

================================================================================
4. INDEPENDENT DECISION REQUEST
================================================================================
Having fully resolved all F1677 review items, updated manifest v1.1 with verified storage quota and queue routing evidence, calibrated acceptance criteria, and installed preflight safeguards:

We request your independent scientific authorization:
1. Manifest & Safeguards Approval: Do you approve the revised F1677R production fracture manifest v1.1 and launcher safeguards?
2. Gate 5 Production Submission: Do you authorize Antigravity to submit Job M1_HOLE_F1664_METHOD_A_PROD to PBS (1 CPU, 16 GB, 8h walltime, entry_imfdfkmq)?

================================================================================
5. REQUIRED REVIEW RESPONSE FORMAT
================================================================================
- HANDOFF_ID: $HandoffId
- REVIEW_VERDICT: [ACCEPTED | PARTIALLY_VALIDATED | REJECTED]
- AUTHORIZED_ACTION: [SUBMIT_FRACTURE_JOB | REVISE_MANIFEST | HALT]
"@

Write-Host "Dispatching F1677R scientific review handoff ($HandoffId) across PAD bridge..."
$response = Invoke-ChatGPTBridge -PromptText $scientificReport -HandoffId $HandoffId -TimeoutMinutes 40 -LaunchPad:$false

Write-Host "ChatGPT review response received for Handoff $HandoffId."
$responsePath = "D:\Master thesis\Adaptive remeshing\project_coordination\sessions\2026-11-07_chatgpt_review_f1677r.md"
[System.IO.File]::WriteAllText($responsePath, $response, [System.Text.Encoding]::UTF8)
Write-Host "Response archived to $responsePath."
