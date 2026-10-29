$ErrorActionPreference='Stop'
$repo=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
. "$repo/scripts/controller/Controller-Recovery.ps1"
. "$repo/scripts/controller/Controller-Preparation.ps1"
. "$repo/scripts/controller/Controller-DefinitionRecovery.ps1"
$fixture=Join-Path $env:TEMP ('definition-recovery-test-'+[guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory "$fixture/project_coordination" -Force|Out-Null
$task=[pscustomobject]@{task_id='F1597-FIXTURE';scientific_checkpoint_required=$true;scientific_operation='';completed_operations=@('mapped_mechanical_history_call_order_probe');next_safe_action='review existing evidence'}
[IO.File]::WriteAllText("$fixture/project_coordination/ACTIVE_TASK.json",($task|ConvertTo-Json))
$count=0
function Assert($ok,$why){if(-not $ok){throw "FAIL: $why"};$script:count++;"PASS $script:count`: $why"}
function Throws($body,$match,$why){$failed=$false;try{& $body|Out-Null}catch{$failed=$_.Exception.Message -match $match};Assert $failed $why}
$script:calls=0;$script:prompts=@();$script:hands=@();$script:responses=@()
$consult={param($p,$h) $script:prompts+= $p;$script:hands+= $h;$script:calls++;return $script:responses[$script:calls-1]}
$original='Review existing evidence. No qdel or qmove.'
$good="OPERATION_ID: research_preparation`nContinue approved F1597-FIXTURE evidence preparation; reconcile existing receipts, preserve scientific gates and report missing review."
$argsBase=@{Workspace=$fixture;Instruction=$original;RecoveryKey='run322:successor:322';Consult=$consult}
function RunCase($name,$replies){$script:calls=0;$script:prompts=@();$script:hands=@();$script:responses=$replies;$script:caseArgs=$argsBase.Clone();$script:caseArgs.StatePath="$fixture/$name.json"}
Assert ((Get-ControllerPreparationPlan $fixture $original).status -eq 'DEFINITION_REJECTED') 'actual negated guard-token rejection reproduced without changing validator'
RunCase 'success' @($good)
$r=Invoke-ControllerDefinitionRecovery @caseArgs
Assert ($r.plan.dispatch_ready -and $r.recovered -and $calls -eq 1) 'initial rejection automatically consults and validates correction'
Assert ($prompts[0].Contains($original) -and $prompts[0] -match 'Unreviewed proposal rejected' -and $prompts[0] -match 'F1597-FIXTURE' -and $prompts[0] -match 'registered_operations' -and $prompts[0] -match 'attempt') 'handoff contains original proposal, exact reasons, task, registry, constraints and attempt'
$before=(Get-FileHash $caseArgs.StatePath).Hash
$restart=Invoke-ControllerDefinitionRecovery @caseArgs
Assert ($calls -eq 1 -and $restart.instruction -eq $good -and (Get-FileHash $caseArgs.StatePath).Hash -eq $before) 'accepted correction survives restart without new consultation or ledger write'
# Simulate the production pending-checkpoint boundary and a single downstream dispatcher.
$executionCount=0;$checkpoint=[pscustomobject]@{state='COMPLETED';next_instruction=$original}
$checkpoint.next_instruction=$r.instruction;$checkpoint.state='PENDING'
if($checkpoint.state -eq 'PENDING'){$p=Get-ControllerPreparationPlan $fixture $checkpoint.next_instruction;if($p.dispatch_ready){$checkpoint.state='RUNNING';$executionCount++}}
if($checkpoint.state -eq 'PENDING'){$executionCount++}
Assert ($executionCount -eq 1) 'validated successor dispatched exactly once across simulated restart boundary'
RunCase 'repeat' @($original)
Throws {Invoke-ControllerDefinitionRecovery @caseArgs} 'Identical rejected' 'identical rejected proposal stops without a second consultation'
Assert ($calls -eq 1) 'same rejection fingerprint dispatched once'
Throws {Invoke-ControllerDefinitionRecovery @caseArgs} 'STOPPED' 'persistent repeated rejection stays stopped after restart'
RunCase 'budget' @('qdel proposal two','qmove proposal three')
Throws {Invoke-ControllerDefinitionRecovery @caseArgs} 'Two consultation attempts exhausted' 'two distinct corrections exhaust bounded budget'
Assert ($calls -eq 2 -and @($hands|Select-Object -Unique).Count -eq 2) 'two distinct persistent handoff IDs, no third dispatch'
Throws {Invoke-ControllerDefinitionRecovery @caseArgs} 'STOPPED' 'exhausted budget persists across restart'
RunCase 'crash' @()
$crashArgs=$caseArgs.Clone();$crashArgs.Consult={param($p,$h)$script:calls++;throw 'SIMULATED_PROCESS_INTERRUPTION'}
Throws {Invoke-ControllerDefinitionRecovery @crashArgs} 'SIMULATED_PROCESS_INTERRUPTION' 'interruption propagates after durable reservation'
$crashArgs.Consult={throw 'MUST_NOT_REDISPATCH'}
Throws {Invoke-ControllerDefinitionRecovery @crashArgs} 'DISPATCH_UNCERTAIN' 'reserved dispatch is not repeated after restart'
$s=Read-DefinitionRecoveryState $crashArgs.StatePath;$a=$s.chains[0].attempts[0]
New-Item -ItemType Directory "$fixture/archive"|Out-Null
$archive="$fixture/archive/response_fixture_$($a.handoff_id).json"
[IO.File]::WriteAllText($archive,(@{bridge_handoff_id=$a.handoff_id;status='OK';response=$good}|ConvertTo-Json))
$crashArgs.BridgeArchive="$fixture/archive"
$recovered=Invoke-ControllerDefinitionRecovery @crashArgs
Assert ($recovered.plan.dispatch_ready -and $calls -eq 1) 'authentic archived bridge response resumes reserved send without redispatch'
RunCase 'unauthorized' @("OPERATION_ID: invented_operation`nExecute an invented registered operation",$good)
$r=Invoke-ControllerDefinitionRecovery @caseArgs
Assert ($calls -eq 2 -and $r.instruction -eq $good) 'ChatGPT cannot self-register an unknown operation'
RunCase 'review' @('DEFINITION_REVIEW_REQUIRED: missing predecessor scientific review')
Throws {Invoke-ControllerDefinitionRecovery @caseArgs} 'Review/registration required' 'missing review is explicit actionable stop'
RunCase 'service' @()
$serviceArgs=$caseArgs.Clone();$serviceArgs.Consult={throw 'AUTHENTICATION_FAILED'}
Throws {Invoke-ControllerDefinitionRecovery @serviceArgs} 'AUTHENTICATION_FAILED' 'authentication failure retains original exception and stops'
RunCase 'external-auth' @($good);$caseArgs.Instruction='INTERACTIVE_SSO_REQUIRED'
$r=Invoke-ControllerDefinitionRecovery @caseArgs
Assert ($r.plan.status -eq 'BLOCKED_EXTERNAL_AUTHENTICATION' -and $calls -eq 0) 'external authentication blocker does not trigger consultation'
RunCase 'security' @('EXPLICIT_SECURITY_RESTRICTION: deny execution')
Throws {Invoke-ControllerDefinitionRecovery @caseArgs} 'RESTRICTED' 'explicit security response remains stopped'
Assert ($calls -eq 1) 'security stop does not consume another recovery turn'
RunCase 'cross-key' @($original)
Throws {Invoke-ControllerDefinitionRecovery @caseArgs} 'Identical rejected' 'seed globally rejected proposal'
$caseArgs.RecoveryKey='different-controller-run'
Throws {Invoke-ControllerDefinitionRecovery @caseArgs} 'Identical rejected' 'same rejected proposal is not dispatched again under a new run key'
Assert ($calls -eq 1) 'cross-key duplicate bridge dispatch prevented'
$ledger=$caseArgs.StatePath;[IO.File]::AppendAllText($ledger,'corrupt')
Throws {Invoke-ControllerDefinitionRecovery @caseArgs} 'ConvertFrom-Json|Invalid JSON|unexpected|CORRUPT' 'corrupt durable recovery state cannot enable a retry'
# Parse actual production wrappers; simulate the bridge only, not routing logic.
$controller="$repo/scripts/controller/Antigravity-Autonomous-Loop.ps1"
$tokens=$null;$errors=$null;$ast=[Management.Automation.Language.Parser]::ParseFile($controller,[ref]$tokens,[ref]$errors)
Assert ($errors.Count -eq 0) 'authoritative controller parses'
$wrapper=$ast.Find({param($n)$n -is [Management.Automation.Language.FunctionDefinitionAst] -and $n.Name -eq 'Invoke-DefinitionCorrectionChatGPT'},$true)
Assert ($null -ne $wrapper) 'production bridge recovery wrapper exists'
Invoke-Expression $wrapper.Extent.Text
function Write-LoopLog {param($Turn,$Tier,$Action,$Message)}
$WorkspaceDir=$fixture;$CurrentTurn=322;$EnableChatGPTBridge=$true
function Invoke-ChatGPTBridgeWithManualFallback {param($Prompt,$ContextLabel,$HandoffId,[switch]$SingleDispatch) Assert ($SingleDispatch -and $HandoffId.StartsWith('HND-DEF-')) 'production uses single automatic dispatch with durable ID'|Out-Null;return $good}
# Redirect only the outbox location via a test USERPROFILE; production code and validator run unchanged.
$savedProfile=$env:USERPROFILE
try{
    $env:USERPROFILE=$fixture;New-Item -ItemType Directory "$fixture/OpenClawPAD" -Force|Out-Null
    $reply=Invoke-DefinitionCorrectionChatGPT $original 'simulated-e2e'
    Assert ($reply -eq $good -and (Get-ControllerPreparationPlan $fixture $reply).dispatch_ready) 'simulated end-to-end production handoff returns only normally validated correction'
}finally{$env:USERPROFILE=$savedProfile}
$text=Get-Content $controller -Raw
Assert ($text -match 'resumePlan.status -eq ''DEFINITION_REJECTED''' -and $text -match 'NEXT_OPERATION_PREPARATION' -and $text -match '\$NextInstruction=Invoke-DefinitionCorrectionChatGPT') 'startup and successor rejection handlers are integrated'
# Run the actual successor handler, with only bridge/loop logging mocked.
$start=$text.IndexOf('    $preparation=Invoke-ControllerOperationPreparation $WorkspaceDir $NextInstruction')
$end=$text.IndexOf('    # AGY_QUOTA_GUARD_V1: if low quota',$start)
$handler=$text.Substring($start,$end-$start)
function Save-LoopStatus {param($Turn,$Status,$Tier,$Action,$Details)}
$savedProfile=$env:USERPROFILE
try{
    $env:USERPROFILE="$fixture/handler";New-Item -ItemType Directory "$env:USERPROFILE/OpenClawPAD" -Force|Out-Null
    $controllerCheckpointPath="$env:USERPROFILE/OpenClawPAD/controller_turn_checkpoint.json"
    $script:ControllerState=[pscustomobject]@{run_id='fixture-run';task_id='F1597-FIXTURE';turn=322;state='COMPLETED';updated_at='';recovery_count=0}
    $NextInstruction=$original;$script:validatedDispatches=0
    Invoke-Expression (":MainLoop while (`$true) {`n"+$handler+"`n`$script:validatedDispatches++; break MainLoop`n}")
    Assert ($script:validatedDispatches -eq 1 -and $NextInstruction -eq $good -and $preparation.dispatch_ready) 'actual NEXT_OPERATION_PREPARATION handler continues only after validated correction'
    $outbox=Read-DefinitionRecoveryState "$env:USERPROFILE/OpenClawPAD/definition_recovery_state.json"
    Assert ($outbox.chains[0].attempts.Count -eq 1) 'production handler makes one persisted bridge request'
    $script:ControllerState.state='PENDING';$script:ControllerState.next_instruction=$NextInstruction;Write-ControllerCheckpoint $controllerCheckpointPath $script:ControllerState
    $script:ControllerState=Read-ControllerCheckpoint $controllerCheckpointPath
    $resumeStart=$text.IndexOf('# Reconcile a rejected durable successor')
    $resumeEnd=$text.IndexOf("if (`$null -ne `$script:ControllerState)",$resumeStart)
    Invoke-Expression $text.Substring($resumeStart,$resumeEnd-$resumeStart)
    $outbox=Read-DefinitionRecoveryState "$env:USERPROFILE/OpenClawPAD/definition_recovery_state.json"
    Assert ($outbox.chains[0].attempts.Count -eq 1 -and $script:ControllerState.next_instruction -eq $good) 'actual restart handler retains pending correction without consulting or executing again'
}finally{$env:USERPROFILE=$savedProfile}
"SIMULATED_DRY_RUN: initial=DEFINITION_REJECTED; consultations=1; corrected=READY; unapproved_executions=0; validated_successor_dispatches=$executionCount"
"ALL $count DEFINITION RECOVERY CHECKS PASSED; no AGY, PAD, network or PBS; fixture=$fixture"
