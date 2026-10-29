$ErrorActionPreference='Stop'
$repo=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
. (Join-Path $repo 'scripts/controller/Controller-Recovery.ps1')
$scriptPath=Join-Path $repo 'scripts/controller/Reconcile-Turn294.ps1'
$fixture=Join-Path ([IO.Path]::GetTempPath()) ('turn294-recovery-'+[guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory $fixture | Out-Null
$count=0
function Assert($ok,$why){if(-not $ok){throw "FAIL: $why"};$script:count++;"PASS $script:count`: $why"}
function Put($name,$text){$p=Join-Path $fixture $name;[IO.File]::WriteAllText($p,$text,[Text.UTF8Encoding]::new($false));return $p}
function Reject($body,$why){$failed=$false;try{& $body|Out-Null}catch{$failed=$_.Exception.Message -match 'BLOCKED'};Assert $failed $why}
$partial=Put 'partial.txt' 'Authentic fixture interruption. No submission.'
$loopPath=Put 'antigravity_loop_state.json' '{"completed_turn":293,"next_instruction":"Evidence-only reconciliation"}'
$path=Join-Path $fixture 'controller_turn_checkpoint.json'
$state=[pscustomobject]@{run_id='77c4cf2d-e740-4737-bb8a-a858fc0afd5a';task_id='F1597';turn=294;state='BLOCKED';recovery_count=0;updated_at='';block_reason='interrupted';stop_reason='';conversation_id='old';next_safe_action='';original_instruction_hash='unchanged-pending-instruction';partial_output=$partial;partial_sha256=(Get-FileHash $partial).Hash}
Write-ControllerCheckpoint $path $state
$original=Join-Path $fixture 'original.json';[IO.File]::Copy($path,$original,$false)
$expected=(Get-FileHash $original).Hash
$roles=@('original_checkpoint','loop_state','partial_output','jsonl','session_report','bootstrap','hpc_ledger','current_state','active_session','previous_checkpoint','remote_history','remote_candidate','remote_active','remote_directories','remote_predecessor','remote_trace','remote_accounting')
$evidence=@();foreach($role in $roles){$p=switch($role){'original_checkpoint'{$original};'loop_state'{$loopPath};'partial_output'{$partial};'remote_history'{Put "$role.txt" 'Job_Name = M1_C4_INC91_H30_CONT'};'remote_candidate'{Put "$role.txt" ''};'remote_predecessor'{Put "$role.txt" 'Job Id: 1418554.mmaster02; Exit_status = 0'};default{Put "$role.txt" 'fixture evidence'}};(Get-Item $p).IsReadOnly=$true;$evidence += [pscustomobject]@{role=$role;path=$p;sha256=(Get-FileHash $p).Hash;exit_code=0}}
$m=[pscustomobject]@{run_id=$state.run_id;turn=294;completed_turn=293;resume_scope='EVIDENCE_ONLY';original_sha256=$expected;hpc_classification='NO_MATCH_IN_RETAINED_EVIDENCE_NON_SUBMISSION_UNPROVEN';evidence=$evidence}
$manifest=Put 'manifest.json' ($m|ConvertTo-Json -Depth 10);(Get-Item $manifest).IsReadOnly=$true
$args294=@{Workspace=$repo;ControllerRoot=$fixture;EvidenceManifest=$manifest;ExpectedOriginalSha256=$expected}
$snapshot=@{};foreach($e in $evidence){$snapshot[$e.path]=$e.sha256}
$dry=& $scriptPath @args294
Assert ($dry.classification -eq 'DRY_RUN_PASS' -and (Get-FileHash $path).Hash -eq $expected) 'dry-run makes no checkpoint write'
Assert ($dry.turn -eq 294 -and $dry.completed_turn -eq 293) 'actual turn accounting retained'
Assert ($dry.next_instruction -match 'EVIDENCE_ONLY_RECOVERY' -and $dry.next_instruction -match 'No qsub') 'safe resumption prohibits original replay and submissions'
$wrongArgs=$args294.Clone();$wrongArgs.ExpectedOriginalSha256='wrong'
Reject { & $scriptPath @wrongArgs } 'wrong original hash rejected'
$bad=Read-ControllerCheckpoint $path;$bad.turn=7;Write-ControllerCheckpoint $path $bad
Reject { & $scriptPath @args294 } 'Turn7 or changed identity rejected'
[IO.File]::WriteAllBytes($path,[IO.File]::ReadAllBytes($original))
# A real scheduler match must halt before any transition, even with self-consistent hashes.
$candidate=$evidence|Where-Object role -eq 'remote_candidate';(Get-Item $candidate.path).IsReadOnly=$false
[IO.File]::WriteAllText($candidate.path,'1419999.mmaster02');$candidate.sha256=(Get-FileHash $candidate.path).Hash;(Get-Item $candidate.path).IsReadOnly=$true
$badManifest=Put 'positive-match.json' ($m|ConvertTo-Json -Depth 10)
$badArgs=$args294.Clone();$badArgs.EvidenceManifest=$badManifest
Reject { & $scriptPath @badArgs -Apply } 'existing PBS receipt cannot be bypassed or duplicated'
Assert ((Get-FileHash $path).Hash -eq $expected) 'PBS match leaves BLOCKED checkpoint intact'
(Get-Item $candidate.path).IsReadOnly=$false;[IO.File]::WriteAllText($candidate.path,'');$candidate.sha256=(Get-FileHash $candidate.path).Hash;(Get-Item $candidate.path).IsReadOnly=$true
$result=& $scriptPath @args294 -Apply
Assert ($result.classification -eq 'APPLIED_EVIDENCE_ONLY') 'supported evidence-only transition applies'
$recovered=Read-ControllerCheckpoint $path
Assert ($recovered.state -eq 'RECOVERY_REQUIRED' -and $recovered.turn -eq 294) 'interrupted attempt is not marked COMPLETED'
Assert ($recovered.original_instruction_hash -eq $state.original_instruction_hash) 'pending instruction identity preserved'
Assert (-not $recovered.conversation_id) 'fresh conversation required'
Assert-ControllerDispatchCheckpoint $repo $recovered
Assert $true 'resumable dispatch and checksum guards pass'
$appliedHash=(Get-FileHash $path).Hash
$again=& $scriptPath @args294 -Apply
Assert ($again.classification -eq 'ALREADY_APPLIED' -and (Get-FileHash $path).Hash -eq $appliedHash) 'repeat execution has no writes or backup overwrite'
foreach($e in $evidence){Assert ((Get-FileHash $e.path).Hash -eq $snapshot[$e.path]) ("evidence unchanged: "+$e.role)}
$recovered.state='COMPLETED'
Reject { Assert-ControllerDispatchCheckpoint $repo $recovered } 'invalid BLOCKED-to-COMPLETED transition rejected'
$recovered.state='RECOVERY_REQUIRED'
$recovered.original_instruction_hash='replay'
Reject { Assert-ControllerDispatchCheckpoint $repo $recovered } 'pending instruction tampering rejected'
$recovered.original_instruction_hash=$state.original_instruction_hash
$missing=$evidence|Where-Object role -eq 'bootstrap';(Get-Item $missing.path).IsReadOnly=$false;[IO.File]::WriteAllText($missing.path,'changed')
Reject { Assert-ControllerDispatchCheckpoint $repo $recovered } 'modified backup fails integrity guard'
Assert ((Get-Content $loopPath -Raw|ConvertFrom-Json).completed_turn -eq 293) 'loop completed turn never changes'
"ALL $count TURN294 CHECKS PASSED; fixture=$fixture; no network, scientific file or submission calls"
