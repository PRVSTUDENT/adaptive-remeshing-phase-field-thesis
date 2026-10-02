# Patch script for Antigravity-Autonomous-Loop.ps1
# Implements:
# 1. Loop-prevention rules in Invoke-SchedulerReviewChatGPT prompt
# 2. Terminal-job filtering from candidate list before scheduler review
# 3. Redundant qstat -x suppression guard to convert redundant terminal queries to STOP wait cycle

$ErrorActionPreference = "Stop"

$targetPath = "C:\Users\pruth\OpenClawPAD\Antigravity-Autonomous-Loop.ps1"
if (-not (Test-Path -LiteralPath $targetPath)) {
    throw "Target file not found: $targetPath"
}

$content = [System.IO.File]::ReadAllText($targetPath, [System.Text.Encoding]::UTF8)

# -----------------------------------------------------------------------------
# Part 1: Update Prompt Rules in Invoke-SchedulerReviewChatGPT
# -----------------------------------------------------------------------------
$oldPromptRules = @'
Rules:
1. Concurrency & Independent Work Check:
   If running jobs (R or Q) exist, but there is free HPC headroom (under 640 CPUs) AND independent Mode-I work is ready (such as launching independent same-thread determinism repeats, evaluating terminal jobs, postprocessing, or advancing Gate 6 evidence):
   Do NOT reply 'stop'. Instruct Antigravity to proceed with that independent work while leaving running jobs untouched!

2. When to reply 'stop':
   Reply exactly 'stop' ONLY if the workflow is strictly blocked waiting for running jobs to finish, and no independent Mode-I tasks can be performed.
   If the scheduler is empty while MODE1_RESOLUTION_EXTENSION_ACTIVE remains unresolved, do NOT return stop; issue the next smallest evidence-producing diagnostic/validation action.

3. If the tracked job ($jobInfoText) is H, W, or another nonstandard state:
   do not automatically return stop. Determine whether intervention or diagnostic accounting is required.

4. If the tracked job ($jobInfoText) is absent from qstat -u pr21vyci:
   instruct Antigravity to run:
   qstat -x $jobInfoText
   and retrieve/evaluate terminal scheduler/solver evidence.

5. If terminal state/evidence (F/C/E) is supplied:
   do not return stop merely because the scheduler job finished.
   Issue the next concrete scientific evidence-retrieval/evaluation action.
'@

$newPromptRules = @'
Rules:
1. Concurrency & Independent Work Check:
   If running jobs (R or Q) exist, but there is free HPC headroom (under 640 CPUs) AND independent Mode-I work is ready (such as launching independent same-thread determinism repeats, evaluating terminal jobs, postprocessing, or advancing Gate 6 evidence):
   Do NOT reply 'stop'. Instruct Antigravity to proceed with that independent work while leaving running jobs untouched!

2. When to reply 'stop':
   Reply exactly 'stop' if all active tracked jobs (such as 1404454.mmaster02) are currently running ('R') undisturbed, and no genuinely new independent Mode-I tasks remain ready to execute right now.
   The loop controller will then enter a wait cycle until the job state actually changes.
   CRITICAL LOOP PREVENTION: While running jobs remain 'R', do NOT loop on repetitive accounting, telemetry queries, or active-ODB reads. Only react when the running job's state actually changes!
   If the scheduler is completely empty while MODE1_RESOLUTION_EXTENSION_ACTIVE remains unresolved, do NOT return stop; issue the next smallest evidence-producing diagnostic/validation action.

3. If the tracked job ($jobInfoText) is H, W, or another nonstandard state:
   do not automatically return stop. Determine whether intervention or diagnostic accounting is required.

4. Terminal Job Lookup & Loop Prevention Rule:
   A previously verified terminal job (e.g., state F/C/E already established, evaluated, or recorded in the ledger/status, such as 1404306.mmaster02) does NOT trigger repeated 'qstat -x' merely because it is absent from 'qstat -u'. Treat already-verified jobs as terminal-and-frozen evidence. Do NOT loop on accounting!
   Only a tracked job whose terminal state is not already established needs that lookup (i.e. a job that was recently running and has newly disappeared from 'qstat -u' without its terminal transition yet having been recorded).

