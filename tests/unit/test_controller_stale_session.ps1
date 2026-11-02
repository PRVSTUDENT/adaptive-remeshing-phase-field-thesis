$ErrorActionPreference='Stop'
$repo=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
. "$repo/scripts/controller/Controller-StaleSession.ps1"
$n=0
function Check($ok,$why){if(-not $ok){throw $why};$script:n++;"PASS $why"}
function Fixture {
 $r=Join-Path $env:TEMP ('stale-owner-'+[guid]::NewGuid().ToString('N'));[IO.Directory]::CreateDirectory($r)|Out-Null
 $p=Join-Path $r 'session.json';@{active=$true;agent='gemini-antigravity';task_id='F1598-PACKAGE166-CONVERGENCE-ACCEPTANCE';controller_run_id='live_monitoring_1419488';claimed_at='2026-11-02T05:16:00.0000000+01:00'}|ConvertTo-Json|Set-Content $p
 Copy-Item $p "$r/ACTIVE_SESSION.json"
 @{root=$r;path=$p;hash=(Get-FileHash $p).Hash}
}
$f=Fixture;$caught=$false
try{Restore-OperatorAuthorizedF1598Session -Path $f.path -ExpectedHash $f.hash -Archive $f.root -AssertNoOwner {throw 'LIVE_OWNER'} -OperatorAuthorized}catch{$caught=$_.ToString() -match 'LIVE_OWNER'}
Check ($caught -and (Get-FileHash $f.path).Hash -eq $f.hash) 'active owner rejected without mutation'
$f=Fixture;$caught=$false
try{Restore-OperatorAuthorizedF1598Session -Path $f.path -ExpectedHash ('0'*64) -Archive $f.root -AssertNoOwner {} -OperatorAuthorized}catch{$caught=$_.ToString() -match 'SESSION_CHANGED'}
Check ($caught -and (Get-FileHash $f.path).Hash -eq $f.hash) 'hash mismatch rejected'
$f=Fixture
Restore-OperatorAuthorizedF1598Session -Path $f.path -ExpectedHash $f.hash -Archive $f.root -AssertNoOwner {} -OperatorAuthorized
$s=Get-Content $f.path -Raw|ConvertFrom-Json
Check (-not $s.active -and $s.agent -eq 'gemini-antigravity') 'exact orphan invalidated without impersonation'
Check ((Get-FileHash ($f.path+'.operator-replaced-original.json')).Hash -eq $f.hash) 'atomic replacement original retained'
Check ((Test-Path "$($f.root)/recovery-event.json") -and -not $s.recovery.monitoring_closeout_verified) 'auditable event no false closeout'
$caught=$false;try{Restore-OperatorAuthorizedF1598Session -Path $f.path -ExpectedHash $f.hash -Archive $f.root -AssertNoOwner {} -OperatorAuthorized}catch{$caught=$true}
Check $caught 'repeat recovery prevented'
"ALL $n STALE CHECKS PASSED"
$f=Fixture;$script:probes=0;$caught=$false
$probe={ $script:probes++; if($script:probes -eq 2){$s=Get-Content $f.path -Raw|ConvertFrom-Json;$s.controller_run_id='different-owner';$s|ConvertTo-Json|Set-Content $f.path} }
# During the second check, the exclusive read handle denies in-place writes;
# a rename by another claimant must instead be detected by the hash comparison.
try{Restore-OperatorAuthorizedF1598Session -Path $f.path -ExpectedHash $f.hash -Archive $f.root -AssertNoOwner $probe -OperatorAuthorized}catch{$caught=$true}
Check ($caught -and -not(Test-Path "$($f.root)/recovery-event.json")) 'ownership change during recovery cannot release claim'
"FINAL $n STALE CHECKS PASSED"
