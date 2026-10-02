$ErrorActionPreference = "Stop"

$controllerPath = "C:\Users\pruth\OpenClawPAD\Antigravity-Autonomous-Loop.ps1"
$backupPath = "C:\Users\pruth\OpenClawPAD\Antigravity-Autonomous-Loop.ps1.bak_20260911_null_fix"

if (-not (Test-Path -LiteralPath $controllerPath)) {
    throw "Controller path does not exist: $controllerPath"
}

Copy-Item -LiteralPath $controllerPath -Destination $backupPath -Force
Write-Host "Created backup at $backupPath"

$content = [System.IO.File]::ReadAllText($controllerPath, [System.Text.Encoding]::UTF8)

# 1. Add $liveRunningJobIds initialization right after $candidateJobIds
$target1 = '        $candidateJobIds = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::OrdinalIgnoreCase)'
$replacement1 = "        `$candidateJobIds = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::OrdinalIgnoreCase)`r`n        `$liveRunningJobIds = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::OrdinalIgnoreCase)"

if (-not $content.Contains($target1)) {
    throw "Target 1 not found in controller script"
}

$content = $content.Replace($target1, $replacement1)
Write-Host "Applied change 1: Initialized `$liveRunningJobIds at start of stop block"

# 2. Add $liveRunningJobIds initialization and population in the live Q/R parsing loop
$target2 = '                    if ($rawId -match ''^1[3-9]\d{5,6}$'') {
                        $fullSchedId = "$rawId.mmaster02"
                        [void]$candidateJobIds.Add($fullSchedId)
                    }'

# Let's verify target2 exact form by checking the inner block
$innerSearch = '[void]$candidateJobIds.Add($fullSchedId)'
$pos = $content.IndexOf($innerSearch)
if ($pos -lt 0) {
    throw "Inner search not found for change 2"
}

# In this loop:
# [void]$candidateJobIds.Add($fullSchedId)
# We want to add:
# [void]$liveRunningJobIds.Add($fullSchedId)
$target2_exact = "                        [void]`$candidateJobIds.Add(`$fullSchedId)"
$replacement2_exact = "                        [void]`$candidateJobIds.Add(`$fullSchedId)`r`n                        [void]`$liveRunningJobIds.Add(`$fullSchedId)"

if (-not $content.Contains($target2_exact)) {
    throw "Target 2 exact not found in controller script"
}

# Also ensure $liveRunningJobIds is initialized right after $hasLiveRunningOrQueued = $false
$target2_init = '        $hasLiveRunningOrQueued = $false'
$replacement2_init = "        `$hasLiveRunningOrQueued = `$false`r`n        `$liveRunningJobIds = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::OrdinalIgnoreCase)"

if (-not $content.Contains($target2_init)) {
    throw "Target 2 init not found in controller script"
}

$content = $content.Replace($target2_init, $replacement2_init)
$content = $content.Replace($target2_exact, $replacement2_exact)
Write-Host "Applied change 2: Initialized and populated `$liveRunningJobIds from live qstat lines"

# 3. In the 900-second wait cycle, prepare the next turn instruction for fresh scheduler check
$target3 = '                Start-Sleep -Seconds 900'
$replacement3 = "                Start-Sleep -Seconds 900`r`n`r`n                # Prepare next turn instruction for fresh scheduler check after sleep`r`n                `$liveJobSummary = if (`$liveRunningJobIds.Count -gt 0) { (`$liveRunningJobIds -join ', ') } else { `"active jobs`" }`r`n                `$termJobSummary = if (`$script:VerifiedTerminalJobs.Count -gt 0) { (`$script:VerifiedTerminalJobs -join ', ') } else { `"verified terminal jobs`" }`r`n                `$NextInstruction = `"Run a single fresh scheduler check now: qstat -u pr21vyci. Evaluate active running job(s) (`$liveJobSummary). Do not query verified terminal jobs (`$termJobSummary). If active job(s) remain R, report current elapsed walltime and confirm solver output remains untouched. If terminal, retrieve terminal logs/accounting and proceed with terminal extraction. Write Finished when done.`""

if (-not $content.Contains($target3)) {
    throw "Target 3 not found in controller script"
}

$content = $content.Replace($target3, $replacement3)
Write-Host "Applied change 3: Set NextInstruction for fresh scheduler check following 900s sleep wait cycle"

[System.IO.File]::WriteAllText($controllerPath, $content, [System.Text.Encoding]::UTF8)
Write-Host "Successfully patched $controllerPath"
