$ErrorActionPreference = 'Stop'

function Get-ControllerTextHash([string]$Text) {
    $sha = [Security.Cryptography.SHA256]::Create()
    try { return ([BitConverter]::ToString($sha.ComputeHash([Text.Encoding]::UTF8.GetBytes($Text)))).Replace('-','').ToLowerInvariant() }
    finally { $sha.Dispose() }
}

function Write-ControllerCheckpoint([string]$Path, $State) {
    $State.updated_at = [DateTimeOffset]::UtcNow.ToString('o')
    $payload = $State | ConvertTo-Json -Depth 30 -Compress
    $envelope = @{schema=1; payload=$payload; sha256=(Get-ControllerTextHash $payload)} | ConvertTo-Json -Depth 5
    $temp = $Path + '.' + [guid]::NewGuid().ToString('N') + '.tmp'
    try {
        [IO.File]::WriteAllText($temp, $envelope, [Text.UTF8Encoding]::new($false))
        if (Test-Path -LiteralPath $Path) { [IO.File]::Replace($temp, $Path, ($Path + '.previous')) }
        else { [IO.File]::Move($temp, $Path) }
    } finally { if (Test-Path -LiteralPath $temp) { Remove-Item -LiteralPath $temp } }
}

function Read-ControllerCheckpoint([string]$Path) {
    if (-not (Test-Path -LiteralPath $Path)) { return $null }
    try {
        $e = Get-Content -LiteralPath $Path -Raw -Encoding UTF8 | ConvertFrom-Json
        if ($e.schema -ne 1 -or (Get-ControllerTextHash $e.payload) -cne $e.sha256) { throw 'checksum/schema mismatch' }
        $s = $e.payload | ConvertFrom-Json
        if ($s.state -notin @('PENDING','RUNNING','CHECKPOINTED','RECOVERY_REQUIRED','COMPLETED','BLOCKED') -or -not $s.task_id -or -not $s.run_id -or $null -eq $s.recovery_count) { throw 'invalid state fields' }
        return $s
    } catch { throw "BLOCKED: corrupted controller checkpoint; preserve and inspect $Path. $($_.Exception.Message)" }
}

