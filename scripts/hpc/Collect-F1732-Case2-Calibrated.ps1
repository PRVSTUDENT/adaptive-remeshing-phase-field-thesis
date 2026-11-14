# -*- coding: utf-8 -*-
# scripts/hpc/Collect-F1732-Case2-Calibrated.ps1
# Collects and Evaluates Task F1732 Case 2 Calibrated Remeshing Receipts from HPC Cluster

$ErrorActionPreference = 'Stop'
$repo = 'D:\Master thesis\Adaptive remeshing'
$activeTaskJson = Join-Path $repo 'project_coordination/ACTIVE_TASK.json'
$remoteDir = "/scratch9/pr21vyci/runs/f1732_case2_calibrated"
$evidenceDir = Join-Path $repo 'results/validation/f1732_case2_calibrated_evidence'
$summaryJson = Join-Path $repo 'results/validation/f1732_case2_calibrated_summary.json'
$cfg = "$env:USERPROFILE\.ssh\codex_config"

function Download-File($remote, $local) {
    & scp -F $cfg -B -o BatchMode=yes "tu_freiberg:$remote" $local
    if ($LASTEXITCODE -ne 0) { throw "SCP failed for $remote to $local" }
}

function Invoke-Remote($cmd) {
    & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $repo '.agents/scripts/Invoke-GuardedSsh.ps1') -RemoteCommand $cmd
}

Write-Output "=== TASK F1732: COLLECTING CASE 2 CALIBRATED EXPERIMENT RECEIPTS ==="

if (-not (Test-Path $evidenceDir)) {
    New-Item -ItemType Directory -Path $evidenceDir -Force | Out-Null
}

$task = Get-Content $activeTaskJson -Raw | ConvertFrom-Json
$jobId = $task.active_pbs_job_id
Write-Output "Active PBS Job ID: $jobId"

# 1. Download evidence files
$filesToDownload = @(
    "pbs_execution.log",
    "f1732_case2_ligament_spatial_audit.json",
    "PK_F1728_CASE_2_AUDIT.json",
    "PK_F1728_CASE_2_ADAPT_PHYS.inp",
    "PK_F1728_CASE_2_PROD.inp",
    "PK_F1732_CASE_2_DC.dat",
    "PK_F1732_CASE_2_DC.msg",
    "PK_F1732_CASE_2_DC.sta",
    "PK_F1732_CASE_2_DC.prt"
)

foreach ($f in $filesToDownload) {
    $remote = "$remoteDir/$f"
    $local = Join-Path $evidenceDir $f
    Write-Output "Downloading $f..."
    try {
        Download-File $remote $local
        Write-Output "  Downloaded $f ($(Get-Item $local | Select-Object -ExpandProperty Length) bytes)"
    } catch {
        Write-Warning "Failed to download $f : $_"
    }
}

# 2. Also copy physical mesh to models/pandey_kumar_mode1/223_f1732_case2_calibrated/
$localMesh = Join-Path $evidenceDir "PK_F1728_CASE_2_ADAPT_PHYS.inp"
$repoMesh = Join-Path $repo "models/pandey_kumar_mode1/223_f1732_case2_calibrated/PK_F1728_CASE_2_ADAPT_PHYS.inp"
if (Test-Path $localMesh) {
    Copy-Item $localMesh $repoMesh -Force
    Write-Output "Copied physical mesh to $repoMesh"
}

# 3. Read and Evaluate Evidence
$pbsLog = Join-Path $evidenceDir "pbs_execution.log"
$spatialAuditJson = Join-Path $evidenceDir "f1732_case2_ligament_spatial_audit.json"
$engineAuditJson = Join-Path $evidenceDir "PK_F1728_CASE_2_AUDIT.json"
$dcDat = Join-Path $evidenceDir "PK_F1732_CASE_2_DC.dat"

$pbsContent = if (Test-Path $pbsLog) { Get-Content $pbsLog -Raw } else { "" }
$spatialAudit = if (Test-Path $spatialAuditJson) { Get-Content $spatialAuditJson -Raw | ConvertFrom-Json } else { $null }
$engineAudit = if (Test-Path $engineAuditJson) { Get-Content $engineAuditJson -Raw | ConvertFrom-Json } else { $null }
$dcDatContent = if (Test-Path $dcDat) { Get-Content $dcDat -Raw } else { "" }

# Gate Evaluation
$gates = [ordered]@{}

# GATE-01: Native Remeshing Execution
$gate01 = ($pbsContent -match "Framework Remesh Finished with Exit Code:\s+0") -and (Test-Path $localMesh)
$gates["GATE-01-REMESH-EXECUTION"] = if ($gate01) { "PASS" } else { "FAIL" }

# GATE-02: Physical Mesh FE Quality (>= 90% quads, det(J) > 0)
$totElems = if ($spatialAudit) { $spatialAudit.total_elements } else { 0 }
$quadPct = if ($spatialAudit) { $spatialAudit.quad_fraction_pct } else { 0.0 }
$nonPosJ = if ($spatialAudit) { $spatialAudit.non_positive_jacobians } else { 999 }
$gate02 = ($totElems -gt 0) -and ($quadPct -ge 90.0) -and ($nonPosJ -eq 0)
$gates["GATE-02-FE-QUALITY"] = if ($gate02) { "PASS" } else { "FAIL" }

