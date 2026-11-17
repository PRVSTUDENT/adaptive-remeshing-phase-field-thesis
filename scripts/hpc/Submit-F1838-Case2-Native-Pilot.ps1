# -*- coding: utf-8 -*-
# scripts/hpc/Submit-F1838-Case2-Native-Pilot.ps1
# Submits Task F1838 Case 2 Native Job-1 Pilot Simulation (1-CPU Serial) to PBS Queue

$ErrorActionPreference = 'Stop'
$repo = 'D:\Master thesis\Adaptive remeshing'
$activeTaskJson = Join-Path $repo 'project_coordination/ACTIVE_TASK.json'
$remoteDir = "/scratch9/pr21vyci/runs/f1838_case2_native_pilot"
$pbsScript = "submit_f1838_case2_pilot.pbs"

function Invoke-Remote($cmd) {
    & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $repo '.agents/scripts/Invoke-GuardedSsh.ps1') -RemoteCommand $cmd
}

Write-Output "=== TASK F1838: PRE-SUBMISSION ACCOUNTING & PREFLIGHT ==="
$task = Get-Content $activeTaskJson -Raw | ConvertFrom-Json

if ($task.task_id -ne "F1838-CASE2-NATIVE-JOB1-PILOT") {
    throw "Active task is $($task.task_id), expected F1838-CASE2-NATIVE-JOB1-PILOT"
}

if ($task.submissions_consumed -ge $task.max_new_pbs_submissions) {
    throw "Submission budget exhausted: consumed $($task.submissions_consumed) of $($task.max_new_pbs_submissions)"
}

Write-Output "Checking remote staging and hashes..."
$checkOutput = Invoke-Remote "sha256sum $remoteDir/PK_HOLE_COARSE_F1838_PILOT.inp $remoteDir/f42_native_miseseri_interface_v1.for $remoteDir/submit_f1838_case2_pilot.pbs"
Write-Output $checkOutput

$checkString = ($checkOutput -join "`n").ToLower()
if ($checkString -notmatch "e5c98b6f601b1cd586571f8e24f357d15abbd1c5d5487b52903ba249734279b2") {
    throw "Remote SHA-256 hash mismatch on f42_native_miseseri_interface_v1.for"
}
if ($checkString -notmatch "555d9285ea417abaa2cf08ae630d50d4dd0db99f5702f6cc45eacebd1d075785") {
    throw "Remote SHA-256 hash mismatch on PK_HOLE_COARSE_F1838_PILOT.inp"
}
if ($checkString -notmatch "b12b7737a1132c8392a4e2376dbcb4249b982d7554b98622e5324c89016c3836") {
    throw "Remote SHA-256 hash mismatch on submit_f1838_case2_pilot.pbs"
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
if (-not ($task.PSObject.Properties.Match('historical_pbs_job_ids').Count)) {
    $task | Add-Member -MemberType NoteProperty -Name "historical_pbs_job_ids" -Value @($jobId)
} else {
    if (-not ($task.historical_pbs_job_ids -contains $jobId)) {
        $task.historical_pbs_job_ids += @($jobId)
    }
}
$task.status = "SUBMITTED_AND_QUEUED"
$task.classification = "CASE2_NATIVE_JOB1_PILOT_SUBMITTED_1CPU_SERIAL"
$task | ConvertTo-Json -Depth 10 | Set-Content $activeTaskJson -Encoding UTF8

# Append to HPC_JOB_LEDGER.csv
$timestampUtc = (Get-Date).ToUniversalTime().ToString("o")
$manifestSha = (Get-FileHash (Join-Path $repo 'models/pandey_kumar_mode1/277_f1838_case2_native_pilot/PK_F1838_CASE2_PILOT_RECEIPT.json') -Algorithm SHA256).Hash.ToLower()
$ledgerLine = "$jobId,M1_C2_NATIVE_PILOT,$remoteDir,,entry_imfdfkmq,$timestampUtc,SUBMITTED,,CASE2_NATIVE_JOB1_PILOT_SUBMITTED_1CPU_SERIAL,$manifestSha"
Add-Content (Join-Path $repo 'project_coordination/HPC_JOB_LEDGER.csv') -Value $ledgerLine -Encoding UTF8

Write-Output "Updated ACTIVE_TASK.json and HPC_JOB_LEDGER.csv with Job ID $jobId."
Write-Output "Submission complete. Do not poll scheduler in a tight loop."
