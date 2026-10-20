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
    $report = ''
    if ($session.session_report) {
        $root = [IO.Path]::GetFullPath((Join-Path $Workspace 'project_coordination/sessions')) + [IO.Path]::DirectorySeparatorChar
        $p = [IO.Path]::GetFullPath((Join-Path $Workspace $session.session_report))
        if (-not $p.StartsWith($root,[StringComparison]::OrdinalIgnoreCase)) { throw 'BLOCKED: unsafe session report path' }
        if (Test-Path -LiteralPath $p -PathType Leaf) {
            $sources[[string]$session.session_report] = (Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash
            $report = [string]$session.session_report
        }
    }
    # Exact IDs are observations from durable ledgers, never a claim of live scheduler state.
    $receipts = @([regex]::Matches((Get-Content -LiteralPath (Join-Path $Workspace 'project_coordination/HPC_JOB_LEDGER.csv') -Raw), '\b\d+\.mmaster02\b') | ForEach-Object Value | Sort-Object -Unique)
    $execution = Get-Content -LiteralPath (Join-Path $Workspace 'project_coordination/MODE1_EXECUTION_LEDGER.json') -Raw -Encoding UTF8 | ConvertFrom-Json
    return [pscustomobject]@{task=$task; session=$session; sources=$sources; pbs_receipts=$receipts; execution_accounting=$execution; report=$report}
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
One bounded next unresolved task only: review the documented failed state-transfer result and its proposed corrective numerical hypothesis against existing equations and authentic checkpoints. Record whether the hypothesis is scientifically supported and the smallest missing evidence. Do not implement changed scientific assumptions or submit dependent jobs during this review. Preserve the frozen production UEL, failed evidence and all once-only reservations. If source information is insufficient or multiple scientific choices remain, report the concrete dependency and stop.
Checkpoint findings after each substantive action, close the owned session truthfully, and return evidence paths plus the exact next safe action. End with Finished.
"@
    }
    return [pscustomobject]@{instruction=$Instruction; stale_replaced=[bool]$stale; evidence=$e}
}

function New-ControllerTurnState($Evidence, [int]$Turn, [string]$Instruction, [int]$RecoveryCount = 0) {
    return [pscustomobject]@{schema=1; run_id=[guid]::NewGuid().ToString(); task_id=[string]$Evidence.task.task_id; turn=$Turn; state='PENDING'; recovery_count=$RecoveryCount; process_id=0; started_at=[DateTimeOffset]::UtcNow.ToString('o'); updated_at=''; last_confirmed_action=[string]$Evidence.task.status; sources=$Evidence.sources; pbs_receipts=$Evidence.pbs_receipts; execution_accounting=$Evidence.execution_accounting; session=$Evidence.session; session_report=$Evidence.report; original_instruction_hash=(Get-ControllerTextHash $Instruction); partial_output=''; partial_sha256=''; next_safe_action='Execute only reconciled instruction'; block_reason=''}
}

function Update-ControllerEvidence([string]$Workspace, [string]$Path, $State) {
    $e = Get-ControllerEvidence $Workspace
    $State.sources=$e.sources; $State.pbs_receipts=$e.pbs_receipts; $State.execution_accounting=$e.execution_accounting
    if (-not $e.session.active -or $e.session.task_id -eq $e.task.task_id) { $State.task_id=[string]$e.task.task_id }
    $State.last_confirmed_action=[string]$e.task.status; $State.session=$e.session; $State.session_report=$e.report
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
        # Only release a newly claimed Gemini session belonging to this owned invocation.
        if ($e.session.active) {
            $claim = [datetimeoffset]::MinValue
            if ($e.session.agent -ne 'gemini-antigravity' -or $e.session.task_id -ne $State.task_id -or
                -not [datetimeoffset]::TryParse([string]$e.session.claimed_at,[ref]$claim) -or $claim -lt [datetimeoffset]::Parse($State.started_at)) {
                throw 'Cannot establish ownership of active repository session'
            }
            $sessionPath = Join-Path $Workspace 'project_coordination/ACTIVE_SESSION.json'
            $e.session.active=$false
            $e.session | Add-Member -NotePropertyName interruption_checkpoint -NotePropertyValue $Path -Force
            $e.session.last_updated=[datetimeoffset]::UtcNow.ToString('o')
            # Preserve every other session field and the old completion timestamp.
            [IO.File]::WriteAllText($sessionPath,($e.session|ConvertTo-Json -Depth 20),[Text.UTF8Encoding]::new($false))
        }
        Update-ControllerEvidence $Workspace $Path $State
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
