# Read-only launch-time checks before the existing Antigravity autonomous controller.
# This does not change controller state, clear a safety block, or validate a real PAD round-trip.
[CmdletBinding()]
param(
    [string]$Workspace = 'D:\Master thesis\Adaptive remeshing',
    [ValidateRange(1,1000)][int]$MaxTurns = 40,
    [ValidateRange(0,100)][int]$QuotaStopThresholdPct = 5,
    [switch]$VerifyOnly
)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

function Require([bool]$Condition, [string]$Message) {
    if (-not $Condition) { throw "PREFLIGHT_BLOCKED: $Message" }
}

$rules = Join-Path $Workspace '.agents\scripts\bridge_rules.txt'
$bridge = Join-Path $Workspace '.agents\scripts\Invoke-ChatGPTBridge.ps1'
$prompt = Join-Path $Workspace '.agents\INITIAL_PROMPT.txt'
$taskFile = Join-Path $Workspace 'project_coordination\ACTIVE_TASK.json'
$sessionFile = Join-Path $Workspace 'project_coordination\ACTIVE_SESSION.json'
$controller = Join-Path $env:USERPROFILE 'OpenClawPAD\Antigravity-Autonomous-Loop.ps1'
$deployedRules = Join-Path $env:USERPROFILE 'OpenClawPAD\ChatGPTBridge\bridge_rules.txt'

foreach ($path in @($rules, $bridge, $prompt, $taskFile, $sessionFile, $controller)) {
    Require (Test-Path -LiteralPath $path -PathType Leaf) "Required file missing: $path"
}
$ruleText = [IO.File]::ReadAllText($rules, [Text.Encoding]::UTF8)
$bridgeText = [IO.File]::ReadAllText($bridge, [Text.Encoding]::UTF8)
$promptText = [IO.File]::ReadAllText($prompt, [Text.Encoding]::UTF8)
Require ($ruleText.Contains('JOB-FIRST / REPORT-AFTER POLICY')) 'Bridge policy compatibility marker missing.'
Require ($bridgeText.Contains('Job-first execution policy missing')) 'Bridge parser/validation changed; inspect and requalify before running.'
foreach ($tag in @('CHATGPT_SUPERVISOR_V1', 'INDEPENDENT_STRUCTURED_REVIEW_V1', 'AUTOMATED MODE-I RESEARCH HANDOFF', 'safety_blocked=true')) {
    Require ($ruleText.Contains($tag)) "Bridge rules missing required contract token: $tag"
}
Require ($promptText.Contains('AUTONOMOUS_METHOD_C_PIPELINE_V2') -or (-not $promptText.Contains('AUTH_RECOVERY_LIVE_AGY') -and ($promptText.Contains('Method C') -or $promptText.Contains('F160')))) 'INITIAL_PROMPT.txt is not the verified Method C continuation prompt.'

# A second deployed copy can be chosen by some launcher paths; reject drift.
if (Test-Path -LiteralPath $deployedRules -PathType Leaf) {
    $canonicalHash = (Get-FileHash -LiteralPath $rules -Algorithm SHA256).Hash
    $deployedHash = (Get-FileHash -LiteralPath $deployedRules -Algorithm SHA256).Hash
    Require ($canonicalHash -ceq $deployedHash) 'Deployed ChatGPTBridge rules differ from canonical repository rules; sync safely and retest.'
}

$task = Get-Content -LiteralPath $taskFile -Raw -Encoding UTF8 | ConvertFrom-Json
$session = Get-Content -LiteralPath $sessionFile -Raw -Encoding UTF8 | ConvertFrom-Json
Require (-not [string]::IsNullOrWhiteSpace([string]$task.task_id)) 'ACTIVE_TASK has no task_id.'
Require ($session.active -eq $false) 'An active AGY session owns the workspace. Do not start a second controller.'

# Check the scientific checkpoint artifact if the current task declares one.
if ($task.PSObject.Properties['scientific_checkpoint'] -and $null -ne $task.scientific_checkpoint -and $task.scientific_checkpoint.PSObject.Properties['artifact'] -and $task.scientific_checkpoint.artifact) {
    $relative = [string]$task.scientific_checkpoint.artifact
    Require (-not ($relative -match '^([A-Za-z]:|[/\\])') -and -not ($relative -match '(^|[/\\])\.\.([/\\]|$)')) 'Unsafe scientific checkpoint path.'
    $artifactPath = Join-Path $Workspace $relative
    Require (Test-Path -LiteralPath $artifactPath -PathType Leaf) "Missing scientific checkpoint artifact: $relative"
    $actual = (Get-FileHash -LiteralPath $artifactPath -Algorithm SHA256).Hash
    $expected = [string]$task.scientific_checkpoint.sha256
    Require ($actual -ieq $expected) "Scientific checkpoint checksum mismatch: $relative"
}

# Test the real canonical prompt-assembly logic, without sending anything over PAD.
. $bridge
$probe = "AUTOMATED MODE-I RESEARCH HANDOFF`nPREFLIGHT_NONEXECUTING: verify current bridge contract only. Finished"
$assembled = Invoke-ChatGPTBridge -PromptText $probe -RulesPath $rules -DryRun
Require (-not [string]::IsNullOrWhiteSpace([string]$assembled)) 'Bridge dry-run returned an empty prompt.'
Require ([string]$assembled -match 'JOB-FIRST / REPORT-AFTER POLICY') 'Bridge dry-run lost compatibility marker.'
Require ([string]$assembled -match 'BRIDGE CONTROLLER RULES') 'Bridge dry-run did not embed the expected policy section.'

# Dry-run the actual deployed controller, not a substitute implementation.
Write-Host "[PREFLIGHT] Bridge policy and scientific checkpoint integrity PASS. Task: $($task.task_id)"
& powershell.exe -NoProfile -ExecutionPolicy Bypass -File $controller -ControllerDryRun
Require ($LASTEXITCODE -eq 0) "Controller dry-run failed with exit code $LASTEXITCODE"
Write-Host '[PREFLIGHT] Controller startup PASS; bridge transport and full-turn round-trip remain untested.'

if ($VerifyOnly) {
    Write-Host '[PREFLIGHT] VerifyOnly requested: no AGY turn dispatched.'
    return
}

# Handoff to canonical controller only AFTER local read-only gates pass.
# PowerShell.exe -File stringifies the $true argument and [bool] binding fails.
# -EncodedCommand preserves PowerShell expression types and process isolation.
Write-Host '[PREFLIGHT] Starting existing autonomous controller; all runtime permissions remain enforced by that controller.'
$controllerLiteral = "'" + $controller.Replace("'", "''") + "'"
$promptLiteral = "'" + $prompt.Replace("'", "''") + "'"
$command = @"
& $controllerLiteral -InitialPromptFile $promptLiteral -MaxTurns $MaxTurns -PrintTimeout '2400s' -EnableSmartAgyProfileSelection `$true -QuotaCheckEveryTurns 1 -QuotaStopThresholdPct $QuotaStopThresholdPct
if (-not `$?) { exit 1 }
"@
$encodedCommand = [Convert]::ToBase64String([Text.Encoding]::Unicode.GetBytes($command))
& powershell.exe -NoProfile -ExecutionPolicy Bypass -EncodedCommand $encodedCommand
exit $LASTEXITCODE
