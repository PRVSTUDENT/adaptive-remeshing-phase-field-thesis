# Test executing the exact stop evaluation block from Antigravity-Autonomous-Loop.ps1
$ErrorActionPreference = "Stop"

$WorkspaceDir = "D:\Master thesis\Adaptive remeshing"
$activeTaskFile = "$WorkspaceDir\project_coordination\ACTIVE_TASK.json"
$hpcLedgerPath = "$WorkspaceDir\project_coordination\HPC_JOB_LEDGER.csv"

# Mock variables as they exist in the controller loop during Turn 3 stop
$NextInstruction = "stop"
$agentResponse = "stop`n"
$qstatText = @"
Job id            Name             User              Time Use S Queue
----------------  ---------------- ----------------  -------- - -----
1404454.mmaster02 PK_M1_NOM1_FQ_S* pr21vyci          09:20:00 R normal_imfdfkmq 
"@

$isStop = (
    [string]::IsNullOrWhiteSpace($NextInstruction) -or
    $NextInstruction -match '^(?i:stop)\s*$'
)

if (-not $isStop) {
    throw "Expected isStop to be true"
}

# 1. Candidate IDs
$candidateJobIds = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::OrdinalIgnoreCase)
$liveRunningJobIds = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::OrdinalIgnoreCase)

# 2. Extract from response
if (-not [string]::IsNullOrWhiteSpace($agentResponse)) {
    $termMatches = [regex]::Matches($agentResponse, '1[3-9]\d{5,6}\.mmaster02')
    foreach ($m in $termMatches) {
        [void]$candidateJobIds.Add($m.Value)
    }
}

# 3. Extract from ACTIVE_TASK.json
if (Test-Path -LiteralPath $activeTaskFile) {
    $taskData = Get-Content -LiteralPath $activeTaskFile -Raw | ConvertFrom-Json
    if ($taskData.active_job_id -and [string]$taskData.active_job_id -match '^1[3-9]\d{5,6}\.mmaster02$') {
        [void]$candidateJobIds.Add([string]$taskData.active_job_id)
    }
    if ($taskData.active_task.governing_rules.active_job_ids) {
        foreach ($j in @($taskData.active_task.governing_rules.active_job_ids)) {
            if ([string]$j -match '^1[3-9]\d{5,6}\.mmaster02$') {
                [void]$candidateJobIds.Add([string]$j)
            }
        }
    }
}

# 4. Parse live Q/R jobs
$hasLiveRunningOrQueued = $false
$liveLines = $qstatText -split "`r?`n"
foreach ($lLine in $liveLines) {
    $lTrim = $lLine.Trim()
    if (-not $lTrim -or $lTrim.StartsWith("Job id") -or $lTrim.StartsWith("Job ID") -or $lTrim.StartsWith("---") -or $lTrim.StartsWith("mmaster02:")) {
        continue
    }
    $lParts = ($lTrim -split '\s+') | Where-Object { $_ -ne '' }
    if ($lParts.Count -ge 5) {
        $lState = if ($lParts.Count -ge 10 -and $lParts[9] -match '^[RQHWFCEBT]$') { $lParts[9].ToUpper() } elseif ($lParts[4] -match '^[RQHWFCEBT]$') { $lParts[4].ToUpper() } else { $null }
        if ($lState -in @('R', 'Q', 'H', 'W')) {
            $hasLiveRunningOrQueued = $true
            $rawId = ($lParts[0] -replace '\*$', '') -replace '\.mmaster02$', '' -replace '\.mmaste$', ''
            if ($rawId -match '^1[3-9]\d{5,6}$') {
                $fullSchedId = "$rawId.mmaster02"
                [void]$candidateJobIds.Add($fullSchedId)
                [void]$liveRunningJobIds.Add($fullSchedId)
            }
        }
    }
}

# 5. Verified terminal jobs
$script:VerifiedTerminalJobs = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::OrdinalIgnoreCase)
if (Test-Path -LiteralPath $hpcLedgerPath) {
    $ledgerLines = Get-Content -LiteralPath $hpcLedgerPath -ErrorAction SilentlyContinue
    foreach ($lLine in $ledgerLines) {
        if ($lLine -match '^(1[3-9]\d{5,6}\.mmaster02),[^,]+,[^,]+,[^,]+,[^,]+,[^,]+,(F|C|E),') {
            [void]$script:VerifiedTerminalJobs.Add($Matches[1])
        }
    }
}

if ($taskData.completed_requalification_job) {
    [void]$script:VerifiedTerminalJobs.Add([string]$taskData.completed_requalification_job)
}

# 6. Separate candidate jobs
$pendingUnverifiedJobIds = [System.Collections.Generic.List[string]]::new()
$activeTrackedForPrompt = [System.Collections.Generic.List[string]]::new()

foreach ($cId in $candidateJobIds) {
    if ($liveRunningJobIds.Contains($cId)) {
        $activeTrackedForPrompt.Add("$cId (Running)")
    }
    elseif ($script:VerifiedTerminalJobs.Contains($cId)) {
        Write-Host "[SCHEDULER] Job $cId is ALREADY verified terminal. Filtering out from active polling." -ForegroundColor DarkGray
    }
    else {
        $pendingUnverifiedJobIds.Add($cId)
        $activeTrackedForPrompt.Add("$cId (Unverified Absent)")
    }
}

$activeJobParam = if ($activeTrackedForPrompt.Count -gt 0) {
    $activeTrackedForPrompt -join '; '
} elseif ($liveRunningJobIds.Count -gt 0) {
    ($liveRunningJobIds | ForEach-Object { "$_ (Running)" }) -join '; '
} else {
    "<none tracked>"
}

# 7. Mock wait cycle logic (without actual 900s sleep)
$schedulerInstruction = "stop"
if ($hasLiveRunningOrQueued) {
    if ($schedulerInstruction -match '^(?i:stop)\s*$') {
        $liveJobSummary = if ($liveRunningJobIds.Count -gt 0) { ($liveRunningJobIds -join ', ') } else { "active jobs" }
        $termJobSummary = if ($script:VerifiedTerminalJobs.Count -gt 0) { ($script:VerifiedTerminalJobs -join ', ') } else { "verified terminal jobs" }
        $NextInstruction = "Run a single fresh scheduler check now: qstat -u pr21vyci. Evaluate active running job(s) ($liveJobSummary). Do not query verified terminal jobs ($termJobSummary). If active job(s) remain R, report current elapsed walltime and confirm solver output remains untouched. If terminal, retrieve terminal logs/accounting and proceed with terminal extraction. Write Finished when done."
    }
}

Write-Host "activeJobParam: $activeJobParam"
Write-Host "NextInstruction for post-sleep turn:"
Write-Host $NextInstruction

if (-not $liveRunningJobIds.Contains("1404454.mmaster02")) {
    throw "liveRunningJobIds should contain 1404454.mmaster02"
}

if ($pendingUnverifiedJobIds.Count -ne 0) {
    throw "pendingUnverifiedJobIds should be empty"
}

if ($NextInstruction -notmatch '1404454\.mmaster02') {
    throw "NextInstruction should reference 1404454.mmaster02"
}

Write-Host "STOP EVALUATION BLOCK TEST PASSED CLEANLY (100%)." -ForegroundColor Green
