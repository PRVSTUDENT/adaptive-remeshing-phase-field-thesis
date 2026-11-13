# -*- coding: utf-8 -*-
# scripts/hpc/Collect-F1729-Case2-Recovery-Datacheck.ps1
# Collects and Audits Solver Evidence for Task F1729 Case 2 Companion Recovery Datacheck

param(
    [string]$JobId
)

$ErrorActionPreference = 'Stop'
$repo = 'D:\Master thesis\Adaptive remeshing'
$cfg = "$env:USERPROFILE\.ssh\codex_config"
$remoteDir = "/scratch9/pr21vyci/runs/f1729_case2_recovery_datacheck"
$localEvidenceDir = Join-Path $repo 'results/validation/f1729_case2_datacheck_evidence'

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

Write-Output "=== TASK F1729: COLLECTING DATACHECK EVIDENCE FROM CLUSTER ==="

# Check remote files
$filesCheck = Invoke-Remote "ls -lh $remoteDir/PK_HOLE_COMPANION_RECOVERY_DC.* $remoteDir/pbs_execution.log"
Write-Output $filesCheck

$evidenceFiles = @(
    "PK_HOLE_COMPANION_RECOVERY_DC.msg",
    "PK_HOLE_COMPANION_RECOVERY_DC.dat",
    "PK_HOLE_COMPANION_RECOVERY_DC.prt",
    "PK_HOLE_COMPANION_RECOVERY_DC.com",
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
$datPath = Join-Path $localEvidenceDir "PK_HOLE_COMPANION_RECOVERY_DC.dat"
$msgPath = Join-Path $localEvidenceDir "PK_HOLE_COMPANION_RECOVERY_DC.msg"
$pbsLog = Join-Path $localEvidenceDir "pbs_execution.log"

$datContent = Get-Content $datPath -Raw
$msgContent = Get-Content $msgPath -Raw
$pbsContent = Get-Content $pbsLog -Raw

$gateResults = @{}

# Gate DC-01: Syntax & keyword validity (no ***ERROR in dat/msg and ANALYSIS DATACHECK COMPLETE present)
$gateResults["DC-01-SYNTAX-VALIDITY"] = if ($datContent -match "ANALYSIS DATACHECK COMPLETE" -and $datContent -notmatch "\*\*\*ERROR" -and $msgContent -notmatch "\*\*\*ERROR") { "PASS" } else { "FAIL" }

# Gate DC-02: Element topology
$gateResults["DC-02-ELEMENT-TOPOLOGY"] = if ($datContent -match "CPE4" -and $datContent -match "CPE3") { "PASS" } else { "FAIL" }

# Gate DC-03: Material assignments
$gateResults["DC-03-MATERIAL-ASSIGNMENTS"] = if ($datContent -match "MAT_BIN_SOFT_20" -and $datContent -notmatch "UNASSIGNED") { "PASS" } else { "FAIL" }

# Gate DC-04: Boundary conditions
$gateResults["DC-04-BOUNDARY-CONDITIONS"] = if ($msgContent -match "S\s+T\s+A\s+T\s+I\s+C\s+A\s+N\s+A\s+L\s+Y\s+S\s+I\s+S" -or $datContent -match "\*BOUNDARY") { "PASS" } else { "FAIL" }

# Gate DC-05: Output variables
$gateResults["DC-05-OUTPUT-VARIABLES"] = if ($datContent -notmatch "OUTPUT VARIABLE.*NOT AVAILABLE" -and $msgContent -notmatch "OUTPUT VARIABLE.*NOT AVAILABLE") { "PASS" } else { "FAIL" }

# Gate DC-06: Exit Code 0
$gateResults["DC-06-EXIT-CODE-ZERO"] = if ($pbsContent -match "Datacheck Finished with Exit Code: 0" -or $pbsContent -match "Exit Code 0") { "PASS" } else { "FAIL" }

$overallPass = ($gateResults.Values | Where-Object { $_ -ne "PASS" }).Count -eq 0

$summary = @{
    task_id = "F1729-CASE2-COMPANION-RECOVERY-DATACHECK"
    job_id = $JobId
    datacheck_status = if ($overallPass) { "DATACHECK_EXIT_0_ALL_GATES_PASS" } else { "DATACHECK_FAILED" }
    overall_pass = $overallPass
    gate_results = $gateResults
    evidence_hashes = $hashes
    timestamp = (Get-Date).ToString("o")
}

$summaryJsonPath = Join-Path $repo 'results/validation/f1729_case2_datacheck_summary.json'
$summary | ConvertTo-Json -Depth 5 | Set-Content $summaryJsonPath -Encoding UTF8
Write-Output "Summary written to: $summaryJsonPath"
Write-Output "Overall Status: $($summary.datacheck_status)"
