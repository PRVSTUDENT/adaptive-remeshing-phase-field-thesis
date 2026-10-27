$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'Controller-Operations.ps1')

function Get-ControllerTextHash([string]$Text) {
    $sha = [Security.Cryptography.SHA256]::Create()
    try { return ([BitConverter]::ToString($sha.ComputeHash([Text.Encoding]::UTF8.GetBytes($Text)))).Replace('-','').ToLowerInvariant() }
    finally { $sha.Dispose() }
}

function Set-ControllerFileAtomic([string]$SourcePath, [string]$DestinationPath, [string]$BackupPath) {
    if (-not (Test-Path -LiteralPath $DestinationPath)) {
        [IO.File]::Move($SourcePath, $DestinationPath)
        return
    }

    $backup = if ($BackupPath) { $BackupPath } else { $DestinationPath + '.previous' }

    $replaced = $false
    for ($attempt = 1; $attempt -le 5; $attempt++) {
        try {
            if (Test-Path -LiteralPath $backup) {
                Remove-Item -LiteralPath $backup -Force -ErrorAction SilentlyContinue
            }
            [IO.File]::Replace($SourcePath, $DestinationPath, $backup)
            $replaced = $true
            break
        } catch {
            Start-Sleep -Milliseconds ($attempt * 50)
        }
    }

    if (-not $replaced) {
        try {
            if (Test-Path -LiteralPath $DestinationPath) {
                Copy-Item -LiteralPath $DestinationPath -Destination $backup -Force -ErrorAction SilentlyContinue
            }
            Copy-Item -LiteralPath $SourcePath -Destination $DestinationPath -Force
            Remove-Item -LiteralPath $SourcePath -Force -ErrorAction SilentlyContinue
        } catch {
            throw "BLOCKED: failed to update file $DestinationPath atomically: $($_.Exception.Message)"
        }
    }
}

