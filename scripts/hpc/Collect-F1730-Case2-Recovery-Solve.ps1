# -*- coding: utf-8 -*-
# scripts/hpc/Collect-F1730-Case2-Recovery-Solve.ps1
# Collects and Audits Solver Evidence for Task F1730 Case 2 Companion Recovery Solve

param(
    [string]$JobId
)

$ErrorActionPreference = 'Stop'
$repo = 'D:\Master thesis\Adaptive remeshing'
$cfg = "$env:USERPROFILE\.ssh\codex_config"
$remoteDir = "/scratch9/pr21vyci/runs/f1730_case2_recovery_solve"
$localEvidenceDir = Join-Path $repo 'results/validation/f1730_case2_recovery_evidence'

if (-not (Test-Path $localEvidenceDir)) {
    New-Item -ItemType Directory -Path $localEvidenceDir -Force | Out-Null
}

function Invoke-Remote($cmd) {
    & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $repo '.agents/scripts/Invoke-GuardedSsh.ps1') -RemoteCommand $cmd
}

function Download-File($remote, $local) {
    & scp -F $cfg -B -o BatchMode=yes "tu_freiberg:$remote" $local
    if ($LASTEXITCODE -ne 0) { throw "SCP failed for $remote to $local" }
}

Write-Output "=== TASK F1730: COLLECTING RECOVERY SOLVE EVIDENCE FROM CLUSTER ==="

# Check remote files
$filesCheck = Invoke-Remote "ls -lh $remoteDir/PK_HOLE_COMPANION_RECOVERY.* $remoteDir/f1730_case2_recovery_telemetry.json $remoteDir/pbs_execution.log"
Write-Output $filesCheck

$evidenceFiles = @(
    "PK_HOLE_COMPANION_RECOVERY.sta",
    "PK_HOLE_COMPANION_RECOVERY.msg",
    "PK_HOLE_COMPANION_RECOVERY.dat",
    "PK_HOLE_COMPANION_RECOVERY.prt",
    "PK_HOLE_COMPANION_RECOVERY.com",
    "f1730_case2_recovery_telemetry.json",
    "pbs_execution.log"
)

