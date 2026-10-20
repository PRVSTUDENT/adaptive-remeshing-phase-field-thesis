$ErrorActionPreference='Stop'
. "$PSScriptRoot/../../scripts/controller/Controller-Recovery.ps1"
$task=[pscustomobject]@{scientific_operation='scripts/validation/probe_mode1_f1597_mechanical_history.py';completed_operations=@('mapped_frozen_history_lower_bound_kkt_probe');next_safe_action='define next'}
if((Resolve-ControllerOperation $task).id -ne 'mapped_mechanical_history_call_order_probe'){throw 'New operation not resolved'}
foreach($path in @('scripts/validation/probe_mode1_f1597_kkt.py','../unregistered.py','scripts/validation/not-qualified.py','')){
    $task.scientific_operation=$path;$failed=$false
    try{$null=Resolve-ControllerOperation $task}catch{$failed=$true}
    if(-not $failed){throw 'Retired/unknown/undefined dispatch accepted'}
}
$task.scientific_operation='scripts/validation/probe_mode1_f1597_mechanical_history.py'
$task.completed_operations+= 'mapped_mechanical_history_call_order_probe'
$failed=$false;try{$null=Resolve-ControllerOperation $task}catch{$failed=$_.Exception.Message -match 'COMPLETED_OPERATION_REJECTED'}
if(-not $failed){throw 'Completed new operation replay allowed'}
$historical=Get-ControllerOperation -ArtifactId 'mapped_frozen_history_lower_bound_kkt_probe' -Historical
if($historical.executable){throw 'Historical artifact became executable'}
$failed=$false;try{Assert-ControllerDispatchCheckpoint $pwd ([pscustomobject]@{state='BLOCKED';block_reason='fixture'})}catch{$failed=$_.Exception.Message -match '^BLOCKED:'}
if(-not $failed){throw 'Blocked checkpoint bypassed'}
$failed=$false;try{Assert-ControllerDispatchCheckpoint $pwd ([pscustomobject]@{state='COMPLETED';reconciliation=[pscustomobject]@{status='COMPLETED_SCIENCE_CREDENTIAL_REPAIR_VERIFIED';original_checkpoint=(Join-Path $env:TEMP ([guid]::NewGuid().ToString()+'.missing'))}})}catch{$failed=$true}
if(-not $failed){throw 'Missing archive accepted'}
'PASS: new dispatch, retired/unknown/undefined rejection, completed-operation rejection, historical verification-only, blocked checkpoint and missing-archive rejection (9 cases)'
