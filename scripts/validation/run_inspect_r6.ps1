$ErrorActionPreference = 'Stop'

$scriptPath = "scripts\validation\extract_stage_a_full_state.py"
$bytes = [System.IO.File]::ReadAllBytes((Resolve-Path $scriptPath))
$b64 = [System.Convert]::ToBase64String($bytes)

$remoteDir = "/scratch9/pr21vyci/runs/mode1_c3_staggered_continuation_r6"
$remoteScript = "$remoteDir/extract_full_states.py"

Write-Host "Uploading extract script to cluster..."
$uploadCmd = "echo $b64 | base64 -d > $remoteScript"
& .\.agents\scripts\Invoke-GuardedSsh.ps1 -RemoteCommand $uploadCmd

$execSh = @"
#!/bin/bash
set -euo pipefail
cd /scratch9/pr21vyci/runs/mode1_c3_staggered_continuation_r6
if ! type module >/dev/null 2>&1; then
    source /etc/profile.d/lmod.sh 2>/dev/null || source /usr/share/Modules/init/bash 2>/dev/null || true
fi
module purge
module load gcc/11.4.0 intel/2024.2.0 abaqus/2023
abaqus python extract_full_states.py
"@

$shBytes = [System.Text.Encoding]::UTF8.GetBytes($execSh)
$shB64 = [System.Convert]::ToBase64String($shBytes)
$remoteSh = "$remoteDir/run_extract_states.sh"

Write-Host "Uploading run_extract_states.sh..."
$uploadShCmd = "echo $shB64 | base64 -d > $remoteSh; chmod +x $remoteSh"
& .\.agents\scripts\Invoke-GuardedSsh.ps1 -RemoteCommand $uploadShCmd

Write-Host "Executing extract script on cluster..."
& .\.agents\scripts\Invoke-GuardedSsh.ps1 -RemoteCommand "$remoteSh" -TimeoutSeconds 180

Write-Host "Downloading r6_extracted_states.json..."
$fetchCmd = "base64 /scratch9/pr21vyci/runs/mode1_c3_staggered_continuation_r6/r6_extracted_states.json"
$b64Out = & .\.agents\scripts\Invoke-GuardedSsh.ps1 -RemoteCommand $fetchCmd -TimeoutSeconds 180
$jsonBytes = [System.Convert]::FromBase64String(($b64Out -join ''))
[System.IO.File]::WriteAllBytes("models/pandey_kumar_mode1/108_r6_c3_multi_increment_continuation/r6_extracted_states.json", $jsonBytes)
Write-Host "Saved models/pandey_kumar_mode1/108_r6_c3_multi_increment_continuation/r6_extracted_states.json"

