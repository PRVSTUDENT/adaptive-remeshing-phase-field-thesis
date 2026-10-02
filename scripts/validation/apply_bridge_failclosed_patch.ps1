# Cleanly replace Invoke-ChatGPTBridgeWithManualFallback and fix line 1222 in Antigravity-Autonomous-Loop.ps1
$targetFile = "C:\Users\pruth\OpenClawPAD\Antigravity-Autonomous-Loop.ps1"
$lines = [System.IO.File]::ReadAllLines($targetFile, [System.Text.UTF8Encoding]::new($false))

# 1. Fix line 1222 manual responseFile write
for ($i = 0; $i -lt $lines.Length; $i++) {
    if ($lines[$i] -match '\$responseFile\s*=\s*Join-Path\s+-Path\s+\$historyDir\s+-ChildPath\s+\("\{0\}\*\{1\}_chatgpt_response\.txt"') {
        Write-Host "Replacing unsafe responseFile write at line $($i + 1)"
        $lines[$i] = @'
        $responseFileName = "${handoffId}_${safeContext}_chatgpt_response.txt"
        $responseFile = Write-SafeUtf8File `
            -Directory $historyDir `
            -FileName $responseFileName `
            -Content $replyTrim
'@
        # Comment out the old WriteAllText lines
        if ($lines[$i + 2] -match '\[System\.IO\.File\]::WriteAllText') {
            $lines[$i + 2] = "        # [System.IO.File]::WriteAllText replaced by Write-SafeUtf8File"
            $lines[$i + 3] = "        # $responseFile"
            $lines[$i + 4] = "        # $replyTrim"
            $lines[$i + 5] = "        # [System.Text.UTF8Encoding]::new($false)"
            $lines[$i + 6] = "        # )"
        }
        break
    }
}

# 2. Replace Invoke-ChatGPTBridgeWithManualFallback (from function header to closing brace)
$startIdx = -1
$endIdx = -1
for ($i = 0; $i -lt $lines.Length; $i++) {
    if ($lines[$i] -match '^function Invoke-ChatGPTBridgeWithManualFallback\b') {
        $startIdx = $i
        # Find closing brace before Invoke-EscalationChatGPT
        for ($j = $i + 1; $j -lt $lines.Length; $j++) {
            if ($lines[$j] -match '^function Invoke-EscalationChatGPT\b') {
                # backtrack to find the previous non-empty line which should be the closing brace
                for ($k = $j - 1; $k -gt $i; $k--) {
                    if ($lines[$k].Trim() -eq '}') {
                        $endIdx = $k
                        break
                    }
                }
                break
            }
        }
        break
    }
}

if ($startIdx -ge 0 -and $endIdx -ge 0) {
    Write-Host "Replacing Invoke-ChatGPTBridgeWithManualFallback from line $($startIdx + 1) to $($endIdx + 1)"
    $newBridgeCode = @'
function Invoke-ChatGPTBridgeWithManualFallback {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Prompt,

        [string]$ContextLabel = "chatgpt"
    )

    if ($script:PreferManualChatGPTBridge -and $EnableManualClipboardFallback) {
        return Invoke-ManualChatGPTBridge `
            -Prompt $Prompt `
            -ContextLabel $ContextLabel
    }

    $BridgeScript = "D:\Master thesis\Adaptive remeshing\.agents\scripts\ask_chatgpt_tampermonkey.ps1"

    if (-not (Test-Path -LiteralPath $BridgeScript)) {
        if ($EnableManualClipboardFallback) {
            Write-Host ""
            Write-Host "Automatic bridge script not found. Using manual clipboard mode." -ForegroundColor Yellow
            Write-Host ""
            return Invoke-ManualChatGPTBridge -Prompt $Prompt -ContextLabel $ContextLabel
        }
        throw "Automatic ChatGPT bridge script not found at: $BridgeScript"
    }

    $attempts = [Math]::Max(1, $ChatGPTBridgeMaxAttempts)
    $timeoutSec = [Math]::Max(10, $ChatGPTBridgeTimeoutSeconds)

    for ($attempt = 1; $attempt -le $attempts; $attempt++) {
        try {
            $BridgeOutput = (
                $Prompt |
                    & $BridgeScript `
                        -TimeoutSeconds $timeoutSec
            ) | Out-String

            $Reply = $BridgeOutput.Trim()

            if ([string]::IsNullOrWhiteSpace($Reply)) {
                throw "Automatic ChatGPT bridge returned an empty response."
            }

            if (
                $Reply -match 'Configured browser node not connected' -or
                $Reply -match 'Could not enumerate OpenClaw Chrome tabs' -or
                $Reply -match 'Browser control authentication was blocked' -or
                $Reply -match 'Relay unreachable' -or
                $Reply -match 'GatewayClientRequestError' -or
                $Reply -match 'GatewayTransportError'
            ) {
                throw "Automatic browser bridge returned a browser/gateway failure: $Reply"
            }

            return $Reply
        }
        catch {
            $bridgeError = $_.Exception.Message

            Write-Warning "ChatGPT local bridge attempt $attempt of $attempts failed: $bridgeError"

            if ($attempt -lt $attempts) {
                Write-Host "[CHATGPT-LOCAL-BRIDGE] Retrying SAME handoff in 2 seconds..." -ForegroundColor Cyan
                Start-Sleep -Seconds 2
                continue
            }

            if ($EnableManualClipboardFallback) {
                try {
                    Write-LoopLog `
                        -Turn $CurrentTurn `
                        -Tier "tier3_chatgpt" `
                        -Action "AUTO_BRIDGE_FAILED_MANUAL_FALLBACK" `
                        -Message "Automatic ChatGPT bridge failed; switching to manual clipboard bridge. Error: $bridgeError"
                }
                catch {}

                Write-Host ""
                Write-Host "Automatic ChatGPT browser bridge failed." -ForegroundColor Yellow
                Write-Host "Switching to reliable manual clipboard mode." -ForegroundColor Yellow
                Write-Host ""

                return Invoke-ManualChatGPTBridge `
                    -Prompt $Prompt `
                    -ContextLabel $ContextLabel
            }

            Write-Host ""
            Write-Host "==========================================================" -ForegroundColor Yellow
            Write-Host " CHATGPT LOCAL BRIDGE UNAVAILABLE" -ForegroundColor Yellow
            Write-Host " CONTROLLER STOPPING FAIL-CLOSED" -ForegroundColor Yellow
            Write-Host "==========================================================" -ForegroundColor Yellow
            Write-Host "No AGY instruction will be replayed."
            Write-Host "No PBS job will be submitted or modified."
            Write-Host "Existing HPC jobs continue independently."
            Write-Host ""

            throw "ChatGPT bridge failed after $attempts attempts. Last error: $bridgeError"
        }
    }
}
'@

    $prefix = $lines[0..($startIdx - 1)]
    $suffix = $lines[($endIdx + 1)..($lines.Length - 1)]
    $lines = $prefix + @($newBridgeCode) + $suffix
} else {
    Write-Warning "Could not find boundaries for Invoke-ChatGPTBridgeWithManualFallback."
}

$newContent = $lines -join "`r`n"
[System.IO.File]::WriteAllText($targetFile, $newContent, [System.Text.UTF8Encoding]::new($false))
Write-Host "Bridge failclosed patch applied cleanly to $targetFile."
