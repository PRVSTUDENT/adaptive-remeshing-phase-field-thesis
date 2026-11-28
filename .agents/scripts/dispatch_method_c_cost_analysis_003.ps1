# -*- coding: utf-8 -*-
# .agents/scripts/dispatch_method_c_cost_analysis_003.ps1
# Dispatches Goal METHOD_C_COST_ANALYSIS_V1 Final Cost Analysis Report Across OpenClaw PAD Bridge.

param(
    [switch]$CheckOnly
)

$ErrorActionPreference = 'Stop'

. "$PSScriptRoot\Invoke-ChatGPTBridge.ps1"

$taskId = "METHOD-C-COST-ANALYSIS"
$handoffId = "HND-METHOD-C-COST-ANALYSIS-003"
$predecessorHandoffId = "HND-METHOD-C-COST-ANALYSIS-002"
$goalId = "METHOD_C_COST_ANALYSIS_V1"

$reportPath = Join-Path $PSScriptRoot "..\..\docs\validation\METHOD_C_COMPUTATIONAL_COST_REPORT.md"
if (-not (Test-Path $reportPath)) {
    throw "Report file not found at: $reportPath"
}
$reportContent = Get-Content -Path $reportPath -Raw -Encoding UTF8
$reportSha = (Get-FileHash -Path $reportPath -Algorithm SHA256).Hash.ToUpper()

$rulesPath = Join-Path $PSScriptRoot "bridge_rules.txt"
$rulesSha = (Get-FileHash -Path $rulesPath -Algorithm SHA256).Hash.ToUpper()

$commitSha = (git rev-parse HEAD).Trim()
$githubBase = "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/$commitSha"

$prompt = @"
[BRIDGE_HANDOFF_ID=$handoffId]
INDEPENDENT_STRUCTURED_REVIEW_V1

