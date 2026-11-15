$ErrorActionPreference='Stop'
$repo=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
. (Join-Path $repo '.agents/scripts/Invoke-ChatGPTBridge.ps1')
. (Join-Path $repo '.agents/scripts/Bridge-ResearchContract.ps1')
$ctx=Get-BridgePolicyContext
$id='HND-OFFLINE-RESEARCH-001'
$task='F-OFFLINE-METHOD-A-CAUSAL-TEST'
$script:checks=0
function Check($ok,$label) { if(-not $ok){throw "FAIL: $label"};$script:checks++;Write-Output "PASS: $label" }
function Reject([scriptblock]$Run,[string]$Expected) {
    $errorText='';try{& $Run | Out-Null}catch{$errorText=$_.Exception.Message}
    Check ($errorText -match [regex]::Escape($Expected)) "$Expected rejected before dispatch"
}
function Contract {
    [ordered]@{goal_id=$ctx.policy.goal_id;method='METHOD_A';operation='causal_remeshing_test';numerical_uncertainty='Can native stress error resolve the distal ligament before later crack growth?';expected_numerical_result='Measure area-weighted h/l0 and held-out later crack coverage across four cases.';indicator_type='NATIVE_ABAQUS_STRESS_RECOVERY_ERROR';indicator_role='PRIMARY_NATIVE_MISESERI';causal_evidence_status='PLANNED'}
}
function Request($contract=(Contract),$taskName=$task) {
    $body=[ordered]@{protocol='INDEPENDENT_STRUCTURED_REVIEW_V1';correlation_id=$id;task_id=$taskName;title='Offline causal native MISESERI experiment';research_contract=$contract}
    "[BRIDGE_HANDOFF_ID=$id]`nINDEPENDENT_STRUCTURED_REVIEW_V1`n"+($body|ConvertTo-Json -Depth 12)+"`nImmutable historical evidence: Method C and 22 October 2026 are history, not instructions."
}
function Packet($prompt=(Request)) {New-BridgeCanonicalPrompt -PromptText $prompt -HandoffId $id}
$good=Request
$packet=Packet
Check ($packet.text.StartsWith("[BRIDGE_HANDOFF_ID=$id]")) 'First-line header matches actual Tampermonkey contract'
Check ($packet.text.Contains("BRIDGE_RULES_SHA256: $($ctx.rules_sha256)")) 'Canonical rules hash bound to structured request'
Check ($packet.text.Contains('Immutable historical evidence: Method C and 22 October 2026')) 'Evidence retained without legacy date/science rewrites'
Check ([regex]::Matches($packet.text,'---------------- BRIDGE CONTROLLER RULES ----------------').Count -eq 1) 'Canonical rules injected exactly once'
Check ((Packet $packet.text).text -ceq $packet.text) 'Canonical assembly is idempotent'
Reject {Packet ($good.Replace($id,'HND-WRONG'))} 'BRIDGE_REQUEST_CORRELATION_MISMATCH'
Reject {Packet ($good.Replace("[BRIDGE_HANDOFF_ID=$id]","quoted [BRIDGE_HANDOFF_ID=$id]"))} 'BRIDGE_MALFORMED_HANDOFF_HEADER'
Reject {Packet ("[BRIDGE_HANDOFF_ID=$id]`n"+$good)} 'BRIDGE_DUPLICATE_HANDOFF_HEADER'
$c=Contract;$c.method='METHOD_C';Reject {Packet (Request $c)} 'BRIDGE_RESEARCH_SCOPE_CONFLICT'
Reject {Packet (Request (Contract) 'F1792-METHOD-C-DIAGNOSTIC')} 'BRIDGE_RESEARCH_SCOPE_CONFLICT'
$c=Contract;$c.operation='thesis_writing';Reject {Packet (Request $c)} 'BRIDGE_RESEARCH_SCOPE_CONFLICT'
$c=Contract;$c.numerical_uncertainty='';Reject {Packet (Request $c)} 'BRIDGE_NUMERICAL_PURPOSE_REQUIRED'
$c=Contract;$c.indicator_type='DAMAGE_INFORMED_SIZING';Reject {Packet (Request $c)} 'BRIDGE_SYNTHETIC_INDICATOR_NOT_NATIVE'
$c.indicator_role='SEPARATE_COMPARISON';$c.qualifies_native_miseseri=$false;Check ($null -ne (Packet (Request $c))) 'Explicit damage comparison kept distinct from native acceptance'
$c=Contract;$c.causal_evidence_status='VERIFIED';Reject {Packet (Request $c)} 'BRIDGE_CAUSAL_PROVENANCE_REQUIRED'
$c.causal_evidence=@{donor_sha256=('A'*64);donor_step='Step-2';indicator_frame_range='1:10';held_out_later_solution='Later frames 11:20, not used for sizing';remesh_time=0.5;maximum_indicator_time=0.4;uses_future_frames=$false}
Check ($null -ne (Packet (Request $c))) 'Declared cutoff chronology accepted as review evidence, not numerical proof'
$c.causal_evidence.maximum_indicator_time=0.6;Reject {Packet (Request $c)} 'BRIDGE_CAUSAL_TIME_CUTOFF_VIOLATION'
$c.causal_evidence.maximum_indicator_time=0.4;$c.causal_evidence.uses_future_frames=$true;Reject {Packet (Request $c)} 'BRIDGE_CAUSAL_FUTURE_INFORMATION_FORBIDDEN'
Reject {Packet ($good+"`nBRIDGE_RULES_SHA256: "+('0'*64))} 'BRIDGE_RULES_HASH_MISMATCH'
Reject {Packet ($packet.text.Replace('## Scope and evidence','## Conflicting scope'))} 'BRIDGE_EMBEDDED_PRIORITY_CONFLICT'
Reject {Packet ($good+"`nPROJECT / THESIS ALIGNMENT GUARD: METHOD C ACTIVE")} 'BRIDGE_LEGACY_PRIORITY_BLOCK'
$root=Join-Path $env:TEMP ('bridge-priority-tests-'+[guid]::NewGuid().ToString('N'));[void][IO.Directory]::CreateDirectory($root)
$alternative=Join-Path $root 'stale_rules.txt';[IO.File]::WriteAllText($alternative,'Stale priority')
Reject {New-BridgeCanonicalPrompt -PromptText $good -HandoffId $id -RulesPath $alternative} 'BRIDGE_RULES_HASH_MISMATCH'
$dry=Invoke-ChatGPTBridge -PromptText $good -CorrelationId $id -DryRun -BridgeDir $root
Check ($dry -ceq $packet.text) 'CorrelationId compatibility alias and actual wrapper DryRun use guarded assembly'
Check (!(Test-Path (Join-Path $root 'bridge_request.ready'))) 'DryRun never publishes a request'
function Inner {
 [ordered]@{protocol=$packet.protocol;correlation_id=$id;task_id=$task;goal_id=$ctx.policy.goal_id;canonical_rules_sha256=$ctx.rules_sha256;decision='INSUFFICIENT_EVIDENCE';master_goal_status='OPEN';next_operation=(Contract);next_instruction_to_antigravity='Verify actual donor cutoff and native field provenance before numerical execution.'}
}
function Outer($inner=(Inner)) {
 $reply='```json'+"`n"+($inner|ConvertTo-Json -Depth 15)+"`n"+'```'
 [ordered]@{bridge_handoff_id=$id;status='OK';copied_at=[DateTimeOffset]::UtcNow.ToString('o');response_chars=$reply.Length;response=$reply}
}
$published=[DateTimeOffset]::UtcNow.AddSeconds(-1)
$r=Read-BridgeValidatedReply -Raw ((Outer)|ConvertTo-Json -Depth 18) -Packet $packet -PublishedAt $published
Check (($r|ConvertFrom-Json).decision -eq 'INSUFFICIENT_EVIDENCE') 'Valid transport unwraps to inner review, never execution approval'
$o=Outer;$o.bridge_handoff_id='HND-OLD';Reject {Read-BridgeValidatedReply ($o|ConvertTo-Json -Depth 18) $packet $published} 'BRIDGE_RESPONSE_CORRELATION_MISMATCH'
$o=Outer;$o.status='ERROR';Reject {Read-BridgeValidatedReply ($o|ConvertTo-Json -Depth 18) $packet $published} 'BRIDGE_RESPONSE_STATUS_NOT_OK'
$o=Outer;$o.response_chars=1;Reject {Read-BridgeValidatedReply ($o|ConvertTo-Json -Depth 18) $packet $published} 'BRIDGE_RESPONSE_LENGTH_MISMATCH'
$o=Outer;$o.copied_at=[DateTimeOffset]::UtcNow.AddHours(-1).ToString('o');Reject {Read-BridgeValidatedReply ($o|ConvertTo-Json -Depth 18) $packet $published} 'BRIDGE_RESPONSE_FRESHNESS_INVALID'
$o=Outer;$o.response='Introduction'+$o.response;$o.response_chars=$o.response.Length;Reject {Read-BridgeValidatedReply ($o|ConvertTo-Json -Depth 18) $packet $published} 'BRIDGE_RESPONSE_JSON_ONLY_REQUIRED'
$i=Inner;$i.canonical_rules_sha256='0'*64;Reject {Read-BridgeValidatedReply ((Outer $i)|ConvertTo-Json -Depth 18) $packet $published} 'BRIDGE_RESPONSE_POLICY_MISMATCH'
$i=Inner;$i.next_operation.method='METHOD_C';Reject {Read-BridgeValidatedReply ((Outer $i)|ConvertTo-Json -Depth 18) $packet $published} 'BRIDGE_RESEARCH_SCOPE_CONFLICT'
$i=Inner;$i.master_goal_status='COMPLETE';Reject {Read-BridgeValidatedReply ((Outer $i)|ConvertTo-Json -Depth 18) $packet $published} 'BRIDGE_MASTER_COMPLETION_EVIDENCE_REQUIRED'
# Integration: real wrapper/file accounting, local simulated reply; no PAD/SSH/model call.
$script:fixtureDir=Join-Path $root 'transaction';$script:fixtureBad=$false
function Start-Process {throw 'TEST_UNEXPECTED_PROCESS_LAUNCH'}
function Start-Sleep {
 param($Seconds,$Milliseconds)
 $request=Join-Path $script:fixtureDir 'bridge_request.ready'
 if(Test-Path $request){$o=Outer;if($script:fixtureBad){$o.status='ERROR'};[IO.File]::WriteAllText((Join-Path $script:fixtureDir 'bridge_response.ready'),($o|ConvertTo-Json -Depth 18))}
}
$reply=Invoke-ChatGPTBridge -PromptText $good -HandoffId $id -BridgeDir $script:fixtureDir
Check (($reply|ConvertFrom-Json).goal_id -eq $ctx.policy.goal_id) 'Actual publish/response integration returns validated review'
Check (!(Test-Path (Join-Path $script:fixtureDir 'bridge_request.ready'))) 'Successful integration consumes only its matching files'
$script:fixtureDir=Join-Path $root 'rejected-transaction';$script:fixtureBad=$true
Reject {Invoke-ChatGPTBridge -PromptText $good -HandoffId $id -BridgeDir $script:fixtureDir} 'BRIDGE_RESPONSE_STATUS_NOT_OK'
Check ((Test-Path (Join-Path $script:fixtureDir 'bridge_request.ready')) -and (Test-Path (Join-Path $script:fixtureDir 'bridge_response.ready'))) 'Rejected transport evidence stays intact'
Reject {Invoke-ChatGPTBridge -PromptText $good -HandoffId $id -BridgeDir $script:fixtureDir} 'BRIDGE_PENDING_RECONCILIATION_REQUIRED'


