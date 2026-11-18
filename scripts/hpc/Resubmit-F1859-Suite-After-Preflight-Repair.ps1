# -*- coding: utf-8 -*-
# scripts/hpc/Resubmit-F1859-Suite-After-Preflight-Repair.ps1
# Resubmission of F1859 Suite following deterministic preflight repair of EXPECTED_INP_SHA

$ErrorActionPreference = 'Stop'
$repo = 'D:\Master thesis\Adaptive remeshing'
$remoteSuiteBase = "/scratch9/pr21vyci/runs/f1859_suite"
$localSuiteDir = Join-Path $repo 'models/pandey_kumar_mode1/286_f1859_four_benchmark_reference_comparison'
$activeTaskJson = Join-Path $repo 'project_coordination/ACTIVE_TASK.json'
$hpcLedgerPath = Join-Path $repo 'project_coordination/HPC_JOB_LEDGER.csv'
$receiptPath = Join-Path $localSuiteDir 'f1859_suite_receipt.json'

function Upload-File($local, $remote) {
    & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $repo '.agents/scripts/Invoke-GuardedSsh.ps1') -UploadFile $local -RemotePath $remote
    if ($LASTEXITCODE -ne 0) { throw "Guarded upload failed for $local to $remote" }
}

function Invoke-Remote($cmd) {
    & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $repo '.agents/scripts/Invoke-GuardedSsh.ps1') -RemoteCommand $cmd
}

Write-Output "=== TASK F1859: PREFLIGHT REPAIR RESUBMISSION (8 JOBS) ==="

# 1. Update HPC_JOB_LEDGER.csv for failed runs 1424411-1424418
$failedIds = @(
    "1424411.mmaster02", "1424412.mmaster02", "1424413.mmaster02", "1424414.mmaster02",
    "1424415.mmaster02", "1424416.mmaster02", "1424417.mmaster02", "1424418.mmaster02"
)
$nowUtc = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")

$ledgerContent = Get-Content $hpcLedgerPath
$newLedger = @()
foreach ($line in $ledgerContent) {
    $matched = $false
    foreach ($fid in $failedIds) {
        if ($line.StartsWith($fid) -and $line.Contains(",SUBMITTED,")) {
            # Update to FAILED
            $updatedLine = $line.Replace(",SUBMITTED,,F1859_PARALLEL_SUITE_SUBMITTED_8CPU_SMP,", ",FAILED,1,PREFLIGHT_INPUT_DECK_SHA_MISMATCH_EXPECTED_CRLF_ACTUAL_LF,")
            $newLedger += $updatedLine
            $matched = $true
            break
        }
    }
    if (-not $matched) {
        $newLedger += $line
    }
}
$newLedger | Set-Content -LiteralPath $hpcLedgerPath -Encoding UTF8
Write-Output "Updated HPC_JOB_LEDGER.csv with FAILED status for jobs 1424411-1424418."

# 2. Upload repaired .pbs scripts and submit
$receipt = Get-Content $receiptPath -Raw | ConvertFrom-Json
$submittedJobs = @()

foreach ($jobProp in $receipt.jobs.PSObject.Properties) {
    $job = $jobProp.Value
    $jid = $job.job_name
    $mname = $job.model_name
    $sdir = $job.scratch_dir
    $subDirName = Split-Path $sdir -Leaf
    $localJobDir = Join-Path $localSuiteDir $subDirName
    $pbsFile = "submit_$($jid.ToLower()).pbs"
    $localPbs = Join-Path $localJobDir $pbsFile
    $remotePbs = "$sdir/$pbsFile"

    Write-Output "`n------------------------------------------------------------"
    Write-Output "UPLOADING AND RESUBMITTING: $jid ($mname)"
    Write-Output "------------------------------------------------------------"

    # Upload repaired PBS script
    Upload-File $localPbs $remotePbs
    Invoke-Remote "chmod 755 $remotePbs"

    # Verify remote hash of PBS script and input deck
    $remoteSums = Invoke-Remote "sha256sum $remotePbs $sdir/$mname.inp"
    Write-Output "Remote hashes: $remoteSums"

    $sumStr = ($remoteSums -join "`n").ToLower()
    $expectedInp = $job.deck_sha256.ToLower()
    $expectedPbs = $job.pbs_sha256.ToLower()

    if ($sumStr -notmatch $expectedInp) { throw "Remote SHA mismatch on $mname.inp" }
    if ($sumStr -notmatch $expectedPbs) { throw "Remote SHA mismatch on $pbsFile" }

    # Clean old pbs_execution.log so new log starts fresh
    Invoke-Remote "rm -f $sdir/pbs_execution.log"

    # Submit job
    Write-Output "Submitting $remotePbs to PBS queue entry_imfdfkmq..."
    $qsubOut = Invoke-Remote "qsub $remotePbs"
    Write-Output "qsub output: $qsubOut"

    $match = [regex]::Match($qsubOut, '(\d+\.mmaster02|\d+)')
    if (-not $match.Success) {
        throw "Failed to parse PBS Job ID from qsub output: $qsubOut"
    }
    $pbsId = $match.Value
    if ($pbsId -notmatch '\.mmaster02$') {
        $pbsId = "${pbsId}.mmaster02"
    }

    Write-Output ">>> RESUBMITTED: $jid -> NEW PBS ID: $pbsId <<<"

    $submittedJobs += [PSCustomObject]@{
        job_name = $jid
        pbs_job_id = $pbsId
        category = $job.category
        case_id = $job.case_id
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

# 3. Update receipts and active task
$submissionSummaryPath = Join-Path $localSuiteDir "f1859_submission_receipt.json"
$submittedJobs | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $submissionSummaryPath -Encoding UTF8
Write-Output "`nUpdated submission receipt saved to $submissionSummaryPath"

# Append new jobs to HPC_JOB_LEDGER.csv
$submitTimeUtc = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
foreach ($sj in $submittedJobs) {
    $row = "$($sj.pbs_job_id),$($sj.job_name),$($sj.scratch_dir),,entry_imfdfkmq,$submitTimeUtc,SUBMITTED,,F1859_PARALLEL_SUITE_RESUBMITTED_PREFLIGHT_REPAIR_8CPU_SMP,$($sj.deck_sha256.ToLower())"
    Add-Content -LiteralPath $hpcLedgerPath -Value $row -Encoding UTF8
}
Write-Output "Appended 8 new entries to HPC_JOB_LEDGER.csv"

# Update ACTIVE_TASK.json
$task = Get-Content $activeTaskJson -Raw | ConvertFrom-Json
$task.active_pbs_job_id = ($submittedJobs | ForEach-Object { $_.pbs_job_id }) -join ","
$task.notes = "All 8 F1859 jobs resubmitted following preflight repair (EXPECTED_INP_SHA LF normalization). Running on entry_imfdfkmq (8 CPUs SMP, 24GB RAM, 48h walltime each)."
$task | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $activeTaskJson -Encoding UTF8
Write-Output "Updated ACTIVE_TASK.json with new active PBS Job IDs."
