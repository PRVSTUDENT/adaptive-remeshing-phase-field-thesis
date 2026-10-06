<#
.SYNOPSIS
    Dispatches a prompt across the Power Automate Desktop (PAD) ChatGPT Bridge.

.DESCRIPTION
    Architecture:
    1. Antigravity PowerShell:
       - Acquires bridge.lock.
       - Reconciles project alignment guard and appends bridge_rules.txt.
       - Writes complete plain-text prompt to bridge_request.tmp.
       - Renames bridge_request.tmp -> bridge_request.ready (atomic).
       - Triggers PAD via ms-powerautomate: run URL.
    2. Power Automate Desktop (PAD):
       - Reads bridge_request.ready as raw text.
       - Pastes into ChatGPT web UI and clicks Submit.
       - Monitors ChatGPT response via Tampermonkey userscript bridge:
         * Userscript extracts full assistant markdown response.
         * Writes response JSON to bridge_response.tmp.
         * Renames bridge_response.tmp -> bridge_response.ready (atomic).
    3. Antigravity PowerShell:
       - Polls for bridge_response.ready with timeout.
       - Reads response JSON, extracts markdown text.
       - Archives request and response to ChatGPTBridge/archive/.
       - Releases bridge.lock.
       - Returns response text to caller.

.PARAMETER PromptText
    The complete prompt text to send to ChatGPT.

.PARAMETER HandoffId
    Optional handoff ID. If omitted, extracted from PromptText or generated as HND-<12 hex>.

.PARAMETER PadUrl
    The Power Automate Desktop run URL. Defaults to env:PAD_CHATGPT_BRIDGE_URL
    or 'ms-powerautomate:/console/flow/run?workflowName=Antigravity_ChatGPT_Bridge'.

.PARAMETER RulesPath
    Optional path to bridge rules file. Defaults to .agents/scripts/bridge_rules.txt
    or OpenClawPAD/ChatGPTBridge/bridge_rules.txt.

.PARAMETER TimeoutMinutes
    Maximum wait time for response before timing out (default 40 minutes).

.PARAMETER BridgeDir
    Directory where bridge files reside (default C:\Users\<YOU>\OpenClawPAD\ChatGPTBridge).

.PARAMETER DryRun
    If specified, returns the assembled prompt without acquiring lock, writing files, or invoking PAD.
