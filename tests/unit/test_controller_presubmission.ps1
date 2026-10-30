$ErrorActionPreference='Stop'
. "$PSScriptRoot/../../scripts/controller/Controller-Operations.ps1"
$root=Join-Path $env:TEMP ('controller-presubmission-'+[guid]::NewGuid())
New-Item -ItemType Directory -Path $root | Out-Null
function Put([string]$path,[string]$text){$full=Join-Path $root $path; New-Item -ItemType Directory -Path (Split-Path $full) -Force|Out-Null;[IO.File]::WriteAllText($full,$text)}
function Hash([string]$path){(Get-FileHash (Join-Path $root $path)).Hash}
$scriptPath='scripts/validation/execute_package148_state_transfer.py'
$manifest='models/pandey_kumar_mode1/148_c4_package148_state_transfer_r1/EXECUTION_MANIFEST.json'
$review='results/validation/review.json'
Put $scriptPath '# fixture; never executed'
Put 'tests/fixture.py' '# passing test fixture'
Put 'scripts/hpc/Invoke-Mode1Execution.ps1' '# fixture; never executed'
Put $manifest '{"scientific_scope":"MODE1","automatic_retry":false,"max_submissions":1,"jobs":[{"id":"M1_C4_P148_R1"}]}'
Put $review '{"verification_passed":true,"review_summary":{"r1_independent_review":"PASS"}}'
$deps=@{};foreach($p in @($manifest,$review,'scripts/hpc/Invoke-Mode1Execution.ps1')){$deps[$p]=Hash $p}
$q=@{schema=1;operation='evaluate_mode1_package148_state_transfer';status='QUALIFIED_FOR_PREFLIGHT';dispatch_ready=$true;canonical_path=$scriptPath;script_sha256=(Hash $scriptPath);execution_mode='HPC_PRE_SUBMISSION';execution_adapter='scripts/hpc/Invoke-Mode1Execution.ps1';production_uel_sha256='CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6';manifest=$manifest;independent_review=$review;tests=@{'tests/fixture.py'=(Hash 'tests/fixture.py')};tests_passed=$true;scientific_dependencies=$deps;verification_criteria=@{required_measurements=@('submitted_jobs')}}
function SaveQ {Put 'scripts/validation/execute_package148_state_transfer.qualification.json' ($q|ConvertTo-Json -Depth 10)}
function Reject([string]$label){SaveQ;$rejected=$false;try{$null=Get-ControllerDynamicQualification $root -Path $scriptPath}catch{$rejected=$true};if(-not $rejected){throw "Accepted $label"}}
SaveQ
$op=Get-ControllerOperation -Path $scriptPath -Workspace $root
if(-not $op.executable -or $op.qualification.pbs_job_id){throw 'Pre-submission registration needs no PBS ID'}
$task=[pscustomobject]@{scientific_checkpoint_required=$true;scientific_operation=$scriptPath;completed_operations=@()}
if((Resolve-ControllerTaskType $task $root).task_type -ne 'QUALIFIED_EXECUTION'){throw 'New turn cannot dispatch'}
$q.pbs_job_id='123.mmaster02';Reject 'pre-existing job masquerading as pre-submission';$q.Remove('pbs_job_id')
$q.execution_adapter='arbitrary.ps1';Reject 'unguarded adapter';$q.execution_adapter='scripts/hpc/Invoke-Mode1Execution.ps1'
$q.tests_passed=$false;Reject 'failed tests';$q.tests_passed=$true
$q.execution_mode='HPC';$q.status='QUALIFIED';Reject 'legacy HPC without PBS ID';$q.execution_mode='HPC_PRE_SUBMISSION';$q.status='QUALIFIED_FOR_PREFLIGHT'
Put $review '{"verification_passed":false}';Reject 'changed review';Put $review '{"verification_passed":true,"review_summary":{"r1_independent_review":"PASS"}}'
SaveQ
Put $manifest 'tampered';Reject 'changed manifest'
'PASS: pre-submission registration/new-turn dispatch; fake ID, unguarded adapter, failed tests, legacy HPC without job, changed review and changed manifest rejected (8 cases). Fixture retained in TEMP.'
$r2='models/pandey_kumar_mode1/148_c4_package148_state_transfer_r2/EXECUTION_MANIFEST.json'
Put $r2 '{"scientific_scope":"MODE1","automatic_retry":false,"max_submissions":1,"jobs":[{"id":"M1_C4_P148_R2"}]}'
Put $review '{"verification_passed":true,"independent_r2_qualification":"PASS","python_36_compatibility":"PASS"}'
$q.operation='evaluate_mode1_package148_state_transfer_r2';$q.manifest=$r2
$q.scientific_dependencies.Remove($manifest);$q.scientific_dependencies[$r2]=Hash $r2;$q.scientific_dependencies[$review]=Hash $review
Put 'scripts/validation/evaluate_mode1_package148_state_transfer_r2.qualification.json' ($q|ConvertTo-Json -Depth 10)
$task|Add-Member -NotePropertyName scientific_operation_id -NotePropertyValue $q.operation
$task.completed_operations=@('evaluate_mode1_package148_state_transfer')
$resolved=Resolve-ControllerTaskType $task $root
if($resolved.task_type -ne 'QUALIFIED_EXECUTION' -or $resolved.operation.id -ne $q.operation){throw 'R2 dispatched as R1/preparation'}
$task.completed_operations+=$q.operation
$denied=$false;try{$null=Resolve-ControllerOperation $task $root}catch{$denied=$_.Exception.Message -match 'COMPLETED_OPERATION_REJECTED'}
if(-not $denied){throw 'Completed R2 replay accepted'}
'PASS: R2 independently resolves with completed R1; completed R2 replay rejected (2 cases).'
$r3='models/pandey_kumar_mode1/148_c4_package148_state_transfer_r3/EXECUTION_MANIFEST.json'
Put $r3 '{"scientific_scope":"MODE1","automatic_retry":false,"max_submissions":1,"jobs":[{"id":"M1_C4_P148_R3"}]}'
Put $review '{"verification_passed":true,"independent_r3_qualification":"PASS","python_36_compatibility":"PASS"}'
$q.operation='evaluate_mode1_package148_state_transfer_r3';$q.manifest=$r3
$q.scientific_dependencies.Remove($r2);$q.scientific_dependencies[$r3]=Hash $r3;$q.scientific_dependencies[$review]=Hash $review
Put 'scripts/validation/evaluate_mode1_package148_state_transfer_r3.qualification.json' ($q|ConvertTo-Json -Depth 10)
$task.scientific_operation_id=$q.operation
$resolved=Resolve-ControllerTaskType $task $root
if($resolved.task_type -ne 'QUALIFIED_EXECUTION' -or $resolved.operation.id -ne $q.operation){throw 'R3 dispatched as R1/R2/preparation'}
$task.completed_operations+=$q.operation
$denied=$false;try{$null=Resolve-ControllerOperation $task $root}catch{$denied=$_.Exception.Message -match 'COMPLETED_OPERATION_REJECTED'}
if(-not $denied){throw 'Completed R3 replay accepted'}
'PASS: R3 independently resolves with completed R1 and R2; completed R3 replay rejected (2 cases).'
$r4='models/pandey_kumar_mode1/148_c4_package148_state_transfer_r4/EXECUTION_MANIFEST.json'
$r4text='{"scientific_scope":"MODE1","automatic_retry":false,"max_submissions":1,"jobs":[{"id":"M1_C4_P148_R4"}]}'
$r4review='{"verification_passed":true,"independent_r4_qualification":"PASS","python_36_compatibility":"PASS"}'
Put $r4 $r4text; Put $review $r4review
$q.operation='evaluate_mode1_package148_state_transfer_r4';$q.manifest=$r4
$q.scientific_dependencies.Remove($r3);$q.scientific_dependencies[$r4]=Hash $r4;$q.scientific_dependencies[$review]=Hash $review
function SaveR4 {Put 'scripts/validation/evaluate_mode1_package148_state_transfer_r4.qualification.json' ($q|ConvertTo-Json -Depth 10)}
function RejectR4([string]$label) {
    SaveR4; $rejected=$false
    try {$null=Get-ControllerOperation -ArtifactId $q.operation -Workspace $root} catch {$rejected=$true}
    if(-not $rejected){throw "R4 accepted $label"}
    Write-Host "PASS: R4 rejects $label"
}
SaveR4
$task.scientific_operation_id=$q.operation
$resolved=Resolve-ControllerTaskType $task $root
if($resolved.task_type -ne 'QUALIFIED_EXECUTION' -or $resolved.operation.id -cne $q.operation){throw 'R4 dispatched as predecessor/preparation'}
'PASS: R4 path/ID binding selects QUALIFIED_EXECUTION despite completed R1/R2/R3'
$task.scientific_operation=$q.operation
if((Resolve-ControllerTaskType $task $root).operation.id -cne $q.operation){throw 'R4 ID-form dispatch failed'}
'PASS: R4 ID-form binding selects exact R4 operation'
$task.completed_operations+=$q.operation
$denied=$false;try{$null=Resolve-ControllerOperation $task $root}catch{$denied=$_.Exception.Message -match 'COMPLETED_OPERATION_REJECTED'}
if(-not $denied){throw 'Completed R4 replay accepted'}
'PASS: completed R4 replay rejected'
Put $review '{"verification_passed":true,"independent_r3_qualification":"PASS","python_36_compatibility":"PASS"}'
$q.scientific_dependencies[$review]=Hash $review; RejectR4 'R3 review relabelled as R4'
Put $review '{"verification_passed":true,"independent_r4_qualification":"PASS","python_36_compatibility":"FAIL"}'
$q.scientific_dependencies[$review]=Hash $review; RejectR4 'failed Python compatibility'
Put $review $r4review;$q.scientific_dependencies[$review]=Hash $review
$q.manifest=$r3;RejectR4 'R3 manifest';$q.manifest=$r4
Put $r4 'changed manifest';RejectR4 'changed manifest hash';Put $r4 $r4text
Put $r4 ($r4text.Replace('"automatic_retry":false','"automatic_retry":true'));$q.scientific_dependencies[$r4]=Hash $r4
RejectR4 'automatic retry';Put $r4 $r4text;$q.scientific_dependencies[$r4]=Hash $r4
Put 'scripts/state_transfer/driver.py' '# original driver'
$q.scientific_dependencies['scripts/state_transfer/driver.py']=Hash 'scripts/state_transfer/driver.py'
Put 'scripts/state_transfer/driver.py' '# changed driver';RejectR4 'changed driver hash'
'PASS: 9 R4 registration/dispatch/failure-closure cases; no scheduler invocation.'

