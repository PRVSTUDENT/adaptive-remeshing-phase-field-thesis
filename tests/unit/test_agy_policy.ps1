$ErrorActionPreference = 'Stop'
. "$PSScriptRoot/../../scripts/validation/AgyControllerPolicy.ps1"
foreach ($pair in @(@(14,100,$false),@(80,20,$false),@(20,80,$false),@(21,21,$true),@(0,0,$false),@(101,90,$false))) {
    $record = [pscustomobject]@{long_remaining_pct=$pair[0];five_h_remaining_pct=$pair[1]}
    if ((Test-AgyQuotaHeadroom $record) -ne $pair[2]) { throw 'Dual-window regression' }
}
if (Test-AgyQuotaHeadroom $null) { throw 'Unknown quota accepted' }
$now = [datetimeoffset]'2026-10-19T12:35:36Z'
$deadline = [datetimeoffset](Get-AgyQuotaCooldownDeadline -Message 'Individual quota reached. Resets in 115h29m17s.' -Now $now)
if ($deadline -ne $now.AddHours(115).AddMinutes(29).AddSeconds(77)) { throw 'Provider reset not respected' }
$longer = $now.AddDays(8).ToString('o')
if ([datetimeoffset](Get-AgyQuotaCooldownDeadline -Message 'Resets in 1h' -Now $now -ExistingUntil $longer) -ne [datetimeoffset]$longer) { throw 'Cooldown shortened' }
if ([datetimeoffset](Get-AgyQuotaCooldownDeadline -Message 'quota exhausted' -Now $now) -lt $now.AddHours(24)) { throw 'Unknown reset cooldown too short' }
if ((Get-AgyBoundedText -Text ('x'*86000) -Limit 6000).Length -gt 6100) { throw 'Prompt unbounded' }

# Exercise installed controller functions with local mocks, without starting it.
$controllerPath = "$env:USERPROFILE/OpenClawPAD/Antigravity-Autonomous-Loop.ps1"
$tokens=$null; $errors=$null
$ast=[Management.Automation.Language.Parser]::ParseFile($controllerPath,[ref]$tokens,[ref]$errors)
if ($errors.Count) { throw 'Installed controller syntax failure' }
foreach ($name in @('Select-AgySmartCandidate','Get-AgySmartCooldownActive','Invoke-EscalationChatGPT')) {
    $functionAst=$ast.Find({param($n) $n -is [Management.Automation.Language.FunctionDefinitionAst] -and $n.Name -eq $name},$true)
    if ($null -eq $functionAst) { throw "Missing function $name" }
    . ([scriptblock]::Create($functionAst.Extent.Text))
}
$SmartMinLongRemainingPct=20; $QuotaStopThresholdPct=20
$script:SmartCooldowns=@{account3=[datetimeoffset]::UtcNow.AddDays(5).ToString('o')}
$records=@(
    [pscustomobject]@{profile='account1';long_remaining_pct=14;five_h_remaining_pct=100;minutes_until_long_reset=1},
    [pscustomobject]@{profile='account2';long_remaining_pct=96;five_h_remaining_pct=80;minutes_until_long_reset=100},
    [pscustomobject]@{profile='account3';long_remaining_pct=99;five_h_remaining_pct=99;minutes_until_long_reset=2}
)
if ((Select-AgySmartCandidate -Records $records).profile -ne 'account2') { throw 'Selector bypassed dual-window/cooldown guards' }
function Invoke-ChatGPTBridgeWithManualFallback { param($Prompt,$ContextLabel) $script:capturedPrompt=$Prompt; return 'NEXT' }
$WorkspaceDir=[IO.Path]::GetFullPath("$PSScriptRoot/../..")
$CurrentTurn=3
$null=Invoke-EscalationChatGPT -AntigravityResponse ('result '*13000) -QuotaSnapshotText ('quota '*10000)
$rulesPath=Join-Path $WorkspaceDir '.agents/scripts/bridge_rules.txt'
$rulesLength=if(Test-Path -LiteralPath $rulesPath){(Get-Item -LiteralPath $rulesPath).Length}else{0}
if ($script:capturedPrompt.Length -gt 17000 -or $script:capturedPrompt.Length+$rulesLength -gt 35000) { throw 'Bridge context regressed to unbounded size' }
. "$PSScriptRoot/../../scripts/controller/Controller-Recovery.ps1"
foreach ($pair in @(@('2400s',480),@('120s',90))) {
    $budget=Get-ControllerBudget $pair[0] 600
    if ($budget.work -ne $pair[1] -or ($budget.work+$budget.closeout) -gt 600) { throw 'Installed turn budget/reserve not enforced' }
}

$folder = Join-Path $env:TEMP ('agy-policy-test-' + [guid]::NewGuid().ToString('N'))
try {
    $coord = Join-Path $folder 'project_coordination'
    $reports = Join-Path $coord 'sessions'
    $null = New-Item -ItemType Directory -Path $reports -Force
    $since = [datetimeoffset]::UtcNow.AddMinutes(-2)
    $reportPath = Join-Path $reports '2026_F9999-test.md'
    ('Verified quantitative research result. '*10) | Set-Content -LiteralPath $reportPath
    $sessionPath = Join-Path $coord 'ACTIVE_SESSION.json'
    @{active=$false;task_id='F9999-TEST';last_released=[datetimeoffset]::UtcNow.ToString('o')} | ConvertTo-Json | Set-Content $sessionPath
    'type,canonical_path', 'session_report,project_coordination/sessions/2026_F9999-test.md' | Set-Content (Join-Path $coord 'ARTIFACT_REGISTRY.csv')
    if ($null -eq (Get-AgyCompletedReceipt -WorkspaceDir $folder -Since $since)) { throw 'Registry-based completed receipt not recovered' }
    (Get-Item $reportPath).LastWriteTimeUtc = $since.UtcDateTime.AddHours(-1)
    if ($null -ne (Get-AgyCompletedReceipt -WorkspaceDir $folder -Since $since)) { throw 'Stale receipt accepted' }
    (Get-Item $reportPath).LastWriteTimeUtc = [datetime]::UtcNow
    @{active=$true;task_id='F9999-TEST';last_released=[datetimeoffset]::UtcNow.ToString('o')} | ConvertTo-Json | Set-Content $sessionPath
    if ($null -ne (Get-AgyCompletedReceipt -WorkspaceDir $folder -Since $since)) { throw 'Active session accepted' }
} finally {
    # Exact test directory under TEMP, checked before recursive cleanup.
    $resolved = [IO.Path]::GetFullPath($folder)
    $tempRoot = [IO.Path]::GetFullPath($env:TEMP).TrimEnd('\') + '\'
    if (-not $resolved.StartsWith($tempRoot,[StringComparison]::OrdinalIgnoreCase) -or (Split-Path $resolved -Leaf) -notlike 'agy-policy-test-*') { throw 'Unsafe test cleanup path' }
    if (Test-Path -LiteralPath $resolved) { Remove-Item -LiteralPath $resolved -Recurse -Force }
}
'PASS: dual-window thresholds, reported reset, cooldown monotonicity, bounded prompts, fresh registered receipt, stale/active rejection'
