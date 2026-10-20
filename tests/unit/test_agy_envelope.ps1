$ErrorActionPreference = 'Stop'
. "$PSScriptRoot/../../scripts/validation/ConvertFrom-AgyEnvelope.ps1"
$payload = @{conversation_id='test-conversation'; status='SUCCESS'; response='Nested {braces}, "quotes", and a trailing slash\'; usage=@{total_tokens=12}} | ConvertTo-Json -Depth 4
foreach ($text in @($payload, "warning`n$payload`n[agy] print timeout after 40m0s with turn in progress; returning partial output", "{bad diagnostic}`n$payload`n{`"other`":true}")) {
    $r = ConvertFrom-AgyEnvelope $text
    if ($r.response -ne 'Nested {braces}, "quotes", and a trailing slash\' -or $r.conversation_id -ne 'test-conversation') { throw 'Envelope changed' }
}
foreach ($text in @('not json', '{"conversation_id":"truncated","status":"SUCCESS"', '{"other":true}')) {
    $failed = $false
    try { $null = ConvertFrom-AgyEnvelope $text } catch { $failed = $true }
    if (-not $failed) { throw 'Invalid output accepted' }
}
'PASS: clean JSON, timeout suffix, leading warnings, unrelated objects, escaped strings, nested objects, and invalid/truncated rejection'

# Execute only the timeout branch, with all project effects stubbed. Never run the controller.
$controllerPath = "$env:USERPROFILE/OpenClawPAD/Antigravity-Autonomous-Loop.ps1"
$tokens = $null; $errors = $null
$ast = [Management.Automation.Language.Parser]::ParseFile($controllerPath, [ref]$tokens, [ref]$errors)
if ($errors.Count) { throw 'Controller syntax regression' }
$node = $ast.Find({param($n) $n -is [Management.Automation.Language.IfStatementAst] -and $n.Extent.Text.StartsWith("if (`$agyText -match '(?i)\[agy\] print timeout")}, $true)
if ($null -eq $node) { throw 'Timeout handler missing' }
$testCode = @'
function Get-AgyCompletedReceipt { return $null }
function Save-LoopState { $script:savedRecovery = $recovery }
function Set-ControllerInterrupted { return [pscustomobject]@{state='RECOVERY_REQUIRED'} }
function Get-ControllerRecoveryInstruction { return 'EVIDENCE_ONLY_RECOVERY: Never replay submissions' }
function Save-LoopStatus { $script:stoppedRecovery = $true }
function Write-LoopLog { }
$agyText = '[agy] print timeout after 40m0s with turn in progress; returning partial output'
$WorkspaceDir = $env:TEMP
$ConversationId = 'existing-conversation'
$CurrentTurn = 1
$CurrentInstruction = 'Original operation MUST NOT be replayed'
$AgyTimeoutRecoveryAttemptsByTurn = @{}
$turnDurationSeconds = 2400
$executions = 0
:MainLoop while ($CurrentTurn -le 1) {
    $executions++
'@ + "`n" + $node.Extent.Text + @'

    throw 'Timeout branch fell through into normal completion'
}
if ($executions -ne 1 -or $CurrentTurn -ne 2 -or -not $script:ControllerRecoveryMode -or $null -ne $ConversationId) { throw 'Recovery dispatch regression' }
if ($script:savedRecovery -notmatch 'Never replay submissions' -or $CurrentInstruction -notmatch 'EVIDENCE_ONLY_RECOVERY') { throw 'Submission replay protection missing' }
'PASS: isolated controller timeout handler saves partial evidence and schedules a fresh next recovery turn with zero immediate model calls'
'@
& ([scriptblock]::Create($testCode))