# R5 registration, independent qualification and dispatch failure-closure
$r5='models/pandey_kumar_mode1/148_c4_package148_state_transfer_r5/EXECUTION_MANIFEST.json'
$r5text='{"scientific_scope":"MODE1","automatic_retry":false,"max_submissions":1,"jobs":[{"id":"M1_C4_P148_R5"}]}'
$r5review='{"verification_passed":true,"independent_r5_qualification":"PASS","python_36_compatibility":"PASS"}'
Put $r5 $r5text; Put $review $r5review
$q.operation='evaluate_mode1_package148_state_transfer_r5';$q.manifest=$r5
$q.scientific_dependencies.Remove($r4);$q.scientific_dependencies.Remove('scripts/state_transfer/driver.py');$q.scientific_dependencies[$r5]=Hash $r5;$q.scientific_dependencies[$review]=Hash $review
function SaveR5 {Put 'scripts/validation/evaluate_mode1_package148_state_transfer_r5.qualification.json' ($q|ConvertTo-Json -Depth 10)}
function RejectR5([string]$label) {
    SaveR5; $rejected=$false
    try {$null=Get-ControllerOperation -ArtifactId $q.operation -Workspace $root} catch {$rejected=$true}
    if(-not $rejected){throw "R5 accepted $label"}
    Write-Host "PASS: R5 rejects $label"
}
SaveR5
$task.scientific_operation=$scriptPath
$task.scientific_operation_id=$q.operation
$resolved=Resolve-ControllerTaskType $task $root
if($resolved.task_type -ne 'QUALIFIED_EXECUTION' -or $resolved.operation.id -cne $q.operation){throw 'R5 dispatched as predecessor/preparation'}
'PASS: R5 path/ID binding selects QUALIFIED_EXECUTION despite completed R1/R2/R3/R4'
$task.scientific_operation=$q.operation
if((Resolve-ControllerTaskType $task $root).operation.id -cne $q.operation){throw 'R5 ID-form dispatch failed'}
'PASS: R5 ID-form binding selects exact R5 operation'
$task.completed_operations+=$q.operation
$denied=$false;try{$null=Resolve-ControllerOperation $task $root}catch{$denied=$_.Exception.Message -match 'COMPLETED_OPERATION_REJECTED'}
if(-not $denied){throw 'Completed R5 replay accepted'}
'PASS: completed R5 replay rejected'
Put $review '{"verification_passed":true,"independent_r4_qualification":"PASS","python_36_compatibility":"PASS"}'
$q.scientific_dependencies[$review]=Hash $review; RejectR5 'R4 review relabelled as R5'
Put $review '{"verification_passed":true,"independent_r5_qualification":"PASS","python_36_compatibility":"FAIL"}'
$q.scientific_dependencies[$review]=Hash $review; RejectR5 'failed Python compatibility'
Put $review $r5review;$q.scientific_dependencies[$review]=Hash $review
$q.manifest=$r4;RejectR5 'R4 manifest';$q.manifest=$r5
Put $r5 'changed manifest';RejectR5 'changed manifest hash';Put $r5 $r5text
Put $r5 ($r5text.Replace('"automatic_retry":false','"automatic_retry":true'));$q.scientific_dependencies[$r5]=Hash $r5
RejectR5 'automatic retry';Put $r5 $r5text;$q.scientific_dependencies[$r5]=Hash $r5
'PASS: 9 R5 registration/dispatch/failure-closure cases; no scheduler invocation.'
