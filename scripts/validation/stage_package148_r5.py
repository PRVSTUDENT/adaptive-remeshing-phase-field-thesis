"""scripts/validation/stage_package148_r5.py
Task: F1597-CORRECT-PACKAGE72-STATE-TRANSFER
Protocol Version: 2

Stages Package 148 R5 to cluster scratch directory and verifies all hashes against EXECUTION_MANIFEST.json.
Runs authentic mechanical and phase datachecks using Abaqus 2023 on mlogin01.
"""
from __future__ import print_function
import hashlib
import json
import os
from pathlib import Path
import subprocess

REPO_ROOT = Path(__file__).resolve().parents[2]
R5_DIR = REPO_ROOT / "models/pandey_kumar_mode1/148_c4_package148_state_transfer_r5"
SSH_CONFIG = Path.home() / ".ssh/codex_config"
REMOTE_RUN_DIR = "/scratch9/pr21vyci/runs/mode1_c4_package148_state_transfer_r5"
REMOTE_R4_DIR = "/scratch9/pr21vyci/runs/mode1_c4_package148_state_transfer_r4"


def run_guarded_ssh(cmd, timeout=180):
    ps_cmd = [
        "powershell.exe",
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(REPO_ROOT / ".agents/scripts/Invoke-GuardedSsh.ps1"),
        "-RemoteCommand",
        cmd,
        "-TimeoutSeconds",
        str(timeout),
    ]
    res = subprocess.run(ps_cmd, cwd=str(REPO_ROOT), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"Guarded SSH failed (exit {res.returncode}): {res.stderr}\n{res.stdout}")
    return res.stdout


def scp_file(local_path, remote_path):
    cmd = [
        "scp.exe",
        "-F",
        str(SSH_CONFIG),
        "-B",
        "-o",
        "BatchMode=yes",
        str(local_path),
        f"tu_freiberg:{remote_path}",
    ]
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"SCP failed for {local_path} -> {remote_path}: {res.stderr}")
    return True


