param(
    [switch]$Publish = $false
)

. 'C:\Users\pruth\OpenClawPAD\ChatGPTBridge\Bridge-ResearchContract.ps1'
. 'C:\Users\pruth\OpenClawPAD\ChatGPTBridge\Invoke-ChatGPTBridge.ps1'

$prompt = @'
[BRIDGE_HANDOFF_ID=HND-METHOD-C-CASE3-JOB1-DIAG-002]
INDEPENDENT_STRUCTURED_REVIEW_V1

{
  "protocol": "INDEPENDENT_STRUCTURED_REVIEW_V1",
  "correlation_id": "HND-METHOD-C-CASE3-JOB1-DIAG-002",
  "predecessor_correlation_id": "HND-METHOD-C-CASE3-JOB1-DIAG-001",
  "task_id": "METHOD-C-CASE3-JOB1-FAILURE-DIAGNOSIS",
  "title": "Method C Case 3: Job-1 Coarse Baseline Solve Failure Diagnosis Re-Issue",
  "goal_id": "METHOD_C_INCREMENTAL_ADAPTIVE_REMESHING_V1",
  "canonical_rules_sha256": "A53F752BD3356D39BDBDC41A1E88A71A147E1E3204FC85971B82C632014A0EB4",
  "artifact_commit": "ee467cec5222ef2bc5fb1df4b5e82b7937402ee3",
  "checkpoint_artifact": "docs/validation/METHOD_C_CASE3_JOB1_FAILURE_DIAGNOSIS_REPORT.md",
  "checkpoint_artifact_sha256": "154540458FD63618ECBE793C5E7C21B471D59D834C5F3691E033EE71103AE180",
  "research_contract": {
    "goal_id": "METHOD_C_INCREMENTAL_ADAPTIVE_REMESHING_V1",
    "method": "METHOD_C",
    "operation": "method_c_case3_job1_failure_diagnosis",
    "numerical_uncertainty": "Can the Job 1424711 failure (Step-2 Inc 13 at u2 = 0.05611 mm) be diagnosed from committed solver outputs (.sta, .msg, .dat, pbs_execution.log, uel_energy_balance.csv), verifying from the .sta/.msg/.dat that Step 1 converged 50/50 (RF2 = 3.9288 kN), peak load F_max = 4.3318 kN was captured, and the termination was the deck dt_min = 1.0e-8 cutback floor, so that Fix Option A (refine from Step-1 donor) versus Fix Option B (dt_min = 1e-14 with line search) can be decided?",
    "expected_numerical_result": "Re-issued diagnosis HND-METHOD-C-CASE3-JOB1-DIAG-002 with five solver-output files committed and SHA-verified, confirming Step-1 50/50 convergence and the Inc-13 dt_min mechanism from repo evidence, and a review decision on Fix Option A vs Fix Option B; 0 new PBS jobs consumed (cumulative 63 preserved); MASTER_GOAL_STATUS = OPEN.",
    "indicator_type": "F1852_MEASURED_DRIVER",
    "indicator_role": "METHOD_C_DRIVER",
    "causal_evidence_status": "PLANNED"
  },
  "evidence_manifest": {
    "diagnosis_report": {
      "path": "docs/validation/METHOD_C_CASE3_JOB1_FAILURE_DIAGNOSIS_REPORT.md",
      "sha256": "154540458FD63618ECBE793C5E7C21B471D59D834C5F3691E033EE71103AE180",
      "github_url": "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/ee467cec5222ef2bc5fb1df4b5e82b7937402ee3/docs/validation/METHOD_C_CASE3_JOB1_FAILURE_DIAGNOSIS_REPORT.md"
    },
    "committed_solver_evidence": {
      "status_file": {
        "path": "models/pandey_kumar_mode1/290_method_c_case3/PK_METHOD_C_CASE3_COARSE_JOB1.sta",
        "sha256": "C2FC8AD21A6258D36ACAE1530C69796BC0DC5EDAC2A210C64693E24AF11C3A5E",
        "github_url": "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/ee467cec5222ef2bc5fb1df4b5e82b7937402ee3/models/pandey_kumar_mode1/290_method_c_case3/PK_METHOD_C_CASE3_COARSE_JOB1.sta"
      },
      "message_file": {
        "path": "models/pandey_kumar_mode1/290_method_c_case3/PK_METHOD_C_CASE3_COARSE_JOB1.msg",
        "sha256": "A8C95DDD4861E2342F51F399553324D6F95FC7072BE2CA78EDCA4C71321BC00B",
        "github_url": "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/ee467cec5222ef2bc5fb1df4b5e82b7937402ee3/models/pandey_kumar_mode1/290_method_c_case3/PK_METHOD_C_CASE3_COARSE_JOB1.msg"
      },
      "data_file": {
        "path": "models/pandey_kumar_mode1/290_method_c_case3/PK_METHOD_C_CASE3_COARSE_JOB1.dat",
        "sha256": "C4C2D56BAA63AB84C19D1DACF779E21494D66A156CED7BC4D7E23719EC6E93C0",
        "github_url": "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/ee467cec5222ef2bc5fb1df4b5e82b7937402ee3/models/pandey_kumar_mode1/290_method_c_case3/PK_METHOD_C_CASE3_COARSE_JOB1.dat"
      },
      "execution_log": {
        "path": "models/pandey_kumar_mode1/290_method_c_case3/pbs_execution.log",
        "sha256": "27FC07A82C36237AA2CBA16C3F84B1129C7C1DC0968271453007B9F0E8A99D60",
        "github_url": "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/ee467cec5222ef2bc5fb1df4b5e82b7937402ee3/models/pandey_kumar_mode1/290_method_c_case3/pbs_execution.log"
      },
      "energy_csv": {
        "path": "models/pandey_kumar_mode1/290_method_c_case3/uel_energy_balance.csv",
        "sha256": "8DA7DDFA4713D55C16FDD0DA5EE715895ABBCEB18D699DEF7B5AA8435F49609B",
        "github_url": "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/ee467cec5222ef2bc5fb1df4b5e82b7937402ee3/models/pandey_kumar_mode1/290_method_c_case3/uel_energy_balance.csv"
      }
    },
    "canonical_frozen_uel": {
      "path": "models/pandey_kumar_mode1/f42_mixed_uel.for",
      "sha256": "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6",
      "github_url": "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/ee467cec5222ef2bc5fb1df4b5e82b7937402ee3/models/pandey_kumar_mode1/f42_mixed_uel.for"
    },
    "executed_deck": {
      "path": "models/pandey_kumar_mode1/290_method_c_case3/PK_METHOD_C_CASE3_COARSE_JOB1.inp",
      "sha256": "1B3C9A62A9644E1E9FD6E8F4AD4B2DC734D69688D80E2655B0A11F8A7A7BDDC2"
    }
  },
  "gap_resolutions": [
    {
      "gap_id": "GAP-MC-C3J1D-01",
      "status": "RESOLVED",
      "description": "Committed all five text solver output files directly to models/pandey_kumar_mode1/290_method_c_case3/ with verified SHA-256 hashes."
    },
    {
      "gap_id": "GAP-MC-C3J1D-02",
      "status": "RESOLVED",
      "description": "Corrected evidence manifest path for frozen UEL to canonical path models/pandey_kumar_mode1/f42_mixed_uel.for (verified SHA CE8D5EDC...)."
    },
    {
      "gap_id": "GAP-MC-C3J1D-03",
      "status": "RESOLVED",
      "description": "Updated research_contract.operation to method_c_case3_job1_failure_diagnosis."
    }
  ]
}
'@

