[CmdletBinding()]
param(
    [Parameter(Mandatory)][ValidateSet('Bootstrap','Scientific','Preparation','Complete')][string]$Stage,
    [Parameter(Mandatory)][string]$Workspace,
    [Parameter(Mandatory)][ValidatePattern('^[a-fA-F0-9-]{36}$')][string]$RunId,
    [Parameter(Mandatory)][string]$TaskId,
    [string]$RuntimeCheckpoint = "$env:USERPROFILE/OpenClawPAD/controller_turn_checkpoint.json",
    [string]$CheckpointArtifact = ''
)
$ErrorActionPreference='Stop'
. (Join-Path $Workspace 'scripts/controller/Controller-Recovery.ps1')
. (Join-Path $Workspace 'scripts/validation/Invoke-BoundedAgyProcess.ps1')
function Invoke-LocalGit([string[]]$Arguments){
    $r=Invoke-BoundedAgyProcess -FilePath (Get-Command git.exe).Source -ArgumentList (@('-C',$Workspace)+$Arguments) -WorkingDirectory $Workspace -TimeoutSeconds 120
    if($r.ExitCode -ne 0){throw ('Git failed: '+$r.Output)}
    return $r.Output.Trim()
}
$state=Read-ControllerCheckpoint $RuntimeCheckpoint
if(-not $state -or $state.run_id -ne $RunId -or $state.state -ne 'RUNNING' -or $state.task_id -ne $TaskId){throw 'Controller turn identity/state mismatch'}
if(-not $state.process_id -or -not(Get-Process -Id $state.process_id -ErrorAction SilentlyContinue)){throw 'Owned controller CLI is not live'}
$recordPath=Join-Path $Workspace ('project_coordination/controller/turn-'+$RunId+'.json')
$sessionPath=Join-Path $Workspace 'project_coordination/ACTIVE_SESSION.json'
$taskPath=Join-Path $Workspace 'project_coordination/ACTIVE_TASK.json'
$record=if(Test-Path -LiteralPath $recordPath){Get-Content -LiteralPath $recordPath -Raw|ConvertFrom-Json}else{$null}
function Save-Record {
    $temp=$recordPath+'.tmp'
    [IO.File]::WriteAllText($temp,(($script:record|ConvertTo-Json -Depth 30).Replace("`r`n","`n")),[Text.UTF8Encoding]::new($false))
    if(Test-Path -LiteralPath $recordPath){[IO.File]::Replace($temp,$recordPath,($recordPath+'.previous'))}else{[IO.File]::Move($temp,$recordPath)}
}
function Assert-Owner {
    $owner=Get-Content -LiteralPath $sessionPath -Raw|ConvertFrom-Json
    if(-not $owner.active -or $owner.agent -ne 'gemini-antigravity' -or $owner.task_id -ne $TaskId -or $owner.controller_run_id -ne $RunId){throw 'Project session is not owned by this turn'}
}
if($Stage -eq 'Bootstrap'){
    if($record){
        $changed=@()
        foreach($property in $record.basis_sources.PSObject.Properties){
            $p=Join-Path $Workspace $property.Name
            if(-not(Test-Path -LiteralPath $p) -or (Get-FileHash -LiteralPath $p).Hash -ne $property.Value){$changed+=$property.Name}
        }
        if($changed.Count){throw ('BOOTSTRAP_STATE_CHANGED: '+($changed -join ', '))}
        $record.repeat_count++;Save-Record
        if($record.repeat_count -gt 1){throw 'BOOTSTRAP_LOOP: completed unchanged prerequisites requested repeatedly'}
        Write-Output 'BOOTSTRAP_ALREADY_COMPLETE: unchanged prerequisites; proceed to Scientific, do not reread bootstrap.'
        return
    }
    # Mandatory ordered read is implemented here, not reconstructed in nested -Command strings.
    $status=Invoke-LocalGit @('status','--short')
    $head=Invoke-LocalGit @('rev-parse','HEAD')
    $summary=Invoke-LocalGit @('log','-1','--oneline')
    $ordered=@('AGENTS.md','project_coordination/START_HERE.md','project_coordination/CURRENT_STATE.md','project_coordination/ACTIVE_SESSION.json','project_coordination/ACTIVE_TASK.json','project_coordination/TASK_LEDGER.csv','project_coordination/HPC_JOB_LEDGER.csv','project_coordination/ARTIFACT_REGISTRY.csv','docs/project/PROJECT_PHASE_CHECKLIST.md')
    $hashes=[ordered]@{};$content=@{}
    foreach($relative in $ordered){
        $p=Join-Path $Workspace $relative
        if(-not(Test-Path -LiteralPath $p -PathType Leaf)){throw "BOOTSTRAP_MISSING: $relative"}
        $content[$relative]=[IO.File]::ReadAllText($p)
        $hashes[$relative]=(Get-FileHash -LiteralPath $p).Hash
    }
    $session=$content['project_coordination/ACTIVE_SESSION.json']|ConvertFrom-Json
    $task=$content['project_coordination/ACTIVE_TASK.json']|ConvertFrom-Json
    if($session.active){throw 'Another agent owns the project session'}
    if($task.task_id -ne $TaskId -or $task.status -match '(?i)^(complete|closed|PACKAGE72_C1_1_AUDIT_COMPLETED)'){throw 'Completed or mismatched task rejected before claim'}
    $taskType=Resolve-ControllerTaskType $task $Workspace
    $operation=$null
    if($taskType.task_type -eq 'QUALIFIED_EXECUTION'){
        $operation=$taskType.operation
        if($operation.path -cne $state.scientific_operation){throw 'Dispatch operation changed after controller preflight'}
        $opId=$operation.id
        $opPath=$operation.path
        $nextStage='Scientific'
    } else {
        $opId=if($state.operation_id){$state.operation_id}else{'research_preparation'}
        $opPath=if($state.scientific_operation){$state.scientific_operation}else{''}
        $nextStage='Preparation'
    }
    if($head -ne $state.repository_commit){throw 'Repository revision changed before bootstrap'}
    $registry=$content['project_coordination/ARTIFACT_REGISTRY.csv']
    if($registry.Contains(('turn-'+$RunId+'.json'))){throw 'Registered turn receipt already exists; reconcile instead of duplicating'}
    $basis=[ordered]@{}
    foreach($name in @('project_coordination/ACTIVE_TASK.json','project_coordination/CURRENT_STATE.md','project_coordination/HPC_JOB_LEDGER.csv','project_coordination/MODE1_EXECUTION_LEDGER.json')){$basis[$name]=(Get-FileHash -LiteralPath (Join-Path $Workspace $name)).Hash}
    $relativeReport='project_coordination/sessions/'+(Get-Date -Format 'yyyy-MM-dd')+'_gemini-antigravity_F1597_'+$RunId+'.md'
    $now=[datetimeoffset]::Now.ToString('o')
    $prepArtifact='results/validation/preparation-'+$RunId+'.json'
    $allowedScope=@(
        $relativeReport,
        ('project_coordination/controller/turn-'+$RunId+'.json'),
        ('results/validation/mode1_f1597/'+$RunId+'.json'),
        $prepArtifact,
        'results/validation/*',
        'scripts/validation/*',
        'tests/unit/*',
        'models/pandey_kumar_mode1/*',
        'project_coordination/ACTIVE_SESSION.json',
        'project_coordination/ACTIVE_TASK.json',
        'project_coordination/CURRENT_STATE.md',
        'project_coordination/TASK_LEDGER.csv',
        'project_coordination/ARTIFACT_REGISTRY.csv'
    )
    $claim=[ordered]@{active=$true;agent='gemini-antigravity';task_id=$TaskId;starting_commit=$head;claimed_at=$now;last_updated=$now;last_released=$null;controller_run_id=$RunId;session_report=$relativeReport;allowed_write_scope=$allowedScope}
    [IO.File]::WriteAllText($sessionPath,(($claim|ConvertTo-Json -Depth 8).Replace("`r`n","`n")),[Text.UTF8Encoding]::new($false))
    New-Item -ItemType Directory -Path (Split-Path $recordPath) -Force|Out-Null
    $script:record=[pscustomobject]@{schema=1;controller_run_id=$RunId;task_id=$TaskId;repository_commit=$head;bootstrap_status='COMPLETE';operation_id=$opId;operation_path=$opPath;task_type=$taskType.task_type;bootstrap_completed_at=$now;ordered_sources=$hashes;basis_sources=$basis;repeat_count=0;session_report=$relativeReport;scientific_checkpoint=$null;stage='BOOTSTRAP_COMPLETE';next_action=$nextStage}
    Save-Record
    [IO.File]::WriteAllText((Join-Path $Workspace $relativeReport),"# $TaskId controlled scientific step`n`nBootstrap completed once; stage=$nextStage. This note does not count as scientific progress.`n",[Text.UTF8Encoding]::new($false))
    [pscustomobject]@{status='BOOTSTRAP_COMPLETE';task=$TaskId;turn=$RunId;commit=$head;ordered_read_count=$ordered.Count;dirty_path_count=@($status).Count;next_stage=$nextStage;objective=$task.phase}|ConvertTo-Json -Depth 6
    return
}
if(-not $record -or $record.bootstrap_status -ne 'COMPLETE'){throw 'Bootstrap receipt required'}
if($record.stage -eq 'COMPLETE'){Write-Output 'TURN_ALREADY_COMPLETE; no repeat scientific operation';return}
Assert-Owner
if($Stage -eq 'Scientific'){
    if($record.scientific_checkpoint){Write-Output 'SCIENTIFIC_CHECKPOINT_ALREADY_EXISTS; use Complete';return}
    $task=Get-Content -LiteralPath $taskPath -Raw|ConvertFrom-Json
    $operation=Resolve-ControllerOperation $task $Workspace
    if($record.operation_id -cne $operation.id -or $record.operation_path -cne $operation.path -or $state.scientific_operation -cne $operation.path){throw 'Dispatch operation changed after bootstrap'}
    foreach($source in $state.sources.PSObject.Properties){if($source.Name -match '^(scripts/|models/|results/)'){if(-not(Test-Path -LiteralPath (Join-Path $Workspace $source.Name)) -or (Get-FileHash -LiteralPath (Join-Path $Workspace $source.Name)).Hash -ne $source.Value){throw 'Scientific basis/source changed after dispatch'}}}
    $probe=$operation.path
    $pinned=$state.sources.$probe
    if(-not $pinned -or (Get-FileHash -LiteralPath (Join-Path $Workspace $probe)).Hash -ne $pinned){throw 'Scientific verifier source changed after dispatch'}
    $relative='results/validation/mode1_f1597/'+$RunId+'.json'
    $output=Join-Path $Workspace $relative
    $result=Invoke-BoundedAgyProcess -FilePath (Get-Command python.exe).Source -ArgumentList @((Join-Path $Workspace $probe),'--workspace',$Workspace,'--output',$output) -WorkingDirectory $Workspace -TimeoutSeconds 120
    if($result.ExitCode -ne 0){throw ('SCIENTIFIC_OPERATION_FAILED exit='+$result.ExitCode+': '+$result.Output)}
    if(-not(Test-Path -LiteralPath $output)){throw 'Scientific operation produced no result'}
    $payload=Get-Content -LiteralPath $output -Raw|ConvertFrom-Json
    if(-not $payload.verification_passed){throw 'Scientific gradient verification failed'}
    $record.scientific_checkpoint=[pscustomobject]@{kind='NUMERICAL_FINDING';operation=$payload.operation;exit_code=0;artifact=$relative;sha256=(Get-FileHash -LiteralPath $output).Hash;created_at=[datetimeoffset]::Now.ToString('o')}
    $record.stage='SCIENTIFIC_CHECKPOINT_VERIFIED';$record.next_action='Complete';Save-Record
    if(-not(Test-ControllerScientificCheckpoint $Workspace $state)){throw 'Scientific measurement/source verification failed'}
    $report=Join-Path $Workspace $record.session_report
    $text="`n## Verified F1597 operation`n`n$($payload.finding)`n`nEvidence: $relative`n`n"+($payload.measurements|ConvertTo-Json)+"`n`nLimit: $($payload.limitation)`n`nNext: $($payload.next_operation)`n"
    [IO.File]::AppendAllText($report,$text.Replace("`r`n","`n"),[Text.UTF8Encoding]::new($false))
    $payload|ConvertTo-Json -Depth 10
    return
}
if($Stage -eq 'Preparation'){
    if($record.scientific_checkpoint){Write-Output 'SCIENTIFIC_CHECKPOINT_ALREADY_EXISTS; use Complete';return}
    $targetArtifact=if($CheckpointArtifact){$CheckpointArtifact}else{'results/validation/preparation-'+$RunId+'.json'}
    $artifactFullPath=Join-Path $Workspace $targetArtifact
    if(-not(Test-Path -LiteralPath $artifactFullPath -PathType Leaf)){throw "PREPARATION_ARTIFACT_MISSING: $targetArtifact"}
    $prep=Get-Content -LiteralPath $artifactFullPath -Raw|ConvertFrom-Json
    if($prep.schema -ne 1 -or -not $prep.finding -or $prep.finding.Trim().Length -lt 20){throw 'Invalid preparation artifact: schema 1 and substantive finding (>=20 chars) required'}
    if($null -eq $prep.evidence_sources -or @($prep.evidence_sources.PSObject.Properties).Count -lt 1){throw 'Invalid preparation artifact: evidence_sources required'}
    $prepStatus=if($prep.status){$prep.status}else{'PREPARATION_COMPLETE'}
    $record.scientific_checkpoint=[pscustomobject]@{
        kind='PREPARATION_CHECKPOINT'
        operation=$(if($prep.operation){$prep.operation}else{'research_preparation'})
        exit_code=0
        artifact=$targetArtifact
        sha256=(Get-FileHash -LiteralPath $artifactFullPath).Hash
        created_at=[datetimeoffset]::Now.ToString('o')
    }
    $record.stage='PREPARATION_CHECKPOINT_VERIFIED'
    $record.next_action='Complete'
    Save-Record
    if(-not(Test-ControllerScientificCheckpoint $Workspace $state)){throw 'Preparation checkpoint verification failed'}
    $report=Join-Path $Workspace $record.session_report
    $text="`n## Verified Research Preparation Finding`n`n$($prep.finding)`n`nEvidence: $targetArtifact`n`nStatus: $prepStatus`n"
    if($prep.qualified_operation){$text+="Qualified Operation: $($prep.qualified_operation)`n"}
    [IO.File]::AppendAllText($report,$text.Replace("`r`n","`n"),[Text.UTF8Encoding]::new($false))
    $prep|ConvertTo-Json -Depth 10
    return
}
if(-not(Test-ControllerScientificCheckpoint $Workspace $state)){throw 'A verified scientific checkpoint is required for closeout'}
$payload=Get-Content -LiteralPath (Join-Path $Workspace $record.scientific_checkpoint.artifact) -Raw|ConvertFrom-Json
$task=Get-Content -LiteralPath $taskPath -Raw|ConvertFrom-Json
if($record.scientific_checkpoint.kind -eq 'PREPARATION_CHECKPOINT'){
    $task.status=if($payload.status){$payload.status}else{'RESEARCH_PREPARATION_COMPLETE'}
    $task.phase=if($payload.finding){$payload.finding}else{'Research preparation complete'}
    $task|Add-Member -NotePropertyName last_updated -NotePropertyValue ([datetimeoffset]::Now.ToString('o')) -Force
    $nextAction=if($payload.next_operation){$payload.next_operation}else{'Advance to qualified execution or next research task'}
    $task|Add-Member -NotePropertyName next_safe_action -NotePropertyValue $nextAction -Force
    $task|Add-Member -NotePropertyName scientific_checkpoint -NotePropertyValue $record.scientific_checkpoint -Force
    if($payload.qualified_operation){
        $task.scientific_operation=$payload.qualified_operation
    } else {
        $task.scientific_operation=''
    }
    $opTitle=if($payload.title){$payload.title}else{'Research preparation'}
    $opId=if($payload.operation){$payload.operation}else{'research_preparation'}
    $classification=if($payload.classification){$payload.classification}else{'RESEARCH_PREPARATION_VERIFIED'}
} else {
    $operation=Resolve-ControllerOperation $task $Workspace
    if($operation.id -cne $record.operation_id -or $operation.path -cne $state.scientific_operation){throw 'Closeout operation mismatch'}
    $task.status=$operation.status
    $task.phase=('F1597: '+$operation.title+' measured; transfer correction remains unqualified.')
    $task|Add-Member -NotePropertyName last_updated -NotePropertyValue ([datetimeoffset]::Now.ToString('o')) -Force
    $task|Add-Member -NotePropertyName next_safe_action -NotePropertyValue $payload.next_operation -Force
    $task|Add-Member -NotePropertyName scientific_checkpoint -NotePropertyValue $record.scientific_checkpoint -Force
    $task.scientific_operation=''
    $task|Add-Member -NotePropertyName completed_operations -NotePropertyValue @(@($task.completed_operations)+$operation.id|Select-Object -Unique) -Force
    $opTitle=$operation.title
    $opId=$operation.id
    $nextAction=$payload.next_operation
    $classification=($operation.id+'_ONLY_CORRECTION_PENDING')
}
[IO.File]::WriteAllText($taskPath,(($task|ConvertTo-Json -Depth 20).Replace("`r`n","`n")),[Text.UTF8Encoding]::new($false))
$record.stage='COMPLETE';$record.next_action=$nextAction;Save-Record
[IO.File]::AppendAllText((Join-Path $Workspace $record.session_report),"`nTurn complete. No unqualified HPC job submitted.`n`nFinished`n")
$session=Get-Content -LiteralPath $sessionPath -Raw|ConvertFrom-Json
$session.active=$false;$session.last_released=[datetimeoffset]::Now.ToString('o');$session.last_updated=$session.last_released
[IO.File]::WriteAllText($sessionPath,(($session|ConvertTo-Json -Depth 10).Replace("`r`n","`n")),[Text.UTF8Encoding]::new($false))
$registry=Join-Path $Workspace 'project_coordination/ARTIFACT_REGISTRY.csv'
$ledger=Join-Path $Workspace 'project_coordination/TASK_LEDGER.csv'
$newPaths=@($record.session_report,('project_coordination/controller/turn-'+$RunId+'.json'),$record.scientific_checkpoint.artifact)
if($operation -and $operation.qualification -and $operation.qualification.qualification_artifact){
    $qArt = $operation.qualification.qualification_artifact
    if(Test-Path -LiteralPath (Join-Path $Workspace $qArt)){
        $newPaths += $qArt
    }
}
$newPaths = @($newPaths | Select-Object -Unique)
foreach($relative in $newPaths){
    $row=[pscustomobject]@{artifact_id=('F1597-'+$RunId+'-'+[IO.Path]::GetFileName($relative));stage='Mode-I';canonical_path=$relative;type='verified_diagnostic_evidence';status='verified';created_by='gemini-antigravity';source_commit=$record.repository_commit;sha256=(Get-FileHash -LiteralPath (Join-Path $Workspace $relative)).Hash;supersedes='';notes=($opTitle+'; not a transfer qualification')}
    $csv=$row|ConvertTo-Csv -NoTypeInformation
    [IO.File]::AppendAllText($registry,$csv[1]+"`n")
}
$row=[pscustomobject]@{task_id=($TaskId+'-'+$opId);stage='Mode-I';title=$opTitle;status='bounded_step_complete';agent='gemini-antigravity';base_commit=$record.repository_commit;result_commit='';write_scope=($newPaths -join ';');job_id='';classification=$classification;next_task=$nextAction;updated_at=$session.last_released}
$csv=$row|ConvertTo-Csv -NoTypeInformation;[IO.File]::AppendAllText($ledger,$csv[1]+"`n")
$staged=Invoke-LocalGit @('diff','--cached','--name-only')
if($staged){throw 'Pre-existing staged paths must be preserved; closeout will not include them'}
Invoke-LocalGit (@('add','--')+$newPaths+@('project_coordination/ACTIVE_SESSION.json','project_coordination/ACTIVE_TASK.json','project_coordination/ARTIFACT_REGISTRY.csv','project_coordination/TASK_LEDGER.csv'))
Invoke-LocalGit @('diff','--cached','--check')
Invoke-LocalGit @('commit','-m',('research(mode1): record '+$opId))
Invoke-LocalGit @('push','origin','HEAD:main','HEAD:mode2-pandey-kumar-reproduction')
Write-Output ('SCIENTIFIC_STEP_COMPLETE: '+$nextAction)
