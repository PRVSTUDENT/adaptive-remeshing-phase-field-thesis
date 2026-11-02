# Durable planning transport. Never executes reviewer text or modifies scientific accounting.
function Assert-ControllerActiveTaskDispatch([string]$Workspace) {
    $task=Get-Content -LiteralPath (Join-Path $Workspace 'project_coordination/ACTIVE_TASK.json') -Raw|ConvertFrom-Json
    $closed=@(Import-Csv -LiteralPath (Join-Path $Workspace 'project_coordination/TASK_LEDGER.csv')|Where-Object {
        $_.task_id -eq $task.task_id -and $_.status -match '^(?i:complete|completed|closed|done)$'
    })
    if($closed.Count){throw ('COMPLETED_TASK_REJECTED: '+$task.task_id+'; authoritative active-file/ledger conflict; do not reactivate or guess a successor')}
}

function Write-ControllerRecoveryNewFile([string]$Path, [string]$Text) {
    $ErrorActionPreference='Stop'
    $bytes=[Text.UTF8Encoding]::new($false).GetBytes($Text)
    $tmp=$Path+'.'+[guid]::NewGuid().ToString('N')+'.tmp'
    $stream=[IO.File]::Open($tmp,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::None)
    try{$stream.Write($bytes,0,$bytes.Length);$stream.Flush($true)}finally{$stream.Dispose()}
    # Move without overwrite: concurrent/restarted dispatch cannot replace evidence.
    [IO.File]::Move($tmp,$Path)
}

function New-ControllerFailurePacket {
    param([string]$Workspace, [string]$CheckpointPath, $State, [string]$ErrorText,
          [string]$Stage='controller', [string]$Root=(Join-Path $env:USERPROFILE 'OpenClawPAD/failure_recovery'))
    $ErrorActionPreference='Stop'
    if(-not $State -and (Test-Path -LiteralPath $CheckpointPath)) { $State=Read-ControllerCheckpoint $CheckpointPath }
    $run=if($State.run_id){[string]$State.run_id}else{'startup'}
    $key=Get-ControllerTextHash ($Workspace.ToLowerInvariant()+'|'+$run)
    $dir=Join-Path $Root $key
    [void][IO.Directory]::CreateDirectory($dir)
    $packetPath=Join-Path $dir 'packet.json'
    if(Test-Path -LiteralPath $packetPath) {
        $pin=Join-Path $dir 'packet.sha256'
        if(-not(Test-Path -LiteralPath $pin) -or (Get-FileHash -LiteralPath $packetPath).Hash -cne ([IO.File]::ReadAllText($pin)).Trim()){throw 'RECOVERY_PACKET_INCOMPLETE_OR_CHANGED: preserve and reconcile'}
        return $dir
    }
    Write-ControllerRecoveryNewFile (Join-Path $dir 'snapshot.intent.json') (@{utc=[DateTimeOffset]::UtcNow.ToString('o')}|ConvertTo-Json)
    $snapshots=[ordered]@{}
    $paths=@('project_coordination/ACTIVE_TASK.json','project_coordination/ACTIVE_SESSION.json',
        'project_coordination/TASK_LEDGER.csv','project_coordination/HPC_JOB_LEDGER.csv',
        'project_coordination/MODE1_EXECUTION_LEDGER.json','project_coordination/CURRENT_STATE.md')
    $active=$null
    foreach($relative in $paths) {
        $p=Join-Path $Workspace $relative
        if(Test-Path -LiteralPath $p) {
            $copy=Join-Path $dir ([IO.Path]::GetFileName($p))
            if(-not(Test-Path -LiteralPath $copy)){[IO.File]::Copy($p,$copy,$false)}
            $snapshots[$relative]=(Get-FileHash -LiteralPath $copy).Hash
            if($relative -eq 'project_coordination/ACTIVE_TASK.json'){$active=Get-Content -LiteralPath $copy -Raw|ConvertFrom-Json}
        }
    }
    $checkpoint=$null
    if(Test-Path -LiteralPath $CheckpointPath) {
        $copy=Join-Path $dir 'controller_checkpoint.json'
        if(-not(Test-Path -LiteralPath $copy)){[IO.File]::Copy($CheckpointPath,$copy,$false)}
        $checkpoint=@{path=$CheckpointPath;archive=$copy;sha256=(Get-FileHash -LiteralPath $copy).Hash;state=$State.state}
    }
    $artifacts=@()
    foreach($relative in @($State.reconciliation.deliverables)+@($State.reconciliation.session_report,$State.reconciliation.bootstrap_record,$State.partial_output,$State.live_output_log)) {
        if(-not $relative){continue}
        $p=if([IO.Path]::IsPathRooted($relative)){$relative}else{Join-Path $Workspace $relative}
        $exists=Test-Path -LiteralPath $p -PathType Leaf
        $artifacts+=@{path=$p;exists=$exists;sha256=$(if($exists){(Get-FileHash -LiteralPath $p).Hash}else{$null})}
    }
    $closed=@()
    if($active -and (Test-Path -LiteralPath (Join-Path $dir 'TASK_LEDGER.csv'))) {
        $closed=@(Import-Csv -LiteralPath (Join-Path $dir 'TASK_LEDGER.csv')|Where-Object {$_.task_id -eq $active.task_id -and $_.status -match '^(?i:complete|completed|closed|done)$'})
    }
    $ledger=Join-Path $dir 'HPC_JOB_LEDGER.csv'
    $pbs=if(Test-Path -LiteralPath $ledger){@([regex]::Matches([IO.File]::ReadAllText($ledger),'\b\d+\.mmaster02\b')|ForEach-Object Value|Sort-Object -Unique)}else{@()}
    $packet=[ordered]@{schema=1;run_id=$run;turn=$State.turn;operation_id=$State.operation_id;
        original_task=$State.task_id;resolved_active_task=$active.task_id;active_task_status=$active.status;
        task_identity_conflict=($closed.Count -gt 0);error=$ErrorText;failure_stage=$Stage;
        created_utc=[DateTimeOffset]::UtcNow.ToString('o');last_checkpoint=$checkpoint;
        recovered_artifacts=$artifacts;sources=$snapshots;pbs_references=$pbs;
        scheduler_observation='Ledger references only; live scheduler not queried';
        outstanding_scientific_work=$active;replay_allowed=$false}
    Write-ControllerRecoveryNewFile $packetPath ($packet|ConvertTo-Json -Depth 30)
    Write-ControllerRecoveryNewFile (Join-Path $dir 'packet.sha256') ((Get-FileHash -LiteralPath $packetPath).Hash)
    return $dir
}

