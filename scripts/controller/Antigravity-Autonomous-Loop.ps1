[CmdletBinding()]
param(
    [string]$ConversationId = "",
    [string]$WorkspaceDir   = "D:\Master thesis\Adaptive remeshing",
    [string]$AgyPath        = "C:\Users\pruth\AppData\Local\agy\bin\agy.exe",
    [string]$Model          = "gemini-3.8-flash-high",
    [string]$InitialPrompt  = "",
    [string]$InitialPromptFile = "",
    [int]$MaxTurns          = 50,
    [string]$PrintTimeout   = "10000s",
    [ValidateRange(60,86400)][int]$ScientificTurnSeconds = 2400,

    # AGY_QUOTA_GUARD_V1
    # 1 = check after every actual AGY turn.
    # 10 = check after every tenth actual AGY turn.
    # 0 = disable scheduled quota checks.
    [int]$QuotaCheckEveryTurns = 1,

    # Rotate/stop at or below this remaining 5-hour quota percentage.
    [double]$QuotaStopThresholdPct = 20.0,

    # Conservative default: evaluate all Antigravity 5-hour groups and use
    # the minimum remaining percentage. Example alternative:
    #   "Gemini Models"
    [string]$QuotaGroupRegex = ".*",

    # Machine-readable quota checker. Install with:
    #   uv tool install ai-limit-checker
    # or:
    #   py -m pip install --upgrade ai-limit-checker
    [string]$QuotaCheckerCommand = "aichecker",
    [string[]]$QuotaCheckerBaseArgs = @(),

    # The controller rewrites this only when a quota handoff is required.
    [string]$QuotaInitialPromptFile = "D:\Master thesis\Adaptive remeshing\.agents\INITIAL_PROMPT.txt",

    # Unknown quota-query failures still fail closed.
    # A persistent Antigravity OAuth 401 is treated specially below because
    # AGY itself remains authoritative and operational.
    [switch]$QuotaCheckFailClosed = $true,

    # Retry transient quota checker failures before classifying them.
    [int]$QuotaRetryCount = 2,
    [int]$QuotaRetryDelaySeconds = 2,

    # ai-limit-checker currently returns persistent OAuth HTTP 401 while agy
    # itself remains authenticated. Do not stop solely for that known telemetry
    # failure. Real AGY quota/rate-limit errors remain hard rotation signals.
    [switch]$ContinueWhenQuotaTelemetryAuthFails = $true,

    # Automatically rotate accounts when a VALID quota snapshot is below the
    # configured threshold.
    [bool]$AutoRotateAgyProfileOnLowQuota = $false,

    # Automatically rotate when AGY itself reports an actual quota/rate limit.
    [bool]$AutoRotateAgyProfileOnAgyQuotaError = $false,

    # Deterministic account order.
    [string[]]$AgyProfileRotationOrder = @(
        "account1",
        "account2",
        "account3",
        "account4",
        "account5"
    ),

        # Authoritative tracked active production PBS job ID (exact format: <integer>.mmaster02)
        # The human controls Antigravity account/profile selection manually.
    # The autonomous controller must NEVER automatically switch profiles.
        [bool]$EnableAutomaticAgyProfileRotation = $false,

    # Quota-prioritized selection is enabled by default at startup and on quota trouble.
    # Five-day/weekly reset timestamp is the first priority; >=20% 5-hour
    # headroom is mandatory. Unknown quota telemetry NEVER implies spare quota.
    [bool]$EnableSmartAgyProfileSelection = $true,
    [double]$SmartMinLongRemainingPct = 20.0,
    [string]$SmartQuotaGroupRegex = "",

    # Authoritative manual AGY profile. Explicit caller selection always wins.
    [ValidatePattern('^account[1-5]$')]
    [string]$AuthoritativeAgyProfile = '',

    # ============================================================
    # CHATGPT LOCAL BRIDGE POLICY
    # ============================================================
    # Enable external ChatGPT review between turns.
    # When $true, every substantive turn is sent to ChatGPT for review
    # and next-step instruction generation.
    [bool]$EnableChatGPTBridge = $true,

    # HTTP bridge timeout is NOT the PBS scheduler wait.
    # Keep this short so a broken localhost bridge does not block
    # the autonomous workflow for 30 minutes.
    [int]$ChatGPTBridgeTimeoutSeconds = 1800,

    # Retry exactly the same handoff once if localhost delivery fails.
    [int]$ChatGPTBridgeMaxAttempts = 2,

    # Fallback to manual clipboard mode when automatic bridge fails.
    [bool]$EnableManualClipboardFallback = $false,

    # Scientific execution must fail closed rather than bypass ChatGPT
    # when ChatGPT bridge mode is active.
    [bool]$ContinueOnChatGPTBridgeFailure = $false,

    # Launch Power Automate Desktop via shortcut/URL per turn (set $false if PAD runs persistent worker loop)
    [bool]$ChatGPTBridgeLaunchPad = $false,

    # Fail quickly if PAD bridge worker heartbeat is missing or stale (>120s)
    [bool]$ChatGPTBridgeRequireHeartbeat = $false,

    [string]$ActiveProductionJobId = "",

    # HUMAN DIRECTIVE 2026-09-10: the supervisor-ready Gates 0-6 package is a
    # frozen baseline, not the end of Mode-I research. Keep the post-handoff
    # Mode-I resolution extension active by default until the two unresolved
    # Mode-I questions are actually resolved or the human explicitly disables it.
    [bool]$ModeIResolutionExtensionActive = $true,

    [ValidateRange(30,600)][int]$NoProgressSeconds = 300,
    [switch]$ControlledSingleTurn,
    [switch]$ControllerDryRun,
    [switch]$AllowSkipPermissions = $true
)

if($ControlledSingleTurn -and $MaxTurns -ne 1){throw 'ControlledSingleTurn requires MaxTurns=1; no research loop allowed'}
# Offline validation exits before credential/profile/bridge or AGY side effects.
. (Join-Path $WorkspaceDir 'scripts/controller/Controller-Recovery.ps1')
. (Join-Path $WorkspaceDir 'scripts/controller/Controller-Preparation.ps1')
$canonicalController = Join-Path $WorkspaceDir 'scripts/controller/Antigravity-Autonomous-Loop.ps1'
if ((Get-FileHash -LiteralPath $PSCommandPath).Hash -ne (Get-FileHash -LiteralPath $canonicalController).Hash) { throw 'Installed controller differs from canonical tested source; redeploy.' }
$controllerCheckpointPath = Join-Path $env:USERPROFILE 'OpenClawPAD/controller_turn_checkpoint.json'
if ($ControllerDryRun) {
    $prompt = if ($InitialPromptFile) { Get-Content -LiteralPath $InitialPromptFile -Raw -Encoding UTF8 } else { $InitialPrompt }
    $preparation=Get-ControllerPreparationPlan $WorkspaceDir $prompt
    if(-not $preparation.dispatch_ready){
        $checkpoint=Read-ControllerCheckpoint $controllerCheckpointPath
        Assert-ControllerDispatchCheckpoint $WorkspaceDir $checkpoint
        $budget=Get-ControllerBudget $PrintTimeout $ScientificTurnSeconds
        [pscustomobject]@{mode='DRY_RUN_NO_EXECUTION';task=(Get-ControllerEvidence $WorkspaceDir).task.task_id;proposed_operation=$preparation.operation_id;scientific_operation=$preparation.path;dispatch_ready=$false;preparation_status=$preparation.status;blocked_on=$preparation.blocked_on;checkpoint_state=$checkpoint.state;active_session=(Get-ControllerEvidence $WorkspaceDir).session.active;budget=$budget;no_progress_seconds=$NoProgressSeconds;source_sha256=(Get-FileHash -LiteralPath $PSCommandPath).Hash}|ConvertTo-Json -Depth 8
        return
    }
    $resolved = Resolve-ControllerInstruction $WorkspaceDir $prompt
    $checkpoint = Read-ControllerCheckpoint $controllerCheckpointPath
    Assert-ControllerDispatchCheckpoint $WorkspaceDir $checkpoint
    $operation=if($resolved.evidence.task.scientific_checkpoint_required){Resolve-ControllerOperation $resolved.evidence.task}else{$null}
    $budget = Get-ControllerBudget $PrintTimeout $ScientificTurnSeconds
    [pscustomobject]@{mode='DRY_RUN_NO_EXECUTION'; scientific_operation=$operation.path; operation_id=$operation.id; checkpoint_reconciliation=$checkpoint.reconciliation.status; task=$resolved.evidence.task.task_id; predecessor_status=$resolved.evidence.task.status; stale_prompt_replaced=$resolved.stale_replaced; active_session=$resolved.evidence.session.active; checkpoint_state=$(if($checkpoint){$checkpoint.state}else{'NONE'}); budget=$budget; no_progress_seconds=$NoProgressSeconds; progress_policy='saved report or PBS/execution evidence; metadata and tokens excluded'; source_sha256=(Get-FileHash -LiteralPath $PSCommandPath).Hash; instruction=$resolved.instruction} | ConvertTo-Json -Depth 8
    return
}

Assert-ControllerDispatchCheckpoint $WorkspaceDir (Read-ControllerCheckpoint $controllerCheckpointPath)
$preparationPrompt=if($InitialPromptFile){Get-Content -LiteralPath $InitialPromptFile -Raw -Encoding UTF8}else{$InitialPrompt}
$preparation=Invoke-ControllerOperationPreparation $WorkspaceDir $preparationPrompt
if(-not $preparation.dispatch_ready){
    Write-Output ('NEXT_OPERATION_PREPARATION: '+($preparation|ConvertTo-Json -Depth 8 -Compress))
    return # No profile selection, model call, timeout retry or completed-operation replay.
}
$preflightCheckpoint = Read-ControllerCheckpoint $controllerCheckpointPath
Assert-ControllerDispatchCheckpoint $WorkspaceDir $preflightCheckpoint
$preflightEvidence = Get-ControllerEvidence $WorkspaceDir
if ($preflightEvidence.session.active) {
    $ownedInterrupted = $null -ne $preflightCheckpoint -and $preflightCheckpoint.state -in @('RUNNING','CHECKPOINTED')
    if($ownedInterrupted){try{Sync-ControllerOwnedSession $preflightEvidence $preflightCheckpoint}catch{$ownedInterrupted=$false}}
    if (-not $ownedInterrupted) { throw 'BLOCKED: repository session active; no profile selection or AGY execution' }
}
if ($null -ne $preflightCheckpoint -and $preflightCheckpoint.state -in @('RUNNING','CHECKPOINTED') -and $preflightCheckpoint.process_id -and (Get-Process -Id $preflightCheckpoint.process_id -ErrorAction SilentlyContinue)) { throw 'BLOCKED: interrupted owned CLI process still exists; no duplicate execution' }

Write-Host " DEBUG PROFILE PARAMETER"
Write-Host " Raw parameter value: '$AuthoritativeAgyProfile'"
Write-Host " Was explicitly bound: $($PSBoundParameters.ContainsKey('AuthoritativeAgyProfile'))"

# AGY_SINGLE_INSTANCE_V1
$controllerSid = [System.Security.Principal.WindowsIdentity]::GetCurrent().User.Value
$controllerMutex = [System.Threading.Mutex]::new($false, ("Global\AdaptiveRemeshing.AgyController." + $controllerSid))
$controllerLockHeld = $false
try {
    try { $controllerLockHeld = $controllerMutex.WaitOne(0) }
    catch [System.Threading.AbandonedMutexException] { $controllerLockHeld = $true }
    if (-not $controllerLockHeld) {
        throw 'Another Antigravity controller is already running for this Windows user. This invocation stopped before profile selection or AGY execution. Close the existing controller before starting another.'
    }
. (Join-Path $WorkspaceDir 'scripts/validation/AgyControllerPolicy.ps1')
. (Join-Path $WorkspaceDir 'scripts/validation/AgyCredentialStores.ps1')
$script:RequestedAgyProfile = $AuthoritativeAgyProfile
if ($EnableSmartAgyProfileSelection) {
    $EnableAutomaticAgyProfileRotation = $true
    $AutoRotateAgyProfileOnLowQuota = $true
    $AutoRotateAgyProfileOnAgyQuotaError = $true
    if ([string]::IsNullOrWhiteSpace($SmartQuotaGroupRegex)) {
        $SmartQuotaGroupRegex = if ($Model -match '(?i)gemini') { '(?i)^Gemini Models$' } else { '(?i)Claude.*GPT' }
    }
    if ($QuotaCheckEveryTurns -le 0) { throw 'Smart quota selection requires QuotaCheckEveryTurns >= 1.' }
    # A 401 or unknown quota cannot be considered usable capacity in smart mode.
    $ContinueWhenQuotaTelemetryAuthFails = $false
    # The existing per-turn low-quota check must use the SAME model family
    # as the smart account selector, not an unrelated family's minimum.
    if ($QuotaGroupRegex -eq '.*') { $QuotaGroupRegex = $SmartQuotaGroupRegex }
}

if (Test-Path "C:\Program Files\Git\usr\bin") {
    if ($env:PATH -notlike "*C:\Program Files\Git\usr\bin*") {
        $env:PATH = "C:\Program Files\Git\usr\bin;$env:PATH"
    }
}
$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$OutputEncoding = [System.Text.UTF8Encoding]::new($false)

# Do NOT override the built-in Join-Path globally.

function Join-PathStrict {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $false)]
        [string]$Path,

        [Parameter(Mandatory = $false)]
        [string]$ChildPath
    )

    if ([string]::IsNullOrWhiteSpace($Path)) {
        throw "Join-PathStrict: Path is null or whitespace."
    }

    if ([string]::IsNullOrWhiteSpace($ChildPath)) {
        throw "Join-PathStrict: ChildPath is null or whitespace."
    }

    Microsoft.PowerShell.Management\Join-Path `
        -Path $Path `
        -ChildPath $ChildPath
}
$PadDir = "$env:USERPROFILE\OpenClawPAD"
if (-not (Test-Path $PadDir)) { New-Item -ItemType Directory -Path $PadDir -Force | Out-Null }

$LogFile       = Join-PathStrict -Path $PadDir -ChildPath "controller_activity.log"
$StatusFile    = Join-PathStrict -Path $PadDir -ChildPath "controller_latest_status.json"
$StateFile     = Join-PathStrict -Path $PadDir -ChildPath "antigravity_loop_state.json"
$SelectionFile = Join-PathStrict -Path $PadDir -ChildPath "agy_selected_profile.json"
$GovernanceFile = Join-PathStrict -Path $PadDir -ChildPath "controller_governance_state.json"

# ==============================================================================
# LIVE MODE-I FUNDAMENTALS GOVERNANCE STATE (POST-17-SEPTEMBER-2026 SUPERVISOR MEETING)
# ==============================================================================
$script:ModeIReproductionStatus = "CLOSED_WITH_SUPERVISOR_ACCEPTED_PUBLICATION_LIMITATION"
$script:ModeIFundamentalsStatus = "ACTIVE"

$script:EnergyFormulationAuditActionable = $true
$script:EnergyBaselineQualified = $false

$script:SpatialTemporalConvergenceActionable = $true
$script:SpatialTemporalConvergenceQualified = $false

$script:ModeIStateTransferStatus = "BLOCKED_UNTIL_ENERGY_BASELINE_QUALIFIED"
$script:ModeIStateTransferActionable = $false
$script:ModeIStateTransferQualified = $false

$script:Gate7VisualizationOnHold = $true
$script:ModeIIHigherComplexityOnHold = $true

$script:ReportUpdateRequired = $true
$script:NextSupervisorMeeting = "2026-10-01T10:00:00+02:00"

$script:AuthorInquiryStatus = "NOT_REQUIRED_SUPERVISOR_ACCEPTED_PUBLICATION_LIMITATION"
$script:ModeIFundamentalsComplete = $false
$script:MODE1_FUNDAMENTALS_COMPLETE = $false

# Retained compatibility fields (must NOT drive live stop/restart logic)
$script:PriorityQuestionA = "RESOLVED_AND_CLOSED"
$script:QuestionAVerifiedCause = "Abaqus keyword/NSET formatting allowed only 16 entries on the malformed data line; the remaining 134 of 150 intended N_BOTTOM nodes were not included in the parsed set. Wrapped across valid data lines."
$script:QuestionACorrectedEvidence = @("1405044.mmaster02", "1404933.mmaster02")
$script:QuestionAActionable = $false

$script:PriorityQuestionB = "SUPERVISOR_ACCEPTED_REPRODUCTION_LIMITATION_CLOSED"
$script:QuestionBVerifiedStatus = "supervisor explicitly accepted reproduction limitation; reproduction of general trends sufficient; additional unpublished discovery not justified"
$script:QuestionBActionable = $false

$script:PremeetingEvidenceFrozen = $false
$script:PBSActive = 0
$script:Gate7_ModeII_StateTransfer_OnHold = $true
$script:ModeIResolutionExtensionComplete = $false

function Get-ModeIFundamentalsActionable {
    return (
        $script:EnergyFormulationAuditActionable -or
        $script:SpatialTemporalConvergenceActionable -or
        $script:ModeIStateTransferActionable -or
        $script:ReportUpdateRequired
    )
}

function Sync-ControllerGovernanceState {
    if (Test-Path -LiteralPath $GovernanceFile) {
        try {
            $gov = Get-Content -LiteralPath $GovernanceFile -Raw | ConvertFrom-Json
            if ($null -ne $gov.ModeIReproductionStatus) { $script:ModeIReproductionStatus = [string]$gov.ModeIReproductionStatus }
            if ($null -ne $gov.ModeIFundamentalsStatus) { $script:ModeIFundamentalsStatus = [string]$gov.ModeIFundamentalsStatus }
            if ($null -ne $gov.EnergyFormulationAuditActionable) { $script:EnergyFormulationAuditActionable = [bool]$gov.EnergyFormulationAuditActionable }
            if ($null -ne $gov.EnergyBaselineQualified) {
                $script:EnergyBaselineQualified = [bool]$gov.EnergyBaselineQualified
                if ($script:EnergyBaselineQualified) {
                    $script:ModeIStateTransferStatus = "MODE1_STATE_TRANSFER_ENERGY_AUDIT_ACTIVE"
                    $script:ModeIStateTransferActionable = $true
                }
            }
            if ($null -ne $gov.SpatialTemporalConvergenceActionable) { $script:SpatialTemporalConvergenceActionable = [bool]$gov.SpatialTemporalConvergenceActionable }
            if ($null -ne $gov.SpatialTemporalConvergenceQualified) { $script:SpatialTemporalConvergenceQualified = [bool]$gov.SpatialTemporalConvergenceQualified }
            if ($null -ne $gov.ModeIStateTransferStatus) { $script:ModeIStateTransferStatus = [string]$gov.ModeIStateTransferStatus }
            if ($null -ne $gov.ModeIStateTransferActionable) { $script:ModeIStateTransferActionable = [bool]$gov.ModeIStateTransferActionable }
            if ($null -ne $gov.ModeIStateTransferQualified) { $script:ModeIStateTransferQualified = [bool]$gov.ModeIStateTransferQualified }
            if ($null -ne $gov.Gate7VisualizationOnHold) { $script:Gate7VisualizationOnHold = [bool]$gov.Gate7VisualizationOnHold }
            if ($null -ne $gov.ModeIIHigherComplexityOnHold) { $script:ModeIIHigherComplexityOnHold = [bool]$gov.ModeIIHigherComplexityOnHold }
            if ($null -ne $gov.ReportUpdateRequired) { $script:ReportUpdateRequired = [bool]$gov.ReportUpdateRequired }
            if ($null -ne $gov.NextSupervisorMeeting) { $script:NextSupervisorMeeting = [string]$gov.NextSupervisorMeeting }
            if ($null -ne $gov.AuthorInquiryStatus) { $script:AuthorInquiryStatus = [string]$gov.AuthorInquiryStatus }
            if ($null -ne $gov.MODE1_FUNDAMENTALS_COMPLETE) {
                $script:ModeIFundamentalsComplete = [bool]$gov.MODE1_FUNDAMENTALS_COMPLETE
                $script:MODE1_FUNDAMENTALS_COMPLETE = [bool]$gov.MODE1_FUNDAMENTALS_COMPLETE
            }
            if ($null -ne $gov.ModeIFundamentalsComplete) {
                $script:ModeIFundamentalsComplete = [bool]$gov.ModeIFundamentalsComplete
                $script:MODE1_FUNDAMENTALS_COMPLETE = [bool]$gov.ModeIFundamentalsComplete
            }

            # Retained compatibility fields (do NOT drive stop/restart logic)
            if ($null -ne $gov.PriorityQuestionA) { $script:PriorityQuestionA = [string]$gov.PriorityQuestionA }
            if ($null -ne $gov.QuestionAActionable) { $script:QuestionAActionable = [bool]$gov.QuestionAActionable }
            if ($null -ne $gov.PriorityQuestionB) { $script:PriorityQuestionB = [string]$gov.PriorityQuestionB }
            if ($null -ne $gov.QuestionBActionable) { $script:QuestionBActionable = [bool]$gov.QuestionBActionable }
            if ($null -ne $gov.PBSActive) { $script:PBSActive = [int]$gov.PBSActive }
            if ($null -ne $gov.Gate7_ModeII_StateTransfer_OnHold) { $script:Gate7_ModeII_StateTransfer_OnHold = [bool]$gov.Gate7_ModeII_StateTransfer_OnHold }
        }
        catch {
            Write-Verbose "Failed to sync governance state: $($_.Exception.Message)"
        }
    }
}
Sync-ControllerGovernanceState

function Get-AgyProfileFromCurrentOutput {
    $raw = ""
    $global:LASTEXITCODE = 0
    try {
        $raw = (& agy-profile current *>&1 | Out-String).Trim()
    }
    catch {
        $raw = "ERROR: $($_.Exception.Message)"
    }

    if ($raw -match '(?im)^Active profile:\s*(account[1-5])\b') {
        return $Matches[1].ToLowerInvariant()
    }

    if ($raw -match '(?i)last switch:\s*(account[1-5])') {
        return $Matches[1].ToLowerInvariant()
    }

    if ($raw -match '(?i)active file:\s*(account[1-5])') {
        return $Matches[1].ToLowerInvariant()
    }

    $activeFile = Join-PathStrict -Path "$env:USERPROFILE\.gemini\agy-profiles" -ChildPath "_active.txt"
    if (Test-Path -LiteralPath $activeFile) {
        $af = (Get-Content -LiteralPath $activeFile -Raw).Trim()
        if ($af -match '(?i)^account[1-5]$') {
            return $af.ToLowerInvariant()
        }
    }

    $selectionFile = Join-PathStrict -Path "$env:USERPROFILE\OpenClawPAD" -ChildPath "agy_selected_profile.json"
    if (Test-Path -LiteralPath $selectionFile) {
        try {
            $sel = Get-Content -LiteralPath $selectionFile -Raw | ConvertFrom-Json
            if ($sel.selected_profile -match '(?i)^account[1-5]$') {
                return ([string]$sel.selected_profile).ToLowerInvariant()
            }
        } catch {}
    }

    throw "Unable to determine active AGY profile.`n$raw"
}

if (-not [string]::IsNullOrWhiteSpace($script:RequestedAgyProfile)) {
    # Explicit caller selection always wins.
    $script:RunLockedAgyProfile = $script:RequestedAgyProfile.ToLowerInvariant()
}
else {
    # Only auto-detect when caller supplied nothing.
    $script:RunLockedAgyProfile = Get-AgyProfileFromCurrentOutput
}

# Compatibility alias
$script:AuthoritativeAgyProfile = $script:RunLockedAgyProfile

Write-Host " Run-Locked Authoritative Profile: '$script:RunLockedAgyProfile'" -ForegroundColor Green

function Get-ManuallySelectedAgyProfile {
    if (-not [string]::IsNullOrWhiteSpace($script:RunLockedAgyProfile)) {
        return $script:RunLockedAgyProfile
    }
    if (-not [string]::IsNullOrWhiteSpace($script:RequestedAgyProfile)) {
        return $script:RequestedAgyProfile
    }
    return "account1"
}

function Get-AgyProfileState {
    $raw = ""
    $global:LASTEXITCODE = 0
    try {
        $raw = (& agy-profile current *>&1 | Out-String).Trim()
    }
    catch {
        $raw = "ERROR: $($_.Exception.Message)"
    }

    $activeProfile = $null
    $lastSwitch    = $null
    $activeFile    = $null

    if ($raw -match '(?im)^Active profile:\s*(account[1-5])\b') {
        $activeProfile = $Matches[1].ToLowerInvariant()
    }

    if ($raw -match '(?i)last switch:\s*(account[1-5])') {
        $lastSwitch = $Matches[1].ToLowerInvariant()
    }

    if ($raw -match '(?i)active file:\s*(account[1-5])') {
        $activeFile = $Matches[1].ToLowerInvariant()
    }

    if (-not $activeFile) {
        $afPath = Join-PathStrict -Path "$env:USERPROFILE\.gemini\agy-profiles" -ChildPath "_active.txt"
        if (Test-Path -LiteralPath $afPath) {
            $af = (Get-Content -LiteralPath $afPath -Raw).Trim().ToLowerInvariant()
            if ($af -match '^account[1-5]$') {
                $activeFile = $af
            }
        }
    }

    [pscustomobject]@{
        ActiveProfile = $activeProfile
        LastSwitch    = $lastSwitch
        ActiveFile    = $activeFile
        Raw           = $raw
    }
}

function Test-AgyProfileLocked {
    param(
        [Parameter(Mandatory)]
        [string]$Expected
    )

    $state = Get-AgyProfileState

    if ($state.ActiveProfile) {
        return ($state.ActiveProfile -eq $Expected)
    }

    # If AGY cannot map the current OAuth credential to a saved profile,
    # require at least the selected file / last-switch provenance to match.
    if (
        $state.ActiveFile -eq $Expected -and
        (
            -not $state.LastSwitch -or
            $state.LastSwitch -eq $Expected
        )
    ) {
        return $true
    }

    return $false
}

function Set-AndVerifyAgyRunProfile {
    param(
        [Parameter(Mandatory)]
        [string]$Context
    )

    $expected = $script:RunLockedAgyProfile
    $tokenPath = Join-Path $env:USERPROFILE '.gemini/antigravity-cli/antigravity-oauth-token'
    $expectedBytes = Get-AgySavedCredentialBytes -Profile $expected
    try {
        try {
            Assert-AgyCredentialStores -ExpectedBytes $expectedBytes -TokenPath $tokenPath
        } catch {
            $verificationFailure = $_
            if ($verificationFailure.Exception.Message -notmatch 'source=native-store stage=ID_TOKEN_MISSING') { throw $verificationFailure }
            Repair-AgyRefreshedNativeCredential -ExpectedBytes $expectedBytes -TokenPath $tokenPath
            Assert-AgyCredentialStores -ExpectedBytes $expectedBytes -TokenPath $tokenPath
            Write-Host "[PROFILE-GUARD] Verified refreshed native grant with provider and synchronized CLI cache [$Context]."
        }
    } finally { [Array]::Clear($expectedBytes,0,$expectedBytes.Length) }

    $state = Get-AgyProfileState

    $mustRestore = $false

    if ($state.ActiveProfile) {
        $mustRestore = ($state.ActiveProfile -ne $expected)
    }
    else {
        # AGY may refresh an OAuth access token during its CLI call. An
        # unidentified saved-profile fingerprint is NOT evidence that a human
        # changed accounts. Only accept the profile marker if it agrees with
        # the run lock and there is no contradictory last-switch record.
        $mustRestore = (
            $state.ActiveFile -ne $expected -or
            (
                $state.LastSwitch -and
                $state.LastSwitch -ne $expected
            )
        )
        if (-not $mustRestore -and $Context -eq 'POST_AGY') {
            Write-Warning ("[PROFILE-GUARD] Saved-profile blob changed after token refresh; native and CLI identity metadata passed the account guard for '{0}'." -f $expected)
        }
    }

    if ($mustRestore) {
        if($ControlledSingleTurn){throw 'Controlled turn profile mismatch; automatic credential switching is disabled'}
        if ($EnableSmartAgyProfileSelection -and $Context -ne 'STARTUP') {
            throw "AGY profile changed during $($Context): expected '$expected', detected '$($state.ActiveProfile)'. Will not silently undo an external switch. Switch only between AGY calls."
        }
        Write-Host ""
        Write-Host "==========================================================" -ForegroundColor Yellow
        Write-Host " AGY PROFILE DRIFT DETECTED [$Context]" -ForegroundColor Yellow
        Write-Host " Required: $expected" -ForegroundColor Yellow
        Write-Host " Current state:" -ForegroundColor Yellow
        Write-Host $state.Raw -ForegroundColor Yellow
        Write-Host " Restoring authoritative run profile..." -ForegroundColor Yellow
        Write-Host "==========================================================" -ForegroundColor Yellow

        $global:LASTEXITCODE = 0
        try {
            $null = & agy-profile switch $expected -Force *>&1
        }
        catch {
            $err = "FATAL: Could not restore AGY profile '$expected' in context '$Context': $($_.Exception.Message)"
            if (Get-Command Write-LoopLog -ErrorAction SilentlyContinue) {
                Write-LoopLog -Turn $CurrentTurn -Tier "CONTROLLER" -Action "PROFILE_RESTORE_FAILED" -Message $err
            }
            throw $err
        }

        # Keep agy_selected_profile.json synchronized with the active restored profile
        if (Test-Path $PadDir) {
            try {
                $selObj = [ordered]@{
                    selected_profile = $expected
                    source           = "controller_run_lock"
                    switched_at_utc  = [DateTime]::UtcNow.ToString("o")
                    switched_by      = "Set-AndVerifyAgyRunProfile"
                }
                [System.IO.File]::WriteAllText(
                    $SelectionFile,
                    ($selObj | ConvertTo-Json -Depth 5),
                    [System.Text.UTF8Encoding]::new($false)
                )
            } catch {}
        }
    }

    $verify = Get-AgyProfileState

    if (
        $verify.ActiveProfile -and
        $verify.ActiveProfile -ne $expected
    ) {
        $err = @"
AGY profile verification failed [$Context].
Expected authenticated profile: $expected
Detected authenticated profile: $($verify.ActiveProfile)
Active file: $($verify.ActiveFile)
"@
        if (Get-Command Write-LoopLog -ErrorAction SilentlyContinue) {
            Write-LoopLog -Turn $CurrentTurn -Tier "CONTROLLER" -Action "PROFILE_VERIFY_FAILED" -Message $err
        }
        throw $err
    }

    if (
        -not $verify.ActiveProfile -and
        $verify.ActiveFile -ne $expected
    ) {
        $err = @"
AGY profile verification failed [$Context].
Expected active file: $expected
Detected active file: $($verify.ActiveFile)
Raw:
$($verify.Raw)
"@
        if (Get-Command Write-LoopLog -ErrorAction SilentlyContinue) {
            Write-LoopLog -Turn $CurrentTurn -Tier "CONTROLLER" -Action "PROFILE_VERIFY_FAILED" -Message $err
        }
        throw $err
    }

    Write-Host "[PROFILE-GUARD] Verified '$expected' [$Context]." -ForegroundColor Green
}