#>
function Invoke-ChatGPTBridge {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [string]$PromptText,

        [string]$HandoffId,

        [string]$PadUrl,

        [string]$RulesPath,

        [switch]$LaunchPad = $false,

        [switch]$RequireHeartbeat = $false,

        [int]$TimeoutMinutes = 40,

        [string]$BridgeDir = (Join-Path $env:USERPROFILE "OpenClawPAD\ChatGPTBridge"),

        [switch]$DryRun = $false
    )

    if (-not (Test-Path -LiteralPath $BridgeDir)) {
        New-Item -ItemType Directory -Path $BridgeDir -Force | Out-Null
    }

    $archiveDir = Join-Path $BridgeDir "archive"
    if (-not (Test-Path -LiteralPath $archiveDir)) {
        New-Item -ItemType Directory -Path $archiveDir -Force | Out-Null
    }

    $lockFile = Join-Path $BridgeDir "bridge.lock"
    $requestTmp = Join-Path $BridgeDir "bridge_request.tmp"
    $requestReady = Join-Path $BridgeDir "bridge_request.ready"
    $responseTmp = Join-Path $BridgeDir "bridge_response.tmp"
    $responseReady = Join-Path $BridgeDir "bridge_response.ready"

    # --- 1. Resolve Handoff ID & Ensure Header in Prompt ---
    if ([string]::IsNullOrWhiteSpace($HandoffId)) {
        $match = [regex]::Match($PromptText, '\[BRIDGE_HANDOFF_ID=([^\]]+)\]')
        if ($match.Success) {
            $HandoffId = $match.Groups[1].Value.Trim()
        } else {
            $HandoffId = "HND-" + ([guid]::NewGuid().ToString("N").Substring(0, 12))
            $PromptText = "[BRIDGE_HANDOFF_ID=$HandoffId]`n`n$PromptText"
        }
    } else {
        if (-not $PromptText.Contains("[BRIDGE_HANDOFF_ID=$HandoffId]")) {
            $PromptText = "[BRIDGE_HANDOFF_ID=$HandoffId]`n`n$PromptText"
        }
    }

    # --- 2a. Reconcile Project Alignment Guard with Authoritative Source ---
    $guardCandidates = @(
        "D:\Master thesis\Adaptive remeshing\.agents\scripts\project_alignment_guard.txt",
        (Join-Path $BridgeDir "..\project_alignment_guard.txt"),
        (Join-Path (Split-Path $BridgeDir -Parent) "project_alignment_guard.txt")
    )
    $authoritativeGuard = $null
    foreach ($gc in $guardCandidates) {
        if (Test-Path -LiteralPath $gc) {
            try {
                $gcText = [System.IO.File]::ReadAllText($gc, [System.Text.UTF8Encoding]::new($false)).Trim()
                if (-not [string]::IsNullOrWhiteSpace($gcText)) {
                    $authoritativeGuard = $gcText
                    break
                }
            } catch {}
        }
    }

    if ($authoritativeGuard) {
        $script:ProjectAlignmentGuard = $authoritativeGuard
        $global:ProjectAlignmentGuard = $authoritativeGuard

        $guardStart = "---------------- PROJECT / THESIS ALIGNMENT GUARD ----------------"
        $guardEnd = "-------------- END PROJECT / THESIS ALIGNMENT GUARD --------------"
        if ($PromptText.Contains($guardStart) -and $PromptText.Contains($guardEnd)) {
            $pStart = $PromptText.IndexOf($guardStart)
            $pEnd = $PromptText.IndexOf($guardEnd) + $guardEnd.Length
            $beforeGuard = $PromptText.Substring(0, $pStart)
            $afterGuard = $PromptText.Substring($pEnd)
            $PromptText = $beforeGuard + $guardStart + "`r`n" + $authoritativeGuard + "`r`n" + $guardEnd + $afterGuard
        }
    }

    # --- 2b. Append Bridge Rules (Separation of Concerns) ---
    if ([string]::IsNullOrWhiteSpace($RulesPath)) {
        $ruleCandidates = @(
            "D:\Master thesis\Adaptive remeshing\.agents\scripts\bridge_rules.txt",
            (Join-Path $BridgeDir "bridge_rules.txt")
        )
        foreach ($rc in $ruleCandidates) {
            if (Test-Path -LiteralPath $rc) {
                $RulesPath = $rc
                break
            }
        }
    }

    $assembledPrompt = $PromptText
    if ($RulesPath -and (Test-Path -LiteralPath $RulesPath)) {
        $rulesContent = [System.IO.File]::ReadAllText($RulesPath, [System.Text.UTF8Encoding]::new($false)).Trim()
        if (-not [string]::IsNullOrWhiteSpace($rulesContent)) {
            $rHeader = "---------------- BRIDGE CONTROLLER RULES ----------------"
            $rFooter = "---------------- END BRIDGE CONTROLLER RULES ----------------"
            if ($assembledPrompt.Contains($rHeader)) {
                $rStart = $assembledPrompt.IndexOf($rHeader)
                $rEnd = $assembledPrompt.IndexOf($rFooter) + $rFooter.Length
                $beforeRules = $assembledPrompt.Substring(0, $rStart)
                $afterRules = $assembledPrompt.Substring($rEnd)
                $assembledPrompt = $beforeRules + $rHeader + "`r`n" + $rulesContent + "`r`n" + $rFooter + $afterRules
            } else {
                $assembledPrompt = @"
$PromptText

$rHeader
$rulesContent
$rFooter

Determine the next instruction to send to Antigravity.
"@
            }
        }
    }

    # --- 2c. Sanity Guard: Verify and sanitize any superseded strings ---
    $stalePatterns = @(
        "01 October 2026",
        "01-Oct-2026",
        "01-Oct",
        "UEL_ENERGY_OUTPUT_NOT_YET_QUALIFIED",
        "MODE1_ENERGY_CONVERGENCE_AND_STATE_TRANSFER_FOUNDATIONS_ACTIVE",
        "MODE1_GATE6B_STEP2_ACTIVE_EVALUATION_AND_CONTINUATION",
        "STEP2_ACTIVE_EVALUATION_AND_CONTINUATION"
    )
    foreach ($sp in $stalePatterns) {
        if ($assembledPrompt.Contains($sp)) {
            Write-Warning "Detected superseded string '$sp' in bridge prompt. Sanitizing to authoritative Gate-6B state..."
            if ($sp -eq "01 October 2026" -or $sp -eq "01-Oct-2026" -or $sp -eq "01-Oct") {
                $assembledPrompt = $assembledPrompt -replace [regex]::Escape($sp), "Thursday, 08 October 2026, 10:00 CEST"
            }
            if ($sp -eq "UEL_ENERGY_OUTPUT_NOT_YET_QUALIFIED") {
                $assembledPrompt = $assembledPrompt -replace [regex]::Escape($sp), "UEL_ENERGY_OUTPUT_QUALIFIED_MECHANICALLY_NONINVASIVE"
            }
            if ($sp -eq "MODE1_ENERGY_CONVERGENCE_AND_STATE_TRANSFER_FOUNDATIONS_ACTIVE" -or $sp -eq "MODE1_GATE6B_STEP2_ACTIVE_EVALUATION_AND_CONTINUATION" -or $sp -eq "STEP2_ACTIVE_EVALUATION_AND_CONTINUATION") {
                $assembledPrompt = $assembledPrompt -replace [regex]::Escape($sp), "MODE1_GATE6B_ACTIVE_EVALUATION_AND_CONTINUATION"
            }
        }
    }

    # Clean any outdated "Priority 1 is UEL Energy Formulation and Output Audit (offline..." string
    $staleAuditPhrase = "Priority 1 is UEL Energy Formulation and Output Audit (offline derivation, source audit, energy balance formulation, non-invasive code design, report updates)."
    if ($assembledPrompt.Contains($staleAuditPhrase)) {
        $assembledPrompt = $assembledPrompt.Replace($staleAuditPhrase, "Priority 1 is UEL Energy Formulation and Output: Status is UEL_ENERGY_OUTPUT_QUALIFIED_MECHANICALLY_NONINVASIVE.")
    }

    
    # Clean any outdated candidate phrasing for Job 1410179
    $staleCandidatePhrases = @(
        "serial Job 1410179 diagnostic and 8T SMP Job 1410504 candidate",
        "serial Job 1410179.mmaster02 and 8-thread SMP Job 1410504.mmaster02",
        "serial Job 1410179.mmaster02 partial diagnostic and 8-thread SMP Job 1410504.mmaster02 candidate"
    )
    foreach ($scp in $staleCandidatePhrases) {
        if ($assembledPrompt.Contains($scp)) {
            $assembledPrompt = $assembledPrompt.Replace($scp, "serial Job 1410179.mmaster02 terminal partial diagnostic evidence and 8-thread SMP Job 1410504.mmaster02 active full-horizon candidate")
        }
    }

    # --- 2d. DryRun Mode ---
    if ($DryRun) {
        Write-Host "[Bridge] Dry-run requested. Prompt assembled successfully ($($assembledPrompt.Length) chars)." -ForegroundColor Cyan
        return $assembledPrompt
    }

    # --- 3. Lockfile Check & Acquisition ---
    if (Test-Path -LiteralPath $lockFile) {
        $lockAge = (Get-Date) - (Get-Item -LiteralPath $lockFile).LastWriteTime
        if ($lockAge.TotalMinutes -gt 60) {
            Write-Warning "Removing stale bridge lock ($([math]::Round($lockAge.TotalMinutes)) minutes old)."
            Remove-Item -LiteralPath $lockFile -Force -ErrorAction SilentlyContinue
        } else {
            $existingLock = Get-Content -LiteralPath $lockFile -Raw -ErrorAction SilentlyContinue
            throw "Bridge is locked by another running transaction (bridge.lock exists). Content: $existingLock"
        }
    }

    $lockContent = [ordered]@{
        bridge_handoff_id = $HandoffId
        locked_at         = (Get-Date).ToString("o")
        pid               = $PID
    } | ConvertTo-Json -Compress

    [System.IO.File]::WriteAllText($lockFile, $lockContent, [System.Text.UTF8Encoding]::new($false))

    try {
        # --- 4. Clean Stale Handshake Files ---
        Remove-Item -LiteralPath $responseReady, $responseTmp, $requestReady, $requestTmp -Force -ErrorAction SilentlyContinue

        # --- 5. Atomic Plain-Text Request Creation ---
        $timestamp = (Get-Date).ToString("yyyyMMdd_HHmmss")
        $archRequest = Join-Path $archiveDir ("request_{0}_{1}.txt" -f $timestamp, $HandoffId)
        [System.IO.File]::WriteAllText($archRequest, $assembledPrompt, [System.Text.UTF8Encoding]::new($false))
        [System.IO.File]::WriteAllText($requestTmp, $assembledPrompt, [System.Text.UTF8Encoding]::new($false))
        Move-Item -LiteralPath $requestTmp -Destination $requestReady -Force

        Write-Host "[Bridge] Plain-text request ready: $requestReady (Handoff ID: $HandoffId, size: $($assembledPrompt.Length) chars, archived: $archRequest)" -ForegroundColor Cyan

        # --- 6. Resolve PAD Trigger Mechanism & Heartbeat Check ---
        if ($LaunchPad) {
            $padShortcut = "C:\Users\pruth\Desktop\Antigravity_ChatGPT_Bridge - Power Automate.url"
            if (Test-Path -LiteralPath $padShortcut) {
                Write-Host "[Bridge] Launching PAD flow via desktop shortcut: $padShortcut" -ForegroundColor Cyan
                Start-Process -FilePath $padShortcut
            } else {
                if ([string]::IsNullOrWhiteSpace($PadUrl)) {
                    $PadUrl = $env:PAD_CHATGPT_BRIDGE_URL
                    if ([string]::IsNullOrWhiteSpace($PadUrl)) {
                        $PadUrl = "ms-powerautomate:/console/flow/run?workflowName=Antigravity_ChatGPT_Bridge"
                    }
                }
                Write-Host "[Bridge] Launching PAD flow via protocol URL: $PadUrl" -ForegroundColor Cyan
                Start-Process $PadUrl
            }
        }

        # --- 7. Poll for Response ---
        $timeoutSeconds = $TimeoutMinutes * 60
        $pollIntervalSeconds = 2
        $elapsed = 0
        $spinChars = @('|', '/', '-', '\')
        $spinIdx = 0

        Write-Host "[Bridge] Polling for response at $responseReady (Timeout: $TimeoutMinutes mins)..." -ForegroundColor Yellow

        while ($elapsed -lt $timeoutSeconds) {
            Start-Sleep -Seconds $pollIntervalSeconds
            $elapsed += $pollIntervalSeconds

            $spin = $spinChars[$spinIdx % 4]
            $spinIdx++
            Write-Host -NoNewline "`r[Bridge] Waiting for ChatGPT via PAD $spin ($elapsed / $timeoutSeconds s)"

            if (Test-Path -LiteralPath $responseReady) {
                Write-Host "`n[Bridge] Response detected after ${elapsed}s!" -ForegroundColor Green
                break
            }
        }

        if (-not (Test-Path -LiteralPath $responseReady)) {
            throw "Bridge timeout reached (${TimeoutMinutes}m) without response from ChatGPT."
        }

        # --- 8. Read and Parse Response JSON ---
        $responseRaw = [System.IO.File]::ReadAllText($responseReady, [System.Text.UTF8Encoding]::new($false))
        $archResponse = Join-Path $archiveDir ("response_{0}_{1}.json" -f $timestamp, $HandoffId)
        [System.IO.File]::WriteAllText($archResponse, $responseRaw, [System.Text.UTF8Encoding]::new($false))

        $responseObj = $responseRaw | ConvertFrom-Json
        $replyText = $responseObj.response

        # --- 9. Clean Handshake Files ---
        Remove-Item -LiteralPath $responseReady -Force -ErrorAction SilentlyContinue
        Remove-Item -LiteralPath $requestReady -Force -ErrorAction SilentlyContinue

        Write-Host "[Bridge] Transaction complete. Extracted $($replyText.Length) chars response." -ForegroundColor Green
        return $replyText
    }
    finally {
        # --- 10. Always Release Lock ---
        if (Test-Path -LiteralPath $lockFile) {
            Remove-Item -LiteralPath $lockFile -Force -ErrorAction SilentlyContinue
        }
    }
}
