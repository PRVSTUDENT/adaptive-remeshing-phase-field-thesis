# Execute only after Inspect-BridgeState.ps1 shows no unresolved pending handoffs.
[CmdletBinding()]
param([string]$Workspace = 'D:\Master thesis\Adaptive remeshing')
$ErrorActionPreference = 'Stop'
$testObjective = @'
CONTROLLER MAINTENANCE ACCEPTANCE ONLY. No new numerical experiment.
ChatGPT: issue one bounded read-only Gemini task to existence-check canonical
coordination records and report the already-verified Package160 receipt without
editing scientific files, claiming physical acceptance, running solvers or
invoking any HPC submission. Gemini must return authentic read-only findings.
After receiving that result, return action STOP and a short acceptance finding.
Never repeat completed run 4040433d-9c04-40c6-916b-0dcc8abb6555. Preserve all
pending handoffs and once-only PBS accounting. This is transport planning,
not independent scientific approval. If evidence conflicts, STOP.
'@
$bridge = Join-Path $env:USERPROFILE 'OpenClawPAD\ChatGPTBridge'
$supervisor = Join-Path $bridge 'supervisor'
$pending = @(Get-ChildItem -LiteralPath $supervisor -Filter '*.pending.json' -File -ErrorAction SilentlyContinue)
if ($pending.Count) {
    throw ('Pending supervisor transaction(s) require evidence-based reconciliation first: ' +
        (($pending | Select-Object -ExpandProperty Name) -join ', '))
}
foreach ($file in @('bridge.lock','bridge_response.ready','bridge_response.tmp','bridge_request.tmp','bridge_request.ready')) {
    if (Test-Path -LiteralPath (Join-Path $bridge $file)) {
        throw "Existing $file must be reconciled, not overwritten."
    }
}
$session = Get-Content -LiteralPath (Join-Path $Workspace 'project_coordination\ACTIVE_SESSION.json') -Raw | ConvertFrom-Json
if ($session.active) { throw 'A project session is active. Do not start a duplicate.' }
$installed = Join-Path $env:USERPROFILE 'OpenClawPAD\Antigravity-Autonomous-Loop.ps1'
if (-not (Test-Path -LiteralPath $installed)) { throw 'Installed autonomous loop script not found.' }
$canonical = Join-Path $Workspace 'scripts\controller\Antigravity-Autonomous-Loop.ps1'
if ((Get-FileHash -LiteralPath $installed).Hash -ne (Get-FileHash -LiteralPath $canonical).Hash) {
    throw 'Installed controller differs from canonical source. Do not bypass the checksum.'
}
& $installed `
    -InitialPrompt $testObjective `
    -ChatGPTSupervisorMode `
    -ChatGPTBridgeLaunchPad:$false `
    -MaxTurns 2 `
    -PrintTimeout '2400s' `
    -EnableSmartAgyProfileSelection $true `
    -QuotaCheckEveryTurns 1 `
    -QuotaStopThresholdPct 20
