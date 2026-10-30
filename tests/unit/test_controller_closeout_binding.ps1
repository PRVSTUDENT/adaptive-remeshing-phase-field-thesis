$ErrorActionPreference='Stop'
. "$PSScriptRoot/../../scripts/controller/Controller-Operations.ps1"
$op=[pscustomobject]@{id='evaluate_mode1_package148_state_transfer_r3';path='scripts/validation/execute_package148_state_transfer.py';qualification=$null}
function State([string]$path){[pscustomobject]@{scientific_operation=$path;operation_id=$op.id;task_type='QUALIFIED_EXECUTION'}}
foreach($recordPath in @($op.path,$op.id)){
 foreach($statePath in @($op.path,$op.id)){
  if(-not (Test-ControllerOperationBinding $op ([pscustomobject]@{operation_id=$op.id;operation_path=$recordPath}) (State $statePath))){throw 'Valid path/ID representation rejected'}
 }
}
$record=[pscustomobject]@{operation_id=$op.id;operation_path=$op.path}
foreach($bad in @('research_preparation','evaluate_mode1_package148_state_transfer_r2','')){
 if(Test-ControllerOperationBinding $op $record (State $bad)){throw 'Wrong state operation accepted'}
}
$stale=State $op.id;$stale.operation_id='research_preparation';$stale.task_type='RESEARCH_PREPARATION'
if(Test-ControllerOperationBinding $op $record $stale){throw 'Stale preparation checkpoint accepted'}
$record.operation_id='evaluate_mode1_package148_state_transfer_r2'
if(Test-ControllerOperationBinding $op $record (State $op.path)){throw 'Wrong record ID accepted'}
$root=Join-Path $env:TEMP ('closeout-pin-'+[guid]::NewGuid())
New-Item -ItemType Directory -Path $root|Out-Null
[IO.File]::WriteAllText((Join-Path $root 'q.json'),'fixture qualification')
$op.qualification=[pscustomobject]@{script_sha256=('A'*64);qualification_artifact='q.json'}
$s=[pscustomobject]@{sources=@{}}
$failed=$false;try{$null=Get-ControllerPinnedOperationHash $op $s $root}catch{$failed=$true}
if(-not $failed){throw 'Missing preflight pin accepted'}
$s.sources['q.json']=(Get-FileHash (Join-Path $root 'q.json')).Hash
if((Get-ControllerPinnedOperationHash $op $s $root) -cne ('A'*64)){throw 'Bound qualification pin rejected'}
[IO.File]::WriteAllText((Join-Path $root 'q.json'),'changed')
$failed=$false;try{$null=Get-ControllerPinnedOperationHash $op $s $root}catch{$failed=$true}
if(-not $failed){throw 'Changed qualification pin accepted'}
$source=Get-Content "$PSScriptRoot/../../scripts/controller/Invoke-ControllerTurn.ps1" -Raw
if(([regex]::Matches($source,'Test-ControllerOperationBinding \$operation \$record \$state')).Count -ne 2){throw 'Scientific and Complete do not share binding validation'}
'PASS: 13 closeout/source-pin cases; shared Scientific/Complete validator; fixture retained in TEMP.'
