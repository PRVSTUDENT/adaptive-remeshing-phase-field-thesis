[CmdletBinding()]
param(
    [int]$Port = 8765,
    [string]$BridgeDir = (Join-Path $env:USERPROFILE 'OpenClawPAD\ChatGPTBridge')
)
$ErrorActionPreference = 'Stop'
$scriptPath = Join-Path $PSScriptRoot 'local_bridge_server.py'
if (-not (Test-Path -LiteralPath $scriptPath)) { throw 'Missing local_bridge_server.py next to this launcher.' }
if (Get-Command py.exe -ErrorAction SilentlyContinue) {
    & py.exe -3 $scriptPath --bridge-dir $BridgeDir --port $Port
} elseif (Get-Command python.exe -ErrorAction SilentlyContinue) {
    & python.exe $scriptPath --bridge-dir $BridgeDir --port $Port
} else {
    throw 'Python 3 is required (standard library only).'
}
