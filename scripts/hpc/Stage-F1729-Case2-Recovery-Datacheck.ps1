# -*- coding: utf-8 -*-
# scripts/hpc/Stage-F1729-Case2-Recovery-Datacheck.ps1
# Staging and Hash Verification for Task F1729 Case 2 Companion Recovery Abaqus Datacheck

$ErrorActionPreference = 'Stop'
$repo = 'D:\Master thesis\Adaptive remeshing'
$cfg = "$env:USERPROFILE\.ssh\codex_config"
$remoteDir = "/scratch9/pr21vyci/runs/f1729_case2_recovery_datacheck"
$pkgDir = Join-Path $repo 'models/pandey_kumar_mode1/220_f1729_case2_recovery_datacheck'

function Upload-File($local, $remote) {
    & scp -F $cfg -B -o BatchMode=yes $local "tu_freiberg:$remote"
    if ($LASTEXITCODE -ne 0) { throw "SCP failed for $local to $remote" }
}

function Invoke-Remote($cmd) {
    & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $repo '.agents/scripts/Invoke-GuardedSsh.ps1') -RemoteCommand $cmd
}

Write-Output "=== TASK F1729: STAGING CASE 2 COMPANION RECOVERY DATACHECK ON CLUSTER ==="
Write-Output "Target directory: $remoteDir"
Invoke-Remote "mkdir -p $remoteDir && chmod 755 $remoteDir"

$files = @(
    "PK_HOLE_COMPANION_RECOVERY.inp",
    "submit_f1729_case2_recovery_datacheck.pbs",
    "job_notifications.sh"
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
$remoteSha = Invoke-Remote "cd $remoteDir && sha256sum PK_HOLE_COMPANION_RECOVERY.inp submit_f1729_case2_recovery_datacheck.pbs job_notifications.sh"
Write-Output $remoteSha

Write-Output "=== STAGING CASE 2 COMPANION RECOVERY DATACHECK COMPLETE ==="
