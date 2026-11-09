# -*- coding: utf-8 -*-
# scripts/hpc/Stage-And-Datacheck-F1705.ps1
# Staging and Cluster Abaqus 2023 Datacheck for Candidate E10 (Task F1705)

$ErrorActionPreference = 'Stop'
$repo = 'D:\Master thesis\Adaptive remeshing'
$cfg = "$env:USERPROFILE\.ssh\codex_config"
$remoteDir = "/scratch9/pr21vyci/runs/mode1_method_a_hole_f1705_prod"
$pkgDir = Join-Path $repo 'models/pandey_kumar_mode1/177_method_a_hole_e10_prod'

function Upload-File($local, $remote) {
    & scp -F $cfg -B -o BatchMode=yes $local "tu_freiberg:$remote"
    if ($LASTEXITCODE -ne 0) { throw "SCP failed for $local to $remote" }
}

function Invoke-Remote($cmd) {
    & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $repo '.agents/scripts/Invoke-GuardedSsh.ps1') -RemoteCommand $cmd
}

Write-Output "=== TASK F1705: STAGING AND CLUSTER DATACHECK ==="
Write-Output "Creating remote directory: $remoteDir"
Invoke-Remote "mkdir -p $remoteDir"

$files = @(
    "PK_HOLE_SEL_E10_PROD.inp",
    "f42_mixed_uel.for",
    "submit_M1_HOLE_SEL_E10_PROD.pbs",
    "job_notifications.sh",
    "run_e10_cluster_datacheck.sh"
)

foreach ($f in $files) {
    $local = (Join-Path $pkgDir $f).Replace('\', '/')
    $remote = "$remoteDir/$f"
    Write-Output "Uploading $f via SCP..."
    Upload-File $local $remote
}

Write-Output "Setting executable permissions..."
Invoke-Remote "chmod 755 $remoteDir/*.sh $remoteDir/*.pbs"

Write-Output "Verifying remote SHA-256 hashes..."
$remoteSha = Invoke-Remote "sha256sum $remoteDir/PK_HOLE_SEL_E10_PROD.inp $remoteDir/f42_mixed_uel.for $remoteDir/submit_M1_HOLE_SEL_E10_PROD.pbs"
Write-Output $remoteSha

Write-Output "Running remote Abaqus 2023 datacheck script on login node..."
$dcOut = Invoke-Remote "bash $remoteDir/run_e10_cluster_datacheck.sh"
Write-Output $dcOut
Write-Output "=== STAGING AND CLUSTER DATACHECK COMPLETE ==="