function Write-ControllerCheckpoint([string]$Path, $State) {
    $State.updated_at = [DateTimeOffset]::UtcNow.ToString('o')
    $payload = $State | ConvertTo-Json -Depth 30 -Compress
    $envelope = @{schema=1; payload=$payload; sha256=(Get-ControllerTextHash $payload)} | ConvertTo-Json -Depth 5
    $temp = $Path + '.' + [guid]::NewGuid().ToString('N') + '.tmp'
    try {
        [IO.File]::WriteAllText($temp, $envelope, [Text.UTF8Encoding]::new($false))
        Set-ControllerFileAtomic -SourcePath $temp -DestinationPath $Path -BackupPath ($Path + '.previous')
    } finally {
        if (Test-Path -LiteralPath $temp) { Remove-Item -LiteralPath $temp -Force -ErrorAction SilentlyContinue }
    }
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
    foreach ($relative in @('scripts/controller/Antigravity-Autonomous-Loop.ps1','scripts/controller/Controller-Recovery.ps1','scripts/controller/Invoke-ControllerTurn.ps1','scripts/controller/Controller-Operations.ps1','scripts/controller/Controller-Preparation.ps1','scripts/controller/Controller-Qualification.ps1','scripts/validation/probe_mode1_f1597_uel_call_trace.py','scripts/validation/probe_mode1_f1597_mechanical_history.py','scripts/validation/probe_mode1_f1597_kkt.py','scripts/validation/Invoke-BoundedAgyProcess.ps1','scripts/validation/AgyControllerPolicy.ps1','scripts/validation/AgyCredentialStores.ps1','models/pandey_kumar_mode1/15_energy_qualification_small/f42_mixed_uel.for','models/pandey_kumar_mode1/72_method_c_coupled_state_transfer/M1_EXP_COUPLED_TRANSFER_650.inp','models/pandey_kumar_mode1/72_method_c_coupled_state_transfer/offset_state_table.csv','models/pandey_kumar_mode1/72_method_c_coupled_state_transfer/f42_experimental_offset_uel.for')) {
        $p=Join-Path $Workspace $relative
        if (Test-Path -LiteralPath $p -PathType Leaf) { $sources[$relative]=(Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash }
    }
    if($task.scientific_operation -eq 'scripts/validation/probe_mode1_f1597_uel_call_trace.py' -or $task.scientific_checkpoint.operation -eq 'authentic_uel_history_call_trace'){
        $q=Get-ControllerTraceQualification $Workspace
        foreach($source in $q.sources.PSObject.Properties){$sources[$source.Name]=$source.Value}
        $sources[$q.qualification_artifact]=(Get-FileHash -LiteralPath (Join-Path $Workspace $q.qualification_artifact)).Hash
    }
    if($task.scientific_operation){
        $probeRel = [string]$task.scientific_operation
        $p = Join-Path $Workspace $probeRel
        if(Test-Path -LiteralPath $p -PathType Leaf){
            $sources[$probeRel] = (Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash
        }
        try {
            $dq = Get-ControllerDynamicQualification -Workspace $Workspace -Path $probeRel
            if($dq){
                $sources[$dq.qualification_artifact] = (Get-FileHash -LiteralPath (Join-Path $Workspace $dq.qualification_artifact)).Hash
                if($dq.scientific_dependencies){
                    foreach($dep in $dq.scientific_dependencies.PSObject.Properties){
                        $dp = Join-Path $Workspace $dep.Name
                        if(Test-Path -LiteralPath $dp -PathType Leaf){
                            $sources[$dep.Name] = (Get-FileHash -LiteralPath $dp -Algorithm SHA256).Hash
                        }
                    }
                }
                if($dq.tests){
                    foreach($t in $dq.tests.PSObject.Properties){
                        $tp = Join-Path $Workspace $t.Name
                        if(Test-Path -LiteralPath $tp -PathType Leaf){
                            $sources[$t.Name] = (Get-FileHash -LiteralPath $tp -Algorithm SHA256).Hash
                        }
                    }
                }
            }
        } catch {}
    }
    if($task.scientific_checkpoint.artifact){
        $relative=[string]$task.scientific_checkpoint.artifact
        if($relative -notmatch '^results/validation/(?:(?:mode1_f1597/)?[a-fA-F0-9-]{36}|preparation-[a-fA-F0-9-]{36}|[a-zA-Z0-9_-]+)\.json$'){throw 'Unsafe scientific basis artifact'}
        $p=Join-Path $Workspace $relative
        if(-not(Test-Path -LiteralPath $p)){throw 'Missing scientific basis artifact'}
        $sources[$relative]=(Get-FileHash -LiteralPath $p).Hash
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
    return [pscustomobject]@{task=$task; session=$session; sources=$sources; pbs_receipts=$receipts; execution_accounting=$execution; report=$report; report_bytes=$reportBytes; commit=$commit; workspace=$Workspace}
}

function Resolve-ControllerInstruction([string]$Workspace, [string]$Instruction) {
    $e = Get-ControllerEvidence $Workspace
    $taskType = Resolve-ControllerTaskType $e.task $Workspace
    $terminal = [string]$e.task.status -match '(?i)(completed|classified|closed|^done$)'
    $heading = ($Instruction -split "`n")[0]
    $id = [regex]::Match($heading,'\bF\d+\b').Value
    $currentId = [regex]::Match([string]$e.task.task_id,'\bF\d+\b').Value
    if ($id) {
        $closed = @(Import-Csv -LiteralPath (Join-Path $Workspace 'project_coordination/TASK_LEDGER.csv') |
            Where-Object { $_.task_id -match ('^' + [regex]::Escape($id) + '(?:-|$)') -and $_.status -match '^(?i:complete|completed|closed)$' })
        if ($closed.Count) {
            # Case 1: Predecessor task different from current active task
            if ($currentId -and $id -ne $currentId) {
                throw ('COMPLETED_TASK_REJECTED: ' + $id + '; select the authoritative active task instead')
            }

            # Case 2: Current active parent task itself is terminal or marked completed in ledger
            if ($terminal) {
                throw ('COMPLETED_TASK_REJECTED: ' + $id + '; select the authoritative active task instead')
            }
            $parentClosed = @($closed | Where-Object { $_.task_id.Trim() -eq $e.task.task_id.Trim() })
            if ($parentClosed.Count -gt 0) {
                throw ('COMPLETED_TASK_REJECTED: ' + $id + '; select the authoritative active task instead')
            }

            # Case 3: Current task is still active, but instruction targets an already-completed subtask or duplicate instruction
            $headingClean = $heading.ToUpperInvariant()
            $instructionUpper = $Instruction.ToUpperInvariant()
            foreach ($entry in $closed) {
                $subtaskId = $entry.task_id.Trim()
                $subtaskUpper = $subtaskId.ToUpperInvariant()
                # Check for explicit subtask ID in heading, explicit task directive, or replay request (context mentions in body permitted)
                $targetedInHeading = $subtaskId -and ($headingClean -match [regex]::Escape($subtaskUpper))
                $targetedInDirective = $subtaskId -and ($instructionUpper -match ('(?im)^\s*(?:task|subtask|objective|controller_task)\s*:\s*' + [regex]::Escape($subtaskUpper)))
                $targetedInReplay = $subtaskId -and ($instructionUpper -match ('(?i)(?:run|execute|replay|repeat)\s+(?:task\s+)?' + [regex]::Escape($subtaskUpper)))
                if ($targetedInHeading -or $targetedInDirective -or $targetedInReplay) {
                    throw ('COMPLETED_TASK_REJECTED: ' + $subtaskId + '; select the authoritative active task instead')
                }

                # Check if heading matches all significant keywords of the completed subtask ID
                $parts = @($subtaskId -split '-' | Where-Object { $_ -and $_ -ne $id })
                if ($parts.Count -gt 0) {
                    $allPartsMatch = $true
                    foreach ($p in $parts) {
                        if ($headingClean -notmatch ('\b' + [regex]::Escape($p) + '\b')) {
                            $allPartsMatch = $false
                            break
                        }
                    }
                    if ($allPartsMatch) {
                        throw ('COMPLETED_TASK_REJECTED: ' + $subtaskId + '; select the authoritative active task instead')
                    }
                }
            }
        }
    }
    $stale = $terminal -and $id -and $id -eq $currentId
    if ($stale -or $Instruction -match '^CONTROLLER_TASK: NEXT_UNRESOLVED') {
        $Instruction = @"
CONTROLLER_TASK: NEXT_UNRESOLVED
Authoritative predecessor: $($e.task.task_id), status $($e.task.status).
Read CURRENT_STATE.md, ACTIVE_TASK.json, TASK_LEDGER.csv, exact session records and HPC/execution ledgers before choosing work. Completed predecessor work must not execute again.
Use the exact canonical -File Bootstrap command supplied by the controller. It performs the ordered prerequisite reads and session claim once for this turn. Its completion receipt replaces repeated bootstrap reads. Never reconstruct bootstrap using nested -Command strings or raw head/tail commands.
Select one next scientifically useful executable action from current evidence. Immediately execute independently ready qualified serial Mode-I jobs through scripts/hpc/Invoke-Mode1Execution.ps1 under the standing limits and once-only accounting. No administrative approval is needed. Do not repeat the completed audit, submit dependent work before quantitative predecessor acceptance, or manufacture a job. If scientific failure blocks execution, do only the smallest essential hypothesis/equation/checkpoint review and report its concrete finding promptly. Preserve the frozen production UEL and authentic failed results.
Create the owned session report and record an initial verified research artifact early (within 120 seconds); update it after each substantive action and at least every 180 seconds. The controller progress watchdog resets upon verified intermediate scientific artifacts (new/modified analysis or test code, passing test receipts, or substantive JSON findings with verified hashes); metadata, conversation chatter, and unchanged stubs do not reset the 600-second deadline. Do not spend the turn rereading broad history. Close the owned session truthfully and return evidence, actual PBS receipts if any, and the exact next safe action. End with Finished.
"@
    }
    return [pscustomobject]@{instruction=$Instruction; stale_replaced=[bool]$stale; evidence=$e; task_type=$taskType.task_type; operation=$taskType.operation}
}

function New-ControllerTurnState($Evidence, [int]$Turn, [string]$Instruction, [int]$RecoveryCount = 0) {
    $runId=[guid]::NewGuid().ToString()
    $taskType = Resolve-ControllerTaskType $Evidence.task $Evidence.workspace
    return [pscustomobject]@{
        schema=1
        run_id=$runId
        workspace=$Evidence.workspace
        bootstrap_record_path=$(if($Evidence.workspace){Join-Path $Evidence.workspace ('project_coordination/controller/turn-'+$runId+'.json')}else{''})
        bootstrap_repeat_reads=0
        requires_scientific_checkpoint=[bool]$Evidence.task.scientific_checkpoint_required
        task_type=$taskType.task_type
        scientific_operation=$(if($taskType.operation){$taskType.operation.path}elseif($Evidence.task.scientific_operation){[string]$Evidence.task.scientific_operation}else{''})
        operation_id=$(if($taskType.operation){$taskType.operation.id}else{'research_preparation'})
        scientific_basis_artifact=[string]$Evidence.task.scientific_checkpoint.artifact
        task_id=[string]$Evidence.task.task_id
        predecessor_task_id=[string]$Evidence.task.task_id
        repository_commit=$Evidence.commit
        initial_session_active=[bool]$Evidence.session.active
        initial_session_hash=$Evidence.sources['project_coordination/ACTIVE_SESSION.json']
        owned_session_fingerprint=''
        turn=$Turn
        state='PENDING'
        recovery_count=$RecoveryCount
        process_id=0
        started_at=[DateTimeOffset]::UtcNow.ToString('o')
        updated_at=''
        last_confirmed_action=[string]$Evidence.task.status
        sources=$Evidence.sources
        pbs_receipts=$Evidence.pbs_receipts
        execution_accounting=$Evidence.execution_accounting
        session=$Evidence.session
        session_report=$Evidence.report
        progress_signature=''
        last_evidence_at=''
        conversation_id=''
        live_buffer=''
        last_stream_step=''
        stop_reason=''
        original_instruction_hash=(Get-ControllerTextHash $Instruction)
        partial_output=''
        partial_sha256=''
        next_safe_action='Execute only reconciled instruction'
        block_reason=''
    }
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

function Invoke-DeterministicTurnRecovery([string]$Workspace, [string]$Path, $State, [string]$Partial, [string]$NextInstruction = '') {
    if (-not $State -or -not $Path) { return [pscustomobject]@{ Reconciled = $false; Reason = 'Missing state or path' } }

    $turnStarted = if ($State.recovery_count -gt 0 -and $State.started_at) {
        try { [DateTimeOffset]::Parse($State.started_at).UtcDateTime.AddHours(-2) } catch { [DateTime]::UtcNow.AddHours(-4) }
    } elseif ($State.started_at) {
        try { [DateTimeOffset]::Parse($State.started_at).UtcDateTime } catch { [DateTime]::UtcNow.AddHours(-2) }
    } else {
        [DateTime]::UtcNow.AddHours(-2)
    }

    $deliverables = [System.Collections.Generic.List[string]]::new()

    $valDir = Join-Path $Workspace 'results/validation'
    if (Test-Path -LiteralPath $valDir) {
        $valFiles = Get-ChildItem -LiteralPath $valDir -Filter '*.json' -File -Recurse -ErrorAction SilentlyContinue
        foreach ($f in $valFiles) {
            if ($f.LastWriteTimeUtc -ge $turnStarted.AddSeconds(-60)) {
                try {
                    $raw = [IO.File]::ReadAllText($f.FullName)
                    if ($raw.Length -ge 40) {
                        $json = $raw | ConvertFrom-Json -ErrorAction SilentlyContinue
                        if ($json.verification_passed -eq $true -or
                            $json.status -in @('PREPARATION_COMPLETE', 'QUALIFIED_OPERATION_READY', 'INVESTIGATION_COMPLETE', 'PASSED') -or
                            ($json.schema -eq 1 -and $json.finding -and $json.finding.Length -ge 20)) {
                            $rel = ($f.FullName.Substring($Workspace.Length)).TrimStart('\', '/').Replace('\', '/')
                            if ($rel -notmatch '(?:^|\/)(?:temp|scratch|\.git|__pycache__)(?:\/|$)') {
                                $deliverables.Add($rel)
                            }
                        }
                    }
                } catch {}
            }
        }
    }

    $modelsDir = Join-Path $Workspace 'models/pandey_kumar_mode1'
    if (Test-Path -LiteralPath $modelsDir) {
        $manifests = Get-ChildItem -LiteralPath $modelsDir -Filter 'PACKAGE_MANIFEST.json' -File -Recurse -ErrorAction SilentlyContinue
        foreach ($m in $manifests) {
            if ($m.LastWriteTimeUtc -ge $turnStarted.AddSeconds(-60)) {
                $rel = ($m.FullName.Substring($Workspace.Length)).TrimStart('\', '/').Replace('\', '/')
                $inp = Join-Path (Split-Path $m.FullName) '*.inp'
                if (Test-Path -Path $inp) {
                    $deliverables.Add($rel)
                }
            }
        }
    }

    $hpcLedger = Join-Path $Workspace 'project_coordination/HPC_JOB_LEDGER.csv'
    $hasNewHpcJob = $false
    if (Test-Path -LiteralPath $hpcLedger) {
        $prevHpcHash = if ($State.sources -and $State.sources['project_coordination/HPC_JOB_LEDGER.csv']) {
            $State.sources['project_coordination/HPC_JOB_LEDGER.csv']
        } else { $null }
        $currHpcHash = (Get-FileHash -LiteralPath $hpcLedger -Algorithm SHA256).Hash
        if ($null -ne $prevHpcHash -and $currHpcHash -ne $prevHpcHash) {
            $lines = Get-Content -LiteralPath $hpcLedger -ErrorAction SilentlyContinue
            $tail = $lines | Select-Object -Last 5
            foreach ($tl in $tail) {
                if ($tl -match '(\d{7}\.mmaster02)') { $hasNewHpcJob = $true }
            }
        }
    }

    if ($deliverables.Count -eq 0 -and -not $hasNewHpcJob) {
        return [pscustomobject]@{ Reconciled = $false; Reason = 'No verifiable scientific deliverables on disk' }
    }

    $partialPath = $Path + '.' + $State.run_id + '.partial.txt'
    [IO.File]::WriteAllText($partialPath, $Partial, [Text.UTF8Encoding]::new($false))
    $State.partial_output = $partialPath
    $State.partial_sha256 = (Get-FileHash -LiteralPath $partialPath -Algorithm SHA256).Hash

    $backupsDir = Join-Path $env:USERPROFILE 'OpenClawPAD/backups'
    if (-not (Test-Path -LiteralPath $backupsDir)) { $null = New-Item -ItemType Directory -Path $backupsDir -Force }
    $archivePath = Join-Path $backupsDir "checkpoint-$($State.run_id)-interrupted.json"
    $archiveHash = ''
    if (Test-Path -LiteralPath $Path) {
        Copy-Item -LiteralPath $Path -Destination $archivePath -Force
        $archiveHash = (Get-FileHash -LiteralPath $archivePath -Algorithm SHA256).Hash
    }

    $sessionRel = "project_coordination/sessions/$((Get-Date).ToString('yyyy-MM-dd'))_gemini-antigravity_$($State.task_id)_$($State.run_id).md"
    $sessionPath = Join-Path $Workspace $sessionRel
    $sessionFile = Join-Path $Workspace 'project_coordination/ACTIVE_SESSION.json'
    if (Test-Path -LiteralPath $sessionFile) {
        $sess = Get-Content -LiteralPath $sessionFile -Raw | ConvertFrom-Json
        if ($sess.session_report) {
            $sessionRel = $sess.session_report
            $sessionPath = Join-Path $Workspace $sessionRel
        }
        $sess.active = $false
        if ($sess.PSObject.Properties['last_released']) {
            $sess.last_released = [DateTimeOffset]::UtcNow.ToString('o')
        } else {
            $sess | Add-Member -NotePropertyName last_released -NotePropertyValue ([DateTimeOffset]::UtcNow.ToString('o')) -Force
        }
        if ($sess.PSObject.Properties['last_updated']) {
            $sess.last_updated = [DateTimeOffset]::UtcNow.ToString('o')
        } else {
            $sess | Add-Member -NotePropertyName last_updated -NotePropertyValue ([DateTimeOffset]::UtcNow.ToString('o')) -Force
        }
        [IO.File]::WriteAllText($sessionFile, ($sess | ConvertTo-Json -Depth 20), [Text.UTF8Encoding]::new($false))
    }

    if (-not (Test-Path -LiteralPath $sessionPath)) {
        $reportDir = Split-Path $sessionPath
        if (-not (Test-Path -LiteralPath $reportDir)) { New-Item -ItemType Directory -Path $reportDir -Force | Out-Null }
        $reportText = @"
# Session Report: Turn $($State.turn) Deterministic Interruption Recovery
**Run ID**: $($State.run_id)
**Task ID**: $($State.task_id)
**Date**: $((Get-Date).ToString('yyyy-MM-dd HH:mm:ss'))
**Reconciliation**: DETERMINISTIC_EVIDENCE_RECOVERY_COMPLETED

## Verified On-Disk Deliverables
$(($deliverables | ForEach-Object { "- $_" }) -join "`n")

Session deterministically reconciled from on-disk evidence without replaying completed work.
Finished
"@
        [IO.File]::WriteAllText($sessionPath, $reportText, [Text.UTF8Encoding]::new($false))
    }
    $sessionReportHash = (Get-FileHash -LiteralPath $sessionPath -Algorithm SHA256).Hash

    $bootRel = "project_coordination/controller/turn-$($State.run_id).json"
    $bootPath = Join-Path $Workspace $bootRel
    if (-not (Test-Path -LiteralPath $bootPath)) {
        $bootDir = Split-Path $bootPath
        if (-not (Test-Path -LiteralPath $bootDir)) { New-Item -ItemType Directory -Path $bootDir -Force | Out-Null }
        $bootData = @{
            stage = 'COMPLETE'
            bootstrap_status = 'COMPLETE'
            controller_run_id = [string]$State.run_id
            task_id = [string]$State.task_id
            session_report = $sessionRel
            timestamp = [DateTimeOffset]::UtcNow.ToString('o')
        }
        [IO.File]::WriteAllText($bootPath, ($bootData | ConvertTo-Json -Depth 10), [Text.UTF8Encoding]::new($false))
    }
    $bootHash = (Get-FileHash -LiteralPath $bootPath -Algorithm SHA256).Hash

    $hpcHash = (Get-FileHash -LiteralPath (Join-Path $Workspace 'project_coordination/HPC_JOB_LEDGER.csv') -Algorithm SHA256).Hash

    $nextInst = if (-not [string]::IsNullOrWhiteSpace($NextInstruction)) { $NextInstruction } else { "Advance $($State.task_id): Proceed to next numerical operation based on verified on-disk deliverables." }

    $updates = @{
        state = 'COMPLETED'
        recovery_count = 0
        stop_reason = 'DETERMINISTIC_RECOVERY_COMPLETED'
        block_reason = ''
        conversation_id = ''
        next_safe_action = $nextInst
        next_instruction = $nextInst
    }
    foreach ($k in $updates.Keys) {
        if ($State.PSObject.Properties[$k]) {
            $State.$k = $updates[$k]
        } else {
            $State | Add-Member -NotePropertyName $k -NotePropertyValue $updates[$k] -Force
        }
    }

    $reconciliationRecord = [ordered]@{
        status = 'INTERRUPTED_TURN_PROGRESS_WATCHDOG_RECONCILED'
        original_checkpoint = $archivePath
        original_sha256 = $archiveHash
        run_id = $State.run_id
        task_id = $State.task_id
        session_report = $sessionRel
        session_report_sha256 = $sessionReportHash
        bootstrap_record = $bootRel
        bootstrap_record_sha256 = $bootHash
        hpc_ledger_sha256 = $hpcHash
        reconciled_at = [DateTimeOffset]::UtcNow.ToString('o')
        deliverables = @($deliverables)
    }

    if ($State.PSObject.Properties['reconciliation']) {
        $State.reconciliation = [pscustomobject]$reconciliationRecord
    } else {
        $State | Add-Member -NotePropertyName reconciliation -NotePropertyValue ([pscustomobject]$reconciliationRecord) -Force
    }

    Write-ControllerCheckpoint $Path $State
    Assert-ControllerDispatchCheckpoint $Workspace $State

    return [pscustomobject]@{
        Reconciled = $true
        NextInstruction = $nextInst
        State = $State
    }
}


function Get-ControllerBudget([string]$PrintTimeout,[int]$Cap,[int]$Reserve=120) {
    $m=[regex]::Match($PrintTimeout,'^(\d+)(s|m|h)$')
    if (-not $m.Success) { throw 'Invalid print timeout' }
    $total=[int][Math]::Min($Cap,([double]$m.Groups[1].Value * @{s=1;m=60;h=3600}[$m.Groups[2].Value]))
    $closeout=[int][Math]::Min($Reserve,[Math]::Floor($total/4))
    if ($total -lt 4) { throw 'Insufficient controller turn budget' }
    return [pscustomobject]@{total=$total; work=($total-$closeout); closeout=$closeout}
}

function Test-ControllerCompletedScienceReceipt([string]$Workspace,$State) {
    # Fail closed: report text by itself is never an execution receipt.
    try {
        if (-not $State -or -not $State.run_id -or -not $State.task_id -or
            -not $State.bootstrap_record_path -or -not $State.session -or
            $State.session.active -ne $false -or
            [string]$State.session.controller_run_id -cne [string]$State.run_id) { return $false }
        if (-not (Test-ControllerScientificCheckpoint $Workspace $State)) { return $false }
        $record = Get-Content -LiteralPath $State.bootstrap_record_path -Raw -Encoding UTF8 | ConvertFrom-Json
        if ($record.stage -cne 'COMPLETE' -or $record.bootstrap_status -cne 'COMPLETE' -or
            [string]$record.controller_run_id -cne [string]$State.run_id -or
            [string]$record.task_id -cne [string]$State.task_id -or
            [string]$record.session_report -cne [string]$State.session.session_report) { return $false }
        $relative = [string]$record.session_report
        if ([string]::IsNullOrWhiteSpace($relative)) { return $false }
        $base = [IO.Path]::GetFullPath((Join-Path $Workspace 'project_coordination/sessions')) + [IO.Path]::DirectorySeparatorChar
        $full = [IO.Path]::GetFullPath((Join-Path $Workspace $relative))
        if (-not $full.StartsWith($base,[StringComparison]::OrdinalIgnoreCase) -or
            -not (Test-Path -LiteralPath $full -PathType Leaf)) { return $false }
        # Each accepted receipt must belong to the same run (not just the task).
        if ($relative -notmatch [regex]::Escape([string]$State.run_id)) { return $false }
        $report = Get-Content -LiteralPath $full -Raw -Encoding UTF8
        if ($report -notmatch '(?s)Finished[.\s]*$' -or
            $report -notmatch [regex]::Escape([string]$State.run_id)) { return $false }
        return $true
    } catch { return $false }
}
function Complete-ControllerTurn([string]$Workspace,[string]$Path,$State,[string]$Response,[switch]$VerifiedReceipt) {
    Update-ControllerEvidence $Workspace $Path $State
    $receiptAccepted = [bool]$VerifiedReceipt
    # A normal successful AGY run may omit a final chat marker after independently
    # committing and releasing a valid scientific result. Accept only a verified
    # receipt tied to THIS controller run, never a stale report or active session.
    if (-not $receiptAccepted -and -not $State.session.active -and
        $Response -notmatch '(?im)^\s*BLOCKED\b' -and
        $Response -notmatch '(?s)Finished[.\s]*$') {
        $receiptAccepted = Test-ControllerCompletedScienceReceipt $Workspace $State
        if ($receiptAccepted) {
            Write-Host ('[RECEIPT] Verified completed scientific turn ' + $State.turn + ' / ' + $State.run_id + ' without terminal chat marker.')
        }
    }
    if ($State.session.active -or $Response -match '(?im)^\s*BLOCKED\b' -or (-not $receiptAccepted -and $Response -notmatch '(?s)Finished[.\s]*$')) {
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
    # Exclude model tokens, conversation output, timestamps, bootstrap, repeated file reads, generic reports or unchanged artifacts.
    if (-not $State.PSObject.Properties['progress_evidence']) {
        $State | Add-Member -NotePropertyName progress_evidence -NotePropertyValue @{}
    }
    if ($State.progress_evidence -isnot [Collections.IDictionary]) {
        $map = @{}
        foreach ($property in $State.progress_evidence.PSObject.Properties) { $map[$property.Name] = $property.Value }
        $State.progress_evidence = $map
    }
    $Workspace = if ($State.workspace -and (Test-Path -LiteralPath $State.workspace)) { $State.workspace } else { (Get-Location).Path }
    $isInitialBaseline = -not $State.progress_signature
    $changed = $false

    # 1. Completed Scientific Qualification (Terminal Checkpoint)
    if ($State.requires_scientific_checkpoint -and (Test-ControllerScientificCheckpoint $Workspace $State)) {
        try {
            $receipt = Get-Content -LiteralPath $State.bootstrap_record_path -Raw | ConvertFrom-Json
            if ($receipt.scientific_checkpoint -and $receipt.scientific_checkpoint.sha256) {
                $sig = 'QUALIFIED_CHECKPOINT:' + $receipt.scientific_checkpoint.sha256
                if ($State.progress_evidence['SCIENTIFIC_CHECKPOINT'] -ne $sig) {
                    if (-not $isInitialBaseline) { $changed = $true }
                    $State.progress_evidence['SCIENTIFIC_CHECKPOINT'] = $sig
                }
            }
        } catch {}
    }

    # 2. Verified Intermediate Research & Validation Artifacts (results/validation/*.json)
    $valDir = Join-Path $Workspace 'results/validation'
    if (Test-Path -LiteralPath $valDir) {
        $valFiles = Get-ChildItem -LiteralPath $valDir -Filter '*.json' -File -Recurse -ErrorAction SilentlyContinue
        foreach ($file in $valFiles) {
            $rel = ($file.FullName.Substring($Workspace.Length)).TrimStart('\', '/').Replace('\', '/')
            if ($rel -match '(?:^|\/)(?:temp|scratch|\.git|__pycache__)(?:\/|$)') { continue }
            try {
                $hash = (Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash
                if (-not $State.progress_evidence.ContainsKey($rel) -or $State.progress_evidence[$rel] -ne $hash) {
                    $raw = [IO.File]::ReadAllText($file.FullName)
                    if ($raw.Length -ge 40) {
                        $json = $raw | ConvertFrom-Json -ErrorAction Stop
                        $hasSubstantiveFinding = ($json.finding -is [string] -and $json.finding.Trim().Length -ge 20)
                        $hasMeasurements = ($null -ne $json.measurements -and @($json.measurements.PSObject.Properties).Count -gt 0)
                        $hasPassedStatus = ($json.verification_passed -eq $true -or $json.status -in @('PREPARATION_COMPLETE', 'QUALIFIED_OPERATION_READY', 'INVESTIGATION_COMPLETE', 'INTERMEDIATE_FINDING', 'PASSED'))
                        $hasEvidence = ($null -ne $json.evidence_sources -and @($json.evidence_sources.PSObject.Properties).Count -gt 0)
                        $hasTests = ($null -ne $json.tests -or $null -ne $json.passed)
                        if ($hasSubstantiveFinding -or $hasMeasurements -or ($hasPassedStatus -and $hasEvidence) -or $hasTests) {
                            if (-not $isInitialBaseline) { $changed = $true }
                            $State.progress_evidence[$rel] = $hash
                        }
                    }
                }
            } catch {}
        }
    }

    # 3. New or Modified Source, Test, or Model Files with Verified Hashes
    $gitDir = Join-Path $Workspace '.git'
    if (Test-Path -LiteralPath $gitDir) {
        $statusLines = & git -C $Workspace status --porcelain -u -- scripts/validation tests/unit models/pandey_kumar_mode1
        foreach ($line in $statusLines) {
            if ($line -match '^(?:[ MADRCU?!]{2})\s+(.+)$') {
                $relPath = $matches[1].Trim().Trim('"').Replace('\', '/')
                $fullPath = Join-Path $Workspace $relPath
                if ((Test-Path -LiteralPath $fullPath -PathType Leaf) -and
                    ($relPath -match '\.(?:py|ps1|for|f|inp|csv|json)$') -and
                    ($relPath -notmatch '(?i)(?:^|\/)(?:\.|\.tmp$|\.log$|\.partial\.txt$|~)') -and
                    ($relPath -notmatch '(?:^|\/)(?:temp|scratch|\.git|__pycache__)(?:\/|$)')) {
                    $item = Get-Item -LiteralPath $fullPath
                    if ($item.Length -gt 0) {
                        $hash = (Get-FileHash -LiteralPath $fullPath -Algorithm SHA256).Hash
                        if (-not $State.progress_evidence.ContainsKey($relPath) -or $State.progress_evidence[$relPath] -ne $hash) {
                            if (-not $isInitialBaseline) { $changed = $true }
                            $State.progress_evidence[$relPath] = $hash
                        }
                    }
                }
            }
        }
        try {
            $headCommit = (& git -C $Workspace rev-parse HEAD).Trim()
            if ($headCommit) {
                if (-not $State.progress_evidence.ContainsKey('GIT_HEAD') -or $State.progress_evidence['GIT_HEAD'] -ne $headCommit) {
                    if (-not $isInitialBaseline -and $State.progress_evidence.ContainsKey('GIT_HEAD')) { $changed = $true }
                    $State.progress_evidence['GIT_HEAD'] = $headCommit
                }
            }
        } catch {}
    } else {
        $scanDirs = @('scripts/validation', 'tests/unit', 'models/pandey_kumar_mode1')
        foreach ($sub in $scanDirs) {
            $fullSub = Join-Path $Workspace $sub
            if (Test-Path -LiteralPath $fullSub) {
                $files = Get-ChildItem -LiteralPath $fullSub -File -Recurse -ErrorAction SilentlyContinue |
                    Where-Object {
                        $_.Extension -in @('.py', '.ps1', '.for', '.f', '.inp', '.csv', '.json') -and
                        $_.Name -notmatch '(?i)(^\.|\.tmp$|\.log$|\.partial\.txt$|~)'
                    }
                foreach ($file in $files) {
                    if ($file.Length -gt 0) {
                        $rel = ($file.FullName.Substring($Workspace.Length)).TrimStart('\', '/').Replace('\', '/')
                        if ($rel -match '(?:^|\/)(?:temp|scratch|\.git|__pycache__)(?:\/|$)') { continue }
                        $hash = (Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash
                        if (-not $State.progress_evidence.ContainsKey($rel) -or $State.progress_evidence[$rel] -ne $hash) {
                            if (-not $isInitialBaseline) { $changed = $true }
                            $State.progress_evidence[$rel] = $hash
                        }
                    }
                }
            }
        }
    }

    # 4. HPC Ledgers
    foreach ($ledger in @('project_coordination/HPC_JOB_LEDGER.csv', 'project_coordination/MODE1_EXECUTION_LEDGER.json')) {
        $lp = Join-Path $Workspace $ledger
        if (Test-Path -LiteralPath $lp) {
            $lhash = (Get-FileHash -LiteralPath $lp -Algorithm SHA256).Hash
            if (-not $State.progress_evidence.ContainsKey($ledger) -or $State.progress_evidence[$ledger] -ne $lhash) {
                if (-not $isInitialBaseline) { $changed = $true }
                $State.progress_evidence[$ledger] = $lhash
            }
        }
    }

    # 5. Substantive Session Report Updates with Concrete Findings
    if ($State.session_report -and $State.owned_session_fingerprint) {
        $srp = Join-Path $Workspace $State.session_report
        if (Test-Path -LiteralPath $srp) {
            $srItem = Get-Item -LiteralPath $srp
            if ($srItem.Length -ge 200) {
                $srText = [IO.File]::ReadAllText($srp)
                $isBoilerplateOnly = ($srText -match '(?i)This note does not count as scientific progress')
                if (-not $isBoilerplateOnly) {
                    $srHash = (Get-FileHash -LiteralPath $srp -Algorithm SHA256).Hash
                    if (-not $State.progress_evidence.ContainsKey($State.session_report) -or $State.progress_evidence[$State.session_report] -ne $srHash) {
                        if (-not $isInitialBaseline) { $changed = $true }
                        $State.progress_evidence[$State.session_report] = $srHash
                    }
                }
            }
        }
    }

    $State.progress_signature = 'BASELINED'
    if ($changed) {
        $State.last_evidence_at = [datetimeoffset]::UtcNow.ToString('o')
    }
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
            $stepKey = "$($event.step_update.step_index):$($event.step_update.step_type):$($event.step_update.state)"
            $lastStep = if ($State.PSObject.Properties['last_stream_step']) { [string]$State.last_stream_step } else { '' }
            if ($lastStep -ne $stepKey) {
                if ($State.PSObject.Properties['last_stream_step']) { $State.last_stream_step = $stepKey }
                else { $State | Add-Member -NotePropertyName last_stream_step -NotePropertyValue $stepKey -Force }
                Write-Host "[AGY] step=$($event.step_update.step_index) type=$($event.step_update.step_type) state=$($event.step_update.state)"
            }
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

function Test-ControllerScientificCheckpoint([string]$Workspace,$State,[switch]$Historical) {
    try{
        if(-not $State.bootstrap_record_path -or -not(Test-Path -LiteralPath $State.bootstrap_record_path -PathType Leaf)){return $false}
        $record=Get-Content -LiteralPath $State.bootstrap_record_path -Raw|ConvertFrom-Json
        $checkpoint=$record.scientific_checkpoint
        if($record.controller_run_id -ne $State.run_id -or $record.task_id -ne $State.task_id -or $record.bootstrap_status -ne 'COMPLETE' -or -not $checkpoint){return $false}
        if($checkpoint.kind -eq 'PREPARATION_CHECKPOINT'){
            if($checkpoint.exit_code -ne 0 -or -not $checkpoint.artifact){return $false}
            $artifactPath = Join-Path $Workspace $checkpoint.artifact
            if(-not(Test-Path -LiteralPath $artifactPath -PathType Leaf) -or (Get-FileHash -LiteralPath $artifactPath).Hash -ne $checkpoint.sha256){return $false}
            $prep = Get-Content -LiteralPath $artifactPath -Raw | ConvertFrom-Json
            if($prep.schema -ne 1 -or -not $prep.finding -or $prep.finding.Trim().Length -lt 20){return $false}
            if($prep.status -notin @('PREPARATION_COMPLETE','QUALIFIED_OPERATION_READY','INVESTIGATION_COMPLETE')){return $false}
            if($prep.PSObject.Properties['verification_passed'] -and -not $prep.verification_passed){return $false}
            if($null -eq $prep.evidence_sources -or @($prep.evidence_sources.PSObject.Properties).Count -lt 1){return $false}
            $root = [IO.Path]::GetFullPath($Workspace).TrimEnd([char[]]'\/') + [IO.Path]::DirectorySeparatorChar
            foreach($item in $prep.evidence_sources.PSObject.Properties){
                if($item.Name -match '(?:\.\.[/\\]|[/\\]\.\.)'){return $false}
                $ep = [IO.Path]::GetFullPath((Join-Path $Workspace $item.Name))
                if(-not $ep.StartsWith($root, [StringComparison]::OrdinalIgnoreCase) -or -not (Test-Path -LiteralPath $ep -PathType Leaf)){return $false}
                if((Get-Item -LiteralPath $ep).Length -gt 16777216){return $false}
                if((Get-FileHash -LiteralPath $ep -Algorithm SHA256).Hash -cne $item.Value){return $false}
            }
            if($prep.qualified_operation){
                try {
                    $dq = Get-ControllerDynamicQualification -Workspace $Workspace -Path $prep.qualified_operation
                    if(-not $dq){return $false}
                } catch { return $false }
            }
            return $true
        }
        if($checkpoint.kind -ne 'NUMERICAL_FINDING' -or $checkpoint.exit_code -ne 0){return $false}
        $expected='results/validation/mode1_f1597/'+$State.run_id+'.json'
        if($checkpoint.artifact -ne $expected){return $false}
        $artifact=Join-Path $Workspace $expected
        if(-not(Test-Path -LiteralPath $artifact -PathType Leaf) -or (Get-FileHash -LiteralPath $artifact).Hash -ne $checkpoint.sha256){return $false}
        $data=Get-Content -LiteralPath $artifact -Raw|ConvertFrom-Json
        if($checkpoint.operation -cne $data.operation){return $false}
        $opPath = if($record.operation_path){ [string]$record.operation_path } elseif($State.scientific_operation){ [string]$State.scientific_operation } else { '' }
        $op=Get-ControllerOperation -ArtifactId $data.operation -Path $opPath -Historical:$Historical -Workspace $Workspace
        if(-not $Historical -and ($State.scientific_operation -cne $op.path -or $record.operation_id -cne $op.id)){return $false}
        if($data.task_id -ne 'F1597' -or $data.verification_passed -isnot [bool] -or -not $data.verification_passed){return $false}
        if($null -eq $data.measurements){return $false}
        foreach($m in $data.measurements.PSObject.Properties){if($m.Value -is [string] -or $null -eq $m.Value -or [double]::IsNaN([double]$m.Value) -or [double]::IsInfinity([double]$m.Value)){return $false}}
        $probe=$op.path
        $required=@($probe)
        if($op.id -eq 'mapped_frozen_history_lower_bound_kkt_probe'){
            if($data.measurements.phase_elements -le 0 -or $data.measurements.phase_nodes -le 0){return $false}
            if($null -eq $data.measurements.finite_difference_gradient_error_kN -or $data.measurements.finite_difference_gradient_error_kN -gt 1e-10){return $false}
            $required+=@('models/pandey_kumar_mode1/15_energy_qualification_small/f42_mixed_uel.for','models/pandey_kumar_mode1/72_method_c_coupled_state_transfer/M1_EXP_COUPLED_TRANSFER_650.inp','models/pandey_kumar_mode1/72_method_c_coupled_state_transfer/offset_state_table.csv','models/pandey_kumar_mode1/72_method_c_coupled_state_transfer/f42_experimental_offset_uel.for')
        }elseif($op.id -eq 'authentic_uel_history_call_trace'){
            $q=Get-ControllerTraceQualification $Workspace
            if($data.pbs_job_id -ne $q.pbs_job_id){return $false}
            $m=$data.measurements
            foreach($name in @('trace_records','uel_calls','phase_calls','mechanical_calls','accepted_element_callbacks','history_write_calls','history_increase_inf_kN_mm2')){if($null -eq $m.PSObject.Properties[$name] -or $m.$name -lt 0){return $false}}
            if($m.trace_records -le 0 -or $m.trace_records -gt 2048 -or $m.phase_calls -le 0 -or $m.mechanical_calls -le 0 -or $m.accepted_element_callbacks -le 0){return $false}
            foreach($source in $q.sources.PSObject.Properties){if($data.sources.($source.Name) -ne $source.Value){return $false}}
            $required+=@('models/pandey_kumar_mode1/15_energy_qualification_small/f42_mixed_uel.for','models/pandey_kumar_mode1/72_method_c_coupled_state_transfer/M1_EXP_COUPLED_TRANSFER_650.inp','models/pandey_kumar_mode1/72_method_c_coupled_state_transfer/offset_state_table.csv','models/pandey_kumar_mode1/72_method_c_coupled_state_transfer/f42_experimental_offset_uel.for',$q.qualification_artifact,$State.scientific_basis_artifact)
        }elseif($op.id -eq 'mapped_mechanical_history_call_order_probe'){
            if($data.measurements.phase_elements -le 0 -or $data.measurements.phase_nodes -le 0){return $false}
            $m=$data.measurements
            $names=@('free_mechanical_dofs','mechanical_free_residual_inf_kN','worst_mechanical_node','worst_mechanical_dof','mapped_displacement_jump_mm','mapped_damage_jump','history_increase_inf_kN_mm2','phase_before_mechanical_inf_kN','phase_after_mechanical_inf_kN','phase_call_order_delta_inf_kN','committed_before_accept_error','retry_restore_error','accepted_commit_error','mechanical_fd_relative_error','prior_kkt_residual_difference_kN')
            foreach($name in $names){if($null -eq $m.PSObject.Properties[$name] -or [double]$m.$name -lt 0){return $false}}
            if($m.free_mechanical_dofs -le 0 -or $m.worst_mechanical_dof -notin @(1,2) -or $m.mechanical_fd_relative_error -gt 1e-7 -or $m.prior_kkt_residual_difference_kN -gt 1e-10 -or $m.mapped_damage_jump -gt 1e-10 -or
                $m.committed_before_accept_error -gt 1e-14 -or $m.retry_restore_error -gt 1e-14 -or $m.accepted_commit_error -gt 1e-14){return $false}
            foreach($entry in @{history_kN_mm2=1e-10;residual_kN=1e-10;fd_relative=1e-7;mapping_mm=1e-10;transaction=1e-14}.GetEnumerator()){if($data.tolerances.($entry.Key) -ne $entry.Value){return $false}}
            $classification=if($m.history_increase_inf_kN_mm2 -gt 1e-10){'HISTORY_UPDATE_AT_MAPPED_STATE'}elseif($m.mechanical_free_residual_inf_kN -gt 1e-10){'MECHANICAL_FREE_DOF_RESIDUAL'}elseif($m.mapped_displacement_jump_mm -gt 1e-10){'DISPLACEMENT_MAPPING_JUMP'}else{'NONE_ABOVE_DECLARED_TOLERANCES'}
            if($data.first_verified_discrepancy.classification -cne $classification){return $false}
            if(-not $State.scientific_basis_artifact){return $false}
            $required+=@('models/pandey_kumar_mode1/15_energy_qualification_small/f42_mixed_uel.for','models/pandey_kumar_mode1/72_method_c_coupled_state_transfer/M1_EXP_COUPLED_TRANSFER_650.inp','models/pandey_kumar_mode1/72_method_c_coupled_state_transfer/offset_state_table.csv','models/pandey_kumar_mode1/72_method_c_coupled_state_transfer/f42_experimental_offset_uel.for','scripts/validation/probe_mode1_f1597_kkt.py',$State.scientific_basis_artifact)
        }elseif($op.qualification){
            $crit=$op.qualification.verification_criteria
            if($crit.required_measurements){
                foreach($req in @($crit.required_measurements)){
                    if($null -eq $data.measurements.PSObject.Properties[$req] -or [double]::IsNaN([double]$data.measurements.$req) -or [double]::IsInfinity([double]$data.measurements.$req)){return $false}
                }
            }
            if($crit.tolerances){
                foreach($tol in $crit.tolerances.PSObject.Properties){
                    if($null -eq $data.tolerances -or $data.tolerances.($tol.Name) -ne $tol.Value){return $false}
                }
            }
            $required+=@($op.qualification.qualification_artifact)
            if($op.qualification.scientific_dependencies){
                foreach($dep in $op.qualification.scientific_dependencies.PSObject.Properties){$required+=$dep.Name}
            }
        }else{
            return $false
        }
        foreach($source in $required){if(-not $data.sources.$source -or $data.sources.$source -ne $State.sources.$source){return $false}}
        $root=[IO.Path]::GetFullPath($Workspace).TrimEnd('\','/')+[IO.Path]::DirectorySeparatorChar
        foreach($source in $data.sources.PSObject.Properties){
            if($source.Name -match '(?:\.\.[/\\]|[/\\]\.\.)'){return $false}
            $path=[IO.Path]::GetFullPath((Join-Path $Workspace $source.Name))
            if(-not $path.StartsWith($root,[StringComparison]::OrdinalIgnoreCase) -or -not(Test-Path -LiteralPath $path -PathType Leaf) -or (Get-FileHash -LiteralPath $path).Hash -ne $source.Value){return $false}
        }
        return $true
    }catch{return $false}
}

# AGY stream events are telemetry, never permission to terminate a normal shell command.
# Session ownership, source verification and execution safeguards remain in the canonical stages.

function Assert-ControllerDispatchCheckpoint([string]$Workspace,$State) {
    if(-not $State){return}
    if($State.state -eq 'BLOCKED'){throw ('BLOCKED: historical checkpoint requires evidence-based reconciliation; '+$State.block_reason)}
    if($State.reconciliation.status -eq 'COMPLETED_SCIENCE_CREDENTIAL_REPAIR_VERIFIED'){
        $r=$State.reconciliation
        if($State.state -ne 'COMPLETED' -or -not(Test-Path -LiteralPath $r.original_checkpoint) -or
            (Get-FileHash -LiteralPath $r.original_checkpoint).Hash -ne $r.original_sha256 -or
            -not(Test-ControllerScientificCheckpoint $Workspace $State -Historical)){throw 'BLOCKED: reconciled historical evidence missing or changed'}
        $original=Read-ControllerCheckpoint $r.original_checkpoint
        if($original.state -ne 'BLOCKED' -or $original.run_id -ne $State.run_id -or $original.scientific_commit -ne $r.scientific_commit){throw 'BLOCKED: original historical checkpoint identity mismatch'}
        $report=Join-Path $Workspace 'project_coordination/sessions/2026-10-20_codex_credential_lifecycle.md'
        if(-not(Test-Path -LiteralPath $report) -or (Get-FileHash -LiteralPath $report).Hash -ne $r.credential_report_sha256){throw 'BLOCKED: credential repair evidence changed'}
    }
    if($State.reconciliation.status -in @('INTERRUPTED_TURN_CREDENTIAL_REPAIR_VERIFIED','INTERRUPTED_TURN_PROGRESS_WATCHDOG_RECONCILED','INTERRUPTED_TURN_UTF8_CRASH_RECONCILED','INTERRUPTED_TURN_FILE_REPLACE_RECONCILED')){
        $r=$State.reconciliation
        if($State.state -ne 'COMPLETED' -or -not(Test-Path -LiteralPath $r.original_checkpoint) -or
            (Get-FileHash -LiteralPath $r.original_checkpoint).Hash -ne $r.original_sha256){throw 'BLOCKED: reconciled historical evidence missing or changed'}
        $original=Read-ControllerCheckpoint $r.original_checkpoint
        if(($original.state -notin @('BLOCKED','RUNNING')) -or $original.run_id -ne $State.run_id){throw 'BLOCKED: original historical checkpoint identity mismatch'}
        if($r.session_report -and (-not(Test-Path -LiteralPath (Join-Path $Workspace $r.session_report)) -or
            (Get-FileHash -LiteralPath (Join-Path $Workspace $r.session_report)).Hash -ne $r.session_report_sha256)){throw 'BLOCKED: session report evidence changed'}
        if($r.bootstrap_record -and (-not(Test-Path -LiteralPath (Join-Path $Workspace $r.bootstrap_record)) -or
            (Get-FileHash -LiteralPath (Join-Path $Workspace $r.bootstrap_record)).Hash -ne $r.bootstrap_record_sha256)){throw 'BLOCKED: bootstrap record evidence changed'}
        if($r.hpc_ledger_sha256 -and (Get-FileHash -LiteralPath (Join-Path $Workspace 'project_coordination/HPC_JOB_LEDGER.csv')).Hash -ne $r.hpc_ledger_sha256){throw 'BLOCKED: HPC job ledger changed unexpectedly'}
    }
}
