# -*- coding: utf-8 -*-
# scripts/hpc/Stage-F1744-Case3-5State-Remesh.ps1
# Staging and Hash Verification for Task F1744 Case 3 5-State Sequential Native Remeshing

$ErrorActionPreference = 'Stop'
$repo = 'D:\Master thesis\Adaptive remeshing'
$cfg = "$env:USERPROFILE\.ssh\codex_config"
$remoteDir = "/scratch9/pr21vyci/runs/mode1_pk_f1744_case3_5state_remesh"
$pkgDir = Join-Path $repo 'models/pandey_kumar_mode1/230_f1744_case3_5state_remesh'

function Upload-File($local, $remote) {
    & scp -F $cfg -B -o BatchMode=yes $local "tu_freiberg:$remote"
    if ($LASTEXITCODE -ne 0) { throw "SCP failed for $local to $remote" }
}

function Invoke-Remote($cmd) {
    & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $repo '.agents/scripts/Invoke-GuardedSsh.ps1') -RemoteCommand $cmd
}

Write-Output "=== TASK F1744: STAGING CASE 3 5-STATE REMESHING EXPERIMENT ON CLUSTER ==="
Write-Output "Target directory: $remoteDir"
Invoke-Remote "mkdir -p $remoteDir && chmod 755 $remoteDir"

$files = @(
    "f1744_case3_5state_remesh.json",
    "f42_mixed_uel.for",
    "run_case3_5state_remesh.py",
    "audit_case3_5state_resolution.py",
    "PK_SEC43_COMPANION_T1.inp",
    "PK_SEC43_COMPANION_T2.inp",
    "PK_SEC43_COMPANION_T3.inp",
    "job_notifications.sh",
    "submit_f1744_case3_5state_remesh.pbs"
)

foreach ($f in $files) {
    $local = (Join-Path $pkgDir $f).Replace('\', '/')
    $remote = "$remoteDir/$f"
    Write-Output "Uploading $f via SCP..."
    Upload-File $local $remote
}

Write-Output "Copying authentic State 2 and State 4 donor ODBs on cluster..."
Invoke-Remote "cp -u /scratch9/pr21vyci/runs/mode1_pk_f1741_case3_remesh/PK_SEC43_PRESCRIBED_STATE*.odb $remoteDir/"

Write-Output "Setting remote permissions..."
Invoke-Remote "chmod 755 $remoteDir/*.sh $remoteDir/*.pbs $remoteDir/*.py"

Write-Output "Verifying remote donor ODBs and scripts..."
$remoteCheck = Invoke-Remote "ls -lh $remoteDir/*.odb"
Write-Output $remoteCheck

$remoteSha = Invoke-Remote "sha256sum $remoteDir/f42_mixed_uel.for $remoteDir/run_case3_5state_remesh.py $remoteDir/submit_f1744_case3_5state_remesh.pbs"
Write-Output $remoteSha

$checkString = ($remoteSha -join "`n")
if ($checkString -notmatch "ce8d5edcd2911dcb018bb15275271f874e7ea62b8fb48cf4a8297469a83acdd6") {
    throw "Remote SHA-256 hash mismatch on f42_mixed_uel.for"
}

Write-Output "=== STAGING CASE 3 5-STATE REMESHING EXPERIMENT COMPLETE ==="
