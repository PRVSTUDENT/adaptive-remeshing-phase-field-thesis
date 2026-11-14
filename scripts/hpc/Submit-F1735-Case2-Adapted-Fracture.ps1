# -*- coding: utf-8 -*-
# scripts/hpc/Submit-F1735-Case2-Adapted-Fracture.ps1
# Submits Task F1735 Case 2 Adapted-Mesh Mode-I Phase-Field Fracture Simulation (1-CPU Serial) to PBS Queue

$ErrorActionPreference = 'Stop'
$repo = 'D:\Master thesis\Adaptive remeshing'
$activeTaskJson = Join-Path $repo 'project_coordination/ACTIVE_TASK.json'
$remoteDir = "/scratch9/pr21vyci/runs/f1735_case2_adapted_fracture"
$pbsScript = "submit_f1735_case2_adapted_fracture.pbs"

function Invoke-Remote($cmd) {
    & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $repo '.agents/scripts/Invoke-GuardedSsh.ps1') -RemoteCommand $cmd
}

Write-Output "=== TASK F1735: PRE-SUBMISSION ACCOUNTING & PREFLIGHT ==="
$task = Get-Content $activeTaskJson -Raw | ConvertFrom-Json

if ($task.task_id -ne "F1735-CASE2-ADAPTED-FRACTURE-EXECUTION-QUALIFICATION") {
    throw "Active task is $($task.task_id), expected F1735-CASE2-ADAPTED-FRACTURE-EXECUTION-QUALIFICATION"
}

if ($task.submissions_consumed -ge $task.max_new_pbs_submissions) {
    throw "Submission budget exhausted: consumed $($task.submissions_consumed) of $($task.max_new_pbs_submissions)"
}

Write-Output "Checking remote staging and hashes..."
$checkOutput = Invoke-Remote "sha256sum $remoteDir/PK_F1728_CASE_2_PROD.inp $remoteDir/f42_mixed_uel.for $remoteDir/submit_f1735_case2_adapted_fracture.pbs"
Write-Output $checkOutput

$checkString = ($checkOutput -join "`n")
if ($checkString -notmatch "ce8d5edcd2911dcb018bb15275271f874e7ea62b8fb48cf4a8297469a83acdd6") {
    throw "Remote SHA-256 hash mismatch on f42_mixed_uel.for"
}
if ($checkString -notmatch "805af9d80126588c1a3e39fe3b5f7a0f53db606106f2dbfe6260f1e1fbddbf94") {
    throw "Remote SHA-256 hash mismatch on PK_F1728_CASE_2_PROD.inp"
}
if ($checkString -notmatch "b452e852787ee77c1b914d072ce13b642b7999ab0c8df568a7e99503f9c729c5") {
    throw "Remote SHA-256 hash mismatch on submit_f1735_case2_adapted_fracture.pbs"
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

# Update ACTIVE_TASK.json safely
if (-not ($task.PSObject.Properties.Match('active_pbs_job_id').Count)) {
    $task | Add-Member -MemberType NoteProperty -Name "active_pbs_job_id" -Value $jobId
} else {
    $task.active_pbs_job_id = $jobId
}
$task.submissions_consumed = [int]$task.submissions_consumed + 1
$task.cumulative_pbs_submissions = [int]$task.cumulative_pbs_submissions + 1
if (-not ($task.historical_pbs_job_ids -contains $jobId)) {
    $task.historical_pbs_job_ids += @($jobId)
}
$task.status = "SUBMITTED_AND_QUEUED"
$task.classification = "CASE2_ADAPTED_FRACTURE_SUBMITTED_1CPU_SERIAL"
$task | ConvertTo-Json -Depth 10 | Set-Content $activeTaskJson -Encoding UTF8

# Append to HPC_JOB_LEDGER.csv
$timestampUtc = (Get-Date).ToUniversalTime().ToString("o")
$manifestSha = (Get-FileHash (Join-Path $repo 'models/pandey_kumar_mode1/225_f1735_case2_adapted_fracture/f1735_case2_fracture_execution.json') -Algorithm SHA256).Hash.ToLower()
$ledgerLine = "$jobId,PK_F1735_C2_FRAC,$remoteDir,,entry_imfdfkmq,$timestampUtc,SUBMITTED,,CASE2_ADAPTED_FRACTURE_SUBMITTED_1CPU_SERIAL,$manifestSha"
Add-Content (Join-Path $repo 'project_coordination/HPC_JOB_LEDGER.csv') -Value $ledgerLine -Encoding UTF8

Write-Output "Updated ACTIVE_TASK.json and HPC_JOB_LEDGER.csv with Job ID $jobId."
Write-Output "Submission complete. Do not poll scheduler in a tight loop."
