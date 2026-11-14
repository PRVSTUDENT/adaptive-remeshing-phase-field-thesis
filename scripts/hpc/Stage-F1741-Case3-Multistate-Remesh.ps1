# -*- coding: utf-8 -*-
# scripts/hpc/Stage-F1741-Case3-Multistate-Remesh.ps1
# Staging and Hash Verification for Task F1741 Case 3 Controlled Multi-State Native Remeshing Experiment

$ErrorActionPreference = 'Stop'
$repo = 'D:\Master thesis\Adaptive remeshing'
$cfg = "$env:USERPROFILE\.ssh\codex_config"
$remoteDir = "/scratch9/pr21vyci/runs/mode1_pk_f1741_case3_remesh"
$pkgDir = Join-Path $repo 'models/pandey_kumar_mode1/228_f1741_case3_multistate_remesh'
$donorDir = Join-Path $repo 'models/pandey_kumar_mode1/200_pk_sec43_prescribed_same_state'

function Upload-File($local, $remote) {
    & scp -F $cfg -B -o BatchMode=yes $local "tu_freiberg:$remote"
    if ($LASTEXITCODE -ne 0) { throw "SCP failed for $local to $remote" }
}

function Invoke-Remote($cmd) {
    & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $repo '.agents/scripts/Invoke-GuardedSsh.ps1') -RemoteCommand $cmd
}

Write-Output "=== TASK F1741: STAGING CASE 3 MULTI-STATE REMESHING EXPERIMENT ON CLUSTER ==="
Write-Output "Target directory: $remoteDir"
Invoke-Remote "mkdir -p $remoteDir && chmod 755 $remoteDir"

$files = @(
    "f1741_case3_multistate_remesh.json",
    "f42_mixed_uel.for",
    "run_case3_multistate_remesh.py",
    "audit_case3_multistate_resolution.py",
    "job_notifications.sh",
    "submit_f1741_case3_multistate_remesh.pbs"
)

foreach ($f in $files) {
    $local = (Join-Path $pkgDir $f).Replace('\', '/')
    $remote = "$remoteDir/$f"
    Write-Output "Uploading $f via SCP..."
    Upload-File $local $remote
}

# Upload authentic solver donor ODBs
$donorFiles = @(
    "PK_SEC43_PRESCRIBED_STATE2.odb",
    "PK_SEC43_PRESCRIBED_STATE4.odb"
)

foreach ($df in $donorFiles) {
    $local = (Join-Path $donorDir $df).Replace('\', '/')
    $remote = "$remoteDir/$df"
    Write-Output "Uploading donor ODB $df via SCP..."
    Upload-File $local $remote
}

Write-Output "Setting remote permissions..."
Invoke-Remote "chmod 755 $remoteDir/*.sh $remoteDir/*.pbs $remoteDir/*.py"

Write-Output "Verifying remote SHA-256 hashes..."
$remoteSha = Invoke-Remote "sha256sum $remoteDir/f1741_case3_multistate_remesh.json $remoteDir/f42_mixed_uel.for $remoteDir/run_case3_multistate_remesh.py $remoteDir/audit_case3_multistate_resolution.py $remoteDir/submit_f1741_case3_multistate_remesh.pbs $remoteDir/job_notifications.sh $remoteDir/PK_SEC43_PRESCRIBED_STATE2.odb $remoteDir/PK_SEC43_PRESCRIBED_STATE4.odb"
Write-Output $remoteSha

$checkString = ($remoteSha -join "`n")
if ($checkString -notmatch "ce8d5edcd2911dcb018bb15275271f874e7ea62b8fb48cf4a8297469a83acdd6") {
    throw "Remote SHA-256 hash mismatch on f42_mixed_uel.for"
}

Write-Output "=== STAGING CASE 3 MULTI-STATE REMESHING EXPERIMENT COMPLETE ==="
