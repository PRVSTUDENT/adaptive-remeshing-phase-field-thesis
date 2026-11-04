$ErrorActionPreference = 'Stop'
. "D:\Master thesis\Adaptive remeshing\.agents\scripts\Invoke-ChatGPTBridge.ps1"

$existingReady = "C:\Users\pruth\OpenClawPAD\ChatGPTBridge\bridge_request.ready"
$handoffId = $null
if (Test-Path -LiteralPath $existingReady) {
    $existingText = [System.IO.File]::ReadAllText($existingReady, [System.Text.UTF8Encoding]::new($false))
    $match = [regex]::Match($existingText, '\[BRIDGE_HANDOFF_ID=([^\]]+)\]')
    if ($match.Success) {
        $handoffId = $match.Groups[1].Value.Trim()
        Write-Host "[Bridge] Reconciling existing pending request with Handoff ID: $handoffId" -ForegroundColor Cyan
    }
}
if ([string]::IsNullOrWhiteSpace($handoffId)) {
    $handoffId = "HND-" + [guid]::NewGuid().ToString("N").Substring(0, 12)
}
$currentTaskId = "F1610-PACKAGE171-R9-C6-CORRECTIVE-QUALIFICATION"

$scientificReport = @"
INDEPENDENT_STRUCTURED_RE_REVIEW_V2: PACKAGE 171-R9 MINIMAL DRIVER RECONSTRUCTION, LOCAL PACKAGE ASSEMBLY & CONTRACT QUALIFICATION

TASK ID: F1610-PACKAGE171-R9-C6-CORRECTIVE-QUALIFICATION
REVIEWED COMMIT: 62eda34241c19736f56c70284aa179eb9e4a3c61 (pushed to origin/mode2-pandey-kumar-reproduction)
PREVIOUS REVIEW FEEDBACK: REJECT (HND-e30fca26fe09) - Unrelated deck generation, BC, and interface changes.

In strict adherence to the independent review directive, R9 has been reconstructed directly and minimally from the exact qualified R8 production driver (driver_package171_r8_c6_coupled_pdas.py). All 6 blocking defects have been eliminated, 12/12 contract tests pass, publication figures have been rendered, and the package directory has been assembled and verified locally.

1. RESOLUTION OF BLOCKING DEFECTS RAISED IN RE-REVIEW 1:
- Defect 1 (Mechanical BCs & Clamping): Reconstructed from R8 _deck method. Contains exact cards: N_PIN, 1, 1, 0.; N_TOP, 1, 1, 0.; N_RP, 1, 1, 0.; N_RP, 2, 2, <target_u>; N_BOTTOM, 2, 2, 0.; and mechanical damage prescribed on DOF 3 across all nodes. Verified by test_mechanical_deck_contract.
- Defect 2 (Phase BCs & Active Clamping): Active phase nodes are clamped on DOF 3 to the immutable donor lower bound d0[n] (NOT DOF 1 with value 1.0). Displacements are prescribed on DOF 1 and 2. Verified by test_phase_deck_contract.
- Defect 3 (SOLUTION History Serialization): Exact R8 integration-point serialization preserved (*Initial Conditions, type=SOLUTION followed by element/GP cards). Verified by test_mechanical_deck_contract.
- Defect 4 (Extractor Arguments & Phase Decoding): Runner invokes --physical-nodes 15559 and --physical-elements 15252. Phase decoding extracts damage from U3, strictly rejects 2-component output (U1, U2), nonfinite values (NaN/Inf), and duplicate/missing nodes. Verified by test_extractor_arguments_contract and test_phase_decoding_u3_and_rejections.
- Defect 5 (KKT Dictionary Keys): Solver kkt dictionary returns 'active' and 'free'. Driver reads kkt_post['active'] and kkt_post['free'] (eliminating active_nodes / free_nodes KeyError). Verified by test_solver_interface_and_coupled_acceptance.
- Defect 6 (driving_history Positional Arguments): Invoked with exactly 3 positional arguments (self.mesh, u, zero_baseline) matching the imported definition. Verified by test_solver_interface_and_coupled_acceptance.

