# Dry-run test for scheduler evaluation logic in Antigravity-Autonomous-Loop.ps1
$ErrorActionPreference = "Stop"

$WorkspaceDir = "D:\Master thesis\Adaptive remeshing"
$activeTaskFile = "$WorkspaceDir\project_coordination\ACTIVE_TASK.json"
$hpcLedgerPath = "$WorkspaceDir\project_coordination\HPC_JOB_LEDGER.csv"

# Mock qstat output matching current cluster state: 1404454 running, 1404306 absent
$qstatText = @"
mmaster02: 
                                                            Req'd  Req'd   Elap
Job ID          Username Queue    Jobname    SessID NDS TSK Memory Time  S Time
--------------- -------- -------- ---------- ------ --- --- ------ ----- - -----
1404454.mmaste* pr21vyci normal_* PK_M1_NOM* 19187*   1   1   32gb 336:0 R 09:20
"@

$candidateJobIds = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::OrdinalIgnoreCase)
$agentResponse = "Previous response mentioning 1404306.mmaster02 and 1404454.mmaster02"

# Extract job IDs from response
$termMatches = [regex]::Matches($agentResponse, '1[3-9]\d{5,6}\.mmaster02')
foreach ($m in $termMatches) {
    [void]$candidateJobIds.Add($m.Value)
}

# Extract job IDs from ACTIVE_TASK.json
$taskData = Get-Content -LiteralPath $activeTaskFile -Raw | ConvertFrom-Json
if ($taskData.active_task.governing_rules.active_job_ids) {
    foreach ($j in @($taskData.active_task.governing_rules.active_job_ids)) {
        if ([string]$j -match '^1[3-9]\d{5,6}\.mmaster02$') {
            [void]$candidateJobIds.Add([string]$j)
        }
    }
}

# Parse live Q/R jobs from qstatText
$liveRunningJobIds = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::OrdinalIgnoreCase)
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

# Terminal jobs detection
$script:VerifiedTerminalJobs = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::OrdinalIgnoreCase)
if (Test-Path -LiteralPath $hpcLedgerPath) {
    $ledgerLines = Get-Content -LiteralPath $hpcLedgerPath -ErrorAction SilentlyContinue
    foreach ($lLine in $ledgerLines) {
        if ($lLine -match '^(1[3-9]\d{5,6}\.mmaster02),[^,]+,[^,]+,[^,]+,[^,]+,[^,]+,(F|C|E),') {
            [void]$script:VerifiedTerminalJobs.Add($Matches[1])
        }
    }
}

if ($taskData.priority_question_a.completed_requalification_job) {
    [void]$script:VerifiedTerminalJobs.Add([string]$taskData.priority_question_a.completed_requalification_job)
}

# Separate candidate jobs
$pendingUnverifiedJobIds = [System.Collections.Generic.List[string]]::new()
$activeTrackedForPrompt = [System.Collections.Generic.List[string]]::new()

foreach ($cId in $candidateJobIds) {
    if ($liveRunningJobIds.Contains($cId)) {
        $activeTrackedForPrompt.Add("$cId (Running)")
    }
    elseif ($script:VerifiedTerminalJobs.Contains($cId)) {
        Write-Host "[FILTER] Job $cId is ALREADY verified terminal ($($cId)). Filtered out from active polling." -ForegroundColor DarkGray
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

# Assertions
if (-not $script:VerifiedTerminalJobs.Contains("1404306.mmaster02")) {
    throw "ASSERTION FAILED: 1404306.mmaster02 was not recognized as verified terminal!"
}
Write-Host "[CHECK 1] 1404306.mmaster02 recognized as terminal: PASS" -ForegroundColor Green

if ($pendingUnverifiedJobIds.Contains("1404306.mmaster02")) {
    throw "ASSERTION FAILED: 1404306.mmaster02 was placed in pending unverified list!"
}
Write-Host "[CHECK 2] 1404306.mmaster02 NOT in pending unverified list: PASS" -ForegroundColor Green

if (-not $liveRunningJobIds.Contains("1404454.mmaster02")) {
    throw "ASSERTION FAILED: 1404454.mmaster02 was not recognized as live running!"
}
Write-Host "[CHECK 3] 1404454.mmaster02 recognized as live running: PASS" -ForegroundColor Green

if ($activeJobParam -ne "1404454.mmaster02 (Running)") {
    throw "ASSERTION FAILED: Expected activeJobParam '1404454.mmaster02 (Running)', got '$activeJobParam'"
}
Write-Host "[CHECK 4] activeJobParam strictly contains live job: PASS ($activeJobParam)" -ForegroundColor Green

if ($pendingUnverifiedJobIds.Count -ne 0) {
    throw "ASSERTION FAILED: Expected 0 pending unverified jobs, got $($pendingUnverifiedJobIds.Count)"
}
Write-Host "[CHECK 5] Zero pending unverified jobs: PASS" -ForegroundColor Green

Write-Host "`nALL DRY-RUN SCHEDULER EVALUATION CHECKS PASSED (5/5)." -ForegroundColor Cyan
