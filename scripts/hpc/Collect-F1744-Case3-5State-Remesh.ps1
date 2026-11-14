# -*- coding: utf-8 -*-
# scripts/hpc/Collect-F1744-Case3-5State-Remesh.ps1
# Collects evidence and validates completion for Task F1744 Case 3 5-State Sequential Remeshing

$ErrorActionPreference = 'Stop'
$repo = 'D:\Master thesis\Adaptive remeshing'
$activeTaskJson = Join-Path $repo 'project_coordination/ACTIVE_TASK.json'
$remoteDir = "/scratch9/pr21vyci/runs/mode1_pk_f1744_case3_5state_remesh"
$pkgDir = Join-Path $repo 'models/pandey_kumar_mode1/230_f1744_case3_5state_remesh'
$cfg = "$env:USERPROFILE\.ssh\codex_config"

function Invoke-Remote($cmd) {
    & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $repo '.agents/scripts/Invoke-GuardedSsh.ps1') -RemoteCommand $cmd
}

function Download-File($remote, $local) {
    & scp -F $cfg -B -o BatchMode=yes "tu_freiberg:$remote" $local
    if ($LASTEXITCODE -ne 0) { throw "SCP failed for $remote to $local" }
}

Write-Output "=== TASK F1744: COLLECTING 5-STATE REMESHING RESULTS ==="
$rawContent = [System.IO.File]::ReadAllText($activeTaskJson, [System.Text.Encoding]::UTF8)
$task = ConvertFrom-Json $rawContent
$jobId = $task.active_pbs_job_id

if (-not $jobId) {
    throw "No active PBS job ID recorded in ACTIVE_TASK.json"
}

Write-Output "Active PBS Job ID: $jobId"

# Check scheduler status
$qstatRaw = Invoke-Remote "qstat $jobId 2>&1 || true"
Write-Output "qstat output: $qstatRaw"

$checkDone = Invoke-Remote "test -f $remoteDir/f1744_case3_spatial_audit.json && echo 'DONE' || echo 'NOT_DONE'"
if (($checkDone -join "") -notmatch "DONE") {
    Write-Output "Job $jobId is still executing or audit JSON not yet produced."
    exit 0
}

Write-Output "Spatial audit JSON detected on cluster. Downloading evidence..."
$localAudit = Join-Path $repo 'results/validation/f1744_case3_spatial_audit.json'
Download-File "$remoteDir/f1744_case3_spatial_audit.json" $localAudit

$localLog = Join-Path $pkgDir 'pbs_execution.log'
Download-File "$remoteDir/pbs_execution.log" $localLog

$localPhys = Join-Path $pkgDir 'PK_F1744_CASE_3_ADAPT_PHYS.inp'
Download-File "$remoteDir/PK_F1744_CASE_3_ADAPT_PHYS.inp" $localPhys

$localProd = Join-Path $pkgDir 'PK_F1744_CASE_3_PROD.inp'
Download-File "$remoteDir/PK_F1744_CASE_3_PROD.inp" $localProd

$localDat = Join-Path $pkgDir 'PK_F1744_CASE_3_DC.dat'
Download-File "$remoteDir/PK_F1744_CASE_3_DC.dat" $localDat

# Inspect spatial audit
$auditContent = Get-Content $localAudit -Raw | ConvertFrom-Json
Write-Output "Downloaded spatial audit summary:"
Write-Output "  Total physical elements: $($auditContent.total_physical_elements)"
Write-Output "  Quad percentage: $($auditContent.quad_percentage)%"
Write-Output "  Min Jacobian det: $($auditContent.min_jacobian_det)"
Write-Output "  Primary Corridor Area <= l0/2: $($auditContent.primary_corridor.pct_area_le_l0_half)%"
Write-Output "  Primary Coarse Barrier: $($auditContent.primary_corridor.has_transverse_coarse_barrier)"
Write-Output "  Secondary Corridor Area <= l0/2: $($auditContent.secondary_corridor.pct_area_le_l0_half)%"
Write-Output "  Secondary Coarse Barrier: $($auditContent.secondary_corridor.has_transverse_coarse_barrier)"
Write-Output "  Hole boundary mean h: $($auditContent.hole_boundary_mean_h_mm) mm"

# Determine classification
$allPass = $true
if ($auditContent.primary_corridor.pct_area_le_l0_half -lt 85.0) { $allPass = $false }
if ($auditContent.secondary_corridor.pct_area_le_l0_half -lt 85.0) { $allPass = $false }
if ($auditContent.primary_corridor.has_transverse_coarse_barrier -or $auditContent.secondary_corridor.has_transverse_coarse_barrier) { $allPass = $false }
if (-not $auditContent.zero_negative_jacobians) { $allPass = $false }

if ($allPass) {
    $class = "CASE3_5STATE_REMESHING_COMPLETE_ALL_SPATIAL_GATES_PASS"
} else {
    $class = "CASE3_5STATE_REMESHING_COMPLETE_SPATIAL_GATE_DEFICIENCY"
}

# Update ACTIVE_TASK.json
$task.status = "COMPLETED"
$task.classification = $class
$task.checkpoint_artifact = "results/validation/f1744_case3_spatial_audit.json"
$updatedJson = ConvertTo-Json $task -Depth 10
[System.IO.File]::WriteAllText($activeTaskJson, $updatedJson, [System.Text.Encoding]::UTF8)

# Update HPC_JOB_LEDGER.csv
$ledgerPath = Join-Path $repo 'project_coordination/HPC_JOB_LEDGER.csv'
$timestampUtc = (Get-Date).ToUniversalTime().ToString("o")
$manifestSha = (Get-FileHash (Join-Path $pkgDir 'f1744_case3_5state_remesh.json') -Algorithm SHA256).Hash.ToLower()
$completedLine = "$jobId,F1744_C3_REMESH,$remoteDir,mnode097,normal_imfdfkmq,$timestampUtc,COMPLETED,0,$class,$manifestSha"
Add-Content $ledgerPath -Value $completedLine

Write-Output "Task F1744 collection complete. Classification: $class"
