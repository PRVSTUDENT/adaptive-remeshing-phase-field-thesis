# -*- coding: utf-8 -*-
# scripts/hpc/Stage-F1735-Case2-Adapted-Fracture.ps1
# Staging and Hash Verification for Task F1735 Case 2 Adapted-Mesh Mode-I Phase-Field Fracture Simulation

$ErrorActionPreference = 'Stop'
$repo = 'D:\Master thesis\Adaptive remeshing'
$cfg = "$env:USERPROFILE\.ssh\codex_config"
$remoteDir = "/scratch9/pr21vyci/runs/f1735_case2_adapted_fracture"
$pkgDir = Join-Path $repo 'models/pandey_kumar_mode1/225_f1735_case2_adapted_fracture'

function Upload-File($local, $remote) {
    & scp -F $cfg -B -o BatchMode=yes $local "tu_freiberg:$remote"
    if ($LASTEXITCODE -ne 0) { throw "SCP failed for $local to $remote" }
}

function Invoke-Remote($cmd) {
    & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $repo '.agents/scripts/Invoke-GuardedSsh.ps1') -RemoteCommand $cmd
}

Write-Output "=== TASK F1735: STAGING CASE 2 ADAPTED FRACTURE SIMULATION ON CLUSTER ==="
Write-Output "Target directory: $remoteDir"
Invoke-Remote "mkdir -p $remoteDir && chmod 755 $remoteDir"

$files = @(
    "PK_F1728_CASE_2_PROD.inp",
    "f42_mixed_uel.for",
    "f1735_case2_fracture_execution.json",
    "job_notifications.sh",
    "submit_f1735_case2_adapted_fracture.pbs"
)

foreach ($f in $files) {
    $local = (Join-Path $pkgDir $f).Replace('\', '/')
    $remote = "$remoteDir/$f"
    Write-Output "Uploading $f via SCP..."
    Upload-File $local $remote
}

Write-Output "Setting remote permissions..."
Invoke-Remote "chmod 755 $remoteDir/*.sh $remoteDir/*.pbs"

Write-Output "Verifying remote SHA-256 hashes..."
$remoteSha = Invoke-Remote "sha256sum $remoteDir/PK_F1728_CASE_2_PROD.inp $remoteDir/f42_mixed_uel.for $remoteDir/submit_f1735_case2_adapted_fracture.pbs"
Write-Output $remoteSha

Write-Output "=== STAGING CASE 2 ADAPTED FRACTURE SIMULATION COMPLETE ==="
