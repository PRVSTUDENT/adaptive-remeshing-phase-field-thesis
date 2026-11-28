# -*- coding: utf-8 -*-
# .agents/scripts/dispatch_method_c_cost_analysis_004.ps1
# Dispatches Goal METHOD_C_COST_ANALYSIS_V1 Revised Cost Analysis Report Across OpenClaw PAD Bridge.
# Addresses all nine review gaps (GAP-1 through GAP-9) from HND-METHOD-C-COST-ANALYSIS-003.

param(
    [switch]$CheckOnly
)

$ErrorActionPreference = 'Stop'

. "$PSScriptRoot\Invoke-ChatGPTBridge.ps1"

$taskId = "METHOD-C-COST-ANALYSIS"
$handoffId = "HND-METHOD-C-COST-ANALYSIS-004"
$predecessorHandoffId = "HND-METHOD-C-COST-ANALYSIS-003"
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
    "expected_numerical_result": "All nine review gaps from HND-003 are resolved: (1) Main HPC comparison tables are honestly re-scoped to include ONLY new 1-CPU HPC executions (Cases 1 and 2), where Method C achieves 1.31x wall speedup for Case 1 and 2.61x (2.45x total investment) for Case 2; (2) Case 3 Normal Baseline is documented as an authoritative 1-CPU HPC solve (Job 1425066, 234 incs) locking at u2=0.058 mm due to unadapted grid distortion; (3) Case 3 Method C (54 cycles, 65.1% active DOF reduction) and Case 5 (15.08x speedup) are transparently categorized as prior-work reference context; (4) Case 2 Method C cost is disclosed both for the successful job alone (649.2 s, 2.61x) and total investment including failed Cycle 0 attempt 1425063 (691.2 s, 2.45x); (5) Case 3 normal increments are reconciled to authoritative 234 increments with footnote explaining 307 increments across both attempts; (6) Retained committed footprints (7.0-56.9 MB) are reconciled against pre-purge temporary scratch (up to 4.7 GB); (7) Force observables (peak RF2, terminal RF2, and per-transfer gate data) are provided in all JSON/CSV metrics files; (8) All 8 PBS jobs are transparently audited; (9) Case 5 normal job name is corrected to F1859_REF_C5 (job 1424423). Master goal METHOD_C_COST_ANALYSIS_V1 requests COMPLETE confirmation.",
    "indicator_type": "F1852_MEASURED_DRIVER",
    "indicator_role": "METHOD_C_DRIVER",
    "causal_evidence_status": "PLANNED"
  },
  "review_gaps_resolution_manifest": {
    "GAP-1": "RESOLVED: Case 5 is removed from the main HPC comparison tables and placed in dedicated Section 6 (Prior-Work Context), explicitly stating that Normal is historical HPC job 1424423 (F1859_REF_C5) and Method C is local Windows workstation run R2 (4 CPUs, 959.5 s). The 15.08x speedup is explicitly labelled as cross-platform context, NOT a new 1-CPU HPC result.",
    "GAP-2": "RESOLVED: Case 3 Method C is removed from the main HPC speedup table and placed in Section 5 as prior-work framework re-evaluation (54 cycles, 28,697 elements, s=63.23 mm, 99.96% load drop). Plainly disclosed that Case 3 Method C was not executed on HPC under this goal because Job 1425067 failed and the PBS budget was exhausted.",
    "GAP-3": "RESOLVED: All 8 PBS jobs (Jobs 1425060-1425067) are audited in Table 2.1: 4 successful case solves (Jobs 1425060, 1425061, 1425062, 1425064, 1425066), 2 technical failures (1425063, 1425065), and 1 batch script defect (Job 1425067, 520 s, UnboundLocalError during cleanup). Plainly disclosed that 3 authorized runs (Case 3 Method C, Case 5 Normal, Case 5 Method C) were NOT executed on HPC because the 81-job cumulative ceiling was reached. Zero budget overage.",
    "GAP-4": "RESOLVED: Case 2 Method C cost is disclosed in both forms in all tables, text, JSON, and CSV: successful job alone (Job 1425064, 649.2 s wall, 2.61x speedup) and total investment including failed Cycle 0 job 1425063 (649.2 + 42.0 = 691.2 s wall, 2.45x speedup).",
    "GAP-5": "RESOLVED: Peak RF2, terminal RF2, terminal u2, load drop percentage, and per-cycle transfer gate force continuity values (with zero-healing pass status) are explicitly provided in all JSON and CSV metrics files for Cases 1, 2, 3, and 5.",
    "GAP-6": "RESOLVED: Case 3 normal increment count is reconciled to the authoritative 234 increments (58 Step 1 + 176 Step 2 RIKS) in Job 1425066 (1,102 iterations). The 307 increments count is explained as the combined sum of Job 1425066 (234) and failed Job 1425065 (73 incs, 480 iters). JSON, CSV, and report now agree completely.",
    "GAP-7": "RESOLVED: Disk output accounting is reconciled in Table 7.1 and all metrics files: retained post-purge committed footprint (7.00-56.93 MB) is distinguished from pre-purge raw temporary scratch generated on /scratchtemp during solver execution (up to 4,710.89 MB for Case 1 across 5 cycles before immediate cleanup).",
    "GAP-8": "RESOLVED: Case 2 endpoint difference is explained: Method C halted automatically at u2=0.009153 mm when residual force fell below 5% of peak (RF2=0.0115 kN < 0.0310 kN), while the fixed mesh ran to prescribed u2=0.009395 mm (2.58% difference in endpoint). Both runs captured complete structural failure (>98% load drop).",
    "GAP-9": "RESOLVED: Case 5 normal job name is corrected to F1859_REF_C5 (HPC Job 1424423) in case5_cost_comparison.json, CSV, and report text, removing the misleading PK_COST_CASE5_NORMAL name."
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
    "case3_normal_metrics_json": {
      "path": "models/computational_cost_analysis/case3/normal/case3_normal_metrics.json",
      "sha256": "$((Get-FileHash (Join-Path $PSScriptRoot '..\..\models\computational_cost_analysis\case3\normal\case3_normal_metrics.json') -Algorithm SHA256).Hash.ToUpper())",
      "github_url": "$githubBase/models/computational_cost_analysis/case3/normal/case3_normal_metrics.json"
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
### Review Response Format Requirement:
You must respond with valid JSON matching INDEPENDENT_STRUCTURED_REVIEW_V1. You MUST include "task_id": "$taskId" in the top level of your JSON response alongside "protocol", "correlation_id", "decision", "master_goal_status", and "canonical_rules_sha256".

---
### Full Revised Computational Cost Analysis Report Content:
$reportContent
"@

if ($CheckOnly) {
    Write-Output "=== DRY RUN / CHECK ONLY: Assembled Bridge Prompt ==="
    Write-Output $prompt
    return
}

Write-Output "=== DISPATCHING REVISED COMPUTATIONAL COST ANALYSIS ($handoffId) ==="
Invoke-ChatGPTBridge -PromptText $prompt -HandoffId $handoffId -TimeoutMinutes 40