function Ensure-AuthoritativeAgyProfile {
    param([string]$Context = "unknown")
    Set-AndVerifyAgyRunProfile -Context $Context
}

$PersistentAgentGuard = @"
PERSISTENT ANTIGRAVITY CLI TOOL-SAFETY RULES -- APPLY TO EVERY TURN:

1. Never pass a workspace/project path such as
   D:\Master thesis\Adaptive remeshing\...
   directly to the Antigravity `write_to_file` / artifact-writing tool.

2. The artifact-writing tool may write only inside the current Antigravity
   conversation brain directory:
   C:\Users\pruth\.gemini\antigravity-cli\brain\<CURRENT_CONVERSATION_ID>\

3. For temporary Python/PowerShell/bash scripts:
   - prefer running code inline from the terminal; or
   - create the temporary file inside the current conversation brain directory.
   Do not create temporary helper scripts directly in the project tree with
   `write_to_file`.

4. If a verified project file genuinely must be created or updated:
   - first create the complete candidate inside the current conversation brain;
   - verify it;
   - then use an ordinary terminal filesystem command (for example PowerShell
     Copy-Item) to copy it to the exact workspace destination.
   Do not use `write_to_file` on the destination workspace path.

5. Before replacing an existing project file, re-read/verify the destination and
   preserve the prior version when appropriate.

6. Do not work around the artifact-path restriction with broad recursive searches,
   global tree scans, or unrelated workspace edits.

7. If an artifact/tool restriction prevents safe completion, report the exact
   restriction and stop instead of attempting an invalid workspace artifact write.

8. All shell/PowerShell commands must be NON-INTERACTIVE and fully parameterized.
   - Always pass `-NonInteractive` when spawning `powershell` (e.g. `powershell -NoProfile -NonInteractive ...`).
   - Never issue a cmdlet that can pause for mandatory parameter input.
   - Use `Get-Content -LiteralPath '<exact path>'` and NEVER bare `Get-Content` or unverified variables that may expand to null.
   - Use `Get-FileHash -LiteralPath '<exact path>' -Algorithm SHA256` and NEVER bare `Get-FileHash`.
   - Use exact `-LiteralPath`, `-Path`, `-Destination`, `-Filter`, etc. values.
   - Do not invoke commands that wait for Read-Host, confirmation, credential,
     parameter-binding, or other console input.

9. If an exact required parameter/path is unknown, do not trigger an interactive
   prompt. Resolve it with a bounded read-only lookup first; if it still cannot be
   resolved safely, report the missing value and stop.

10. Prefer fail-fast command forms (`-ErrorAction Stop` where appropriate) so a
    malformed helper command returns an error to the controller instead of hanging
    indefinitely at an interactive PowerShell prompt.

11. Never call `view_file`, `read_file`, or any artifact-reading tool on a path
    unless that exact file has first been proven to exist.
    For Windows paths use a bounded check such as:
      Test-Path -LiteralPath '<exact path>'
    For Linux/cluster paths use an exact non-interactive existence check.

12. Never invent or assume a scratch/brain artifact filename because a computation
    was planned or launched. A planned output is NOT an existing artifact.

13. If an expected temporary result file is missing:
    - do not call `view_file` on it;
    - first determine whether the computation actually produced it;
    - if not, recompute the result inline or explicitly create the artifact inside
      the current brain directory;
    - verify existence with `Test-Path -LiteralPath` before reading it.

14. Prefer returning computed scientific results directly in the agent response
    rather than creating unnecessary temporary JSON/Markdown artifacts.

15. A missing temporary brain artifact must never trigger a new PBS submission,
    repeat a completed HPC calculation, or broaden the scientific task. Recover
    locally from existing evidence and continue the current turn.

16. REMOTE COMMAND SAFETY - MANDATORY:
    - All noninteractive SSH commands must use `ssh -n -T` and `-o BatchMode=yes`.
    - The `-n` flag is strictly required to disconnect stdin from null and prevent remote tools
      from hanging indefinitely waiting on console input.
    - Never wrap simple remote inspection commands in nested `bash -c`, `bash -lc`, or `sh -c`.
      Pass the remote command directly to SSH with explicit arguments.
    - Never execute bare `tail`, bare `cat`, bare `grep`, or another program that can wait on stdin.
    - Prefer calling `powershell -NoProfile -ExecutionPolicy Bypass -File .\.agents\scripts\Invoke-GuardedSsh.ps1 -RemoteCommand "..."`.
    - Every SSH command must have a bounded execution timeout (default 120s). A timed-out command
      must terminate only its own spawned SSH process, return a tool failure, and allow recovery.
    - For complex multi-command remote logic, use a controlled temporary remote script rather than
      nested shell quoting.
"@



$ProjectAlignmentGuard = @"
PROJECT / THESIS ALIGNMENT GUARD -- SUPERVISOR-ALIGNED DIRECTIVE:

================================================================================
SUPERVISOR GOVERNING DIRECTIVE & ACTIVE SCIENTIFIC PHASE
================================================================================
"We need to have understood everything related to the first model before we increase complexity."

ACTIVE SCIENTIFIC PHASE:
  MODE1_GATE6B_ACTIVE_EVALUATION_AND_CONTINUATION

NEW SCIENTIFIC ROADMAP:
  Qualified Mode-I benchmark
    -> corrected mechanical implementation
    -> qualified MISESERI/adaptive-remeshing workflow
    -> UEL ENERGY FORMULATION / OUTPUT AUDIT
    -> GLOBAL ENERGY BALANCE
    -> SPATIAL + TEMPORAL MODE-I CONVERGENCE
    -> PHASE-FIELD / CRACK-PATH CONVERGENCE
    -> MODE-I STATE-TRANSFER ENERGY PRESERVATION
    -> complete Mode-I report
    -> supervisor review
    -> only then visualization integration / higher-complexity example

NEXT SUPERVISOR MEETING:
  Thursday, 08 October 2026, 10:00 CEST
  All Mode-I work completed before that meeting must be incorporated directly into
  the growing report, including theory, methods, results, unresolved issues, and figures.

================================================================================
SUPERSEDING SUPERVISOR DECISIONS (17 SEPTEMBER 2026)
================================================================================

A. 71,320-MESH STIFFNESS DEFECT:
   Status: RESOLVED_AND_CLOSED
   Verified cause: Abaqus keyword/NSET formatting allowed only 16 entries on the
   malformed data line; the remaining 134 of 150 intended N_BOTTOM nodes were not
   included in the parsed set.
   Verified correction: wrap the N_BOTTOM node IDs across valid data lines.
   Authoritative corrected evidence: 1405044.mmaster02, 1404933.mmaster02.
   Rule: Do NOT reopen this diagnostic unless genuinely contradictory new evidence appears.

B. 13,941-vs-71,320 PANDEY-KUMAR ELEMENT-COUNT REPRODUCTION:
   New status: SUPERVISOR_ACCEPTED_REPRODUCTION_LIMITATION_CLOSED
   The supervisor explicitly accepted that:
   - the complete authors' implementation/code is not available;
   - the publication does not expose enough information to reproduce every reported
     element count exactly;
   - the project has tested the justified accessible variables;
   - reproduction of general trends is sufficient;
   - additional effort trying to discover an unpublished detail is NOT justified.
   Therefore:
   - STOP treating 13,941 vs 71,320 as the active scientific blocker.
   - STOP new Abaqus-version tests for this purpose.
   - STOP errorTarget tuning for the purpose of forcing 13,941.
   - STOP further arbitrary remeshing-factor sweeps aimed only at matching an element count.
   - Do NOT send the prepared author inquiry unless the human/supervisor explicitly reopens it.
   - Retain all existing reproduction results in the thesis/report as documented evidence.

Preserved project sensitivity results:
   errorTarget=1.0 -> 71,320 finite elements
   errorTarget=2.0 -> 17,687 finite elements
   errorTarget=3.0 ->  8,120 finite elements
   errorTarget=5.0 ->  4,356 finite elements
   Interpret them strictly as sensitivity/trend evidence.

Explicitly preserve:
   errorTarget=1.0 means a 1% target error tolerance under UNIFORM_ERROR sizing.
   It does NOT mean MISESERI=1.
   errorTarget=2.0 does NOT mean MISESERI=2.
   errorTarget is not a direct MISESERI threshold.

The old A/B reproduction-resolution phase is closed, but MODE-I FUNDAMENTALS ARE NOT COMPLETE.

================================================================================
NEW ACTIVE TECHNICAL PRIORITIES & GOVERNANCE STATE
================================================================================

PRIORITY 1 -- UEL ENERGY FORMULATION AND OUTPUT (HIGHEST PRIORITY):
Status: UEL_ENERGY_OUTPUT_QUALIFIED_MECHANICALLY_NONINVASIVE
The supervisor explicitly requested meaningful GLOBAL ENERGY measures and energy balance,
not only peak reaction force and not only external-work integration.
The existing statement that Abaqus UEL ENERGY is unavailable must NOT be treated as a
permanent limitation. Audit the authoritative Fortran formulation in f42_mixed_uel.for and
determine what energetic terms can be rigorously computed and output.

MANDATORY ORDER:
1. Inspect the authoritative UEL equations/source before editing anything.
2. Derive the energy expressions actually consistent with the implemented weak form.
3. Identify, with units and sign conventions, at minimum where applicable:
   - stored elastic/strain energy;
   - phase-field/fracture surface energy;
   - dissipated/fracture contribution;
   - external work: W_ext(u) = integral_0^u F(u_tilde) du_tilde;
   - any other term required by the exact implemented formulation.
4. Establish the correct global energy-balance identity for THIS implementation.
   Do NOT label integral(F du) as internal energy or fracture energy.
5. Determine how these terms should be exposed through Abaqus UEL ENERGY and/or
   rigorously defined state/output variables without double-counting co-located UEL/UMAT layers.
6. Do not invent energy terms simply to produce plots.
7. Preserve the original authoritative Fortran source and hash before instrumentation.
8. Any energy-output modification must be mechanically non-invasive:
   RHS, AMATRX, constitutive evolution, and existing STATEV semantics must remain unchanged.
9. Prove before/after mechanical parity after adding energy instrumentation.
10. Before expensive Mode-I reruns:
    source audit -> derivation -> code review -> compile -> datacheck ->
    smallest meaningful verification -> authoritative Mode-I verification.

Only after the energy implementation is physically and numerically qualified may the
controller launch the full convergence batch.

PRIORITY 2 -- MULTIFACETED MODE-I CONVERGENCE:
Peak F_max alone is explicitly insufficient.
Computational cost is NOT a required convergence criterion for the present supervisor task.
Required convergence evidence:
1. Complete force-displacement response: elastic branch, crack initiation, F_max, u(F_max), post-peak.
2. Initial structural stiffness K0 using one consistent extraction rule:
   Canonical reference stiffness K_0 = 137.945520 kN/mm (intercept 4.472368e-5 kN, R^2 = 0.99999960, N = 400 active increments).
   Do NOT imply Pandey & Kumar Fig. 7 reports K0. K0 is project-derived.
3. Global energy evolution and energy-balance quantities (residuals, normalized error).
4. Spatial phase-field distribution d(x).
5. Matched-displacement phase-field contours.
6. Quantitative ligament/localization profiles, e.g. d(x, y=0.5 mm).
7. Crack-path/localization convergence.
8. Spatial-resolution convergence.
9. Temporal/time-increment convergence.
10. Phase-field length-scale sensitivity/convergence where required.
Report exactly whether each quantity is: CONVERGED / STABLE, MESH-SENSITIVE, TEMPORALLY SENSITIVE,
or NOT YET QUALIFIED. Use global integral measures.

PRIORITY 3 -- MODE-I STATE-TRANSFER CONSERVATION:
Status: BLOCKED_UNTIL_ENERGY_BASELINE_QUALIFIED.
Once the baseline energy implementation is qualified, automatically promote to:
MODE1_STATE_TRANSFER_ENERGY_AUDIT_ACTIVE.
Assess transfer between nonmatching meshes using the SAME simple Mode-I benchmark:
compare before/after mapping: d-field; history/state variables; spatial localization;
||d_mapped - d_donor||; ||grad(d_mapped) - grad(d_donor)||; every qualified global energy
component; total energy/balance; energy difference introduced by mapping.
Primary question: Does mesh-to-mesh state transfer preserve the physically relevant energetic
state, or does it introduce measurable energy gain/loss?
Do NOT return to Mode-II for this investigation.

ACTIVE SCOPE HOLDS:
- MODE-II: HOLD.
- Mixed mode: HOLD.
- Multiple-crack / holes / higher-complexity reproduction: HOLD.
- Gate 7 visualization / ABAQUSER integration: HOLD UNTIL MODE-I FUNDAMENTALS ARE QUALIFIED.
- After Mode-I fundamentals are qualified, ONE representative more-complex model may
  eventually be used to demonstrate that the framework generalizes.
  Do NOT plan to reproduce all complex Pandey-Kumar examples.

GOVERNING PRESENTATION & RESEARCH LOGIC:
  [Define problem] -> [Define expected solution] -> [Establish reference]
  -> [Apply adaptive method] -> [Compare] -> [Explain discrepancies]

PROHIBITED REPORTING STRUCTURE:
  DO NOT present work as:
  [Simulation history] -> [All things attempted] -> [Current result].

================================================================================
1. PROBLEM DEFINITION & FIXED-MESH REFERENCE ANCHOR
================================================================================
BENCHMARK BOUNDARY VALUE PROBLEM:
- Domain: Omega = 1 mm x 1 mm square plate.
- Crack: a_0 = 0.5 mm sharp edge crack (zero-gap seam along y = 0.5 mm, 0 <= x <= 0.5 mm).
  (Note: The finite-width notch was an erroneous implementation that radically altered structural
   compliance; the zero-gap sharp seam is the mandatory correct benchmark representation).
- Boundary conditions:
  * Bottom edge (y = 0): u_y = 0 (roller support) with pinned point (u_x = 0) to prevent rigid body motion.
  * Top edge (y = 1): Mode-I displacement-controlled tensile loading (u_y prescribed).
- Material & phase-field parameters:
  * Young's modulus: E = 210 GPa (210 kN/mm^2)
  * Poisson's ratio: nu = 0.3
  * Critical fracture energy release rate: G_c = 2.7e-3 kN/mm (2.7 N/mm)
  * Phase-field length scale: l_0 = 0.0075 mm (7.5 um)

EXPECTED PHYSICAL RESPONSE:
- Initial linear-elastic response.
- Crack-tip phase-field damage localization (0 <= d <= 1).
- Peak reaction force followed by sharp post-peak load drop.
- Pure horizontal crack extension along the symmetry line (y = 0.5 mm).

FIXED-MESH REFERENCE AS THE QUANTITATIVE ANCHOR:
- The fixed-mesh reference solution is the quantitative baseline against which all
  adaptive results must be judged:
  * Reconstructed fixed-mesh baseline (Job 1398090, 15,192 finite elements):
      F_max = 0.757778 kN,  u(F_max) = 0.005857 mm,
      Canonical reference stiffness K_0 = 137.945520 kN/mm (intercept 4.472368e-5 kN, R^2 = 0.99999960, N = 400 active increments).
      (Note: K_0 is project-derived from the elastic response; Pandey & Kumar Fig. 7 reports F-u response and does NOT report K_0).
  * Digitized reference values (Pandey & Kumar, 2025, Fig. 7(a)):
      F_max ~ 0.758 kN,     u(F_max) ~ 0.005860 mm
- Mandatory anchor statement:
  "This is the reference response that my adaptive solution must reproduce to an acceptable accuracy."
  Everything after that must be measured against it.

================================================================================
2. COMPREHENSIVE CONVERGENCE EVALUATION (PEAK FORCE ALONE IS NOT ENOUGH)
================================================================================
- Peak reaction force (F_max) alone is strictly INSUFFICIENT to establish mesh adequacy or convergence.
- Convergence must be evaluated through multiple complementary quantities:
  1. Complete force-displacement (F-u) response curve across the full range (elastic, peak, softening).
  2. Peak reaction force (F_max).
  3. Displacement at peak force (u(F_max)).
  4. Global energy evolution and energy-balance quantities:
     * Priority 1 Task: Audit the authoritative Fortran weak form in f42_mixed_uel.for and expose UEL energy terms.
     * The existing statement that Abaqus UEL ENERGY is unavailable must NOT be treated as a permanent limitation.
     * Identify stored elastic energy, phase-field surface energy, dissipated fracture contribution, external work W_ext = integral F du, and any other required terms.
     * Produce global energy balance, residuals, and normalized error.
  5. Phase-field / damage distribution (d-field contour and tip localization).
  6. Crack-path and localization-profile convergence.
  7. Computational cost: Computational cost is NOT a required convergence criterion for the present supervisor task.
- Mandatory formulation for report and narrative:
  "Mesh adequacy is evaluated using global force-displacement response, qualified UEL energetic measures and global balance, damage-field evolution, and localization profiles."

================================================================================
3. 13,941-VS-71,320 ELEMENT-COUNT REPRODUCTION LIMITATION (CLOSED)
================================================================================
- Literature reported mesh: Pandey & Kumar report an element count of ~13,941 for their Mode-I adaptive mesh.
- Status: SUPERVISOR_ACCEPTED_REPRODUCTION_LIMITATION_CLOSED.
- The supervisor explicitly accepted that:
  * The complete authors' implementation/code is not available;
  * The publication does not expose enough information to reproduce every reported element count exactly;
  * The project has tested the justified accessible variables;
  * Reproduction of general trends is sufficient;
  * Additional effort trying to discover an unpublished detail is NOT justified.
- Governed rules:
  * STOP treating 13,941 vs 71,320 as the active scientific blocker.
  * STOP new Abaqus-version tests for this purpose.
  * STOP errorTarget tuning for the purpose of forcing 13,941.
  * STOP further arbitrary remeshing-factor sweeps aimed only at matching an element count.
  * Do NOT send the prepared author inquiry unless the human/supervisor explicitly reopens it.
  * Retain all existing reproduction results in the thesis/report as documented evidence.
- Preserved project sensitivity results:
  * errorTarget=1.0 -> 71,320 finite elements
  * errorTarget=2.0 -> 17,687 finite elements (canonical errorTarget=2.0 sensitivity)
  * errorTarget=3.0 ->  8,120 finite elements (canonical errorTarget=3.0 sensitivity)
  * errorTarget=5.0 ->  4,356 finite elements (canonical errorTarget=5.0 sensitivity)
  Interpret them strictly as sensitivity/trend evidence.
- Explicitly preserve:
  * errorTarget=1.0 means a 1% target error tolerance under UNIFORM_ERROR sizing. It does NOT mean MISESERI=1.
  * errorTarget=2.0 does NOT mean MISESERI=2.
  * errorTarget is not a direct MISESERI threshold.

================================================================================
4. PHYSICAL UNDERSTANDING OF MISESERI
================================================================================
- Safe wording:
  "MISESERI is the Abaqus Mises stress discretization/error indicator associated with the recovered stress solution."
  Do NOT assert an exact proprietary SPR/ZZ/internal Abaqus sizing formula unless a primary source proves it.
  * It is based on stress-recovery error estimation on the linear-elastic continuum stress field.
  * It is NOT phase-field error.
  * It is NOT damage error.
- Canonical Mode-I MISESERI provenance:
  * Coarse mesh = 2,906 finite elements (2,818 CPE4 + 88 CPE3) and 2,988 nodes.
  * 2,906 WHOLE_ELEMENT MISESERI scalar values, exactly one value per underlying finite element.
  * The old 3,930-row dataset belonged to Mode-II and is purged from the active Mode-I narrative.
- Representation:
  * Plotted points in Mode-I represent element-field error indicator data from the 2,906-element pre-analysis, not simple nodes.
- Conceptual causal chain:
  [Coarse FE stress field]
         |
         v
  [Stress recovery / error estimation]
         |
         v
  [MISESERI error indicator field]
         |
         v
  [Abaqus RemeshingRule identifies under-resolved regions]
         |
         v
  [Local element sizing calculation]
         |
         v
  [adaptiveRemesh generates new mesh]
- Verification question:
  "Does the generated mesh spatially correspond to the regions where refinement was expected based on the stress error field?"

================================================================================
5. ACTIVE PROJECT SCOPE RESTRICTIONS
================================================================================
- MODE-II WORK IS PAUSED:
  * Mode-II introduces shear loading, crack angle/direction, sliding/friction-like effects,
    and complex crack path interpretations.
  * Rule: DO NOT continue Mode-II while MODE1_RESOLUTION_EXTENSION_ACTIVE is true.
  * Completion of a supervisor handoff package does NOT release this hold. Release
    requires verified closure of the active Mode-I resolution questions or explicit
    human/supervisor authorization.
  * Even if the rest of the thesis period were spent understanding the Mode-I problem properly,
    that is acceptable.
  * Chapter 5 material remains archived and preserved, but MUST NOT drive active research, tasks, or controller turns.
- STATE TRANSFER IS SECONDARY:
  * State transfer between nonmatching meshes is an enabling restart technology, not the main branch now.
  * Numerical Diffusion Warning: When mapping phase-field d between meshes (d_h^(A) -> d_h^(B)),
    interpolation/extrapolation inevitably diffuses gradients (|grad d| decreases), even between nominally equivalent meshes.
    Because the phase field represents the crack strictly through steep spatial gradients of d,
    repeated mapping causes numerical diffusion.
  * Future evaluation will compare ||d_mapped - d_donor|| and ||grad d_mapped - grad d_donor||.
  * Mode-I must be understood before returning to multi-step state transfer.

================================================================================
6. TERMINOLOGY DISCIPLINE: ELIMINATE "PHYSICAL ELEMENT"
================================================================================
- REMOVE the phrase "physical element" entirely when describing the finite element mesh.
- Always use standard finite-element terminology:
  * "number of finite elements" or "element count"
  * Example: "an element count of 17,687" or "17,687 finite elements" (NEVER "17,687 physical elements").
- When describing the multi-layer UEL/UMAT formulation:
  * Refer to "co-located UEL user elements" and "companion visualization UMAT elements" precisely,
    not as "physical" vs "non-physical".

================================================================================
7. STRUCTURAL STIFFNESS EXPLANATION (FIGURE 7.1)
================================================================================
- Figure 7.1 compares initial stiffness values: K_0 ~ 138.15 kN/mm vs 75.47 kN/mm vs 141.82 kN/mm.
- Rigorous definition: Initial stiffness K_0 is the slope of the initial linear-elastic range
  of the global reaction force versus prescribed displacement curve:
    K_0 = dF/du |_{initial elastic range} ~ Delta F / Delta u
- Physical meaning:
  * K_0 is a GLOBAL STRUCTURAL STIFFNESS, NOT the material Young's modulus E.
  * The finite-width notch radically increased structural compliance (reducing K_0 to 75.47 kN/mm).
  * Replacing the notch with the zero-gap sharp seam restored the specimen's structural stiffness
    to ~138 kN/mm, matching the reference behavior.

================================================================================
8. STRUCTURE OF THE GROWING MODE-I REPORT (PRE-OCTOBER-2026)
================================================================================
Everything verified in Mode-I must be incorporated into the report continuously
before the 08 October 2026 meeting (10:00).
The report should strictly distinguish:
  * THEORY / EXPECTATION
  * VERIFIED NUMERICAL EVIDENCE
  * UNRESOLVED / NOT YET QUALIFIED
Specifically include:
  - MISESERI theory and role;
  - Published vs project implementation distinctions;
  - N_BOTTOM defect / root cause / fix;
  - Remeshing reproduction trends and supervisor-accepted publication limitation;
  - Complete F-u convergence;
  - Global energy formulation and balance;
  - Phase-field spatial profiles;
  - Temporal convergence;
  - State-transfer energy preservation once available.
Do NOT organize the thesis/report as simulation chronology.

================================================================================
9. SCIENTIFIC EPISTEMOLOGY & CLAIMS DISCIPLINE
================================================================================
Do not present AI-derived claims that cannot be defended. Strictly categorize every statement:
1. "I know this" -- analytical definitions, physical constants, boundary conditions.
2. "I verified this numerically" -- exact solver jobs, extracted F-u data, convergence metrics, hashes.
3. "I do not yet understand this" -- genuine scientific open questions (e.g. nominal 1% element count discrepancy).
Stating "I do not yet understand this" is scientifically superior to giving an unsupported explanation.

================================================================================
10. REQUIRED SUPERVISOR DELIVERABLES SPECIFICATION
================================================================================
The supervisor does NOT want tens of gigabytes of large ODB files.
Deliver a clean, lightweight local reproduction package:
- Complete input decks (.inp);
- User subroutine Fortran source files (.for);
- Python remeshing and post-processing scripts (.py);
- commands.txt: exact, step-by-step shell/Abaqus execution instructions matching the real cluster/local environment.

================================================================================
11. SUPERVISOR-ALIGNED MASTER GATE DASHBOARD & HARD STOP RULES
================================================================================
The thesis execution is strictly governed by 12 sequential gates (Gates 0-11).
No new branch may bypass the active gate. A gate is closed only when its exit
evidence is complete and can be defended without AI-generated speculation:

- Gate 0 -- Source & Scope Freeze (Proposal Tasks 1-2):
  Exit evidence: Primary papers, formal proposal, meeting notes, and benchmark
  parameters indexed. Active scientific question stated in one sentence.
  HARD STOP RULE: Do not run simulations until the exact Mode-I problem and
  expected response are written down.

- Gate 1 -- Conventional Mode-I Reference (Proposal Task 3):
  Exit evidence: Fixed-mesh model reproduces the paper/reference response and its
  mesh/convergence basis is documented.
  HARD STOP RULE: No adaptive interpretation before the reference solution is qualified.

- Gate 2 -- Multi-Quantity Convergence Qualification (Task 3 Prerequisite):
  Exit evidence: F-u curve, F_max, u_peak, K_0, d-field/profile, crack path,
  energy/work status (with UEL limitation acknowledged), and computational cost addressed.
  HARD STOP RULE: Peak force alone CANNOT close this gate.

- Gate 3 -- MISESERI Mechanism Verification (Task 4 Prerequisite):
  Exit evidence: Source of MISESERI, field meaning, element set, step, output position,
  and spatial distribution understood and reproducible.
  HARD STOP RULE: Do not treat MISESERI as phase-field error or damage error.

- Gate 4 -- Native Python Refinement Implementation (Proposal Task 4):
  Exit evidence: RemeshingRule + adaptiveRemesh generate a genuine topology/size change;
  UEL/UMAT layers reconstructed deterministically.
  HARD STOP RULE: No custom remesher may substitute for the built-in reference method.

- Gate 5 -- Native-Remesh Reproduction (71,320 vs 13,941):
  Status: CLOSED_WITH_SUPERVISOR_ACCEPTED_PUBLICATION_LIMITATION
  Exit evidence: The supervisor explicitly accepted that the publication does not expose
  enough information to reproduce every reported element count exactly; reproduction of
  general trends is sufficient; additional effort trying to discover an unpublished detail
  is not justified.
  Exact 13,941 reproduction is NO LONGER an exit requirement or active blocker.
  Preserve tested errorTarget sensitivity trends (1.0 -> 71,320; 2.0 -> 17,687; 3.0 -> 8,120; 5.0 -> 4,356)
  and missing-information boundary.

- Gate 6A -- Mechanical Mode-I Implementation:
  Status: RESOLVED_AND_CLOSED
  Exit evidence: N_BOTTOM defect identified (Abaqus keyword/NSET 16-entry card limit silently
  omitted 134/150 bottom nodes) and corrected (card wrapping across lines). Corrected full-fracture
  response verified (1405044.mmaster02, 1404933.mmaster02).
  Do NOT reopen this diagnostic unless contradictory new evidence appears.

- Gate 6B -- Mode-I Energetic / Convergence Qualification:
  Status: ACTIVE -- HIGHEST PRIORITY
  Exit evidence: Physically derived UEL energy quantities; verified energy output; global energy balance;
  full F-u comparison; spatial phase-field convergence; temporal convergence; relevant length-scale convergence.
  MANDATORY ORDER: source audit -> derivation -> code review -> compile -> datacheck ->
  smallest meaningful verification -> authoritative Mode-I verification.

- Gate 6C -- Mode-I State-Transfer Conservation:
  Status: PENDING_GATE_6B
  Release only after energy baseline is qualified. Automatically promote to MODE1_STATE_TRANSFER_ENERGY_AUDIT_ACTIVE.
  Evaluate whether mesh-to-mesh transfer preserves energetic state or introduces energy gain/loss.

- Gate 7 -- ABAQUSER Integration / Visualization (Proposal Task 6):
  Status: HOLD (until Mode-I fundamentals are qualified).
  Exit evidence: Authentic IMFD ABAQUSER path integrated and verified.

- Gate 8 -- Higher-Complexity Benchmarks (Proposal Task 7):
  Status: HOLD (until Mode-I fundamentals are qualified).
  After Mode-I fundamentals are qualified, ONE representative more-complex model may demonstrate generalization.

- Gate 9 -- Parameter Recommendations (Proposal Task 8):
  Exit evidence: Recommendations based on verified sensitivity trends, not a single outcome.
  HARD STOP RULE: State applicability range and numerical limitations explicitly.

- Gate 10 -- Future-User Documentation (Proposal Task 9):
  Status: ACTIVE CONTINUOUSLY.
  Exit evidence: Reproduction package contains .inp, .for, .py, commands.txt, and provenance.
  HARD STOP RULE: Do not require multi-GB ODB transfers for basic reproduction.

- Gate 11 -- Thesis Synthesis (Proposal Task 10):
  Status: ACTIVE CONTINUOUSLY but cannot close until Mode-I fundamentals are qualified.
  Exit evidence: Final thesis organized by scientific logic, not historical chronology;
  verified and unresolved findings strictly separated.
  HARD STOP RULE: No unresolved question may be written as a proven physical mechanism.

