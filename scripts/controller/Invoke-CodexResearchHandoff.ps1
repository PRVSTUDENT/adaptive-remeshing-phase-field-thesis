[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$PromptFile,
    [Parameter(Mandatory)][ValidatePattern('^HND-CODEX-[A-Za-z0-9-]+$')][string]$HandoffId,
    [string]$Workspace = 'D:\Master thesis\Adaptive remeshing',
    [ValidateRange(1,40)][int]$TimeoutMinutes = 15,
    [switch]$DryRun
)
$ErrorActionPreference = 'Stop'
$session = Get-Content (Join-Path $Workspace 'project_coordination/ACTIVE_SESSION.json') -Raw | ConvertFrom-Json
if (-not $session.active -or $session.agent -cne 'codex') { throw 'CODEX_SESSION_REQUIRED' }
$workers = Get-CimInstance Win32_Process | Where-Object {
    $_.ProcessId -ne $PID -and $_.Name -match '^(powershell|pwsh|agy)\.exe$' -and
    $_.CommandLine -match '(?:-File\s+[^\r\n]*(?:Antigravity-Autonomous-Loop|Start-Verified-MethodCLoop)\.ps1|agy\.exe"?\s+.*--print)'
}
if ($workers) { throw 'COMPETING_RESEARCH_WORKER' }
$prompt = [IO.File]::ReadAllText((Resolve-Path -LiteralPath $PromptFile), [Text.Encoding]::UTF8)
if (-not $prompt.StartsWith('AUTOMATED MODE-I RESEARCH HANDOFF') -or -not $prompt.TrimEnd().EndsWith('Finished')) { throw 'HANDOFF_FORMAT_INVALID' }
. (Join-Path $Workspace '.agents/scripts/Invoke-ChatGPTBridge.ps1')
if ($DryRun) { Invoke-ChatGPTBridge -PromptText $prompt -HandoffId $HandoffId -DryRun; return }
$bridgeDir = Join-Path $env:USERPROFILE 'OpenClawPAD/ChatGPTBridge'
foreach ($name in @('bridge.lock','bridge_request.ready','bridge_request.tmp','bridge_response.ready','bridge_response.tmp')) {
    if (Test-Path -LiteralPath (Join-Path $bridgeDir $name)) { throw "PENDING_BRIDGE_TRANSACTION: $name; preserve and reconcile" }
}
$receiptDir = Join-Path $Workspace 'project_coordination/codex_loop'
[void][IO.Directory]::CreateDirectory($receiptDir)
$receiptPath = Join-Path $receiptDir ($HandoffId + '.json')
$receipt = [ordered]@{schema=1;executor='codex';session_id=$session.session_id;task_id=$session.task_id;
    handoff_id=$HandoffId;status='RESERVED_ONCE';created_at=[DateTimeOffset]::UtcNow.ToString('o');
    prompt_sha256=(Get-FileHash -LiteralPath $PromptFile).Hash;response='';error_category=''}
# CreateNew is the durable once-only reservation; never reuse an interrupted ID.
$stream = [IO.File]::Open($receiptPath,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::None)
try { $bytes=[Text.Encoding]::UTF8.GetBytes(($receipt|ConvertTo-Json -Depth 8)); $stream.Write($bytes,0,$bytes.Length); $stream.Flush($true) }
finally { $stream.Dispose() }
try {
    $reply = Invoke-ChatGPTBridge -PromptText $prompt -HandoffId $HandoffId -BridgeDir $bridgeDir -TimeoutMinutes $TimeoutMinutes
    $receipt.status='RECEIVED_VALIDATED';$receipt.response=$reply
    $receipt.completed_at=[DateTimeOffset]::UtcNow.ToString('o')
    $reply
} catch {
    $receipt.status='RECONCILIATION_REQUIRED';$receipt.error_category=$_.Exception.Message
    throw
} finally {
    $tmp=$receiptPath+'.tmp';[IO.File]::WriteAllText($tmp,($receipt|ConvertTo-Json -Depth 8),[Text.UTF8Encoding]::new($false))
    [IO.File]::Replace($tmp,$receiptPath,($receiptPath+'.reservation.bak'))
}