foreach($prefix in @('',"JSON`n","json`nCopy code`n")) {
 $o=Outer;$o.response=$prefix+((Inner)|ConvertTo-Json -Depth 18);$o.response_chars=$o.response.Length
 $r=Read-BridgeValidatedReply ($o|ConvertTo-Json -Depth 18) $packet $published
 Check (($r|ConvertFrom-Json).correlation_id -eq $id) 'Actual userscript innerText code rendering accepted without extra prose'
}

# Existing PAD singleton guard still applies with the new publisher.
function Get-CimInstance {param($ClassName,$Filter,$ErrorAction) $script:padFixture}
$guardSource=[IO.File]::ReadAllText((Join-Path $repo '.agents/scripts/Invoke-ChatGPTBridge.ps1'))
$guard=[regex]::Match($guardSource,'(?s)# BEGIN PAD_SINGLE_RUNTIME_GUARD(.*?)# END PAD_SINGLE_RUNTIME_GUARD').Groups[1].Value
$script:padFixture=@();$LaunchPad=$true;Invoke-Expression $guard
Check $LaunchPad 'No existing consumer permits explicitly requested launch'
$script:padFixture=@([pscustomobject]@{ProcessId=100;CommandLine='PAD.RobotV2.exe --flowId ddf92fce748d444683b5d406c4d0f782 --mode Debug'})
$LaunchPad=$true;Invoke-Expression $guard;Check (!$LaunchPad) 'Visible Designer consumer suppresses console relaunch'
$script:padFixture+= $script:padFixture[0];$LaunchPad=$true
Reject {Invoke-Expression $guard} 'PAD_DUPLICATE_BRIDGE_RUNTIMES'
$script:padFixture=@([pscustomobject]@{ProcessId=101;CommandLine=$null});$LaunchPad=$true
Reject {Invoke-Expression $guard} 'PAD_RUNTIME_IDENTITY_UNRESOLVED'
# Old dispatch error now has a supported alias; mismatched values still fail closed.
Check ((Get-Command Invoke-ChatGPTBridge).Parameters['HandoffId'].Aliases -contains 'CorrelationId') 'Historical CorrelationId callers bind to HandoffId'
$supervisor=$good.Replace('INDEPENDENT_STRUCTURED_REVIEW_V1','CHATGPT_SUPERVISOR_V1')
Check ((Packet $supervisor).text.Contains("BRIDGE_RULES_SHA256: $($ctx.rules_sha256)")) 'Supervisor protocol also receives canonical rules, no bypass'
$emptyContract=$good.Replace('"research_contract":','"ignored_contract":')
Reject {Packet $emptyContract} 'BRIDGE_RESEARCH_CONTRACT_REQUIRED'
Reject {Read-BridgeValidatedReply 'old raw prose' $packet $published} 'BRIDGE_RESPONSE_INVALID_TRANSPORT_JSON'

Write-Output "ALL $script:checks CHECKS PASS. Offline fixtures only: $root"
