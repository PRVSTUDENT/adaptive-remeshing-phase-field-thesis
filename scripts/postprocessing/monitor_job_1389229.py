#!/usr/bin/env python3
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")

SSH_KEY = os.path.expanduser("~/.ssh/tu_freiberg_codex")
REMOTE_HOST = "pr21vyci@mlogin01.hrz.tu-freiberg.de"
REMOTE_CANDIDATE = "/home/pr21vyci/projects/adaptive-remeshing/models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART2R7"

remote_cmd = (
    "qstat 1389229.mmaster02 || true; "
    f"echo '=== STA ==='; cat {REMOTE_CANDIDATE}/M2STATE_FRACFIX_RESTART2R7.sta 2>/dev/null || true; "
    f"echo '=== LOG TAIL ==='; tail -n 25 {REMOTE_CANDIDATE}/M2STATE_FRACFIX_RESTART2R7.o* 2>/dev/null || true; "
    f"echo '=== MSG SUMMARY ==='; grep -E 'INCREMENT|ITERATION|COMPLETED|ERROR|FATAL' {REMOTE_CANDIDATE}/M2STATE_FRACFIX_RESTART2R7.msg 2>/dev/null | tail -n 20 || true"
)

cmd = [
    "ssh", "-i", SSH_KEY,
    "-o", "BatchMode=yes",
    "-o", "StrictHostKeyChecking=no",
    REMOTE_HOST,
    remote_cmd
]
res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
print("STDOUT:")
print(res.stdout.decode("utf-8", errors="replace"))
print("STDERR:")
print(res.stderr.decode("utf-8", errors="replace"))
