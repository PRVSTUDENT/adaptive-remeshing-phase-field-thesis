# -*- coding: utf-8 -*-
# scripts/hpc/Stage-And-Datacheck-F1709.ps1
# Staging and Cluster Abaqus 2023 Datacheck for Section 4.3 Job-2 (Staggered UEL Formulation)

$ErrorActionPreference = 'Stop'
$repo = 'D:\Master thesis\Adaptive remeshing'
$cfg = "$env:USERPROFILE\.ssh\codex_config"
$remoteDir = "/scratch9/pr21vyci/runs/mode1_pk_sec43_job2_staggered_f1709"
$pkgDir = Join-Path $repo 'models/pandey_kumar_mode1/205_pk_sec43_job2_staggered'

function Upload-File($local, $remote) {
    & scp -F $cfg -B -o BatchMode=yes $local "tu_freiberg:$remote"
    if ($LASTEXITCODE -ne 0) { throw "SCP failed for $local to $remote" }
}

function Download-File($remote, $local) {
    & scp -F $cfg -B -o BatchMode=yes "tu_freiberg:$remote" $local
    if ($LASTEXITCODE -ne 0) { throw "SCP download failed for $remote to $local" }
}

function Invoke-Remote($cmd) {
    & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $repo '.agents/scripts/Invoke-GuardedSsh.ps1') -RemoteCommand $cmd
}

Write-Output "=== TASK F1709: STAGING AND CLUSTER DATACHECK ==="
Write-Output "Creating remote directory: $remoteDir"
Invoke-Remote "mkdir -p $remoteDir"

$files = @(
    "PK_SEC43_JOB2_ADAPTED_PROD.inp",
    "f42_staggered_variant_uel.for",
    "f42_mixed_uel.for",
    "submit_M1_PK_SEC43_JOB2_STAGGERED.pbs",
    "job_notifications.sh",
    "run_cluster_datacheck.sh"
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
$remoteSha = Invoke-Remote "sha256sum $remoteDir/PK_SEC43_JOB2_ADAPTED_PROD.inp $remoteDir/f42_staggered_variant_uel.for $remoteDir/submit_M1_PK_SEC43_JOB2_STAGGERED.pbs"
Write-Output $remoteSha

Write-Output "Running remote Abaqus 2023 datacheck script on login node..."
$dcOut = Invoke-Remote "bash $remoteDir/run_cluster_datacheck.sh"
Write-Output $dcOut

Write-Output "Downloading datacheck .dat and .msg artifacts..."
Download-File "$remoteDir/M1_PK_SEC43_JOB2_STAGGERED_DATACHECK.dat" (Join-Path $pkgDir "M1_PK_SEC43_JOB2_STAGGERED_DATACHECK.dat")
Download-File "$remoteDir/M1_PK_SEC43_JOB2_STAGGERED_DATACHECK.msg" (Join-Path $pkgDir "M1_PK_SEC43_JOB2_STAGGERED_DATACHECK.msg")

Write-Output "=== STAGING AND CLUSTER DATACHECK COMPLETE ==="
