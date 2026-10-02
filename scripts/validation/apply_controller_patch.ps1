# Apply refined Invoke-SchedulerReviewChatGPT and user-level qstat architecture
$targetFile = "C:\Users\pruth\OpenClawPAD\Antigravity-Autonomous-Loop.ps1"
$lines = [System.IO.File]::ReadAllLines($targetFile, [System.Text.UTF8Encoding]::new($false))

$fnStartIdx = -1
$fnEndIdx = -1

for ($i = 0; $i -lt $lines.Length; $i++) {
    if ($lines[$i] -like "function Invoke-SchedulerReviewChatGPT*") {
        $fnStartIdx = $i
    }
    if ($fnStartIdx -ge 0 -and $lines[$i] -like "# MAIN AUTONOMOUS LOOP CONTROLLER*") {
        $fnEndIdx = $i - 2
        break
    }
}

if ($fnStartIdx -ge 0 -and $fnEndIdx -gt $fnStartIdx) {
    Write-Host "Found Invoke-SchedulerReviewChatGPT at lines $($fnStartIdx + 1) to $($fnEndIdx + 1)"

    $newFn = @'
function Invoke-SchedulerReviewChatGPT($ActiveJobId, $QstatText) {
    $jobInfoText = if ([string]::IsNullOrWhiteSpace($ActiveJobId)) { "<none tracked>" } else { $ActiveJobId }

    $Prompt = @"
SCHEDULER REVIEW

HUMAN (USER) AUTHORIZATION STATUS:
The human user has EXPLICITLY authorized today's tasks, solver evidence evaluations, and follow-up workflow executions for this project.

Tracked active production PBS job:
$jobInfoText

Fresh result of qstat -u pr21vyci:

---------------- SCHEDULER RESULT ----------------
$QstatText
-------------- END SCHEDULER RESULT --------------

Determine the next instruction to send to Antigravity.

Workflow requirements:
1. Give only the next actionable instruction. Do not add unnecessary commentary.
2. If the tracked active production job ($jobInfoText) is present in the scheduler table and in state R, Q, H, or W, and no immediate intervention is required, reply exactly:
stop
3. If the tracked job is no longer present in qstat -u pr21vyci (or has transitioned to a terminal state F/C/E), instruct Antigravity to query exact terminal accounting (e.g. qstat -x $jobInfoText) and retrieve/evaluate the authoritative solver evidence (.sta, .msg, .dat, .odb, pbs_execution.log).
4. If an abnormal scheduler failure or cancellation is detected, provide the precise diagnostic instruction.
5. Preserve exact PBS job IDs. Do not construct or infer job IDs from arbitrary numerical metrics.
6. When asking Antigravity to perform work, require it to write "Finished" at the end.
7. Return only the next instruction that should be sent to Antigravity.
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
'@

    $prefix = $lines[0..($fnStartIdx - 1)] -join "`r`n"
    $suffix = $lines[($fnEndIdx + 1)..($lines.Length - 1)] -join "`r`n"
    $newContent = "$prefix`r`n$newFn`r`n$suffix"

    [System.IO.File]::WriteAllText($targetFile, $newContent, [System.Text.UTF8Encoding]::new($false))
    Write-Host "Updated Invoke-SchedulerReviewChatGPT successfully."
} else {
    Write-Error "Could not locate Invoke-SchedulerReviewChatGPT bounds: fnStartIdx=$fnStartIdx, fnEndIdx=$fnEndIdx"
}
