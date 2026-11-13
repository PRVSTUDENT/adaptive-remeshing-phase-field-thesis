# -*- coding: utf-8 -*-
# scripts/hpc/Stage-F1728-Case1-Pilot.ps1
# Staging and Hash Verification for Task F1728 Case 1 Mode-I Adaptive Remeshing Pilot

$ErrorActionPreference = 'Stop'
$repo = 'D:\Master thesis\Adaptive remeshing'
$cfg = "$env:USERPROFILE\.ssh\codex_config"
$remoteDir = "/scratch9/pr21vyci/runs/f1728_case1_pilot"
$pkgDir = Join-Path $repo 'models/pandey_kumar_mode1/219_f1728_five_geometry_study'

function Upload-File($local, $remote) {
    & scp -F $cfg -B -o BatchMode=yes $local "tu_freiberg:$remote"
    if ($LASTEXITCODE -ne 0) { throw "SCP failed for $local to $remote" }
}

function Invoke-Remote($cmd) {
    & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $repo '.agents/scripts/Invoke-GuardedSsh.ps1') -RemoteCommand $cmd
}

Write-Output "=== TASK F1728: STAGING CASE 1 PILOT ON CLUSTER ==="
Write-Output "Target directory: $remoteDir"
Invoke-Remote "mkdir -p $remoteDir && chmod 755 $remoteDir"

$files = @(
    "f1728_case1_mode1_edge_crack.json",
    "f42_mixed_uel.for",
    "reusable_2d_adaptive_framework.py",
    "job_notifications.sh",
    "submit_f1728_case1_pilot.pbs",
    "preflight_f1728_case1.sh"
)

foreach ($f in $files) {
    $local = (Join-Path $pkgDir $f).Replace('\', '/')
    $remote = "$remoteDir/$f"
    Write-Output "Uploading $f via SCP..."
    Upload-File $local $remote
}

Write-Output "Setting remote permissions..."
Invoke-Remote "chmod 755 $remoteDir/*.sh $remoteDir/*.pbs $remoteDir/*.py"

Write-Output "Verifying remote SHA-256 hashes..."
$remoteSha = Invoke-Remote "cd $remoteDir && sha256sum f1728_case1_mode1_edge_crack.json f42_mixed_uel.for reusable_2d_adaptive_framework.py submit_f1728_case1_pilot.pbs job_notifications.sh"
Write-Output $remoteSha

Write-Output "Checking donor ODB existence..."
$donorCheck = Invoke-Remote "ls -lh /scratch9/pr21vyci/runs/mode1_package46_coarse_fine_preanalysis/PK_M1_COARSE_FINE_CONT.odb"
Write-Output $donorCheck

Write-Output "=== STAGING CASE 1 PILOT COMPLETE ==="
