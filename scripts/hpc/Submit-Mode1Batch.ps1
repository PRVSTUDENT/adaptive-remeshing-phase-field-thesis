[CmdletBinding()]
param([Parameter(Mandatory)][string]$ManifestPath,[Parameter(Mandatory)][string]$Job,[switch]$DryRun)
$ErrorActionPreference='Stop'
$repo='D:\Master thesis\Adaptive remeshing'
$ManifestPath=[IO.Path]::GetFullPath($ManifestPath)
if(-not $ManifestPath.StartsWith((Join-Path $repo 'models/pandey_kumar_mode1/'),[StringComparison]::OrdinalIgnoreCase)){throw 'Manifest outside Mode-I models'}
$batch=Get-Content $ManifestPath -Raw|ConvertFrom-Json
$candidates=@($batch.jobs|Where-Object {$_.id -ceq $Job})
if($candidates.Count -ne 1){throw 'Job absent or ambiguous'}
$j=$candidates[0];$run=$batch.remote_run_dir
if($run -notmatch '^/scratch9/pr21vyci/runs/mode1_[a-z0-9_/]+$' -or $run.Contains('..') -or $j.pbs -notmatch '^submit_M1_[A-Z0-9_]+\.pbs$'){throw 'Unsafe execution path'}
$remote='qsub -q entry_imfdfkmq '+$run+'/'+$j.pbs
$expected='powershell -NoProfile -ExecutionPolicy Bypass -File .\.agents\scripts\Invoke-GuardedSsh.ps1 -RemoteCommand "'+$remote+'"'
if($j.command -cne $expected){throw 'Command outside exact guarded adapter'}
if($DryRun){Write-Output "DRY_RUN: $Job; exact command, atomic gate, PBS receipt, dual-channel SUBMITTED; no remote execution";return}
Push-Location $repo
try{
 # Install the notification-only helper before reserving the submission slot.
 $helper=[IO.File]::ReadAllText((Join-Path $repo 'scripts/hpc/notify_mode1_submitted.sh')).Replace("`r`n","`n")
 $helper64=[Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($helper))
 $install="import base64,pathlib,sys; p=pathlib.Path(sys.argv[1]); p.write_bytes(base64.b64decode(sys.argv[2])); print('Notification helper ready')"
 $code64=[Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($install))
 & powershell -NoProfile -ExecutionPolicy Bypass -File .\.agents\scripts\Invoke-GuardedSsh.ps1 -RemoteCommand "python3 -c 'import base64,sys;exec(base64.b64decode(sys.argv.pop(1)))' $code64 $run/notify_mode1_submitted.sh $helper64"
 if($LASTEXITCODE -ne 0){throw 'Notification helper preparation failed before reservation'}
 $payload=@{toolCall=@{args=@{CommandLine=$j.command}}}|ConvertTo-Json -Depth 5 -Compress
 $decision=$payload|& powershell -NoProfile -ExecutionPolicy Bypass -File .\.agents\qsub-safety-gate.ps1|ConvertFrom-Json
 if($decision.decision -ne 'allow'){throw $decision.reason}
 $result=& powershell -NoProfile -ExecutionPolicy Bypass -File .\.agents\scripts\Invoke-GuardedSsh.ps1 -RemoteCommand $remote
 $status=$LASTEXITCODE
 Write-Output $result
 if($status -ne 0){throw 'Submission status uncertain or failed; inspect scheduler and ledger; never repeat automatically'}
 $id=($result|Out-String).Trim()
 if($id -notmatch '^\d+\.mmaster02$'){throw 'Unrecognized scheduler response; reconcile scheduler; no retry'}
 $digest=(Get-FileHash $ManifestPath).Hash.ToLowerInvariant()
 $receipt=Join-Path $repo 'project_coordination/MODE1_BATCH_SUBMISSIONS.json'
 $all=if(Test-Path -LiteralPath $receipt){Get-Content $receipt -Raw|ConvertFrom-Json}else{[pscustomobject]@{}}
 if(-not $all.PSObject.Properties[$digest]){$all|Add-Member -NotePropertyName $digest -NotePropertyValue ([pscustomobject]@{})}
 $entries=$all.PSObject.Properties[$digest].Value
 if($entries.PSObject.Properties[$Job]){throw "PBS accepted $id; previous receipt exists; reconcile without resubmission"}
 $entries|Add-Member -NotePropertyName $Job -NotePropertyValue @{pbs_job_id=$id;submitted_at=[DateTimeOffset]::UtcNow.ToString('o');command_sha256=$j.command_sha256}
 $tmp=$receipt+'.tmp';[IO.File]::WriteAllText($tmp,($all|ConvertTo-Json -Depth 20),[Text.UTF8Encoding]::new($false));Move-Item -LiteralPath $tmp -Destination $receipt -Force
 $name=[IO.Path]::GetFileNameWithoutExtension($j.pbs).Replace('submit_','')
 Add-Content -LiteralPath (Join-Path $repo 'project_coordination/HPC_JOB_LEDGER.csv') -Value "$id,$name,$run,,entry_imfdfkmq,$([DateTimeOffset]::UtcNow.ToString('o')),SUBMITTED,,STANDING_MODE1_V2_ACCEPTED_ONCE,$($batch.files.PSObject.Properties[$j.input].Value)"
 & powershell -NoProfile -ExecutionPolicy Bypass -File .\.agents\scripts\Invoke-GuardedSsh.ps1 -RemoteCommand "bash $run/notify_mode1_submitted.sh $run $id $name"
 if($LASTEXITCODE -ne 0){throw "PBS accepted $id; notification failed; preserve job and retry notification only"}
}finally{Pop-Location}
