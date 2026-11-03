$ErrorActionPreference='Stop'
$repo=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
. "$repo/scripts/controller/Controller-AuthRecovery.ps1"
$n=0
function Check($x,$why){if(-not $x){throw $why};$script:n++;"PASS $why"}
function PathForTest {$r=Join-Path $env:TEMP ('auth-recovery-'+[guid]::NewGuid().ToString('N'));[IO.Directory]::CreateDirectory($r)|Out-Null;Join-Path $r 'state.json'}
$script:refreshCount=0;$script:ready=$false;$p=PathForTest
$r=Invoke-ControllerAuthRecovery -StatePath $p -CheckpointHash 'fixture' -Profiles @('account1','account2') -Identity {param($p) 'registered-'+$p} -Activate {} -Verify {param($p) if(-not $script:ready){throw 'HTTP 401'};'registered-'+$p} -Refresh {$script:refreshCount++;$script:ready=$true}
Check ($r.status -eq 'VERIFIED_PROFILE' -and $r.selected_profile -eq 'account1') 'expired token refreshed and verified'
Check ($script:refreshCount -eq 1 -and $r.attempts[0].refresh_attempted) 'refresh intent persisted once'
Check (-not $r.safety_blocked) 'safety unblocked only after genuine verification callback'
$p=PathForTest;$script:refreshCount=0
$r=Invoke-ControllerAuthRecovery -StatePath $p -CheckpointHash 'fixture' -Profiles @('account1','account2') -Identity {param($p) 'registered-'+$p} -Activate {} -Verify {param($p) if($p -eq 'account1'){throw 'HTTP 401'};'registered-'+$p} -Refresh {$script:refreshCount++;throw 'refresh rejected'}
Check ($r.selected_profile -eq 'account2' -and $script:refreshCount -eq 1) 'alternate verified profile after failed refresh'
$p=PathForTest
$r=Invoke-ControllerAuthRecovery -StatePath $p -CheckpointHash 'fixture' -Profiles @('account1') -Identity {'registered'} -Activate {} -Verify {'different-identity'} -Refresh {throw 'must not refresh mismatch'}
Check ($r.safety_blocked -and $r.attempts[0].outcome -eq 'IDENTITY_MISMATCH') 'identity mismatch never accepted'
$p=PathForTest;$script:refreshCount=0
$args=@{StatePath=$p;CheckpointHash='fixture';Profiles=@('account1','account2');Identity={param($p) 'registered-'+$p};Activate={};Verify={throw 'HTTP 401'};Refresh={$script:refreshCount++;throw 'rejected'}}
$r=Invoke-ControllerAuthRecovery @args
Check ($r.status -eq 'AUTH_RECOVERY_REQUIRED' -and $r.safety_blocked -and $script:refreshCount -eq 2) 'bounded exhaustion across existing profiles'
$r=Invoke-ControllerAuthRecovery @args
Check ($script:refreshCount -eq 2 -and $r.attempts.Count -eq 2) 'restart cannot repeat exhausted refresh attempts'
$caught=$false;try{Invoke-ControllerAuthRecovery -StatePath $p -CheckpointHash 'changed' -Profiles @('account1') -Identity {} -Activate {} -Verify {} -Refresh {}|Out-Null}catch{$caught=$true}
Check $caught 'checkpoint identity cannot change under recovery'
$caught=$false;try{Invoke-ControllerAuthRecovery -StatePath (PathForTest) -CheckpointHash 'fixture' -Profiles @('unregistered') -Identity {} -Activate {} -Verify {} -Refresh {}|Out-Null}catch{$caught=$true}
Check $caught 'unregistered profile rejected'
"ALL $n AUTH RECOVERY CHECKS PASS; simulated providers only"
$tokens=$null;$errors=$null;$ast=[Management.Automation.Language.Parser]::ParseFile("$repo/scripts/controller/Antigravity-Autonomous-Loop.ps1",[ref]$tokens,[ref]$errors)
& {
 $script:order=[Collections.Generic.List[string]]::new()
 function Invoke-AgyAuthenticationFailover {$script:order.Add('verify')}
 function Set-AndVerifyAgyRunProfileCore {param($Context) $script:order.Add('legacy')}
 $node=$ast.Find({param($x)$x -is [Management.Automation.Language.FunctionDefinitionAst] -and $x.Name -eq 'Set-AndVerifyAgyRunProfile'},$true)
 . ([scriptblock]::Create($node.Extent.Text))
 Set-AndVerifyAgyRunProfile -Context STARTUP
 if(($script:order -join ',') -ne 'verify,legacy'){throw 'Legacy refresh preceded bounded verification'}
}
Check $true 'production startup verifies through bounded recovery before legacy refresh'
"FINAL $n AUTH RECOVERY CHECKS PASS"
$p=PathForTest;$cp=$p+'.checkpoint';'fixture pending operation'|Set-Content $cp;$hash=(Get-FileHash $cp).Hash
New-ControllerAuthResumeReservation -CheckpointPath $cp -ExpectedHash $hash -ReservationPath $p -Verify {$true} -AssertOwnerFree {}
$caught=$false;try{New-ControllerAuthResumeReservation -CheckpointPath $cp -ExpectedHash $hash -ReservationPath $p -Verify {$true} -AssertOwnerFree {}}catch{$caught=$true}
Check $caught 'atomic resume reservation prevents duplicate launches'
Check ((Get-FileHash $cp).Hash -eq $hash) 'reservation preserves pending checkpoint bytes'
"FINAL $n AUTH RECOVERY CHECKS PASS"
. "$repo/scripts/controller/Controller-Recovery.ps1"
$s=[pscustomobject]@{state='PENDING';turn=36;process_id=0;next_instruction='';owned_session_fingerprint='';original_instruction_hash=(Get-ControllerTextHash 'exact saved operation')}
$r=Get-ControllerPendingAuthResumePlan -State $s -Instruction 'exact saved operation' -ProviderVerified
Check ($r.turn -eq 36 -and $r.instruction -eq 'exact saved operation') 'resume exact pending turn instead of turn1'
$caught=$false;try{Get-ControllerPendingAuthResumePlan -State $s -Instruction 'different' -ProviderVerified|Out-Null}catch{$caught=$true};Check $caught 'different pending instruction rejected'
$caught=$false;try{Get-ControllerPendingAuthResumePlan -State $s -Instruction 'exact saved operation'|Out-Null}catch{$caught=$true};Check $caught 'provider proof required before resume'
$s.process_id=123;$caught=$false;try{Get-ControllerPendingAuthResumePlan -State $s -Instruction 'exact saved operation' -ProviderVerified|Out-Null}catch{$caught=$true};Check $caught 'started model operation cannot use unstarted resume path'
"FINAL $n AUTH CHECKS PASSED"