def stage_r5():
    print("Step 1: Creating remote directory structure...")
    run_guarded_ssh(f"mkdir -p {REMOTE_RUN_DIR}/runtime/scripts/validation {REMOTE_RUN_DIR}/runtime/scripts/state_transfer")

    print("Step 2: Copying base static files and runtime tree from R4 directory on cluster...")
    copy_base = (
        f"cp -p {REMOTE_R4_DIR}/active_set_boundary_cards.inc "
        f"{REMOTE_R4_DIR}/d_lower_bounds.csv "
        f"{REMOTE_R4_DIR}/f42_mixed_uel.for "
        f"{REMOTE_R4_DIR}/job_notifications.sh "
        f"{REMOTE_R4_DIR}/nodal_displacements_initial.csv "
        f"{REMOTE_R4_DIR}/nodal_phase_field_initial.csv "
        f"{REMOTE_RUN_DIR}/ && cp -rp {REMOTE_R4_DIR}/runtime {REMOTE_RUN_DIR}/"
    )
    run_guarded_ssh(copy_base)

    print("Step 3: Uploading R5-specific files via SCP...")
    r5_specific_files = [
        ("initial_conditions_solution.inc", f"{REMOTE_RUN_DIR}/initial_conditions_solution.inc"),
        ("M1_C4_PACKAGE148_STATE_TRANSFER.inp", f"{REMOTE_RUN_DIR}/M1_C4_PACKAGE148_STATE_TRANSFER.inp"),
        ("P148_MECHANICAL_DC.inp", f"{REMOTE_RUN_DIR}/P148_MECHANICAL_DC.inp"),
        ("P148_PHASE_DC.inp", f"{REMOTE_RUN_DIR}/P148_PHASE_DC.inp"),
        ("submit_M1_C4_P148_R5.pbs", f"{REMOTE_RUN_DIR}/submit_M1_C4_P148_R5.pbs"),
        ("PACKAGE_MANIFEST.json", f"{REMOTE_RUN_DIR}/PACKAGE_MANIFEST.json"),
        ("EXECUTION_MANIFEST.json", f"{REMOTE_RUN_DIR}/EXECUTION_MANIFEST.json"),
        ("run_datacheck.sh", f"{REMOTE_RUN_DIR}/run_datacheck.sh"),
    ]
    for local_name, remote_dest in r5_specific_files:
        print(f"  Uploading {local_name}...")
        scp_file(R5_DIR / local_name, remote_dest)

    # Make run_datacheck.sh executable
    run_guarded_ssh(f"chmod +x {REMOTE_RUN_DIR}/run_datacheck.sh")

    print("Step 4: Uploading verified Python driver and extractor to runtime tree...")
    driver = REPO_ROOT / "scripts/state_transfer/driver_package146_147_pdas_continuation.py"
    scp_file(driver, f"{REMOTE_RUN_DIR}/runtime/scripts/state_transfer/driver_package146_147_pdas_continuation.py")
    extractor = REPO_ROOT / "scripts/validation/extract_package148_iteration.py"
    scp_file(extractor, f"{REMOTE_RUN_DIR}/runtime/scripts/validation/extract_package148_iteration.py")
    deck_builder = REPO_ROOT / "scripts/state_transfer/build_package146_147_transfer_deck.py"
    scp_file(deck_builder, f"{REMOTE_RUN_DIR}/runtime/scripts/state_transfer/build_package146_147_transfer_deck.py")

    print("Step 5: Verifying remote hashes against EXECUTION_MANIFEST.json...")
    check_script = f"""import hashlib, json, sys
run_dir = '{REMOTE_RUN_DIR}'
with open(run_dir + '/EXECUTION_MANIFEST.json') as f:
    manifest = json.load(f)
errors = []
for fname, expected in manifest['files'].items():
    p = run_dir + '/' + fname
    try:
        with open(p, 'rb') as f:
            h = hashlib.sha256(f.read()).hexdigest().lower()
        if h != expected.lower():
            errors.append(f'Hash mismatch for {{fname}}: {{h}} != {{expected}}')
    except Exception as e:
        errors.append(f'Missing {{fname}}: {{e}}')
for rname, expected in manifest['runtime_source_hashes'].items():
    p = manifest['runtime_root'] + '/' + rname
    try:
        with open(p, 'rb') as f:
            h = hashlib.sha256(f.read()).hexdigest().upper()
        if h != expected.upper():
            errors.append(f'Hash mismatch for runtime {{rname}}: {{h}} != {{expected}}')
    except Exception as e:
        errors.append(f'Missing runtime {{rname}}: {{e}}')
if errors:
    print('ERRORS:\\n' + '\\n'.join(errors))
    sys.exit(1)
print('ALL_REMOTE_HASHES_VERIFIED_PASS')
"""
    verify_py_path = f"{REMOTE_RUN_DIR}/verify_staged_hashes.py"
    run_guarded_ssh(f"cat << 'EOF' > {verify_py_path}\n{check_script}\nEOF")
    out = run_guarded_ssh(f"python3 {verify_py_path}")
    print(out)
    if "ALL_REMOTE_HASHES_VERIFIED_PASS" not in out:
        raise RuntimeError("Remote hash verification failed!")

    print("Step 6: Running authentic mechanical datacheck on cluster...")
    out_mech = run_guarded_ssh(f"bash {REMOTE_RUN_DIR}/run_datacheck.sh mechanical")
    print(out_mech)
    if "AUTHENTIC_DATACHECK_PASS" not in out_mech:
        raise RuntimeError(f"Mechanical datacheck failed: {out_mech}")

    print("Step 7: Running authentic phase datacheck on cluster...")
    out_phase = run_guarded_ssh(f"bash {REMOTE_RUN_DIR}/run_datacheck.sh phase")
    print(out_phase)
    if "AUTHENTIC_DATACHECK_PASS" not in out_phase:
        raise RuntimeError(f"Phase datacheck failed: {out_phase}")

    print("STAGE_AND_DATACHECK_COMPLETE: Exit 0 on both mechanical and phase datachecks!")


if __name__ == '__main__':
    stage_r5()
