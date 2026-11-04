$ErrorActionPreference='Stop'
$workspace=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
. (Join-Path $workspace 'scripts/controller/Controller-Supervisor.ps1')
$root=Join-Path ([IO.Path]::GetTempPath()) ('controller-supervisor-'+[guid]::NewGuid().ToString('N'))
[IO.Directory]::CreateDirectory($root)|Out-Null
$script:count=0
function Check($condition,$message){if(-not $condition){throw $message};$script:count++;Write-Output "PASS: $message"}
$transport={param($prompt,$id) @{correlation_id=$id;action='DIAGNOSE';instruction='Inspect preserved evidence; no HPC submission.'}|ConvertTo-Json}
$r=Invoke-ControllerSupervisor -Workspace $workspace -Kind INITIAL -Evidence 'Maintenance objective' -ArchiveRoot $root -Transport $transport
Check ($r.execution_allowed -and !$r.approval) 'Bounded planning reply is never scientific approval'
# Consumer contract from the supplied installed Tampermonkey v1.5.0 script.
$trigger='(?m)^\s*\[BRIDGE_HANDOFF_ID=(HND-[A-Za-z0-9_-]+)\]\s*$'
$request=Get-Content (Join-Path (Join-Path $root $r.correlation_id) 'request.txt') -Raw
Check ([regex]::Match($request,$trigger).Groups[1].Value -ceq $r.correlation_id) 'Actual supervisor request arms the installed HND-only paste listener'
Check (![regex]::IsMatch('[BRIDGE_HANDOFF_ID=SUP-old-invalid]',$trigger)) 'Former SUP-only handoff reproduces the installed trigger failure'
$r2=Invoke-ControllerSupervisor -Workspace $workspace -Kind RESULT -Evidence 'Completed authentic read-only test' -RunId result -Turn 1 -ArchiveRoot $root -Transport $transport
Check ($r.correlation_id -ne $r2.correlation_id) 'Each result handoff has a unique correlation'
$r3=Invoke-ControllerSupervisor -Workspace $workspace -Kind ERROR -Evidence 'HARMLESS_TEST_ERROR: missing fixture; completed work preserved' -RunId error -SafetyBlocked -ArchiveRoot $root -Transport $transport
Check (!$r3.execution_allowed) 'Competing ownership or uncertain submission cannot be overridden by a reply'
$errorEvidence=Get-Content (Join-Path (Join-Path $root $r3.correlation_id) 'evidence.json') -Raw
Check ($errorEvidence -match 'HARMLESS_TEST_ERROR' -and (Test-Path (Join-Path (Join-Path $root $r3.correlation_id) 'HPC_JOB_LEDGER.csv'))) 'Raw error and ledger archived before transport'
$failed=$false
try{Invoke-ControllerSupervisor -Workspace $workspace -Kind ERROR -Evidence 'timeout fixture' -RunId uncertain -ArchiveRoot $root -Transport {throw 'TEST_TRANSPORT_TIMEOUT'}|Out-Null}catch{$failed=$_.Exception.Message -match 'TEST_TRANSPORT_TIMEOUT'}
Check $failed 'Transport failure is retained and propagated'
$called=$false;$blocked=$false
try{Invoke-ControllerSupervisor -Workspace $workspace -Kind ERROR -Evidence 'restart' -RunId uncertain -ArchiveRoot $root -Transport {$script:called=$true}|Out-Null}catch{$blocked=$_.Exception.Message -match 'RECONCILIATION_REQUIRED'}
Check ($blocked -and !$called) 'Restart does not replay uncertain handoff'
$stale=$false
try{Invoke-ControllerSupervisor -Workspace $workspace -Kind RESULT -Evidence 'stale fixture' -RunId stale -ArchiveRoot $root -Transport {param($p,$id) @{correlation_id='old';action='CONTINUE';instruction='Unsafe reuse'}|ConvertTo-Json}|Out-Null}catch{$stale=$_.Exception.Message -match 'STALE_RESPONSE'}
Check $stale 'Stale response is rejected without execution'
$invalid=$false
try{Invoke-ControllerSupervisor -Workspace $workspace -Kind RESULT -Evidence 'invalid action' -RunId invalid -ArchiveRoot $root -Transport {param($p,$id) @{correlation_id=$id;action='APPROVE';instruction='submit'}|ConvertTo-Json}|Out-Null}catch{$invalid=$_.Exception.Message -match 'INVALID_ACTION'}
Check $invalid 'Approval-shaped action is rejected'
. (Join-Path $workspace '.agents/scripts/Invoke-ChatGPTBridge.ps1')
$packet="[BRIDGE_HANDOFF_ID=SUP-OFFLINE]`nCHATGPT_SUPERVISOR_V1`nExact error: INTERACTIVE_SSO_REQUIRED; 1 CPU; historical words are evidence."
$assembled=Invoke-ChatGPTBridge -PromptText $packet -HandoffId SUP-OFFLINE -DryRun
Check ($assembled -ceq $packet) 'Supervisor packet bypasses legacy text rewrites while execution gates remain separate'
$bareJsonTransport = { param($p,$id) "JSON`n" + (@{correlation_id=$id;action='DIAGNOSE';instruction='Bare JSON prefix test'}|ConvertTo-Json) }
$rBare = Invoke-ControllerSupervisor -Workspace $workspace -Kind RESULT -Evidence 'Bare JSON test' -RunId barejson -Turn 2 -ArchiveRoot $root -Transport $bareJsonTransport
Check ($rBare.instruction -eq 'Bare JSON prefix test' -and $rBare.action -eq 'DIAGNOSE') 'Supervisor response with bare JSON prefix parses cleanly'
Write-Output "ALL $count SUPERVISOR TESTS PASSED (MOCKED TRANSPORT; NOT LIVE ACCEPTANCE)."
# Keep the small archived fixtures for diagnostic inspection.
