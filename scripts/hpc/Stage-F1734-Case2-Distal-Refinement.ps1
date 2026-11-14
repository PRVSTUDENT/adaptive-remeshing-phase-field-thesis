# -*- coding: utf-8 -*-
# scripts/hpc/Stage-F1734-Case2-Distal-Refinement.ps1
# Staging and Hash Verification for Task F1734 Case 2 Mode-I Controlled Distal Refinement Experiment (eta = 2.30%)

$ErrorActionPreference = 'Stop'
$repo = 'D:\Master thesis\Adaptive remeshing'
$cfg = "$env:USERPROFILE\.ssh\codex_config"
$remoteDir = "/scratch9/pr21vyci/runs/f1734_case2_distal_refinement"
$pkgDir = Join-Path $repo 'models/pandey_kumar_mode1/224_f1734_case2_distal_refinement'

function Upload-File($local, $remote) {
    & scp -F $cfg -B -o BatchMode=yes $local "tu_freiberg:$remote"
    if ($LASTEXITCODE -ne 0) { throw "SCP failed for $local to $remote" }
}

function Invoke-Remote($cmd) {
    & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $repo '.agents/scripts/Invoke-GuardedSsh.ps1') -RemoteCommand $cmd
}

Write-Output "=== TASK F1734: STAGING CASE 2 DISTAL REFINEMENT EXPERIMENT ON CLUSTER ==="
Write-Output "Target directory: $remoteDir"
Invoke-Remote "mkdir -p $remoteDir && chmod 755 $remoteDir"

$files = @(
    "f1734_case2_off_axis_hole.json",
    "f42_mixed_uel.for",
    "reusable_2d_adaptive_framework.py",
    "audit_case2_distal_refinement_resolution.py",
    "job_notifications.sh",
    "submit_f1734_case2_distal_refinement.pbs"
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
$remoteSha = Invoke-Remote "sha256sum $remoteDir/f1734_case2_off_axis_hole.json $remoteDir/f42_mixed_uel.for $remoteDir/reusable_2d_adaptive_framework.py $remoteDir/audit_case2_distal_refinement_resolution.py $remoteDir/submit_f1734_case2_distal_refinement.pbs $remoteDir/job_notifications.sh"
Write-Output $remoteSha

Write-Output "Checking donor ODB existence..."
$donorCheck = Invoke-Remote "ls -lh /scratch9/pr21vyci/runs/f1730_case2_recovery_solve/PK_HOLE_COMPANION_RECOVERY.odb"
Write-Output $donorCheck

Write-Output "=== STAGING CASE 2 DISTAL REFINEMENT EXPERIMENT COMPLETE ==="
