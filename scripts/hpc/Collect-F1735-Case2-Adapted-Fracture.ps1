# -*- coding: utf-8 -*-
# scripts/hpc/Collect-F1735-Case2-Adapted-Fracture.ps1
# Collects and Evaluates Task F1735 Case 2 Adapted Fracture Receipts from HPC Cluster

$ErrorActionPreference = 'Stop'
$repo = 'D:\Master thesis\Adaptive remeshing'
$activeTaskJson = Join-Path $repo 'project_coordination/ACTIVE_TASK.json'
$remoteDir = "/scratch9/pr21vyci/runs/f1735_case2_adapted_fracture"
$evidenceDir = Join-Path $repo 'results/validation/f1735_case2_fracture_evidence'
$summaryJson = Join-Path $repo 'results/validation/f1735_case2_fracture_summary.json'
$cfg = "$env:USERPROFILE\.ssh\codex_config"

function Download-File($remote, $local) {
    & scp -F $cfg -B -o BatchMode=yes "tu_freiberg:$remote" $local
    if ($LASTEXITCODE -ne 0) { throw "SCP failed for $remote to $local" }
}

function Invoke-Remote($cmd) {
    & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $repo '.agents/scripts/Invoke-GuardedSsh.ps1') -RemoteCommand $cmd
}

Write-Output "=== TASK F1735: COLLECTING CASE 2 ADAPTED FRACTURE RECEIPTS ==="

if (-not (Test-Path $evidenceDir)) {
    New-Item -ItemType Directory -Path $evidenceDir -Force | Out-Null
}

$task = Get-Content $activeTaskJson -Raw | ConvertFrom-Json
$jobId = $task.active_pbs_job_id
Write-Output "Active PBS Job ID: $jobId"

# 1. Download evidence files (text and tabular receipts only; exclude bulky ODB)
$filesToDownload = @(
    "pbs_execution.log",
    "PK_F1735_CASE_2_FRAC.sta",
    "PK_F1735_CASE_2_FRAC.msg",
    "PK_F1735_CASE_2_FRAC.dat",
    "PK_F1735_CASE_2_FRAC.prt",
    "PK_F1735_CASE_2_FRAC.com",
    "uel_energy_balance.csv",
    "uel_svars_out.txt"
)

foreach ($f in $filesToDownload) {
    $remote = "$remoteDir/$f"
    $local = Join-Path $evidenceDir $f
    try {
        Download-File $remote $local
        Write-Output "  Downloaded $f ($(Get-Item $local | Select-Object -ExpandProperty Length) bytes)"
    } catch {
        Write-Warning "Could not download $f (may not exist if not generated): $_"
    }
}

# 2. Check remote ODB metadata
Write-Output "Auditing remote ODB presence..."
$odbAudit = Invoke-Remote "ls -lh $remoteDir/PK_F1735_CASE_2_FRAC.odb 2>&1 || true"
Write-Output "Remote ODB: $odbAudit"

# 3. Read and Evaluate Evidence
$pbsLog = Join-Path $evidenceDir "pbs_execution.log"
$staFile = Join-Path $evidenceDir "PK_F1735_CASE_2_FRAC.sta"
$msgFile = Join-Path $evidenceDir "PK_F1735_CASE_2_FRAC.msg"
$datFile = Join-Path $evidenceDir "PK_F1735_CASE_2_FRAC.dat"

$pbsContent = if (Test-Path $pbsLog) { Get-Content $pbsLog -Raw } else { "" }
$staContent = if (Test-Path $staFile) { Get-Content $staFile -Raw } else { "" }
$msgContent = if (Test-Path $msgFile) { Get-Content $msgFile -Raw } else { "" }
$datContent = if (Test-Path $datFile) { Get-Content $datFile -Raw } else { "" }

$gates = [ordered]@{}

# GATE-01: Solver Execution Status
$solverExit0 = ($pbsContent -match "Abaqus Solver Completed with Exit Code:\s+0") -or ($staContent -match "THE ANALYSIS HAS COMPLETED SUCCESSFULLY")
$gates["GATE-01-SOLVER-COMPLETION"] = if ($solverExit0) { "PASS" } else { "EVALUATE_EXIT_STATUS" }

# GATE-02: Increment Convergence
$numIncs = 0
if ($staContent) {
    $staLines = $staContent -split "`n" | Where-Object { $_ -match '^\s*\d+\s+\d+' }
    $numIncs = $staLines.Count
}
$gates["GATE-02-INCREMENT-CONVERGENCE"] = if ($numIncs -ge 50) { "PASS" } else { "EVALUATE_INCS" }

# GATE-03: Bitwise UEL Verification
$uelVerified = ($pbsContent -match "User subroutine hash verified:\s+ce8d5edcd2911dcb018bb15275271f874e7ea62b8fb48cf4a8297469a83acdd6") -or ($pbsContent -match "Frozen UEL integrity verified PASS")
$gates["GATE-03-UEL-VERIFICATION"] = if ($uelVerified) { "PASS" } else { "FAIL" }

# GATE-04: Bitwise Deck Verification
$deckVerified = ($pbsContent -match "Production deck integrity verified PASS")
$gates["GATE-04-DECK-VERIFICATION"] = if ($deckVerified) { "PASS" } else { "FAIL" }

# GATE-05: Single-CPU Determinism
$serialVerified = ($pbsContent -match "CPUs:\s+1 \(Serial") -and ($pbsContent -match "cpus=1")
$gates["GATE-05-SERIAL-DETERMINISM"] = if ($serialVerified) { "PASS" } else { "FAIL" }

Write-Output "=== EXECUTION GATE SUMMARY ==="
$allPass = $true
foreach ($k in $gates.Keys) {
    Write-Output "  $k : $($gates[$k])"
    if ($gates[$k] -ne "PASS") { $allPass = $false }
}

$summary = [ordered]@{
    "job_id" = $jobId
    "task_id" = "F1735-CASE2-ADAPTED-FRACTURE-EXECUTION-QUALIFICATION"
    "all_gates_pass" = $allPass
    "gates" = $gates
    "converged_increments" = $numIncs
    "remote_odb_info" = ($odbAudit -join "`n").Trim()
    "collected_at" = (Get-Date).ToUniversalTime().ToString("o")
}

$summary | ConvertTo-Json -Depth 10 | Set-Content $summaryJson -Encoding UTF8
Write-Output "Saved summary receipt to: $summaryJson"