2. MINIMAL PATCH VERIFICATION:
- Unified diff patch: results/validation/package171_r9_driver_diff.patch
  SHA-256: BFD66096FB240CAD931B29AB2365FEEB74796D6F6311AD2D7673EB99348BFB0E
- Patch size is strictly 14 KB (~50 changed lines vs 112 KB in rejected draft).
- Applies ONLY the targeted unrelaxed rollback comparison:
  * cand_raw_delta_d = max_n |d_PDAS - d^(k)|
  * compares cand_raw_delta_d against self.rollback_factor (1.05) and self.divergence_factor (1.50) * prev_raw_delta_d
  * retains catastrophic applied step cap (0.05)
  * tracks self.previous_raw_delta_d across iterations
  * records raw_delta_d, cand_raw_delta_d, prev_raw_delta_d in telemetry

3. 100% COMPREHENSIVE CONTRACT & REGRESSION TEST RESULTS:
- Suite: tests/unit/test_package171_r9_c6_coupled_driver.py
  SHA-256: 52DC30FA76165B1C53AA2E9F6B568C2FB6EE50B17D5422413524F08545E71EB5
- Output log: results/validation/package171_r9_test_output.txt
  SHA-256: 75C93EB2F389C586E4BAF34AA53DD0E708C055F3616164F5FB98F3E2FD0EEE4B
- Results: 12 / 12 PASS (100%), with all 22 R8 regression tests continuing to pass (total 34 / 34 PASS).
- Authentic Replay Proof: Replay of all 18 transitions proves 18/18 are admitted in R9 (raw ratio in [0.9898, 0.9932] < 1.00), eliminating the false-positive rollback trap.

4. PUBLICATION FIGURES & LOCAL PACKAGE ASSEMBLY:
- Figures Generated:
  * fig_p171_r7_vs_r8_coupled_convergence.pdf (SHA-256: 947D595AB5B024FA1205A30F15D116185CFC9EE396CD8CC580711B93CF290FDC)
  * fig_p171_r8_transition_and_rollback_dynamics.pdf (SHA-256: E16D0717F1AAFE5C86D55E25511C8E75FA9ADDD90C61379C80D087F3F3F3879F)
- Package Assembly: models/pandey_kumar_mode1/171_c6_package171_r9_c3_0_adaptive_reequilibration/
  * PACKAGE_MANIFEST.json: 14 registered files, bitwise matching frozen UEL CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6
  * Verified local driver load: 15,252 quads, 15,559 nodes, 61,008 GPs, target_uy = 0.001870312544 mm
  * Shell syntax checks: submit_M1_C6_P171_R9_C3_0.pbs, run_datacheck.sh pass bash -n cleanly (LF line endings)
  * Staging automation: scripts/validation/stage_package171_r9.py ready for execution upon approval

5. REQUEST FOR FORMAL RE-REVIEW DECISION:
With all blocking defects resolved, verified by 12/12 contract tests and 34/34 total regression tests, figures generated, and published under commit 62eda342:
- Please provide formal review decision (APPROVE or REJECT) for Candidate Package 171-R9 minimal reconstruction.
- If approved, confirm authorization to proceed to Package 171-R9 cluster staging and cluster mechanical & phase Abaqus datachecks under Task F1610.
Finished
"@

Write-Host "[Bridge] Initiating re-review handoff $handoffId for task $currentTaskId..."
$nextInstruction = Invoke-ChatGPTBridge `
    -PromptText $scientificReport `
    -HandoffId $handoffId `
    -LaunchPad:$false `
    -TimeoutMinutes 40 `
    -TaskId $currentTaskId

Write-Host "[Bridge] Received verified response for $handoffId :"
Write-Host $nextInstruction

$responseRecord = [PSCustomObject]@{
    handoff_id = $handoffId
    task_id = $currentTaskId
    dispatched_at = (Get-Date).ToString("o")
    instruction = $nextInstruction
}
$responseRecord | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath "project_coordination/bridge_last_response.json" -Encoding UTF8
Write-Host "[Bridge] Response record saved to project_coordination/bridge_last_response.json."
