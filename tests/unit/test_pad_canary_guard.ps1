$ErrorActionPreference='Stop'
$workspace=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
. (Join-Path $workspace 'scripts/controller/pad_canary/Invoke-PadCanaryGuard.ps1') -LibraryOnly
$tempRoot=Join-Path ([IO.Path]::GetTempPath()) ('pad-canary-offline-'+[guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $tempRoot|Out-Null
$script:n=0;$script:fixture=0
function Check($ok,$message){if(!$ok){throw $message};$script:n++;Write-Output "PASS: $message"}
function Reject($action,$message){$failed=$false;try{&$action|Out-Null}catch{$failed=$true};Check $failed $message}
function Fixture {
 $script:fixture++;$p=Join-Path $tempRoot ('fixture'+$script:fixture)
 $id=New-PadCanary $p;Claim-PadCanary $p|Out-Null
 # Synthetic past reservation for offline temporal validation, never live state.
 $a=Get-Content (Join-Path $p 'paste_attempt.json') -Raw|ConvertFrom-Json
 $a.reserved_utc=[DateTimeOffset]::UtcNow.AddSeconds(-30).ToString('o')
 [IO.File]::WriteAllText((Join-Path $p 'paste_attempt.json'),($a|ConvertTo-Json))
 return @{path=$p;id=$id;reply=@{bridge_handoff_id=$id;status='OK';response='PAD_CANARY_PASS';response_chars=15;copied_at=[DateTimeOffset]::UtcNow.ToString('o')}}
}
function Candidate($f){$f.reply.response_chars=([string]$f.reply.response).Length;[IO.File]::WriteAllText((Join-Path $f.path 'clipboard_candidate.json'),($f.reply|ConvertTo-Json),[Text.Encoding]::Unicode)}
$f=Fixture
Check ((Get-PadHash (Join-Path $f.path 'bridge_request.ready')) -ceq (Get-PadHash (Join-Path $f.path 'archive/request.txt'))) 'Original request archived byte-for-byte before execution'
Reject {New-PadCanary $f.path} 'Preparation cannot erase or replace the single transaction'
Reject {Claim-PadCanary $f.path} 'A second PAD execution cannot reserve the same handoff'
Candidate $f;Check ((Validate-PadCanary $f.path) -ceq 'VALIDATED') 'Matching fresh v1.5 Unicode clipboard JSON validates'
$returned=(Receive-PadCanary $f.path)|ConvertFrom-Json
Check ($returned.response -ceq 'PAD_CANARY_PASS' -and $returned.full_single_handoff_pass -ceq 'AWAITING_ACTUAL_BROWSER_OBSERVATIONS') 'Controller receives response without manufacturing a live browser PASS'
Check (Test-Path (Join-Path $f.path 'bridge_request.ready')) 'Request remains recoverable even after successful validation'
Reject {Validate-PadCanary $f.path} 'A validated response cannot be published twice'
$g=Fixture;$g.reply.bridge_handoff_id='HND-PAD-CANARY-wrong';Candidate $g
Reject {Validate-PadCanary $g.path} 'Wrong handoff is rejected'
Check ((Test-Path (Join-Path $g.path 'failure.json')) -and (Test-Path (Join-Path $g.path 'archive/clipboard_candidate.json')) -and (Test-Path (Join-Path $g.path 'bridge_request.ready'))) 'Rejected reply and original request preserved with stop evidence'
$g=Fixture;Fail-PadCanary $g.path 'OFFLINE_TIMEOUT_FIXTURE'
Reject {Claim-PadCanary $g.path} 'A timeout is terminal and cannot trigger automatic paste retry'
$g=Fixture;$g.reply.copied_at=[DateTimeOffset]::UtcNow.AddHours(-1).ToString('o');Candidate $g
Reject {Validate-PadCanary $g.path} 'A stale clipboard timestamp cannot qualify'
$g=Fixture;[IO.File]::AppendAllText((Join-Path $g.path 'bridge_request.ready'),'changed')
Reject {Validate-PadCanary $g.path} 'Changed request bytes fail closed'
$g=Fixture;$g.reply.status='ERROR';Candidate $g
Reject {Validate-PadCanary $g.path} 'An error badge or ERROR JSON cannot pass'
Reject {Assert-PadCanaryRoot (Join-Path $env:USERPROFILE 'OpenClawPAD/ChatGPTBridge')} 'Production bridge root is excluded from this canary guard'
Write-Output "ALL $n OFFLINE PAD GUARD CHECKS PASS; zero browser/PAD sends."
