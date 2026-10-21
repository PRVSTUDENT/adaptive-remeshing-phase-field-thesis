$ErrorActionPreference='Stop'
$repo=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
. (Join-Path $repo 'scripts/controller/Controller-Recovery.ps1')
. (Join-Path $repo 'scripts/validation/Invoke-BoundedAgyProcess.ps1')
. (Join-Path $repo 'scripts/validation/ConvertFrom-AgyEnvelope.ps1')
. (Join-Path $repo 'scripts/validation/AgyControllerPolicy.ps1')
$fixture=Join-Path ([IO.Path]::GetTempPath()) ('agy-controller-test-'+[guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path (Join-Path $fixture 'project_coordination/sessions') -Force|Out-Null
$count=0
function Assert($Condition,[string]$Message) { if (-not $Condition) { throw "FAIL: $Message" }; $script:count++; "PASS $script:count`: $Message" }
function Put([string]$Relative,[string]$Text) { [IO.File]::WriteAllText((Join-Path $fixture $Relative),$Text,[Text.UTF8Encoding]::new($false)) }
function Set-Session([bool]$Active=$false,[string]$Agent='gemini-antigravity',[string]$Claim='2020-01-01T00:00:00Z') {
    Put 'project_coordination/ACTIVE_SESSION.json' (@{active=$Active;agent=$Agent;task_id='F1596-AUDIT';claimed_at=$Claim;last_updated=$Claim;session_report='project_coordination/sessions/audit.md'}|ConvertTo-Json)
}
try {
    Put 'project_coordination/ACTIVE_TASK.json' '{"task_id":"F1596-AUDIT","status":"AUDIT_COMPLETED_CLASSIFIED_FAIL"}'
    Set-Session
    Put 'project_coordination/CURRENT_STATE.md' 'Package72 scientific failure; preserve quantitative evidence.'
    Put 'project_coordination/TASK_LEDGER.csv' "task_id,status`nF1596-AUDIT,completed"
    Put 'project_coordination/HPC_JOB_LEDGER.csv' "job_id,status`n1415199.mmaster02,Exit0_scientific_FAIL"
    Put 'project_coordination/MODE1_EXECUTION_LEDGER.json' '{"reserved_commands":["job72"],"pbs_id":"1415199.mmaster02","attempts":1}'
    Put 'project_coordination/sessions/audit.md' 'Existing completed audit. No repeated audit or new submission.'
    $path=Join-Path $fixture 'checkpoint.json'
    $rejected=$false;try{$null=Resolve-ControllerInstruction $fixture '# Antigravity F1596: repeat audit'}catch{$rejected=$_.Exception.Message -match 'COMPLETED_TASK_REJECTED'}
    Assert $rejected 'completed F1596 rejected before model invocation'
    $resolved=Resolve-ControllerInstruction $fixture 'CONTROLLER_TASK: NEXT_UNRESOLVED'
    $e=$resolved.evidence
    $s=New-ControllerTurnState $e 1 $resolved.instruction
    Write-ControllerCheckpoint $path $s
    Assert ((Read-ControllerCheckpoint $path).state -eq 'PENDING') 'atomic checksum-protected checkpoint round trip'
    $s.state='RUNNING'; Write-ControllerCheckpoint $path $s
    $s=Set-ControllerInterrupted $fixture $path $s 'partial measured evidence'
    Assert ($s.state -eq 'RECOVERY_REQUIRED' -and (Test-Path -LiteralPath $s.partial_output) -and (Get-Content -LiteralPath $s.partial_output -Raw) -eq 'partial measured evidence') 'timeout preserves partial bytes and creates safe recovery state'
    Assert ($s.pbs_receipts -contains '1415199.mmaster02' -and $s.execution_accounting.attempts -eq 1) 'actual PBS receipts and reserved submission count preserved'
    $recovery=Get-ControllerRecoveryInstruction $s
    Assert ($recovery -match 'No qsub, Mode1Execution' -and $recovery -notmatch 'repeat audit') 'recovery instruction resumes evidence only without original submission replay'
    $s=New-ControllerTurnState $e 2 $recovery 1
    $s=Set-ControllerInterrupted $fixture $path $s 'second timeout'
    Assert ($s.state -eq 'BLOCKED' -and $s.block_reason -match 'already used') 'repeated timeout is bounded and explicitly BLOCKED'
    $s=New-ControllerTurnState $e 3 'review'
    Set-Session $true 'grok'
    $s=Set-ControllerInterrupted $fixture $path $s 'partial'
    Assert ($s.state -eq 'BLOCKED' -and (Get-ControllerEvidence $fixture).session.active) 'foreign active session preserved and recovery blocked'
    Set-Session
    $s=New-ControllerTurnState (Get-ControllerEvidence $fixture) 4 'review'
    Set-Session $true 'gemini-antigravity' ([DateTimeOffset]::UtcNow.AddSeconds(1).ToString('o'))
    $s=Set-ControllerInterrupted $fixture $path $s 'owned partial'
    Assert ($s.state -eq 'RECOVERY_REQUIRED' -and -not (Get-ControllerEvidence $fixture).session.active) 'owned interrupted session released while preserving its fields'
    $budget=Get-ControllerBudget '2400s' 2400
    Assert ($budget.work -eq 2280 -and $budget.closeout -eq 120 -and $budget.total -eq 2400) 'controller work deadline reserves local closeout without extending timeout'
    # Real Windows child processes stand in for AGY; PBS data above is a durable fixture.
    $mock=Join-Path $fixture 'mock-agy.ps1'
    [IO.File]::WriteAllText($mock,'[Console]::Out.WriteLine(''{"conversation_id":"mock","status":"SUCCESS","response":"verified existing evidence\nFinished"}'')')
    $before=(Get-ControllerEvidence $fixture).sources['project_coordination/HPC_JOB_LEDGER.csv']
    $completed=0
    for($turn=1;$turn -le 20;$turn++) {
        $s=New-ControllerTurnState (Get-ControllerEvidence $fixture) $turn 'mock next instruction'
        $s.state='RUNNING'; Write-ControllerCheckpoint $path $s
        $r=Invoke-BoundedAgyProcess -FilePath "$PSHOME/powershell.exe" -ArgumentList @('-NoProfile','-NonInteractive','-File',$mock) -TimeoutSeconds 10 -WorkingDirectory $fixture
        if($r.ExitCode -ne 0 -or $r.TimedOut){throw 'Mock process failed'}
        $obj=ConvertFrom-AgyEnvelope $r.Output
        if((Complete-ControllerTurn $fixture $path $s $obj.response) -ne 'COMPLETED'){throw 'Mock completion failed'}
        $completed++
    }
    Assert ($completed -eq 20 -and (Read-ControllerCheckpoint $path).turn -eq 20 -and (Read-ControllerCheckpoint $path).state -eq 'COMPLETED') 'twenty mocked AGY lifecycle turns complete cleanly with next instructions'
    Assert ((Get-ControllerEvidence $fixture).sources['project_coordination/HPC_JOB_LEDGER.csv'] -eq $before) 'successful recovery/lifecycle never changes PBS submission ledger'
    $pidPath=Join-Path $fixture 'child-pid.txt'
    $mockTimeout=Join-Path $fixture 'mock-timeout.ps1'
    [IO.File]::WriteAllText($mockTimeout,('[IO.File]::WriteAllText('''+$pidPath+''',[string]$PID); [Console]::Out.WriteLine(''partial output before deadline''); Start-Sleep -Seconds 30'))
    $ticks=[System.Collections.Generic.List[int]]::new()
    $r=Invoke-BoundedAgyProcess -FilePath "$PSHOME/powershell.exe" -ArgumentList @('-NoProfile','-NonInteractive','-Command',(Get-Content -LiteralPath $mockTimeout -Raw)) -TimeoutSeconds 8 -WorkingDirectory $fixture -CheckpointIntervalSeconds 1 -Checkpoint { $ticks.Add(1) }
    if(-not(Test-Path -LiteralPath $pidPath)){throw "Mock child did not initialize: $($r|ConvertTo-Json -Compress)"}
    $ownedPid=[int](Get-Content -LiteralPath $pidPath)
    "WATCHDOG_RESULT="+($r|ConvertTo-Json -Compress)+" checkpoints=$($ticks.Count) owned_pid=$ownedPid alive=$([bool](Get-Process -Id $ownedPid -ErrorAction SilentlyContinue))"
    Assert ($r.TimedOut -and $r.Output -match 'partial output before deadline' -and $ticks.Count -ge 1 -and -not (Get-Process -Id $ownedPid -ErrorAction SilentlyContinue)) 'watchdog preserves partial stdout, checkpoints periodically and leaves no owned process'
    $childPidPath=Join-Path $fixture 'descendant-pid.txt'
    $treeMock=Join-Path $fixture 'mock-process-tree.ps1'
    $treeCode='$null=[Console]::In.ReadToEnd(); $child=Start-Process -FilePath "$PSHOME/powershell.exe" -ArgumentList ''-NoProfile -NonInteractive -Command "Start-Sleep -Seconds 60"'' -WindowStyle Hidden -PassThru; [IO.File]::WriteAllText('''+$childPidPath+''',[string]$child.Id); [Console]::Out.WriteLine(''tree ready''); Start-Sleep -Seconds 60'
    [IO.File]::WriteAllText($treeMock,$treeCode)
    $treeResult=Invoke-BoundedAgyProcess -FilePath "$PSHOME/powershell.exe" -ArgumentList @('-NoProfile','-NonInteractive','-Command',(Get-Content -LiteralPath $treeMock -Raw)) -InputText 'mock research' -TimeoutSeconds 6 -WorkingDirectory $fixture
    if(-not(Test-Path -LiteralPath $childPidPath)){throw 'Tree mock did not initialize'}
    $descendantPid=[int](Get-Content -LiteralPath $childPidPath)
    Assert ($treeResult.TimedOut -and $treeResult.Output -match 'tree ready' -and -not(Get-Process -Id $descendantPid -ErrorAction SilentlyContinue)) 'watchdog kills owned descendants as well as root without orphaned processes'
    # Execute the production timeout AST against fixtures; all external effects are stubs.
    $tokens=$null; $errors=$null
    $source=Join-Path $repo 'scripts/controller/Antigravity-Autonomous-Loop.ps1'
    $ast=[Management.Automation.Language.Parser]::ParseFile($source,[ref]$tokens,[ref]$errors)
    Assert ($errors.Count -eq 0) 'canonical installed controller has valid PowerShell syntax'
    $node=$ast.Find({param($n) $n -is [Management.Automation.Language.IfStatementAst] -and $n.Extent.Text.StartsWith("if (`$agyText -match '(?i)\[agy\] print timeout")},$true)
    function Get-AgyCompletedReceipt { return $null }
    function Save-LoopState { }
    function Write-LoopLog { }
    $WorkspaceDir=$fixture; $controllerCheckpointPath=$path; $script:ControllerState=New-ControllerTurnState (Get-ControllerEvidence $fixture) 1 'original must not replay'
    $CurrentTurn=1; $ConversationId='old'; $agyText='[agy] print timeout returning partial output'; $turnStartTime=[DateTimeOffset]::UtcNow; $turnDurationSeconds=3; $CurrentInstruction='original must not replay'
    $script:ControllerRecoveryMode=$false
    $code=':MainLoop while ($CurrentTurn -le 1) {' + $node.Extent.Text + '; throw "timeout branch failed to advance" }'
    . ([scriptblock]::Create($code))
    Assert ($CurrentTurn -eq 2 -and $script:ControllerRecoveryMode -and $null -eq $ConversationId -and $CurrentInstruction -match 'EVIDENCE_ONLY_RECOVERY') 'actual production timeout handler advances to fresh recovery turn instead of exiting/replaying'
    $script:ControllerState=New-ControllerTurnState (Get-ControllerEvidence $fixture) 2 'recover' 1
    $CurrentTurn=2
    . ([scriptblock]::Create(':MainLoop while ($true) {'+$node.Extent.Text+'; throw "unexpected retry" }'))
    Assert ($script:ControllerState.state -eq 'BLOCKED' -and $CurrentTurn -eq 2) 'production timeout handler stops second failed recovery explicitly'
    $loop=$ast.Find({param($n) $n -is [Management.Automation.Language.WhileStatementAst] -and $n.Label -eq 'MainLoop'},$true)
    $StartTurn=1; $MaxTurns=20; $CurrentTurn=1; $script:loopCalls=0
    . ([scriptblock]::Create('while ('+$loop.Condition.Extent.Text+') { $script:loopCalls++; $CurrentTurn++ }'))
    Assert ($script:loopCalls -eq 20 -and $CurrentTurn -eq 21) 'actual production loop condition terminates exactly after twenty successful turns'
    $s=New-ControllerTurnState (Get-ControllerEvidence $fixture) 1 'review'
    Assert ((Complete-ControllerTurn $fixture $path $s 'BLOCKED: evidence missing') -eq 'BLOCKED') 'blocked/incomplete model response cannot count as completion'
    $s=New-ControllerTurnState (Get-ControllerEvidence $fixture) 1 'review'
    Assert ((Complete-ControllerTurn $fixture $path $s 'Authentic completed session report without marker' -VerifiedReceipt) -eq 'COMPLETED') 'verified completed receipt preserves work even without Finished marker'
    $s=Set-ControllerInterrupted $fixture $path $s 'trusted partial'
    [IO.File]::AppendAllText($s.partial_output,'tampered')
    $failed=$false; try {$null=Get-ControllerRecoveryInstruction $s}catch{$failed=$_.Exception.Message -match 'modified recovery'}
    Assert $failed 'modified partial evidence fails closed before recovery instruction'
    [IO.File]::WriteAllText($path,'{"schema":1,"payload":"{}","sha256":"corrupt"}')
    $failed=$false; try {$null=Read-ControllerCheckpoint $path}catch{$failed=$_.Exception.Message -match 'corrupted'}
    Assert $failed 'corrupted checkpoint fails closed'
    Assert (-not (Test-AgyQuotaHeadroom @{long_remaining_pct=90;five_h_remaining_pct=0})) 'exhausted quota fails closed'
    $text=Get-Content -LiteralPath $source -Raw
    Assert ($text.Contains('Set-AndVerifyAgyRunProfile "PRE_AGY"') -and $text.Contains('Set-AndVerifyAgyRunProfile "POST_AGY"') -and $text.Contains('$controllerMutex.ReleaseMutex()')) 'strict credentials and single-controller mutex release remain in production path'
    $idxPending = $text.IndexOf("`$script:ControllerState.state='PENDING'")
    $idxTurnEnd = $text.IndexOf('Ensure-AuthoritativeAgyProfile "TURN_END"')
    Assert ($idxPending -gt 0 -and $idxTurnEnd -gt $idxPending) 'PENDING next turn checkpoint is written before TURN_END profile verification'
    $lockName='Local\AgyControllerTest-'+[guid]::NewGuid().ToString('N')
    $mutex=[Threading.Mutex]::new($false,$lockName)
    try { Assert ($mutex.WaitOne(0)) 'test mutex acquired'; $mutex.ReleaseMutex() }
    finally { $mutex.Dispose() }
    $mutex=[Threading.Mutex]::new($false,$lockName)
    try { Assert ($mutex.WaitOne(0)) 'no abandoned controller lock remains after release'; $mutex.ReleaseMutex() }
    finally { $mutex.Dispose() }
    "ALL $count CONTROLLER RECOVERY CHECKS PASSED; no real AGY or PBS calls"
} finally {
    # Keep fixture evidence available for diagnosing failures; do not recursively delete.
    "TEST_FIXTURE=$fixture"
}
