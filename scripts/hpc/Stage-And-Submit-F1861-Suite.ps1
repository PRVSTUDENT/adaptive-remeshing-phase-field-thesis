# -*- coding: utf-8 -*-
# scripts/hpc/Stage-And-Submit-F1861-Suite.ps1
# Staging, Verification, and Parallel Submission for Task F1861 Uniform Reference Suite (4 Jobs)

$ErrorActionPreference = 'Stop'
$repo = 'D:\Master thesis\Adaptive remeshing'
$remoteSuiteBase = "/scratch9/pr21vyci/runs/f1861_uniform_reference"
$localSuiteDir = Join-Path $repo 'models/pandey_kumar_mode1/288_f1861_uniform_reference'
$activeTaskJson = Join-Path $repo 'project_coordination/ACTIVE_TASK.json'
$receiptPath = Join-Path $localSuiteDir 'f1861_suite_receipt.json'

function Upload-File($local, $remote) {
    & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $repo '.agents/scripts/Invoke-GuardedSsh.ps1') -UploadFile $local -RemotePath $remote
    if ($LASTEXITCODE -ne 0) { throw "Guarded upload failed for $local to $remote" }
}

function Invoke-Remote($cmd) {
    & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $repo '.agents/scripts/Invoke-GuardedSsh.ps1') -RemoteCommand $cmd
}

Write-Output "=== TASK F1861: PARALLEL UNIFORM REFERENCE SUITE STAGING AND SUBMISSION ==="

$task = Get-Content $activeTaskJson -Raw | ConvertFrom-Json
if ($task.task_id -ne "F1861-UNIFORM-HIGHLY-REFINED-REFERENCE") {
    throw "Active task is $($task.task_id), expected F1861-UNIFORM-HIGHLY-REFINED-REFERENCE"
}
if ($task.submissions_consumed -ge $task.max_new_pbs_submissions) {
    throw "Submission budget exhausted: consumed $($task.submissions_consumed) of $($task.max_new_pbs_submissions)"
}

$receipt = Get-Content $receiptPath -Raw | ConvertFrom-Json

# Check active jobs on cluster before submission
$activeUserJobs = Invoke-Remote "qstat -u pr21vyci"
Write-Output "Initial active user jobs on scheduler: $activeUserJobs"

# Create base remote suite dir
Invoke-Remote "mkdir -p $remoteSuiteBase && chmod 755 $remoteSuiteBase"

$submittedJobs = @()

