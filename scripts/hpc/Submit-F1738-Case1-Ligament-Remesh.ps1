# -*- coding: utf-8 -*-
# scripts/hpc/Submit-F1738-Case1-Ligament-Remesh.ps1
# Submits Task F1738 Case 1 Ligament Adaptive Remeshing Experiment to PBS Queue

$ErrorActionPreference = 'Stop'
$repo = 'D:\Master thesis\Adaptive remeshing'
$activeTaskJson = Join-Path $repo 'project_coordination/ACTIVE_TASK.json'
$remoteDir = "/scratch9/pr21vyci/runs/mode1_pk_f1738_case1_ligament"
$pbsScript = "submit_f1738_case1_ligament_remesh.pbs"

function Invoke-Remote($cmd) {
    & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $repo '.agents/scripts/Invoke-GuardedSsh.ps1') -RemoteCommand $cmd
}

Write-Output "=== TASK F1738: PRE-SUBMISSION ACCOUNTING & PREFLIGHT ==="
$task = Get-Content $activeTaskJson -Raw | ConvertFrom-Json

if ($task.task_id -ne "F1738-CASE1-LIGAMENT-ADAPTIVE-REMESHING-QUALIFICATION") {
    throw "Active task is $($task.task_id), expected F1738-CASE1-LIGAMENT-ADAPTIVE-REMESHING-QUALIFICATION"
}

if ($task.submissions_consumed -ge $task.max_new_pbs_submissions) {
    throw "Submission budget exhausted: consumed $($task.submissions_consumed) of $($task.max_new_pbs_submissions)"
}

Write-Output "Checking remote staging and hashes..."
$checkOutput = Invoke-Remote "sha256sum $remoteDir/f42_mixed_uel.for $remoteDir/$pbsScript"
Write-Output $checkOutput

$checkString = ($checkOutput -join "`n")
if ($checkString -notmatch "ce8d5edcd2911dcb018bb15275271f874e7ea62b8fb48cf4a8297469a83acdd6") {
    throw "Remote SHA-256 hash mismatch on f42_mixed_uel.for"
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
$task.classification = "CASE1_LIGAMENT_REMESH_SUBMITTED"
$task | ConvertTo-Json -Depth 10 | Set-Content $activeTaskJson -Encoding UTF8

# Append to HPC_JOB_LEDGER.csv
$timestampUtc = (Get-Date).ToUniversalTime().ToString("o")
$manifestSha = (Get-FileHash (Join-Path $repo 'models/pandey_kumar_mode1/226_f1738_case1_ligament_refinement/f1738_case1_ligament.json') -Algorithm SHA256).Hash.ToLower()
$ledgerLine = "$jobId,F1738_C1_REMESH,$remoteDir,,entry_imfdfkmq,$timestampUtc,SUBMITTED,,CASE1_LIGAMENT_REMESH_SUBMITTED,$manifestSha"
Add-Content (Join-Path $repo 'project_coordination/HPC_JOB_LEDGER.csv') -Value $ledgerLine -Encoding UTF8

Write-Output "Updated ACTIVE_TASK.json and HPC_JOB_LEDGER.csv with Job ID $jobId."
Write-Output "Submission complete. Do not poll scheduler in a tight loop."