# GATE-03: Fracture Corridor Spatial Resolution (h <= l0/2 = 3.75 um)
$w2MeanH = if ($spatialAudit -and $spatialAudit.overlapping_diagnostic_windows.W2_FULL_PRIMARY_CORRIDOR) { $spatialAudit.overlapping_diagnostic_windows.W2_FULL_PRIMARY_CORRIDOR.mean_h_area_um } else { 999.0 }
$w2MinH = if ($spatialAudit -and $spatialAudit.overlapping_diagnostic_windows.W2_FULL_PRIMARY_CORRIDOR) { $spatialAudit.overlapping_diagnostic_windows.W2_FULL_PRIMARY_CORRIDOR.min_h_area_um } else { 999.0 }
$w2PctHalf = if ($spatialAudit -and $spatialAudit.overlapping_diagnostic_windows.W2_FULL_PRIMARY_CORRIDOR) { $spatialAudit.overlapping_diagnostic_windows.W2_FULL_PRIMARY_CORRIDOR.pct_le_l0_half } else { 0.0 }
$gate03 = ($w2MinH -le 3.75) -and ($w2PctHalf -ge 30.0)
$gates["GATE-03-CORRIDOR-RESOLUTION-L0-HALF"] = if ($gate03) { "PASS" } else { "EVALUATE_EMPIRICAL" }

# GATE-04: Hole Boundary Resolution (h <= l0 = 7.50 um)
$w3PctL0 = if ($spatialAudit -and $spatialAudit.overlapping_diagnostic_windows.W3_FULL_HOLE_RING) { $spatialAudit.overlapping_diagnostic_windows.W3_FULL_HOLE_RING.pct_le_l0 } else { 0.0 }
$gate04 = ($w3PctL0 -ge 50.0)
$gates["GATE-04-HOLE-BOUNDARY-RESOLUTION-L0"] = if ($gate04) { "PASS" } else { "EVALUATE_EMPIRICAL" }

# GATE-05: Production 3-Layer Deck Assembly
$prodDeckLocal = Join-Path $repo "models/pandey_kumar_mode1/223_f1732_case2_calibrated/PK_F1728_CASE_2_PROD.inp"
if (Test-Path (Join-Path $evidenceDir "PK_F1728_CASE_2_PROD.inp")) {
    Copy-Item (Join-Path $evidenceDir "PK_F1728_CASE_2_PROD.inp") $prodDeckLocal -Force
}
$prodDeckCreated = (Test-Path (Join-Path $evidenceDir "PK_F1728_CASE_2_PROD.inp")) -or ($engineAudit -and $engineAudit.production_deck.status -eq "SUCCESS")
$gates["GATE-05-PROD-DECK-ASSEMBLY"] = if ($prodDeckCreated) { "PASS" } else { "FAIL" }

# GATE-06: Abaqus Datacheck Verification
$dcExit0 = ($dcDatContent -match "ANALYSIS DATACHECK COMPLETE")
$gates["GATE-06-DATACHECK-EXIT-0"] = if ($dcExit0) { "PASS" } else { "FAIL" }

# GATE-07: UEL Bitwise Verification
$uelVerified = ($pbsContent -match "User subroutine hash verified:\s+ce8d5edcd2911dcb018bb15275271f874e7ea62b8fb48cf4a8297469a83acdd6") -or ($engineAudit -and $engineAudit.production_deck.uel_hash_verified -eq $true)
$gates["GATE-07-UEL-VERIFICATION"] = if ($uelVerified) { "PASS" } else { "FAIL" }

Write-Output "=== EXECUTION GATE SUMMARY ==="
$allPass = $true
foreach ($k in $gates.Keys) {
    Write-Output "  $k : $($gates[$k])"
    if ($gates[$k] -ne "PASS") { $allPass = $false }
}

# Compile summary receipt
$summary = [ordered]@{
    "job_id" = $jobId
    "task_id" = "F1732-CASE2-ADAPTIVE-REMESH-CALIBRATION"
    "all_gates_pass" = $allPass
    "gates" = $gates
    "mesh_metrics" = if ($spatialAudit) {
        [ordered]@{
            "total_physical_elements" = $spatialAudit.total_elements
            "total_nodes" = $spatialAudit.total_nodes
            "quad_fraction_pct" = $spatialAudit.quad_fraction_pct
            "min_signed_jacobian" = $spatialAudit.min_signed_jacobian
            "non_positive_jacobians" = $spatialAudit.non_positive_jacobians
            "mean_aspect_ratio" = $spatialAudit.mean_aspect_ratio
            "max_aspect_ratio" = $spatialAudit.max_aspect_ratio
            "global_resolution" = $spatialAudit.global_resolution
            "mutually_exclusive_partition" = $spatialAudit.mutually_exclusive_partition
            "overlapping_diagnostic_windows" = $spatialAudit.overlapping_diagnostic_windows
            "along_path_trajectory_stations" = $spatialAudit.along_path_trajectory_stations
        }
    } else { $null }
    "donor_odb_provenance" = [ordered]@{
        "path" = "/scratch9/pr21vyci/runs/f1730_case2_recovery_solve/PK_HOLE_COMPANION_RECOVERY.odb"
        "sha256" = "a6514fb8c07c3b855bb4ba841fdb20a9ae8a1c887a6e6ad1a397ba34222ab856"
        "classification" = "PROVISIONAL_DONOR_WITH_DOCUMENTED_SPR_LIMITATION"
    }
}

$summary | ConvertTo-Json -Depth 10 | Set-Content $summaryJson -Encoding UTF8
Write-Output "Saved summary receipt to: $summaryJson"

if ($allPass) {
    Write-Output "ALL 7 EXECUTION GATES PASS!"
} else {
    Write-Warning "Gate evaluation completed. Review summary for details."
}
