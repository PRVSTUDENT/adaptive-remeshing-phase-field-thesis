import os
import sys
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CANDIDATE_DIR = ROOT / "models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART2R1"

def main():
    key = os.path.expanduser("~/.ssh/tu_freiberg_codex")
    remote_host = "pr21vyci@mlogin01.hrz.tu-freiberg.de"
    remote_base = "/home/pr21vyci/projects/adaptive-remeshing/models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART2R1"

    # 1. Create remote directory
    mkdir_cmd = ["ssh", "-i", key, "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=no", remote_host, f"mkdir -p {remote_base}"]
    subprocess.run(mkdir_cmd, check=True)

    # 2. SCP candidate files to remote
    print("Staging candidate files to remote...")
    for f in CANDIDATE_DIR.glob("*"):
        if f.is_file():
            scp_cmd = ["scp", "-i", key, "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=no", str(f), f"{remote_host}:{remote_base}/"]
            subprocess.run(scp_cmd, check=True)

    # Copy unit test to remote for remote regression
    remote_test_dir = "/home/pr21vyci/projects/adaptive-remeshing/tests/unit"
    subprocess.run(["ssh", "-i", key, "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=no", remote_host, f"mkdir -p {remote_test_dir}"], check=True)
    subprocess.run(["scp", "-i", key, "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=no", str(ROOT / "tests/unit/test_m2state_fracfix_restart2r1.py"), f"{remote_host}:{remote_test_dir}/"], check=True)

    # 3. Execute remote qualification script
    remote_script = f"""
import os, sys, json, hashlib, subprocess

remote_dir = '{remote_base}'
os.chdir(remote_dir)

# A. Hash check
with open('PACKAGE_MANIFEST.json') as f:
    m = json.load(f)
files = m.get('files', m.get('file_hashes', {{}}))

hash_errors = 0
for fname, h in files.items():
    actual = hashlib.sha256(open(fname, 'rb').read()).hexdigest()
    if actual != h:
        print('HASH MISMATCH:', fname, actual, h)
        hash_errors += 1

if hash_errors == 0:
    print('REMOTE_HASH_CHECK = PASS')

# B. Unit tests
res_ut = subprocess.run([sys.executable, '-m', 'unittest', 'tests.unit.test_m2state_fracfix_restart2r1'], cwd='/home/pr21vyci/projects/adaptive-remeshing', stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
print('REMOTE_UNIT_TESTS_STDOUT:', res_ut.stdout)
print('REMOTE_UNIT_TESTS_STDERR:', res_ut.stderr)
print('REMOTE_UNIT_TESTS_RC =', res_ut.returncode)

# C. Guarded wrapper dry-run
res_dry = subprocess.run(['bash', 'submit_m2state_fracfix_restart2r1.sh', '--dry-run'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
print('GUARDED_DRY_RUN_STDOUT:', res_dry.stdout)
print('GUARDED_DRY_RUN_RC =', res_dry.returncode)

# D. Abaqus Syntaxcheck
syn_cmd = 'source /etc/profile; export XDG_RUNTIME_DIR=/tmp/runtime-pr21vyci; mkdir -p /tmp/runtime-pr21vyci; module load abaqus/2023 gcc/11.4.0 intel/2024.2.0; abaqus syntaxcheck job=M2STATE_FRACFIX_RESTART2R1 user=f42_mixed_uel.for interactive'
res_syn = subprocess.run(['bash', '-c', syn_cmd], stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
print('SYNTAXCHECK_STDOUT:', res_syn.stdout)
print('SYNTAXCHECK_STDERR:', res_syn.stderr)
print('SYNTAXCHECK_RC =', res_syn.returncode)

# Inspect log/dat for error/fatal
err_count = 0
fat_count = 0
if os.path.exists('M2STATE_FRACFIX_RESTART2R1.log'):
    log_text = open('M2STATE_FRACFIX_RESTART2R1.log', 'r', errors='ignore').read()
    err_count += log_text.upper().count('ERROR')
    fat_count += log_text.upper().count('FATAL')

if os.path.exists('M2STATE_FRACFIX_RESTART2R1.dat'):
    dat_text = open('M2STATE_FRACFIX_RESTART2R1.dat', 'r', errors='ignore').read()
    err_count += dat_text.upper().count('***ERROR')
    fat_count += dat_text.upper().count('***FATAL')

print('SYNTAXCHECK_ERROR_COUNT =', err_count)
print('SYNTAXCHECK_FATAL_COUNT =', fat_count)

"""
    cmd = [
        "ssh", "-i", key,
        "-o", "BatchMode=yes",
        "-o", "StrictHostKeyChecking=no",
        remote_host,
        f"python3 -c {subprocess.list2cmdline([remote_script])}"
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    print("STDOUT:\n", res.stdout)
    print("STDERR:\n", res.stderr)
    print("RC =", res.returncode)

if __name__ == "__main__":
    main()
