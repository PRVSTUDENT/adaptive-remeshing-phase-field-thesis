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
