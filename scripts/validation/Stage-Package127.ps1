$ErrorActionPreference = 'Stop'
$repo = 'D:\Master thesis\Adaptive remeshing'
$cfg = "$env:USERPROFILE\.ssh\codex_config"

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

Write-Output "=== STAGING PACKAGE 127 ==="
$remoteDir = "/scratch9/pr21vyci/runs/mode1_c4_inc86_instrumented_checkpoint"
Invoke-Remote "mkdir -p $remoteDir"

$pkg127 = Join-Path $repo 'models/pandey_kumar_mode1/127_c4_inc86_instrumented_checkpoint'
$manifest = Get-Content (Join-Path $pkg127 'M1_C4_INC86_INSTRUMENTED_AUTHORIZATION.json') -Raw | ConvertFrom-Json

foreach ($property in $manifest.files.PSObject.Properties) {
    $f = $property.Name
    $local = (Join-Path $pkg127 $f).Replace('\', '/')
    $remote = "$remoteDir/$f"
    Write-Output "Uploading $f via SCP..."
    Upload-File $local $remote
}

Write-Output "Making shell scripts and pbs executable..."
Invoke-Remote "chmod +x $remoteDir/*.sh $remoteDir/*.pbs"

Write-Output "Running remote datacheck for Package 127..."
$dcOut = Invoke-Remote "bash $remoteDir/run_c4_inc86_instrumented_datacheck.sh"
Write-Output $dcOut

$verify = Invoke-Remote "grep -c 'ANALYSIS DATACHECK COMPLETE' $remoteDir/M1_C4_INC86_INSTRUMENTED_DC.dat"
Write-Output "Package 127 datacheck complete count: $verify"
if ($verify.Trim() -lt 1) {
    throw "Datacheck did not complete successfully for Package 127"
}

Write-Output "Downloading datacheck outputs..."
Download-File "$remoteDir/M1_C4_INC86_INSTRUMENTED_DC.dat" (Join-Path $pkg127 'M1_C4_INC86_INSTRUMENTED_DC.dat').Replace('\', '/')
Download-File "$remoteDir/M1_C4_INC86_INSTRUMENTED_DC.msg" (Join-Path $pkg127 'M1_C4_INC86_INSTRUMENTED_DC.msg').Replace('\', '/')

Write-Output "=== STAGING AND DATACHECK COMPLETE FOR PACKAGE 127 ==="