================================================================================
12. PRE-JOB ANTI-DEVIATION CARD & GATE-MAPPING CONTRACT
================================================================================
Every simulation, script change, or solver job MUST complete this mental card:
[ ] Which original proposal task does this job advance? (Tasks 1-10)
[ ] Which active gate does it close? (Gates 0-11, currently Gate 6B)
[ ] What is the scientific question / hypothesis?
[ ] What is the single intended change from the previous qualified case?
    (Change one numerical/physical factor at a time for diagnosis; do not vary
     geometry, mesh rules, time-stepping, and solver controls simultaneously).
[ ] What must remain frozen?
[ ] What are the primary outputs and pre-declared acceptance criteria?
[ ] If the result is unexpected, the next action MUST be the smallest isolated
    evidence-supported diagnostic -- NOT a new research branch.
[ ] Queue availability or spare HPC capacity is NEVER a reason to launch a job.
[ ] A job that exits 0 is technically complete, NOT automatically scientifically accepted.

ENERGY-JOB ANTI-DEVIATION CARD:
For every UEL energy code change or solver run require:
[ ] Which Mode-I fundamentals question does this close?
[ ] What energy term is being evaluated?
[ ] What exact equation defines it?
[ ] Where in the UEL is it computed?
[ ] What units/sign convention are used?
[ ] What is the single intended source/input change?
[ ] What RHS/AMATRX/STATEV behavior must remain unchanged?
[ ] What is the before/after mechanical-parity criterion?
[ ] What is the global energy-balance quantity?
[ ] What output will be added to the report?
[ ] What result would falsify the implementation?
A successful Abaqus exit is NOT energy qualification.

================================================================================
REVISED HPC CONCURRENCY POLICY â€” MODE-I SHARED-MEMORY MULTI-THREADING & BATCH CAPACITY
================================================================================

PROJECT ACTIVE-JOB CAPACITY & QUEUE LIMITS:

    Demonstrated Minimum Concurrency: 10 SIMULTANEOUS ACTIVE JOBS (97 CPUs in R state)
    Queue: normal_imfdfkmq
    - No explicit per-user max_run job-count limit.
    - Per-user running CPU limit: 640 CPUs.
    - Per-user running memory limit: 4 TB.
    - Theoretical CPU headroom: ~543 additional CPUs with 97 CPUs allocated
      (node availability and placement permitting).

    POLICY PRINCIPLE:
    10 is a demonstrated minimum capability floor, not a ceiling.
    During the September-9 window, Antigravity can cautiously expand to
    15â€“20 useful Mode-I jobs where scientifically justified.

    GOVERNING CONSTRAINT:
    Scientific usefulness, not an arbitrary job-count cap.
    Strictly NO redundant or dummy jobs just to test capacity or consume resources.    PARALLEL EXECUTION ARCHITECTURE:
    f42_mixed_uel.for remains unqualified for true multi-rank MPI (strictly disqualified).
    Individual Abaqus jobs must execute in single-rank shared-memory mode:
    1-CPU serial is the authoritative scientific reference anchor;
    8-thread shared-memory SMP is empirically qualified for the tested Mode-I formulation and controls;
    16-thread shared-memory execution is UNQUALIFIED pending independent Stage-A/B verification;
    4-thread shared-memory execution is not part of the active approved execution path.
    High throughput is achieved primarily by running many independent scientific jobs concurrently.

Q and R both count as active.

================================================================================
SERIAL AUTHORITATIVE JOBS
================================================================================

The authoritative Mode-I formulation remains:

    f42_mixed_uel.for

Serial reference execution:

    exactly 1 CPU

These jobs provide the authoritative scientific convergence/reference sequence.

Do not alter:
- formulation;
- geometry;
- mesh;
- boundary conditions;
- material parameters;
- phase-field parameters;
- increment controls;
- solver controls

merely to enable parallel execution.

================================================================================
SHARED-MEMORY MULTI-THREADING QUALIFICATION & SCALING (8-THREAD SMP QUALIFIED)
================================================================================

The shared-memory parallelization question is:

"Can the exact original authoritative dual-element formulation
f42_mixed_uel.for reproduce the serial solution when Abaqus uses shared-memory
threads inside ONE shared-memory process (8-thread SMP qualified, 16-thread unqualified, 4-thread not approved)?"

Therefore the intended configuration is:

    1 MPI PROCESS / RANK
    8 SHARED-MEMORY THREADS (or 16-thread qualification candidate when authorized)

This is NOT a true multi-rank MPI qualification.

Do NOT configure the original f42_mixed_uel.for as multi-rank MPI (e.g. 4x1, 8x1),
because previous evidence established that the mutable
COMMON /CB_STATE_TRANS/ architecture is not qualified for distributed-memory
MPI.

Job 1401531.mmaster02 remains evidence that true multi-rank MPI of the original
dual formulation is unqualified.

================================================================================
REQUIRED ABAQUS TELEMETRY
================================================================================

For a shared-memory multi-threaded job, acceptable telemetry must demonstrate
an equivalent of:

    1 MPI rank x 8 threads (qualified SMP execution; 16-thread unqualified, 4-thread not approved)

or:

    1 domain/process using N threads

The exact supported Abaqus 2023 cluster launch syntax must be verified from the
actual environment rather than guessed.

Do NOT classify multi-rank MPI as the desired execution mode for the original UEL.

If the solver launches distributed MPI processes, terminate the qualification
classification as:

    WRONG_PARALLEL_MODE / TRUE_MPI_NOT_ALLOWED_FOR_ORIGINAL_DUAL_UEL

Do not use that result as serial/thread parity evidence.

================================================================================
THREAD-SAFETY STATUS
================================================================================

Shared address space does NOT automatically mean the original UEL is thread-safe.

The original formulation contains mutable shared COMMON state.

Therefore its starting classification is:

    THREAD_SAFETY_UNVERIFIED

Multi-threaded jobs must be evaluated strictly with parity checks.

Potential hazards include:
- simultaneous COMMON writes;
- changed UEL call ordering;
- race conditions;
- phase/mechanical co-located element ordering differences;
- nondeterministic d/H trial-state exchange.

Do not claim parallelization success from Exit_status=0 alone.

================================================================================
THREAD-PARITY QUALIFICATION
================================================================================

A multi-thread candidate must be compared against a corresponding 1-CPU run.

ONLY intended change:

    CPU execution:
        1 CPU serial
            ->
        8 CPU shared-memory threads (or 16-thread qualification candidate; 4-thread not approved)

Freeze everything else.

Compare:
- complete F-u response;
- K0 using identical extraction;
- Fmax;
- u(Fmax);
- final RF;
- dmax;
- Hmax;
- selected d/H spatial values;
- crack localization/path;
- increment history;
- Newton iteration counts;
- cutbacks;
- achieved displacement;
- external work integral F du;
- warnings/singularities;
- walltime;
- CPU time;
- memory.

Any meaningful scientific-response difference must be classified as thread
sensitivity or race/order sensitivity, NOT as physical mesh behavior.

================================================================================
DETERMINISM REQUIREMENT
================================================================================

One serial/thread parity pass is insufficient to declare thread safety.

Required qualification progression:

Stage A:
    one multi-threaded run versus its exact 1-CPU twin.

If Stage A passes:

Stage B:
    repeat the SAME multi-threaded case independently.

Compare the two N-thread runs for deterministic identity/tight numerical parity.

Only after both stages pass may classification progress to:

    THREAD_PARITY_PASS
    THREAD_DETERMINISM_PASS
    THREAD_PARALLELIZATION_QUALIFIED

Scaling to 8-thread and 16-thread shared-memory execution is authorized for
scaling/parity evaluation on larger fixed, reference, and adaptive meshes,
provided single-rank shared-memory threading (1 MPI rank x 8 threads qualified SMP, or 16 threads for authorized qualification) is maintained.

================================================================================
TRUE MPI BRANCH
================================================================================

Preserve the separate MPI research finding:

Original f42_mixed_uel.for:
    serial = authoritative
    true multi-rank MPI = NOT QUALIFIED

Unified/compatibility UEL:
    true MPI self-parity demonstrated
    exact dual-equivalence NOT established

Do not mix unified MPI results into the authoritative Mode-I mesh-convergence
sequence.

The unified branch remains a separate development branch and must not replace
the original formulation without explicit scientific approval.

================================================================================
ACTIVE SLOT MANAGEMENT
================================================================================

Before each qsub query exact current project jobs.

Count:

    SERIAL_ACTIVE
    PARALLEL_THREAD_ACTIVE
    TOTAL_ACTIVE

Rules:

1. TOTAL_ACTIVE is governed by scientific usefulness and queue limits:
   10 simultaneous active jobs is a demonstrated minimum floor.
   Controlled expansion up to 15â€“20 active Mode-I jobs is permitted during
   the September-9 window for validated, scientifically justified cases.

2. Existing valid jobs are grandfathered until terminal.
   Do NOT cancel them.

3. Execution mode: 1-CPU serial serves as the authoritative reference anchor;
   8-thread shared-memory SMP is empirically qualified for active Mode-I production;
   16-thread shared-memory execution remains unqualified pending independent Stage-A/B proof;
   4-thread shared-memory execution is not part of the active approved execution path;
   distributed multi-rank MPI remains strictly disqualified for f42_mixed_uel.for.

4. High throughput is driven by concurrent independent jobs across available nodes.

5. Strictly NO redundant or dummy jobs just to consume resources or test capacity.

6. Do not launch work merely because a slot is free; every job must have an
   explicit scientific question, gate alignment, and pre-declared acceptance criteria.

7. Every parallel/threaded run must correspond to an explicit serial parity reference
   or scaling benchmark.

================================================================================
HISTORICAL CONCURRENCY DEMONSTRATION -- NOT CURRENT SCHEDULER STATE
================================================================================

The jobs below historically demonstrated at least 10 simultaneous Mode-I jobs and
97 CPUs in R state. They MUST NOT be described as currently active unless a fresh
`qstat -u pr21vyci` snapshot independently shows them in Q/R:
- 1403368.mmaster02: PK_M1_C7_2PCT (1 CPU serial)
- 1403369.mmaster02: PK_M1_FIX_H0015 (8 threads)
- 1403370.mmaster02: PK_M1_NOM_1PCT_71K (8 threads)
- 1403371.mmaster02: PK_M1_NOM_1PCT_71K (16 threads)
- 1403372.mmaster02: PK_M1_C7_2PCT (8 threads)
- 1403373.mmaster02: PK_M1_C7_2PCT (16 threads)
- 1403374.mmaster02: PK_M1_H0030 (8 threads)
- 1403375.mmaster02: PK_M1_H0020 (8 threads)
- 1403376.mmaster02: PK_M1_H0015 (8 threads)
- 1403377.mmaster02: PK_M1_H0015 (16 threads)

Preserve these jobs as historical evidence. Never cancel/modify/restart an existing
valid job. Current scheduler truth always comes from the fresh scheduler query.

================================================================================
EXPANSION AND QUALIFICATION SUBMISSION CRITERIA
================================================================================

Additional submissions within the 15â€“20 job guideline must satisfy:
- Explicit scientific purpose (e.g. 8-thread scaling/parity or deterministic repeats on large meshes,
  or PBS post-processing/extractions);
- Pre-declared acceptance criteria;
- Exact .inp and f42_mixed_uel.for hashes verified;
- Input syntax / datacheck preflight verified;
- Single-rank shared-memory threading confirmed (1 MPI rank x 8 threads qualified SMP, or 16 threads for authorized qualification);
- Dual-channel notification integration verified;
- Qualified manifest and technical preflight recorded; per-job human authorization is removed.

================================================================================
BRIDGE RESPONSE RULE
================================================================================

MODE-I FUNDAMENTALS GOVERNANCE (POST-17-SEPTEMBER-2026 SUPERVISOR MEETING):
- Active scientific phase: MODE1_GATE6B_ACTIVE_EVALUATION_AND_CONTINUATION.
- 71,320-mesh stiffness defect is RESOLVED_AND_CLOSED.
- 13,941 vs 71,320 element-count reproduction is CLOSED_WITH_SUPERVISOR_ACCEPTED_PUBLICATION_LIMITATION.
- Priority 1 is UEL Energy Formulation and Output Audit (Status: UEL_ENERGY_OUTPUT_QUALIFIED_MECHANICALLY_NONINVASIVE).
- Actionable independent work:
  * Inspect authoritative Fortran UEL source (f42_mixed_uel.for) and weak form;
  * Derive energy expressions and global energy balance identity;
  * Plan mechanically non-invasive energy output exposing UEL energy;
  * Update thesis/report continuously before 08-Oct-2026 meeting.
- STOP / RESUME RULES:
  * Do NOT assume zero Q/R jobs means stop or park. If Mode-I fundamentals tasks (energy audit, derivation, offline analysis, report updates) are actionable, CONTINUE that work!
  * With Q/R jobs running: leave them untouched. If independent offline analysis, derivations, or report work remain, continue that work!
  * Reply "stop" ONLY when all currently justified independent work is already executing or complete AND further progress genuinely depends on a running job or external result.
  * When a job becomes terminal: retrieve actual scheduler/solver evidence; evaluate scientifically against predeclared criteria; update report/provenance; do NOT return stop just because Exit_status=0.
  * Do NOT reopen 13,941 target matching, author inquiries, Mode-II, or visualization integration (Gate 7).

Do not choose the scheduler polling interval.

================================================================================
"@

$ModeIFundamentalsKickoffInstruction = @"
Resume POST-MEETING MODE-I FUNDAMENTALS QUALIFICATION.
Follow the new supervisor roadmap established on 17 September 2026:
Priority 1 is UEL ENERGY FORMULATION AND OUTPUT AUDIT.
1. Inspect the authoritative Fortran UEL equations and source (f42_mixed_uel.for) before editing anything.
2. Derive the energy expressions actually consistent with the implemented weak form (stored elastic/strain energy, phase-field/fracture surface energy, dissipated fracture contribution, external work, and other model terms) with explicit units and sign conventions.
3. Establish the correct global energy-balance identity for this implementation.
4. Determine how these terms should be exposed through Abaqus UEL ENERGY and/or rigorously defined state/output variables without double counting co-located UEL/visualization layers.
5. Any energy-output modification must be mechanically non-invasive: RHS, AMATRX, constitutive evolution, and existing STATEV semantics must remain unchanged. Prove before/after mechanical parity.
6. Before expensive Mode-I reruns, complete: source audit -> derivation -> code review -> compile -> datacheck -> smallest meaningful verification -> authoritative Mode-I verification.
Do not launch a simulation merely to obtain a plot before the energy definitions and output implementation are scientifically justified.
7. After the energy baseline is qualified, execute multifaceted Mode-I convergence (complete F-u, K0, global energy balance, spatial d(x) profiles, temporal convergence, length-scale sensitivity).
8. Once baseline energy is qualified, activate Mode-I state-transfer energy-preservation study.
9. Continuously incorporate all findings into the growing Mode-I thesis/report before the 08 October 2026 meeting.
10. Strict scope constraints:
- Do NOT reopen the 71,320 stiffness anomaly (RESOLVED_AND_CLOSED).
- Do NOT reopen the exact 13,941 element-count hunt (SUPERVISOR_ACCEPTED_REPRODUCTION_LIMITATION_CLOSED).
- Do NOT start Mode-II, mixed mode, or higher-complexity benchmarks (HOLD).
- Do NOT start Gate-7 visualization / ABAQUSER integration (HOLD).
Write Finished when the instructed unit of work is complete.
"@

# Alias for backwards compatibility with any existing caller
$ModeIResolutionKickoffInstruction = $ModeIFundamentalsKickoffInstruction

# ------------------------------------------------------------------------------
# Conversation lifecycle
#
# IMPORTANT:
# agy.exe does NOT accept an arbitrary new GUID via --conversation.
#
# - Explicit -ConversationId: reuse that already-existing Antigravity conversation.
# - Pending resume with no new prompt: reuse the saved conversation_id.
# - New workflow with a prompt and no explicit ID: leave ConversationId blank;
#   the first agy.exe call is made WITHOUT --conversation, allowing agy to create
#   a real conversation. The returned conversation_id is then captured and reused.
# ------------------------------------------------------------------------------
$ConversationIdSource = "explicit"

if ([string]::IsNullOrWhiteSpace($ConversationId)) {
    $hasNewPrompt = (
        -not [string]::IsNullOrWhiteSpace($InitialPrompt) -or
        -not [string]::IsNullOrWhiteSpace($InitialPromptFile)
    )

    if (-not $hasNewPrompt -and (Test-Path -LiteralPath $StateFile)) {
        try {
            $resumeMeta = Get-Content -LiteralPath $StateFile -Raw | ConvertFrom-Json
            $savedProfile = [string]$resumeMeta.agy_profile
            $currentProfile = Get-CurrentAgyProfileName

            if (
                $resumeMeta.loop_status -eq "PENDING_NEXT_TURN" -and
                -not [string]::IsNullOrWhiteSpace([string]$resumeMeta.conversation_id)
            ) {
                if (-not [string]::IsNullOrWhiteSpace($savedProfile) -and $savedProfile -ne $currentProfile) {
                    Write-Host ""
                    Write-Host "[NOTICE] Saved conversation was created under profile '$savedProfile', but current active profile is '$currentProfile'." -ForegroundColor Yellow
                    Write-Host "Cross-account conversation reuse is prohibited. Starting a fresh conversation under '$currentProfile'." -ForegroundColor Yellow
                    Write-Host ""
                    $ConversationId = $null
                    $ConversationIdSource = "fresh-profile-mismatch"
                } else {
                    $ConversationId = [string]$resumeMeta.conversation_id
                    $ConversationIdSource = "resume-state"
                }
            }
        }
        catch {
            # Do not trust malformed/stale state. A later no-conversation agy call
            # will create a new conversation if new work is actually supplied.
        }
    }

    if ([string]::IsNullOrWhiteSpace($ConversationId)) {
        $ConversationIdSource = "agy-create-on-first-turn"
    }
}


function Write-LoopLog($Turn, $Tier, $Action, $Message) {
    $timestamp = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
    $logLine = "[$timestamp] [Turn: $Turn] [Tier: $Tier] [Action: $Action] $Message"
    Add-Content -Path $LogFile -Value $logLine -Encoding utf8
    Write-Host $logLine -ForegroundColor Cyan
}

function Save-LoopStatus($Turn, $Status, $Tier, $Action, $Details) {
    $timestamp = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
    $currentProf = Get-CurrentAgyProfileName
    $obj = [PSCustomObject]@{
        timestamp       = $timestamp
        turn            = $Turn
        conversation_id = $ConversationId
        agy_profile     = $currentProf
        status          = $Status
        tier            = $Tier
        action          = $Action
        details         = $Details
    }
    $json = $obj | ConvertTo-Json -Compress
    [System.IO.File]::WriteAllText($StatusFile, $json, [System.Text.UTF8Encoding]::new($false))
}

function Get-LivePbsJobs {
    [CmdletBinding()]
    param(
        [string]$User = "pr21vyci",
        [string]$HostAlias = "tu_freiberg",
        [string]$ConfigPath = "$env:USERPROFILE\.ssh\codex_config"
    )

    $sshCommand = Get-Command ssh.exe -ErrorAction Stop
    $sshPath = $sshCommand.Source

    $remoteCommand = "qstat -u $User"

    $savedErrorActionPreference = $ErrorActionPreference
    $hadNativePreference = $null -ne (Get-Variable -Name PSNativeCommandUseErrorActionPreference -ErrorAction SilentlyContinue)
    if ($hadNativePreference) {
        $savedNativePreference = $PSNativeCommandUseErrorActionPreference
    }

    try {
        $ErrorActionPreference = "Continue"
        if ($hadNativePreference) {
            $PSNativeCommandUseErrorActionPreference = $false
        }

        $raw = & $sshPath -n -T -o BatchMode=yes -o ConnectTimeout=20 -F $ConfigPath $HostAlias $remoteCommand 2>&1
        $exitCode = $LASTEXITCODE
    }
    finally {
        $ErrorActionPreference = $savedErrorActionPreference
        if ($hadNativePreference) {
            $PSNativeCommandUseErrorActionPreference = $savedNativePreference
        }
    }

    $cleanRaw = @(
        $raw |
        ForEach-Object {
            $_.ToString()
        } |
        Where-Object {
            $_ -notmatch "post-quantum key exchange algorithm"
        }
    )

    $text = ($cleanRaw | Out-String).Trim()

    if ($exitCode -ne 0) {
        throw "Failed to query live scheduler ($remoteCommand):`n$text"
    }

    $lines = $text -split "`r?`n"

    $liveJobs = @()
    $runningJobs = @()
    $queuedJobs = @()
    $finishedJobs = @()
    $otherJobs = @()

    foreach ($line in $lines) {
        $trimmed = $line.Trim()
        if (-not $trimmed -or $trimmed.StartsWith("Job id") -or $trimmed.StartsWith("Job ID") -or $trimmed.StartsWith("---") -or $trimmed.StartsWith("mmaster02:")) {
            continue
        }

        $parts = ($trimmed -split '\s+') | Where-Object { $_ -ne '' }
        if ($parts.Count -ge 5) {
            $rawJobId = $parts[0] -replace '\*$', ''

            # State determination:
            # In 6-col format (qstat -x <id>): [JobId, Name, User, TimeUse, S, Queue] -> S is index 4
            # In 11-col format (qstat -u <user>): [JobId, Username, Queue, Jobname, SessID, NDS, TSK, Memory, ReqTime, S, ElapTime] -> S is index 9
            $state = $null
            if ($parts.Count -ge 10 -and $parts[9] -match '^[RQHWFCEBT]$') {
                $state = $parts[9].ToUpper()
            }
            elseif ($parts.Count -ge 5 -and $parts[4] -match '^[RQHWFCEBT]$') {
                $state = $parts[4].ToUpper()
            }
            else {
                for ($i = 1; $i -lt $parts.Count; $i++) {
                    if ($parts[$i] -match '^[RQHWFCEBT]$') {
                        $state = $parts[$i].ToUpper()
                        break
                    }
                }
            }

            if ($rawJobId -match '^\d+(\.\w+)?$') {
                $jobObj = [PSCustomObject]@{
                    JobId = $rawJobId
                    State = $state
                    Line  = $trimmed
                }
                $liveJobs += $jobObj

                if ($state -eq 'R') {
                    $runningJobs += $rawJobId
                }
                elseif ($state -in @('Q', 'H', 'W')) {
                    $queuedJobs += $rawJobId
                }
                elseif ($state -in @('F', 'C', 'E')) {
                    $finishedJobs += $rawJobId
                }
                else {
                    $otherJobs += $rawJobId
                }
            }
        }
    }

    return [PSCustomObject]@{
        LiveJobs     = $liveJobs
        RunningJobs  = $runningJobs
        QueuedJobs   = $queuedJobs
        WaitableJobs = @($runningJobs + $queuedJobs)
        FinishedJobs = $finishedJobs
        OtherJobs    = $otherJobs
        RawOutput    = $text
    }
}

function Get-ActivePbsJobIds {
    $sshConfig = Join-PathStrict -Path $env:USERPROFILE -ChildPath ".ssh\codex_config"

    $savedErrorActionPreference = $ErrorActionPreference
    $hadNativePreference = $null -ne (Get-Variable -Name PSNativeCommandUseErrorActionPreference -ErrorAction SilentlyContinue)
    if ($hadNativePreference) {
        $savedNativePreference = $PSNativeCommandUseErrorActionPreference
    }

    try {
        $ErrorActionPreference = "Continue"
        if ($hadNativePreference) {
            $PSNativeCommandUseErrorActionPreference = $false
        }

        $result = & ssh `
            -n -T `
            -o BatchMode=yes `
            -o ConnectTimeout=20 `
            -F $sshConfig `
            tu_freiberg `
            "qstat -u pr21vyci" 2>&1

        $exitCode = $LASTEXITCODE
    }
    finally {
        $ErrorActionPreference = $savedErrorActionPreference
        if ($hadNativePreference) {
            $PSNativeCommandUseErrorActionPreference = $savedNativePreference
        }
    }

    # Remove harmless OpenSSH warnings from stderr/stdout mixing
    $cleanResult = @(
        $result |
        ForEach-Object {
            $_.ToString()
        } |
        Where-Object {
            $_ -notmatch "post-quantum key exchange algorithm"
        }
    )

    $text = ($cleanResult | Out-String).Trim()

    if ($exitCode -ne 0) {
        throw "qstat failed with exit code $($exitCode):`n$text"
    }

    return @(
        $cleanResult |
        ForEach-Object {
            $line = $_.ToString().Trim()
            if ($line -match '^\d+(\.\w+)?$') {
                $line
            }
            else {
                $firstCol = ($line -split '\s+')[0]
                if ($firstCol -match '^\d+(\.\w+)?$') {
                    $firstCol
                }
            }
        } |
        Where-Object {
            $_ -match '^\d+(\.\w+)?$'
        }
    )
}


function Get-ExactPbsJobIdsFromText {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [AllowEmptyString()]
        [string]$Text
    )

    if ([string]::IsNullOrWhiteSpace($Text)) {
        return @()
    }

    # Match ONLY PBS IDs that already explicitly contain ".mmaster02".
    # Never manufacture job IDs from scientific numbers such as
    # 0.00247551, 0.05551289, reaction forces, displacements, etc.
    $pattern = '(?<![A-Za-z0-9_.])(?<id>1[3-9]\d{5,6}\.mmaster02)(?![A-Za-z0-9_.])'

    return @(
        [regex]::Matches($Text, $pattern) |
        ForEach-Object {
            $_.Groups['id'].Value
        } |
        Where-Object {
            $_ -match '^1[3-9]\d{5,6}\.mmaster02$'
        } |
        Select-Object -Unique
    )
}

function Get-FreshProductionPbsJobIdFromText {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [AllowEmptyString()]
        [string]$Text
    )

    if ([string]::IsNullOrWhiteSpace($Text)) {
        return $null
    }

    # Prefer explicit production-solve declarations from the latest Antigravity response.
    # This prevents a stale ACTIVE_TASK.json job (for example an old datacheck) from
    # overriding a newer exact production job that was just submitted.
    $patterns = @(
        '(?im)Production Solve Submission\s*\(\s*`?(?<id>1[3-9]\d{5,6}\.mmaster02)`?\s*\)',
        '(?im)production solve job\s*\(\s*`?(?<id>1[3-9]\d{5,6}\.mmaster02)`?',
        '(?im)authorized production solve job\s*\(\s*`?(?<id>1[3-9]\d{5,6}\.mmaster02)`?',
        '(?im)^\s*-\s*\*\*Exact PBS Job ID\*\*:\s*\*\*`?(?<id>1[3-9]\d{5,6}\.mmaster02)`?\*\*\s*$'
    )

    $candidates = New-Object System.Collections.Generic.List[string]

    foreach ($pattern in $patterns) {
        foreach ($match in [regex]::Matches($Text, $pattern)) {
            $id = $match.Groups['id'].Value
            if ($id -match '^1[3-9]\d{5,6}\.mmaster02$' -and -not $candidates.Contains($id)) {
                [void]$candidates.Add($id)
            }
        }
    }

    # If several exact production IDs are mentioned, the last explicit production
    # declaration in the latest response is the best fresh candidate.
    if ($candidates.Count -gt 0) {
        return $candidates[$candidates.Count - 1]
    }

    return $null
}

function Invoke-DirectPbsQuery {
    param(
        [Parameter(Mandatory = $true)]
        [string[]]$JobIds
    )

    if (-not $JobIds -or $JobIds.Count -eq 0) {
        throw "Invoke-DirectPbsQuery called without PBS job IDs."
    }

    $sshConfig = Join-PathStrict -Path $env:USERPROFILE -ChildPath ".ssh\codex_config"

    if (-not (Test-Path -LiteralPath $sshConfig)) {
        throw "SSH config not found: $sshConfig"
    }

    $remoteCommand = "qstat -x " + ($JobIds -join " ")

    Write-Host "[SCHEDULER] Running direct PBS query:"
    Write-Host "[SCHEDULER] ssh -F $sshConfig tu_freiberg `"$remoteCommand`""

    $savedErrorActionPreference = $ErrorActionPreference
    $hadNativePreference = $null -ne (Get-Variable -Name PSNativeCommandUseErrorActionPreference -ErrorAction SilentlyContinue)
    if ($hadNativePreference) {
        $savedNativePreference = $PSNativeCommandUseErrorActionPreference
    }

    try {
        $ErrorActionPreference = "Continue"
        if ($hadNativePreference) {
            $PSNativeCommandUseErrorActionPreference = $false
        }

        $output = & ssh `
            -n -T `
            -o BatchMode=yes `
            -o ConnectTimeout=20 `
            -F $sshConfig `
            tu_freiberg `
            $remoteCommand 2>&1

        $exitCode = $LASTEXITCODE
    }
    finally {
        $ErrorActionPreference = $savedErrorActionPreference
        if ($hadNativePreference) {
            $PSNativeCommandUseErrorActionPreference = $savedNativePreference
        }
    }

    $cleanLines = @(
        $output |
        ForEach-Object { $_.ToString() } |
        Where-Object {
            $_ -notmatch "post-quantum key exchange algorithm"
        }
    )

    $text = ($cleanLines | Out-String).Trim()

    if ($exitCode -ne 0) {
        throw "Direct qstat query failed with exit code $($exitCode):`n$text"
    }

    if ([string]::IsNullOrWhiteSpace($text)) {
        throw "Direct qstat query returned exit code 0 but no scheduler payload for: $($JobIds -join ', ')"
    }

    return $text
}

# AGY_QUOTA_GUARD_V1 -----------------------------------------------------------

