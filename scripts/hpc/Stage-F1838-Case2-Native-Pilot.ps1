# -*- coding: utf-8 -*-
# scripts/hpc/Stage-F1838-Case2-Native-Pilot.ps1
# Staging and Hash Verification for Task F1838 Case 2 Native Job-1 Pilot Simulation

$ErrorActionPreference = 'Stop'
$repo = 'D:\Master thesis\Adaptive remeshing'
$cfg = "$env:USERPROFILE\.ssh\codex_config"
$remoteDir = "/scratch9/pr21vyci/runs/f1838_case2_native_pilot"
$pkgDir = Join-Path $repo 'models/pandey_kumar_mode1/277_f1838_case2_native_pilot'

function Upload-File($local, $remote) {
    & scp -F $cfg -B -o BatchMode=yes $local "tu_freiberg:$remote"
    if ($LASTEXITCODE -ne 0) { throw "SCP failed for $local to $remote" }
}

function Invoke-Remote($cmd) {
    & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $repo '.agents/scripts/Invoke-GuardedSsh.ps1') -RemoteCommand $cmd
}

Write-Output "=== TASK F1838: STAGING CASE 2 NATIVE JOB-1 PILOT SIMULATION ON CLUSTER ==="
Write-Output "Target directory: $remoteDir"
Invoke-Remote "mkdir -p $remoteDir && chmod 755 $remoteDir"

$files = @(
    "PK_HOLE_COARSE_F1838_PILOT.inp",
    "f42_native_miseseri_interface_v1.for",
    "job_notifications.sh",
    "submit_f1838_case2_pilot.pbs"
)

foreach ($f in $files) {
    $local = Join-Path $pkgDir $f
    if (-not (Test-Path $local)) {
        throw "Missing local file: $local"
    }
    $remote = "$remoteDir/$f"
    Write-Output "Uploading $f via SCP..."
    Upload-File $local $remote
}

Invoke-Remote "chmod 755 $remoteDir/submit_f1838_case2_pilot.pbs $remoteDir/job_notifications.sh"

Write-Output "Verifying remote SHA-256 checksums..."
$remoteSums = Invoke-Remote "sha256sum $remoteDir/PK_HOLE_COARSE_F1838_PILOT.inp $remoteDir/f42_native_miseseri_interface_v1.for $remoteDir/submit_f1838_case2_pilot.pbs"
Write-Output $remoteSums

$sumStr = ($remoteSums -join "`n").ToLower()

$expectedInp = "555d9285ea417abaa2cf08ae630d50d4dd0db99f5702f6cc45eacebd1d075785"
$expectedFor = "e5c98b6f601b1cd586571f8e24f357d15abbd1c5d5487b52903ba249734279b2"
$expectedPbs = "b12b7737a1132c8392a4e2376dbcb4249b982d7554b98622e5324c89016c3836"

if ($sumStr -notmatch $expectedInp) { throw "Remote SHA-256 hash mismatch on PK_HOLE_COARSE_F1838_PILOT.inp" }
if ($sumStr -notmatch $expectedFor) { throw "Remote SHA-256 hash mismatch on f42_native_miseseri_interface_v1.for" }
if ($sumStr -notmatch $expectedPbs) { throw "Remote SHA-256 hash mismatch on submit_f1838_case2_pilot.pbs" }

Write-Output "=== REMOTE STAGING AND INTEGRITY VERIFICATION COMPLETE: ALL HASHES MATCH ==="
