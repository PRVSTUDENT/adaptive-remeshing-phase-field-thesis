$ErrorActionPreference='Stop'
$repo=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
. "$repo/scripts/controller/Controller-Recovery.ps1"
. "$repo/scripts/validation/Invoke-BoundedAgyProcess.ps1"
. "$repo/scripts/validation/ConvertFrom-AgyEnvelope.ps1"
$dir=Join-Path $env:TEMP ('agy-progress-test-'+[guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path "$dir/project_coordination/sessions" -Force|Out-Null
$script:checks=0
function Assert($Value,[string]$Message){if(-not $Value){throw "FAIL: $Message"};$script:checks++;"PASS $script:checks`: $Message"}
function Put($Relative,$Text){[IO.File]::WriteAllText((Join-Path $dir $Relative),$Text)}
function Session($Task='F1596-AUDIT',$Agent='gemini-antigravity',$Active=$false,$Claim='2020-01-01T00:00:00Z'){
    Put 'project_coordination/ACTIVE_SESSION.json' (@{active=$Active;agent=$Agent;task_id=$Task;claimed_at=$Claim;starting_commit='abc';last_updated=$Claim;session_report='project_coordination/sessions/review.md'}|ConvertTo-Json)
}
try{
    Put 'project_coordination/ACTIVE_TASK.json' '{"task_id":"F1596-AUDIT","status":"COMPLETED_FAIL"}'
    Put 'project_coordination/CURRENT_STATE.md' 'Package72 failed. No dependent continuation.'
    Put 'project_coordination/HPC_JOB_LEDGER.csv' "job_id,status`n1415199.mmaster02,completed"
    Put 'project_coordination/MODE1_EXECUTION_LEDGER.json' '{"reserved":1,"id":"1415199.mmaster02"}'
    Put 'project_coordination/TASK_LEDGER.csv' "task_id,status`nF1596-AUDIT,completed"
    Session
    $cp=Join-Path $dir 'state.json';$e=Get-ControllerEvidence $dir
    $s=New-ControllerTurnState $e 1 'next';$s.repository_commit='abc'
    Session 'F1597-NEW-REVIEW' 'gemini-antigravity' $true ([datetimeoffset]::UtcNow.AddSeconds(1).ToString('o'))
    Update-ControllerEvidence $dir $cp $s
    Assert ($s.task_id -eq 'F1597-NEW-REVIEW' -and $s.predecessor_task_id -eq 'F1596-AUDIT' -and $s.owned_session_fingerprint) 'exact live failure reproduced: new session binds independently of completed predecessor'
    $loaded=Read-ControllerCheckpoint $cp
    $loaded=Set-ControllerInterrupted $dir $cp $loaded 'actual raw tool/result evidence'
    Assert ($loaded.state -eq 'RECOVERY_REQUIRED' -and -not(Get-ControllerEvidence $dir).session.active -and $loaded.task_id -eq 'F1597-NEW-REVIEW') 'restart and timeout release verified F1597 while ACTIVE_TASK still names F1596'
    Assert ((Get-Content -LiteralPath $loaded.partial_output -Raw) -eq 'actual raw tool/result evidence') 'recovery stores genuine raw output instead of synthesized timeout envelope'
    Session
    $s=New-ControllerTurnState (Get-ControllerEvidence $dir) 1 'next';$s.repository_commit='abc'
    Session 'F1597-NEW-REVIEW' 'grok' $true ([datetimeoffset]::UtcNow.AddSeconds(1).ToString('o'))
    $s=Set-ControllerInterrupted $dir $cp $s 'raw'
    Assert ($s.state -eq 'BLOCKED' -and (Get-ControllerEvidence $dir).session.active) 'foreign active agent remains protected'
    Session
    $s=New-ControllerTurnState (Get-ControllerEvidence $dir) 1 'next'
    Assert (-not(Test-ControllerDurableProgress $s)) 'initial metadata creates baseline, not progress'
    Session 'F1597-NEW-REVIEW' 'gemini-antigravity' $true ([datetimeoffset]::UtcNow.AddSeconds(1).ToString('o'))
    Update-ControllerEvidence $dir $cp $s
    Assert (-not(Test-ControllerDurableProgress $s)) 'session claim and heartbeat do not reset no-result deadline'
    Put 'project_coordination/sessions/review.md' ('Finding: verified checkpoint and input provenance; source models/package72; force continuity remains failed. '*3)
    Update-ControllerEvidence $dir $cp $s
    Assert (Test-ControllerDurableProgress $s) 'saved evidence report resets no-result deadline'
    Assert (-not(Test-ControllerDurableProgress $s)) 'unchanged evidence does not manufacture ongoing progress'
    Session
    $s=New-ControllerTurnState (Get-ControllerEvidence $dir) 1 'next'
    [void](Test-ControllerDurableProgress $s)
    Remove-Item -LiteralPath (Join-Path $dir 'project_coordination/sessions/review.md')
    Session 'F1597-NO-REPORT' 'gemini-antigravity' $true ([datetimeoffset]::UtcNow.AddSeconds(1).ToString('o'))
    Update-ControllerEvidence $dir $cp $s
    Assert (-not(Test-ControllerDurableProgress $s)) 'removing predecessor report or claiming a task does not count as a saved result'
    $raw=@'
{"event":"init","conversation_id":"real-schema"}
{"event":"step_update","step_update":{"step_index":1,"state":"DONE","step_type":"error_message"}}
{"event":"result","result":{"conversation_id":"real-schema","status":"ERROR","response":"","error":"Individual quota reached. Resets in 98h24m26s."}}
'@
    $result=ConvertFrom-AgyEnvelope (ConvertFrom-ControllerStream $raw)
    Assert ($result.conversation_id -eq 'real-schema' -and $result.error -match 'Individual quota reached') 'actual CLI NDJSON event/result schema preserves quota failures'
    $result=ConvertFrom-AgyEnvelope (ConvertFrom-ControllerStream '{"event":"result","result":{"conversation_id":"normal","status":"SUCCESS","response":"Finished"}}')
    Assert ($result.status -eq 'SUCCESS' -and $result.response -eq 'Finished') 'normal streamed final response reaches existing completion checks'
    $partial='{"event":"init","conversation_id":"partial-live"}'+"`n[agy] print timeout returning partial output"
    $result=ConvertFrom-AgyEnvelope (ConvertFrom-ControllerStream $partial)
    Assert ($result.conversation_id -eq 'partial-live' -and -not $result.response) 'CLI partial-stream timeout enters reconciliation without inventing a final response'
    Write-ControllerStreamEvent $s ($raw+"`n")
    Assert ($s.conversation_id -eq 'real-schema') 'conversation identity captured before final model response'
    $mock=Join-Path $dir 'chatter.ps1';$live=Join-Path $dir 'live.jsonl'
    [IO.File]::WriteAllText($mock,'$null=[Console]::In.ReadToEnd(); for($i=0;$i -lt 100;$i++){[Console]::Out.WriteLine(''{"event":"step_update","step_update":{"step_type":"thinking"}}''); Start-Sleep -Milliseconds 100}')
    $seen=[Collections.Generic.List[int]]::new()
    $r=Invoke-BoundedAgyProcess -FilePath "$PSHOME/powershell.exe" -ArgumentList @('-NoProfile','-NonInteractive','-File',$mock) -InputText test -TimeoutSeconds 15 -NoProgressSeconds 2 -CheckpointIntervalSeconds 1 -StatusIntervalSeconds 1 -OutputLogPath $live -OnOutput {param($chunk) if(Test-Path -LiteralPath $live){$seen.Add(1)}}
    Assert ($r.StopReason -eq 'NO_DURABLE_PROGRESS' -and $r.TimedOut -and $r.DurationSeconds -lt 14) 'continuous model chatter cannot evade no-result deadline'
    Assert ($seen.Count -gt 0 -and (Get-Content -LiteralPath $live -Raw) -match 'step_update') 'raw event log is available during execution, not only after timeout'
    Session
    $s=New-ControllerTurnState (Get-ControllerEvidence $dir) 1 'next';$s.stop_reason='NO_DURABLE_PROGRESS'
    $s=Set-ControllerInterrupted $dir $cp $s $r.Output
    Assert ($s.state -eq 'BLOCKED' -and $s.block_reason -match 'No durable result') 'no-result stall stops explicitly with no automatic model replay'
    $r=Resolve-ControllerInstruction $dir 'CONTROLLER_TASK: NEXT_UNRESOLVED'
    Assert ($r.instruction -match 'Immediately execute independently ready qualified' -and $r.instruction -notmatch 'Do not implement changed scientific assumptions or submit dependent jobs during this review') 'job-first policy restored without bypassing scientific predecessor review'
    $r=Invoke-BoundedAgyProcess -FilePath "$PSHOME/powershell.exe" -ArgumentList @('-NoProfile','-NonInteractive','-Command','[Console]::Out.Write(''partial-without-newline''); Start-Sleep -Seconds 20') -TimeoutSeconds 5 -NoProgressSeconds 1 -OutputLogPath (Join-Path $dir 'partial.log')
    Assert ($r.Output -match 'partial-without-newline' -and $r.StopReason -eq 'NO_DURABLE_PROGRESS') 'partial lines survive early termination'
    # Invoke the actual production dispatch AST with an isolated model stand-in.
    Session
    $integration=Join-Path $dir 'claim-next-task.ps1'
    $integrationCode='$null=[Console]::In.ReadToEnd(); $s=@{active=$true;agent=''gemini-antigravity'';task_id=''F1597-INTEGRATION'';starting_commit=''abc'';claimed_at=[datetimeoffset]::UtcNow.ToString(''o'');last_updated=[datetimeoffset]::UtcNow.ToString(''o'');session_report=''project_coordination/sessions/missing.md''}; [IO.File]::WriteAllText('''+(Join-Path $dir 'project_coordination/ACTIVE_SESSION.json')+''',($s|ConvertTo-Json)); [Console]::Out.WriteLine(''{"event":"init","conversation_id":"integration-owned"}''); Start-Sleep -Seconds 20'
    [IO.File]::WriteAllText($integration,$integrationCode)
    $tokens=$null;$errors=$null
    $ast=[Management.Automation.Language.Parser]::ParseFile("$repo/scripts/controller/Antigravity-Autonomous-Loop.ps1",[ref]$tokens,[ref]$errors)
    $dispatch=$ast.Find({param($n)$n -is [Management.Automation.Language.AssignmentStatementAst] -and $n.Left.Extent.Text -eq '$boundedRun'},$true)
    $script:ControllerState=New-ControllerTurnState (Get-ControllerEvidence $dir) 1 'qualified next task';$script:ControllerState.repository_commit='abc'
    $WorkspaceDir=$dir;$controllerCheckpointPath=$cp;$AgyPath="$PSHOME/powershell.exe";$agyArgs=@('-NoProfile','-NonInteractive','-Command',$integrationCode);$EffectiveInstruction='fixture';$hardTimeout=10;$NoProgressSeconds=2;$livePath=Join-Path $dir 'production-dispatch.jsonl'
    [void](Test-ControllerDurableProgress $script:ControllerState)
    . ([scriptblock]::Create($dispatch.Extent.Text))
    $script:ControllerState.stop_reason=$boundedRun.StopReason
    $script:ControllerState=Set-ControllerInterrupted $dir $cp $script:ControllerState $boundedRun.Output
    Assert ($script:ControllerState.task_id -eq 'F1597-INTEGRATION' -and -not(Get-ControllerEvidence $dir).session.active) 'production dispatch callbacks capture/release newly claimed task independently of predecessor'
    Assert ($script:ControllerState.block_reason -match 'No durable result' -and $script:ControllerState.conversation_id -eq 'integration-owned') 'production callbacks stop stalled live stream with explicit reason and conversation receipt'
    "ALL $script:checks PROGRESS/OWNERSHIP CHECKS PASSED; no scientific jobs"
}finally{"EVIDENCE_FIXTURE=$dir"}
