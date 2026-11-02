$ErrorActionPreference='Stop'
$repo=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
. (Join-Path $repo 'scripts/controller/Controller-Recovery.ps1')
. (Join-Path $repo 'scripts/controller/Controller-Supervisor.ps1')
. (Join-Path $repo 'scripts/controller/Controller-Preparation.ps1')
. (Join-Path $repo 'scripts/controller/Controller-FailureHandoff.ps1')
$fixture=Join-Path ([IO.Path]::GetTempPath()) ('controller-failure-'+[guid]::NewGuid().ToString('N'))
[void][IO.Directory]::CreateDirectory((Join-Path $fixture 'project_coordination'))
$root=Join-Path $fixture 'packets';$checkpoint=Join-Path $fixture 'checkpoint.json'
$script:n=0;$script:sends=0
function Check($ok,$message){if(-not $ok){throw "FAIL $message"};$script:n++;"PASS $script:n $message"}
function Put($rel,$text){[IO.File]::WriteAllText((Join-Path $fixture $rel),$text)}
Put 'project_coordination/ACTIVE_TASK.json' '{"task_id":"F1597-TRUSTED-REVIEW-BOUNDARY-AND-PACKAGE160","status":"PREPARATION_COMPLETE"}'
Put 'project_coordination/ACTIVE_SESSION.json' '{"active":false,"agent":"gemini-antigravity"}'
Put 'project_coordination/CURRENT_STATE.md' 'Retain results. Scientific acceptance not established by controller recovery.'
Put 'project_coordination/TASK_LEDGER.csv' "task_id,status`nF1597-TRUSTED-REVIEW-BOUNDARY-AND-PACKAGE160,completed"
Put 'project_coordination/HPC_JOB_LEDGER.csv' "job_id,status`n1419305.mmaster02,COMPLETED"
Put 'project_coordination/MODE1_EXECUTION_LEDGER.json' '{"attempts":1,"pbs_id":"1419305.mmaster02"}'
Put 'artifact.json' '{"status":"PREPARATION_COMPLETE","scientific_acceptance":false}'
$state=[pscustomobject]@{schema=1;run_id='turn35-injection';turn=35;task_id='F1597-TRUSTED-REVIEW-BOUNDARY-AND-PACKAGE160';operation_id='research_preparation';state='COMPLETED';recovery_count=0;updated_at='';reconciliation=@{deliverables=@('artifact.json')}}
Write-ControllerCheckpoint $checkpoint $state
$pin=(Get-FileHash -LiteralPath $checkpoint).Hash
$mock={param($prompt,$id) $script:sends++;@{correlation_id=$id;action='DIAGNOSE';instruction='Reconcile the authoritative active task against the completed ledger without repeating any operation.'}|ConvertTo-Json}
# Exact original resolver failure, handled through the production durable boundary.
try{$null=Resolve-ControllerInstruction $fixture 'Advance F1597-TRUSTED-REVIEW-BOUNDARY-AND-PACKAGE160: Proceed to next numerical operation';throw 'Expected rejection did not occur'}
catch{if($_.Exception.Message -notmatch 'COMPLETED_TASK_REJECTED: F1597'){throw};$r=Invoke-ControllerFailureHandoff $fixture $checkpoint $state ($_|Out-String) -Root $root -Transport $mock}
Check ($r.status -eq 'RECOVERY_ACKNOWLEDGED_VALIDATION_REQUIRED') 'Exact Turn35 completed-task exception becomes an acknowledged ChatGPT-bound packet'
$p=Get-Content (Join-Path $r.packet 'packet.json') -Raw|ConvertFrom-Json
Check ($p.task_identity_conflict -and $p.original_task -eq $p.resolved_active_task) 'Active-file versus completed-ledger conflict is explicit; task is not reactivated'
Check ($p.recovered_artifacts[0].sha256 -eq (Get-FileHash (Join-Path $fixture 'artifact.json')).Hash) 'Recovered deliverable hash preserved'
Check ((Get-FileHash $checkpoint).Hash -eq $pin) 'Completed checkpoint remains byte-identical after later controller failure'
$again=Invoke-ControllerFailureHandoff $fixture $checkpoint $state 'second observation' -Root $root -Transport $mock
Check ($script:sends -eq 1 -and $again.status -eq 'RECOVERY_ALREADY_RECORDED_NO_REDISPATCH') 'Restart or duplicate observer cannot send a second recovery'
try{$null=Test-ControllerFailureResumePlan $fixture $r.packet;throw 'Unsafe resume accepted'}catch{Check ($_.Exception.Message -match 'TASK_IDENTITY_RECONCILIATION_REQUIRED') 'Reply cannot bypass completed task identity guard'}
try{Assert-ControllerActiveTaskDispatch $fixture;throw 'Completed task accepted without heading'}catch{Check ($_.Exception.Message -match 'COMPLETED_TASK_REJECTED') 'A heading without F1597 cannot bypass the exact active-task ledger check'}
$state.run_id='watchdog'
$bad={param($prompt,$id) throw 'simulated bridge unavailable'}
$r2=Invoke-ControllerFailureHandoff $fixture $checkpoint $state 'WATCHDOG_TIMEOUT; recovered progress retained' -Root $root -Transport $bad
Check ($r2.status -eq 'RECOVERY_PENDING_TRANSPORT' -and (Test-Path (Join-Path $r2.packet 'pending.json'))) 'Watchdog and bridge failure persist as pending evidence'
$again=Invoke-ControllerFailureHandoff $fixture $checkpoint $state 'retry' -Root $root -Transport $mock
Check ($script:sends -eq 1) 'Failed bridge transaction is never automatically resent'
$state.run_id='stale-task';$state.task_id='F1596-OLD'
$r3=Invoke-ControllerFailureHandoff $fixture $checkpoint $state 'task validation failed' -Root $root -NoTransport
$p3=Get-Content (Join-Path $r3.packet 'packet.json') -Raw|ConvertFrom-Json
Check ($p3.original_task -eq 'F1596-OLD' -and $p3.resolved_active_task -eq 'F1597-TRUSTED-REVIEW-BOUNDARY-AND-PACKAGE160') 'Stale owned task and authoritative task remain distinct'
Check ($p3.pbs_references -contains '1419305.mmaster02' -and $p3.scheduler_observation -like 'Ledger*') 'PBS references are preserved without invented live scheduler status'
$state.run_id='wrong-reply'
$r4=Invoke-ControllerFailureHandoff $fixture $checkpoint $state 'completion sync error' -Root $root -Transport {param($prompt,$id)'{"correlation_id":"stale","action":"CONTINUE","instruction":"repeat"}'}
Check ($r4.status -eq 'RECOVERY_PENDING_TRANSPORT' -and -not(Test-Path (Join-Path $r4.packet 'acknowledged.json'))) 'Wrong correlation cannot acknowledge or resume'
$source=Get-Content (Join-Path $repo 'scripts/controller/Antigravity-Autonomous-Loop.ps1') -Raw
$tokens=$null;$errors=$null;$ast=[Management.Automation.Language.Parser]::ParseInput($source,[ref]$tokens,[ref]$errors)
Check (-not $errors) 'Controller parses after common failure-boundary integration'
$handlers=@($ast.FindAll({param($a)$a -is [Management.Automation.Language.TryStatementAst] -and $a.CatchClauses.Extent.Text -match 'Invoke-ControllerFailureHandoff'},$true))
Check ($handlers.Count -gt 0) 'Production main try/catch calls the same tested boundary'
Check ($source -match 'RECOVERED_TURN_REVIEW_REQUIRED' -and $source.Contains("if(`$Status -eq 'FAILED')")) 'Recovered-success and recorded-failure paths are routed to the boundary'
# Execute the actual production catch with the real rejecting resolver; only transport is injected.
$script:productionBoundary=(Get-Command Invoke-ControllerFailureHandoff).ScriptBlock
function Invoke-ControllerFailureHandoff {
    param($Workspace,$CheckpointPath,$State,$ErrorText,$Stage,[switch]$NoTransport,[switch]$LaunchPad)
    $script:injectedOutcome=& $script:productionBoundary @PSBoundParameters -Root (Join-Path $fixture 'production-catch') -Transport $mock
    return $script:injectedOutcome
}
$WorkspaceDir=$fixture;$controllerCheckpointPath=$checkpoint;$EnableChatGPTBridge=$true;$ChatGPTBridgeLaunchPad=$false
$script:ControllerState=$state;$script:ControllerState.run_id='exact-production-catch'
$mainCatch=@($handlers | Where-Object {$_.CatchClauses.Extent.Text -match "Stage 'main_controller'"})[0].CatchClauses[0].Extent.Text
$fault="try { `$null=Resolve-ControllerInstruction `$WorkspaceDir 'Advance F1597-TRUSTED-REVIEW-BOUNDARY-AND-PACKAGE160: Proceed to next numerical operation' } "+$mainCatch
Invoke-Expression $fault
Check ($script:injectedOutcome.status -eq 'RECOVERY_ACKNOWLEDGED_VALIDATION_REQUIRED' -and $script:ControllerFailureHandled) 'Production catch contains exact Turn35 fault without an uncaught exception'
"ALL $script:n FAILURE HANDOFF CHECKS PASS; fixtures=$fixture; no live bridge, AGY or HPC calls"