# Healthy-profile verification is read-only even when background hubs exist.
$p=PathForTest; $cp=$p+'.checkpoint'; 'pending'|Set-Content $cp
$hash=(Get-FileHash $cp).Hash; $script:ownerChecks=0
$r=Invoke-ControllerReadOnlyProfileCheck -CheckpointPath $cp -CurrentProfile account5 -AssertOwnerFree {$script:ownerChecks++} -Verify {param($profile) $profile -eq 'account5'}
Check ($r.read_only -and $r.selected_profile -eq 'account5' -and $script:ownerChecks -eq 2) 'healthy current profile verified without activation or refresh'
Check ((Get-FileHash $cp).Hash -eq $hash) 'read-only profile verification preserves checkpoint'
$caught=$false;try{Invoke-ControllerReadOnlyProfileCheck -CheckpointPath $cp -CurrentProfile account5 -AssertOwnerFree {throw 'AUTH_RECOVERY_LIVE_AGY'} -Verify {throw 'must not run'}|Out-Null}catch{$caught=$true};Check $caught 'live or uncertain owner blocks even read-only resume'
$caught=$false;try{Invoke-ControllerReadOnlyProfileCheck -CheckpointPath $cp -CurrentProfile account5 -AssertOwnerFree {} -Verify {$false}|Out-Null}catch{$caught=$_.Exception.Message -match 'credential mutation remains blocked'};Check $caught 'failed provider proof never falls through to credential mutation'
$caught=$false;try{Invoke-ControllerReadOnlyProfileCheck -CheckpointPath $cp -CurrentProfile account5 -AssertOwnerFree {} -Verify {'changed'|Set-Content $cp; $true}|Out-Null}catch{$caught=$_.Exception.Message -eq 'AUTH_RECOVERY_CHECKPOINT_CHANGED'};Check $caught 'checkpoint race rejected'
& {
 function Read-ControllerCheckpoint {param($path) [pscustomobject]@{workspace=$repo;process_id=$script:workerPid}}
 $script:workerPid=0; $script:hubCommand='agy.exe --hub --hub-port=123';$script:ownerMatches=$true
 function Get-CimInstance {param($ClassName,$Filter,$ErrorAction)
  if($Filter -eq "Name = 'agy.exe'"){[pscustomobject]@{ExecutablePath=(Join-Path $env:USERPROFILE '.gemini/bin/agy.exe');CommandLine=$script:hubCommand;ParentProcessId=123;CreationDate=[datetime]'2026-11-03'}}
  else{[pscustomobject]@{Name='Code.exe';CreationDate=[datetime]'2026-11-02'}}
 }
 function Invoke-CimMethod {param($InputObject,$MethodName,$ErrorAction) [pscustomobject]@{ReturnValue=0;Sid=$(if($script:ownerMatches){[Security.Principal.WindowsIdentity]::GetCurrent().User.Value}else{'different'})}}
 Assert-ControllerBackgroundHubsOnly fixture;Check $true 'verified same-user VS Code hub allows read-only check'
 $script:hubCommand='agy.exe --input-format text';$caught=$false;try{Assert-ControllerBackgroundHubsOnly fixture}catch{$caught=$true};Check $caught 'CLI worker is never mistaken for background hub'
 $script:hubCommand='agy.exe --hub';$script:ownerMatches=$false;$caught=$false;try{Assert-ControllerBackgroundHubsOnly fixture}catch{$caught=$true};Check $caught 'foreign hub owner rejected'
 $script:ownerMatches=$true;$script:workerPid=123;$caught=$false;try{Assert-ControllerBackgroundHubsOnly fixture}catch{$caught=$true};Check $caught 'checkpoint-owned worker rejected'
}
