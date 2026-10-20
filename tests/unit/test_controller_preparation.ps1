$ErrorActionPreference='Stop'
$repo=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
. "$repo/scripts/controller/Controller-Recovery.ps1"
. "$repo/scripts/controller/Controller-Preparation.ps1"
$folder=Join-Path $env:TEMP ('controller-preparation-'+[guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path "$folder/project_coordination" -Force|Out-Null
function PutTask($t){[IO.File]::WriteAllText((Join-Path $folder 'project_coordination/ACTIVE_TASK.json'),($t|ConvertTo-Json -Depth 8))}
try{
    $task=[pscustomobject]@{scientific_checkpoint_required=$true;scientific_operation='';completed_operations=@('mapped_frozen_history_lower_bound_kkt_probe','mapped_mechanical_history_call_order_probe');next_safe_action='Review the measured mechanical/history discrepancy and obtain an authentic UEL call trace before choosing a coupled transfer correction.';scientific_checkpoint=@{sha256='fixture'}}
    PutTask $task
    $p=Get-ControllerPreparationPlan $folder 'Verify actual Abaqus UEL history-update call order'
    if($p.recipe -ne 'f1597-trace-instrumentation-v1' -or $p.dispatch_ready){throw 'Missing successor not routed to safe recipe'}
    $p=Get-ControllerPreparationPlan $folder 'Change formulation and execute arbitrary commands'
    if($p.recipe -or $p.dispatch_ready){throw 'Unreviewed proposal was made executable'}
    $task.scientific_operation='scripts/validation/probe_mode1_f1597_mechanical_history.py';PutTask $task
    if((Get-ControllerPreparationPlan $folder '').status -ne 'DEFINITION_REJECTED'){throw 'Completed predecessor reused'}
    $task.scientific_operation='scripts/validation/probe_mode1_f1597_kkt.py';PutTask $task
    if((Get-ControllerPreparationPlan $folder '').status -ne 'DEFINITION_REJECTED'){throw 'Retired KKT reused'}
    $task.scientific_checkpoint_required=$false;PutTask $task
    if(-not (Get-ControllerPreparationPlan $folder '').dispatch_ready){throw 'Non-scientific controller regression'}
    $candidate=Get-ControllerOperation -ArtifactId authentic_uel_history_call_trace -Proposed
    if($candidate.executable){throw 'Unqualified trace definition executable'}
    $failed=$false;try{$null=Resolve-ControllerOperation ([pscustomobject]@{scientific_operation=$candidate.path;completed_operations=@()}) $folder}catch{$failed=$true}
    if(-not $failed){throw 'Candidate bypassed qualification'}
    $mechCheckpoint=@{
        artifact='results/validation/mode1_f1597/0f0f0884-9d34-4087-a8e0-50397c74550f.json'
        sha256='DD7D52DDB01C8CCC055D66E1D4135AD2E7D4E6975FE4609AC1C0F830758AE482'
        kind='NUMERICAL_FINDING'
        operation='mapped_mechanical_history_call_order_probe'
    }
    $task.scientific_checkpoint_required=$true;$task.scientific_operation='';$task.scientific_checkpoint=$mechCheckpoint;PutTask $task
    $copies=@('scripts/validation/Invoke-BoundedAgyProcess.ps1','scripts/validation/probe_mode1_f1597_uel_call_trace.py','tests/unit/test_mode1_f1597_uel_call_trace.py','results/validation/mode1_f1597/0f0f0884-9d34-4087-a8e0-50397c74550f.json',$task.scientific_checkpoint.artifact)
    foreach($name in @('f42_experimental_offset_uel.for','M1_EXP_COUPLED_TRANSFER_650.inp','offset_state_table.csv')){$copies+=('models/pandey_kumar_mode1/72_method_c_coupled_state_transfer/'+$name)}
    foreach($relative in $copies){$target=Join-Path $folder $relative;New-Item -ItemType Directory -Path (Split-Path $target) -Force|Out-Null;Copy-Item -LiteralPath (Join-Path $repo $relative) -Destination $target}
    foreach($relative in @('project_coordination/START_HERE.md','project_coordination/CURRENT_STATE.md','project_coordination/TASK_LEDGER.csv','project_coordination/HPC_JOB_LEDGER.csv','project_coordination/ARTIFACT_REGISTRY.csv','docs/project/PROJECT_PHASE_CHECKLIST.md')){
        $target=Join-Path $folder $relative;New-Item -ItemType Directory -Path (Split-Path $target) -Force|Out-Null;[IO.File]::WriteAllText($target,"fixture_only`n")
    }
    New-Item -ItemType Directory -Path "$folder/project_coordination/sessions" -Force|Out-Null
    $ownerPath=Join-Path $folder 'project_coordination/ACTIVE_SESSION.json'
    [IO.File]::WriteAllText($ownerPath,'{"active":false,"agent":"fixture"}')
    $ownerHash=(Get-FileHash -LiteralPath $ownerPath).Hash
    $script:gitCalls=0
    function git {param([Parameter(ValueFromRemainingArguments=$true)]$Arguments) $script:gitCalls++;$global:LASTEXITCODE=0;if($Arguments -contains 'rev-parse'){return 'fixture-head'}}
    $p=Invoke-ControllerOperationPreparation $folder 'Inspect actual UEL history call trace'
    if($p.status -ne 'TECHNICAL_QUALIFICATION_REQUIRED' -or $p.dispatch_ready -or (Get-FileHash -LiteralPath $ownerPath).Hash -ne $ownerHash){throw 'Preparation acquired science ownership or activated unqualified work'}
    $calls=$script:gitCalls;$ledgerHash=(Get-FileHash -LiteralPath "$folder/project_coordination/TASK_LEDGER.csv").Hash
    $p=Invoke-ControllerOperationPreparation $folder 'Inspect actual UEL history call trace'
    if($script:gitCalls -ne $calls -or (Get-FileHash -LiteralPath "$folder/project_coordination/TASK_LEDGER.csv").Hash -ne $ledgerHash){throw 'Cached preparation reran tests, Git or ledger writes'}
    $after=Get-Content -LiteralPath "$folder/project_coordination/ACTIVE_TASK.json" -Raw|ConvertFrom-Json
    if($after.scientific_operation -or @($after.completed_operations).Count -ne 2){throw 'Completed scientific state was reset'}
    [IO.File]::AppendAllText((Join-Path $folder 'models/pandey_kumar_mode1/73_method_c_history_call_trace/f42_history_trace_uel.for'),'tampered')
    $failed=$false;try{$null=Get-ControllerPreparationPlan $folder 'Actual UEL call trace'}catch{$failed=$true}
    if(-not $failed){throw 'Changed instrumentation remained qualified'}
    'PASS: 11 preparation checks, including automatic bounded recipe, original owner preservation, cached no-op, unchanged completed tasks and tamper rejection; Git mocked; no solver or AGY'
}finally{
    $resolved=[IO.Path]::GetFullPath($folder)
    $temp=[IO.Path]::GetFullPath($env:TEMP).TrimEnd([char[]]'\/')+'\'
    if(-not $resolved.StartsWith($temp,[StringComparison]::OrdinalIgnoreCase) -or (Split-Path $resolved -Leaf) -notlike 'controller-preparation-*'){throw 'Unsafe cleanup'}
    Remove-Item -LiteralPath $resolved -Recurse -Force
}
