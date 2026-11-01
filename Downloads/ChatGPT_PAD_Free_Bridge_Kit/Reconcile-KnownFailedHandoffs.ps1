# This reconciles ONLY proven bridge transport failures (timeout / wrong correlation).
# It NEVER edits scientific/HPC state or a controller checkpoint.
[CmdletBinding()]
param(
    [switch]$ArchiveVerifiedFailures,
    [string]$Workspace = 'D:\Master thesis\Adaptive remeshing'
)
$ErrorActionPreference = 'Stop'
$bridge = Join-Path $env:USERPROFILE 'OpenClawPAD\ChatGPTBridge'
$supervisor = Join-Path $bridge 'supervisor'
$sessionPath = Join-Path $Workspace 'project_coordination\ACTIVE_SESSION.json'
$session = Get-Content -LiteralPath $sessionPath -Raw | ConvertFrom-Json
if ($session.active) { throw 'STOP: a project session is active' }
$activeControllers = @(Get-CimInstance Win32_Process | Where-Object {
    $_.ProcessId -ne $PID -and
    $_.Name -in @('powershell.exe','pwsh.exe') -and
    $_.CommandLine -match 'Antigravity-Autonomous-Loop.ps1|Invoke-ChatGPTBridge.ps1'
})
if ($activeControllers.Count) { throw 'STOP: a local controller/bridge PowerShell process is still running' }
$checkpointPath = Join-Path $env:USERPROFILE 'OpenClawPAD\controller_turn_checkpoint.json'
if (Test-Path -LiteralPath $checkpointPath) {
    . (Join-Path $Workspace 'scripts/controller/Controller-Recovery.ps1')
    $cp = Read-ControllerCheckpoint $checkpointPath
    Assert-ControllerDispatchCheckpoint $Workspace $cp
    if ($cp.state -notin @('COMPLETED','PENDING')) {
        throw "STOP: controller checkpoint $($cp.state) must be independently reconciled"
    }
}
foreach ($filename in @('bridge.lock','bridge_response.ready','bridge_response.tmp','bridge_request.tmp')) {
    if (Test-Path -LiteralPath (Join-Path $bridge $filename)) {
        throw "STOP: $filename exists; possible live/unconsumed transaction"
    }
}
$pending = @(Get-ChildItem -LiteralPath $supervisor -Filter '*.pending.json' -File -ErrorAction SilentlyContinue)
if ($pending.Count -eq 0) { Write-Host 'No pending supervisor transactions.'; return }
$plan = @()
foreach ($file in $pending) {
    $r = Get-Content -LiteralPath $file.FullName -Raw | ConvertFrom-Json
    $id = [string]$r.correlation_id
    # Old SUP-only failures predate the corrected browser trigger. Preserve and
    # inspect them by original identity; never rename/replay them as HND IDs.
    if ($id -notmatch '^(HND-)?SUP-[a-fA-F0-9]{32}$') { throw "STOP: invalid ID in $($file.Name)" }
    $dir = Join-Path $supervisor $id
    if ([IO.Path]::GetFullPath([string]$r.archive) -ine [IO.Path]::GetFullPath($dir)) {
        throw "STOP: mismatched original archive in $($file.Name)"
    }
    $request = Join-Path $dir 'request.txt'
    $errorPath = Join-Path $dir 'transport_error.txt'
    $replyPath = Join-Path $dir 'response.txt'
    $decision = Join-Path $dir 'decision.json'
    if (!(Test-Path -LiteralPath $request) -or !(Test-Path -LiteralPath $errorPath)) {
        throw "STOP: missing original request/error evidence $id"
    }
    if (!(Select-String -LiteralPath $request -SimpleMatch "[BRIDGE_HANDOFF_ID=$id]" -Quiet)) {
        throw "STOP: original request identity mismatch $id"
    }
    if (Test-Path -LiteralPath $decision) {
        throw "STOP: existing decision requires independent completion reconciliation $id"
    }
    $errorText = Get-Content -LiteralPath $errorPath -Raw
    $status = ''
    if ($errorText -match 'SUPERVISOR_STALE_RESPONSE') {
        if (!(Test-Path -LiteralPath $replyPath)) {
            throw "STOP: stale-response error without preserved response $id"
        }
        $raw = (Get-Content -LiteralPath $replyPath -Raw).Trim()
        $raw = $raw -replace '^```(?:json)?\s*','' -replace '\s*```$',''
        try { $reply = $raw | ConvertFrom-Json -ErrorAction Stop }
        catch { throw "STOP: cannot parse rejected response $id; inspect manually" }
        if ([string]$reply.correlation_id -eq $id) {
            throw "STOP: reply matched original ID; conflict requires manual investigation $id"
        }
        $status = 'PROVEN_REJECTED_CORRELATION'
    } elseif ($errorText -match 'Bridge timeout reached') {
        if (Test-Path -LiteralPath $replyPath) {
            throw "STOP: timeout with a preserved response $id; inspect manually"
        }
        $status = 'PROVEN_TIMEOUT_NO_CONSUMED_RESPONSE'
    } else { throw "STOP: unrecognized failure $id; no automatic reconciliation" }
    $target = Join-Path $dir ('reconciled_' + (Get-Date -Format yyyyMMdd_HHmmss_fff) + '.pending.json')
    if (Test-Path -LiteralPath $target) { throw "STOP: archive collision $target" }
    $plan += [pscustomobject]@{
        Id=$id; Classification=$status; Source=$file.FullName; Destination=$target; Dir=$dir
    }
}
$readyPath = Join-Path $bridge 'bridge_request.ready'
$readyOwner = $null
if (Test-Path -LiteralPath $readyPath) {
    $text = Get-Content -LiteralPath $readyPath -Raw
    $match = @($plan | Where-Object { $text.Contains("[BRIDGE_HANDOFF_ID=$($_.Id)]") })
    if ($match.Count -ne 1) { throw 'STOP: bridge_request.ready does not belong to exactly one known failed transaction' }
    $readyOwner = $match[0]
}
$plan | Select-Object Id, Classification, Source, Destination | Format-Table -AutoSize
if (-not $ArchiveVerifiedFailures) {
    Write-Host 'READ-ONLY. Review classifications, then add -ArchiveVerifiedFailures to archive only these confirmed failures.'
    return
}
if ($readyOwner) {
    $archivedRequest = Join-Path $readyOwner.Dir ('stale_request_' + (Get-Date -Format yyyyMMdd_HHmmss_fff) + '.ready')
    Move-Item -LiteralPath $readyPath -Destination $archivedRequest -ErrorAction Stop
}
foreach ($item in $plan) {
    Move-Item -LiteralPath $item.Source -Destination $item.Destination -ErrorAction Stop
    Write-Host "ARCHIVED confirmed failed supervisor transaction: $($item.Id) [$($item.Classification)]" -ForegroundColor Green
}
Write-Host 'Failed handoffs archived. No controller checkpoints, scientific results, or HPC ledgers were changed.'