{
  "protocol": "INDEPENDENT_STRUCTURED_REVIEW_V1",
  "correlation_id": "$handoffId",
  "predecessor_correlation_id": "$predecessorHandoffId",
  "task_id": "$taskId",
  "title": "Method C Computational Cost Analysis — Normal vs Adaptive (Cases 1, 2, 3, 5)",
  "goal_id": "$goalId",
  "canonical_rules_sha256": "$rulesSha",
  "artifact_commit": "$commitSha",
  "checkpoint_artifact": "docs/validation/METHOD_C_COMPUTATIONAL_COST_REPORT.md",
  "checkpoint_artifact_sha256": "$reportSha",
  "research_contract": {
    "goal_id": "$goalId",
    "method": "METHOD_C",
    "operation": "computational_cost_analysis",
    "numerical_uncertainty": "Can Method C incremental adaptive remeshing demonstrate quantitative wall-clock, CPU time, and degree-of-freedom advantages over conventional one-shot zone-refined discretizations across all four Mode-I benchmarks (Cases 1, 2, 3, 5) on the HPC cluster using 1 CPU per job under strict temporary scratch constraints without compromising physical fidelity or exceeding the 8-job submission budget?",
    "expected_numerical_result": "Method C demonstrates significant computational speedup across all four cases (Case 1: 1.31x wall speedup / 1.40x CPU speedup / 12.0% mesh reduction; Case 2: 2.61x wall speedup [61.65% reduction] / 2.82x CPU speedup [64.50% reduction] / 19.26% mesh reduction / 57.86% increment reduction; Case 3: normal baseline locks at u2=0.058 mm [2289s wall, 79184 DOFs] due to unadapted grid distortion while Method C achieves complete plate severance across 54 cycles with a 65.1% reduction in active DOFs; Case 5: 15.08x wall speedup [93.37% reduction, 959.5s vs 14467s]); all peak forces agree within <= 3.7% of reference benchmarks; all force continuity gates pass <= 5.0%; exactly 8 new PBS jobs consumed (Jobs 1425060-1425067, cumulative 73 to 81 ceiling strictly respected); frozen UEL CE8D5EDC bitwise identical; master goal status requests COMPLETE confirmation.",
    "indicator_type": "F1852_MEASURED_DRIVER",
    "indicator_role": "METHOD_C_DRIVER",
    "causal_evidence_status": "PLANNED"
  },
  "evidence_manifest": {
    "cost_analysis_report": {
      "path": "docs/validation/METHOD_C_COMPUTATIONAL_COST_REPORT.md",
      "sha256": "$reportSha",
      "github_url": "$githubBase/docs/validation/METHOD_C_COMPUTATIONAL_COST_REPORT.md"
    },
    "case1_cost_comparison_json": {
      "path": "models/computational_cost_analysis/case1/case1_cost_comparison.json",
      "sha256": "$((Get-FileHash (Join-Path $PSScriptRoot '..\..\models\computational_cost_analysis\case1\case1_cost_comparison.json') -Algorithm SHA256).Hash.ToUpper())",
      "github_url": "$githubBase/models/computational_cost_analysis/case1/case1_cost_comparison.json"
    },
    "case1_cost_comparison_csv": {
      "path": "models/computational_cost_analysis/case1/case1_cost_comparison.csv",
      "sha256": "$((Get-FileHash (Join-Path $PSScriptRoot '..\..\models\computational_cost_analysis\case1\case1_cost_comparison.csv') -Algorithm SHA256).Hash.ToUpper())",
      "github_url": "$githubBase/models/computational_cost_analysis/case1/case1_cost_comparison.csv"
    },
    "case2_cost_comparison_json": {
      "path": "models/computational_cost_analysis/case2/case2_cost_comparison.json",
      "sha256": "$((Get-FileHash (Join-Path $PSScriptRoot '..\..\models\computational_cost_analysis\case2\case2_cost_comparison.json') -Algorithm SHA256).Hash.ToUpper())",
      "github_url": "$githubBase/models/computational_cost_analysis/case2/case2_cost_comparison.json"
    },
    "case2_cost_comparison_csv": {
      "path": "models/computational_cost_analysis/case2/case2_cost_comparison.csv",
      "sha256": "$((Get-FileHash (Join-Path $PSScriptRoot '..\..\models\computational_cost_analysis\case2\case2_cost_comparison.csv') -Algorithm SHA256).Hash.ToUpper())",
      "github_url": "$githubBase/models/computational_cost_analysis/case2/case2_cost_comparison.csv"
    },
    "case3_cost_comparison_json": {
      "path": "models/computational_cost_analysis/case3/case3_cost_comparison.json",
      "sha256": "$((Get-FileHash (Join-Path $PSScriptRoot '..\..\models\computational_cost_analysis\case3\case3_cost_comparison.json') -Algorithm SHA256).Hash.ToUpper())",
      "github_url": "$githubBase/models/computational_cost_analysis/case3/case3_cost_comparison.json"
    },
    "case3_cost_comparison_csv": {
      "path": "models/computational_cost_analysis/case3/case3_cost_comparison.csv",
      "sha256": "$((Get-FileHash (Join-Path $PSScriptRoot '..\..\models\computational_cost_analysis\case3\case3_cost_comparison.csv') -Algorithm SHA256).Hash.ToUpper())",
      "github_url": "$githubBase/models/computational_cost_analysis/case3/case3_cost_comparison.csv"
    },
    "case5_cost_comparison_json": {
      "path": "models/computational_cost_analysis/case5/case5_cost_comparison.json",
      "sha256": "$((Get-FileHash (Join-Path $PSScriptRoot '..\..\models\computational_cost_analysis\case5\case5_cost_comparison.json') -Algorithm SHA256).Hash.ToUpper())",
      "github_url": "$githubBase/models/computational_cost_analysis/case5/case5_cost_comparison.json"
    },
    "case5_cost_comparison_csv": {
      "path": "models/computational_cost_analysis/case5/case5_cost_comparison.csv",
      "sha256": "$((Get-FileHash (Join-Path $PSScriptRoot '..\..\models\computational_cost_analysis\case5\case5_cost_comparison.csv') -Algorithm SHA256).Hash.ToUpper())",
      "github_url": "$githubBase/models/computational_cost_analysis/case5/case5_cost_comparison.csv"
    }
  },
  "governance_and_accounting": {
    "pbs_jobs_consumed_under_this_goal": 8,
    "cumulative_pbs_submissions": 81,
    "authorized_budget_ceiling": 81,
    "budget_status": "EXACT_CEILING_REACHED (Zero overage; no further jobs permitted under this goal)",
    "active_pbs_jobs": 0,
    "scratch_hygiene": "All intermediate .odb, .res, .sim, .pac, .stt, and .mdl files purged from /scratchtemp/pr21vyci immediately following metric extraction",
    "frozen_uel_sha256": "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6",
    "canonical_bridge_rules_sha256": "$rulesSha",
    "master_goal_status": "OPEN",
    "requested_decision": "APPROVE (Master Goal METHOD_C_COST_ANALYSIS_V1 COMPLETE)"
  }
}

---
### Full Computational Cost Analysis Report Content:
$reportContent
"@

if ($CheckOnly) {
    Write-Output "=== DRY RUN / CHECK ONLY: Assembled Bridge Prompt ==="
    Write-Output $prompt
    return
}

Write-Output "=== DISPATCHING FINAL COMPUTATIONAL COST ANALYSIS ($handoffId) ==="
Invoke-ChatGPTBridge -PromptText $prompt -HandoffId $handoffId -TimeoutMinutes 40
