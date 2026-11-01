$ErrorActionPreference='Stop'
$repo=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
. (Join-Path $repo 'scripts/controller/Controller-Recovery.ps1')
$root=Join-Path ([IO.Path]::GetTempPath()) ('completed-recovery-'+[guid]::NewGuid().ToString('N'))
foreach($dir in @('project_coordination','project_coordination/controller','project_coordination/sessions','results/validation')){[void](New-Item -ItemType Directory -Path (Join-Path $root $dir) -Force)}
function Put($rel,$text){[IO.File]::WriteAllText((Join-Path $root $rel),$text,[Text.UTF8Encoding]::new($false))}
function Check($condition,$message){if(-not $condition){throw "FAIL: $message"};Write-Output "PASS: $message"}
try {
 $run=[guid]::NewGuid().ToString();$task='F1597-RECOVERY-TEST';$report="project_coordination/sessions/$run.md";$boot="project_coordination/controller/turn-$run.json";$prep="results/validation/preparation-$run.json"
 Put 'project_coordination/ACTIVE_TASK.json' (@{task_id=$task;status='PREPARATION_COMPLETE'}|ConvertTo-Json)
 Put 'project_coordination/CURRENT_STATE.md' 'Completed preparation fixture'
 Put 'project_coordination/TASK_LEDGER.csv' "task_id,status`n$task,completed"
 Put 'project_coordination/HPC_JOB_LEDGER.csv' "Job_ID,Status`n1419305.mmaster02,SUBMITTED`n"
 Put 'project_coordination/MODE1_EXECUTION_LEDGER.json' '{}'
 $session=@{active=$false;agent='gemini-antigravity';task_id=$task;controller_run_id=$run;claimed_at='2026-11-01T10:00:00Z';starting_commit='abc';session_report=$report}
 Put 'project_coordination/ACTIVE_SESSION.json' ($session|ConvertTo-Json)
 Put $report "Completed scientific preparation $run`nFinished`n"
 $ledgerHash=(Get-FileHash (Join-Path $root 'project_coordination/HPC_JOB_LEDGER.csv')).Hash
 Put $prep (@{schema=1;status='PREPARATION_COMPLETE';finding='Completed actual scientific evidence fixture with preserved source hashes.';verification_passed=$true;evidence_sources=@{'project_coordination/HPC_JOB_LEDGER.csv'=$ledgerHash}}|ConvertTo-Json -Depth 8)
 Put $boot (@{repository_commit='abc';controller_run_id=$run;task_id=$task;stage='COMPLETE';bootstrap_status='COMPLETE';session_report=$report;scientific_checkpoint=@{kind='PREPARATION_CHECKPOINT';operation='research_preparation';exit_code=0;artifact=$prep;sha256=(Get-FileHash (Join-Path $root $prep)).Hash}}|ConvertTo-Json -Depth 8)
 function State {
  $s=New-ControllerTurnState (Get-ControllerEvidence $root) 1 'original instruction'
  $s.run_id=$run;$s.repository_commit='abc';$s.bootstrap_record_path=Join-Path $root $boot
  $s.sources[$prep]=(Get-FileHash (Join-Path $root $prep)).Hash
  $s.sources[$report]=(Get-FileHash (Join-Path $root $report)).Hash
  $s.owned_session_fingerprint=Get-ControllerTextHash ((@($session.agent,$session.task_id,$session.claimed_at,$session.starting_commit)) -join '|')
  return $s
 }
 $s=State;$path=Join-Path $root 'checkpoint.json'
 $proof=Get-ControllerCompletedPreparationEvidence $root $s
 Check ($proof.run_id -eq $run) 'Released exact owner has hash-bound completion evidence'
 Sync-ControllerOwnedSession (Get-ControllerEvidence $root) $s
 Check ($s.task_id -eq $task) 'Observation after legitimate release preserves ownership'
 Check (Complete-ControllerAfterCliFailure $root $path $s) 'CLI failure after legitimate completion reconciles without model retry'
 $restored=Read-ControllerCheckpoint $path
 Check ($restored.state -eq 'COMPLETED' -and $restored.run_id -eq $run) 'Completed checkpoint survives CLI failure and restart'
 Assert-ControllerDispatchCheckpoint $root $restored
 Check ($restored.state -eq 'COMPLETED') 'Restart accepts completed checkpoint without replay'
 foreach($active in @($true,$false)){
  $altered=$session.Clone();$altered.active=$active;$altered.claimed_at='2026-11-01T11:00:00Z'
  Put 'project_coordination/ACTIVE_SESSION.json' ($altered|ConvertTo-Json)
  $rejected=$false;try{Sync-ControllerOwnedSession (Get-ControllerEvidence $root) (State)}catch{$rejected=$_.Exception.Message -match 'ownership changed'}
  Check $rejected "Unexpected ownership mutation is rejected (active=$active)"
 }
 $live=$session.Clone();$live.active=$true;Put 'project_coordination/ACTIVE_SESSION.json' ($live|ConvertTo-Json)
 Check (-not(Complete-ControllerAfterCliFailure $root $path (State))) 'An active owner is never salvaged or released'
 $mutexName='Local\ControllerRecoveryTest-'+[guid]::NewGuid().ToString('N');$mutex=[Threading.Mutex]::new($false,$mutexName);$null=$mutex.WaitOne(0)
 try {
  $output=& powershell -NoProfile -Command ('$m=[Threading.Mutex]::new($false,'''+$mutexName+''');if($m.WaitOne(0)){$m.ReleaseMutex();throw ''duplicate acquired''}else{''BLOCKED_DUPLICATE''};$m.Dispose()')
  Check (($output|Out-String) -match 'BLOCKED_DUPLICATE') 'Simultaneous controller instance cannot acquire owned mutex'
 } finally {$mutex.ReleaseMutex();$mutex.Dispose()}
 Write-Output 'ALL COMPLETED RECOVERY TESTS PASSED'
} finally {
 $target=[IO.Path]::GetFullPath($root);$temp=[IO.Path]::GetFullPath([IO.Path]::GetTempPath())
 if(-not $target.StartsWith($temp,[StringComparison]::OrdinalIgnoreCase) -or (Split-Path $target -Leaf) -notlike 'completed-recovery-*'){throw 'Unsafe fixture cleanup'}
 Remove-Item -LiteralPath $target -Recurse -Force
}
