# -*- coding: utf-8 -*-
# scripts/hpc/Submit-F1744-Case3-5State-Remesh.ps1
# Submits Task F1744 Case 3 5-State Sequential Native Remeshing to PBS Queue

$ErrorActionPreference = 'Stop'
$repo = 'D:\Master thesis\Adaptive remeshing'
$activeTaskJson = Join-Path $repo 'project_coordination/ACTIVE_TASK.json'
$remoteDir = "/scratch9/pr21vyci/runs/mode1_pk_f1744_case3_5state_remesh"
$pbsScript = "submit_f1744_case3_5state_remesh.pbs"

function Invoke-Remote($cmd) {
    & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $repo '.agents/scripts/Invoke-GuardedSsh.ps1') -RemoteCommand $cmd
}

Write-Output "=== TASK F1744: PRE-SUBMISSION ACCOUNTING & PREFLIGHT ==="
$rawContent = [System.IO.File]::ReadAllText($activeTaskJson, [System.Text.Encoding]::UTF8)
$task = ConvertFrom-Json $rawContent

if ($task.task_id -ne "F1744-CASE3-5STATE-REMESHING-EXECUTION") {
    throw "Active task is $($task.task_id), expected F1744-CASE3-5STATE-REMESHING-EXECUTION"
}

if ($task.submissions_consumed -ge $task.max_new_pbs_submissions) {
    throw "Submission budget exhausted: consumed $($task.submissions_consumed) of $($task.max_new_pbs_submissions)"
}

Write-Output "Checking remote staging and hashes..."
$checkOutput = Invoke-Remote "sha256sum $remoteDir/f42_mixed_uel.for $remoteDir/$pbsScript $remoteDir/run_case3_5state_remesh.py $remoteDir/audit_case3_5state_resolution.py $remoteDir/PK_SEC43_COMPANION_T1.inp"
Write-Output $checkOutput

$checkString = ($checkOutput -join "`n")
if ($checkString -notmatch "ce8d5edcd2911dcb018bb15275271f874e7ea62b8fb48cf4a8297469a83acdd6") {
    throw "Remote SHA-256 hash mismatch on f42_mixed_uel.for"
}

Write-Output "Verifying State 2 and State 4 donor ODBs present in $remoteDir..."
$odbCheck = Invoke-Remote "ls -l $remoteDir/PK_SEC43_PRESCRIBED_STATE*.odb"
Write-Output $odbCheck

Write-Output "Clearing any stale lock files..."
Invoke-Remote "rm -f $remoteDir/F1744_C3_REMESH.lck"

Write-Output "Submitting $remoteDir/$pbsScript to PBS queue entry_imfdfkmq..."
$qsubOutput = Invoke-Remote "qsub $remoteDir/$pbsScript"
Write-Output "qsub output: $qsubOutput"

$jobIdMatch = [regex]::Match($qsubOutput, '(\d+\.mmaster02|\d+)')
if (-not $jobIdMatch.Success) {
    throw "Failed to parse PBS Job ID from qsub output: $qsubOutput"
}
$jobId = $jobIdMatch.Value
if ($jobId -notmatch '\.mmaster02$') {
    $jobId = "${jobId}.mmaster02"
}

Write-Output "=== PBS SUBMISSION ACCEPTED: $jobId ==="

# Update ACTIVE_TASK.json
$task.active_pbs_job_id = $jobId
$task.submissions_consumed = $task.submissions_consumed + 1
$task.cumulative_pbs_submissions = $task.cumulative_pbs_submissions + 1
$task.historical_pbs_job_ids += $jobId
$task.status = "SUBMITTED_AND_QUEUED"
$task.classification = "CASE3_5STATE_REMESHING_SUBMITTED"
$updatedJson = ConvertTo-Json $task -Depth 10
[System.IO.File]::WriteAllText($activeTaskJson, $updatedJson, [System.Text.Encoding]::UTF8)

# Append to HPC_JOB_LEDGER.csv
$timestampUtc = (Get-Date).ToUniversalTime().ToString("o")
$manifestSha = (Get-FileHash (Join-Path $repo 'models/pandey_kumar_mode1/230_f1744_case3_5state_remesh/f1744_case3_5state_remesh.json') -Algorithm SHA256).Hash.ToLower()
$ledgerLine = "$jobId,F1744_C3_REMESH,$remoteDir,,entry_imfdfkmq,$timestampUtc,SUBMITTED,,CASE3_5STATE_REMESHING_SUBMITTED,$manifestSha"
Add-Content (Join-Path $repo 'project_coordination/HPC_JOB_LEDGER.csv') -Value $ledgerLine

Write-Output "Recorded submission $jobId in HPC_JOB_LEDGER.csv and ACTIVE_TASK.json."
Write-Output "Cumulative PBS submissions: $($task.cumulative_pbs_submissions)"