function Invoke-ControllerFailureHandoff {
    param([string]$Workspace,[string]$CheckpointPath,$State,[string]$ErrorText,[string]$Stage='controller',
        [string]$Root=(Join-Path $env:USERPROFILE 'OpenClawPAD/failure_recovery'),
        [switch]$LaunchPad,[switch]$NoTransport,[scriptblock]$Transport)
    $ErrorActionPreference='Stop'
    $dir=New-ControllerFailurePacket -Workspace $Workspace -CheckpointPath $CheckpointPath -State $State -ErrorText $ErrorText -Stage $Stage -Root $Root
    $intent=Join-Path $dir 'dispatch.intent.json'
    if(Test-Path -LiteralPath $intent){
        $observation=Join-Path $dir ('observation-'+(Get-ControllerTextHash ($Stage+'|'+$ErrorText))+'.json')
        if(-not(Test-Path -LiteralPath $observation)){
            Write-ControllerRecoveryNewFile $observation (@{stage=$Stage;error=$ErrorText;utc=[DateTimeOffset]::UtcNow.ToString('o')}|ConvertTo-Json)
        }
        return [pscustomobject]@{status='RECOVERY_ALREADY_RECORDED_NO_REDISPATCH';packet=$dir}
    }
    # Reserve the handoff before touching the bridge. Crash or timeout is uncertain, never auto-retried.
    try{Write-ControllerRecoveryNewFile $intent (@{utc=[DateTimeOffset]::UtcNow.ToString('o');attempt=1}|ConvertTo-Json)}
    catch {return [pscustomobject]@{status='RECOVERY_ALREADY_RESERVED';packet=$dir}}
    try {
        if($NoTransport){throw 'ChatGPT transport disabled; packet remains pending'}
        $body=[IO.File]::ReadAllText((Join-Path $dir 'packet.json'))
        $p=$body|ConvertFrom-Json
        $decision=Invoke-ControllerSupervisor -Workspace $Workspace -Kind ERROR -Evidence $body -RunId $p.run_id -Turn ([int]$p.turn) -SafetyBlocked -LaunchPad:$LaunchPad -Transport $Transport -ArchiveRoot (Join-Path $dir 'bridge')
        Write-ControllerRecoveryNewFile (Join-Path $dir 'acknowledged.json') (@{packet_sha256=(Get-FileHash -LiteralPath (Join-Path $dir 'packet.json')).Hash;decision=$decision;execution_allowed=$false}|ConvertTo-Json -Depth 12)
        Write-ControllerRecoveryNewFile (Join-Path $dir 'acknowledged.sha256') ((Get-FileHash -LiteralPath (Join-Path $dir 'acknowledged.json')).Hash)
        return [pscustomobject]@{status='RECOVERY_ACKNOWLEDGED_VALIDATION_REQUIRED';packet=$dir;instruction=$decision.instruction}
    } catch {
        Write-ControllerRecoveryNewFile (Join-Path $dir 'pending.json') (@{status='PENDING_RECONCILIATION';error=($_|Out-String);retry_allowed=$false}|ConvertTo-Json)
        return [pscustomobject]@{status='RECOVERY_PENDING_TRANSPORT';packet=$dir}
    }
}

