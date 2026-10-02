# Apply fail-closed quota exit logic to Sections 1, 2, and 3
$targetFile = "C:\Users\pruth\OpenClawPAD\Antigravity-Autonomous-Loop.ps1"
$lines = [System.IO.File]::ReadAllLines($targetFile, [System.Text.UTF8Encoding]::new($false))

# Section 1: Insert guard right before "if ($attempts -lt $AgyProfileRotationOrder.Count)" under "if ($isQuotaError)"
for ($i = 0; $i -lt $lines.Length; $i++) {
    if ($lines[$i] -match 'if \(\$isQuotaError\)' -and $i -lt 1600) {
        Write-Host "Found Section 1 if (`$isQuotaError) at line $($i + 1)"
        $guardCode = @'
            if (-not $EnableAutomaticAgyProfileRotation) {
                Write-Host ""
                Write-Host "==========================================================" -ForegroundColor Yellow
                Write-Host " ANTIGRAVITY ACCOUNT QUOTA/RATE LIMIT REACHED" -ForegroundColor Yellow
                Write-Host " AUTOMATIC PROFILE SWITCHING IS DISABLED" -ForegroundColor Yellow
                Write-Host "==========================================================" -ForegroundColor Yellow
                Write-Host ""
                Write-Host "The controller will stop without changing the AGY profile."
                Write-Host ""
                Write-Host "Switch manually, for example:"
                Write-Host "  agy-profile list"
                Write-Host "  agy-profile switch account2"
                Write-Host "  agy-profile current"
                Write-Host ""
                Write-Host "Then restart the autonomous controller."
                Write-Host ""

                Save-LoopStatus `
                    -Turn $CurrentTurn `
                    -Status "STOPPED_QUOTA" `
                    -Tier "CONTROLLER" `
                    -Action "AGY_QUOTA_EXHAUSTED_MANUAL_REQUIRED" `
                    -Details "Antigravity account quota reached. Automatic rotation is disabled. Switch profile manually and restart."

                break MainLoop
            }
'@
        $lines[$i] = "$($lines[$i])`r`n$guardCode"
        break
    }
}

# Section 2: Insert guard right after "if ($isQuotaError) {" in status parsing (around line 1860)
for ($i = 1800; $i -lt [Math]::Min($lines.Length, 2000); $i++) {
    if ($lines[$i] -match 'if \(\$isQuotaError\)') {
        Write-Host "Found Section 2 if (`$isQuotaError) at line $($i + 1)"
        $guardCode = @'
                if (-not $EnableAutomaticAgyProfileRotation) {
                    Write-Host ""
                    Write-Host "==========================================================" -ForegroundColor Yellow
                    Write-Host " ANTIGRAVITY ACCOUNT QUOTA/RATE LIMIT REACHED" -ForegroundColor Yellow
                    Write-Host " AUTOMATIC PROFILE SWITCHING IS DISABLED" -ForegroundColor Yellow
                    Write-Host "==========================================================" -ForegroundColor Yellow
                    Write-Host ""
                    Write-Host "The controller will stop without changing the AGY profile."
                    Write-Host ""
                    Write-Host "Switch manually, for example:"
                    Write-Host "  agy-profile list"
                    Write-Host "  agy-profile switch account2"
                    Write-Host "  agy-profile current"
                    Write-Host ""
                    Write-Host "Then restart the autonomous controller."
                    Write-Host ""

                    Save-LoopStatus `
                        -Turn $CurrentTurn `
                        -Status "STOPPED_QUOTA" `
                        -Tier "CONTROLLER" `
                        -Action "AGY_STATUS_QUOTA_EXHAUSTED_MANUAL_REQUIRED" `
                        -Details "Antigravity status error indicated quota exhaustion. Automatic rotation is disabled. Switch profile manually and restart."

                    break MainLoop
                }
'@
        $lines[$i] = "$($lines[$i])`r`n$guardCode"
        break
    }
}

# Section 3: Insert guard under quota below threshold (around line 2440)
for ($i = 2400; $i -lt [Math]::Min($lines.Length, 2550); $i++) {
    if ($lines[$i] -match '\[bool\]\$quotaSnapshot\.below_threshold') {
        # find the opening brace for this if block
        for ($j = $i; $j -lt $i + 10; $j++) {
            if ($lines[$j] -match '\{\s*$') {
                Write-Host "Found Section 3 opening brace at line $($j + 1)"
                $guardCode = @'
            if (-not $EnableAutomaticAgyProfileRotation) {
                Write-Host ""
                Write-Host "==========================================================" -ForegroundColor Yellow
                Write-Host " ANTIGRAVITY 5H QUOTA BELOW THRESHOLD" -ForegroundColor Yellow
                Write-Host " AUTOMATIC PROFILE SWITCHING IS DISABLED" -ForegroundColor Yellow
                Write-Host "==========================================================" -ForegroundColor Yellow
                Write-Host ""
                Write-Host "The controller will stop without changing the AGY profile."
                Write-Host ""
                Write-Host "Switch manually, for example:"
                Write-Host "  agy-profile list"
                Write-Host "  agy-profile switch account2"
                Write-Host "  agy-profile current"
                Write-Host ""
                Write-Host "Then restart the autonomous controller."
                Write-Host ""

                Save-LoopStatus `
                    -Turn $CurrentTurn `
                    -Status "STOPPED_QUOTA_LOW" `
                    -Tier "CONTROLLER" `
                    -Action "QUOTA_LOW_MANUAL_SWITCH_REQUIRED" `
                    -Details "5h quota fell below threshold. Automatic rotation is disabled. Switch profile manually and restart."

                break MainLoop
            }
'@
                $lines[$j] = "$($lines[$j])`r`n$guardCode"
                break
            }
        }
        break
    }
}

$newContent = $lines -join "`r`n"
[System.IO.File]::WriteAllText($targetFile, $newContent, [System.Text.UTF8Encoding]::new($false))
Write-Host "Sections 1, 2, and 3 patched successfully in $targetFile."
