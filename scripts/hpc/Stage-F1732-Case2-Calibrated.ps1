# -*- coding: utf-8 -*-
# scripts/hpc/Stage-F1732-Case2-Calibrated.ps1
# Staging and Hash Verification for Task F1732 Case 2 Mode-I Calibrated Adaptive Remeshing Experiment

$ErrorActionPreference = 'Stop'
$repo = 'D:\Master thesis\Adaptive remeshing'
$cfg = "$env:USERPROFILE\.ssh\codex_config"
$remoteDir = "/scratch9/pr21vyci/runs/f1732_case2_calibrated"
$pkgDir = Join-Path $repo 'models/pandey_kumar_mode1/223_f1732_case2_calibrated'

function Upload-File($local, $remote) {
    & scp -F $cfg -B -o BatchMode=yes $local "tu_freiberg:$remote"
    if ($LASTEXITCODE -ne 0) { throw "SCP failed for $local to $remote" }
}

function Invoke-Remote($cmd) {
    & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $repo '.agents/scripts/Invoke-GuardedSsh.ps1') -RemoteCommand $cmd
}

Write-Output "=== TASK F1732: STAGING CASE 2 CALIBRATED EXPERIMENT ON CLUSTER ==="
Write-Output "Target directory: $remoteDir"
Invoke-Remote "mkdir -p $remoteDir && chmod 755 $remoteDir"

$files = @(
    "f1732_case2_off_axis_hole.json",
    "f42_mixed_uel.for",
    "reusable_2d_adaptive_framework.py",
    "audit_case2_calibrated_resolution.py",
    "job_notifications.sh",
    "submit_f1732_case2_calibrated.pbs"
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
$remoteSha = Invoke-Remote "cd $remoteDir && sha256sum f1732_case2_off_axis_hole.json f42_mixed_uel.for reusable_2d_adaptive_framework.py audit_case2_calibrated_resolution.py submit_f1732_case2_calibrated.pbs job_notifications.sh"
Write-Output $remoteSha

Write-Output "Checking donor ODB existence..."
$donorCheck = Invoke-Remote "ls -lh /scratch9/pr21vyci/runs/f1730_case2_recovery_solve/PK_HOLE_COMPANION_RECOVERY.odb"
Write-Output $donorCheck

Write-Output "=== STAGING CASE 2 CALIBRATED EXPERIMENT COMPLETE ==="
