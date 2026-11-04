# Planning transport only. A reply never activates an execution/review policy.
function Invoke-ControllerSupervisor {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)][string]$Workspace,
        [Parameter(Mandatory)][ValidateSet('INITIAL','RESULT','ERROR')][string]$Kind,
        [Parameter(Mandatory)][string]$Evidence,
        [string]$RunId = 'startup',
        [int]$Turn = 0,
        [switch]$SafetyBlocked,
        [int]$TimeoutMinutes = 15,
        [switch]$LaunchPad,
        [scriptblock]$Transport,
        [string]$ArchiveRoot = (Join-Path $env:USERPROFILE 'OpenClawPAD/ChatGPTBridge/supervisor')
    )
    # Never resend an uncertain transaction automatically, including after restart.
    [IO.Directory]::CreateDirectory($ArchiveRoot) | Out-Null
    $key = ($RunId + '-' + $Turn + '-' + $Kind) -replace '[^a-zA-Z0-9_-]', '_'
    $pending = Join-Path $ArchiveRoot ($key + '.pending.json')
    if (Test-Path -LiteralPath $pending) { throw "SUPERVISOR_RECONCILIATION_REQUIRED: $pending" }
    # The installed Tampermonkey v1.5 paste listener only arms on HND- IDs.
    $id = 'HND-SUP-' + [guid]::NewGuid().ToString('N')
    $dir = Join-Path $ArchiveRoot $id
    [IO.Directory]::CreateDirectory($dir) | Out-Null
    $utf8 = [Text.UTF8Encoding]::new($false)
    $snapshot = [ordered]@{correlation_id=$id;kind=$Kind;run_id=$RunId;turn=$Turn;safety_blocked=[bool]$SafetyBlocked;evidence=$Evidence;files=@{}}
    foreach ($relative in @('project_coordination/ACTIVE_SESSION.json','project_coordination/ACTIVE_TASK.json','project_coordination/HPC_JOB_LEDGER.csv')) {
        $path = Join-Path $Workspace $relative
        if (Test-Path -LiteralPath $path) {
            $snapshot.files[$relative] = (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash
            [IO.File]::Copy($path,(Join-Path $dir ([IO.Path]::GetFileName($path))),$false)
        }
    }
    $checkpoint = Join-Path $env:USERPROFILE 'OpenClawPAD/controller_turn_checkpoint.json'
    if(Test-Path -LiteralPath $checkpoint){[IO.File]::Copy($checkpoint,(Join-Path $dir 'controller_turn_checkpoint.json'),$false)}
    $body = $snapshot | ConvertTo-Json -Depth 12
    [IO.File]::WriteAllText((Join-Path $dir 'evidence.json'),$body,$utf8)
    $prompt = @"
[BRIDGE_HANDOFF_ID=$id]
CHATGPT_SUPERVISOR_V1
You are the scientific supervisor; Gemini is the bounded executor. This is planning, never independent approval or cryptographic authorization. Preserve all project scientific, ownership, resource and once-only PBS gates. Do not replay completed operations. No new HPC jobs during maintenance acceptance.
HPC STATUS: See archived ledger hashes and verified evidence below; never infer live scheduler status.
SCIENTIFIC RESULT / ERROR: $body
NEXT DECISION: Return ONLY a JSON object with correlation_id exactly "$id", action one of DIAGNOSE, CONTINUE, WAIT, STOP, and instruction containing one bounded actionable task. If safety_blocked=true, execution remains stopped regardless of your reply; provide diagnostic guidance only. No credential values in replies.
"@
    [IO.File]::WriteAllText((Join-Path $dir 'request.txt'),$prompt,$utf8)
    [IO.File]::WriteAllText($pending,(@{correlation_id=$id;archive=$dir}|ConvertTo-Json),$utf8)
    try {
        if (-not $Transport) {
            . (Join-Path $Workspace '.agents/scripts/Invoke-ChatGPTBridge.ps1')
            $raw = Invoke-ChatGPTBridge -PromptText $prompt -HandoffId $id -TimeoutMinutes $TimeoutMinutes -RequireHeartbeat -LaunchPad:$LaunchPad
        } else { $raw = & $Transport $prompt $id }
        [IO.File]::WriteAllText((Join-Path $dir 'response.txt'),[string]$raw,$utf8)
        $rawStr = [string]$raw
        $firstBrace = $rawStr.IndexOf('{')
        $lastBrace = $rawStr.LastIndexOf('}')
        if ($firstBrace -ge 0 -and $lastBrace -gt $firstBrace) {
            $clean = $rawStr.Substring($firstBrace, $lastBrace - $firstBrace + 1)
        } else {
            $clean = $rawStr.Trim() -replace '^\s*(?:```(?:json)?|json)\s*','' -replace '\s*```\s*$',''
        }
        $reply = $clean | ConvertFrom-Json -ErrorAction Stop
        if ($reply.correlation_id -cne $id) { throw 'SUPERVISOR_STALE_RESPONSE: correlation mismatch' }
        if ($reply.action -cnotin @('DIAGNOSE','CONTINUE','WAIT','STOP')) { throw 'SUPERVISOR_INVALID_ACTION' }
        if ([string]::IsNullOrWhiteSpace($reply.instruction)) { throw 'SUPERVISOR_EMPTY_INSTRUCTION' }
        $decision = [ordered]@{correlation_id=$id;action=$reply.action;instruction=[string]$reply.instruction;execution_allowed=(!$SafetyBlocked -and $reply.action -in @('DIAGNOSE','CONTINUE'));approval=$false}
        [IO.File]::WriteAllText((Join-Path $dir 'decision.json'),($decision|ConvertTo-Json),$utf8)
        Remove-Item -LiteralPath $pending -ErrorAction Stop
        return [pscustomobject]$decision
    } catch {
        [IO.File]::WriteAllText((Join-Path $dir 'transport_error.txt'),($_|Out-String),$utf8)
        throw # Pending marker remains; no uncertain handoff replay.
    }
}
