$ErrorActionPreference='Stop'
$repo=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
. (Join-Path $repo 'scripts/controller/Controller-Recovery.ps1')
. (Join-Path $repo 'scripts/controller/Controller-Preparation.ps1')
$f=Join-Path $env:TEMP ('successor-registration-'+[guid]::NewGuid().ToString('N'))
[void][IO.Directory]::CreateDirectory((Join-Path $f 'project_coordination/task_definitions'))
$script:n=0
function Check($ok,$message){if(-not $ok){throw "FAIL $message"};$script:n++;"PASS $script:n $message"}
function Put($relative,$text){[IO.File]::WriteAllText((Join-Path $f $relative),$text)}
$ledger="task_id,status,next_task,classification`nF1597-CLOSED,completed,F1598-EVALUATION,`nF1598-EVALUATION,ready,,REGISTERED_NOT_EXECUTED"
Put 'project_coordination/TASK_LEDGER.csv' $ledger
Put 'project_coordination/ACTIVE_SESSION.json' '{"active":false,"agent":"codex"}'
Put 'project_coordination/CURRENT_STATE.md' 'Preserve original outputs; no experiment in maintenance.'
Put 'project_coordination/HPC_JOB_LEDGER.csv' "Job_ID,Status`n1419480.mmaster02,SUBMITTED"
Put 'project_coordination/MODE1_EXECUTION_LEDGER.json' '{"attempts":1,"reserved_commands":["package166"],"pbs_job_id":"1419480.mmaster02"}'
Put 'evidence.json' '{"reported_physical_pass":false}'
$state=[pscustomobject]@{schema=1;run_id='19280009-42f4-4897-8d3a-9b52d2e5168a';task_id='F1597-CLOSED';turn=35;state='COMPLETED';recovery_count=0;updated_at='';next_instruction='Advance F1597-CLOSED: repeat old work'}
$cp=Join-Path $f 'checkpoint.json';Write-ControllerCheckpoint $cp $state
$pin=(Get-FileHash $cp).Hash
$d=[ordered]@{schema=1;task_id='F1598-EVALUATION';predecessor=@{task_id='F1597-CLOSED';run_id=$state.run_id;checkpoint_sha256=$pin};operation=@{id='research_preparation';mode='READ_ONLY_SCIENTIFIC_EVALUATION'};max_new_pbs_submissions=0;inherited_completed_operations=@('package166_submitted_once');evidence_sources=@{'evidence.json'=(Get-FileHash (Join-Path $f 'evidence.json')).Hash};initial_instruction="TASK: F1598-EVALUATION`nOPERATION_ID: research_preparation`nInspect existing evidence; no new job."}
$rel='project_coordination/task_definitions/F1598-EVALUATION.json';Put $rel ($d|ConvertTo-Json -Depth 15)
$task=@{task_id=$d.task_id;status='READY_READ_ONLY_EVALUATION';predecessor_task=$d.predecessor;registration=@{definition=$rel;sha256=(Get-FileHash (Join-Path $f $rel)).Hash};scientific_operation='';scientific_operation_id='research_preparation';scientific_checkpoint_required=$true;completed_operations=@('package166_submitted_once')}
function SaveTask {Put 'project_coordination/ACTIVE_TASK.json' ($task|ConvertTo-Json -Depth 15)}
SaveTask
$r=Get-ControllerTaskRegistrationPlan $f
Check ($r.dispatch_ready -and $r.status -eq 'REGISTERED_READ_ONLY_EVALUATION') 'Registered successor qualifies as evidence evaluation, never numerical execution'
$savedRegistration=$task.registration;$task.Remove('registration');SaveTask
Check (-not(Get-ControllerTaskRegistrationPlan $f).dispatch_ready) 'Removing a registered successor binding cannot downgrade it to a legacy task'
$task.registration=$savedRegistration;SaveTask
Assert-ControllerTaskLifecycle $f
$transition=Get-ControllerSuccessorCheckpointPlan $f $cp (Read-ControllerCheckpoint $cp)
Check ($transition.fresh_successor -and $transition.instruction -ceq $d.initial_instruction) 'Completed-parent transition chooses exact registered successor instruction'
Check ((Get-FileHash $cp).Hash -ceq $pin) 'Saved stale predecessor instruction is preserved byte-for-byte, never rewritten'
$plan=Get-ControllerPreparationPlan $f $transition.instruction
$resolved=Resolve-ControllerInstruction $f $transition.instruction
Check ($plan.dispatch_ready -and $resolved.evidence.task.task_id -ceq $d.task_id) 'Successor preflight selects new task without COMPLETED_TASK_REJECTED'
Put 'project_coordination/TASK_LEDGER.csv' ($ledger+"`nF1598-EVALUATION,ready,")
Check (-not(Get-ControllerTaskRegistrationPlan $f).dispatch_ready) 'Duplicate exact task registration rejected'
Put 'project_coordination/TASK_LEDGER.csv' $ledger
$state.state='RUNNING'
try{$null=Get-ControllerSuccessorCheckpointPlan $f $cp $state;throw 'Expected nonterminal rejection'}catch{Check ($_.Exception.Message -match 'foreign nonterminal') 'Unfinished foreign checkpoint cannot be discarded for a new task'}
$state.state='COMPLETED';$state.run_id='wrong-run'
try{$null=Get-ControllerSuccessorCheckpointPlan $f $cp $state;throw 'Expected wrong run rejection'}catch{Check ($_.Exception.Message -match 'binding missing or changed') 'Wrong predecessor run binding rejected'}
$state.run_id=$d.predecessor.run_id
$task.completed_operations=@();SaveTask
Check (-not(Get-ControllerTaskRegistrationPlan $f).dispatch_ready) 'Completed-operation protection cannot be reset by successor registration'
$task.completed_operations=@('package166_submitted_once');SaveTask
[IO.File]::AppendAllText((Join-Path $f $rel),'changed')
Check (-not(Get-ControllerTaskRegistrationPlan $f).dispatch_ready) 'Tampered task definition rejected'
Put $rel ($d|ConvertTo-Json -Depth 15)
Put 'evidence.json' '{"reported_physical_pass":true}'
Check (-not(Get-ControllerTaskRegistrationPlan $f).dispatch_ready) 'Changed scientific evidence requires requalification'
Put 'evidence.json' '{"reported_physical_pass":false}'
$hpcPin=(Get-FileHash (Join-Path $f 'project_coordination/HPC_JOB_LEDGER.csv')).Hash
$executionPin=(Get-FileHash (Join-Path $f 'project_coordination/MODE1_EXECUTION_LEDGER.json')).Hash
$again=Get-ControllerSuccessorCheckpointPlan $f $cp (Read-ControllerCheckpoint $cp)
Check ($again.fresh_successor -and (Get-FileHash $cp).Hash -ceq $pin) 'Repeated read-only recovery observes successor without consuming or replaying predecessor'
Check ((Get-FileHash (Join-Path $f 'project_coordination/HPC_JOB_LEDGER.csv')).Hash -ceq $hpcPin -and (Get-FileHash (Join-Path $f 'project_coordination/MODE1_EXECUTION_LEDGER.json')).Hash -ceq $executionPin) 'Successor/recovery/preflight leave once-only PBS receipts unchanged'
try{$null=Resolve-ControllerInstruction $f '# F1597: repeat predecessor';throw 'Expected predecessor rejection'}catch{Check ($_.Exception.Message -match 'COMPLETED_TASK_REJECTED') 'Closed predecessor remains rejected after successor registration'}
'ALL '+$script:n+' SUCCESSOR CHECKS PASS; fixture='+$f+'; zero AGY, PAD or HPC calls'
