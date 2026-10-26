"""
Apply Idempotent External-Blocker Guard to:
1. .agents/scripts/bridge_rules.txt
2. .agents/scripts/project_alignment_guard.txt
3. .agents/scripts/Invoke-ChatGPTBridge.ps1
4. OpenClawPAD deployment targets
"""
import os
import shutil

REPO_ROOT = r"D:\Master thesis\Adaptive remeshing"
USERPROFILE = os.environ.get("USERPROFILE", r"C:\Users\pruth")

GUARD_BLOCK = """---------------- EXTERNAL AUTHENTICATION & IDEMPOTENT BRIDGE GUARD ----------------
- External Authentication Blocker Precedence:
  When an external institutional authentication blocker (e.g. INTERACTIVE_SSO_REQUIRED /
  R18_OFFLINE_QUALIFIED__INTERACTIVE_SSO_REQUIRED / BLOCKED_EXTERNAL_AUTHENTICATION) is active
  and cluster network connectivity is unauthenticated (e.g. eduVPN OAuth expired, DNS resolution
  of cluster login nodes blocked pending workstation browser SSO), outgoing ChatGPT bridge dispatches
  MUST be suppressed to prevent infinite orchestration loops.
- Resumption Requirements:
  Resumption of bridge dispatch requires a genuine external event:
  1. Live cluster connectivity restored (authenticated DNS resolution and SSH reachability confirmed), OR
  2. Explicit administrative override via -Resume / -ForceResume parameter or RESUME_AFTER_SSO=1 environment variable.
- Standing Authorization & Offline Safety:
  Package 108 Revision 18 and frozen user subroutines (f42_mixed_uel.for, f42_unified_12dof_active_set_uel.for)
  must remain 100% bitwise frozen. Do not fabricate artificial R19 packages or repeat identical offline
  qualification checks merely to satisfy loop activity.
"""

def update_bridge_rules():
    path = os.path.join(REPO_ROOT, r".agents\scripts\bridge_rules.txt")
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    target = "---------------- MASTER SCIENTIFIC GOVERNANCE & ROADMAP ----------------"
    if "EXTERNAL AUTHENTICATION & IDEMPOTENT BRIDGE GUARD" not in content:
        assert target in content, "Target header not found in bridge_rules.txt"
        replacement = GUARD_BLOCK.strip() + "\n\n" + target
        new_content = content.replace(target, replacement, 1)
        with open(path, "w", encoding="utf-8", newline="\r\n") as f:
            f.write(new_content)
        print("Updated bridge_rules.txt successfully.")
    else:
        print("bridge_rules.txt already has guard block.")

def update_project_alignment_guard():
    path = os.path.join(REPO_ROOT, r".agents\scripts\project_alignment_guard.txt")
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    target = "================================================================================\n"
    if "EXTERNAL AUTHENTICATION & IDEMPOTENT BRIDGE GUARD" not in content:
        # insert right before the final delimiter line
        last_idx = content.rfind("================================================================================")
        assert last_idx != -1, "Target delimiter not found in project_alignment_guard.txt"
        new_content = content[:last_idx] + GUARD_BLOCK.strip() + "\n\n" + content[last_idx:]
        with open(path, "w", encoding="utf-8", newline="\r\n") as f:
            f.write(new_content)
        print("Updated project_alignment_guard.txt successfully.")
    else:
        print("project_alignment_guard.txt already has guard block.")

def update_invoke_chatgpt_bridge():
    path = os.path.join(REPO_ROOT, r".agents\scripts\Invoke-ChatGPTBridge.ps1")
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Update param block
    param_target = "[switch]$DryRun = $false\n    )"
    param_replacement = """[switch]$DryRun = $false,

        [switch]$Resume = $false,

        [switch]$ForceResume = $false,

        [string]$TaskId = $null
    )"""

    if "[switch]$Resume = $false" not in content:
        # Check CRLF or LF
        if param_target not in content:
            param_target = param_target.replace("\n", "\r\n")
            param_replacement = param_replacement.replace("\n", "\r\n")
        assert param_target in content, "param target not found in Invoke-ChatGPTBridge.ps1"
        content = content.replace(param_target, param_replacement, 1)

    # 2. Add Section 2d External Authentication Blocker Guard before DryRun
    dryrun_target = "# --- 2d. DryRun Mode ---"
    if "# --- 2d. External Authentication Blocker Guard ---" not in content:
        assert dryrun_target in content, "DryRun marker not found in Invoke-ChatGPTBridge.ps1"
        guard_code = """    # --- 2d. External Authentication Blocker Guard ---
    $isBlocked = $false
    $ssoBlockerPatterns = 'INTERACTIVE_SSO_REQUIRED|BLOCKED_EXTERNAL_AUTHENTICATION|OFFLINE_QUALIFIED__INTERACTIVE_SSO_REQUIRED'

    # Check if prompt text explicitly indicates external authentication blocker
    if ($PromptText -match $ssoBlockerPatterns) {
        $isBlocked = $true
    }

    # Check active task and current state in project coordination if task matches or not specified
    if (-not $isBlocked) {
        $coordDirs = @(
            "D:\\Master thesis\\Adaptive remeshing\\project_coordination",
            (Join-Path $PSScriptRoot "..\\..\\project_coordination"),
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
                        if ($PromptText -notmatch 'F1597|Package\\s*108|Revision\\s*18|R18') {
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

    if ($isBlocked -and -not $isResumed) {
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

    # --- 2e. DryRun Mode ---"""

        if "\r\n" in content:
            guard_code = guard_code.replace("\n", "\r\n")

        content = content.replace(dryrun_target, guard_code, 1)

        with open(path, "w", encoding="utf-8", newline="\r\n") as f:
            f.write(content)
        print("Updated Invoke-ChatGPTBridge.ps1 successfully.")
    else:
        print("Invoke-ChatGPTBridge.ps1 already has guard.")

def deploy_to_openclawpad():
    src_bridge = os.path.join(REPO_ROOT, r".agents\scripts\Invoke-ChatGPTBridge.ps1")
    dst_bridge = os.path.join(USERPROFILE, r"OpenClawPAD\ChatGPTBridge\Invoke-ChatGPTBridge.ps1")
    if os.path.exists(os.path.dirname(dst_bridge)):
        shutil.copy2(src_bridge, dst_bridge)
        print(f"Deployed {dst_bridge}")

    src_rules = os.path.join(REPO_ROOT, r".agents\scripts\bridge_rules.txt")
    dst_rules = os.path.join(USERPROFILE, r"OpenClawPAD\ChatGPTBridge\bridge_rules.txt")
    if os.path.exists(os.path.dirname(dst_rules)):
        shutil.copy2(src_rules, dst_rules)
        print(f"Deployed {dst_rules}")

    src_guard = os.path.join(REPO_ROOT, r".agents\scripts\project_alignment_guard.txt")
    dst_guard = os.path.join(USERPROFILE, r"OpenClawPAD\project_alignment_guard.txt")
    if os.path.exists(os.path.dirname(dst_guard)):
        shutil.copy2(src_guard, dst_guard)
        print(f"Deployed {dst_guard}")

if __name__ == "__main__":
    update_bridge_rules()
    update_project_alignment_guard()
    update_invoke_chatgpt_bridge()
    deploy_to_openclawpad()
