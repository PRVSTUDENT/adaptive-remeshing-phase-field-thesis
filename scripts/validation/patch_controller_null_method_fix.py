import sys
import shutil
from pathlib import Path

controller_path = Path(r"C:\Users\pruth\OpenClawPAD\Antigravity-Autonomous-Loop.ps1")
backup_path = Path(r"C:\Users\pruth\OpenClawPAD\Antigravity-Autonomous-Loop.ps1.bak_20260911_null_fix")

if not controller_path.exists():
    print(f"ERROR: Controller path does not exist: {controller_path}")
    sys.exit(1)

shutil.copy2(controller_path, backup_path)
print(f"Created backup at {backup_path}")

content = controller_path.read_text(encoding="utf-8")

# 1. Add $liveRunningJobIds initialization right after $candidateJobIds
target1 = """        # Collect candidate PBS job IDs strictly matching verified scheduler ID format
        $candidateJobIds = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::OrdinalIgnoreCase)"""

replacement1 = """        # Collect candidate PBS job IDs strictly matching verified scheduler ID format
        $candidateJobIds = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::OrdinalIgnoreCase)
        $liveRunningJobIds = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::OrdinalIgnoreCase)"""

if target1 not in content:
    print("ERROR: Target 1 not found in controller script")
    sys.exit(1)

content = content.replace(target1, replacement1, 1)
print("Applied change 1: Initialized $liveRunningJobIds at start of stop block")

# 2. Add $liveRunningJobIds initialization and population in the live Q/R parsing loop
target2 = """        # Parse live Q/R jobs from user table (Only reached if query succeeded with ExitCode=0)
        $hasLiveRunningOrQueued = $false
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
                    }
                }
            }
        }"""

replacement2 = """        # Parse live Q/R jobs from user table (Only reached if query succeeded with ExitCode=0)
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
        }"""

if target2 not in content:
    print("ERROR: Target 2 not found in controller script")
    sys.exit(1)

content = content.replace(target2, replacement2, 1)
print("Applied change 2: Populated $liveRunningJobIds from live qstat lines")

# 3. In the 900-second wait cycle, prepare the next turn instruction for fresh scheduler check
target3 = """                Start-Sleep -Seconds 900
            }
        }
        else {"""

replacement3 = """                Start-Sleep -Seconds 900

                # Prepare next turn instruction for fresh scheduler check after sleep
                $liveJobSummary = if ($liveRunningJobIds.Count -gt 0) { ($liveRunningJobIds -join ', ') } else { "active jobs" }
                $termJobSummary = if ($script:VerifiedTerminalJobs.Count -gt 0) { ($script:VerifiedTerminalJobs -join ', ') } else { "verified terminal jobs" }
                $NextInstruction = "Run a single fresh scheduler check now: qstat -u pr21vyci. Evaluate active running job(s) ($liveJobSummary). Do not query verified terminal jobs ($termJobSummary). If active job(s) remain R, report current elapsed walltime and confirm solver output remains untouched. If terminal, retrieve terminal logs/accounting and proceed with terminal extraction. Write Finished when done."
            }
        }
        else {"""

if target3 not in content:
    print("ERROR: Target 3 not found in controller script")
    sys.exit(1)

content = content.replace(target3, replacement3, 1)
print("Applied change 3: Set NextInstruction for fresh scheduler check following 900s sleep wait cycle")

controller_path.write_text(content, encoding="utf-8")
print("Successfully patched Antigravity-Autonomous-Loop.ps1")
