import os

target_path = r"C:\Users\pruth\OpenClawPAD\Antigravity-Autonomous-Loop.ps1"

with open(target_path, "r", encoding="utf-8", newline="") as f:
    content = f.read()

has_crlf = "\r\n" in content
content = content.replace("\r\n", "\n")

# 1. Update Get-LivePbsJobs to run qstat -u $User
old_remote_cmd = '$remoteCommand = "qstat -x -u $User"'
new_remote_cmd = '$remoteCommand = "qstat -u $User"'
assert old_remote_cmd in content, "old_remote_cmd not found"
content = content.replace(old_remote_cmd, new_remote_cmd, 1)

# 2. Update Section 5 Candidate Selection Block
old_candidate_block = '''        # --------------------------------------------------------
        # Collect candidate PBS job IDs from:
        # 1. Latest agent response (e.g. submitted job ID)
        # 2. ACTIVE_TASK.json
        # 3. controller-state.json (tracked active jobs)
        # 4. Live scheduler (qstat -x -u)
        # --------------------------------------------------------
        $candidateJobIds = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::OrdinalIgnoreCase)

        # 1. From agent response
        if (-not [string]::IsNullOrWhiteSpace($agentResponse)) {
            $mMatches = [regex]::Matches($agentResponse, '\\b(\\d{6,8}(\\.mmaster02)?)\\b')
            foreach ($m in $mMatches) {
                $val = $m.Value
                if ($val -notmatch '\\.mmaster02$') { $val = "$val.mmaster02" }
                [void]$candidateJobIds.Add($val)
            }
        }

        # 2. From ACTIVE_TASK.json
        $activeTaskFile = Join-Path $WorkspaceDir "project_coordination\\ACTIVE_TASK.json"
        if (Test-Path -LiteralPath $activeTaskFile) {
            try {
                $taskData = Get-Content -LiteralPath $activeTaskFile -Raw | ConvertFrom-Json
                if ($taskData.active_job_id -and [string]$taskData.active_job_id -match '^\\d+(\\.\\w+)?$') {
                    $j = [string]$taskData.active_job_id
                    if ($j -notmatch '\\.mmaster02$') { $j = "$j.mmaster02" }
                    [void]$candidateJobIds.Add($j)
                }
            } catch {}
        }

        # 3. From controller-state.json
        try {
            $tracked = @(Get-ActivePbsJobIds)
            foreach ($j in $tracked) {
                if ($j) {
                    $jFull = if ($j -notmatch '\\.mmaster02$') { "$j.mmaster02" } else { $j }
                    [void]$candidateJobIds.Add($jFull)
                }
            }
        } catch {}

        # 4. From live scheduler
        try {
            $liveScheduler = Get-LivePbsJobs
            foreach ($j in @($liveScheduler.LiveJobs)) {
                if ($j.JobId) {
                    $jFull = if ($j.JobId -notmatch '\\.mmaster02$') { "$($j.JobId).mmaster02" } else { $j.JobId }
                    [void]$candidateJobIds.Add($jFull)
                }
            }
        } catch {}'''

new_candidate_block = '''        # --------------------------------------------------------
        # Collect candidate PBS job IDs from:
        # 1. Latest agent response (e.g. submitted job ID)
        # 2. ACTIVE_TASK.json (active_job_id)
        # 3. HPC_JOB_LEDGER.csv (active/submitted jobs or latest entry)
        # 4. controller-state.json (tracked active jobs)
        # 5. Live scheduler (running/queued jobs)
        # --------------------------------------------------------
        $candidateJobIds = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::OrdinalIgnoreCase)

        $AddValidJobId = {
            param([string]$rawId)
            if ([string]::IsNullOrWhiteSpace($rawId)) { return }
            $cleaned = $rawId.Trim()
            if ($cleaned -match '^\\d{6,8}(\\.mmaster02)?$') {
                $fullId = if ($cleaned -notmatch '\\.mmaster02$') { "$cleaned.mmaster02" } else { $cleaned }
                [void]$candidateJobIds.Add($fullId)
            }
        }

        # 1. From agent response
        if (-not [string]::IsNullOrWhiteSpace($agentResponse)) {
            $mMatches = [regex]::Matches($agentResponse, '\\b(\\d{6,8}(\\.mmaster02)?)\\b')
            foreach ($m in $mMatches) {
                & $AddValidJobId $m.Value
            }
        }

        # 2. From ACTIVE_TASK.json
        $activeTaskFile = Join-Path $WorkspaceDir "project_coordination\\ACTIVE_TASK.json"
        if (Test-Path -LiteralPath $activeTaskFile) {
            try {
                $taskData = Get-Content -LiteralPath $activeTaskFile -Raw | ConvertFrom-Json
                if ($taskData.active_job_id) {
                    & $AddValidJobId ([string]$taskData.active_job_id)
                }
            } catch {}
        }

        # 3. From HPC_JOB_LEDGER.csv (active/running/queued jobs or latest entry)
        $hpcLedgerFile = Join-Path $WorkspaceDir "project_coordination\\HPC_JOB_LEDGER.csv"
        if (Test-Path -LiteralPath $hpcLedgerFile) {
            try {
                $ledgerEntries = Import-Csv -LiteralPath $hpcLedgerFile -ErrorAction SilentlyContinue
                if ($ledgerEntries) {
                    $activeRows = $ledgerEntries | Where-Object { $_.status -in @('SUBMITTED', 'RUNNING', 'QUEUED', 'ACTIVE') }
                    foreach ($row in $activeRows) {
                        if ($row.job_id) { & $AddValidJobId $row.job_id }
                    }
                    if ($activeRows.Count -eq 0 -and $ledgerEntries.Count -gt 0) {
                        $lastRow = $ledgerEntries[-1]
                        if ($lastRow.job_id) { & $AddValidJobId $lastRow.job_id }
                    }
                }
            } catch {}
        }

        # 4. From controller-state.json
        try {
            $tracked = @(Get-ActivePbsJobIds)
            foreach ($j in $tracked) {
                & $AddValidJobId $j
            }
        } catch {}

        # 5. From live scheduler (running/queued jobs only)
        try {
            $liveScheduler = Get-LivePbsJobs
            foreach ($j in @($liveScheduler.WaitableJobs)) {
                & $AddValidJobId $j
            }
        } catch {}'''

assert old_candidate_block in content, "old_candidate_block not found"
content = content.replace(old_candidate_block, new_candidate_block, 1)

if has_crlf:
    content = content.replace("\n", "\r\n")

with open(target_path, "w", encoding="utf-8", newline="") as f:
    f.write(content)

print(f"Target successfully updated: {target_path}")