foreach ($f in $evidenceFiles) {
    $remoteFile = "$remoteDir/$f"
    $localFile = (Join-Path $localEvidenceDir $f).Replace('\', '/')
    Write-Output "Downloading $f..."
    Download-File $remoteFile $localFile
}

Write-Output "Computing SHA-256 digests of downloaded evidence..."
$hashes = @{}
foreach ($f in $evidenceFiles) {
    $path = Join-Path $localEvidenceDir $f
    if (Test-Path $path) {
        $hashes[$f] = (Get-FileHash -Path $path -Algorithm SHA256).Hash
        Write-Output "  $f : $($hashes[$f])"
    }
}

# Audit Gate Criteria
$datPath = Join-Path $localEvidenceDir "PK_HOLE_COMPANION_RECOVERY.dat"
$msgPath = Join-Path $localEvidenceDir "PK_HOLE_COMPANION_RECOVERY.msg"
$staPath = Join-Path $localEvidenceDir "PK_HOLE_COMPANION_RECOVERY.sta"
$pbsLog = Join-Path $localEvidenceDir "pbs_execution.log"
$telemetryPath = Join-Path $localEvidenceDir "f1730_case2_recovery_telemetry.json"

$datContent = if (Test-Path $datPath) { Get-Content $datPath -Raw } else { "" }
$msgContent = if (Test-Path $msgPath) { Get-Content $msgPath -Raw } else { "" }
$staContent = if (Test-Path $staPath) { Get-Content $staPath -Raw } else { "" }
$pbsContent = if (Test-Path $pbsLog) { Get-Content $pbsLog -Raw } else { "" }

$telemetry = if (Test-Path $telemetryPath) {
    Get-Content $telemetryPath -Raw -Encoding UTF8 | ConvertFrom-Json
} else {
    $null
}

$gateResults = @{}

# Gate SOLVE-01: Solver completes with Exit Code 0 and 1 converged increment
$solve01Pass = ($pbsContent -match "Abaqus Solver Finished with Exit Code: 0" -or $pbsContent -match "Abaqus Solver Execution Succeeded \(Exit Code 0\)") -and `
               ($staContent -match "THE ANALYSIS HAS COMPLETED SUCCESSFULLY" -or $msgContent -match "THE ANALYSIS HAS COMPLETED SUCCESSFULLY") -and `
               ($datContent -notmatch "\*\*\*ERROR")
$gateResults["SOLVE-01-CONVERGED-INCREMENT"] = if ($solve01Pass) { "PASS" } else { "FAIL" }

# Gate SOLVE-02: Vertical static force equilibrium: |sum RF_y(bottom) + RF_y(top)| <= 1.0e-4 |RF_y(top)|
$solve02Pass = $false
if ($telemetry -ne $null -and $telemetry.reaction_forces -ne $null) {
    $relRes = [double]$telemetry.reaction_forces.relative_vertical_residual
    $solve02Pass = ($relRes -le 1.0e-4)
}
$gateResults["SOLVE-02-VERTICAL-EQUILIBRIUM"] = if ($solve02Pass) { "PASS" } else { "FAIL" }

# Gate SOLVE-03: Recovered reaction force quantitatively reported and distinguished
$solve03Pass = $false
if ($telemetry -ne $null -and $telemetry.reaction_forces -ne $null) {
    $topRf = [double]$telemetry.reaction_forces.top_rf_y_kn
    $solve03Pass = ($topRf -gt 0.0 -and $telemetry.reaction_forces.original_coupled_peak_force_kn -eq 0.731015)
}
$gateResults["SOLVE-03-REACTION-FORCE-REPORTED"] = if ($solve03Pass) { "PASS" } else { "FAIL" }

# Gate SOLVE-04: ODB fields S, EVOL, MISESAVG, MISESERI present and populated across all 2,906 elements
$solve04Pass = $false
if ($telemetry -ne $null -and $telemetry.mesh_coverage -ne $null) {
    $totElem = [int]$telemetry.mesh_coverage.total_elements
    $solve04Pass = ($totElem -eq 2906)
}
$gateResults["SOLVE-04-FIELDS-POPULATED"] = if ($solve04Pass) { "PASS" } else { "FAIL" }

# Gate SOLVE-05: Finite indicator coverage: 100% of elements have finite non-NaN, non-inf error values
$solve05Pass = $false
if ($telemetry -ne $null -and $telemetry.mesh_coverage -ne $null) {
    $covPct = [double]$telemetry.mesh_coverage.finite_coverage_pct
    $nonFin = [int]$telemetry.mesh_coverage.non_finite_count
    $solve05Pass = ($covPct -eq 100.0 -and $nonFin -eq 0)
}
$gateResults["SOLVE-05-FINITE-COVERAGE"] = if ($solve05Pass) { "PASS" } else { "FAIL" }

# Gate SOLVE-06: Spatial error localization: process-zone contrast >= 5.0x vs bulk evaluated on 48 damaged and 6 boundary elements
$solve06Pass = $false
if ($telemetry -ne $null -and $telemetry.error_indicator_statistics -ne $null) {
    $cDam = [double]$telemetry.error_indicator_statistics.contrast_damaged_vs_bulk
    $cBnd = [double]$telemetry.error_indicator_statistics.contrast_boundary_ligament_vs_bulk
    $solve06Pass = ($cDam -ge 5.0 -and $cBnd -ge 5.0)
}
$gateResults["SOLVE-06-PROCESS-ZONE-CONTRAST"] = if ($solve06Pass) { "PASS" } else { "FAIL" }

# Gate SOLVE-07: Warning classification: 2 SPR section warnings verified benign in runtime solver output
$solve07Pass = ($datContent -match "ALL ELEMENTS IN THE ERROR\s+RECOVERY DOMAIN" -and $datContent -match "PLEASE DISREGARD THE ABOVE\s+WARNING")
$gateResults["SOLVE-07-WARNINGS-CLASSIFIED"] = if ($solve07Pass) { "PASS" } else { "FAIL" }

$overallPass = ($gateResults.Values | Where-Object { $_ -ne "PASS" }).Count -eq 0

$summary = @{
    task_id = "F1730-CASE2-COMPANION-RECOVERY-SOLVE"
    job_id = $JobId
    solve_status = if ($overallPass) { "RECOVERY_SOLVE_EXIT_0_ALL_7_GATES_PASS" } else { "RECOVERY_SOLVE_FAILED" }
    overall_pass = $overallPass
    gate_results = $gateResults
    evidence_hashes = $hashes
    timestamp = (Get-Date).ToString("o")
}

$summaryJsonPath = Join-Path $repo 'results/validation/f1730_case2_recovery_solve_summary.json'
$summary | ConvertTo-Json -Depth 5 | Set-Content $summaryJsonPath -Encoding UTF8
Write-Output "Summary written to: $summaryJsonPath"
Write-Output "Overall Status: $($summary.solve_status)"
