import os
import sys
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PKG_DIR = ROOT / "models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART1R1R7"

def main():
    key = os.path.expanduser('~/.ssh/tu_freiberg_codex')
    host = 'pr21vyci@mlogin01.hrz.tu-freiberg.de'
    remote_pkg_dir = '/home/pr21vyci/projects/adaptive-remeshing/models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART1R1R7'

    print("=== Step 1: Upload candidate M2STATE_FRACFIX_RESTART1R1R7 to cluster ===")
    mkdir_cmd = ['ssh', '-i', key, '-o', 'BatchMode=yes', '-o', 'StrictHostKeyChecking=no', host, f'mkdir -p {remote_pkg_dir}']
    subprocess.run(mkdir_cmd, check=True)

    files_to_upload = [
        "M2STATE_FRACFIX_RESTART1R1R7.inp",
        "f42_mixed_uel.for",
        "STATE_TRANSFER_ARTIFACT.json",
        "TRANSFER_MANIFEST.json",
        "RESTART_ACCEPTANCE_CONTRACT.json",
        "job_notifications.sh",
        "validate_package_manifest.py",
        "M2STATE_FRACFIX_RESTART1R1R7.pbs",
        "submit_m2state_fracfix_restart1r1r7.sh",
        "PACKAGE_MANIFEST.json"
    ]

    for f in files_to_upload:
        src = PKG_DIR / f
        dest = f"{host}:{remote_pkg_dir}/{f}"
        scp_cmd = ['scp', '-i', key, '-o', 'BatchMode=yes', '-o', 'StrictHostKeyChecking=no', str(src), dest]
        subprocess.run(scp_cmd, check=True)
    print("Files uploaded successfully.")

    print("\n=== Step 2: Remote Manifest Verification & Datacheck ===")
    remote_script = f"""set -e
cd {remote_pkg_dir}
sed -i 's/\\r$//' submit_m2state_fracfix_restart1r1r7.sh validate_package_manifest.py M2STATE_FRACFIX_RESTART1R1R7.pbs job_notifications.sh 2>/dev/null || true
chmod +x submit_m2state_fracfix_restart1r1r7.sh validate_package_manifest.py

echo "--- Validating Manifest ---"
python3 validate_package_manifest.py PACKAGE_MANIFEST.json

echo "--- Loading Modules ---"
module purge
module load gcc/11.4.0 intel/2024.2.0 abaqus/2023 python/gcc/11.4.0/3.11.7

echo "--- Running Abaqus Datacheck ---"
abaqus job=M2STATE_FRACFIX_RESTART1R1R7_DATACHECK user=f42_mixed_uel.for input=M2STATE_FRACFIX_RESTART1R1R7.inp datacheck interactive
echo "DATACHECK_EXIT_CODE=$?"

echo "--- Creating Step 1-only Model for Interactive Qualification Solve ---"
python3 -c "
with open('M2STATE_FRACFIX_RESTART1R1R7.inp') as f:
    text = f.read()

# Stop before Step 2
step2_idx = text.find('*STEP, NAME=Step-2-Continuation')
if step2_idx != -1:
    step1_text = text[:step2_idx]
    with open('M2STATE_FRACFIX_RESTART1R1R7_STEP1.inp', 'w') as f_out:
        f_out.write(step1_text)
    print('Created M2STATE_FRACFIX_RESTART1R1R7_STEP1.inp')
else:
    print('Error: Step 2 not found')
"

echo "--- Running Interactive Step-1 Qualification Solve ---"
abaqus job=M2STATE_FRACFIX_RESTART1R1R7_STEP1 user=f42_mixed_uel.for input=M2STATE_FRACFIX_RESTART1R1R7_STEP1.inp interactive
echo "STEP1_SOLVE_EXIT_CODE=$?"

echo "--- Guarded Wrapper Dry-Run ---"
./submit_m2state_fracfix_restart1r1r7.sh --dry-run
"""
    clean_bytes = remote_script.replace('\r\n', '\n').replace('\r', '\n').encode('utf-8')

    cmd = ['ssh', '-i', key, '-o', 'BatchMode=yes', '-o', 'StrictHostKeyChecking=no', host, 'bash']
    res = subprocess.run(cmd, input=clean_bytes, capture_output=True, text=False)
    print("STDOUT:\n", res.stdout.decode('utf-8', errors='replace'))
    print("STDERR:\n", res.stderr.decode('utf-8', errors='replace'))

if __name__ == "__main__":
    main()
