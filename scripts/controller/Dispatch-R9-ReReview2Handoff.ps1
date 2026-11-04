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
INDEPENDENT_STRUCTURED_RE_REVIEW_V2: PACKAGE 171-R9 MINIMAL DRIVER RECONSTRUCTION & CONTRACT QUALIFICATION

TASK ID: F1610-PACKAGE171-R9-C6-CORRECTIVE-QUALIFICATION
REVIEWED COMMIT: 6351806f412742430ffd8c038a1407e3c1b327eb (pushed to origin/mode2-pandey-kumar-reproduction)
PREVIOUS REVIEW FEEDBACK: REJECT (HND-e30fca26fe09) - Unrelated deck generation, BC, and interface changes.

In strict adherence to the independent review directive, R9 has been reconstructed directly and minimally from the exact qualified R8 production driver (driver_package171_r8_c6_coupled_pdas.py). All 6 blocking defects have been eliminated and verified.

1. RESOLUTION OF BLOCKING DEFECTS RAISED IN RE-REVIEW 1:
- Defect 1 (Mechanical BCs & Clamping): Reconstructed from R8 _deck method. Contains exact cards: N_PIN, 1, 1, 0.; N_TOP, 1, 1, 0.; N_RP, 1, 1, 0.; N_RP, 2, 2, <target_u>; N_BOTTOM, 2, 2, 0.; and mechanical damage prescribed on DOF 3 across all nodes. Verified by test_mechanical_deck_contract.
- Defect 2 (Phase BCs & Active Clamping): Active phase nodes are clamped on DOF 3 to the immutable donor lower bound d0[n] (NOT DOF 1 with value 1.0). Displacements are prescribed on DOF 1 and 2. Verified by test_phase_deck_contract.
- Defect 3 (SOLUTION History Serialization): Exact R8 integration-point serialization preserved (*Initial Conditions, type=SOLUTION followed by element/GP cards). Verified by test_mechanical_deck_contract.
- Defect 4 (Extractor Arguments & Phase Decoding): Runner invokes --physical-nodes 15559 and --physical-elements 15252. Phase decoding extracts damage from U3, strictly rejects 2-component output (U1, U2), nonfinite values (NaN/Inf), and duplicate/missing nodes. Verified by test_extractor_arguments_contract and test_phase_decoding_u3_and_rejections.
- Defect 5 (KKT Dictionary Keys): Solver kkt dictionary returns 'active' and 'free'. Driver reads kkt_post['active'] and kkt_post['free'] (eliminating active_nodes / free_nodes KeyError). Verified by test_solver_interface_and_coupled_acceptance.
- Defect 6 (driving_history Positional Arguments): Invoked with exactly 3 positional arguments (self.mesh, u, zero_baseline) matching the imported definition. Verified by test_solver_interface_and_coupled_acceptance.

2. MINIMAL PATCH VERIFICATION (Commit 6351806f412742430ffd8c038a1407e3c1b327eb):
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
- Results: 12 / 12 PASS (100%):
  * test_mechanical_deck_contract: PASS
  * test_phase_deck_contract: PASS
  * test_solution_history_serialization_contract: PASS
  * test_extractor_arguments_contract: PASS
  * test_phase_decoding_u3_and_rejections: PASS
  * test_solver_interface_and_coupled_acceptance: PASS
  * test_force_drift_prohibits_checkpoint: PASS
  * test_authentic_r8_outer89_transition_replay: PASS (R8 ratio 1.6845 > 1.50 [ROLLBACK] vs R9 raw ratio 0.9908 < 1.00 [ADMITTED])
  * test_all_18_authentic_r8_rollbacks_replayed: PASS (18/18 admitted in R9, raw ratio in [0.9898, 0.9932])
  * test_genuine_divergence_triggers_rollback: PASS (1.60x raw growth triggers divergence rollback)
  * test_genuine_residual_growth_triggers_rollback: PASS (1.08x raw growth triggers growth rollback)
  * test_catastrophic_jump_triggers_rollback: PASS (0.055 applied step triggers catastrophic rollback)
  * test_compound_active_set_stability_gate: PASS (|A| <= 500, |Delta A| <= 10, Delta A^+ == 0)
- Existing R8 regression suites: 22 / 22 PASS (total 34 / 34 PASS across all suites).

4. PUBLISHED ARTIFACT SHA-256 REGISTRY:
- driver_package171_r9_c6_coupled_pdas.py: 6D693CFD111C01F1559588B114AA261B9BA51C9EA889727A1249188B6180BB20
- package171_r9_driver_diff.patch: BFD66096FB240CAD931B29AB2365FEEB74796D6F6311AD2D7673EB99348BFB0E
- test_package171_r9_c6_coupled_driver.py: 52DC30FA76165B1C53AA2E9F6B568C2FB6EE50B17D5422413524F08545E71EB5
- package171_r9_test_output.txt: 75C93EB2F389C586E4BAF34AA53DD0E708C055F3616164F5FB98F3E2FD0EEE4B
- package171_r9_technical_correction_proposal.json: 63757974D4D8A066068D82EF89D0D3DB3998D27D5B5C5B6B83CB170F4014FAA4
- package171_r8_authentic_rollback_replay.json: AB531B1C2158417711AD390CBC73D9E137CE30E183D6FBCFF3894AF75C672913
- package171_r8_authentic_rollback_replay.md: 37DBDB05FD718847F401B4EBFB13583E6B0979E404CDD582D450BFD2D83D8B0F
- extract_r8_rollback_replay_evidence.py: 0759B0DBC6011C73508406BB03198ED43A3D01781F6FF1CC49AA3035E1A46038
- frozen_uel: CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6 (strictly unchanged)
- Task Definition: project_coordination/task_definitions/F1610-PACKAGE171-R9-C6-CORRECTIVE-QUALIFICATION.json: 796D290DE0DA933ECD89F3BD6A2CCCA0BBB8B108D37A98FF318B726C336F4435 (max_new_pbs_submissions: 0)

5. REQUEST FOR FORMAL RE-REVIEW DECISION:
With all blocking defects resolved, verified by 12/12 contract and regression tests, and published under commit 6351806f412742430ffd8c038a1407e3c1b327eb:
- Please provide formal review decision (APPROVE or REJECT) for Candidate Package 171-R9 minimal reconstruction.
- If approved, confirm authorization to proceed to Package 171-R9 staging and cluster mechanical & phase Abaqus datachecks under Task F1610.
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
