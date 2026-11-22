param(
    [switch]$Publish = $false
)

. 'C:\Users\pruth\OpenClawPAD\ChatGPTBridge\Bridge-ResearchContract.ps1'
. 'C:\Users\pruth\OpenClawPAD\ChatGPTBridge\Invoke-ChatGPTBridge.ps1'

$commitSha = "0c0f7682e4b755e80a73c9db80e1c52067576b23"

$prompt = @"
[BRIDGE_HANDOFF_ID=HND-METHOD-C-CASE3-FRAMEWORK-KILL-AND-FIX-003]
INDEPENDENT_STRUCTURED_REVIEW_V1

{
  "protocol": "INDEPENDENT_STRUCTURED_REVIEW_V1",
  "correlation_id": "HND-METHOD-C-CASE3-FRAMEWORK-KILL-AND-FIX-003",
  "predecessor_correlation_id": "HND-METHOD-C-CASE3-FRAMEWORK-KILL-AND-FIX-002",
  "task_id": "METHOD-C-CASE3-FRAMEWORK-KILL-1424881-AND-FIX-TRANSFER",
  "title": "Method C Case 3: Kill Run 1424881, Measure Phase Timings, Fix Transfer Bottleneck, Stalled Resume Load, and Robust Crack Tip Extraction (Re-Issue 3)",
  "goal_id": "METHOD_C_INCREMENTAL_ADAPTIVE_REMESHING_V1",
  "canonical_rules_sha256": "A53F752BD3356D39BDBDC41A1E88A71A147E1E3204FC85971B82C632014A0EB4",
  "artifact_commit": "$commitSha",
  "checkpoint_artifact": "docs/validation/METHOD_C_CASE3_FRAMEWORK_TRANSFER_SPEEDUP_REPORT.md",
  "checkpoint_artifact_sha256": "70265E41D9F8EBBB97F98B7F2FDF535269B52C25063459D11409002037ED1F91",
  "research_contract": {
    "goal_id": "METHOD_C_INCREMENTAL_ADAPTIVE_REMESHING_V1",
    "method": "METHOD_C",
    "operation": "method_c_case3_framework_kill_and_fix_transfer",
    "numerical_uncertainty": "Can the framework reliably resume from Cycle-6 checkpoint at u2 = 0.1000 mm with an authentic crack tip in both x and y so that the narrow band covers the crack front without spurious far-field node corruption?",
    "expected_numerical_result": "Re-issued transfer speedup and resume report HND-METHOD-C-CASE3-FRAMEWORK-KILL-AND-FIX-003 resolving GAP-MC-C3KFX-07: robust crack tip extraction ignores isolated spurious node 1029 and selects leading front node 8260 at (30.5113, 66.7437) mm; verified on cluster scratch test_cluster_c6_extraction.py with 0.0000 mm distance from crack front to narrow band centreline, local range [65.74, 67.74] mm, crack front 100% enclosed in fine h=0.140 mm mesh; 28/28 unit tests PASS; 0 new PBS jobs consumed (cumulative 71 strictly preserved); MASTER_GOAL_STATUS = OPEN.",
    "indicator_type": "F1852_MEASURED_DRIVER",
    "indicator_role": "METHOD_C_DRIVER",
    "causal_evidence_status": "PLANNED"
  },
  "evidence_manifest": {
    "transfer_report": {
      "path": "docs/validation/METHOD_C_CASE3_FRAMEWORK_TRANSFER_SPEEDUP_REPORT.md",
      "sha256": "70265E41D9F8EBBB97F98B7F2FDF535269B52C25063459D11409002037ED1F91",
      "size_bytes": 17121,
      "github_url": "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/$commitSha/docs/validation/METHOD_C_CASE3_FRAMEWORK_TRANSFER_SPEEDUP_REPORT.md"
    },
    "orchestrator": {
      "path": "models/pandey_kumar_mode1/290_method_c_case3/case3_single_job_orchestrator.py",
      "sha256": "3CCEB29405F7ACDEE21F859944BD2A730E30FB67656D8CE04DBE02EE2971A00F",
      "size_bytes": 86325,
      "github_url": "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/$commitSha/models/pandey_kumar_mode1/290_method_c_case3/case3_single_job_orchestrator.py"
    },
    "test_suite": {
      "path": "tests/unit/test_method_c_case3_framework_package.py",
      "sha256": "25B73115112E98F305A32CB00D8DF5A3CD4624D5093EAF78F24C275B91D48878",
      "size_bytes": 41079,
      "github_url": "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/$commitSha/tests/unit/test_method_c_case3_framework_package.py"
    },
    "cluster_extraction_test": {
      "path": "scripts/hpc/test_cluster_c6_extraction.py",
      "sha256": "547A72E866701587A6B2BBC843B3F1ACACCF8749EBB2755D883491B3670ED86E",
      "size_bytes": 2287,
      "github_url": "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/$commitSha/scripts/hpc/test_cluster_c6_extraction.py"
    },
    "frozen_uel": {
      "path": "models/pandey_kumar_mode1/f42_mixed_uel.for",
      "sha256": "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6",
      "size_bytes": 29722,
      "github_url": "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/$commitSha/models/pandey_kumar_mode1/f42_mixed_uel.for"
    }
  }
}
"@

if ($Publish) {
    Write-Host "Publishing bridge request to C:\Users\pruth\OpenClawPAD\ChatGPTBridge\bridge_request.ready..."
    $handoffId = "HND-METHOD-C-CASE3-FRAMEWORK-KILL-AND-FIX-003"
    $bridgeDir = "C:\Users\pruth\OpenClawPAD\ChatGPTBridge"
    $requestTmp = Join-Path $bridgeDir "bridge_request.tmp"
    $requestReady = Join-Path $bridgeDir "bridge_request.ready"
    
    [System.IO.File]::WriteAllText($requestTmp, $prompt, [System.Text.Encoding]::UTF8)
    if (Test-Path $requestReady) {
        Remove-Item $requestReady -Force
    }
    Move-Item -Path $requestTmp -Destination $requestReady -Force
    Write-Host "Bridge request published successfully."
} else {
    Write-Host "Dry run. To publish, pass -Publish."
    Write-Host $prompt
}