if ($Publish) {
    # Publish to bridge_request.ready via the guarded prompt builder
    $packet = New-BridgeCanonicalPrompt -PromptText $prompt -HandoffId 'HND-METHOD-C-CASE3-JOB1-DIAG-002' -TaskId 'METHOD-C-CASE3-JOB1-FAILURE-DIAGNOSIS'
    $bridgeDir = "C:\Users\pruth\OpenClawPAD\ChatGPTBridge"
    $archiveDir = Join-Path $bridgeDir "archive"
    $timestamp = (Get-Date).ToString("yyyyMMdd_HHmmss")
    $archRequest = Join-Path $archiveDir ("request_{0}_{1}.txt" -f $timestamp, $packet.handoff_id)
    $requestTmp = Join-Path $bridgeDir "bridge_request.tmp"
    $requestReady = Join-Path $bridgeDir "bridge_request.ready"

    [System.IO.File]::WriteAllText($archRequest, $packet.text, [System.Text.UTF8Encoding]::new($false))
    [System.IO.File]::WriteAllText($requestTmp, $packet.text, [System.Text.UTF8Encoding]::new($false))
    Move-Item -LiteralPath $requestTmp -Destination $requestReady -Force
    Write-Host "[Bridge] Published bridge_request.ready with $($packet.text.Length) chars, archived to $archRequest"
} else {
    $res = Invoke-ChatGPTBridge -DryRun -PromptText $prompt -HandoffId 'HND-METHOD-C-CASE3-JOB1-DIAG-002' -TaskId 'METHOD-C-CASE3-JOB1-FAILURE-DIAGNOSIS'
    Write-Host "Dry run passed. Prompt length: $($res.Length)"
}
