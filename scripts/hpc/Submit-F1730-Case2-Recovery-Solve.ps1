# -*- coding: utf-8 -*-
# scripts/hpc/Submit-F1730-Case2-Recovery-Solve.ps1
# Submits Task F1730 Case 2 Companion Recovery Abaqus Solve to PBS Queue

$ErrorActionPreference = 'Stop'
$repo = 'D:\Master thesis\Adaptive remeshing'
$activeTaskJson = Join-Path $repo 'project_coordination/ACTIVE_TASK.json'
$remoteDir = "/scratch9/pr21vyci/runs/f1730_case2_recovery_solve"
$pbsScript = "submit_f1730_case2_recovery_solve.pbs"

function Invoke-Remote($cmd) {
    & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $repo '.agents/scripts/Invoke-GuardedSsh.ps1') -RemoteCommand $cmd
}

Write-Output "=== TASK F1730: PRE-SUBMISSION ACCOUNTING & PREFLIGHT ==="
$task = Get-Content $activeTaskJson -Raw | ConvertFrom-Json

if ($task.task_id -ne "F1730-CASE2-COMPANION-RECOVERY-SOLVE") {
    throw "Active task is $($task.task_id), expected F1730-CASE2-COMPANION-RECOVERY-SOLVE"
}

if ($task.submissions_consumed -ge $task.max_new_pbs_submissions) {
    throw "Submission budget exhausted: consumed $($task.submissions_consumed) of $($task.max_new_pbs_submissions)"
}

Write-Output "Checking remote staging and hashes..."
$checkOutput = Invoke-Remote "sha256sum $remoteDir/PK_HOLE_COMPANION_RECOVERY.inp"
Write-Output $checkOutput

if ($checkOutput -notmatch "0286f591f865e060d3c34482671d8e378916831d3781db17a4e8bc70963e51e0") {
    throw "Remote SHA-256 hash mismatch on PK_HOLE_COMPANION_RECOVERY.inp"
}

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
$task.submissions_consumed = 1
$task.status = "SUBMITTED_AND_QUEUED"
$task.classification = "CASE2_RECOVERY_SOLVE_SUBMITTED"
$task | ConvertTo-Json -Depth 10 | Set-Content $activeTaskJson -Encoding UTF8

# Append to HPC_JOB_LEDGER.csv
$timestampUtc = (Get-Date).ToUniversalTime().ToString("o")
$manifestSha = "0286f591f865e060d3c34482671d8e378916831d3781db17a4e8bc70963e51e0"
$ledgerLine = "$jobId,F1730_CASE2_SOLVE,$remoteDir,,entry_imfdfkmq,$timestampUtc,SUBMITTED,,CASE2_RECOVERY_SOLVE_SUBMITTED,$manifestSha"
Add-Content (Join-Path $repo 'project_coordination/HPC_JOB_LEDGER.csv') -Value $ledgerLine -Encoding UTF8

Write-Output "Updated ACTIVE_TASK.json and HPC_JOB_LEDGER.csv with Job ID $jobId."
Write-Output "Submission complete. Do not poll scheduler in a tight loop."