function Get-ControllerEvidence([string]$Workspace) {
    $sources = [ordered]@{}
    $task = $null; $session = $null
    foreach ($relative in @('project_coordination/ACTIVE_TASK.json','project_coordination/CURRENT_STATE.md','project_coordination/ACTIVE_SESSION.json','project_coordination/HPC_JOB_LEDGER.csv','project_coordination/MODE1_EXECUTION_LEDGER.json','project_coordination/TASK_LEDGER.csv')) {
        $p = Join-Path $Workspace $relative
        if (-not (Test-Path -LiteralPath $p -PathType Leaf)) { throw "BLOCKED: missing authoritative source $relative" }
        $sources[$relative] = (Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash
        if ($relative -like '*/ACTIVE_TASK.json') { $task = Get-Content -LiteralPath $p -Raw -Encoding UTF8 | ConvertFrom-Json }
        if ($relative -like '*/ACTIVE_SESSION.json') { $session = Get-Content -LiteralPath $p -Raw -Encoding UTF8 | ConvertFrom-Json }
    }
    foreach ($relative in @('scripts/controller/Antigravity-Autonomous-Loop.ps1','scripts/controller/Controller-Recovery.ps1','scripts/validation/Invoke-BoundedAgyProcess.ps1','scripts/validation/AgyControllerPolicy.ps1','scripts/validation/AgyCredentialStores.ps1','models/pandey_kumar_mode1/15_energy_qualification_small/f42_mixed_uel.for')) {
        $p=Join-Path $Workspace $relative
        if (Test-Path -LiteralPath $p -PathType Leaf) { $sources[$relative]=(Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash }
    }
    if (-not $task.task_id -or $session.active -isnot [bool]) { throw 'BLOCKED: invalid task/session identity' }
    $report = ''; $reportBytes=0
    if ($session.session_report) {
        $root = [IO.Path]::GetFullPath((Join-Path $Workspace 'project_coordination/sessions')) + [IO.Path]::DirectorySeparatorChar
        $p = [IO.Path]::GetFullPath((Join-Path $Workspace $session.session_report))
        if (-not $p.StartsWith($root,[StringComparison]::OrdinalIgnoreCase)) { throw 'BLOCKED: unsafe session report path' }
        if (Test-Path -LiteralPath $p -PathType Leaf) {
            $sources[[string]$session.session_report] = (Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash
            $report = [string]$session.session_report
            $reportBytes=(Get-Item -LiteralPath $p).Length
        }
    }
    # Exact IDs are observations from durable ledgers, never a claim of live scheduler state.
    $receipts = @([regex]::Matches((Get-Content -LiteralPath (Join-Path $Workspace 'project_coordination/HPC_JOB_LEDGER.csv') -Raw), '\b\d+\.mmaster02\b') | ForEach-Object Value | Sort-Object -Unique)
    $execution = Get-Content -LiteralPath (Join-Path $Workspace 'project_coordination/MODE1_EXECUTION_LEDGER.json') -Raw -Encoding UTF8 | ConvertFrom-Json
    $commit=''
    if(Test-Path -LiteralPath (Join-Path $Workspace '.git')){ $commit=(& git -C $Workspace rev-parse HEAD).Trim() }
    return [pscustomobject]@{task=$task; session=$session; sources=$sources; pbs_receipts=$receipts; execution_accounting=$execution; report=$report; report_bytes=$reportBytes; commit=$commit}
}

function Resolve-ControllerInstruction([string]$Workspace, [string]$Instruction) {
    $e = Get-ControllerEvidence $Workspace
    $terminal = [string]$e.task.status -match '(?i)(completed|classified|closed|^done$)'
    $heading = ($Instruction -split "`n")[0]
    $id = [regex]::Match($heading,'\bF\d+\b').Value
    $currentId = [regex]::Match([string]$e.task.task_id,'\bF\d+\b').Value
    $stale = $terminal -and $id -and $id -eq $currentId
    if ($stale -or $Instruction -match '^CONTROLLER_TASK: NEXT_UNRESOLVED') {
        $Instruction = @"
CONTROLLER_TASK: NEXT_UNRESOLVED
Authoritative predecessor: $($e.task.task_id), status $($e.task.status).
Read CURRENT_STATE.md, ACTIVE_TASK.json, TASK_LEDGER.csv, exact session records and HPC/execution ledgers before choosing work. Completed predecessor work must not execute again.
Perform the mandatory ordered bootstrap in one batched PowerShell call: read the required files in order, then emit current state and only relevant task/job/registry rows plus source hashes. Do not print entire historical ledgers into model context or read each historical file in a separate model round trip. Claim the session promptly after verifying it is inactive.
Select one next scientifically useful executable action from current evidence. Immediately execute independently ready qualified serial Mode-I jobs through scripts/hpc/Invoke-Mode1Execution.ps1 under the standing limits and once-only accounting. No administrative approval is needed. Do not repeat the completed audit, submit dependent work before quantitative predecessor acceptance, or manufacture a job. If scientific failure blocks execution, do only the smallest essential hypothesis/equation/checkpoint review and report its concrete finding promptly. Preserve the frozen production UEL and authentic failed results.
Create the owned session report within 120 seconds, recording exact sources and the first concrete finding or blocker. Update it after each substantive action and at least every 180 seconds. A session claim, heartbeat, timestamp, or tool chatter is not a saved result. The controller will stop after 300 seconds without durable evidence. Do not spend the turn rereading broad history. Close the owned session truthfully and return evidence, actual PBS receipts if any, and the exact next safe action. End with Finished.
"@
    }
    return [pscustomobject]@{instruction=$Instruction; stale_replaced=[bool]$stale; evidence=$e}
}

function New-ControllerTurnState($Evidence, [int]$Turn, [string]$Instruction, [int]$RecoveryCount = 0) {
    return [pscustomobject]@{schema=1; run_id=[guid]::NewGuid().ToString(); task_id=[string]$Evidence.task.task_id; predecessor_task_id=[string]$Evidence.task.task_id; repository_commit=$Evidence.commit; initial_session_active=[bool]$Evidence.session.active; initial_session_hash=$Evidence.sources['project_coordination/ACTIVE_SESSION.json']; owned_session_fingerprint=''; turn=$Turn; state='PENDING'; recovery_count=$RecoveryCount; process_id=0; started_at=[DateTimeOffset]::UtcNow.ToString('o'); updated_at=''; last_confirmed_action=[string]$Evidence.task.status; sources=$Evidence.sources; pbs_receipts=$Evidence.pbs_receipts; execution_accounting=$Evidence.execution_accounting; session=$Evidence.session; session_report=$Evidence.report; progress_signature=''; last_evidence_at=''; conversation_id=''; live_buffer=''; stop_reason=''; original_instruction_hash=(Get-ControllerTextHash $Instruction); partial_output=''; partial_sha256=''; next_safe_action='Execute only reconciled instruction'; block_reason=''}
}

function Sync-ControllerOwnedSession($Evidence,$State) {
    if(-not $Evidence.session.active){return}
    $s=$Evidence.session; $claim=[datetimeoffset]::MinValue
    $fingerprint=Get-ControllerTextHash ((@($s.agent,$s.task_id,$s.claimed_at,$s.starting_commit)) -join '|')
    if($State.owned_session_fingerprint){
        if($fingerprint -ne $State.owned_session_fingerprint){throw 'Active session ownership changed during owned CLI execution'}
    } else {
        if($State.initial_session_active -or $s.agent -ne 'gemini-antigravity' -or -not $s.task_id -or
            -not [datetimeoffset]::TryParse([string]$s.claimed_at,[ref]$claim) -or $claim -lt [datetimeoffset]::Parse($State.started_at) -or
            ($State.repository_commit -and $s.starting_commit -ne $State.repository_commit) -or
            $State.initial_session_hash -eq $Evidence.sources['project_coordination/ACTIVE_SESSION.json']){throw 'Cannot establish ownership of active repository session'}
        $State.owned_session_fingerprint=$fingerprint
        Write-Host "[SESSION] owned task=$($s.task_id); predecessor=$($State.predecessor_task_id)"
    }
    # The live task may differ from the completed predecessor in ACTIVE_TASK.json.
    $State.task_id=[string]$s.task_id
}

function Update-ControllerEvidence([string]$Workspace, [string]$Path, $State) {
    $e = Get-ControllerEvidence $Workspace
    Sync-ControllerOwnedSession $e $State
    $State.sources=$e.sources; $State.pbs_receipts=$e.pbs_receipts; $State.execution_accounting=$e.execution_accounting
    if (-not $e.session.active -and -not $State.owned_session_fingerprint) { $State.task_id=[string]$e.task.task_id }
    $State.last_confirmed_action=[string]$e.task.status; $State.session=$e.session; $State.session_report=$e.report
    $State | Add-Member -NotePropertyName report_bytes -NotePropertyValue $e.report_bytes -Force
    Write-ControllerCheckpoint $Path $State
}

function Set-ControllerInterrupted([string]$Workspace, [string]$Path, $State, [string]$Partial) {
    # Save partial bytes before any reconciliation that can fail.
    $partialPath = $Path + '.' + $State.run_id + '.partial.txt'
    [IO.File]::WriteAllText($partialPath,$Partial,[Text.UTF8Encoding]::new($false))
    $State.partial_output=$partialPath; $State.partial_sha256=(Get-FileHash -LiteralPath $partialPath -Algorithm SHA256).Hash
    $State.state='CHECKPOINTED'; Write-ControllerCheckpoint $Path $State
    try {
        $e = Get-ControllerEvidence $Workspace
        # Bind to a newly claimed matching invocation, independently of predecessor ID.
        Sync-ControllerOwnedSession $e $State
        if ($e.session.active) {
            $sessionPath = Join-Path $Workspace 'project_coordination/ACTIVE_SESSION.json'
            $e.session.active=$false
            $e.session | Add-Member -NotePropertyName interruption_checkpoint -NotePropertyValue $Path -Force
            $e.session.last_updated=[datetimeoffset]::UtcNow.ToString('o')
            # Preserve every other session field and the old completion timestamp.
            [IO.File]::WriteAllText($sessionPath,($e.session|ConvertTo-Json -Depth 20),[Text.UTF8Encoding]::new($false))
        }
        Update-ControllerEvidence $Workspace $Path $State
        if ($State.stop_reason -eq 'NO_DURABLE_PROGRESS') { throw 'No durable result within progress deadline; inspect live log before another model call' }
        if ($State.recovery_count -ge 1) { throw 'Bounded recovery already used; no further model calls' }
        $State.state='RECOVERY_REQUIRED'
        $State.next_safe_action='Evidence-only reconciliation in a fresh conversation; no solver, submission, or scientific changes'
    } catch { $State.state='BLOCKED'; $State.block_reason=$_.Exception.Message; $State.next_safe_action='Inspect preserved evidence and resolve the recorded block' }
    Write-ControllerCheckpoint $Path $State
    return $State
}

function Get-ControllerRecoveryInstruction($State) {
    if (-not $State.partial_output -or -not (Test-Path -LiteralPath $State.partial_output -PathType Leaf) -or
        (Get-FileHash -LiteralPath $State.partial_output -Algorithm SHA256).Hash -ne $State.partial_sha256) {
        throw 'BLOCKED: missing or modified recovery evidence; never replay the original instruction'
    }
    return @"
CONTROLLER_TASK: EVIDENCE_ONLY_RECOVERY
Recover interrupted task $($State.task_id). Checkpoint: $($State.partial_output); SHA256 $($State.partial_sha256).
Do not repeat the original instruction. Read the checkpoint and exact task/session/job/execution ledgers, existence-check partial artifacts, and reconcile already completed work. Receipts remain reserved exactly once. Use guarded qstat only if exact job state is needed. No qsub, Mode1Execution, solver, numerical changes or new experiment is allowed in this recovery turn. Complete only unfinished accounting/reporting in the owned scope; do not repeat a completed audit. If evidence is insufficient, report BLOCKED. Release the owned session. Return verified findings, existing PBS IDs and a proposed next safe action; end with Finished.
"@
}

function Get-ControllerBudget([string]$PrintTimeout,[int]$Cap,[int]$Reserve=120) {
    $m=[regex]::Match($PrintTimeout,'^(\d+)(s|m|h)$')
    if (-not $m.Success) { throw 'Invalid print timeout' }
    $total=[int][Math]::Min($Cap,([double]$m.Groups[1].Value * @{s=1;m=60;h=3600}[$m.Groups[2].Value]))
    $closeout=[int][Math]::Min($Reserve,[Math]::Floor($total/4))
    if ($total -lt 4) { throw 'Insufficient controller turn budget' }
    return [pscustomobject]@{total=$total; work=($total-$closeout); closeout=$closeout}
}

function Complete-ControllerTurn([string]$Workspace,[string]$Path,$State,[string]$Response,[switch]$VerifiedReceipt) {
    Update-ControllerEvidence $Workspace $Path $State
    if ($State.session.active -or $Response -match '(?im)^\s*BLOCKED\b' -or (-not $VerifiedReceipt -and $Response -notmatch '(?s)Finished\s*$')) {
        $State.state='BLOCKED'; $State.block_reason='Response incomplete, explicitly blocked, or repository session not released'
    } else {
        $State.state='COMPLETED'
        $State.next_safe_action='Completed response preserved; reconcile next instruction against current artifacts'
    }
    $State | Add-Member -NotePropertyName response -NotePropertyValue $Response -Force
    Write-ControllerCheckpoint $Path $State
    return $State.state
}

function Test-ControllerDurableProgress($State) {
    # Exclude ACTIVE_SESSION, task/status timestamps, source hashes and raw model chatter.
    if(-not $State.PSObject.Properties['progress_evidence']){ $State|Add-Member -NotePropertyName progress_evidence -NotePropertyValue @{} }
    if($State.progress_evidence -isnot [Collections.IDictionary]){
        $map=@{};foreach($property in $State.progress_evidence.PSObject.Properties){$map[$property.Name]=$property.Value};$State.progress_evidence=$map
    }
    $changed=$false
    $names=if($State.sources -is [Collections.IDictionary]){$State.sources.Keys}else{$State.sources.PSObject.Properties.Name}
    foreach($name in $names){
        $value=if($State.sources -is [Collections.IDictionary]){$State.sources[$name]}else{$State.sources.$name}
        $report=$name -eq $State.session_report -and $State.owned_session_fingerprint -and $State.report_bytes -ge 160
        if($report -or $name -in @('project_coordination/HPC_JOB_LEDGER.csv','project_coordination/MODE1_EXECUTION_LEDGER.json')){
            if($State.progress_signature -and $State.progress_evidence[$name] -ne $value){$changed=$true}
            $State.progress_evidence[$name]=$value
        }
    }
    # Removed predecessor reports and changed session IDs do not count as progress.
    $State.progress_signature='BASELINED'
    if($changed){$State.last_evidence_at=[datetimeoffset]::UtcNow.ToString('o')}
    return $changed
}

function Write-ControllerStreamEvent($State,[string]$Chunk) {
    $State.live_buffer+=$Chunk
    while($State.live_buffer.Contains("`n")){
        $split=$State.live_buffer.IndexOf("`n");$line=$State.live_buffer.Substring(0,$split);$State.live_buffer=$State.live_buffer.Substring($split+1)
        try{$event=$line|ConvertFrom-Json -ErrorAction Stop}catch{continue}
        if($event.event -eq 'init'){
            $State.conversation_id=[string]$event.conversation_id
            Write-Host "[AGY] conversation=$($State.conversation_id) initialized"
        }elseif($event.event -eq 'step_update'){
            Write-Host "[AGY] step=$($event.step_update.step_index) type=$($event.step_update.step_type) state=$($event.step_update.state)"
        }elseif($event.event -eq 'result'){Write-Host "[AGY] result=$($event.result.status)"}
    }
}

function ConvertFrom-ControllerStream([string]$Raw) {
    $conversation=''
    foreach($line in ($Raw -split "`n")){
        try{$event=$line|ConvertFrom-Json -ErrorAction Stop}catch{continue}
        if($event.event -eq 'init'){$conversation=[string]$event.conversation_id}
        if($event.event -eq 'result' -and $event.result.status){return ($event.result|ConvertTo-Json -Depth 30)+"`n"+$(if($Raw -match '(?i)\[agy\] print timeout.*returning partial output'){'[agy] print timeout returning partial output'}else{''})}
    }
    if($Raw -match '(?i)\[agy\] print timeout.*returning partial output'){
        return (@{conversation_id=$conversation;status='SUCCESS';response=''}|ConvertTo-Json)+"`n[agy] print timeout returning partial output"
    }
    return $Raw
}
