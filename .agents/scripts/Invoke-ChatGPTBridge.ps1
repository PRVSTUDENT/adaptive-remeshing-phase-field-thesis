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
    Durable HND- correlation ID (CorrelationId is a compatibility alias). If omitted, extracted from the standalone header; never regenerated on retry.

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
    If specified, validates canonical policy and returns the assembled prompt without publishing or invoking PAD.
#>
function Invoke-ChatGPTBridge {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [string]$PromptText,

        [Alias("CorrelationId")]
        [string]$HandoffId,

        [string]$PadUrl,

        [string]$RulesPath,

        [switch]$LaunchPad = $false,

        [switch]$RequireHeartbeat = $false,

        [int]$TimeoutMinutes = 40,

        [string]$BridgeDir = (Join-Path $env:USERPROFILE "OpenClawPAD\ChatGPTBridge"),

        [switch]$DryRun = $false,

        [switch]$Resume = $false,

        [switch]$ForceResume = $false,

        [string]$TaskId = $null
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

    # Canonical policy applies to EVERY structured request; evidence is never rewritten.
    . (Join-Path $PSScriptRoot 'Bridge-ResearchContract.ps1')
    $bridgePacket = New-BridgeCanonicalPrompt -PromptText $PromptText -HandoffId $HandoffId -TaskId $TaskId -RulesPath $RulesPath
    $HandoffId = $bridgePacket.handoff_id
    $TaskId = $bridgePacket.task_id
    $assembledPrompt = $bridgePacket.text

            # Re-source Controller-Preparation to ensure running controller loop has latest plan logic
    $prepScriptCandidates = @(
        "D:\Master thesis\Adaptive remeshing\scripts\controller\Controller-Preparation.ps1",
        (Join-Path $PSScriptRoot "..\..\scripts\controller\Controller-Preparation.ps1")
    )
    foreach ($psc in $prepScriptCandidates) {
        if (Test-Path -LiteralPath $psc) {
            try { . $psc } catch {}
            break
        }
    }

    # --- 2d. External Authentication Blocker Guard ---
    $isBlocked = $false
    $ssoBlockerPatterns = 'INTERACTIVE_SSO_REQUIRED|BLOCKED_EXTERNAL_AUTHENTICATION|OFFLINE_QUALIFIED__INTERACTIVE_SSO_REQUIRED'

    # Check if prompt text explicitly indicates external authentication blocker
    if ($PromptText -match $ssoBlockerPatterns) {
        $isBlocked = $true
    }

    # Check active task and current state in project coordination if task matches or not specified
    if (-not $isBlocked) {
        $coordDirs = @(
            "D:\Master thesis\Adaptive remeshing\project_coordination",
            (Join-Path $PSScriptRoot "..\..\project_coordination"),
            (Join-Path (Split-Path $BridgeDir -Parent) "project_coordination")
        )
        foreach ($cd in $coordDirs) {
            $activeTaskFile = Join-Path $cd "ACTIVE_TASK.json"
            if (Test-Path -LiteralPath $activeTaskFile) {
                try {
                    $taskJson = Get-Content -LiteralPath $activeTaskFile -Raw -Encoding UTF8 | ConvertFrom-Json
                    $taskMatches = $true
                    if (-not [string]::IsNullOrWhiteSpace($TaskId)) {
                        $taskMatches = ($taskJson.task_id -eq $TaskId)
                    } elseif ($PromptText -notmatch [regex]::Escape($taskJson.task_id) -and -not [string]::IsNullOrWhiteSpace($taskJson.task_id)) {
                        # If TaskId is omitted and PromptText does not mention the active task or Mode-1/R18, do not block unrelated prompts
                        if ($PromptText -notmatch 'F1597|Package\s*108|Revision\s*18|R18') {
                            $taskMatches = $false
                        }
                    }

                    if ($taskMatches) {
                        $taskStateStr = "$($taskJson.phase) $($taskJson.status) $($taskJson.gate_status)"
                        if ($taskStateStr -match $ssoBlockerPatterns) {
                            $isBlocked = $true
                            break
                        }
                    }
                } catch {}
            }
        }
    }

    $isResumed = ($Resume -or $ForceResume -or ($env:RESUME_AFTER_SSO -eq '1'))

    if ($isBlocked -and -not $isResumed -and $PromptText -notmatch '(?m)^CHATGPT_SUPERVISOR_V1') {
        # Check if live authenticated network connectivity to the cluster is restored
        $networkRestored = $false
        try {
            $entry = [System.Net.Dns]::GetHostAddresses("mlogin01.hrz.tu-freiberg.de")
            if ($entry -and $entry.Count -gt 0) {
                $networkRestored = $true
            }
        } catch {
            $networkRestored = $false
        }

        if (-not $networkRestored) {
            $blockedNotice = @"
BLOCKED_EXTERNAL_AUTHENTICATION
Status: R18_OFFLINE_QUALIFIED__INTERACTIVE_SSO_REQUIRED
Package: models/pandey_kumar_mode1/108_r18_c3_donor_kinematics_active_set/
Checkpoint: results/validation/mode1_f1597/r18_donor_kinematics_audit.json
Action Required: User must connect university eduVPN on workstation and complete browser-based SSO login for TU Bergakademie Freiberg.
"@
            Write-Warning "[Bridge] External authentication blocker active: university eduVPN interactive browser SSO required."
            Write-Host "[Bridge] Suppressing outgoing bridge dispatch to prevent infinite orchestration loop." -ForegroundColor Yellow
            return $blockedNotice.Trim()
        }
    }

    # --- 2e. DryRun Mode ---
    if ($DryRun) {
        Write-Host "[Bridge] Dry-run requested. Prompt assembled successfully ($($assembledPrompt.Length) chars)." -ForegroundColor Cyan
        return $assembledPrompt
    }

    # --- 3. Lockfile Check & Acquisition ---
    # BRIDGE_OWNER_LOCK_V2: serialize acquisition; recover dead owners, never by age.
    $bridgeLockKey = [BitConverter]::ToString([Security.Cryptography.SHA256]::Create().ComputeHash(
        [Text.Encoding]::UTF8.GetBytes([IO.Path]::GetFullPath($BridgeDir).ToLowerInvariant()))).Replace('-', '')
    $bridgeMutex = [Threading.Mutex]::new($false, "Global\AdaptiveRemeshing.Bridge.$bridgeLockKey")
    $bridgeMutexHeld = $false
    $ownsLockFile = $false
    try {
        try { $bridgeMutexHeld = $bridgeMutex.WaitOne(0) }
        catch [Threading.AbandonedMutexException] { $bridgeMutexHeld = $true }
        if (-not $bridgeMutexHeld) { throw 'Bridge is locked by another running transaction (OS owner lock).' }
        if (Test-Path -LiteralPath $lockFile) {
            $existingLock = Get-Content -LiteralPath $lockFile -Raw -ErrorAction Stop
            try { $owner = $existingLock | ConvertFrom-Json -ErrorAction Stop }
            catch { throw 'Bridge lock metadata is invalid; preserving it for diagnosis.' }
            if (-not $owner.pid -or [int]$owner.pid -le 0) { throw 'Bridge lock has no valid owner PID; preserving evidence.' }
            $ownerProcess = Get-Process -Id ([int]$owner.pid) -ErrorAction SilentlyContinue
            if ($ownerProcess) {
                # PID reuse is only proven when exact recorded process start differs.
                $sameOwner = $true
                if ($owner.process_started_utc) {
                    $sameOwner = ($ownerProcess.StartTime.ToUniversalTime().ToString('o') -eq $owner.process_started_utc)
                }
                if ($sameOwner) { throw "Bridge is locked by live owner PID $($owner.pid); age does not override ownership." }
            }
            $staleTag = 'orphan_' + [guid]::NewGuid().ToString('N')
            foreach ($staleFile in @($lockFile, $requestReady, $requestTmp, $responseReady, $responseTmp)) {
                if (Test-Path -LiteralPath $staleFile) {
                    Move-Item -LiteralPath $staleFile -Destination (Join-Path $archiveDir ($staleTag + '_' + [IO.Path]::GetFileName($staleFile))) -ErrorAction Stop
                }
            }
            Write-Warning "Recovered orphaned bridge transaction from dead/reused PID $($owner.pid); evidence archived."
        }
        foreach ($pendingFile in @($requestReady,$requestTmp,$responseReady,$responseTmp)) {
            if (Test-Path -LiteralPath $pendingFile) { throw "BRIDGE_PENDING_RECONCILIATION_REQUIRED: $pendingFile" }
        }
        $lockContent = [ordered]@{
            bridge_handoff_id = $HandoffId
            locked_at = (Get-Date).ToString('o')
            pid = $PID
            process_started_utc = (Get-Process -Id $PID).StartTime.ToUniversalTime().ToString('o')
        } | ConvertTo-Json -Compress
        [IO.File]::WriteAllText($lockFile, $lockContent, [Text.UTF8Encoding]::new($false))
        $ownsLockFile = $true

        # --- 4. Clean Stale Handshake Files ---
        Remove-Item -LiteralPath $responseReady, $responseTmp, $requestReady, $requestTmp -Force -ErrorAction SilentlyContinue

        # --- 5. Atomic Plain-Text Request Creation ---
        $timestamp = (Get-Date).ToString("yyyyMMdd_HHmmss")
        $archRequest = Join-Path $archiveDir ("request_{0}_{1}.txt" -f $timestamp, $HandoffId)
        [System.IO.File]::WriteAllText($archRequest, $assembledPrompt, [System.Text.UTF8Encoding]::new($false))
        [System.IO.File]::WriteAllText($requestTmp, $assembledPrompt, [System.Text.UTF8Encoding]::new($false))
        $bridgePublishedAt = [DateTimeOffset]::UtcNow
        Move-Item -LiteralPath $requestTmp -Destination $requestReady -Force

        Write-Host "[Bridge] Plain-text request ready: $requestReady (Handoff ID: $HandoffId, size: $($assembledPrompt.Length) chars, archived: $archRequest)" -ForegroundColor Cyan

        # --- 6. Resolve PAD Trigger Mechanism & Heartbeat Check ---
        # BEGIN PAD_SINGLE_RUNTIME_GUARD
        if ($LaunchPad) {
            # Reuse the visible bridge loop; never start a second consumer.
            $padRobots = @(Get-CimInstance Win32_Process -Filter "Name='PAD.RobotV2.exe'" -ErrorAction Stop)
            if (@($padRobots | Where-Object { [string]::IsNullOrWhiteSpace($_.CommandLine) }).Count -gt 0) {
                throw 'PAD_RUNTIME_IDENTITY_UNRESOLVED: refusing another flow launch.'
            }
            $bridgeRobots = @($padRobots | Where-Object {
                $_.CommandLine -match '(?i)--flowId\s+"?ddf92fce-?748d-?4446-?83b5-?d406c4d0f782"?(?=\s|$)'
            })
            if ($bridgeRobots.Count -gt 1) {
                throw 'PAD_DUPLICATE_BRIDGE_RUNTIMES: reconcile existing consumers; no new launch.'
            }
            if ($bridgeRobots.Count -eq 1) {
                Write-Host "[Bridge] Reusing existing PAD bridge runtime PID $($bridgeRobots[0].ProcessId); launch suppressed." -ForegroundColor Cyan
                $LaunchPad = $false
            }
        }
        # END PAD_SINGLE_RUNTIME_GUARD
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
        $responseRaw = [System.IO.File]::ReadAllText($responseReady)
        $archResponse = Join-Path $archiveDir ("response_{0}_{1}.json" -f $timestamp, $HandoffId)
        [System.IO.File]::WriteAllText($archResponse, $responseRaw, [System.Text.UTF8Encoding]::new($false))

        # Fail closed; invalid responses stay archived and ready for reconciliation.
        $replyText = Read-BridgeValidatedReply -Raw $responseRaw -Packet $bridgePacket -PublishedAt $bridgePublishedAt

        # --- 9. Clean Handshake Files ---
        Remove-Item -LiteralPath $responseReady -Force -ErrorAction SilentlyContinue
        Remove-Item -LiteralPath $requestReady -Force -ErrorAction SilentlyContinue

        Write-Host "[Bridge] Transaction complete. Extracted $($replyText.Length) chars response." -ForegroundColor Green
        return $replyText
    }
    finally {
        # --- 10. Always Release Only Our Lock ---
        try {
            if ($ownsLockFile -and (Test-Path -LiteralPath $lockFile)) {
                Remove-Item -LiteralPath $lockFile -Force -ErrorAction Stop
            }
        } finally {
            if ($bridgeMutexHeld) { $bridgeMutex.ReleaseMutex() }
            $bridgeMutex.Dispose()
        }
    }
}
