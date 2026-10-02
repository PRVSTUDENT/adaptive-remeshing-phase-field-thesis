#!/usr/bin/env python3
import os
import subprocess
import sys

SSH_KEY = os.path.expanduser("~/.ssh/tu_freiberg_codex")
REMOTE_HOST = "pr21vyci@mlogin01.hrz.tu-freiberg.de"
REMOTE_CANDIDATE = "/home/pr21vyci/projects/adaptive-remeshing/models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART2R7"

step1_cmd = (
    "source /etc/profile.d/modules.sh 2>/dev/null || source /etc/profile 2>/dev/null || true && "
    "module purge && "
    "module load gcc/11.4.0 intel/2024.2.0 abaqus/2023 python/gcc/11.4.0/3.11.7 && "
    f"cd {REMOTE_CANDIDATE} && "
    "head -n 108573 M2STATE_FRACFIX_RESTART2R7.inp > STEP1_SOLVE.inp && "
    "rm -f STEP1_SOLVE.odb STEP1_SOLVE.msg STEP1_SOLVE.dat STEP1_SOLVE.sta STEP1_SOLVE.com STEP1_SOLVE.prt && "
    "abaqus job=STEP1_SOLVE user=f42_mixed_uel.for interactive double=both cpus=1 memory=16gb scratch=. && "
    "grep -E 'THE ANALYSIS HAS COMPLETED|ERROR|FATAL|ILLEGAL' STEP1_SOLVE.msg || true"
)

cmd = ["ssh", "-i", SSH_KEY, "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=no", REMOTE_HOST, step1_cmd]
res = subprocess.run(cmd, capture_output=True, text=True)
print("STDOUT:")
print(res.stdout)
print("STDERR:")
print(res.stderr)
print("RC =", res.returncode)