5. If a job's terminal transition is newly detected:
   Issue the next concrete scientific evidence-retrieval/evaluation action rather than stopping. Once evaluated, treat that job as terminal-and-frozen evidence; do not poll it again.
'@

# Normalize line endings for replacement
$oldPromptNorm = ($oldPromptRules -replace "`r`n", "`n").Trim()
$newPromptNorm = ($newPromptRules -replace "`r`n", "`n").Trim()
$contentNorm = $content -replace "`r`n", "`n"

if (-not $contentNorm.Contains($oldPromptNorm)) {
    throw "Target oldPromptRules not found in $targetPath"
}

$contentNorm = $contentNorm.Replace($oldPromptNorm, $newPromptNorm)
Write-Host "[PATCH 1] Prompt rules in Invoke-SchedulerReviewChatGPT updated successfully." -ForegroundColor Green

# -----------------------------------------------------------------------------
# Part 2: Update Candidate Evaluation and Redundant Loop Guard
# -----------------------------------------------------------------------------
$oldEvalBlock = @'
        # Check if candidate jobs from turn 1 are already terminal (F/C/E)
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
                    -ActiveJobId ($candidateJobIds -join '; ') `
                    -QstatText $qstatText
            }
'@

$newEvalBlock = @'
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
'@

$oldEvalNorm = ($oldEvalBlock -replace "`r`n", "`n").Trim()
$newEvalNorm = ($newEvalBlock -replace "`r`n", "`n").Trim()

if (-not $contentNorm.Contains($oldEvalNorm)) {
    throw "Target oldEvalBlock not found in $targetPath"
}

$contentNorm = $contentNorm.Replace($oldEvalNorm, $newEvalNorm)
Write-Host "[PATCH 2] Candidate job filtering and activeJobParam logic updated successfully." -ForegroundColor Green

# -----------------------------------------------------------------------------
# Part 3: Add Redundant Terminal Query Loop Suppression Guard
# -----------------------------------------------------------------------------
$oldCatchBlock = @'
                Save-LoopStatus `
                    -Turn $CurrentTurn `
                    -Status "FAILED" `
                    -Tier "tier3_chatgpt" `
                    -Action "CHATGPT_ERROR" `
                    -Details $_.Exception.Message

                break MainLoop
            }

            if ($schedulerInstruction -notmatch '^(?i:stop)\s*$') {
                # ChatGPT determined an actionable independent instruction!
'@

$newCatchBlock = @'
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
'@

$oldCatchNorm = ($oldCatchBlock -replace "`r`n", "`n").Trim()
$newCatchNorm = ($newCatchBlock -replace "`r`n", "`n").Trim()

if (-not $contentNorm.Contains($oldCatchNorm)) {
    throw "Target oldCatchBlock not found in $targetPath"
}

$contentNorm = $contentNorm.Replace($oldCatchNorm, $newCatchNorm)
Write-Host "[PATCH 3] Redundant terminal query loop suppression guard added successfully." -ForegroundColor Green

# -----------------------------------------------------------------------------
# Verify syntax before writing
# -----------------------------------------------------------------------------
# Write to a temp file and parse with AST
$tempFile = [System.IO.Path]::GetTempFileName()
[System.IO.File]::WriteAllText($tempFile, ($contentNorm -replace "`n", "`r`n"), [System.Text.Encoding]::UTF8)

$tokens = $null
$errors = $null
[System.Management.Automation.Language.Parser]::ParseFile($tempFile, [ref]$tokens, [ref]$errors) | Out-Null

if ($errors.Count -gt 0) {
    Remove-Item -LiteralPath $tempFile -Force -ErrorAction SilentlyContinue
    throw "Syntax errors detected in patched content: $($errors | Out-String)"
}

Write-Host "[VERIFICATION] PowerShell AST parser validated patched content (0 errors)." -ForegroundColor Green

# Atomically overwrite target file
[System.IO.File]::WriteAllText($targetPath, ($contentNorm -replace "`n", "`r`n"), [System.Text.Encoding]::UTF8)
Remove-Item -LiteralPath $tempFile -Force -ErrorAction SilentlyContinue

Write-Host "[SUCCESS] $targetPath successfully updated and validated." -ForegroundColor Cyan
