$ErrorActionPreference = 'Stop'

$scriptPath = "scripts\validation\extract_stage_a_u1341.py"
$bytes = [System.IO.File]::ReadAllBytes((Resolve-Path $scriptPath))
$b64 = [System.Convert]::ToBase64String($bytes)

$remoteDir = "/scratch9/pr21vyci/runs/mode1_c3_staggered_continuation_r6"
$remoteScript = "$remoteDir/inspect_cracktip.py"

Write-Host "Uploading inspect script to cluster..."
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
abaqus python inspect_cracktip.py
"@

$shBytes = [System.Text.Encoding]::UTF8.GetBytes($execSh)
$shB64 = [System.Convert]::ToBase64String($shBytes)
$remoteSh = "$remoteDir/run_inspect.sh"

Write-Host "Uploading run_inspect.sh..."
$uploadShCmd = "echo $shB64 | base64 -d > $remoteSh; chmod +x $remoteSh"
& .\.agents\scripts\Invoke-GuardedSsh.ps1 -RemoteCommand $uploadShCmd

Write-Host "Executing inspect script on cluster..."
& .\.agents\scripts\Invoke-GuardedSsh.ps1 -RemoteCommand "$remoteSh" -TimeoutSeconds 180