function Get-AgyFiveHourQuotaSnapshot {
    # Use the same isolated saved-profile reader as startup inventory.
    # The global checker can discover unrelated/stale credentials after AGY runs.
    $profile = $script:RunLockedAgyProfile
    if ($profile -notmatch '^account[1-5]$') { throw 'Cannot verify quota profile.' }
    $ag = Get-AgyQuotaProviderJson -Profile $profile

    $selected = @()

    foreach ($group in @($ag.groups)) {
        $groupName = [string]$group.name
        if ($groupName -notmatch $QuotaGroupRegex) {
            continue
        }

        foreach ($bucket in @($group.buckets)) {
            $window = ([string]$bucket.window).Trim().ToLowerInvariant()
            $label  = ([string]$bucket.label).Trim().ToLowerInvariant()

            $isFiveHour = (
                $window -eq "5h" -or
                $window -eq "five_hour" -or
                $window -eq "five-hour" -or
                $window -eq "five hour" -or
                $label -match "five\s*hour"
            )

            if (-not $isFiveHour) {
                continue
            }

            $remainingPct = $null

            if ($null -ne $bucket.remaining_pct) {
                $remainingPct = [double]$bucket.remaining_pct
            }
            elseif ($null -ne $bucket.remaining_fraction) {
                $remainingPct = 100.0 * [double]$bucket.remaining_fraction
            }
            elseif ($null -ne $bucket.remainingFraction) {
                $remainingPct = 100.0 * [double]$bucket.remainingFraction
            }
            elseif ($null -ne $bucket.used_pct) {
                $remainingPct = 100.0 - [double]$bucket.used_pct
            }

            if ($null -eq $remainingPct) {
                continue
            }

            if ($remainingPct -lt 0.0) { $remainingPct = 0.0 }
            if ($remainingPct -gt 100.0) { $remainingPct = 100.0 }

            $selected += [PSCustomObject]@{
                group         = $groupName
                window        = [string]$bucket.window
                label         = [string]$bucket.label
                remaining_pct = [math]::Round($remainingPct, 6)
                used_pct      = if ($null -ne $bucket.used_pct) { [double]$bucket.used_pct } else { [math]::Round(100.0 - $remainingPct, 6) }
                resets_at     = [string]$bucket.resets_at
            }
        }
    }

    if ($selected.Count -eq 0) {
        throw "No matching Antigravity five-hour quota bucket was found for group regex '$QuotaGroupRegex'."
    }

    $minimum = [double](($selected | Measure-Object -Property remaining_pct -Minimum).Minimum)

    return [PSCustomObject]@{
        checked_at_utc        = [DateTimeOffset]::UtcNow.ToString("o")
        source                = "isolated saved-profile quota: $profile"
        tier                  = [string]$ag.tier
        group_regex           = $QuotaGroupRegex
        five_hour_buckets     = $selected
        minimum_remaining_pct = [math]::Round($minimum, 6)
        threshold_pct         = [double]$QuotaStopThresholdPct
        below_threshold       = ($minimum -le [double]$QuotaStopThresholdPct)
    }
}

function Format-AgyQuotaSnapshot {
    param($Snapshot)

    if ($null -eq $Snapshot) {
        return "Quota check was not scheduled for this turn."
    }

    $lines = @()
    $lines += "Source: $($Snapshot.source)"
    $lines += "Checked UTC: $($Snapshot.checked_at_utc)"
    if (-not [string]::IsNullOrWhiteSpace([string]$Snapshot.tier)) {
        $lines += "Tier: $($Snapshot.tier)"
    }

    foreach ($bucket in @($Snapshot.five_hour_buckets)) {
        $resetText = if ([string]::IsNullOrWhiteSpace([string]$bucket.resets_at)) {
            "reset=unknown"
        }
        else {
            "reset=$($bucket.resets_at)"
        }

        $lines += ("5h [{0}] remaining={1:N3}% used={2:N3}% {3}" -f `
            $bucket.group, `
            [double]$bucket.remaining_pct, `
            [double]$bucket.used_pct, `
            $resetText)
    }

    $lines += ("Minimum selected 5h remaining: {0:N3}%" -f [double]$Snapshot.minimum_remaining_pct)
    $lines += ("Stop threshold: <= {0:N3}%" -f [double]$Snapshot.threshold_pct)
    $lines += "Below threshold: $($Snapshot.below_threshold)"

    return ($lines -join "`n")
}

function Write-QuotaRotationInitialPrompt {
    param(
        [Parameter(Mandatory = $true)][int]$Turn,
        [Parameter(Mandatory = $true)][string]$LastResponse,
        [Parameter(Mandatory = $true)][string]$NextInstruction,
        [Parameter(Mandatory = $true)][string]$QuotaText
    )

    $promptPath = $QuotaInitialPromptFile
    $promptDir = Split-Path -Parent $promptPath

    if (-not (Test-Path -LiteralPath $promptDir)) {
        New-Item -ItemType Directory -Path $promptDir -Force | Out-Null
    }

    if (Test-Path -LiteralPath $promptPath) {
        $stamp = Get-Date -Format "yyyyMMdd_HHmmss"
        $promptBackup = "$promptPath.backup_before_quota_rotation_$stamp"
        Copy-Item -LiteralPath $promptPath -Destination $promptBackup -Force
        Write-Host "[QUOTA] Previous INITIAL_PROMPT backed up to:" -ForegroundColor DarkGray
        Write-Host "[QUOTA] $promptBackup" -ForegroundColor DarkGray
    }

    $handoff = @"
QUOTA-ROTATION CONTINUATION -- START A NEW AGY ACCOUNT AND A NEW ANTIGRAVITY CONVERSATION

The previous autonomous controller run intentionally stopped after completing controller Turn $Turn
because the configured Antigravity five-hour quota guard was triggered.

Previous Antigravity conversation ID:
$ConversationId

IMPORTANT:
- Continue the SAME project workflow.

---------------- PROJECT / THESIS ALIGNMENT GUARD ----------------
$ProjectAlignmentGuard
-------------- END PROJECT / THESIS ALIGNMENT GUARD --------------

- Do not try to resume the previous Antigravity conversation under the new Google account.
- Start a NEW Antigravity conversation.
- Do not repeat completed scientific/HPC work merely because the CLI account changed.
- Preserve exact PBS job IDs, scientific provenance, validation states, and existing project artifacts.
- The instruction below was already determined from the completed previous turn and is the next action to execute.

---------------- PREVIOUS ANTIGRAVITY TURN RESULT ----------------
$LastResponse
-------------- END PREVIOUS ANTIGRAVITY TURN RESULT --------------

---------------- QUOTA RESULT ----------------
$QuotaText
-------------- END QUOTA RESULT --------------

---------------- NEXT INSTRUCTION ----------------
$NextInstruction
-------------- END NEXT INSTRUCTION --------------

Execute the NEXT INSTRUCTION above under the new Antigravity CLI account.
Follow the project's existing safety, HPC authorization, notification, scheduler, artifact,
and scientific-validation rules.
"@

    $tmp = "$promptPath.tmp"
    [System.IO.File]::WriteAllText($tmp, $handoff, [System.Text.UTF8Encoding]::new($false))
    Move-Item -LiteralPath $tmp -Destination $promptPath -Force

    return $promptPath
}

# END AGY_QUOTA_GUARD_V1 -------------------------------------------------------
# AGY_AUTO_PROFILE_ROTATION_V1 -----------------------------------------------

$script:LastAutoRotatedAgyProfile = $null


function Sync-AndVerifyAgyProfile {
    [CmdletBinding()]
    param([int]$Turn)

    Ensure-AuthoritativeAgyProfile "Sync-AndVerifyAgyProfile"
    return (Get-ManuallySelectedAgyProfile)
}

function Get-CurrentAgyProfileName {
    $state = Get-AgyProfileState
    if ($state.ActiveProfile) {
        return $state.ActiveProfile
    }
    if ($state.ActiveFile) {
        return $state.ActiveFile
    }
    if ($state.LastSwitch) {
        return $state.LastSwitch
    }
    return $null
}


function Switch-ToNextAgyProfile {
    param([string]$QuotaError = $script:LastAgyQuotaError)
    if ($EnableSmartAgyProfileSelection) {
        $oldProfile = Get-CurrentAgyProfileName
        if ($QuotaError) { Set-AgySmartQuotaCooldown -Profile $oldProfile -Reason 'ACTUAL_QUOTA_ERROR' -Message $QuotaError }
        return (Invoke-AgySmartSelection -ExcludeProfile $oldProfile -Reason 'QUOTA_TRIGGER')
    }
    if (-not $EnableAutomaticAgyProfileRotation) {
        throw "Automatic AGY profile rotation is disabled."
    }

    if (
        $null -eq $AgyProfileRotationOrder -or
        $AgyProfileRotationOrder.Count -eq 0
    ) {
        throw "AgyProfileRotationOrder is empty."
    }

    if (-not (Get-Command agy-profile -ErrorAction SilentlyContinue)) {
        throw "agy-profile command is unavailable."
    }


    $current = Get-CurrentAgyProfileName
    $target = $null


    if ([string]::IsNullOrWhiteSpace($current)) {

        # Safe deterministic fallback.
        $target = $AgyProfileRotationOrder[0]
    }
    else {

        $index = [Array]::IndexOf(
            $AgyProfileRotationOrder,
            $current
        )

        if ($index -lt 0) {
            $target = $AgyProfileRotationOrder[0]
        }
        else {
            $target = $AgyProfileRotationOrder[
                ($index + 1) % $AgyProfileRotationOrder.Count
            ]
        }
    }


    Write-Host ""
    Write-Host "[PROFILE] Automatic AGY account rotation" -ForegroundColor Yellow
    Write-Host "[PROFILE] Current: $current"
    Write-Host "[PROFILE] Target : $target"


    $savedEap = $ErrorActionPreference

    try {
        $ErrorActionPreference = "Continue"

        $switchOutput = & agy-profile switch $target -Force 2>&1
    }
    finally {
        $ErrorActionPreference = $savedEap
    }


    $switchText = ($switchOutput | Out-String).Trim()

    if ($switchText) {
        Write-Host "[PROFILE] $switchText" -ForegroundColor DarkGray
    }


    Start-Sleep -Seconds 1

    $verified = Get-CurrentAgyProfileName

    if (
        -not [string]::IsNullOrWhiteSpace($verified) -and
        $verified -ne $target
    ) {
        throw (
            "agy-profile switch verification failed. " +
            "Requested '$target', detected '$verified'."
        )
    }


    $oldConversationId = $ConversationId

    $script:LastAutoRotatedAgyProfile = $target

    # CRITICAL:
    # An Antigravity conversation belongs to the previous account.
    # Never reuse it after switching profiles.
    $script:ConversationId = ""
    $script:ConversationIdSource = "agy-create-on-first-turn"
    # Deliberate switch must update the SAME authoritative profile variable
    # checked at TURN_START, PRE_AGY and TURN_END; otherwise it is reverted.
    $script:RunLockedAgyProfile = $target
    $script:AuthoritativeAgyProfile = $target
    $script:SelectedAgyProfile = $target
    $script:PinnedAgyProfile = $target

    return [PSCustomObject]@{
        previous_profile        = $current
        new_profile             = $target
        previous_conversation   = $oldConversationId
        new_conversation_policy = "agy-create-on-first-turn"
    }
}


function Test-IsAgyQuotaLimitError {
    param(
        [string]$Message
    )

    if ([string]::IsNullOrWhiteSpace($Message)) {
        return $false
    }

    return (
        $Message -match '(?i)HTTP\s*429' -or
        $Message -match '(?i)status\s*429' -or
        $Message -match '(?i)RESOURCE_EXHAUSTED' -or
        $Message -match '(?i)quota\s+(?:exceeded|exhausted|reached)' -or
        $Message -match '(?i)individual\s+quota' -or
        $Message -match '(?i)weekly\s+(?:limit|quota)' -or
        $Message -match '(?i)hit your weekly limit' -or
        $Message -match '(?i)quota\s+limit' -or
        $Message -match '(?i)upgrade your subscription' -or
        $Message -match '(?i)rate.?limit(?:ed| exceeded)?' -or
        $Message -match '(?i)too many requests' -or
        $Message -match '(?i)usage\s+limit' -or
        $Message -match '(?i)plan.?limit'
    )
}


function Test-SalvageAgySessionFromDisk {
    param([string]$WorkspaceDir)
    if ($null -eq $turnStartTime) { return $null }
    return Get-AgyCompletedReceipt -WorkspaceDir $WorkspaceDir -Since $turnStartTime
}

function Test-IsAgyTransientNetworkOr503Error {
    param(
        [string]$Message
    )

    if ([string]::IsNullOrWhiteSpace($Message)) {
        return $false
    }

    return (
        $Message -match '(?i)\bUNAVAILABLE\b' -or
        $Message -match '(?i)code\s*503' -or
        $Message -match '(?i)service is currently unavailable' -or
        $Message -match '(?i)code\s*502' -or
        $Message -match '(?i)Bad Gateway' -or
        $Message -match '(?i)code\s*504' -or
        $Message -match '(?i)Gateway Timeout' -or
        $Message -match '(?i)wsarecv.*(?:connection was aborted|aborted by the software)' -or
        $Message -match '(?i)wsasend.*(?:forcibly closed|remote host)' -or
        $Message -match '(?i)forcibly closed by the remote host' -or
        $Message -match '(?i)connection was aborted by the software' -or
        $Message -match '(?i)connection reset by peer' -or
        $Message -match '(?i)streamGenerateContent.*(?:EOF|read tcp|write tcp|request failed)' -or
        $Message -match '(?i)transport error'
    )
}


# END AGY_AUTO_PROFILE_ROTATION_V1 -------------------------------------------

# AGY_SMART_PROFILE_SELECTION_V2 ------------------------------------------------
# The quotas are queried only BETWEEN AGY calls; never while agy.exe is active.
# No secrets/credentials are stored. The audit JSON stores only percentages,
# reset times, profile names, and selection reasons.
$script:SmartProfileStatePath = Join-PathStrict -Path $PadDir -ChildPath 'agy_smart_profiles.json'
$script:SmartCooldowns = @{}
$script:PendingSmartProfileContext = ''

function Read-AgySmartProfileState {
    if (-not (Test-Path -LiteralPath $script:SmartProfileStatePath)) { return }
    try {
        $state = Get-Content -LiteralPath $script:SmartProfileStatePath -Raw | ConvertFrom-Json
        foreach ($entry in @($state.cooldowns)) {
            if ($entry.profile -match '^account[1-5]$') {
                $script:SmartCooldowns[[string]$entry.profile] = [string]$entry.until_utc
            }
        }
    } catch {
        Write-Warning "Ignoring unreadable smart-profile state: $($_.Exception.Message)"
    }
}

function Write-AgySmartProfileState {
    param([object[]]$Snapshots = @(), [string]$Reason = '', [string]$Selected = '')
    $cd = @()
    foreach ($key in @($script:SmartCooldowns.Keys)) {
        $cd += [pscustomobject]@{ profile = $key; until_utc = $script:SmartCooldowns[$key] }
    }
    $record = [ordered]@{
        checked_at_utc = [DateTimeOffset]::UtcNow.ToString('o')
        reason         = $Reason
        selected       = $Selected
        quotas         = @($Snapshots)
        cooldowns      = @($cd)
    }
    $folder = Split-Path -Parent $script:SmartProfileStatePath
    if (-not (Test-Path -LiteralPath $folder)) { $null = New-Item -ItemType Directory -Path $folder -Force }
    $tmp = "$($script:SmartProfileStatePath).tmp"
    [System.IO.File]::WriteAllText($tmp, ($record | ConvertTo-Json -Depth 12), [System.Text.UTF8Encoding]::new($false))
    Move-Item -LiteralPath $tmp -Destination $script:SmartProfileStatePath -Force
}

function Get-AgyQuotaProviderJson {
    param([string]$Profile = '')
    if ($Profile) {
        if ($Profile -notmatch '^account[1-5]$') { throw 'Invalid quota profile.' }
        $worker = Join-Path $env:USERPROFILE 'OpenClawPAD\agy_profile_quota.py'
        $python = Join-Path $env:APPDATA 'uv\tools\ai-limit-checker\Scripts\python.exe'
        $file = Join-Path $env:USERPROFILE ".gemini\agy-profiles\$Profile\credential.dpapi"
        foreach ($required in @($worker,$python,$file)) {
            if (-not (Test-Path -LiteralPath $required)) { throw "Missing profile quota dependency: $required" }
        }
        Add-Type -AssemblyName System.Security
        try {
            $bytes = [Security.Cryptography.ProtectedData]::Unprotect([IO.File]::ReadAllBytes($file),$null,'CurrentUser')
            $credential = [Text.Encoding]::UTF8.GetString($bytes) | ConvertFrom-Json
            $request = @{credential=$credential;audit_only=$false} | ConvertTo-Json -Depth 10 -Compress
            $output = $request | & $python $worker 2>$null
            if ($LASTEXITCODE -ne 0) { throw 'Saved-profile quota worker failed.' }
            $result = $output | ConvertFrom-Json
            if ($result.antigravity.status -ne 'ok') { throw 'Saved-profile quota unavailable; account login may be required.' }
            $result.antigravity | Add-Member -NotePropertyName profile_identity -NotePropertyValue $result.identity
            return $result.antigravity
        } finally { $bytes=$null; $credential=$null; $request=$null; $output=$null }
    }
    $cmd = Get-Command $QuotaCheckerCommand -ErrorAction SilentlyContinue
    $argsForChecker = @($QuotaCheckerBaseArgs)
    if (-not $cmd -and $QuotaCheckerCommand -eq 'aichecker') {
        $cmd = Get-Command py -ErrorAction SilentlyContinue
        if ($cmd) { $argsForChecker = @('-m', 'ai_limit_checker') }
    }
    if (-not $cmd) { throw "Quota checker '$QuotaCheckerCommand' is not installed." }
    $oldEap = $ErrorActionPreference
    $nativePrefExists = $null -ne (Get-Variable PSNativeCommandUseErrorActionPreference -ErrorAction SilentlyContinue)
    if ($nativePrefExists) { $oldNativeEap = $PSNativeCommandUseErrorActionPreference }
    try {
        $ErrorActionPreference = 'Continue'
        if ($nativePrefExists) { $PSNativeCommandUseErrorActionPreference = $false }
        $raw = & $cmd.Source @argsForChecker --antigravity --json --no-cache 2>&1
        $code = $LASTEXITCODE
    } finally {
        $ErrorActionPreference = $oldEap
        if ($nativePrefExists) { $PSNativeCommandUseErrorActionPreference = $oldNativeEap }
    }
    $output = ($raw | Out-String).Trim()
    if ($code -ne 0) { throw "Quota checker exited $($code): $output" }
    $start = $output.IndexOf('{')
    if ($start -lt 0) { throw 'Quota checker returned no JSON.' }
    $root = $output.Substring($start) | ConvertFrom-Json
    $ag = $root.antigravity
    if ($null -eq $ag -and $root.groups) { $ag = $root }
    if ($null -eq $ag -or $ag.status -ne 'ok') { throw "Antigravity quota telemetry unavailable: $($ag.status)" }
    return $ag
}

function Get-AgySmartRemainingPct {
    param($Bucket)
    if ($null -ne $Bucket.remaining_pct) { $val = [double]$Bucket.remaining_pct }
    elseif ($null -ne $Bucket.remaining_fraction) { $val = 100.0 * [double]$Bucket.remaining_fraction }
    elseif ($null -ne $Bucket.remainingFraction) { $val = 100.0 * [double]$Bucket.remainingFraction }
    elseif ($null -ne $Bucket.used_pct) { $val = 100.0 - [double]$Bucket.used_pct }
    else { throw 'Missing remaining percentage in quota bucket.' }
    if ($val -lt 0.0 -or $val -gt 100.0) { throw 'Invalid quota percentage.' }
    return $val
}

function ConvertTo-AgySmartQuotaRecord {
    param([string]$Profile, $Payload, [string]$GroupRegex, [datetimeoffset]$Now = [DateTimeOffset]::UtcNow)
    $longBuckets = @()
    $shortBuckets = @()
    foreach ($group in @($Payload.groups)) {
        if ([string]$group.name -notmatch $GroupRegex) { continue }
        foreach ($bucket in @($group.buckets)) {
            $window = ([string]$bucket.window).Trim().ToLowerInvariant()
            $label = ([string]$bucket.label).Trim().ToLowerInvariant()
            $kind = if ($window -match '^(weekly|week|7d|five_day|five-day|5d|120h)$' -or
                       $label -match '(weekly|five.day|5.day)') { 'long' }
                    elseif ($window -match '^(5h|five_hour|five-hour|five hour)$' -or
                            $label -match 'five.hour') { 'short' }
                    else { '' }
            if (-not $kind) { continue }
            $remaining = Get-AgySmartRemainingPct -Bucket $bucket
            $reset = $null
            if (-not [string]::IsNullOrWhiteSpace([string]$bucket.resets_at)) {
                try { $reset = [DateTimeOffset]::Parse([string]$bucket.resets_at, [Globalization.CultureInfo]::InvariantCulture) }
                catch { throw "Invalid quota reset timestamp for $Profile." }
            }
            if ($kind -eq 'long') {
                if ($null -eq $reset) { throw "Missing longer-window reset timestamp for $Profile." }
                $longBuckets += [pscustomobject]@{ Remaining = $remaining; Reset = $reset }
            } else {
                $shortBuckets += [pscustomobject]@{ Remaining = $remaining; Reset = $reset }
            }
        }
    }
    if ($longBuckets.Count -eq 0) { throw "No five-day/weekly quota bucket for $Profile and group '$GroupRegex'." }
    # If the provider does not expose a five-hour window, it must not be
    # misclassified as having 100% short-term capacity.
    if ($shortBuckets.Count -eq 0) { throw "No five-hour quota bucket for $Profile and group '$GroupRegex'." }
    $mostConstrainedLong = $longBuckets | Sort-Object Remaining | Select-Object -First 1
    $mostConstrainedShort = $shortBuckets | Sort-Object Remaining | Select-Object -First 1
    $resetMinutes = ($mostConstrainedLong.Reset - $Now).TotalMinutes
    if ($resetMinutes -lt 0) { throw "Stale long-window reset timestamp for $Profile." }
    return [pscustomobject]@{
        telemetry_scope    = 'GROUP_HEADROOM_ONLY'
        requested_model    = $Model
        effective_model_capacity = 'NOT_EXPOSED_BY_PROVIDER_TELEMETRY'
        profile            = $Profile
        long_remaining_pct = [math]::Round($mostConstrainedLong.Remaining, 3)
        five_h_remaining_pct = [math]::Round($mostConstrainedShort.Remaining, 3)
        long_reset_utc     = $mostConstrainedLong.Reset.ToUniversalTime().ToString('o')
        five_h_reset_utc   = if ($null -ne $mostConstrainedShort.Reset) { $mostConstrainedShort.Reset.ToUniversalTime().ToString('o') } else { '' }
        minutes_until_long_reset = [math]::Round($resetMinutes, 2)
    }
}

function Set-AgyCredentialProfileStrict {
    param([Parameter(Mandatory)][string]$Profile)
    $state = Get-AgyProfileState
    if ($state.ActiveProfile -eq $Profile -and
        (-not $state.ActiveFile -or $state.ActiveFile -eq $Profile)) {
        try {
            Assert-AgyCredentialStores -ExpectedBytes (Get-AgySavedCredentialBytes -Profile $Profile) -TokenPath (Join-Path $env:USERPROFILE '.gemini/antigravity-cli/antigravity-oauth-token')
            return
        } catch { Write-Warning 'AGY credential stores need synchronization; repairing selected profile before execution.' }
    }
    $oldEap = $ErrorActionPreference
    try {
        $ErrorActionPreference = 'Continue'
        $result = & agy-profile switch $Profile -Force 2>&1
        $code = $LASTEXITCODE
    } finally { $ErrorActionPreference = $oldEap }
    if ($code -ne 0) { throw "agy-profile switch $Profile failed: $(($result | Out-String).Trim())" }
    $new = Get-AgyProfileState
    # Require authenticated identity, NOT just a last-switch marker.
    if ($new.ActiveProfile -ne $Profile -or
        ($new.ActiveFile -and $new.ActiveFile -ne $Profile)) {
        throw "Credential switch verification FAILED for $Profile; actual=$($new.ActiveProfile), file=$($new.ActiveFile)."
    }
}

function Get-AgySmartCooldownActive {
    param([string]$Profile)
    if (-not $script:SmartCooldowns.ContainsKey($Profile)) { return $false }
    try { $until = [DateTimeOffset]::Parse([string]$script:SmartCooldowns[$Profile]) }
    catch { return $false }
    return ($until -gt [DateTimeOffset]::UtcNow)
}

function Set-AgySmartQuotaCooldown {
    param([string]$Profile, [string]$Reason, [string]$Message = '')
    if ($Profile -notmatch '^account[1-5]$') { return }
    $existing = if ($script:SmartCooldowns.ContainsKey($Profile)) { [string]$script:SmartCooldowns[$Profile] } else { '' }
    $until = Get-AgyQuotaCooldownDeadline -Message $Message -ExistingUntil $existing
    $script:SmartCooldowns[$Profile] = $until
    Write-AgySmartProfileState -Reason $Reason
    Write-Host "[SMART-AGY] Excluding $Profile until $until after $Reason (provider reset respected)." -ForegroundColor Yellow
}

function Select-AgySmartCandidate {
    param([object[]]$Records, [string]$ExcludeProfile = '')
    $eligible = @($Records | Where-Object {
        $_.profile -ne $ExcludeProfile -and
        (Test-AgyQuotaHeadroom -Record $_ -ShortThreshold $QuotaStopThresholdPct -LongThreshold ([Math]::Max(20, $SmartMinLongRemainingPct))) -and
        -not (Get-AgySmartCooldownActive -Profile $_.profile)
    })
    # Primary: soonest REAL long-window reset. Secondary: most 5h quota
    # remaining, then deterministic account name. This does not simply pin
    # account1 and does not exhaust a below-threshold five-hour account.
    return ($eligible | Sort-Object `
        @{ Expression = 'minutes_until_long_reset'; Ascending = $true }, `
        @{ Expression = 'five_h_remaining_pct'; Descending = $true }, `
        @{ Expression = 'profile'; Ascending = $true } | Select-Object -First 1)
}

function Get-AgySavedProfileIdentity {
    param([string]$Profile)
    return (ConvertTo-AgyCredentialToken -Bytes (Get-AgySavedCredentialBytes -Profile $Profile)).Identity
}

function Invoke-AgySmartSelectionOnce {
    param([string]$ExcludeProfile = '', [string]$Reason = 'STARTUP')
    $original = Get-CurrentAgyProfileName
    if ($original -notmatch '^account[1-5]$') { throw 'Cannot verify current AGY identity before smart scan.' }
    $results = @()
    $failures = @()
    $seenIdentities = @{}
    $blockedIdentities = @{}
    foreach ($cooldownProfile in @($script:SmartCooldowns.Keys)) {
        if (Get-AgySmartCooldownActive -Profile $cooldownProfile) {
            try { $blockedIdentities[(Get-AgySavedProfileIdentity -Profile $cooldownProfile)] = $true }
            catch { throw "Cannot verify exhausted account identity for $cooldownProfile; refusing an unsafe alias scan." }
        }
    }
    foreach ($profile in @($AgyProfileRotationOrder | Where-Object { $_ -match '^account[1-5]$' } | Select-Object -Unique)) {
        if (Get-AgySmartCooldownActive -Profile $profile) { continue }
        try {
            # Inventory reads each saved credential directly; only the winner is switched.
            $payload = Get-AgyQuotaProviderJson -Profile $profile
            if (-not $payload.profile_identity) { throw 'Missing quota profile identity.' }
            if ($blockedIdentities.ContainsKey($payload.profile_identity)) { continue }
            if ($seenIdentities.ContainsKey($payload.profile_identity)) {
                Write-Warning "[SMART-AGY] $profile is an alias of $($seenIdentities[$payload.profile_identity]); skipping duplicate capacity."
                continue
            }
            $seenIdentities[$payload.profile_identity] = $profile
            if ($ExcludeProfile) {
                # Exclude every alias of an exhausted identity, not only its label.
                $excluded = Get-AgySavedProfileIdentity -Profile $ExcludeProfile
                if ($payload.profile_identity -eq $excluded) { continue }
            }
            $results += ConvertTo-AgySmartQuotaRecord -Profile $profile -Payload $payload -GroupRegex $SmartQuotaGroupRegex
        } catch {
            $failures += "$profile`: $($_.Exception.Message)"
            Write-Warning "[SMART-AGY] quota unknown for $profile; NOT eligible. $($_.Exception.Message)"
        }
    }
    $selected = Select-AgySmartCandidate -Records $results -ExcludeProfile $ExcludeProfile
    Write-AgySmartProfileState -Snapshots $results -Reason $Reason -Selected $(if ($selected) { $selected.profile } else { '' })
    if ($null -eq $selected) {
        throw "No verified account with long quota > $SmartMinLongRemainingPct% and 5h quota > $QuotaStopThresholdPct%. Check aichecker OAuth/401 and profiles. $($failures -join '; ')"
    }
    $prior = $script:RunLockedAgyProfile
    Set-AgyCredentialProfileStrict -Profile $selected.profile
    $script:RunLockedAgyProfile = $selected.profile
    $script:AuthoritativeAgyProfile = $selected.profile
    $script:SelectedAgyProfile = $selected.profile
    $script:PinnedAgyProfile = $selected.profile
    $selectedMetadata = [ordered]@{
        selected_profile = $selected.profile
        source = 'smart-quota-selector'
        switched_at_utc = [DateTimeOffset]::UtcNow.ToString('o')
    }
    [System.IO.File]::WriteAllText($SelectionFile, ($selectedMetadata | ConvertTo-Json), [System.Text.UTF8Encoding]::new($false))
    if ($prior -ne $selected.profile) {
        $script:ConversationId = ''
        $script:ConversationIdSource = 'new-conversation-smart-profile'
        # Keep factual continuity across accounts without reusing any
        # cross-account conversation token.
        $previousResponse = ''
        if (Get-Variable agentResponse -Scope Script -ErrorAction SilentlyContinue) {
            $previousResponse = [string]$script:agentResponse
        }
        if ([string]::IsNullOrWhiteSpace($previousResponse) -and (Test-Path -LiteralPath $StateFile)) {
            try { $previousResponse = [string]((Get-Content -LiteralPath $StateFile -Raw | ConvertFrom-Json).last_response) } catch {}
        }
        if ($previousResponse.Length -gt 6000) { $previousResponse = $previousResponse.Substring($previousResponse.Length - 6000) }
        $script:PendingSmartProfileContext = "Before any action read project_coordination/ACTIVE_SESSION.json, ACTIVE_TASK.json, HPC_JOB_LEDGER.csv, MODE1_EXECUTION_LEDGER.json and the latest session report. Reconcile guarded qstat with all reserved IDs; never repeat a submission. PROFILE CHANGE: $prior -> $($selected.profile). Previous conversation belongs to the old account and MUST NOT be reused. Continue project from persistent artifacts, do not repeat completed HPC work. Previous completed response (if any):`n$previousResponse`n"
    }
    Write-Host ("[SMART-AGY] {0}: selected {1}; longer window resets in {2:N1} h; long quota {3}%; 5h quota {4}%." -f `
        $Reason, $selected.profile, ($selected.minutes_until_long_reset / 60.0), `
        $selected.long_remaining_pct, $selected.five_h_remaining_pct) -ForegroundColor Green
    return [pscustomobject]@{
        previous_profile = $prior
        new_profile = $selected.profile
        previous_conversation = ''
        new_conversation_policy = 'agy-create-on-first-turn'
    }
}

