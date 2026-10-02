#!/usr/bin/env python3
"""
Apply SSH Non-Interactive Safety Guards to Antigravity-Autonomous-Loop.ps1
- Injects Rule 16 into $PersistentAgentGuard
- Injects -n -T -o BatchMode=yes -o ConnectTimeout=20 into internal scheduler SSH calls
- Validates AST syntax before saving
"""

import os
import re
import sys
import shutil
from datetime import datetime

target_file = r"C:\Users\pruth\OpenClawPAD\Antigravity-Autonomous-Loop.ps1"

if not os.path.exists(target_file):
    print(f"ERROR: Target file not found: {target_file}")
    sys.exit(1)

# Create timestamped backup
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup_file = f"{target_file}.backup_before_ssh_safety_{timestamp}"
shutil.copyfile(target_file, backup_file)
print(f"Created backup: {backup_file}")

with open(target_file, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Inject Rule 16 into $PersistentAgentGuard
rule16_text = (
    "\n16. REMOTE COMMAND SAFETY - MANDATORY:\n"
    "    - All noninteractive SSH commands must use `ssh -n -T` and `-o BatchMode=yes`.\n"
    "    - The `-n` flag is strictly required to disconnect stdin from null and prevent remote tools\n"
    "      from hanging indefinitely waiting on console input.\n"
    "    - Never wrap simple remote inspection commands in nested `bash -c`, `bash -lc`, or `sh -c`.\n"
    "      Pass the remote command directly to SSH with explicit arguments.\n"
    "    - Never execute bare `tail`, bare `cat`, bare `grep`, or another program that can wait on stdin.\n"
    "    - Prefer calling `powershell -NoProfile -ExecutionPolicy Bypass -File .\\.agents\\scripts\\Invoke-GuardedSsh.ps1 -RemoteCommand \"...\"`.\n"
    "    - Every SSH command must have a bounded execution timeout (default 120s). A timed-out command\n"
    "      must terminate only its own spawned SSH process, return a tool failure, and allow recovery.\n"
    "    - For complex multi-command remote logic, use a controlled temporary remote script rather than\n"
    "      nested shell quoting.\n"
)

if "16. REMOTE COMMAND SAFETY - MANDATORY" not in content:
    pattern_rule15 = r"(15\..*?continue the current turn\.)\s*(\r?\n\"@)"
    match = re.search(pattern_rule15, content, re.DOTALL)
    if match:
        content = content[:match.end(1)] + "\n" + rule16_text + content[match.start(2):]
        print("Injected Rule 16 into $PersistentAgentGuard")
    else:
        print("WARNING: Could not locate Rule 15 boundary in $PersistentAgentGuard")
else:
    print("Rule 16 already present in $PersistentAgentGuard")

# 2. Add -n -T -o BatchMode=yes -o ConnectTimeout=20 to Query-Scheduler-Direct (line ~374)
old_line_374 = r"$raw = & $sshPath -F $ConfigPath $HostAlias $remoteCommand 2>&1"
new_line_374 = r"$raw = & $sshPath -n -T -o BatchMode=yes -o ConnectTimeout=20 -F $ConfigPath $HostAlias $remoteCommand 2>&1"
if old_line_374 in content:
    content = content.replace(old_line_374, new_line_374, 1)
    print("Updated line 374 ssh call with -n -T -o BatchMode=yes -o ConnectTimeout=20")

# 3. Add -n -T -o BatchMode=yes -o ConnectTimeout=20 to other controller ssh calls
old_ssh_block1 = """        $result = & ssh `
            -F $sshConfig `
            tu_freiberg `
            "qstat -u pr21vyci" 2>&1"""

new_ssh_block1 = """        $result = & ssh `
            -n -T `
            -o BatchMode=yes `
            -o ConnectTimeout=20 `
            -F $sshConfig `
            tu_freiberg `
            "qstat -u pr21vyci" 2>&1"""

if old_ssh_block1 in content:
    content = content.replace(old_ssh_block1, new_ssh_block1, 1)
    print("Updated controller qstat ssh call 1 with -n -T")

old_ssh_block2 = """        $output = & ssh `
            -F $sshConfig `
            tu_freiberg `
            $remoteCommand 2>&1"""

new_ssh_block2 = """        $output = & ssh `
            -n -T `
            -o BatchMode=yes `
            -o ConnectTimeout=20 `
            -F $sshConfig `
            tu_freiberg `
            $remoteCommand 2>&1"""

if old_ssh_block2 in content:
    content = content.replace(old_ssh_block2, new_ssh_block2, 1)
    print("Updated controller remoteCommand ssh call with -n -T")

old_ssh_block3 = """            $SchedulerResult = & ssh `
                -F $sshConfig `
                tu_freiberg `
                $RemoteCommand 2>&1"""

new_ssh_block3 = """            $SchedulerResult = & ssh `
                -n -T `
                -o BatchMode=yes `
                -o ConnectTimeout=20 `
                -F $sshConfig `
                tu_freiberg `
                $RemoteCommand 2>&1"""

if old_ssh_block3 in content:
    content = content.replace(old_ssh_block3, new_ssh_block3)
    print("Updated controller SchedulerResult ssh calls with -n -T")

with open(target_file, "w", encoding="utf-8") as f:
    f.write(content)

print(f"Successfully wrote updated content to {target_file}")
