[CmdletBinding()]
param(
    [string]$Workspace = 'D:\Master thesis\Adaptive remeshing',
    [string]$ControllerRoot = (Join-Path $env:USERPROFILE 'OpenClawPAD'),
    [Parameter(Mandatory=$true)][string]$EvidenceManifest,
    [string]$ExpectedOriginalSha256 = 'E117C7BA3320E5F27DCB2115B863F7D0D2E18C822B2FC102B953096A794C92A9',
    [switch]$Apply
)
$ErrorActionPreference = 'Stop'
. (Join-Path $Workspace 'scripts/controller/Controller-Recovery.ps1')

# Never dispatch a model or perform remote operations here. Dry-run is read-only.
$sid = [Security.Principal.WindowsIdentity]::GetCurrent().User.Value
$mutex = [Threading.Mutex]::new($false, ('Global\AdaptiveRemeshing.AgyController.' + $sid))
$locked = $false
try {
    $locked = $mutex.WaitOne(0)
    if (-not $locked) { throw 'BLOCKED: autonomous controller is active' }
    $path = Join-Path $ControllerRoot 'controller_turn_checkpoint.json'
    $state = Read-ControllerCheckpoint $path
    if (-not (Test-Path -LiteralPath $EvidenceManifest -PathType Leaf)) { throw 'BLOCKED: evidence manifest missing' }
    $manifestHash = (Get-FileHash -LiteralPath $EvidenceManifest).Hash
    $m = Get-Content -LiteralPath $EvidenceManifest -Raw -Encoding UTF8 | ConvertFrom-Json
    if ($m.run_id -ne '77c4cf2d-e740-4737-bb8a-a858fc0afd5a' -or $m.turn -ne 294 -or
        $m.completed_turn -ne 293 -or $m.resume_scope -ne 'EVIDENCE_ONLY' -or
        $m.original_sha256 -ne $ExpectedOriginalSha256 -or
        $m.hpc_classification -ne 'NO_MATCH_IN_RETAINED_EVIDENCE_NON_SUBMISSION_UNPROVEN') {
        throw 'BLOCKED: invalid evidence manifest identity or HPC classification'
    }
    $roles = @('original_checkpoint','loop_state','partial_output','jsonl','session_report','bootstrap','hpc_ledger','current_state','active_session','previous_checkpoint','remote_history','remote_candidate','remote_active','remote_directories','remote_predecessor','remote_trace','remote_accounting')
    foreach ($role in $roles) {
        $items = @($m.evidence | Where-Object { $_.role -eq $role })
        if ($items.Count -ne 1) { throw "BLOCKED: missing or duplicate evidence role $role" }
    }
    foreach ($e in $m.evidence) {
        if (-not $e.path -or -not $e.sha256 -or -not (Test-Path -LiteralPath $e.path -PathType Leaf) -or
            (Get-FileHash -LiteralPath $e.path).Hash -ne $e.sha256 -or
            -not (Get-Item -LiteralPath $e.path).IsReadOnly) { throw 'BLOCKED: immutable evidence check failed' }
    }
    foreach ($role in @('remote_history','remote_candidate','remote_active','remote_predecessor')) {
        $e = $m.evidence | Where-Object role -eq $role
        if ($e.exit_code -ne 0) { throw "BLOCKED: unsuccessful remote query $role" }
        $text = Get-Content -LiteralPath $e.path -Raw -Encoding UTF8
        if ($role -eq 'remote_candidate' -and -not [string]::IsNullOrWhiteSpace($text)) { throw 'BLOCKED: possible existing Package140 PBS ID requires accounting review' }
        if ($role -in @('remote_history','remote_active') -and $text -match '(?i)H31|INC92') { throw 'BLOCKED: possible Package140 scheduler match requires accounting review' }
        if ($role -eq 'remote_history' -and $text -notmatch 'M1_C4_INC91_H30_CONT') { throw 'BLOCKED: retained history lacks known predecessor' }
        if ($role -eq 'remote_predecessor' -and ($text -notmatch '1418554.mmaster02' -or $text -notmatch 'Exit_status\s*=\s*0')) { throw 'BLOCKED: predecessor receipt not verified' }
    }
    if ($state.reconciliation.status -eq 'INTERRUPTED_TURN294_EVIDENCE_ONLY_READY') {
        Assert-ControllerDispatchCheckpoint $Workspace $state
        if ($state.reconciliation.manifest_sha256 -ne $manifestHash) { throw 'BLOCKED: different reconciliation already applied' }
        return [pscustomobject]@{classification='ALREADY_APPLIED';checkpoint_sha256=(Get-FileHash $path).Hash;turn=294;completed_turn=293}
    }
    if ($state.state -ne 'BLOCKED' -or $state.run_id -ne $m.run_id -or $state.turn -ne 294 -or
        (Get-FileHash $path).Hash -ne $ExpectedOriginalSha256) { throw 'BLOCKED: checkpoint identity/hash changed' }
    $loopPath = Join-Path $ControllerRoot 'antigravity_loop_state.json'
    $loop = Get-Content -LiteralPath $loopPath -Raw -Encoding UTF8 | ConvertFrom-Json
    $loopEvidence = $m.evidence | Where-Object role -eq 'loop_state'
    if ($loop.completed_turn -ne 293 -or (Get-FileHash $loopPath).Hash -ne $loopEvidence.sha256) { throw 'BLOCKED: actual loop state changed' }
    $original = $m.evidence | Where-Object role -eq 'original_checkpoint'
    if ($original.sha256 -ne $ExpectedOriginalSha256) { throw 'BLOCKED: original archive hash mismatch' }
    $null = Get-ControllerRecoveryInstruction $state
    $candidate = $state | ConvertTo-Json -Depth 30 | ConvertFrom-Json
    $candidate.state = 'RECOVERY_REQUIRED'
    $candidate.block_reason = ''
    $candidate.conversation_id = ''
    $candidate.stop_reason = 'INTERRUPTED_ATTEMPT_EVIDENCE_ONLY_READY'
    $candidate.next_safe_action = 'Resume Turn294 evidence-only recovery in a fresh conversation. Package140 non-submission is unproven; no submission or original instruction replay.'
    $record = [pscustomobject]@{
        status='INTERRUPTED_TURN294_EVIDENCE_ONLY_READY';original_checkpoint=$original.path
        original_sha256=$ExpectedOriginalSha256;manifest_path=$EvidenceManifest;manifest_sha256=$manifestHash
        turn=294;completed_turn=293;resume_scope='EVIDENCE_ONLY';scientific_completion=$false
        hpc_classification=$m.hpc_classification;pending_instruction_hash=$state.original_instruction_hash
        evidence=@($m.evidence) + @([pscustomobject]@{role='manifest';path=$EvidenceManifest;sha256=$manifestHash})
        reconciled_at=[DateTimeOffset]::UtcNow.ToString('o')
    }
    $candidate | Add-Member -NotePropertyName reconciliation -NotePropertyValue $record -Force
    Assert-ControllerDispatchCheckpoint $Workspace $candidate
    $instruction = Get-ControllerRecoveryInstruction $candidate
    if ($Apply) {
        # Compare again immediately before the single atomic write; loop files are untouched.
        if ((Get-FileHash $path).Hash -ne $ExpectedOriginalSha256) { throw 'BLOCKED: concurrent checkpoint change' }
        Write-ControllerCheckpoint $path $candidate
        Assert-ControllerDispatchCheckpoint $Workspace (Read-ControllerCheckpoint $path)
    }
    [pscustomobject]@{classification=if($Apply){'APPLIED_EVIDENCE_ONLY'}else{'DRY_RUN_PASS'};state=$candidate.state;turn=294;completed_turn=293;original_sha256=$ExpectedOriginalSha256;checkpoint_sha256=(Get-FileHash $path).Hash;next_instruction=$instruction}
} finally {
    if ($locked) { $mutex.ReleaseMutex() }
    $mutex.Dispose()
}