# AGY_SMART_TELEMETRY_REFRESH_V1
# Called only BETWEEN completed AGY turns by Invoke-AgySmartSelection.
# Refresh credentials once ONLY if fresh quota telemetry prevented selecting an
# otherwise unknown candidate. Valid low-quota readings are NEVER overridden.
function Invoke-AgyBoundedInventoryRefresh {
    param([string]$Reason = 'QUOTA_UNKNOWN')

    $original = Get-CurrentAgyProfileName
    if ($original -notmatch '^account[1-5]$') {
        throw '[SMART-AGY] Refusing credential refresh: active saved profile is unknown.'
    }
    $identity = Get-AgyProfileState
    if (($identity.ActiveProfile -and $identity.ActiveProfile -ne $original) -or
        ($identity.ActiveFile -and $identity.ActiveFile -ne $original)) {
        throw "[SMART-AGY] Refusing credential refresh: profile identity/marker disagreement for '$original'."
    }

    $refreshScript = Join-Path $env:USERPROFILE 'OpenClawPAD\Refresh-AgyAccounts.ps1'
    if (-not (Test-Path -LiteralPath $refreshScript -PathType Leaf)) {
        throw "[SMART-AGY] Credential refresh script missing: $refreshScript"
    }
    # Never run interactive credential prompts inside an unattended scan.
    $shell = Join-Path $PSHOME 'powershell.exe'
    if (-not (Test-Path -LiteralPath $shell -PathType Leaf)) {
        throw '[SMART-AGY] Windows PowerShell executable not found.'
    }

    Write-Host "[SMART-AGY] $($Reason): quota telemetry unavailable; running one bounded credential refresh." -ForegroundColor Yellow
    $oldEap = $ErrorActionPreference
    $refreshExit = $null
    try {
        # Windows PowerShell 5.1 can surface benign native stderr progress as
        # NativeCommandError when ErrorActionPreference is Stop.
        $ErrorActionPreference = 'Continue'
        $null = & $shell -NoProfile -NonInteractive -ExecutionPolicy Bypass -File $refreshScript 2>&1
        $refreshExit = $LASTEXITCODE
    }
    finally {
        $ErrorActionPreference = $oldEap
        # Refresh-AgyAccounts.ps1 may walk all five credential profiles.
        # Restore the caller's profile even when refresh fails. Any inability
        # to restore is FATAL and must never be swallowed.
        Set-AgyCredentialProfileStrict -Profile $original
    }
    if ($refreshExit -ne 0) {
        throw "[SMART-AGY] Refresh-AgyAccounts.ps1 exited $refreshExit; stopping without trusting unknown quota."
    }
    Write-Host '[SMART-AGY] Credential refresh finished; requiring a new aichecker scan to establish eligible capacity.' -ForegroundColor Green
}

function Invoke-AgySmartSelection {
    param([string]$ExcludeProfile = '', [string]$Reason = 'STARTUP')
    try {
        return (Invoke-AgySmartSelectionOnce -ExcludeProfile $ExcludeProfile -Reason $Reason)
    }
    catch {
        $failure = [string]$_.Exception.Message
        # Only inventory telemetry failures qualify. A real (measured) low
        # quota, identity drift, syntax error, or other problem never does.
        $inventoryFailed = $failure -match '^No verified account with long quota' -and
            $failure -match '(?i)(telemetry unavailable|token refresh failed|HTTP\s*401|invalid_client|unauthorized)'
        if (-not $inventoryFailed) { throw }
        Invoke-AgyBoundedInventoryRefresh -Reason $Reason
        # This second scan is authoritative. No third attempt, stale cache,
        # guessed quota, or fallback to the below-threshold original account.
        return (Invoke-AgySmartSelectionOnce -ExcludeProfile $ExcludeProfile -Reason "$Reason-POST_REFRESH")
    }
}
# END AGY_SMART_TELEMETRY_REFRESH_V1
function Adopt-ExternalAgySwitchAtBoundary {
    if (-not $EnableSmartAgyProfileSelection) { return }
    $live = Get-AgyProfileState
    if ($live.ActiveProfile -and $live.ActiveProfile -ne $script:RunLockedAgyProfile) {
        if ($live.ActiveProfile -notmatch '^account[1-5]$' -or
            ($live.ActiveFile -and $live.ActiveFile -ne $live.ActiveProfile)) {
            throw 'Manual account change cannot be authenticated; stopping instead of restoring or guessing.'
        }
        # A human-initiated switch between turns is authoritative until the
        # selected profile next runs low. Do not undo it via an old run lock.
        $old = $script:RunLockedAgyProfile
        $script:RunLockedAgyProfile = $live.ActiveProfile
        $script:AuthoritativeAgyProfile = $live.ActiveProfile
        $script:SelectedAgyProfile = $live.ActiveProfile
        $script:PinnedAgyProfile = $live.ActiveProfile
        $script:ConversationId = ''
        $script:ConversationIdSource = 'manual-switch-new-conversation'
        $script:PendingSmartProfileContext = "The human switched AGY profile from $old to $($live.ActiveProfile) between turns. Start a NEW AGY conversation; use the persisted project records and next instruction, without redoing completed work."
        Write-Host "[SMART-AGY] Adopted verified human switch: $old -> $($live.ActiveProfile)." -ForegroundColor Green
    }
}
Read-AgySmartProfileState
# END AGY_SMART_PROFILE_SELECTION_V2 --------------------------------------------

function Save-LoopState($Turn, $Status, $LastInstruction, $LastResponse, $NextInstruction, $Duration, $Usage, $Tier, $Action) {
    $currentProf = Get-CurrentAgyProfileName
    $stateObj = [PSCustomObject]@{
        last_updated     = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
        completed_turn   = $Turn
        conversation_id  = $ConversationId
        agy_profile      = $currentProf
        workspace        = $WorkspaceDir
        loop_status      = $Status
        duration_sec     = $Duration
        usage            = $Usage
        tier             = $Tier
        action           = $Action
        last_instruction = $LastInstruction
        last_response    = $LastResponse
        next_instruction = $NextInstruction
    }
    $json = $stateObj | ConvertTo-Json -Depth 5
    [System.IO.File]::WriteAllText($StateFile, $json, [System.Text.UTF8Encoding]::new($false))
}

# =====================================================================
# CHATGPT BRIDGE MODE
#
# $true  = reliable manual clipboard bridge; browser automation bypassed
# $false = try automatic Tampermonkey/OpenClaw first, then manual fallback
# =====================================================================

$script:PreferManualChatGPTBridge = $false


function Write-SafeUtf8File {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [string]$Directory,

        [Parameter(Mandatory = $true)]
        [string]$FileName,

        [Parameter(Mandatory = $true)]
        [AllowEmptyString()]
        [string]$Content
    )

    if (-not (Test-Path -LiteralPath $Directory)) {
        New-Item -ItemType Directory -Path $Directory -Force | Out-Null
    }

    # FileName only - never permit a prompt, URL, qstat text, etc.
    # to become part of a Windows filesystem path.
    $safeName = [regex]::Replace(
        $FileName,
        '[<>:"/\\|?*\x00-\x1F]',
        '_'
    )

    $safeName = $safeName.TrimEnd([char[]]@('.', ' '))

    if ([string]::IsNullOrWhiteSpace($safeName)) {
        throw "Refusing to create an empty/invalid filename."
    }

    $fullPath = Join-PathStrict -Path $Directory -ChildPath $safeName

    [System.IO.File]::WriteAllText(
        $fullPath,
        $Content,
        [System.Text.UTF8Encoding]::new($false)
    )

    return $fullPath
}

function Invoke-ManualChatGPTBridge {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Prompt,

        [string]$ContextLabel = "chatgpt"
    )

    $handoffId = "HND-" + ([guid]::NewGuid().ToString("N").Substring(0, 12))

    $payload = @"
[BRIDGE_HANDOFF_ID=$handoffId]

