# Session Report: Controller Tightened Candidate PBS Job Selection

- **Task ID**: `F390-CONTROLLER-TIGHTEN-CANDIDATE-JOB-SELECTION`
- **Agent**: `gemini-antigravity`
- **Timestamp**: `2026-08-25T08:15:00+02:00`
- **Protocol Version**: `2`

## Summary of Changes

### 1. `Get-LivePbsJobs` (`C:\Users\pruth\OpenClawPAD\Antigravity-Autonomous-Loop.ps1`)
- Restored `qstat -u $User` for live scheduler queries so it only queries and returns currently active queued/running jobs without pulling the 350+ historical finished jobs from `qstat -x -u`.

### 2. Tightened Candidate Job Selection in STOP Handler (Section 5)
- Replaced broad historical scheduler job inclusion with strict, validated selection:
  ```powershell
  $candidateJobIds = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::OrdinalIgnoreCase)

  $AddValidJobId = {
      param([string]$rawId)
      if ([string]::IsNullOrWhiteSpace($rawId)) { return }
      $cleaned = $rawId.Trim()
      if ($cleaned -match '^\d{6,8}(\.mmaster02)?$') {
          $fullId = if ($cleaned -notmatch '\.mmaster02$') { "$cleaned.mmaster02" } else { $cleaned }
          [void]$candidateJobIds.Add($fullId)
      }
  }

  # 1. From latest agent response
  if (-not [string]::IsNullOrWhiteSpace($agentResponse)) {
      $mMatches = [regex]::Matches($agentResponse, '\b(\d{6,8}(\.mmaster02)?)\b')
      foreach ($m in $mMatches) { & $AddValidJobId $m.Value }
  }

  # 2. From ACTIVE_TASK.json (active_job_id)
  $activeTaskFile = Join-Path $WorkspaceDir "project_coordination\ACTIVE_TASK.json"
  if (Test-Path -LiteralPath $activeTaskFile) {
      try {
          $taskData = Get-Content -LiteralPath $activeTaskFile -Raw | ConvertFrom-Json
          if ($taskData.active_job_id) { & $AddValidJobId ([string]$taskData.active_job_id) }
      } catch {}
  }

  # 3. From HPC_JOB_LEDGER.csv (active/running/queued jobs or latest entry)
  $hpcLedgerFile = Join-Path $WorkspaceDir "project_coordination\HPC_JOB_LEDGER.csv"
  if (Test-Path -LiteralPath $hpcLedgerFile) {
      try {
          $ledgerEntries = Import-Csv -LiteralPath $hpcLedgerFile -ErrorAction SilentlyContinue
          if ($ledgerEntries) {
              $activeRows = $ledgerEntries | Where-Object { $_.status -in @('SUBMITTED', 'RUNNING', 'QUEUED', 'ACTIVE') }
              foreach ($row in $activeRows) { if ($row.job_id) { & $AddValidJobId $row.job_id } }
              if ($activeRows.Count -eq 0 -and $ledgerEntries.Count -gt 0) {
                  $lastRow = $ledgerEntries[-1]
                  if ($lastRow.job_id) { & $AddValidJobId $lastRow.job_id }
              }
          }
      } catch {}
  }

  # 4. From controller-state.json
  try {
      $tracked = @(Get-ActivePbsJobIds)
      foreach ($j in $tracked) { & $AddValidJobId $j }
  } catch {}

  # 5. From live scheduler (running/queued jobs only)
  try {
      $liveScheduler = Get-LivePbsJobs
      foreach ($j in @($liveScheduler.WaitableJobs)) { & $AddValidJobId $j }
  } catch {}
  ```
- Every candidate ID is strictly format-validated against `^\d{6,8}(\.mmaster02)?$`.
- Prevents passing hundreds of historical or truncated IDs to `qstat -x`.

## Verification
- Executed direct test query `qstat -x 1397397.mmaster02` $\to$ **`ExitCode: 0`**.
- `scripts/validation/validate_controller_syntax.ps1`: AST parsing and pattern verification **PASS (100%)**.
- `tests/unit/test_controller_stop_patch.ps1`: Full unit test suite **PASS (100%)**.