foreach ($jobProp in $receipt.jobs.PSObject.Properties) {
    $job = $jobProp.Value
    $jid = $job.job_name
    $mname = $job.model_name
    $sdir = $job.scratch_dir
    $subDirName = Split-Path $sdir -Leaf
    $localJobDir = Join-Path $localSuiteDir $subDirName

    Write-Output "`n------------------------------------------------------------"
    Write-Output "STAGING AND SUBMITTING: $jid ($mname)"
    Write-Output "------------------------------------------------------------"

    # Create remote dir
    Invoke-Remote "mkdir -p $sdir && chmod 755 $sdir"

    # Files to upload
    $inpFile = "$mname.inp"
    $pbsFile = "submit_$($jid.ToLower()).pbs"
    $subFile = "f42_native_miseseri_interface_v1.for"
    $notifFile = "job_notifications.sh"

    $filesToUpload = @($inpFile, $pbsFile, $subFile, $notifFile)
    foreach ($f in $filesToUpload) {
        $loc = Join-Path $localJobDir $f
        if (-not (Test-Path $loc)) { throw "Missing local file: $loc" }
        $rem = "$sdir/$f"
        Write-Output "Uploading $f..."
        Upload-File $loc $rem
    }

    Invoke-Remote "chmod 755 $sdir/$pbsFile $sdir/$notifFile"

    # Verify remote hashes
    Write-Output "Verifying remote SHA-256 hashes..."
    $remoteSums = Invoke-Remote "sha256sum $sdir/$inpFile $sdir/$subFile $sdir/$pbsFile"
    Write-Output $remoteSums

    $sumStr = ($remoteSums -join "`n").ToLower()
    $expectedInp = $job.deck_sha256.ToLower()
    $expectedFor = "e5c98b6f601b1cd586571f8e24f357d15abbd1c5d5487b52903ba249734279b2"
    $expectedPbs = $job.pbs_sha256.ToLower()

    if ($sumStr -notmatch $expectedInp) { throw "Remote SHA mismatch on $inpFile" }
    if ($sumStr -notmatch $expectedFor) { throw "Remote SHA mismatch on $subFile" }
    if ($sumStr -notmatch $expectedPbs) { throw "Remote SHA mismatch on $pbsFile" }

    Write-Output "Remote integrity verified for $jid."

    # Submit job
    Write-Output "Submitting $sdir/$pbsFile to PBS queue entry_imfdfkmq..."
    $qsubOut = Invoke-Remote "qsub $sdir/$pbsFile"
    Write-Output "qsub output: $qsubOut"

    $match = [regex]::Match($qsubOut, '(\d+\.mmaster02|\d+)')
    if (-not $match.Success) {
        throw "Failed to parse PBS Job ID from qsub output: $qsubOut"
    }
    $pbsId = $match.Value
    if ($pbsId -notmatch '\.mmaster02$') {
        $pbsId = "${pbsId}.mmaster02"
    }

    Write-Output ">>> SUBMITTED: $jid -> PBS ID: $pbsId <<<"

    $submittedJobs += [PSCustomObject]@{
        job_name = $jid
        pbs_job_id = $pbsId
        case_id = $job.case_id
        name = $job.name
        model_name = $mname
        physical_elements = $job.physical_elements
        layered_elements = $job.layered_elements
        cpus = $job.cpus
        memory = $job.memory
        walltime = $job.walltime
        queue = $job.queue
        scratch_dir = $sdir
        deck_sha256 = $job.deck_sha256
        submitted_at_utc = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
    }

    Start-Sleep -Seconds 1
}

Write-Output "`n============================================================"
Write-Output "ALL 4 UNIFORM REFERENCE JOBS SUCCESSFULLY SUBMITTED IN PARALLEL!"
Write-Output "============================================================"

# Save submission receipt
$submissionSummaryPath = Join-Path $localSuiteDir "f1861_submission_receipt.json"
$submittedJobs | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $submissionSummaryPath -Encoding UTF8
Write-Output "Submission receipt saved to $submissionSummaryPath"

# Append to HPC_JOB_LEDGER.csv
$hpcLedgerPath = Join-Path $repo 'project_coordination/HPC_JOB_LEDGER.csv'
$nowUtc = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")

foreach ($sj in $submittedJobs) {
    $row = "$($sj.pbs_job_id),$($sj.job_name),$($sj.scratch_dir),,entry_imfdfkmq,$nowUtc,SUBMITTED,,F1861_UNIFORM_REFERENCE_PARALLEL_16CPU_SMP,$($sj.deck_sha256.ToLower())"
    Add-Content -LiteralPath $hpcLedgerPath -Value $row -Encoding UTF8
}
Write-Output "Appended 4 entries to HPC_JOB_LEDGER.csv (cumulative 53 -> 57)."

# Update ACTIVE_TASK.json
$task.submissions_consumed = 4
$task.cumulative_pbs_submissions = 57
$task.active_pbs_job_id = ($submittedJobs | ForEach-Object { $_.pbs_job_id }) -join ","
$task.notes = "All 4 F1861 uniform reference jobs submitted in parallel via entry_imfdfkmq (16 CPUs SMP, 48GB RAM, 72h walltime each). Cumulative PBS 57."
$task | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $activeTaskJson -Encoding UTF8
Write-Output "Updated ACTIVE_TASK.json: 4 submissions consumed, cumulative 57."