$Prompt
"@

    $agentsDir = "D:\Master thesis\Adaptive remeshing\.agents"
    $historyDir = Join-PathStrict -Path $agentsDir -ChildPath "bridge_history"

    New-Item -ItemType Directory -Path $agentsDir -Force | Out-Null
    New-Item -ItemType Directory -Path $historyDir -Force | Out-Null

    $pendingFile = Join-PathStrict -Path $agentsDir -ChildPath "PENDING_CHATGPT_BRIDGE.md"

    $safeContext = $ContextLabel -replace '[^A-Za-z0-9_.-]', '_'

    $historyPayloadFile = Join-PathStrict -Path $historyDir -ChildPath ("{0}_{1}_payload.md" -f $handoffId, $safeContext)

    [System.IO.File]::WriteAllText(
        $pendingFile,
        $payload,
        [System.Text.UTF8Encoding]::new($false)
    )

    [System.IO.File]::WriteAllText(
        $historyPayloadFile,
        $payload,
        [System.Text.UTF8Encoding]::new($false)
    )

    Set-Clipboard -Value $payload

    try {
        Write-LoopLog `
            -Turn $CurrentTurn `
            -Tier "tier3_chatgpt" `
            -Action "MANUAL_BRIDGE_READY" `
            -Message "Handoff $handoffId copied to clipboard; controller waiting for ChatGPT response."
    }
    catch {}

    Write-Host ""
    Write-Host "==========================================================" -ForegroundColor Cyan
    Write-Host " MANUAL CHATGPT BRIDGE - CONTROLLER STILL RUNNING" -ForegroundColor Green
    Write-Host "==========================================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Handoff ID:" -NoNewline
    Write-Host " $handoffId" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Bridge payload saved:"
    Write-Host "  $pendingFile"
    Write-Host ""
    Write-Host "Bridge payload is already on the Windows clipboard."
    Write-Host ""
    Write-Host "ACTION:"
    Write-Host "  1. Return to THIS ChatGPT conversation."
    Write-Host "  2. Click the message box."
    Write-Host "  3. Press Ctrl+V."
    Write-Host "  4. Send the message."
    Write-Host "  5. Wait for ChatGPT's reply."
    Write-Host "  6. Copy ONLY ChatGPT's reply."
    Write-Host "  7. Return to this PowerShell window."
    Write-Host "  8. Press ENTER."
    Write-Host ""
    Write-Host "Commands while waiting:"
    Write-Host "  R       = copy the bridge payload to clipboard again"
    Write-Host "  ABORT   = fail closed and stop this bridge"
    Write-Host ""
    Write-Host "IMPORTANT: Do NOT close this PowerShell/controller window."
    Write-Host "=========================================================="
    Write-Host ""

    while ($true) {

        $manualCommand = Read-Host `
            "Press ENTER after ChatGPT's reply is copied, R to recopy, or ABORT"

        if ($manualCommand -match '^(?i:ABORT|QUIT|Q)$') {
            throw "Manual ChatGPT bridge aborted by user for handoff $handoffId."
        }

        if ($manualCommand -match '^(?i:R|RECOPY)$') {

            Set-Clipboard -Value $payload

            Write-Host ""
            Write-Host "Bridge payload copied to clipboard again." -ForegroundColor Cyan
            Write-Host ""

            continue
        }

        try {
            $reply = Get-Clipboard -Raw -ErrorAction Stop
        }
        catch {
            Write-Host ""
            Write-Host "Could not read Windows clipboard. Try again." -ForegroundColor Yellow
            continue
        }

        if ([string]::IsNullOrWhiteSpace($reply)) {
            Write-Host ""
            Write-Host "Clipboard is empty. Copy ChatGPT's reply first." -ForegroundColor Yellow
            continue
        }

        $replyTrim = $reply.Trim()
        $payloadTrim = $payload.Trim()

        if ($replyTrim -eq $payloadTrim) {
            Write-Host ""
            Write-Host "Clipboard still contains the bridge payload." -ForegroundColor Yellow
            Write-Host "Copy ChatGPT's RESPONSE, then press ENTER again."
            continue
        }

        if ($replyTrim.StartsWith("[BRIDGE_HANDOFF_ID=$handoffId]")) {
            Write-Host ""
            Write-Host "Clipboard appears to contain the original handoff again." -ForegroundColor Yellow
            Write-Host "Copy only ChatGPT's response."
            continue
        }

        $responseFileName = "${handoffId}_${safeContext}_chatgpt_response.txt"
        $responseFile = Write-SafeUtf8File `
            -Directory $historyDir `
            -FileName $responseFileName `
            -Content $replyTrim

        # [System.IO.File]::WriteAllText replaced by Write-SafeUtf8File
        #
        #
        # [System.Text.UTF8Encoding]::new(False)
        # )

        if (Test-Path -LiteralPath $pendingFile) {
            Remove-Item -LiteralPath $pendingFile -Force
        }

        try {
            Write-LoopLog `
                -Turn $CurrentTurn `
                -Tier "tier3_chatgpt" `
                -Action "MANUAL_BRIDGE_RESPONSE_RECEIVED" `
                -Message "ChatGPT response recovered for handoff $handoffId."
        }
        catch {}

        Write-Host ""
        Write-Host "ChatGPT response accepted." -ForegroundColor Green
        Write-Host "Saved:"
        Write-Host "  $responseFile"
        Write-Host ""
        Write-Host "Controller continuing automatically..." -ForegroundColor Green
        Write-Host ""

        return $replyTrim
    }
}


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

    $BridgeScript = "D:\Master thesis\Adaptive remeshing\.agents\scripts\Invoke-ChatGPTBridge.ps1"
    if (-not (Test-Path -LiteralPath $BridgeScript)) {
        $BridgeScript = Join-Path $env:USERPROFILE "OpenClawPAD\ChatGPTBridge\Invoke-ChatGPTBridge.ps1"
    }

    if (-not (Test-Path -LiteralPath $BridgeScript)) {
        if ($EnableManualClipboardFallback) {
            Write-Host ""
            Write-Host "Automatic bridge script not found. Using manual clipboard mode." -ForegroundColor Yellow
            Write-Host ""
            return Invoke-ManualChatGPTBridge -Prompt $Prompt -ContextLabel $ContextLabel
        }
        throw "Automatic ChatGPT bridge script not found at: $BridgeScript"
    }

    . $BridgeScript

    $attempts = [Math]::Max(1, $ChatGPTBridgeMaxAttempts)
    $timeoutMinutes = [Math]::Max(1, [int][Math]::Ceiling($ChatGPTBridgeTimeoutSeconds / 60))

    # Generate a single persistent handoff ID for all retries of this logical request
    $persistentHandoffId = "HND-" + ([guid]::NewGuid().ToString("N").Substring(0, 12))

    for ($attempt = 1; $attempt -le $attempts; $attempt++) {
        try {
            $Reply = Invoke-ChatGPTBridge `
                -PromptText $Prompt `
                -HandoffId $persistentHandoffId `
                -LaunchPad:$ChatGPTBridgeLaunchPad `
                -RequireHeartbeat:$ChatGPTBridgeRequireHeartbeat `
                -TimeoutMinutes $timeoutMinutes

            $Reply = ($Reply | Out-String).Trim()

            if ([string]::IsNullOrWhiteSpace($Reply)) {
                throw "Automatic ChatGPT bridge returned an empty response."
            }

            return $Reply
        }
        catch {
            $bridgeError = $_.Exception.Message

            Write-Warning "ChatGPT local bridge attempt $attempt of $attempts failed: $bridgeError"

            if ($attempt -lt $attempts) {
                Write-Host "[CHATGPT-LOCAL-BRIDGE] Retrying SAME handoff ($persistentHandoffId) in 2 seconds..." -ForegroundColor Cyan
                Start-Sleep -Seconds 2
                continue
            }

            # -------------------------------------------------------------------------
            # CHATGPT BRIDGE FAILURE POLICY
            # Project requirement: automatic bridge only; manual clipboard fallback is
            # prohibited. Failure must stop the controller before another AGY turn,
            # scientific mutation, remote execution action, or instruction replay can occur.
            # -------------------------------------------------------------------------

            $bridgeFailureMessage = @"
Automatic ChatGPT bridge failed after all configured retry attempts.

FAIL-CLOSED POLICY ACTIVE:
- Manual clipboard fallback is DISABLED.
- No Antigravity continuation is permitted.
- No instruction may be replayed without ChatGPT validation.
- No cluster submission is permitted.
- No simulation or scientific artifact modification is permitted.

Repair the ChatGPT bridge and restart the controller.
"@

            Write-Warning $bridgeFailureMessage

            throw "CHATGPT_BRIDGE_FAIL_CLOSED"
        }
    }
}

function Invoke-EscalationChatGPT($AntigravityResponse, $QuotaSnapshotText = "") {
    $stateFile = Join-Path $WorkspaceDir 'project_coordination/CURRENT_STATE.md'
    $stateText = if (Test-Path -LiteralPath $stateFile) { Get-AgyBoundedText -Text (Get-Content -LiteralPath $stateFile -Raw) -Limit 5000 } else { 'Current state unavailable: require artifact reconciliation before action.' }
    $resultText = Get-AgyBoundedText -Text ([string]$AntigravityResponse) -Limit 7000
    $quotaText = Get-AgyBoundedText -Text ([string]$QuotaSnapshotText) -Limit 1800
    $Prompt = @"
AUTOMATED MODE-I RESEARCH HANDOFF, controller turn $CurrentTurn
$(Get-AgyCompactRules)
AUTHORITATIVE CURRENT STATE SNAPSHOT (may require live reconciliation):
$stateText
LATEST RESULT (bounded excerpt; full evidence is in project session reports):
$resultText
QUOTA SNAPSHOT:
$quotaText
Give ONLY the next instruction for ONE bounded scientific investigation or one independent qualified batch. Keep it below 4000 characters. Preserve the Method C pipeline; reconcile existing experiments before new work. Read exact task/session/ledger artifacts to recover details omitted from this compact handoff. Require exact quantitative evidence, job receipts, tests and truthful closeout. Ready qualified jobs must execute; do not spend another turn retelling project history. No waiting inside AGY for solver completion. If no scientifically supported next action can be determined, reply ESCALATION_UNRESOLVED. Never infer scientific success from an empty queue.
"@
    $Reply = Invoke-ChatGPTBridgeWithManualFallback -Prompt $Prompt -ContextLabel "AGY_TURN_$CurrentTurn"
    if ($Reply -eq 'ESCALATION_UNRESOLVED') { throw 'ChatGPT could not determine a safe next instruction.' }
    return $Reply
}

function Invoke-SchedulerReviewChatGPT($ActiveJobId, $QstatText) {
    $jobInfoText = if ([string]::IsNullOrWhiteSpace($ActiveJobId)) { "<none tracked>" } else { $ActiveJobId }

    $Prompt = @"
SCHEDULER DECISION RULES

HUMAN (USER) & SUPERVISOR DIRECTIVE STATUS:
The supervisor and human user have explicitly directed following the 17-Sep-2026 meeting: focus strictly on Mode-I fundamentals qualification. Mode-II is on HOLD. Visualization (Gate 7) is on HOLD.
The 71,320 stiffness anomaly is RESOLVED_AND_CLOSED. The 13,941 vs 71,320 reproduction is CLOSED_WITH_SUPERVISOR_ACCEPTED_PUBLICATION_LIMITATION.
Active Priority 1 is UEL Energy Formulation and Output Audit; Priority 2 is Multifaceted Mode-I Convergence; Priority 3 is Mode-I State-Transfer Energy Preservation (pending energy baseline qualification).
Evaluate solver evidence and job status against the Mode-I reference anchor, the active fundamentals roadmap, and multi-quantity convergence criteria.

---------------- PROJECT / THESIS ALIGNMENT GUARD ----------------
$(Get-AgyCompactRules)
-------------- END PROJECT / THESIS ALIGNMENT GUARD --------------

Tracked production PBS job:
$jobInfoText

Fresh scheduler snapshot:
qstat -u pr21vyci

---------------- SCHEDULER RESULT ----------------
$QstatText
-------------- END SCHEDULER RESULT --------------

Determine the next instruction to send to Antigravity.

Rules:
1. Concurrency & Independent Work Check:
   If running jobs (R or Q) exist, but there is free HPC headroom (under 640 CPUs) AND independent Mode-I work is ready (such as launching independent same-thread determinism repeats, evaluating terminal jobs, postprocessing, or advancing Gate 6 evidence):
   Do NOT reply 'stop'. Instruct Antigravity to proceed with that independent work while leaving running jobs untouched!

2. When to reply 'stop':
   Reply exactly 'stop' if all active tracked jobs (such as 1404454.mmaster02) are currently running ('R') undisturbed, and no genuinely new independent Mode-I tasks remain ready to execute right now.
   The loop controller will then enter a wait cycle until the job state actually changes.
   CRITICAL LOOP PREVENTION: While running jobs remain 'R', do NOT loop on repetitive accounting, telemetry queries, or active-ODB reads. Only react when the running job's state actually changes!
   If the scheduler is completely empty, check whether Mode-I fundamentals work (energy formulation audit, mathematical derivations, offline parity planning, report updates) is actionable.
   If Mode-I fundamentals work is actionable, instruct Antigravity to proceed with that independent work! Do NOT reply 'stop' when independent work remains.
   Reply exactly 'stop' ONLY when all currently justified independent Mode-I work is completed or running, and progress genuinely depends on an active job reaching terminal state.

3. If the tracked job ($jobInfoText) is H, W, or another nonstandard state:
   do not automatically return stop. Determine whether intervention or diagnostic accounting is required.

4. Terminal Job Lookup & Loop Prevention Rule:
   A previously verified terminal job (e.g., state F/C/E already established, evaluated, or recorded in the ledger/status, such as 1404306.mmaster02) does NOT trigger repeated 'qstat -x' merely because it is absent from 'qstat -u'. Treat already-verified jobs as terminal-and-frozen evidence. Do NOT loop on accounting!
   Only a tracked job whose terminal state is not already established needs that lookup (i.e. a job that was recently running and has newly disappeared from 'qstat -u' without its terminal transition yet having been recorded).

5. If a job's terminal transition is newly detected:
   Issue the next concrete scientific evidence-retrieval/evaluation action rather than stopping. Once evaluated, treat that job as terminal-and-frozen evidence; do not poll it again.

6. Never infer or construct PBS IDs from numerical scientific values.
7. When asking Antigravity to perform work, require it to write "Finished" at the end.
8. If the supplied information is insufficient for a safe next instruction, reply exactly:
ESCALATION_UNRESOLVED
"@

    $Reply = Invoke-ChatGPTBridgeWithManualFallback `
        -Prompt $Prompt `
        -ContextLabel "SCHEDULER_REVIEW_TURN_$CurrentTurn"

    if ($Reply -eq "ESCALATION_UNRESOLVED") {
        throw "ChatGPT could not determine a safe next instruction."
    }

    if ($Reply -match '^(?i:stop)\s*$') {
        return "stop"
    }

    return $Reply
}
# ==============================================================================
# MAIN AUTONOMOUS LOOP CONTROLLER
# ==============================================================================
Write-Host "==========================================================" -ForegroundColor Green
Write-Host " STARTING ANTIGRAVITY AUTONOMOUS CONTROLLER LOOP " -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Green
$conversationDisplay = if ([string]::IsNullOrWhiteSpace($ConversationId)) { "<agy will create>" } else { $ConversationId }
Write-Host " Conversation ID: $conversationDisplay"
Write-Host " Conversation Src:$ConversationIdSource"
Write-Host " Workspace:       $WorkspaceDir"
Write-Host " agy Executable:  $AgyPath"
Write-Host " Model:           $Model"
Write-Host " Max Turns:       $MaxTurns"
Write-Host " Requested timeout:$PrintTimeout; scientific cap=${ScientificTurnSeconds}s; local closeout reserve=120s; no-result deadline=${NoProgressSeconds}s; immediate model closeout retries=0"
Write-Host " Mode-I Fundam.:  $($script:ModeIFundamentalsStatus) (Actionable: $(Get-ModeIFundamentalsActionable))"
Write-Host " Active Prod Job: $ActiveProductionJobId"
if ($EnableSmartAgyProfileSelection -and
    -not $PSBoundParameters.ContainsKey('AuthoritativeAgyProfile')) {
    # Startup scan is safe because no AGY process has started yet.
    $null = Invoke-AgySmartSelection -Reason 'STARTUP'
}
Set-AndVerifyAgyRunProfile "STARTUP"
$script:SelectedAgyProfile = $script:RunLockedAgyProfile
$script:PinnedAgyProfile = $script:RunLockedAgyProfile
Write-Host " Authoritative Manual Profile: $($script:RunLockedAgyProfile)" -ForegroundColor Green
Write-Host " Auto Profile:    $EnableAutomaticAgyProfileRotation (smart: $EnableSmartAgyProfileSelection)"
Write-Host " SkipPerms Flag:  $AllowSkipPermissions"
Write-Host " Persistent Guard:ENABLED (artifact-safe + non-interactive commands)"
Write-Host " Scheduler Query: ROBUST SSH STDERR + 1 RETRY ON DIRECT QSTAT FAILURE"
Write-Host " Artifact Read:  EXISTENCE-GUARDED + 1 LOCAL AUTO-RECOVERY (slash-normalized)"
Write-Host " Quota Guard:    ENABLED when QuotaCheckEveryTurns > 0"
Write-Host " Quota Check:    every $QuotaCheckEveryTurns AGY turn(s)"
Write-Host " Quota Threshold:rotate/stop when selected 5h remaining <= $QuotaStopThresholdPct%"
Write-Host " Quota Groups:   $QuotaGroupRegex"
Write-Host " Quota Source:   $QuotaCheckerCommand $($QuotaCheckerBaseArgs -join ' ') --antigravity --json --no-cache"
$bridgeStatusStr = if ($EnableChatGPTBridge) { "ENABLED (PAD Three-Part Bridge)" } else { "DISABLED (Autonomous AGY Direct)" }
Write-Host " ChatGPT Bridge:  $bridgeStatusStr"
Write-Host "==========================================================" -ForegroundColor Green

# ============================================================
# INITIAL PROMPT FILE
# ============================================================
if (-not [string]::IsNullOrWhiteSpace($InitialPromptFile)) {
    if (-not (Test-Path -LiteralPath $InitialPromptFile)) {
        throw "Initial prompt file does not exist: $InitialPromptFile"
    }

    if (-not [string]::IsNullOrWhiteSpace($InitialPrompt)) {
        throw "Use either -InitialPrompt or -InitialPromptFile, not both."
    }

    $InitialPrompt = Get-Content `
        -LiteralPath $InitialPromptFile `
        -Raw `
        -Encoding UTF8

    if ([string]::IsNullOrWhiteSpace($InitialPrompt)) {
        throw "Initial prompt file is empty: $InitialPromptFile"
    }

    Write-Host "Initial Prompt:  FILE" -ForegroundColor Cyan
    Write-Host "Prompt File:     $InitialPromptFile" -ForegroundColor Cyan
    Write-Host "Prompt Length:   $($InitialPrompt.Length) characters" -ForegroundColor Cyan
}

# 1. Resolve Resume State / Initial Instruction
$CurrentInstruction = $InitialPrompt
$StartTurn = 1

if ([string]::IsNullOrWhiteSpace($CurrentInstruction)) {
    if (Test-Path $StateFile) {
        try {
            $existing = Get-Content $StateFile -Raw | ConvertFrom-Json
            $modeIFundamentalsActionable = Get-ModeIFundamentalsActionable

            if ($modeIFundamentalsActionable -and -not $script:ModeIFundamentalsComplete) {
                if ($existing.loop_status -eq "WAITING_ON_SUPERVISOR_DECISION" -or $existing.loop_status -eq "STOPPED_CLEAN" -or [string]::IsNullOrWhiteSpace($existing.next_instruction) -or $existing.next_instruction -match '^(?i:stop)\s*$') {
                    Write-Host "`n[NOTICE] Resuming Mode-I fundamentals qualification following 17-Sep-2026 supervisor meeting." -ForegroundColor Yellow
                    Write-Host "[RESUME] Priority 1: UEL Energy Formulation and Output Audit." -ForegroundColor Green
                    $CurrentInstruction = $ModeIFundamentalsKickoffInstruction
                    $StartTurn = [int]($existing.completed_turn) + 1
                    Save-LoopStatus -Turn ($existing.completed_turn) -Status "MODE1_FUNDAMENTALS_ACTIVE" -Tier "CONTROLLER" -Action "ENERGY_FORMULATION_AUDIT_ACTIONABLE" -Details "Supervisor meeting completed. Mode-I fundamentals active."
                }
                elseif ($existing.next_instruction) {
                    $CurrentInstruction = $existing.next_instruction
                    $StartTurn = [int]($existing.completed_turn) + 1
                    Write-Host "[RESUME] Safely resuming from pending next_instruction (Turn ${StartTurn})." -ForegroundColor Green
                }
            }
            elseif ($existing.loop_status -eq "STOPPED_CLEAN" -or [string]::IsNullOrWhiteSpace($existing.next_instruction) -or $existing.next_instruction -match '^(?i:stop)\s*$') {
                Write-Host "`n[NOTICE] Previous workflow in '$StateFile' reached completion ('stop') and no further fundamentals work is actionable." -ForegroundColor Yellow
                Write-Host "To start a new workflow turn, please specify -InitialPrompt '<prompt>'." -ForegroundColor Yellow
                Save-LoopStatus -Turn ($existing.completed_turn) -Status "IDLE" -Tier "CONTROLLER" -Action "WAITING_FOR_NEW_PROMPT" -Details "Previous run finished cleanly."
                exit 0
            }
            elseif ($existing.next_instruction) {
                $CurrentInstruction = $existing.next_instruction
                $StartTurn = [int]($existing.completed_turn) + 1
                Write-Host "[RESUME] Safely resuming from pending next_instruction (Turn ${StartTurn})." -ForegroundColor Green
            }
        } catch { }
    }
}

if ([string]::IsNullOrWhiteSpace($CurrentInstruction)) {
    $CurrentInstruction = $ModeIFundamentalsKickoffInstruction
}

$resolved = Resolve-ControllerInstruction $WorkspaceDir $CurrentInstruction
$CurrentInstruction = $resolved.instruction
$script:ControllerState = Read-ControllerCheckpoint $controllerCheckpointPath
$script:ControllerRecoveryMode = $false
if ($null -ne $script:ControllerState -and $script:ControllerState.state -in @('RUNNING','CHECKPOINTED')) {
    $script:ControllerState = Set-ControllerInterrupted $WorkspaceDir $controllerCheckpointPath $script:ControllerState 'Controller restart after interruption; inspect preserved periodic checkpoint and artifacts.'
}
if ($null -ne $script:ControllerState -and $script:ControllerState.state -eq 'BLOCKED') { throw "BLOCKED: $($script:ControllerState.block_reason)" }
if ($null -ne $script:ControllerState -and $script:ControllerState.state -eq 'RECOVERY_REQUIRED') {
    $CurrentInstruction = Get-ControllerRecoveryInstruction $script:ControllerState
    $script:ControllerRecoveryMode = $true
    $ConversationId = $null
}
if ($null -ne $script:ControllerState -and $script:ControllerState.state -eq 'PENDING' -and $script:ControllerState.next_instruction) {
    $CurrentInstruction = (Resolve-ControllerInstruction $WorkspaceDir $script:ControllerState.next_instruction).instruction
    $ConversationId = $null
}
$session = (Get-ControllerEvidence $WorkspaceDir).session
if ($session.active) { throw "BLOCKED: repository session still active for $($session.agent); reconcile ownership before AGY execution." }

$CurrentTurn = $StartTurn
Set-Location $WorkspaceDir

# One automatic recovery is allowed per controller turn for the narrow case where
# Antigravity attempts to read a temporary brain/scratch artifact that does not
# exist. This is a tooling recovery only: it must not resubmit/recompute HPC work.
$MissingArtifactRecoveryUsed = @{}

# Prevent endless account cycling for one logical AGY turn.
$AgyQuotaRotationAttemptsByTurn = @{}

# Prevent endless streaming transport retries for one logical AGY turn.
$AgyTransportRecoveryAttemptsByTurn = @{}

# Prevent endless transient 503/network retries for one logical AGY turn.
$AgyTransientRetriesByTurn = @{}
$AgyEmptyRecoveryAttemptsByTurn = @{}
$AgyTimeoutRecoveryAttemptsByTurn = @{}

:MainLoop while ($CurrentTurn -le ($StartTurn + $MaxTurns - 1)) {
    # Reconcile every dispatch, including router-generated follow-up instructions.
    $resolved = Resolve-ControllerInstruction $WorkspaceDir $CurrentInstruction
    if (-not $script:ControllerRecoveryMode) { $CurrentInstruction=$resolved.instruction }
    if ($resolved.evidence.session.active) { throw 'BLOCKED: another repository session is active' }
    $recoveryCount = if ($script:ControllerRecoveryMode) { 1 } else { 0 }
    $script:ControllerState = New-ControllerTurnState $resolved.evidence $CurrentTurn $CurrentInstruction $recoveryCount
    Write-ControllerCheckpoint $controllerCheckpointPath $script:ControllerState
    Adopt-ExternalAgySwitchAtBoundary
    $script:LastAgyQuotaError = ''
    if ($EnableSmartAgyProfileSelection) {
        $current = Get-CurrentAgyProfileName
        $ready = $false
        try {
            $payload = Get-AgyQuotaProviderJson -Profile $current
            if ($payload.profile_identity -ne (Get-AgySavedProfileIdentity -Profile $current)) { throw 'Quota identity mismatch' }
            $record = ConvertTo-AgySmartQuotaRecord -Profile $current -Payload $payload -GroupRegex $SmartQuotaGroupRegex
            $ready = (Test-AgyQuotaHeadroom -Record $record -ShortThreshold $QuotaStopThresholdPct -LongThreshold ([Math]::Max(20, $SmartMinLongRemainingPct))) -and -not (Get-AgySmartCooldownActive -Profile $current)
        } catch { Write-Warning "[SMART-AGY] Current profile quota cannot be qualified: $($_.Exception.Message)" }
        if (-not $ready) { $null = Invoke-AgySmartSelection -ExcludeProfile $current -Reason 'PRE_TURN_BOTH_WINDOWS' }
    }
    Ensure-AuthoritativeAgyProfile "TURN_START"
    Write-Host "`n----------------------------------------------------------" -ForegroundColor Yellow
    Write-Host " TURN $CurrentTurn STARTING " -ForegroundColor Yellow
    Write-Host "----------------------------------------------------------" -ForegroundColor Yellow
    $previewText = if ($CurrentInstruction.Length -gt 120) { $CurrentInstruction.Substring(0, 120) } else { $CurrentInstruction }
    Write-LoopLog -Turn $CurrentTurn -Tier "CONTROLLER" -Action "INSTRUCTION_DISPATCH" -Message "Prompt: ${previewText}..."

    # ------------------------------------------------------------
    # 2. Invoke Antigravity CLI (agy.exe)
    # ------------------------------------------------------------
    $agyArgs = @()

    if (-not [string]::IsNullOrWhiteSpace($ConversationId)) {
        $agyArgs += "--conversation"
        $agyArgs += $ConversationId
    }

    if (-not [string]::IsNullOrWhiteSpace($Model)) {
        $agyArgs += "--model"
        $agyArgs += $Model
    }

    $agyArgs += "--input-format"
    $agyArgs += "text"
    $agyArgs += "--output-format"
    $agyArgs += "stream-json"
    $effectivePrintTimeout = if ($script:ControllerRecoveryMode) { '180s' } else { $PrintTimeout }
    $budgetMatch = [regex]::Match($effectivePrintTimeout, '^(\d+)(s|m|h)$')
    if (-not $budgetMatch.Success) { throw "Unsupported print timeout: $effectivePrintTimeout" }
    $requestedSeconds = [int]$budgetMatch.Groups[1].Value * @{s=1;m=60;h=3600}[$budgetMatch.Groups[2].Value]
    $controllerBudget = Get-ControllerBudget $effectivePrintTimeout $ScientificTurnSeconds
    $effectivePrintTimeout = "$($controllerBudget.work)s"
    $agyArgs += "--print-timeout"
    $agyArgs += $effectivePrintTimeout
    if ($AllowSkipPermissions) {
        $agyArgs += "--dangerously-skip-permissions"
    }

    # Always prepend the CLI artifact/tool guard, including on ChatGPT/router
    # follow-up turns. This prevents Turn 2+ from forgetting the restriction.
    # TURN10_NONINTERACTIVE_GUARD_V1
    $CurrentInstruction = "Use powershell.exe -NoProfile -NonInteractive for generated shell commands. Always supply explicit -Path and -ChildPath to Join-Path; missing paths are technical errors to diagnose locally. Never wait for a terminal parameter prompt. Do not use timer tools with empty arguments. Recover existing PBS IDs before any submission.`r`n" + $CurrentInstruction
    $bootstrapCommands=''
    if($script:ControllerState.requires_scientific_checkpoint){
        $entry=Join-Path $WorkspaceDir 'scripts/controller/Invoke-ControllerTurn.ps1'
        $common=' -Workspace "'+$WorkspaceDir+'" -RunId '+$script:ControllerState.run_id+' -TaskId '+$script:ControllerState.task_id
        $bootstrapCommands="FIRST TOOL CALL: powershell.exe -NoProfile -NonInteractive -ExecutionPolicy Bypass -File `"$entry`" -Stage Bootstrap$common`nSECOND TOOL CALL: powershell.exe -NoProfile -NonInteractive -ExecutionPolicy Bypass -File `"$entry`" -Stage Scientific$common`nTHIRD TOOL CALL: powershell.exe -NoProfile -NonInteractive -ExecutionPolicy Bypass -File `"$entry`" -Stage Complete$common`nThese canonical -File commands implement ordered bootstrap/claim, the source-pinned F1597 numerical operation, verified evidence and selective closeout. Do not generate nested -Command scripts, reread bootstrap files, or repeat F1596. Execute the stages once in order, report the actual measured result and next correction step, then finish. A generic status note is not a scientific checkpoint. If a stage fails, report its exact error; do not substitute invented measurements.`n"
    }
    $EffectiveInstruction = $bootstrapCommands + (Get-AgyCompactRules) + "`nThe canonical Bootstrap stage performs required prerequisite reads in order; once its receipt is COMPLETE, proceed to the scientific operation without rereading it. Work budget: $($controllerBudget.work) seconds. The controller reserves $($controllerBudget.closeout) seconds for local evidence reconciliation. Create the owned session report with exact sources and the first concrete finding or blocker within 120 seconds; update it every 180 seconds. Metadata/tool chatter does not reset the $NoProgressSeconds-second saved-result deadline; close the session before the work deadline and emit a final response. `n" + $script:PendingSmartProfileContext + "`n" + $CurrentInstruction

    # ------------------------------------------------------------
    # 2. Invoke Antigravity CLI (agy.exe) with hardened error guard
    # ------------------------------------------------------------
    $prevEAP = $ErrorActionPreference

    $nativePrefExists = $null -ne (
        Get-Variable -Name PSNativeCommandUseErrorActionPreference `
            -ErrorAction SilentlyContinue
    )

    if ($nativePrefExists) {
        $prevNativeEAP = $PSNativeCommandUseErrorActionPreference
    }

    $script:ControllerReceiptVerified = $false
    $preservedResponse = $null
    $agyRawOutput = $null
    $agyExitCode = $null
    $agyInvocationException = $null
    $turnStartTime = [DateTimeOffset]::UtcNow

    try {
        $ErrorActionPreference = "Continue"

        if ($nativePrefExists) {
            $PSNativeCommandUseErrorActionPreference = $false
        }

        Set-AndVerifyAgyRunProfile "PRE_AGY"

        try {
            # Independent deadline: CLI print-timeout can emit output without exiting.
            . (Join-Path $WorkspaceDir 'scripts/validation/Invoke-BoundedAgyProcess.ps1')
            $timeoutMatch = [regex]::Match($effectivePrintTimeout, '^(\d+)(s|m|h)$')
            if (-not $timeoutMatch.Success) { throw "Unsupported PrintTimeout: $PrintTimeout" }
            $unitSeconds = @{s=1; m=60; h=3600}[$timeoutMatch.Groups[2].Value]
            $hardTimeout = $controllerBudget.work
            $script:ControllerState.state='RUNNING'
            Write-ControllerCheckpoint $controllerCheckpointPath $script:ControllerState
            $livePath=Join-Path $PadDir ('controller-turn-'+$script:ControllerState.run_id+'.jsonl')
            $script:ControllerState | Add-Member -NotePropertyName live_output_log -NotePropertyValue $livePath -Force
            $agyArgs += @('--log-file',($livePath+'.cli.log'))
            [void](Test-ControllerDurableProgress $script:ControllerState)
            Write-Host "[PROGRESS] live log=$livePath; stop after ${NoProgressSeconds}s without a saved report/result; tokens and session metadata do not count."
            $boundedRun = Invoke-BoundedAgyProcess -FilePath $AgyPath -ArgumentList $agyArgs -InputText $EffectiveInstruction -TimeoutSeconds $hardTimeout -WorkingDirectory $WorkspaceDir -Checkpoint { Update-ControllerEvidence $WorkspaceDir $controllerCheckpointPath $script:ControllerState } -OnStarted { param($ownedProcessId) $script:ControllerState.process_id=$ownedProcessId; Write-ControllerCheckpoint $controllerCheckpointPath $script:ControllerState } -NoProgressSeconds $NoProgressSeconds -ProgressProbe { Test-ControllerDurableProgress $script:ControllerState } -OutputLogPath $livePath -OnOutput {param($chunk) Write-ControllerStreamEvent $script:ControllerState $chunk}
            $script:ControllerState.stop_reason=$boundedRun.StopReason
            $script:ControllerState | Add-Member -NotePropertyName captured_raw_output -NotePropertyValue $boundedRun.Output -Force
            if($script:ControllerState.conversation_id){$ConversationId=$script:ControllerState.conversation_id}
            $agyRawOutput = ConvertFrom-ControllerStream $boundedRun.Output
            $agyExitCode = $boundedRun.ExitCode
            if ($boundedRun.TimedOut) {
                [IO.File]::WriteAllText((Join-Path $PadDir 'controller_watchdog_last_partial.log'), [string]$boundedRun.Output, [Text.UTF8Encoding]::new($false))
                $completedReceipt = Get-AgyCompletedReceipt -WorkspaceDir $WorkspaceDir -Since $turnStartTime
                if ($null -ne $completedReceipt) {
                    $agyRawOutput = @{conversation_id=$ConversationId;status='SUCCESS';response=$completedReceipt.content;usage=$null} | ConvertTo-Json -Depth 5
                    $agyExitCode = 0
                    $script:ControllerReceiptVerified = $true
                    $ConversationId = $null
                    $ConversationIdSource = 'fresh-after-watchdog-receipt'
                    Write-LoopLog -Turn $CurrentTurn -Tier 'CONTROLLER' -Action 'AGY_WATCHDOG_COMPLETED_RECEIPT' -Message "Recovered fresh completed task $($completedReceipt.task_id) from disk; raw partial output preserved."
                } else {
                    # Rejoin the common timeout path AFTER strict POST_AGY verification.
                    $agyRawOutput = '[agy] print timeout returning partial output' + "`n" + (@{conversation_id=$ConversationId;status='SUCCESS';response='';usage=$null}|ConvertTo-Json)
                    $agyExitCode = 0

                }
            }
        }
        catch {
            $agyInvocationException = $_

            if ($null -ne $LASTEXITCODE) {
                $agyExitCode = $LASTEXITCODE
            }
            else {
                $agyExitCode = 1
            }
        }

        $turnDurationSeconds =
            ([DateTimeOffset]::UtcNow - $turnStartTime).TotalSeconds

        $outputLines = foreach ($item in @($agyRawOutput)) {
            if ($item -is [System.Management.Automation.ErrorRecord]) {
                $item.Exception.Message
            }
            else {
                [string]$item
            }
        }

        $agyText = $outputLines -join "`r`n"
        if (Test-IsAgyQuotaLimitError -Message $agyText) { $script:LastAgyQuotaError = $agyText }

        if ($agyInvocationException) {
            $agyText =
                "INVOCATION_EXCEPTION: " +
                $agyInvocationException.Exception.Message +
                "`r`n" +
                $agyText
        }
    }
    finally {
        $ErrorActionPreference = $prevEAP

        if ($nativePrefExists) {
            $PSNativeCommandUseErrorActionPreference = $prevNativeEAP
        }
    }

    if ($null -eq $agyExitCode) {
        $agyExitCode = 1
    }
    if ($agyExitCode -eq 0) { $script:PendingSmartProfileContext = '' }

    if (($script:ControllerRecoveryMode -or $ControlledSingleTurn) -and ($agyExitCode -ne 0 -or $agyInvocationException)) { throw 'BLOCKED: recovery process failure; no retry' }
    if ($agyExitCode -ne 0 -or $agyInvocationException) {

        Write-Host `
            "[AGY-PROCESS-FAIL] agy.exe exit code: $agyExitCode" `
            -ForegroundColor Red

        if (-not [string]::IsNullOrWhiteSpace($agyText)) {

            $snippet = $agyText

            if ($snippet.Length -gt 1500) {
                $snippet = $snippet.Substring(0, 1500) +
                    "`r`n...[truncated]"
            }

            Write-Host "[AGY-DIAGNOSTIC-OUTPUT]" -ForegroundColor Red
            Write-Host $snippet -ForegroundColor Red
        }

        $failureLog = Join-Path `
            $env:USERPROFILE `
            "OpenClawPAD\agy_last_failure.log"

        try {
            @"
Timestamp: $(Get-Date -Format o)
Turn: $CurrentTurn
Conversation: $ConversationId
ExitCode: $agyExitCode

$agyText
"@ | Set-Content -Path $failureLog -Encoding UTF8
        }
        catch {}
    }

    if (
        $agyExitCode -ne 0 -and
        $agyText -match '(?i)Individual quota reached' -and
        -not $EnableSmartAgyProfileSelection
    ) {
        Set-AndVerifyAgyRunProfile "AGY_QUOTA_FAILURE_RECOVERY"

        Write-LoopLog `
            -Turn $CurrentTurn `
            -Tier "CONTROLLER" `
            -Action "AGY_INDIVIDUAL_QUOTA_REACHED" `
            -Message "The run-locked profile '$script:RunLockedAgyProfile' reached its individual quota. Failing closed without account rotation."

        Save-LoopStatus `
            -Turn $CurrentTurn `
            -Status "FAILED" `
            -Tier "CONTROLLER" `
            -Action "AGY_INDIVIDUAL_QUOTA_EXHAUSTED" `
            -Details "The run-locked Antigravity profile '$script:RunLockedAgyProfile' has reached its individual quota. Automatic profile substitution is disabled."

        throw @"
The run-locked Antigravity profile '$script:RunLockedAgyProfile'
has reached its individual quota.

Automatic profile substitution is disabled.
The controller will not continue using another account.
"@
    }

    # Keep the result durable even if the post-call credential store was changed externally.
    [IO.File]::WriteAllText((Join-Path $PadDir 'controller_last_agy_result.log'), [string]$agyText, [Text.UTF8Encoding]::new($false))
    try { Set-AndVerifyAgyRunProfile "POST_AGY" }
    catch {
        Save-LoopState -Turn ($CurrentTurn - 1) -Status 'POST_AGY_CREDENTIAL_VERIFICATION_FAILED' -LastInstruction $CurrentInstruction -LastResponse $agyText -NextInstruction 'Reconcile existing partial result, current session and PBS receipts before any scientific action. Repair credential identity verification; never replay submissions.' -Duration $turnDurationSeconds -Usage $null -Tier 'CONTROLLER' -Action 'POST_AGY_CREDENTIAL_VERIFICATION_FAILED'
        Save-LoopStatus -Turn $CurrentTurn -Status 'FAILED' -Tier 'CONTROLLER' -Action 'POST_AGY_CREDENTIAL_VERIFICATION_FAILED' -Details $_.Exception.Message
        throw
    }

    if ($agyExitCode -ne 0) {

        $errText = $agyText

        $isQuotaFailure = Test-IsAgyQuotaLimitError `
            -Message $errText


        if (
            $AutoRotateAgyProfileOnAgyQuotaError -and
            $isQuotaFailure
        ) {

            $turnKey = [string]$CurrentTurn

            $attempts = if (
                $AgyQuotaRotationAttemptsByTurn.ContainsKey($turnKey)
            ) {
                [int]$AgyQuotaRotationAttemptsByTurn[$turnKey]
            }
            else {
                0
            }


            if ($attempts -lt $AgyProfileRotationOrder.Count) {

                try {

                    $rotation = Switch-ToNextAgyProfile

                    $AgyQuotaRotationAttemptsByTurn[$turnKey] = (
                        $attempts + 1
                    )


                    Write-LoopLog `
                        -Turn $CurrentTurn `
                        -Tier "CONTROLLER" `
                        -Action "AGY_QUOTA_AUTO_PROFILE_ROTATION" `
                        -Message (
                            "AGY quota/rate-limit process failure. " +
                            "Rotated profile '$($rotation.previous_profile)' -> " +
                            "'$($rotation.new_profile)'. " +
                            "Old conversation '$($rotation.previous_conversation)' " +
                            "will NOT be reused. Retrying same logical instruction."
                        )


                    # CurrentInstruction has NOT completed.
                    # Retry the same logical turn under the fresh account.
                    continue MainLoop
                }
                catch {

                    Write-LoopLog `
                        -Turn $CurrentTurn `
                        -Tier "CONTROLLER" `
                        -Action "AGY_QUOTA_AUTO_ROTATION_FAILED" `
                        -Message $_.Exception.Message
                }
            }
        }


                # ------------------------------------------------------------
        # AGY transient 503 / network connection retry (process failure)
        # ------------------------------------------------------------
        $isTransientFailure = Test-IsAgyTransientNetworkOr503Error -Message $errText

        if ($isTransientFailure) {
            $turnKey = [string]$CurrentTurn
            $transientAttempts = if ($AgyTransientRetriesByTurn.ContainsKey($turnKey)) {
                [int]$AgyTransientRetriesByTurn[$turnKey]
            } else { 0 }

            if ($transientAttempts -lt 3) {
                $AgyTransientRetriesByTurn[$turnKey] = $transientAttempts + 1
                $backoffSec = 30 * ($transientAttempts + 1)

                Write-LoopLog `
                    -Turn $CurrentTurn `
                    -Tier "CONTROLLER" `
                    -Action "AGY_503_TRANSIENT_RETRY" `
                    -Message "Transient 503/network process failure detected (attempt $($transientAttempts + 1)/3): $errText. Sleeping ${backoffSec}s before retrying turn."

                Start-Sleep -Seconds $backoffSec
                continue MainLoop
            }
        }

        Write-LoopLog `
            -Turn $CurrentTurn `
            -Tier "CONTROLLER" `
            -Action "AGY_CRASH_FAIL_CLOSED" `
            -Message "Exit code ${agyExitCode} - ${errText}"

        Save-LoopStatus `
            -Turn $CurrentTurn `
            -Status "FAILED" `
            -Tier "CONTROLLER" `
            -Action "AGY_PROCESS_ERROR" `
            -Details $errText

        break MainLoop
    }

    $agyText = ($agyRawOutput | Out-String).Trim()
    if ([string]::IsNullOrWhiteSpace($agyText)) {
        Write-LoopLog -Turn $CurrentTurn -Tier "CONTROLLER" -Action "AGY_EMPTY_FAIL_CLOSED" -Message "Empty stdout from agy"
        Save-LoopStatus -Turn $CurrentTurn -Status "FAILED" -Tier "CONTROLLER" -Action "AGY_EMPTY_OUTPUT" -Details "No output"
        break MainLoop
    }

    # Parse the result envelope without treating stderr warnings as JSON.
    . (Join-Path $WorkspaceDir 'scripts/validation/ConvertFrom-AgyEnvelope.ps1')
    try {
        $agyObj = ConvertFrom-AgyEnvelope -Text $agyText
        $cleanJson = $agyObj | ConvertTo-Json -Depth 30
    } catch {
        Write-LoopLog -Turn $CurrentTurn -Tier "CONTROLLER" -Action "AGY_PARSE_ERROR" -Message "No complete AGY envelope: $_"
        Save-LoopState -Turn ($CurrentTurn - 1) -Status 'AGY_PARSE_ERROR' -LastInstruction $CurrentInstruction -LastResponse $agyText -NextInstruction 'Inspect existing session, ledgers and scheduler before further work. Recover incomplete CLI output; never replay submissions.' -Duration $turnDurationSeconds -Usage $null -Tier 'CONTROLLER' -Action 'AGY_PARSE_ERROR'
        Save-LoopStatus -Turn $CurrentTurn -Status "FAILED" -Tier "CONTROLLER" -Action "JSON_PARSE_ERROR" -Details $_.Exception.Message
        break MainLoop
    }

    # If this was a new workflow, agy created the real conversation. Capture it
    # immediately so every subsequent turn uses the exact returned ID.
    if (
        [string]::IsNullOrWhiteSpace($ConversationId) -and
        $agyObj.conversation_id -and
        -not [string]::IsNullOrWhiteSpace([string]$agyObj.conversation_id)
    ) {
        $ConversationId = [string]$agyObj.conversation_id
        $ConversationIdSource = "created-by-agy"

        Write-LoopLog `
            -Turn $CurrentTurn `
            -Tier "CONTROLLER" `
            -Action "AGY_CONVERSATION_CREATED" `
            -Message "Captured Antigravity conversation ID: $ConversationId"
    }

    if ($agyText -match '(?i)\[agy\] print timeout.*returning partial output') {
        # Timeout JSON may contain a tool message rather than a final scientific report.
        # Salvage only a newly completed, released session with an existing report.
        $diskSalvage = Get-AgyCompletedReceipt -WorkspaceDir $WorkspaceDir -Since $turnStartTime
        $sessionFile = Join-Path $WorkspaceDir 'project_coordination/ACTIVE_SESSION.json'
        $freshCompletedReport = $false
        if ($null -ne $diskSalvage -and (Test-Path -LiteralPath $sessionFile)) {
            $reportFile = Join-Path $WorkspaceDir $diskSalvage.session_report
            if (Test-Path -LiteralPath $reportFile) {
                $freshCompletedReport = (Get-Item -LiteralPath $sessionFile).LastWriteTimeUtc -ge $turnStartTime.UtcDateTime -and (Get-Item -LiteralPath $reportFile).LastWriteTimeUtc -ge $turnStartTime.UtcDateTime
            }
        }
        if ($freshCompletedReport) {
            $preservedResponse = $diskSalvage.content
            $script:ControllerReceiptVerified = $true
            Write-LoopLog -Turn $CurrentTurn -Tier 'CONTROLLER' -Action 'AGY_TIMEOUT_COMPLETED_SESSION' -Message 'Print timeout received; fresh released session report recovered. No work replayed.'
            $ConversationId = $null
            $ConversationIdSource = 'fresh-after-timeout-completed-session'
        } else {
            $script:ControllerState = Set-ControllerInterrupted $WorkspaceDir $controllerCheckpointPath $script:ControllerState $(if($script:ControllerState.captured_raw_output){$script:ControllerState.captured_raw_output}else{$agyText})
            $recovery = if ($script:ControllerState.state -eq 'BLOCKED') { $script:ControllerState.next_safe_action } else { Get-ControllerRecoveryInstruction $script:ControllerState }
            Save-LoopState -Turn $CurrentTurn -Status $script:ControllerState.state -LastInstruction $CurrentInstruction -LastResponse $agyText -NextInstruction $recovery -Duration $turnDurationSeconds -Usage $null -Tier 'CONTROLLER' -Action 'AGY_TIMEOUT_CHECKPOINTED'
            if ($script:ControllerState.state -eq 'BLOCKED') {
                Write-LoopLog -Turn $CurrentTurn -Tier 'CONTROLLER' -Action 'BLOCKED' -Message $script:ControllerState.block_reason
                break MainLoop
            }
            Write-LoopLog -Turn $CurrentTurn -Tier 'CONTROLLER' -Action 'RECOVERY_REQUIRED' -Message 'Partial evidence checkpointed. Next turn is a fresh bounded evidence-only recovery; no original instruction replay.'
            $CurrentInstruction = $recovery
            $script:ControllerRecoveryMode = $true
            $ConversationId = $null
            $CurrentTurn++
            continue MainLoop
        }
    }

    if (($script:ControllerRecoveryMode -or $ControlledSingleTurn) -and $agyObj.status -ne 'SUCCESS') { throw 'BLOCKED: recovery returned an error; no retry' }
    if ($agyObj.status -ne "SUCCESS") {
        $errMsg = if ($agyObj.error) {
            [string]$agyObj.error
        }
        else {
            "No explicit error message"
        }

        # ------------------------------------------------------------
        # AGY disk session salvage (status error)
        #
        # If agy reported an error (503 UNAVAILABLE, stream interrupted,
        # socket abort, etc.), but the agent already finished its task,
        # released ACTIVE_SESSION.json, and wrote a valid session report,
        # salvage that report directly from disk rather than failing!
        # ------------------------------------------------------------
        $diskSalvage = Test-SalvageAgySessionFromDisk -WorkspaceDir $WorkspaceDir
        if ($null -ne $diskSalvage) {
            $preservedResponse = $diskSalvage.content

            Write-LoopLog `
                -Turn $CurrentTurn `
                -Tier "CONTROLLER" `
                -Action "AGY_DISK_SESSION_SALVAGED" `
                -Message (
                    "AGY reported status '$($agyObj.status)' ($errMsg), but Task '$($diskSalvage.task_id)' was successfully completed on disk, " +
                    "ACTIVE_SESSION.json was released (active=false), and session report '$($diskSalvage.session_report)' ($($preservedResponse.Length) chars) is verified. " +
                    "Salvaging session report from disk and proceeding to bridge escalation; subsequent turn will start with a fresh conversation."
                )

            if (Get-Variable -Name AgyContextRecoveryAttempts -Scope Script -ErrorAction SilentlyContinue) {
                $script:AgyContextRecoveryAttempts = 0
            }
            $turnKey = [string]$CurrentTurn
            if (Get-Variable -Name AgyTransientRetriesByTurn -Scope Script -ErrorAction SilentlyContinue) {
                $script:AgyTransientRetriesByTurn.Remove($turnKey)
            }

            # Reset conversation ID so the next turn starts in a fresh uncorrupted session
            $ConversationId = $null
            $ConversationIdSource = "fresh-after-disk-salvaged-turn"

            # Bypass error exit; proceed directly to $agentResponse processing
        }
        else {

        # ------------------------------------------------------------
        # AGY lifecycle recovery: context canceled / stream interrupted / tool schema
        #
        # Antigravity can finish substantive work and/or perform side
        # effects before agy reports the lifecycle error
        # "context canceled" or "The stream was interrupted".
        # ------------------------------------------------------------

        $isAgyRecoverableLifecycleError = (
            $agyObj.status -eq "ERROR" -and
            (
                $errMsg -match '(?i)\bcontext canceled\b' -or
                $errMsg -match "(?i)additional properties 'ArtifactMetadata' not allowed" -or
                $errMsg -match "(?i)invalid arguments:.*missing property 'Pattern'" -or
                $errMsg -match '(?i)cannot kill task .*DONE' -or
                $errMsg -match '(?i)\bstream was interrupted\b' -or
                $errMsg -match '(?i)(malformed function call|failed to parse function call|improperly formatted function call|function call is empty)'
            )
        )

        $preservedResponse = if ($agyObj.response) {
            [string]$agyObj.response
        }
        else {
            ""
        }

        if ($isAgyRecoverableLifecycleError -and ($preservedResponse.Trim().Length -ge 100)) {

            Write-LoopLog `
                -Turn $CurrentTurn `
                -Tier "CONTROLLER" `
                -Action "AGY_LIFECYCLE_RESPONSE_SALVAGED" `
                -Message (
                    "Transport/lifecycle error '$errMsg' occurred, but AGY preserved a substantive response " +
                    "($($preservedResponse.Length) chars). Salvaging response and proceeding to bridge processing; " +
                    "subsequent turn will start with a fresh conversation."
                )

            if (
                Get-Variable `
                    -Name AgyContextRecoveryAttempts `
                    -Scope Script `
                    -ErrorAction SilentlyContinue
            ) {
                $script:AgyContextRecoveryAttempts = 0
            }

            # Reset conversation ID so the next turn starts in a fresh uncorrupted session
            $ConversationId = $null
            $ConversationIdSource = "fresh-after-salvaged-turn"

            # Bypass error exit; proceed directly to $agentResponse processing
        }
        elseif ($isAgyRecoverableLifecycleError) {

            if (-not (
                Get-Variable `
                    -Name AgyContextRecoveryAttempts `
                    -Scope Script `
                    -ErrorAction SilentlyContinue
            )) {
                $script:AgyContextRecoveryAttempts = 0
            }

            if ($script:AgyContextRecoveryAttempts -lt 1) {

                $script:AgyContextRecoveryAttempts++

                $deadConversationId = $ConversationId
                # Reset ConversationId to null so recovery runs in a FRESH conversation
                $ConversationId = $null
                $ConversationIdSource = "recovery-fresh-conversation"

                Write-LoopLog `
                    -Turn $CurrentTurn `
                    -Tier "CONTROLLER" `
                    -Action "AGY_LIFECYCLE_TOOLING_RECOVERY" `
                    -Message (
                        "Lifecycle error '$errMsg' detected with empty/truncated response. " +
                        "DeadConversationId=$deadConversationId. " +
                        "Starting one state-aware recovery continuation on a FRESH conversation."
                    )

                Save-LoopStatus `
                    -Turn $CurrentTurn `
                    -Status "RECOVERING" `
                    -Tier "CONTROLLER" `
                    -Action "AGY_LIFECYCLE_TOOLING_RECOVERY" `
                    -Details (
                        "DeadConversationId=$deadConversationId; " +
                        "Error=$errMsg; " +
                        "PreservedResponseLength=$($preservedResponse.Length)"
                    )

                $CurrentInstruction = @"
RECOVERY CONTINUATION AFTER AGY LIFECYCLE ERROR

The immediately preceding Antigravity execution ended with this recoverable AGY lifecycle/tooling error:

$errMsg

Previous Interrupted Conversation ID:
$deadConversationId

This is a controller/AGY lifecycle recovery turn running in a fresh conversation.

DO NOT restart or replay the preceding task from the beginning.

The preceding execution may already have modified files, updated ledgers,
submitted an HPC/PBS job, or completed substantial work.

FIRST recover authoritative state from the existing workspace.

Inspect:

1. project_coordination/ACTIVE_SESSION.json
2. project_coordination/ACTIVE_TASK.json
3. project_coordination/HPC_JOB_LEDGER.csv
4. project_coordination/TASK_LEDGER.csv
5. files modified during the immediately preceding execution
6. controller/recovered response evidence where available
7. the HPC scheduler for any PBS job created during the preceding execution

If a PBS job was already submitted:

- preserve its exact PBS job ID;
- DO NOT submit another copy;
- query/evaluate that exact existing job;
- if it is Q or R with no required intervention, report the exact state and stop;
- if it is terminal, retrieve and evaluate its actual output/evidence before deciding
  what work remains.

If no PBS job was submitted:

- preserve all valid completed file changes;
- continue only from the first genuinely incomplete operation;
- do not repeat completed side effects.

If the preceding execution already completed the requested work despite the lifecycle
error, recover that result rather than repeating it.

Do not infer authorization from this recovery instruction.
Preserve all existing HPC authorization, replacement-count, scientific, Git,
notification, frozen-thesis, and safety rules from the repository coordination state.

Do not qdel or qmove unless separately authorized.
Do not commit or push unless separately authorized.

At the end report exactly what was recovered and what remains.

Finished
"@

                continue MainLoop
            }

            Write-LoopLog `
                -Turn $CurrentTurn `
                -Tier "CONTROLLER" `
                -Action "AGY_LIFECYCLE_TOOLING_RECOVERY_EXHAUSTED" `
                -Message (
                    "A second recoverable AGY lifecycle/tooling failure occurred after " +
                    "the single permitted recovery continuation. Failing closed."
                )

            Save-LoopStatus `
                -Turn $CurrentTurn `
                -Status "FAILED" `
                -Tier "CONTROLLER" `
                -Action "AGY_LIFECYCLE_TOOLING_RECOVERY_EXHAUSTED" `
                -Details (
                    "ConversationId=$ConversationId; Error=$errMsg"
                )

            break MainLoop
        }
        else {

            Write-LoopLog `
                -Turn $CurrentTurn `
                -Tier "CONTROLLER" `
                -Action "AGY_STATUS_ERROR" `
                -Message "Status was $($agyObj.status) - $errMsg"

            # ------------------------------------------------------------
            # AGY quota/rate-limit recovery.
            # Only explicit quota/rate-limit signals qualify.
            # Do NOT apply this to arbitrary tooling/scientific failures.
            # ------------------------------------------------------------

            $isAgyQuotaFailure = Test-IsAgyQuotaLimitError `
                -Message $errMsg

            if (
                $AutoRotateAgyProfileOnAgyQuotaError -and
                $isAgyQuotaFailure
            ) {

                $turnKey = [string]$CurrentTurn

                $attempts = if (
                    $AgyQuotaRotationAttemptsByTurn.ContainsKey($turnKey)
                ) {
                    [int]$AgyQuotaRotationAttemptsByTurn[$turnKey]
                }
                else {
                    0
                }

                if ($attempts -lt $AgyProfileRotationOrder.Count) {

                    try {

                        $rotation = Switch-ToNextAgyProfile

                        $AgyQuotaRotationAttemptsByTurn[$turnKey] = (
                            $attempts + 1
                        )

                        Write-LoopLog `
                            -Turn $CurrentTurn `
                            -Tier "CONTROLLER" `
                            -Action "AGY_STATUS_QUOTA_AUTO_PROFILE_ROTATION" `
                            -Message (
                                "AGY reported quota/rate-limit exhaustion. " +
                                "Rotated '$($rotation.previous_profile)' -> " +
                                "'$($rotation.new_profile)'. " +
                                "Previous conversation will not be reused."
                            )

                        continue MainLoop
                    }
                    catch {

                        Write-LoopLog `
                            -Turn $CurrentTurn `
                            -Tier "CONTROLLER" `
                            -Action "AGY_STATUS_QUOTA_ROTATION_FAILED" `
                            -Message $_.Exception.Message
                    }
                }
            }

            # Narrow automatic recovery for a missing TEMPORARY brain/scratch artifact
            $normalizedErrMsg = ($errMsg -replace '\\', '/')

            $isMissingArtifactRead = (
                $errMsg -match '(?i)(view_file|read_file)' -and
                $errMsg -match '(?i)(cannot find the file specified|no such file|failed to read file)' -and
                $normalizedErrMsg -match '(?i)/\.gemini/antigravity-cli/brain/'
            )

            $turnKey = [string]$CurrentTurn
            $alreadyRecovered = (
                $MissingArtifactRecoveryUsed.ContainsKey($turnKey) -and
                [bool]$MissingArtifactRecoveryUsed[$turnKey]
            )

            if ($isMissingArtifactRead -and -not $alreadyRecovered) {
                $MissingArtifactRecoveryUsed[$turnKey] = $true

                Write-LoopLog `
                    -Turn $CurrentTurn `
                    -Tier "CONTROLLER" `
                    -Action "AGY_MISSING_ARTIFACT_AUTO_RECOVERY" `
                    -Message "Recoverable temporary brain artifact read failure detected. Retrying same conversation/turn once without resubmitting HPC work."

                $CurrentInstruction = @"
Recover the CURRENT task after a tooling-only failure.

Your previous attempt failed because you tried to read a temporary Antigravity
brain/scratch artifact that does not exist:

$errMsg

Do NOT call view_file/read_file on that path again unless you first prove the
exact file exists with a bounded existence check.

Continue the SAME scientific task from the evidence already available in this
conversation. Do not restart completed analysis unnecessarily.

If the missing artifact contained a planned offline calculation:
- recompute the result inline, OR
- explicitly create the result inside the current conversation brain directory,
  verify it exists, and only then read it.

Do NOT resubmit or repeat any completed PBS/HPC job.
Do NOT call qdel or qmove.
Do NOT commit or push.
Do not broaden the task.

Return the requested scientific result and end with exactly:
Finished
"@

                continue
            }

            # ------------------------------------------------------------
            # AGY streaming transport/EOF recovery (streamGenerateContent EOF).
            # One-time recovery: reconnects to the existing conversation ID
            # without restarting from scratch or duplicating HPC jobs.
            # ------------------------------------------------------------
            $isStreamEofError = (
                $errMsg -match '(?i)streamGenerateContent.*EOF' -or
                $errMsg -match '(?i)connection reset by peer' -or
                $errMsg -match '(?i)transport error'
            )

            $turnKey = [string]$CurrentTurn
            $alreadyRecoveredTransport = (
                $AgyTransportRecoveryAttemptsByTurn.ContainsKey($turnKey) -and
                [bool]$AgyTransportRecoveryAttemptsByTurn[$turnKey]
            )

            if ($isStreamEofError -and -not $alreadyRecoveredTransport) {
                $AgyTransportRecoveryAttemptsByTurn[$turnKey] = $true

                Write-LoopLog `
                    -Turn $CurrentTurn `
                    -Tier "CONTROLLER" `
                    -Action "AGY_STREAM_EOF_AUTO_RECOVERY" `
                    -Message "Streaming API EOF error detected. Restoring profile and recovering existing conversation '$ConversationId'."

                Ensure-AuthoritativeAgyProfile "STREAM_EOF_RECOVERY"

                # Prompt the existing conversation to recover state without duplicating external work
                $CurrentInstruction = @"
Recover the current session following an upstream API streaming connection drop (streamGenerateContent EOF).

Your conversation context ($ConversationId) and all local/HPC artifacts are intact.
Do NOT duplicate any PBS job submissions or rerun completed analysis.

Inspect the latest status of the running/completed jobs on the cluster, harvest newly completed cases, update the master convergence and energy tables, and report the current scientific synthesis. End with exactly:
Finished
"@

                continue MainLoop
            }

                        # ------------------------------------------------------------
            # AGY transient 503 / network connection retry (status error)
            # ------------------------------------------------------------
            $isTransientError = Test-IsAgyTransientNetworkOr503Error -Message $errMsg

            $turnKey = [string]$CurrentTurn
            $transientAttempts = if ($AgyTransientRetriesByTurn.ContainsKey($turnKey)) {
                [int]$AgyTransientRetriesByTurn[$turnKey]
            } else { 0 }

            if ($isTransientError) {
                if ($transientAttempts -lt 3) {
                    $AgyTransientRetriesByTurn[$turnKey] = $transientAttempts + 1
                    $backoffSec = 30 * ($transientAttempts + 1)

                    Write-LoopLog `
                        -Turn $CurrentTurn `
                        -Tier "CONTROLLER" `
                        -Action "AGY_503_TRANSIENT_RETRY" `
                        -Message "Transient API/network error (503/socket abort) detected (attempt $($transientAttempts + 1)/3): $errMsg. Waiting ${backoffSec}s before retrying turn."

                    Start-Sleep -Seconds $backoffSec
                    continue MainLoop
                }
                elseif ($EnableAutomaticAgyProfileRotation -or $EnableSmartAgyProfileSelection) {
                    $quotaAttempts = if ($AgyQuotaRotationAttemptsByTurn.ContainsKey($turnKey)) {
                        [int]$AgyQuotaRotationAttemptsByTurn[$turnKey]
                    } else { 0 }

                    if ($quotaAttempts -lt $AgyProfileRotationOrder.Count) {
                        try {
                            $rotation = Switch-ToNextAgyProfile
                            $AgyQuotaRotationAttemptsByTurn[$turnKey] = $quotaAttempts + 1
                            $AgyTransientRetriesByTurn[$turnKey] = 0
                            $ConversationId = $null
                            $ConversationIdSource = "fresh-after-503-profile-rotation"

                            Write-LoopLog `
                                -Turn $CurrentTurn `
                                -Tier "CONTROLLER" `
                                -Action "AGY_503_AUTO_PROFILE_ROTATION" `
                                -Message (
                                    "Persistent transient 503/network error after 3 retries on '$($rotation.previous_profile)'. " +
                                    "Auto-rotating profile '$($rotation.previous_profile)' -> '$($rotation.new_profile)'. " +
                                    "Starting fresh conversation."
                                )

                            continue MainLoop
                        }
                        catch {
                            Write-LoopLog `
                                -Turn $CurrentTurn `
                                -Tier "CONTROLLER" `
                                -Action "AGY_503_ROTATION_FAILED" `
                                -Message $_.Exception.Message
                        }
                    }
                }
            }

            Save-LoopStatus `
                -Turn $CurrentTurn `
                -Status "FAILED" `
                -Tier "CONTROLLER" `
                -Action "AGY_STATUS_NOT_SUCCESS" `
                -Details $cleanJson

            break MainLoop
        }
        }
    }

    # Successful AGY turn closes the previous lifecycle-recovery incident.
    if (
        Get-Variable `
            -Name AgyContextRecoveryAttempts `
            -Scope Script `
            -ErrorAction SilentlyContinue
    ) {
        $script:AgyContextRecoveryAttempts = 0
    }

    $agentResponse = if (-not [string]::IsNullOrWhiteSpace($preservedResponse)) {
        $preservedResponse
    }
    else {
        [string]$agyObj.response
    }
    if($ControlledSingleTurn -and (Test-ControllerScientificCheckpoint $WorkspaceDir $script:ControllerState)){
        $completed=Get-Content -LiteralPath $script:ControllerState.bootstrap_record_path -Raw|ConvertFrom-Json
        $report=Join-Path $WorkspaceDir $completed.session_report
        if($completed.stage -eq 'COMPLETE' -and (Test-Path -LiteralPath $report)){
            $script:ControllerReceiptVerified=$true
            if([string]::IsNullOrWhiteSpace($agentResponse)){$agentResponse=Get-Content -LiteralPath $report -Raw}
        }
    }
    if (($script:ControllerRecoveryMode -or $ControlledSingleTurn) -and [string]::IsNullOrWhiteSpace($agentResponse)) { throw 'BLOCKED: empty recovery response; no retry' }
    if ([string]::IsNullOrWhiteSpace($agentResponse)) {
        # 1. Check if task was completed on disk despite the empty agent response
        $diskSalvage = Test-SalvageAgySessionFromDisk -WorkspaceDir $WorkspaceDir
        if ($null -ne $diskSalvage) {
            $agentResponse = $diskSalvage.content
            $script:ControllerReceiptVerified = $true
            Write-LoopLog `
                -Turn $CurrentTurn `
                -Tier "CONTROLLER" `
                -Action "AGY_DISK_SESSION_SALVAGED" `
                -Message (
                    "Agent response field was empty, but Task '$($diskSalvage.task_id)' was successfully completed on disk, " +
                    "ACTIVE_SESSION.json was released (active=false), and session report '$($diskSalvage.session_report)' ($($agentResponse.Length) chars) is verified. " +
                    "Salvaging session report from disk and proceeding to bridge escalation; subsequent turn will start with a fresh conversation."
                )

            $ConversationId = $null
            $ConversationIdSource = "fresh-after-disk-salvaged-turn"
        }
        else {
            $turnKey = [string]$CurrentTurn
            $emptyRecoveries = if ($AgyEmptyRecoveryAttemptsByTurn.ContainsKey($turnKey)) {
                [int]$AgyEmptyRecoveryAttemptsByTurn[$turnKey]
            } else { 0 }

            if ($emptyRecoveries -lt 2) {
                $AgyEmptyRecoveryAttemptsByTurn[$turnKey] = $emptyRecoveries + 1
                Write-LoopLog `
                    -Turn $CurrentTurn `
                    -Tier "CONTROLLER" `
                    -Action "AGY_EMPTY_RESPONSE_AUTO_RECOVERY" `
                    -Message "Agent response field was empty (attempt $($emptyRecoveries + 1)/2). Prompting conversation '$ConversationId' to complete and emit its final scientific report."

                $CurrentInstruction = @"
CONTINUATION INSTRUCTION:
Your immediately preceding tool call or turn completed without emitting a final response text.
Inspect the current state of the workspace and ledgers, complete any remaining verification or closeout steps, and provide your full final scientific report.
End your final response with exactly:
Finished
"@
                continue MainLoop
            }

            Write-LoopLog -Turn $CurrentTurn -Tier "CONTROLLER" -Action "AGY_EMPTY_RESPONSE" -Message "Agent response field is empty after 2 recovery attempts"
            Save-LoopStatus -Turn $CurrentTurn -Status "FAILED" -Tier "CONTROLLER" -Action "EMPTY_RESPONSE" -Details $cleanJson
            break MainLoop
        }
    }

    $completion = Complete-ControllerTurn $WorkspaceDir $controllerCheckpointPath $script:ControllerState $agentResponse -VerifiedReceipt:$script:ControllerReceiptVerified
    if ($completion -eq 'BLOCKED') { throw "BLOCKED: $($script:ControllerState.block_reason)" }
    if($ControlledSingleTurn){
        if(-not(Test-ControllerScientificCheckpoint $WorkspaceDir $script:ControllerState)){throw 'Controlled turn failed to reach a verified scientific operation'}
        $receipt=Get-Content -LiteralPath $script:ControllerState.bootstrap_record_path -Raw|ConvertFrom-Json
        if($receipt.stage -ne 'COMPLETE'){throw 'Controlled turn scientific closeout is incomplete'}
        $refs=@(& git -C $WorkspaceDir rev-parse HEAD origin/main)
        if($refs.Count -ne 2 -or $refs[0] -ne $refs[1] -or $refs[0] -eq $receipt.repository_commit){throw 'Controlled scientific closeout was not committed and synchronized to origin/main'}
        Save-LoopState -Turn $CurrentTurn -Status 'CONTROLLED_SCIENTIFIC_STEP_COMPLETE' -LastInstruction $CurrentInstruction -LastResponse $agentResponse -NextInstruction $receipt.next_action -Duration $turnDurationSeconds -Usage $agyObj.usage -Tier 'CONTROLLER' -Action 'VERIFIED_SCIENTIFIC_OPERATION'
        Write-LoopLog -Turn $CurrentTurn -Tier 'CONTROLLER' -Action 'VERIFIED_SCIENTIFIC_OPERATION' -Message ('Controlled F1597 step completed; next='+$receipt.next_action)
        break MainLoop
    }
    if ($script:ControllerRecoveryMode) {
        Write-LoopLog -Turn $CurrentTurn -Tier 'CONTROLLER' -Action 'COMPLETED_TURN' -Message 'Evidence-only recovery completed; original research instruction was not replayed.'
        Save-LoopState -Turn $CurrentTurn -Status 'RECOVERY_REVIEW_REQUIRED' -LastInstruction $CurrentInstruction -LastResponse $agentResponse -NextInstruction 'CONTROLLER_TASK: NEXT_UNRESOLVED' -Duration $turnDurationSeconds -Usage $null -Tier 'CONTROLLER' -Action 'RECOVERY_COMPLETED'
        break MainLoop
    }

    $tokenCount = if ($agyObj.usage -and $agyObj.usage.total_tokens) { $agyObj.usage.total_tokens } else { 0 }
    Write-LoopLog -Turn $CurrentTurn -Tier "AGY" -Action "COMPLETED_TURN" -Message ("Duration: {0:N2}s, CLI-reported tokens (may be conversation-cumulative): {1}" -f $turnDurationSeconds, $tokenCount)

    # ------------------------------------------------------------------------
    # AGY_QUOTA_GUARD_V1: collect fresh five-hour quota after this AGY turn.
    # This does NOT invoke `agy -p "/usage"`.
    # ------------------------------------------------------------------------
    $quotaSnapshot = $null
    $quotaSnapshotText = "Quota check was not scheduled for this turn."
    $quotaStopPending = $false
    $quotaCheckFailed = $false
    $quotaTelemetryUnavailable = $false

    $turnOrdinalInThisRun = ($CurrentTurn - $StartTurn + 1)
    $quotaCheckDue = (
        $QuotaCheckEveryTurns -gt 0 -and
        (($turnOrdinalInThisRun % $QuotaCheckEveryTurns) -eq 0)
    )

    if ($quotaCheckDue) {
        Ensure-AuthoritativeAgyProfile "PRE_QUOTA_CHECK"
        Write-LoopLog `
            -Turn $CurrentTurn `
            -Tier "CONTROLLER" `
            -Action "QUOTA_CHECK_START" `
            -Message "Checking Antigravity 5-hour quota after AGY turn; threshold is < $QuotaStopThresholdPct%."

        try {
            $quotaSnapshot = Get-AgyFiveHourQuotaSnapshot
            $quotaSnapshotText = Format-AgyQuotaSnapshot -Snapshot $quotaSnapshot

            Write-Host ""
            Write-Host "[QUOTA] $quotaSnapshotText" -ForegroundColor Cyan

            Write-LoopLog `
                -Turn $CurrentTurn `
                -Tier "CONTROLLER" `
                -Action "QUOTA_CHECK_RESULT" `
                -Message ("Minimum selected 5h remaining={0:N3}%; threshold < {1:N3}%; below_threshold={2}" -f `
                    [double]$quotaSnapshot.minimum_remaining_pct, `
                    [double]$QuotaStopThresholdPct, `
                    [bool]$quotaSnapshot.below_threshold)

            if ([bool]$quotaSnapshot.below_threshold) {
                $quotaStopPending = $true
            }
        }
        catch {

            $quotaCheckFailed = $true
            $quotaLastError = $_.Exception.Message
            $quotaRetryRecovered = $false


            for (
                $quotaRetry = 1;
                $quotaRetry -le $QuotaRetryCount;
                $quotaRetry++
            ) {

                Write-LoopLog `
                    -Turn $CurrentTurn `
                    -Tier "CONTROLLER" `
                    -Action "QUOTA_CHECK_RETRY" `
                    -Message (
                        "Quota check retry $quotaRetry of " +
                        "$QuotaRetryCount after: $quotaLastError"
                    )


                if ($quotaLastError -match '(?i)(401|token refresh failed|unauthorized)') {
                    Write-Warning '[PROFILE-GUARD] OAuth quota error: saved profiles will not be overwritten. Re-authenticate the affected account if the error persists.'
                    Ensure-AuthoritativeAgyProfile "QUOTA_401_RETRY_PREP"
                }

                if ($QuotaRetryDelaySeconds -gt 0) {
                    Start-Sleep -Seconds $QuotaRetryDelaySeconds
                }


                try {

                    $quotaSnapshot = Get-AgyFiveHourQuotaSnapshot

                    $quotaSnapshotText = Format-AgyQuotaSnapshot `
                        -Snapshot $quotaSnapshot

                    $quotaCheckFailed = $false
                    $quotaRetryRecovered = $true


                    Write-Host ""
                    Write-Host (
                        "[QUOTA] Retry recovered quota telemetry."
                    ) -ForegroundColor Green

                    Write-Host $quotaSnapshotText -ForegroundColor Cyan


                    Write-LoopLog `
                        -Turn $CurrentTurn `
                        -Tier "CONTROLLER" `
                        -Action "QUOTA_CHECK_RETRY_RECOVERED" `
                        -Message (
                            "Minimum selected 5h remaining={0:N3}%." -f `
                            [double]$quotaSnapshot.minimum_remaining_pct
                        )


                    if ([bool]$quotaSnapshot.below_threshold) {
                        $quotaStopPending = $true
                    }


                    break
                }
                catch {

                    $quotaLastError = $_.Exception.Message
                }
            }


            if (-not $quotaRetryRecovered) {

                $quotaSnapshotText = (
                    "QUOTA CHECK FAILED after " +
                    "$($QuotaRetryCount + 1) attempt(s): " +
                    $quotaLastError
                )


                $isKnownAuth401 = (
                    $quotaLastError -match '(?i)HTTP\s*401' -or
                    $quotaLastError -match '(?i)token refresh failed' -or
                    $quotaLastError -match '(?i)unauthorized'
                )


                if (
                    $ContinueWhenQuotaTelemetryAuthFails -and
                    $isKnownAuth401
                ) {

                    $quotaTelemetryUnavailable = $true

                    # IMPORTANT:
                    # This disables only the external telemetry stop for a manually
                    # selected profile. Smart profile inventory NEVER treats 401
                    # telemetry as usable quota.
                    # This disables only the external telemetry stop.
                    # AGY's own quota/rate-limit response is still a hard
                    # automatic profile-rotation trigger.
                    $quotaStopPending = $false

                    Write-Host "[PROFILE-GUARD] Restoring authoritative profile after quota telemetry auth failure..." -ForegroundColor Yellow
                    Ensure-AuthoritativeAgyProfile "QUOTA_401_POST_FAILURE"

                    Write-LoopLog `
                        -Turn $CurrentTurn `
                        -Tier "CONTROLLER" `
                        -Action "QUOTA_TELEMETRY_AUTH_UNAVAILABLE_CONTINUE" `
                        -Message (
                            "$quotaSnapshotText " +
                            "Continuing because this is the known external " +
                            "aichecker OAuth 401 condition; authoritative profile verified."
                        )
                }
                else {

                    Write-LoopLog `
                        -Turn $CurrentTurn `
                        -Tier "CONTROLLER" `
                        -Action "QUOTA_CHECK_FAILED" `
                        -Message $quotaSnapshotText


                    if ($QuotaCheckFailClosed) {
                        $quotaStopPending = $true
                    }
                }
            }
        }
        Ensure-AuthoritativeAgyProfile "POST_QUOTA_CHECK"
    }

    # Preserve both ordinary AGY token accounting and the plan-quota snapshot.
    $combinedUsage = [PSCustomObject]@{
        agy_usage              = $agyObj.usage
        quota_check_due        = $quotaCheckDue
        quota_check_failed          = $quotaCheckFailed
        quota_telemetry_unavailable = $quotaTelemetryUnavailable
        quota_stop_pending          = $quotaStopPending
        five_hour_quota             = $quotaSnapshot
        five_hour_quota_text   = $quotaSnapshotText
    }

    # ------------------------------------------------------------
    # 3. Synchronize Router State (WSL)
    # ------------------------------------------------------------
    # Run the WSL router to parse and track job state in controller-state.json.
    # Note: As per Rule 1 & Rule 2, router heuristic regex decisions
    # MUST NOT short-circuit scientific/HPC workflows. Every substantive
    # turn escalates directly to Tier-3 ChatGPT.
    $prevEAP = $ErrorActionPreference
    $ErrorActionPreference = "Continue"

    $routerRaw = $agentResponse | & wsl.exe `
        -d OpenClawGateway `
        -u openclaw `
        -- `
        python3 /home/openclaw/.openclaw/workspace-antigravity-controller/run_router.py `
        2>&1

    $routerExit = $LASTEXITCODE
    $ErrorActionPreference = $prevEAP

    if ($routerExit -eq 0) {
        $routerText = ($routerRaw | Out-String).Trim()
        $rJsonStart = $routerText.IndexOf("{")
        if ($rJsonStart -ge 0) {
            try {
                $routerResult = $routerText.Substring($rJsonStart) | ConvertFrom-Json
                Write-LoopLog -Turn $CurrentTurn -Tier "ROUTER" -Action "ROUTER_STATE_SYNC" -Message "Tracked metadata: $($routerResult.tier)/$($routerResult.reason)"
            } catch {}
        }
    } else {
        $rErr = $routerRaw | Out-String
        Write-LoopLog -Turn $CurrentTurn -Tier "ROUTER" -Action "ROUTER_WARN_NONFATAL" -Message "Router state sync warning (exit code ${routerExit}): ${rErr}"
    }

    # ------------------------------------------------------------
    # 4. Escalate Substantive AGY Turn to ChatGPT Bridge (Rule 1, Rule 9)
    # ------------------------------------------------------------
    $NextInstruction = ""
    if ($EnableChatGPTBridge) {
        Write-LoopLog -Turn $CurrentTurn -Tier "tier3_chatgpt" -Action "ESCALATE_CHATGPT" -Message "Escalating substantive turn to ChatGPT bridge..."
        try {
            $NextInstruction = Invoke-EscalationChatGPT -AntigravityResponse $agentResponse -QuotaSnapshotText $quotaSnapshotText
            $gptPreview = if ($NextInstruction.Length -gt 80) { $NextInstruction.Substring(0, 80) } else { $NextInstruction }
            Write-LoopLog -Turn $CurrentTurn -Tier "tier3_chatgpt" -Action "CHATGPT_DISPATCH" -Message "ChatGPT response received: ${gptPreview}..."
        } catch {
            Write-LoopLog -Turn $CurrentTurn -Tier "tier3_chatgpt" -Action "CHATGPT_FAILURE_STOP" -Message "Error: $_"
            Save-LoopStatus -Turn $CurrentTurn -Status "FAILED" -Tier "tier3_chatgpt" -Action "CHATGPT_ERROR" -Details $_.Exception.Message
            break MainLoop
        }
    } else {
        Write-LoopLog -Turn $CurrentTurn -Tier "tier1_antigravity" -Action "DIRECT_AGY_EXECUTION" -Message "ChatGPT bridge disabled; evaluating AGY response directly..."
        if ($agentResponse -match '(?i)\bFinished\b') {
            Write-Host ""
            Write-Host "==========================================================" -ForegroundColor Green
            Write-Host " ANTIGRAVITY COMPLETED INSTRUCTION ('Finished' DETECTED) " -ForegroundColor Green
            Write-Host "==========================================================" -ForegroundColor Green
            Save-LoopStatus -Turn $CurrentTurn -Status "SUCCESS" -Tier "tier1_antigravity" -Action "COMPLETED" -Details "Antigravity completed task ('Finished' detected)."
            break MainLoop
        }
        $NextInstruction = "Continue with the next required action under the active gate and coordination state. Write Finished when done."
    }

    # ------------------------------------------------------------
    # 5. Handle ChatGPT STOP & Scheduler Waiting (Rules 3, 4, 5, 8, 10)
    #
    # Architecture:
    # 1. ChatGPT returns STOP
    # 2. Synchronize $ActiveProductionJobId from ACTIVE_TASK.json or agent response
    # 3. Wait 900 seconds (15 minutes)
    # 4. Query user scheduler table: qstat -u pr21vyci
    # 5. Pass full table + $ActiveProductionJobId to ChatGPT
    # 6. ChatGPT evaluates state:
    #    - R/Q -> replies "stop" (triggering another 15m wait on next turn)
    #    - Absent / Terminal -> instructs Antigravity to run qstat -x and inspect solver evidence
    # ------------------------------------------------------------

    $isStop = (
        [string]::IsNullOrWhiteSpace($NextInstruction) -or
        $NextInstruction -match '^(?i:stop)\s*$'
    )

    if ($isStop) {

        Write-LoopLog `
            -Turn $CurrentTurn `
            -Tier "CONTROLLER" `
            -Action "CHATGPT_STOP_RECEIVED" `
            -Message "ChatGPT STOP received. Entering multi-job scheduler evaluation logic."

        # Collect candidate PBS job IDs strictly matching verified scheduler ID format
        $candidateJobIds = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::OrdinalIgnoreCase)
        $liveRunningJobIds = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::OrdinalIgnoreCase)

        if (-not [string]::IsNullOrWhiteSpace($agentResponse)) {
            $extractedJobIds = Get-ExactPbsJobIdsFromText -Text $agentResponse
            foreach ($jId in $extractedJobIds) {
                if ($jId -match '^1[3-9]\d{5,6}\.mmaster02$') {
                    [void]$candidateJobIds.Add($jId)
                }
            }
        }

        $activeTaskFile = Join-PathStrict -Path $WorkspaceDir -ChildPath "project_coordination\ACTIVE_TASK.json"
        if (Test-Path -LiteralPath $activeTaskFile) {
            try {
                $taskData = Get-Content -LiteralPath $activeTaskFile -Raw | ConvertFrom-Json
                if ($taskData.active_job_id -and [string]$taskData.active_job_id -match '^1[3-9]\d{5,6}\.mmaster02$') {
                    [void]$candidateJobIds.Add([string]$taskData.active_job_id)
                }
                if ($taskData.active_task.governing_rules.active_job_ids) {
                    foreach ($j in @($taskData.active_task.governing_rules.active_job_ids)) {
                        if ([string]$j -match '^1[3-9]\d{5,6}\.mmaster02$') {
                            [void]$candidateJobIds.Add([string]$j)
                        }
                    }
                }
                $fullFractureJob = $taskData.benchmark_anomaly_resolution.priority_a_stiffness_anomaly.active_full_fracture_run.job_id
                if ($fullFractureJob -and [string]$fullFractureJob -match '^1[3-9]\d{5,6}\.mmaster02$') {
                    [void]$candidateJobIds.Add([string]$fullFractureJob)
                }
            } catch {}
        }

        # Query live user queue immediately (no 15-minute blind sleep!)
        $sshConfig = Join-PathStrict -Path $env:USERPROFILE -ChildPath ".ssh\codex_config"
        $RemoteCommand = "qstat -u pr21vyci"

        Write-Host ""
        Write-Host "[SCHEDULER] Querying live user scheduler state (qstat -u pr21vyci)..." -ForegroundColor Yellow

        $savedErrorActionPreference = $ErrorActionPreference
        $hadNativePreference = $null -ne (Get-Variable -Name PSNativeCommandUseErrorActionPreference -ErrorAction SilentlyContinue)
        if ($hadNativePreference) {
            $savedNativePreference = $PSNativeCommandUseErrorActionPreference
        }

        try {
            $ErrorActionPreference = "Continue"
            if ($hadNativePreference) {
                $PSNativeCommandUseErrorActionPreference = $false
            }

            $SchedulerResult = & ssh `
                -n -T `
                -o BatchMode=yes `
                -o ConnectTimeout=20 `
                -F $sshConfig `
                tu_freiberg `
                $RemoteCommand 2>&1

            $SchedulerExitCode = $LASTEXITCODE
        }
        finally {
            $ErrorActionPreference = $savedErrorActionPreference
            if ($hadNativePreference) {
                $PSNativeCommandUseErrorActionPreference = $savedNativePreference
            }
        }

        $cleanSched = @(
            $SchedulerResult |
            ForEach-Object { $_.ToString() } |
            Where-Object { $_ -notmatch "post-quantum key exchange algorithm" }
        )
        $qstatText = ($cleanSched | Out-String).Trim()

        # Fail-closed check: verify transport and query success before parsing scheduler state
        $isSchedulerUnreachable = (
            $SchedulerExitCode -ne 0 -or
            $qstatText -match '(?i)(?:ssh:\s*connect|connection timed out|connection refused|network is unreachable|could not resolve hostname|permission denied|host key verification failed|qstat:\s*(?:cannot connect|server|communication))'
        )

        if ($isSchedulerUnreachable) {
            Write-Host "`n==========================================================" -ForegroundColor Red
            Write-Host " SCHEDULER QUERY UNREACHABLE (SSH/NETWORK TRANSPORT ERROR) " -ForegroundColor Red
            Write-Host "==========================================================" -ForegroundColor Red
            Write-Host "[SCHEDULER] SSH/qstat transport failed (ExitCode=$SchedulerExitCode)." -ForegroundColor Yellow
            Write-Host "[SCHEDULER] Output: $qstatText" -ForegroundColor Yellow
            Write-Host "[SCHEDULER] State: SCHEDULER_STATE_UNKNOWN_UNREACHABLE. Preserving last verified job state without asserting zero Q/R." -ForegroundColor Yellow

            Write-LoopLog `
                -Turn $CurrentTurn `
                -Tier "CONTROLLER" `
                -Action "SCHEDULER_QUERY_UNREACHABLE" `
                -Message "Scheduler query unreachable (ExitCode=$SchedulerExitCode): $qstatText. Preserving job state."

            Save-LoopStatus `
                -Turn $CurrentTurn `
                -Status "SCHEDULER_STATE_UNKNOWN_UNREACHABLE" `
                -Tier "CONTROLLER" `
                -Action "HPC_REACHABILITY_BLOCKED" `
                -Details "Scheduler query unreachable (ExitCode=$SchedulerExitCode): $qstatText"

            break MainLoop
        }

        # Parse live Q/R jobs from user table (Only reached if query succeeded with ExitCode=0)
        $hasLiveRunningOrQueued = $false
        $liveRunningJobIds = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::OrdinalIgnoreCase)
        $liveLines = $qstatText -split "`r?`n"
        foreach ($lLine in $liveLines) {
            $lTrim = $lLine.Trim()
            if (-not $lTrim -or $lTrim.StartsWith("Job id") -or $lTrim.StartsWith("Job ID") -or $lTrim.StartsWith("---") -or $lTrim.StartsWith("mmaster02:")) {
                continue
            }
            $lParts = ($lTrim -split '\s+') | Where-Object { $_ -ne '' }
            if ($lParts.Count -ge 5) {
                $lState = if ($lParts.Count -ge 10 -and $lParts[9] -match '^[RQHWFCEBT]$') { $lParts[9].ToUpper() } elseif ($lParts[4] -match '^[RQHWFCEBT]$') { $lParts[4].ToUpper() } else { $null }
                if ($lState -in @('R', 'Q', 'H', 'W')) {
                    $hasLiveRunningOrQueued = $true
                    $rawId = ($lParts[0] -replace '\*$', '') -replace '\.mmaster02$', '' -replace '\.mmaste$', ''
                    if ($rawId -match '^1[3-9]\d{5,6}$') {
                        $fullSchedId = "$rawId.mmaster02"
                        [void]$candidateJobIds.Add($fullSchedId)
                        [void]$liveRunningJobIds.Add($fullSchedId)
                    }
                }
            }
        }

        # Track verified terminal jobs across turns
        if ($null -eq $script:VerifiedTerminalJobs) {
            $script:VerifiedTerminalJobs = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::OrdinalIgnoreCase)
        }

        # Load verified terminal jobs from HPC_JOB_LEDGER.csv
        $hpcLedgerPath = Join-PathStrict -Path $WorkspaceDir -ChildPath "project_coordination\HPC_JOB_LEDGER.csv"
        if (Test-Path -LiteralPath $hpcLedgerPath) {
            try {
                $ledgerLines = Get-Content -LiteralPath $hpcLedgerPath -ErrorAction SilentlyContinue
                foreach ($lLine in $ledgerLines) {
                    if ($lLine -match '^(1[3-9]\d{5,6}\.mmaster02),[^,]+,[^,]+,[^,]+,[^,]+,[^,]+,(F|C|E),') {
                        [void]$script:VerifiedTerminalJobs.Add($Matches[1])
                    }
                }
            } catch {}
        }

        # Also inspect ACTIVE_TASK.json for completed requalification jobs
        if (Test-Path -LiteralPath $activeTaskFile) {
            try {
                if ($taskData.priority_question_a.completed_requalification_job -and [string]$taskData.priority_question_a.completed_requalification_job -match '^1[3-9]\d{5,6}\.mmaster02$') {
                    [void]$script:VerifiedTerminalJobs.Add([string]$taskData.priority_question_a.completed_requalification_job)
                }
                if ($taskData.completed_requalification_job -and [string]$taskData.completed_requalification_job -match '^1[3-9]\d{5,6}\.mmaster02$') {
                    [void]$script:VerifiedTerminalJobs.Add([string]$taskData.completed_requalification_job)
                }
            } catch {}
        }

        # Also check if agent response verified any job as terminal (e.g. state F/C/E)
        if (-not [string]::IsNullOrWhiteSpace($agentResponse)) {
            $termMatches = [regex]::Matches($agentResponse, '(?im)^\s*(1[3-9]\d{5,6}\.mmaster02)\s+\S+\s+\S+\s+\S+\s+([FCE])\b')
            foreach ($tm in $termMatches) {
                [void]$script:VerifiedTerminalJobs.Add($tm.Groups[1].Value)
            }
            $termMatches2 = [regex]::Matches($agentResponse, '(?i)(?:job|id)\s*`?(1[3-9]\d{5,6}\.mmaster02)`?\s*.*?\b(?:terminal|finished|state:\s*F)\b')
            foreach ($tm2 in $termMatches2) {
                [void]$script:VerifiedTerminalJobs.Add($tm2.Groups[1].Value)
            }
        }

        # Separate candidate jobs: live running, unverified pending, and already verified terminal
        $pendingUnverifiedJobIds = [System.Collections.Generic.List[string]]::new()
        $activeTrackedForPrompt = [System.Collections.Generic.List[string]]::new()

        foreach ($cId in $candidateJobIds) {
            if ($liveRunningJobIds.Contains($cId)) {
                $activeTrackedForPrompt.Add("$cId (Running)")
            }
            elseif ($script:VerifiedTerminalJobs.Contains($cId)) {
                Write-Host "[SCHEDULER] Job $cId is ALREADY verified terminal. Filtering out from active polling." -ForegroundColor DarkGray
            }
            else {
                # Truly unverified job absent from qstat -u
                $pendingUnverifiedJobIds.Add($cId)
                $activeTrackedForPrompt.Add("$cId (Unverified Absent)")
            }
        }

        $activeJobParam = if ($activeTrackedForPrompt.Count -gt 0) {
            $activeTrackedForPrompt -join '; '
        } elseif ($liveRunningJobIds.Count -gt 0) {
            ($liveRunningJobIds | ForEach-Object { "$_ (Running)" }) -join '; '
        } else {
            "<none tracked>"
        }

        if ($candidateJobIds.Count -gt 0) {
            Write-Host "[SCHEDULER] Evaluating candidate PBS job(s): $($candidateJobIds -join ', ')" -ForegroundColor Cyan
        }

        if ($hasLiveRunningOrQueued) {
            Write-Host ""
            Write-Host "[SCHEDULER] Active PBS jobs remain in R/Q state." -ForegroundColor Yellow
            Write-Host "[SCHEDULER] Forwarding current scheduler table to ChatGPT for batch decision..." -ForegroundColor Cyan

            Write-LoopLog `
                -Turn $CurrentTurn `
                -Tier "tier3_chatgpt" `
                -Action "ESCALATE_SCHEDULER_REVIEW" `
                -Message "Sending fresh scheduler table to ChatGPT bridge..."

            try {
                $schedulerInstruction = Invoke-SchedulerReviewChatGPT `
                    -ActiveJobId $activeJobParam `
                    -QstatText $qstatText
            }
            catch {
                Write-LoopLog `
                    -Turn $CurrentTurn `
                    -Tier "tier3_chatgpt" `
                    -Action "CHATGPT_FAILURE_STOP" `
                    -Message "Error during scheduler review: $_"

                Save-LoopStatus `
                    -Turn $CurrentTurn `
                    -Status "FAILED" `
                    -Tier "tier3_chatgpt" `
                    -Action "CHATGPT_ERROR" `
                    -Details $_.Exception.Message

                break MainLoop
            }

            # Guard against redundant loop: if ChatGPT returned an instruction solely asking
            # to run qstat -x on already-terminal jobs while active jobs are running, suppress it!
            if ($schedulerInstruction -notmatch '^(?i:stop)\s*$') {
                $isRedundantLoop = $false
                if ($hasLiveRunningOrQueued -and $pendingUnverifiedJobIds.Count -eq 0) {
                    foreach ($tJob in $script:VerifiedTerminalJobs) {
                        if ($schedulerInstruction -match [regex]::Escape($tJob) -and ($schedulerInstruction -match '(?i)qstat\s+-x' -or $schedulerInstruction -match '(?i)absent from the current qstat')) {
                            $isRedundantLoop = $true
                            break
                        }
                    }
                }

                if ($isRedundantLoop) {
                    Write-Host "`n[SCHEDULER] LOOP DETECTED & SUPPRESSED: ChatGPT requested repeated qstat -x for already-verified terminal job(s) ($($script:VerifiedTerminalJobs -join ', '))." -ForegroundColor Yellow
                    Write-Host "[SCHEDULER] Live job ($($liveRunningJobIds -join ', ')) is running undisturbed. Converting instruction to STOP wait cycle." -ForegroundColor Cyan
                    Write-LoopLog `
                        -Turn $CurrentTurn `
                        -Tier "CONTROLLER" `
                        -Action "SUPPRESS_REDUNDANT_TERMINAL_QUERY_LOOP" `
                        -Message "Suppressed redundant qstat -x query on already-verified terminal job. Converting to STOP wait cycle."
                    $schedulerInstruction = "stop"
                }
            }

            if ($schedulerInstruction -notmatch '^(?i:stop)\s*$') {
                # ChatGPT determined an actionable independent instruction!
                $NextInstruction = $schedulerInstruction
                $gptPreview = if ($NextInstruction.Length -gt 80) { $NextInstruction.Substring(0, 80) } else { $NextInstruction }
                Write-LoopLog `
                    -Turn $CurrentTurn `
                    -Tier "tier3_chatgpt" `
                    -Action "CHATGPT_SCHEDULER_DISPATCH" `
                    -Message "Actionable instruction received while jobs run: ${gptPreview}..."
            }
            else {
                # Genuine wait: all independent work dispatched; wait 15m polling cycle
                Write-Host ""
                Write-Host "[SCHEDULER] All active work is running. Entering 900-second wait cycle..." -ForegroundColor Cyan

                Write-LoopLog `
                    -Turn $CurrentTurn `
                    -Tier "CONTROLLER" `
                    -Action "WAITING_FOR_SCHEDULER" `
                    -Message "Waiting 900 seconds for active Q/R PBS jobs..."

                Start-Sleep -Seconds 900

                # Prepare next turn instruction for fresh scheduler check after sleep
                $liveJobSummary = if ($liveRunningJobIds.Count -gt 0) { ($liveRunningJobIds -join ', ') } else { "active jobs" }
                $termJobSummary = if ($script:VerifiedTerminalJobs.Count -gt 0) { ($script:VerifiedTerminalJobs -join ', ') } else { "verified terminal jobs" }
                $NextInstruction = "Run a single fresh scheduler check now: qstat -u pr21vyci. Evaluate active running job(s) ($liveJobSummary). Do not query verified terminal jobs ($termJobSummary). If active job(s) remain R, report current elapsed walltime and confirm solver output remains untouched. If terminal, retrieve terminal logs/accounting and proceed with terminal extraction. Write Finished when done."
            }
        }
        else {
            # No running jobs on scheduler.
            $fundamentalsExplicitlyComplete = (
                -not [string]::IsNullOrWhiteSpace($agentResponse) -and
                ($agentResponse -match '(?im)^\s*MODE1_FUNDAMENTALS_COMPLETE\s*$' -or $agentResponse -match '(?im)^\s*MODE1_RESOLUTION_EXTENSION_COMPLETE\s*$')
            )
            # Synchronize latest governance state
            Sync-ControllerGovernanceState

            $modeIFundamentalsActionable = Get-ModeIFundamentalsActionable

            if ($modeIFundamentalsActionable -and -not $fundamentalsExplicitlyComplete -and -not $script:ModeIFundamentalsComplete) {
                Write-Host "`n==========================================================" -ForegroundColor Green
                Write-Host " ZERO ACTIVE Q/R PBS JOBS -- MODE-I FUNDAMENTALS ACTIVE " -ForegroundColor Green
                Write-Host "==========================================================" -ForegroundColor Green
                Write-Host "[GOVERNANCE] Priority 1: UEL Energy Formulation and Output Audit (Actionable: $($script:EnergyFormulationAuditActionable))" -ForegroundColor Cyan
                Write-Host "[GOVERNANCE] Priority 2: Multifaceted Mode-I Convergence (Actionable: $($script:SpatialTemporalConvergenceActionable))" -ForegroundColor Cyan
                Write-Host "[GOVERNANCE] Priority 3: Mode-I State-Transfer Conservation ($($script:ModeIStateTransferStatus))" -ForegroundColor Cyan
                Write-Host "[GOVERNANCE] Independent fundamentals work actionable offline. Continuing controller loop." -ForegroundColor Cyan

                Write-LoopLog `
                    -Turn $CurrentTurn `
                    -Tier "CONTROLLER" `
                    -Action "MODE1_FUNDAMENTALS_ACTIVE" `
                    -Message "Zero live Q/R PBS jobs. Mode-I fundamentals work actionable offline. Continuing controller turn."

                Save-LoopStatus `
                    -Turn $CurrentTurn `
                    -Status "MODE1_FUNDAMENTALS_ACTIVE" `
                    -Tier "CONTROLLER" `
                    -Action "ENERGY_FORMULATION_AUDIT_ACTIONABLE" `
                    -Details "Zero live Q/R jobs. Mode-I fundamentals active. Priority 1: UEL Energy Formulation and Output Audit."

                # Forward to next turn to continue offline fundamentals task
                $NextInstruction = "Continue Mode-I fundamentals qualification: UEL energy formulation and output audit. Inspect authoritative Fortran UEL weak form in f42_mixed_uel.for, derive exact energy terms and global energy balance identity, design non-invasive output exposing UEL energy, verify on smallest meaningful case, prove mechanical parity, and update thesis/report before 08-Oct-2026. Write Finished when the unit of work is complete."
            }
            else {
                Write-Host "`n==========================================================" -ForegroundColor Green
                Write-Host " ZERO ACTIVE Q/R PBS JOBS REMAIN ON SCHEDULER " -ForegroundColor Green
                Write-Host "==========================================================" -ForegroundColor Green

                Write-LoopLog `
                    -Turn $CurrentTurn `
                    -Tier "CONTROLLER" `
                    -Action "LOOP_TERMINATED_SAFE" `
                    -Message "Zero live Q/R PBS jobs remain and Mode-I fundamentals work is complete or not actionable."

                Save-LoopStatus `
                    -Turn $CurrentTurn `
                    -Status "STOPPED_CLEAN" `
                    -Tier "CONTROLLER" `
                    -Action "NORMAL_TERMINATION" `
                    -Details "All independent Mode-I fundamentals work completed cleanly."

                try {
                    if (Test-Path -LiteralPath $StateFile) {
                        $st = Get-Content -LiteralPath $StateFile -Raw | ConvertFrom-Json
                        $st.loop_status = "STOPPED_CLEAN"
                        $st.next_instruction = "stop"
                        $stJson = $st | ConvertTo-Json -Depth 10
                        [System.IO.File]::WriteAllText($StateFile, $stJson, [System.Text.UTF8Encoding]::new($false))
                    }
                } catch { }

                break MainLoop
            }
        }
    }
    # ------------------------------------------------------------------------
    # Qualify a proposed successor before any account rotation or next model turn.
    $preparation=Invoke-ControllerOperationPreparation $WorkspaceDir $NextInstruction
    if(-not $preparation.dispatch_ready){
        $script:ControllerState|Add-Member -NotePropertyName operation_preparation -NotePropertyValue $preparation -Force
        $script:ControllerState|Add-Member -NotePropertyName next_instruction -NotePropertyValue $NextInstruction -Force
        Write-ControllerCheckpoint $controllerCheckpointPath $script:ControllerState
        Write-LoopLog -Turn $CurrentTurn -Tier 'CONTROLLER' -Action 'NEXT_OPERATION_PREPARATION' -Message ($preparation|ConvertTo-Json -Depth 8 -Compress)
        break MainLoop
    }
    # AGY_QUOTA_GUARD_V1: if low quota was detected, the completed AGY turn has
    # now been routed and NextInstruction is known. Persist the handoff and stop
    # BEFORE dispatching another AGY turn.
    # ------------------------------------------------------------------------
    if ($quotaStopPending) {

        # --------------------------------------------------------
        # VALID low-quota snapshot: rotate automatically.
        # Unknown quota failures still fall through to the original
        # fail-closed/manual-preservation block below.
        # --------------------------------------------------------

        if (
            $AutoRotateAgyProfileOnLowQuota -and
            (
                ($null -ne $quotaSnapshot -and [bool]$quotaSnapshot.below_threshold) -or
                ($EnableSmartAgyProfileSelection -and $quotaCheckFailed)
            ) -and
            -not [string]::IsNullOrWhiteSpace($NextInstruction) -and
            $NextInstruction -notmatch '^(?i:stop)\s*$'
        ) {
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

            try {

                $oldConversation = $ConversationId

                $rotation = Switch-ToNextAgyProfile


                Write-LoopLog `
                    -Turn $CurrentTurn `
                    -Tier "CONTROLLER" `
                    -Action "QUOTA_LOW_AUTO_PROFILE_ROTATION" `
                    -Message (
                        "Valid 5h quota below threshold. " +
                        "Rotated '$($rotation.previous_profile)' -> " +
                        "'$($rotation.new_profile)'. " +
                        "Old conversation '$oldConversation' will not be reused."
                    )


                Save-LoopState `
                    -Turn $CurrentTurn `
                    -Status "PENDING_NEXT_TURN" `
                    -LastInstruction $CurrentInstruction `
                    -LastResponse $agentResponse `
                    -NextInstruction $NextInstruction `
                    -Duration $turnDurationSeconds `
                    -Usage $combinedUsage `
                    -Tier $tierName `
                    -Action "QUOTA_LOW_AUTO_PROFILE_ROTATION"


                Save-LoopStatus `
                    -Turn $CurrentTurn `
                    -Status "AUTO_PROFILE_ROTATED" `
                    -Tier "CONTROLLER" `
                    -Action "QUOTA_LOW_AUTO_PROFILE_ROTATION" `
                    -Details (
                        "Profile '$($rotation.previous_profile)' -> " +
                        "'$($rotation.new_profile)'; fresh AGY conversation required."
                    )


                $CurrentInstruction = $NextInstruction
                $CurrentTurn++


                Write-Host ""
                Write-Host "==========================================================" -ForegroundColor Green
                Write-Host " AGY PROFILE AUTO-ROTATED - LOOP CONTINUING" -ForegroundColor Green
                Write-Host "==========================================================" -ForegroundColor Green
                Write-Host " New profile: $($rotation.new_profile)"
                Write-Host " Old conversation discarded: $oldConversation"
                Write-Host " Next AGY call will create a fresh conversation."
                Write-Host ""


                continue MainLoop
            }
            catch {

                Write-LoopLog `
                    -Turn $CurrentTurn `
                    -Tier "CONTROLLER" `
                    -Action "QUOTA_LOW_AUTO_ROTATION_FAILED" `
                    -Message $_.Exception.Message

                # Deliberately fall through to the existing fail-closed
                # handoff block rather than silently consuming quota.
            }
        }


        if (
            -not [string]::IsNullOrWhiteSpace($NextInstruction) -and
            $NextInstruction -notmatch '^(?i:stop)\s*$'
        ) {
            try {
                $handoffPromptPath = Write-QuotaRotationInitialPrompt `
                    -Turn $CurrentTurn `
                    -LastResponse $agentResponse `
                    -NextInstruction $NextInstruction `
                    -QuotaText $quotaSnapshotText
            }
            catch {
                Write-LoopLog `
                    -Turn $CurrentTurn `
                    -Tier "CONTROLLER" `
                    -Action "QUOTA_HANDOFF_WRITE_FAILED" `
                    -Message "$_"

                Save-LoopStatus `
                    -Turn $CurrentTurn `
                    -Status "FAILED" `
                    -Tier "CONTROLLER" `
                    -Action "QUOTA_HANDOFF_WRITE_FAILED" `
                    -Details $_.Exception.Message

                break MainLoop
            }

            Save-LoopState -Turn $CurrentTurn `
                           -Status "QUOTA_HANDOFF_REQUIRED" `
                           -LastInstruction $CurrentInstruction `
                           -LastResponse $agentResponse `
                           -NextInstruction $NextInstruction `
                           -Duration $turnDurationSeconds `
                           -Usage $combinedUsage `
                           -Tier $tierName `
                           -Action "QUOTA_GUARD_STOP"

            Save-LoopStatus `
                -Turn $CurrentTurn `
                -Status "QUOTA_HANDOFF_REQUIRED" `
                -Tier "CONTROLLER" `
                -Action "QUOTA_GUARD_STOP" `
                -Details $quotaSnapshotText

            Write-LoopLog `
                -Turn $CurrentTurn `
                -Tier "CONTROLLER" `
                -Action "QUOTA_GUARD_STOP" `
                -Message "Stopping before another AGY turn. New-account handoff written to $handoffPromptPath"

            Write-Host ""
            Write-Host "==========================================================" -ForegroundColor Yellow
            Write-Host " AGY FIVE-HOUR QUOTA GUARD STOPPED THE LOOP " -ForegroundColor Yellow
            Write-Host "==========================================================" -ForegroundColor Yellow
            Write-Host $quotaSnapshotText -ForegroundColor Yellow
            Write-Host ""
            Write-Host "The completed turn result and next instruction were preserved." -ForegroundColor Green
            Write-Host "Updated initial prompt:" -ForegroundColor Green
            Write-Host "  $handoffPromptPath" -ForegroundColor Green
            Write-Host ""
            Write-Host "MANUAL ACCOUNT ROTATION:" -ForegroundColor Cyan
            Write-Host "  agy-profile switch <next-account>" -ForegroundColor White
            Write-Host "  agy-profile current" -ForegroundColor White
            Write-Host ""
            Write-Host "Then start a NEW Antigravity conversation with:" -ForegroundColor Cyan
            Write-Host '  $promptFile = "D:\Master thesis\Adaptive remeshing\.agents\INITIAL_PROMPT.txt"' -ForegroundColor White
            Write-Host '  $prompt = Get-Content -LiteralPath $promptFile -Raw' -ForegroundColor White
            Write-Host '  $run = @{' -ForegroundColor White
            Write-Host '      InitialPrompt = $prompt' -ForegroundColor White
            Write-Host '      MaxTurns = 50' -ForegroundColor White
            Write-Host '      PrintTimeout = "10000s"' -ForegroundColor White
            Write-Host '      QuotaCheckEveryTurns = 1' -ForegroundColor White
            Write-Host '      QuotaStopThresholdPct = 15' -ForegroundColor White
            Write-Host '  }' -ForegroundColor White
            Write-Host '  & "$env:USERPROFILE\OpenClawPAD\Antigravity-Autonomous-Loop.ps1" @run' -ForegroundColor White
            Write-Host ""
            Write-Host "Do NOT pass the old ConversationId after switching accounts." -ForegroundColor Yellow

            break MainLoop
        }
    }

    # Save pending next turn state
    Save-LoopState -Turn $CurrentTurn `
                   -Status "PENDING_NEXT_TURN" `
                   -LastInstruction $CurrentInstruction `
                   -LastResponse $agentResponse `
                   -NextInstruction $NextInstruction `
                   -Duration $turnDurationSeconds `
                   -Usage $combinedUsage `
                   -Tier $tierName `
                   -Action $routerResult.action

    Ensure-AuthoritativeAgyProfile "TURN_END"
    # Durably preserve the router's next instruction; a new prompt cannot override it.
    $script:ControllerState.state='PENDING'
    $script:ControllerState | Add-Member -NotePropertyName next_instruction -NotePropertyValue $NextInstruction -Force
    $script:ControllerState.next_safe_action=$NextInstruction
    Write-ControllerCheckpoint $controllerCheckpointPath $script:ControllerState

    # Prepare for next turn
    $CurrentInstruction = $NextInstruction
    $CurrentTurn++
}

if ($CurrentTurn -gt ($StartTurn + $MaxTurns - 1)) {
    Write-LoopLog -Turn $CurrentTurn -Tier "CONTROLLER" -Action "MAX_TURNS_EXCEEDED" -Message "Halted after reaching max turn limit ($MaxTurns)."
    Save-LoopStatus -Turn $CurrentTurn -Status "MAX_TURNS_EXCEEDED" -Tier "CONTROLLER" -Action "MAX_TURNS_HALT" -Details "Hit $MaxTurns turns."
}






 } finally {
    if ($null -ne $script:ControllerState -and $script:ControllerState.state -in @('RUNNING','CHECKPOINTED')) {
        # Release only proven owned sessions on abnormal closeout, never a live/foreign process.
        if(-not $script:ControllerState.process_id -or -not(Get-Process -Id $script:ControllerState.process_id -ErrorAction SilentlyContinue)){
            $raw=if($script:ControllerState.captured_raw_output){$script:ControllerState.captured_raw_output}elseif($script:ControllerState.live_output_log -and (Test-Path -LiteralPath $script:ControllerState.live_output_log)){Get-Content -LiteralPath $script:ControllerState.live_output_log -Raw}else{'Controller exited abnormally; inspect live output log and checkpoint.'}
            $script:ControllerState=Set-ControllerInterrupted $WorkspaceDir $controllerCheckpointPath $script:ControllerState $raw
        }
        $script:ControllerState.state='BLOCKED'
        $script:ControllerState.block_reason='Controller exited before a verified completed response; inspect loop status, credential/quota and preserved evidence'
        Write-ControllerCheckpoint $controllerCheckpointPath $script:ControllerState
    }
    if ($controllerLockHeld) { $controllerMutex.ReleaseMutex() }
    $controllerMutex.Dispose()
}
