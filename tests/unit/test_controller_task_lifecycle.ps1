$ErrorActionPreference='Stop'
$repo=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
. (Join-Path $repo 'scripts/controller/Controller-Recovery.ps1')
. (Join-Path $repo 'scripts/controller/Controller-Preparation.ps1')
. (Join-Path $repo 'scripts/controller/Controller-FailureHandoff.ps1')
$fixture=Join-Path $env:TEMP ('task-lifecycle-'+[guid]::NewGuid().ToString('N'))
[void][IO.Directory]::CreateDirectory((Join-Path $fixture 'project_coordination'))
$script:n=0
function Check($ok,$text){if(-not $ok){throw "FAIL $text"};$script:n++;"PASS $script:n $text"}
function Put($name,$text){[IO.File]::WriteAllText((Join-Path $fixture $name),$text)}
function Task($id,$status,$extra=@{}){
    $t=@{task_id=$id;status=$status;scientific_operation='';scientific_checkpoint_required=$true;completed_operations=@('submitted_once')}
    foreach($key in $extra.Keys){$t[$key]=$extra[$key]}
    Put 'project_coordination/ACTIVE_TASK.json' ($t|ConvertTo-Json -Depth 10)
}
Put 'project_coordination/ACTIVE_SESSION.json' '{"active":false,"agent":"codex"}'
Put 'project_coordination/CURRENT_STATE.md' 'Existing science retained; tests do not authorize a numerical run.'
Put 'project_coordination/HPC_JOB_LEDGER.csv' "job_id,status`n1419305.mmaster02,COMPLETED"
Put 'project_coordination/MODE1_EXECUTION_LEDGER.json' '{"attempts":1,"reserved_commands":["submitted_once"]}'
Put 'project_coordination/TASK_LEDGER.csv' "task_id,status,next_task`nF1597-CLOSED,completed,Complete bridge review and submit existing Package160"
Task 'F1597-CLOSED' 'PREPARATION_COMPLETE'
$life=Get-ControllerTaskLifecycle $fixture
Check ($life.terminal -and -not $life.preparation_is_terminal -and -not $life.dispatch_ready) 'Exact closed parent wins over a preparation checkpoint status'
Check ($life.transition -eq 'SUCCESSOR_REQUIRED' -and -not $life.next_authoritative_task) 'Prose next_task never becomes a fabricated task identity'
try{Assert-ControllerTaskLifecycle $fixture;throw 'Expected closed parent rejection'}catch{Check ($_.Exception.Message -match 'COMPLETED_TASK_REJECTED') 'Completed parent rejected before dispatch'}
$plan=Get-ControllerPreparationPlan $fixture "Writing`nReview existing evidence"
Check ($plan.status -eq 'TASK_SUCCESSOR_REQUIRED' -and -not $plan.dispatch_ready) 'An unlabelled instruction cannot dispatch or register a completed parent'
$resolution=Resolve-ControllerInstruction $fixture 'CONTROLLER_TASK: NEXT_UNRESOLVED'
Check (-not $resolution.dispatch_ready -and -not $resolution.next_authoritative_task) 'Task resolver cannot turn a closed predecessor into generic executable work'
Put 'project_coordination/TASK_LEDGER.csv' "task_id,status,next_task`nF1597-CLOSED,completed,F1600-EXISTING`nF1600-EXISTING,ready,"
$life=Get-ControllerTaskLifecycle $fixture
Check ($life.next_authoritative_task -eq 'F1600-EXISTING' -and $life.transition -eq 'SELECT_RECORDED_SUCCESSOR') 'Only exact existing open successor selected from recorded link'
Check (-not $life.dispatch_ready -and (Get-Content (Join-Path $fixture 'project_coordination/ACTIVE_TASK.json') -Raw|ConvertFrom-Json).task_id -eq 'F1597-CLOSED') 'Read-only successor selection does not activate it or reopen predecessor'
Put 'project_coordination/TASK_LEDGER.csv' "task_id,status,next_task`nF1597-CLOSED,completed,F1600-EXISTING`nF1600-EXISTING,ready,`nF1600-EXISTING,completed,"
Check (-not (Get-ControllerTaskLifecycle $fixture).next_authoritative_task) 'A historical exact closure prevents successor replay even after active rows'
Put 'project_coordination/TASK_LEDGER.csv' "task_id,status,next_task`nF1597-CLOSED,completed,F1600-EXISTING`nF1600-EXISTING,bounded_step_complete,"
Check (-not (Get-ControllerTaskLifecycle $fixture).next_authoritative_task) 'A completed bounded-operation row is not an open successor task'
Put 'project_coordination/TASK_LEDGER.csv' "task_id,status,next_task`nF1597-CLOSED,completed,F1600-EXISTING`nF1600-EXISTING,ready,"
Task 'F1600-EXISTING' 'PREPARATION_COMPLETE' @{predecessor_task=@{task_id='F1597-CLOSED';status='COMPLETED'}}
$life=Get-ControllerTaskLifecycle $fixture
Check (-not $life.terminal -and $life.dispatch_ready) 'Legitimate active successor remains active after preparation completion'
$resolved=Resolve-ControllerInstruction $fixture '# F1600: inspect existing successor evidence'
Assert-ControllerTaskLifecycle $fixture
Check ($resolved.evidence.task.task_id -eq 'F1600-EXISTING') 'Ordinary instruction resolution uses authoritative successor instead of closed predecessor'
try{$null=Resolve-ControllerInstruction $fixture '# F1597: repeat prior closed work';throw 'Expected predecessor rejection'}catch{Check ($_.Exception.Message -match 'COMPLETED_TASK_REJECTED') 'Completed predecessor remains rejected after successor selection'}
$t=Get-Content (Join-Path $fixture 'project_coordination/ACTIVE_TASK.json') -Raw|ConvertFrom-Json
$updated=Set-ControllerPreparationStepStatus $t 'PREPARATION_COMPLETE'
Check ($updated.status -eq 'ACTIVE' -and $updated.last_step_status -eq 'PREPARATION_COMPLETE' -and $updated.completed_operations -contains 'submitted_once') 'Closeout separates bounded step status from parent lifecycle and preserves operation accounting'
try{$null=Set-ControllerPreparationStepStatus ([pscustomobject]@{task_id='F1597-CLOSED';status='COMPLETED'}) 'PREPARATION_COMPLETE';throw 'Expected terminal rejection'}catch{Check ($_.Exception.Message -match 'COMPLETED_TASK_REJECTED') 'Preparation closeout cannot reopen an explicitly terminal parent'}
$s=New-ControllerTurnState (Get-ControllerEvidence $fixture) 35 'review preserved evidence'
$s.state='COMPLETED';$s|Add-Member -NotePropertyName next_instruction -NotePropertyValue 'Retain completed evidence; do not replay'
$checkpoint=Join-Path $fixture 'checkpoint.json';Write-ControllerCheckpoint $checkpoint $s
$pin=(Get-FileHash $checkpoint).Hash
$recovered=Read-ControllerCheckpoint $checkpoint
Check ($recovered.state -eq 'COMPLETED' -and (Get-FileHash $checkpoint).Hash -eq $pin) 'Interruption/restart observes completed checkpoint without rewriting it'
Check ((Get-ControllerTaskLifecycle $fixture).next_authoritative_task -eq 'F1600-EXISTING') 'Restart task selection remains deterministic'
$source=Get-Content (Join-Path $repo 'scripts/controller/Invoke-ControllerTurn.ps1') -Raw
Check ($source.Contains('Assert-ControllerTaskLifecycle $Workspace') -and $source.Contains('Set-ControllerPreparationStepStatus') -and -not $source.Contains('$task.status=if($payload.status)')) 'Bootstrap and closeout use lifecycle guard and never overwrite parent status from payload'
Check ((Test-ControllerTaskTerminalStatus 'COMPLETED') -and -not(Test-ControllerTaskTerminalStatus 'PREPARATION_COMPLETE') -and -not(Test-ControllerTaskTerminalStatus 'bounded_step_complete')) 'Parent terminal and bounded-checkpoint statuses have explicit distinct semantics'
"ALL $script:n LIFECYCLE CHECKS PASS; fixtures=$fixture; zero AGY, bridge or HPC calls"
