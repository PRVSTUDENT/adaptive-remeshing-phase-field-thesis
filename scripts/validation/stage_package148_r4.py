"""scripts/validation/stage_package148_r4.py
Task: F1597-CORRECT-PACKAGE72-STATE-TRANSFER
Protocol Version: 2

Stages Package 148 R4 to cluster scratch directory and verifies all hashes against EXECUTION_MANIFEST.json.
"""
from __future__ import print_function
import hashlib
import json
import os
from pathlib import Path
import subprocess

REPO_ROOT = Path(__file__).resolve().parents[2]
R4_DIR = REPO_ROOT / "models/pandey_kumar_mode1/148_c4_package148_state_transfer_r4"
SSH_CONFIG = Path.home() / ".ssh/codex_config"
REMOTE_RUN_DIR = "/scratch9/pr21vyci/runs/mode1_c4_package148_state_transfer_r4"
REMOTE_R3_DIR = "/scratch9/pr21vyci/runs/mode1_c4_package148_state_transfer_r3"


def run_guarded_ssh(cmd, timeout=120):
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


def stage_r4():
    print("Step 1: Creating remote directory structure...")
    run_guarded_ssh(f"mkdir -p {REMOTE_RUN_DIR}/runtime/scripts/validation {REMOTE_RUN_DIR}/runtime/scripts/state_transfer")

    print("Step 2: Copying base files and runtime tree from R3 directory on cluster...")
    copy_base = (
        f"cp -p {REMOTE_R3_DIR}/active_set_boundary_cards.inc "
        f"{REMOTE_R3_DIR}/d_lower_bounds.csv "
        f"{REMOTE_R3_DIR}/f42_mixed_uel.for "
        f"{REMOTE_R3_DIR}/initial_conditions_solution.inc "
        f"{REMOTE_R3_DIR}/job_notifications.sh "
        f"{REMOTE_R3_DIR}/M1_C4_PACKAGE148_STATE_TRANSFER.inp "
        f"{REMOTE_R3_DIR}/nodal_displacements_initial.csv "
        f"{REMOTE_R3_DIR}/nodal_phase_field_initial.csv "
        f"{REMOTE_R3_DIR}/P148_MECHANICAL_DC.inp "
        f"{REMOTE_R3_DIR}/P148_PHASE_DC.inp "
        f"{REMOTE_RUN_DIR}/ && cp -rp {REMOTE_R3_DIR}/runtime {REMOTE_RUN_DIR}/"
    )
    run_guarded_ssh(copy_base)

    print("Step 3: Uploading R4-specific files via SCP...")
    r4_specific_files = [
        ("submit_M1_C4_P148_R4.pbs", f"{REMOTE_RUN_DIR}/submit_M1_C4_P148_R4.pbs"),
        ("PACKAGE_MANIFEST.json", f"{REMOTE_RUN_DIR}/PACKAGE_MANIFEST.json"),
        ("EXECUTION_MANIFEST.json", f"{REMOTE_RUN_DIR}/EXECUTION_MANIFEST.json"),
        ("run_datacheck.sh", f"{REMOTE_RUN_DIR}/run_datacheck.sh"),
    ]
    for local_name, remote_dest in r4_specific_files:
        print(f"  Uploading {local_name}...")
        scp_file(R4_DIR / local_name, remote_dest)

    # Make run_datacheck.sh executable
    run_guarded_ssh(f"chmod +x {REMOTE_RUN_DIR}/run_datacheck.sh")

    print("Step 4: Uploading repaired Python driver and extractor to runtime tree...")
    repaired_driver = REPO_ROOT / "scripts/state_transfer/driver_package146_147_pdas_continuation.py"
    scp_file(repaired_driver, f"{REMOTE_RUN_DIR}/runtime/scripts/state_transfer/driver_package146_147_pdas_continuation.py")
    extractor = REPO_ROOT / "scripts/validation/extract_package148_iteration.py"
    scp_file(extractor, f"{REMOTE_RUN_DIR}/runtime/scripts/validation/extract_package148_iteration.py")

    print("Step 5: Verifying remote hashes against EXECUTION_MANIFEST.json...")
    # Upload verification helper to remote
    helper_script = f"""import hashlib, json, sys
run_dir = '{REMOTE_RUN_DIR}'
with open(run_dir + '/EXECUTION_MANIFEST.json') as f:
    manifest = json.load(f)
errors = []
for fname, exp_hash in manifest['files'].items():
    p = run_dir + '/' + fname
    try:
        with open(p, 'rb') as fp:
            actual = hashlib.sha256(fp.read()).hexdigest().lower()
        if actual != exp_hash.lower():
            errors.append((fname, exp_hash, actual))
    except Exception as e:
        errors.append((fname, exp_hash, str(e)))
for src_rel, exp_hash in manifest['runtime_source_hashes'].items():
    p = run_dir + '/runtime/' + src_rel
    try:
        with open(p, 'rb') as fp:
            actual = hashlib.sha256(fp.read()).hexdigest().lower()
        if actual != exp_hash.lower():
            errors.append((src_rel, exp_hash, actual))
    except Exception as e:
        errors.append((src_rel, exp_hash, str(e)))
if errors:
    print('HASH_MISMATCH:', errors)
    sys.exit(1)
else:
    print('ALL_REMOTE_HASHES_MATCH_EXACTLY')
"""
    helper_path = REPO_ROOT / "results/validation/verify_r4_remote_hashes.py"
    helper_path.write_text(helper_script, encoding="utf-8")
    scp_file(helper_path, f"{REMOTE_RUN_DIR}/verify_remote_hashes.py")

    output = run_guarded_ssh(f"python3 {REMOTE_RUN_DIR}/verify_remote_hashes.py")
    print("Verification output:", output.strip())
    assert "ALL_REMOTE_HASHES_MATCH_EXACTLY" in output, f"Verification failed: {output}"


if __name__ == "__main__":
    stage_r4()
