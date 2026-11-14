# -*- coding: utf-8 -*-
# scripts/hpc/Run-F1735-Case2-Odb-Audit.ps1
# Stages extract_f1735_case2_odb_sdv.py to cluster scratch, executes via abaqus python,
# and retrieves f1735_case2_final_frame_sdv.csv and f1735_case2_odb_summary.json locally.

$ErrorActionPreference = 'Stop'
$repo = 'D:\Master thesis\Adaptive remeshing'
$cfg = "$env:USERPROFILE\.ssh\codex_config"
$remoteDir = "/scratch9/pr21vyci/runs/f1735_case2_adapted_fracture"
$localScript = (Join-Path $repo "scripts/remeshing/extract_f1735_case2_odb_sdv.py").Replace('\', '/')
$localSh = (Join-Path $repo "scripts/remeshing/run_f1735_odb_audit.sh").Replace('\', '/')
$localCsv = (Join-Path $repo "results/validation/f1735_case2_final_frame_sdv.csv").Replace('\', '/')
$localJson = (Join-Path $repo "results/validation/f1735_case2_odb_summary.json").Replace('\', '/')

function Upload-File($local, $remote) {
    & scp -F $cfg -B -o BatchMode=yes $local "tu_freiberg:$remote"
    if ($LASTEXITCODE -ne 0) { throw "SCP failed for $local to $remote" }
}

function Download-File($remote, $local) {
    & scp -F $cfg -B -o BatchMode=yes "tu_freiberg:$remote" $local
    if ($LASTEXITCODE -ne 0) { throw "SCP failed for $remote to $local" }
}

function Invoke-Remote($cmd, $timeout=300) {
    & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $repo '.agents/scripts/Invoke-GuardedSsh.ps1') -RemoteCommand $cmd -TimeoutSeconds $timeout
}

Write-Host "1. Uploading extraction script and shell wrapper to cluster..."
Upload-File $localScript "$remoteDir/extract_f1735_case2_odb_sdv.py"
Upload-File $localSh "$remoteDir/run_f1735_odb_audit.sh"

Write-Host "2. Setting remote permissions..."
Invoke-Remote "chmod 755 $remoteDir/run_f1735_odb_audit.sh"

Write-Host "3. Executing ODB extraction via abaqus python on cluster..."
Invoke-Remote "bash $remoteDir/run_f1735_odb_audit.sh" 300

Write-Host "4. Downloading results..."
Download-File "$remoteDir/f1735_case2_final_frame_sdv.csv" $localCsv
Download-File "$remoteDir/f1735_case2_odb_summary.json" $localJson

if ((Test-Path $localCsv) -and (Test-Path $localJson)) {
    Write-Host "Successfully downloaded CSV ($((Get-Item $localCsv).Length) bytes) and JSON ($((Get-Item $localJson).Length) bytes)"
} else {
    throw "Failed to download output artifacts"
}
