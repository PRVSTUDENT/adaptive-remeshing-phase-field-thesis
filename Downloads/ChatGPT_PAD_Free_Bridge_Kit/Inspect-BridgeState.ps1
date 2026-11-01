# Read-only view of supervisor pending handoffs, legacy handshake and project session.
[CmdletBinding()]
param([string]$Workspace = 'D:\Master thesis\Adaptive remeshing')
$ErrorActionPreference = 'Stop'
$bridge = Join-Path $env:USERPROFILE 'OpenClawPAD\ChatGPTBridge'
$supervisor = Join-Path $bridge 'supervisor'
$sessionPath = Join-Path $Workspace 'project_coordination\ACTIVE_SESSION.json'
if (Test-Path -LiteralPath $sessionPath) {
    $session = Get-Content -LiteralPath $sessionPath -Raw | ConvertFrom-Json
    Write-Host "Project session active: $($session.active); run: $($session.controller_run_id)"
}
Get-ChildItem -LiteralPath $supervisor -Filter '*.pending.json' -File -ErrorAction SilentlyContinue |
    ForEach-Object {
        $r = Get-Content -LiteralPath $_.FullName -Raw | ConvertFrom-Json
        $dir = Join-Path $supervisor ([string]$r.correlation_id)
        $errFile = Join-Path $dir 'transport_error.txt'
        $resFile = Join-Path $dir 'response.txt'
        $decisionFile = Join-Path $dir 'decision.json'
        [pscustomobject]@{
            Pending = $_.Name
            HandoffId = $r.correlation_id
            HasTransportError = (Test-Path -LiteralPath $errFile)
            HasResponse = (Test-Path -LiteralPath $resFile)
            HasDecision = (Test-Path -LiteralPath $decisionFile)
        }
    } | Format-Table -AutoSize
foreach ($filename in @('bridge.lock','bridge_request.ready','bridge_response.ready','bridge_response.tmp','bridge_request.tmp')) {
    $path = Join-Path $bridge $filename
    Write-Host "$(if(Test-Path -LiteralPath $path){'PRESENT'}else{'absent '}) $filename"
}
