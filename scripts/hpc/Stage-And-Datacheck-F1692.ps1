$ErrorActionPreference = 'Stop'
$repo = 'D:\Master thesis\Adaptive remeshing'
$cfg = "$env:USERPROFILE\.ssh\codex_config"
$remoteDir = "/scratch9/pr21vyci/runs/mode1_pk_sec43_staggered_job1"
$pkgDir = Join-Path $repo 'models/pandey_kumar_mode1/192_pk_sec43_staggered_job1'

function Upload-File($local, $remote) {
    & scp -F $cfg -B -o BatchMode=yes $local "tu_freiberg:$remote"
    if ($LASTEXITCODE -ne 0) { throw "SCP failed for $local to $remote" }
}

function Download-File($remote, $local) {
    & scp -F $cfg -B -o BatchMode=yes "tu_freiberg:$remote" $local
    if ($LASTEXITCODE -ne 0) { throw "SCP failed for $remote to $local" }
}

function Invoke-Remote($cmd) {
    & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $repo '.agents/scripts/Invoke-GuardedSsh.ps1') -RemoteCommand $cmd
}

Write-Output "=== TASK F1692: STAGING AND DATACHECK ==="
Write-Output "Creating remote directory: $remoteDir"
Invoke-Remote "mkdir -p $remoteDir"

$files = @(
    "PK_SEC43_STAGGERED_JOB1.inp",
    "f42_staggered_variant_uel.for",
    "submit_M1_PK_SEC43_STAGGERED_JOB1.pbs",
    "job_notifications.sh",
    "PK_SEC43_STAGGERED_PHYS.inp",
    "run_sec43_staggered_datacheck.sh"
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
$remoteSha = Invoke-Remote "sha256sum $remoteDir/PK_SEC43_STAGGERED_JOB1.inp $remoteDir/f42_staggered_variant_uel.for $remoteDir/submit_M1_PK_SEC43_STAGGERED_JOB1.pbs"
Write-Output $remoteSha

Write-Output "Running remote Abaqus 2023 datacheck script..."
$dcOut = Invoke-Remote "bash $remoteDir/run_sec43_staggered_datacheck.sh"
Write-Output $dcOut

Write-Output "Verifying datacheck completion in .dat file..."
$verify = Invoke-Remote "grep -c 'THE ANALYSIS HAS COMPLETED SUCCESSFULLY' $remoteDir/PK_SEC43_STAGGERED_DC.dat || true"
Write-Output "Datacheck completion count: $verify"

Write-Output "Downloading datacheck outputs..."
Download-File "$remoteDir/PK_SEC43_STAGGERED_DC.dat" (Join-Path $pkgDir 'PK_SEC43_STAGGERED_DC.dat').Replace('\', '/')
Download-File "$remoteDir/PK_SEC43_STAGGERED_DC.msg" (Join-Path $pkgDir 'PK_SEC43_STAGGERED_DC.msg').Replace('\', '/')
Download-File "$remoteDir/PK_SEC43_STAGGERED_DC.sta" (Join-Path $pkgDir 'PK_SEC43_STAGGERED_DC.sta').Replace('\', '/')
Download-File "$remoteDir/PK_SEC43_STAGGERED_DC.log" (Join-Path $pkgDir 'PK_SEC43_STAGGERED_DC.log').Replace('\', '/')

Write-Output "[PASS] Remote staging and datacheck completed successfully!"
