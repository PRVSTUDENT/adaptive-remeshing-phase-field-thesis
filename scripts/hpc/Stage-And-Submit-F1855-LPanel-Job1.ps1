# -*- coding: utf-8 -*-
# scripts/hpc/Stage-And-Submit-F1855-LPanel-Job1.ps1
# Staging, Verification, and Submission for Task F1855 L-Panel Fracture Job-1

$ErrorActionPreference = 'Stop'
$repo = 'D:\Master thesis\Adaptive remeshing'
$cfg = "$env:USERPROFILE\.ssh\codex_config"
$remoteDir = "/scratch9/pr21vyci/runs/f1855_lpanel_fracture_job1"
$pkgDir = Join-Path $repo 'models/pandey_kumar_mode1/284_f1855_lpanel_fracture_job1'
$activeTaskJson = Join-Path $repo 'project_coordination/ACTIVE_TASK.json'

function Upload-File($local, $remote) {
    & scp -F $cfg -B -o BatchMode=yes $local "tu_freiberg:$remote"
    if ($LASTEXITCODE -ne 0) { throw "SCP failed for $local to $remote" }
}

function Invoke-Remote($cmd) {
    & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $repo '.agents/scripts/Invoke-GuardedSsh.ps1') -RemoteCommand $cmd
}

Write-Output "=== TASK F1855: STAGING AND SUBMISSION PREFLIGHT ==="

# Check active task
$task = Get-Content $activeTaskJson -Raw | ConvertFrom-Json
if ($task.task_id -ne "F1855-LPANEL-FRACTURE-JOB1") {
    throw "Active task is $($task.task_id), expected F1855-LPANEL-FRACTURE-JOB1"
}
if ($task.submissions_consumed -ge $task.max_new_pbs_submissions) {
    throw "Submission budget exhausted: consumed $($task.submissions_consumed) of $($task.max_new_pbs_submissions)"
}

# Verify local files
$files = @(
    "PK_F1855_LPANEL_COARSE_JOB1.inp",
    "f42_native_miseseri_interface_v1.for",
    "job_notifications.sh",
    "submit_f1855_lpanel_job1.pbs"
)

foreach ($f in $files) {
    $local = Join-Path $pkgDir $f
    if (-not (Test-Path $local)) {
        throw "Missing local file: $local"
    }
}

# Create remote directory
Write-Output "Creating remote directory: $remoteDir"
Invoke-Remote "mkdir -p $remoteDir && chmod 755 $remoteDir"

# Upload files
foreach ($f in $files) {
    $local = Join-Path $pkgDir $f
    $remote = "$remoteDir/$f"
    Write-Output "Uploading $f via SCP..."
    Upload-File $local $remote
}

Invoke-Remote "chmod 755 $remoteDir/submit_f1855_lpanel_job1.pbs $remoteDir/job_notifications.sh"

# Verify remote hashes
Write-Output "Verifying remote SHA-256 checksums..."
$remoteSums = Invoke-Remote "sha256sum $remoteDir/PK_F1855_LPANEL_COARSE_JOB1.inp $remoteDir/f42_native_miseseri_interface_v1.for $remoteDir/submit_f1855_lpanel_job1.pbs"
Write-Output $remoteSums

$sumStr = ($remoteSums -join "`n").ToLower()
$expectedInp = (Get-FileHash (Join-Path $pkgDir "PK_F1855_LPANEL_COARSE_JOB1.inp") -Algorithm SHA256).Hash.ToLower()
$expectedFor = "e5c98b6f601b1cd586571f8e24f357d15abbd1c5d5487b52903ba249734279b2"
$expectedPbs = (Get-FileHash (Join-Path $pkgDir "submit_f1855_lpanel_job1.pbs") -Algorithm SHA256).Hash.ToLower()

if ($sumStr -notmatch $expectedInp) { throw "Remote SHA-256 hash mismatch on PK_F1855_LPANEL_COARSE_JOB1.inp" }
if ($sumStr -notmatch $expectedFor) { throw "Remote SHA-256 hash mismatch on f42_native_miseseri_interface_v1.for" }
if ($sumStr -notmatch $expectedPbs) { throw "Remote SHA-256 hash mismatch on submit_f1855_lpanel_job1.pbs" }

Write-Output "=== REMOTE STAGING INTEGRITY VERIFIED ==="

# Check active jobs on cluster before submission
$activeUserJobs = Invoke-Remote "qstat -u pr21vyci"
Write-Output "Active user jobs on scheduler: $activeUserJobs"

# Submit to PBS queue
Write-Output "Submitting $remoteDir/submit_f1855_lpanel_job1.pbs to PBS queue..."
$qsubOutput = Invoke-Remote "qsub $remoteDir/submit_f1855_lpanel_job1.pbs"
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
$task.classification = "LPANEL_COARSE_FRACTURE_JOB1_SUBMITTED_1CPU_SERIAL"
$task | ConvertTo-Json -Depth 10 | Set-Content $activeTaskJson -Encoding UTF8

# Append to HPC_JOB_LEDGER.csv
$timestampUtc = (Get-Date).ToUniversalTime().ToString("o")
$manifestSha = (Get-FileHash (Join-Path $pkgDir 'PK_F1855_LPANEL_JOB1_RECEIPT.json') -Algorithm SHA256).Hash.ToLower()
$ledgerLine = "$jobId,F1855_LPANEL_J1,$remoteDir,,entry_imfdfkmq,$timestampUtc,SUBMITTED,,LPANEL_COARSE_FRACTURE_JOB1_SUBMITTED_1CPU_SERIAL,$manifestSha"
Add-Content (Join-Path $repo 'project_coordination/HPC_JOB_LEDGER.csv') -Value $ledgerLine -Encoding UTF8

Write-Output "Updated ACTIVE_TASK.json and HPC_JOB_LEDGER.csv with Job ID $jobId."
