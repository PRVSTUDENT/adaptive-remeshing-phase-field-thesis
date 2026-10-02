$WorkspaceDir = "D:\Master thesis\Adaptive remeshing"
$agentResponse = "Restart job submitted successfully. PBS Job ID: 1397397.mmaster02."

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
    foreach ($m in $mMatches) {
        & $AddValidJobId $m.Value
    }
}

# 2. From ACTIVE_TASK.json
$activeTaskFile = Join-Path $WorkspaceDir "project_coordination\ACTIVE_TASK.json"
if (Test-Path -LiteralPath $activeTaskFile) {
    try {
        $taskData = Get-Content -LiteralPath $activeTaskFile -Raw | ConvertFrom-Json
        if ($taskData.active_job_id) {
            & $AddValidJobId ([string]$taskData.active_job_id)
        }
    } catch {}
}

# 3. From HPC_JOB_LEDGER.csv
$hpcLedgerFile = Join-Path $WorkspaceDir "project_coordination\HPC_JOB_LEDGER.csv"
if (Test-Path -LiteralPath $hpcLedgerFile) {
    try {
        $ledgerEntries = Import-Csv -LiteralPath $hpcLedgerFile -ErrorAction SilentlyContinue
        if ($ledgerEntries) {
            $activeRows = $ledgerEntries | Where-Object { $_.status -in @('SUBMITTED', 'RUNNING', 'QUEUED', 'ACTIVE') }
            foreach ($row in $activeRows) {
                if ($row.job_id) { & $AddValidJobId $row.job_id }
            }
            if ($activeRows.Count -eq 0 -and $ledgerEntries.Count -gt 0) {
                $lastRow = $ledgerEntries[-1]
                if ($lastRow.job_id) { & $AddValidJobId $lastRow.job_id }
            }
        }
    } catch {}
}

$activeJobsToQuery = @($candidateJobIds)
Write-Host "Selected Candidate Job IDs: $($activeJobsToQuery -join ', ')"

# Test qstat -x query with exact candidate IDs
$sshConfig = Join-Path $env:USERPROFILE ".ssh\codex_config"
$jobArg = $activeJobsToQuery -join ' '
$cmd = "qstat -x $jobArg"
Write-Host "Running command: $cmd"
$out = & ssh -F $sshConfig tu_freiberg $cmd 2>&1
Write-Host "ExitCode: $LASTEXITCODE"
$out | ForEach-Object { Write-Host "  [$_]" }