function Test-ControllerFailureResumePlan([string]$Workspace,[string]$PacketDirectory) {
    $ErrorActionPreference='Stop'
    $packet=Join-Path $PacketDirectory 'packet.json'
    $hash=(Get-FileHash -LiteralPath $packet).Hash
    if($hash -cne ([IO.File]::ReadAllText((Join-Path $PacketDirectory 'packet.sha256'))).Trim()){throw 'RECOVERY_PACKET_CHANGED'}
    $p=Get-Content -LiteralPath $packet -Raw|ConvertFrom-Json
    $ack=Get-Content -LiteralPath (Join-Path $PacketDirectory 'acknowledged.json') -Raw|ConvertFrom-Json
    if((Get-FileHash -LiteralPath (Join-Path $PacketDirectory 'acknowledged.json')).Hash -cne ([IO.File]::ReadAllText((Join-Path $PacketDirectory 'acknowledged.sha256'))).Trim()){throw 'RECOVERY_ACK_CHANGED'}
    if($ack.packet_sha256 -cne $hash){throw 'RECOVERY_ACK_MISMATCH'}
    $e=Get-ControllerEvidence $Workspace
    if($e.session.active){throw 'RECOVERY_FOREIGN_OR_ACTIVE_SESSION: reconcile ownership first'}
    if($p.task_identity_conflict -or $e.task.task_id -cne $p.resolved_active_task){throw 'RECOVERY_TASK_IDENTITY_RECONCILIATION_REQUIRED'}
    Assert-ControllerActiveTaskDispatch $Workspace
    foreach($rel in @('project_coordination/ACTIVE_TASK.json','project_coordination/HPC_JOB_LEDGER.csv','project_coordination/MODE1_EXECUTION_LEDGER.json')){
        if((Get-FileHash -LiteralPath (Join-Path $Workspace $rel)).Hash -cne $p.sources.$rel){throw 'RECOVERY_CONTEXT_CHANGED: re-review current task and once-only accounting'}
    }
    if($ack.decision.action -notin @('CONTINUE','DIAGNOSE')){throw 'RECOVERY_REVIEWER_STOP_OR_WAIT'}
    $resolved=Resolve-ControllerInstruction $Workspace $ack.decision.instruction
    # Planning result only. The ordinary bootstrap, qualified-operation and once-only submission gates still apply.
    $plan=Get-ControllerPreparationPlan $Workspace $resolved.instruction
    if(-not $plan.dispatch_ready){throw 'RECOVERY_INSTRUCTION_NOT_QUALIFIED'}
    return $resolved.instruction
}
