# Offline completion protocol regression. All checkpoint writes are isolated;
# no controller loop, SSH, scheduler, credential or submission entrypoint runs.
param([string]$ResponsePath)
$ErrorActionPreference = 'Stop'
$repo = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
. (Join-Path $repo 'scripts/controller/Controller-Recovery.ps1')
$root = Join-Path ([IO.Path]::GetTempPath()) ('completion-notification-' + [guid]::NewGuid().ToString('N'))
[void](New-Item -ItemType Directory -Path $root)
$script:checks = 0
function Check([bool]$Okay,[string]$Message) {
    if (-not $Okay) { throw "FAIL: $Message" }
    $script:checks++; Write-Host "PASS: $Message"
}
# Isolate evidence refresh, not completion/checkpoint serialization logic.
function Update-ControllerEvidence([string]$Workspace,[string]$Path,$State) { }
function New-State {
    [pscustomobject]@{state='RUNNING';turn=354;run_id='fixture-run';task_id='fixture-task';
        recovery_count=0;session=[pscustomobject]@{active=$false};updated_at='';
        block_reason='';next_safe_action='';task_type='RESEARCH_PREPARATION';scientific_operation=''}
}
$ack = 'Notification received; background log query task-572 exited with code 0. Turn 354 remains fully closed out, session lock released, and state synchronized to remote repository. Awaiting next controller instruction.'
$response = "Diagnostic complete.`nFinished`n$ack`n"
Check ($response -notmatch '(?s)Finished[.\s]*$') 'Reproduces original terminal-marker rejection'
Check (Test-ControllerResponseFinished $response 354) 'Successful same-turn acknowledgement accepted'
Check (Test-ControllerResponseFinished "Done`nFinished.`r`n$ack`r`n" 354) 'CRLF and punctuated marker accepted'
Check (Test-ControllerResponseFinished "Done`nFinished`n" 354) 'Ordinary marker unchanged'
foreach ($bad in @(
    $response.Replace('code 0','code 1'),
    $response.Replace('Turn 354','Turn 355'),
    $response.Replace("Finished`n",''),
    "Finished`nUnfinished scientific work remains",
    ($response + 'Additional work started'),
    $response.Replace('Finished','The text mentions Finished'),
    "Partial response"
)) { Check (-not (Test-ControllerResponseFinished $bad 354)) 'Unknown/failed/stale/incomplete suffix rejected' }
$path = Join-Path $root 'checkpoint.json'
$s = New-State
Check ((Complete-ControllerTurn $root $path $s $response) -eq 'COMPLETED') 'Completion dry run accepts diagnostic response'
Check ($s.task_type -eq 'RESEARCH_PREPARATION' -and -not $s.scientific_operation) 'Completion does not qualify scientific execution'
$saved = Read-ControllerCheckpoint $path
Check ($saved.response -ceq $response) 'Raw response retained verbatim in checksummed isolated checkpoint'
$s = New-State; $s.session.active=$true
Check ((Complete-ControllerTurn $root $path $s $response -VerifiedReceipt) -eq 'BLOCKED') 'Active session still blocks even with receipt'
$s = New-State
Check ((Complete-ControllerTurn $root $path $s ("BLOCKED: unavailable operation`n"+$response) -VerifiedReceipt) -eq 'BLOCKED') 'Explicit BLOCKED still blocks even with receipt'
$s = New-State
Check ((Complete-ControllerTurn $root $path $s 'Incomplete response') -eq 'BLOCKED') 'Missing marker and receipt fail closed'
if ($ResponsePath) {
    if (-not (Test-Path -LiteralPath $ResponsePath -PathType Leaf)) { throw 'Missing replay input' }
    $original = Get-Content -LiteralPath $ResponsePath -Raw -Encoding UTF8 | ConvertFrom-Json
    Check ($original.status -ceq 'SUCCESS') 'Original AGY result status verified'
    $s = New-State
    Check ((Complete-ControllerTurn $root $path $s $original.response) -eq 'COMPLETED') 'Full original Turn 354 response replay passes without submission'
    Check ($s.scientific_operation -eq '' -and $s.task_type -eq 'RESEARCH_PREPARATION') 'Original replay leaves execution unqualified'
}
Write-Host "PASS: $script:checks completion checks; isolated dry-run checkpoint: $path"
