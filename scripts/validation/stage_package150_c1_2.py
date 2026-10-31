# -*- coding: utf-8 -*-
"""
scripts/validation/stage_package150_c1_2.py
Task: F1597-CORRECT-PACKAGE72-STATE-TRANSFER
Protocol Version: 2

Stages Package 150 Stage C1-2 forward continuation package to cluster scratch.
Verifies all file and runtime hashes against EXECUTION_MANIFEST.json.
Executes authentic mechanical and phase datachecks using Abaqus 2023.
"""
from __future__ import print_function
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PKG_DIR = REPO_ROOT / "models/pandey_kumar_mode1/150_c4_package150_c1_2_continuation"
SSH_CONFIG = Path.home() / ".ssh/codex_config"
REMOTE_RUN_DIR = "/scratch9/pr21vyci/runs/mode1_c4_package150_c1_2_continuation"
REMOTE_R8_DIR = "/scratch9/pr21vyci/runs/mode1_c4_package148_state_transfer_r8"


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
        raise RuntimeError("Guarded SSH failed (exit %d): %s\n%s" % (res.returncode, res.stderr, res.stdout))
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
        "tu_freiberg:%s" % remote_path,
    ]
    res = subprocess.run(cmd, cwd=str(REPO_ROOT), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if res.returncode != 0:
        raise RuntimeError("SCP failed (exit %d): %s\n%s" % (res.returncode, res.stderr, res.stdout))


def stage_package():
    print("Step 1: Creating remote directory tree...")
    dirs = [
        REMOTE_RUN_DIR,
        "%s/runtime/scripts/state_transfer" % REMOTE_RUN_DIR,
        "%s/runtime/scripts/validation" % REMOTE_RUN_DIR,
        "%s/runtime/models/pandey_kumar_mode1/147_c4_corrected_reference" % REMOTE_RUN_DIR,
        "%s/runtime/results/validation/package148" % REMOTE_RUN_DIR,
    ]
    run_guarded_ssh("mkdir -p " + " ".join(dirs))

    print("Step 2: Copying reusable files from R8 directory...")
    # Copy files from R8 that are identical
    reusable = [
        ("f42_mixed_uel.for", "%s/f42_mixed_uel.for" % REMOTE_RUN_DIR),
        ("job_notifications.sh", "%s/job_notifications.sh" % REMOTE_RUN_DIR),
        ("runtime/scripts/state_transfer/c3_int_to_c4_spatial_mapping.py",
         "%s/runtime/scripts/state_transfer/c3_int_to_c4_spatial_mapping.py" % REMOTE_RUN_DIR),
        ("runtime/scripts/state_transfer/driver_package146_147_pdas_continuation.py",
         "%s/runtime/scripts/state_transfer/driver_package146_147_pdas_continuation.py" % REMOTE_RUN_DIR),
        ("runtime/scripts/validation/extract_package148_iteration.py",
         "%s/runtime/scripts/validation/extract_package148_iteration.py" % REMOTE_RUN_DIR),
        ("runtime/models/pandey_kumar_mode1/147_c4_corrected_reference/M1_C4_CORRECTED_PACKAGE147_REF.inp",
         "%s/runtime/models/pandey_kumar_mode1/147_c4_corrected_reference/M1_C4_CORRECTED_PACKAGE147_REF.inp" % REMOTE_RUN_DIR),
    ]
    copy_cmds = ["cp -p %s/%s %s" % (REMOTE_R8_DIR, src, dst) for src, dst in reusable]
    run_guarded_ssh("; ".join(copy_cmds))

    print("Step 3: Uploading Package 150 unique files via SCP...")
    upload_files = [
        (PKG_DIR / "active_set_boundary_cards.inc", "%s/active_set_boundary_cards.inc" % REMOTE_RUN_DIR),
        (PKG_DIR / "d_lower_bounds.csv", "%s/d_lower_bounds.csv" % REMOTE_RUN_DIR),
        (PKG_DIR / "initial_conditions_solution.inc", "%s/initial_conditions_solution.inc" % REMOTE_RUN_DIR),
        (PKG_DIR / "M1_C4_PACKAGE150_C1_2_CONTINUATION.inp", "%s/M1_C4_PACKAGE150_C1_2_CONTINUATION.inp" % REMOTE_RUN_DIR),
        (PKG_DIR / "nodal_displacements_initial.csv", "%s/nodal_displacements_initial.csv" % REMOTE_RUN_DIR),
        (PKG_DIR / "nodal_phase_field_initial.csv", "%s/nodal_phase_field_initial.csv" % REMOTE_RUN_DIR),
        (PKG_DIR / "P150_MECHANICAL_DC.inp", "%s/P150_MECHANICAL_DC.inp" % REMOTE_RUN_DIR),
        (PKG_DIR / "P150_PHASE_DC.inp", "%s/P150_PHASE_DC.inp" % REMOTE_RUN_DIR),
        (PKG_DIR / "run_datacheck.sh", "%s/run_datacheck.sh" % REMOTE_RUN_DIR),
        (PKG_DIR / "submit_M1_C4_P150_C1_2.pbs", "%s/submit_M1_C4_P150_C1_2.pbs" % REMOTE_RUN_DIR),
        (PKG_DIR / "EXECUTION_MANIFEST.json", "%s/EXECUTION_MANIFEST.json" % REMOTE_RUN_DIR),
        (PKG_DIR / "PACKAGE_MANIFEST.json", "%s/PACKAGE_MANIFEST.json" % REMOTE_RUN_DIR),
        (REPO_ROOT / "scripts/state_transfer/driver_package150_c1_2_continuation.py",
         "%s/runtime/scripts/state_transfer/driver_package150_c1_2_continuation.py" % REMOTE_RUN_DIR),
        (REPO_ROOT / "results/validation/package148/r8_equilibrium_checkpoint.json",
         "%s/runtime/results/validation/package148/r8_equilibrium_checkpoint.json" % REMOTE_RUN_DIR),
    ]

    for local_p, remote_p in upload_files:
        print("  Uploading %s -> %s" % (local_p.name, remote_p))
        scp_file(local_p, remote_p)

    print("Step 4: Setting permissions...")
    run_guarded_ssh("chmod 755 %s/run_datacheck.sh %s/submit_M1_C4_P150_C1_2.pbs %s/job_notifications.sh" %
                    (REMOTE_RUN_DIR, REMOTE_RUN_DIR, REMOTE_RUN_DIR))

    print("Step 5: Verifying remote SHA-256 hashes against EXECUTION_MANIFEST.json...")
    verify_script = """
import hashlib, json, os, sys
from pathlib import Path

run_dir = Path(%r)
manifest = json.loads((run_dir / "EXECUTION_MANIFEST.json").read_text())

# Verify package files
for fname, exp_hash in manifest["files"].items():
    fpath = run_dir / fname
    if not fpath.is_file():
        print("MISSING_FILE: " + fname)
        sys.exit(1)
    act_hash = hashlib.sha256(fpath.read_bytes()).hexdigest().lower()
    if act_hash != exp_hash.lower():
        print("HASH_MISMATCH: " + fname + " exp=" + exp_hash + " act=" + act_hash)
        sys.exit(2)

# Verify runtime dependencies
for rpath, exp_hash in manifest["runtime_source_hashes"].items():
    fpath = run_dir / "runtime" / rpath
    if not fpath.is_file():
        print("MISSING_RUNTIME: " + rpath)
        sys.exit(3)
    act_hash = hashlib.sha256(fpath.read_bytes()).hexdigest().upper()
    if act_hash != exp_hash.upper():
        print("RUNTIME_HASH_MISMATCH: " + rpath + " exp=" + exp_hash + " act=" + act_hash)
        sys.exit(4)

print("ALL_HASHES_VERIFIED_PASS")
""" % REMOTE_RUN_DIR

    encoded = verify_script.encode().hex()
    res = run_guarded_ssh("python3 -c exec\\(bytes.fromhex\\(\\'" + encoded + "\\'\\)\\)")
    print("Hash verification result:", res.strip())
    if "ALL_HASHES_VERIFIED_PASS" not in res:
        raise RuntimeError("Remote hash verification failed: %s" % res)

    print("Step 6: Executing authentic datachecks on cluster (MLOGIN)...")
    for role in ("mechanical", "phase"):
        job_name = "P150_MECHANICAL_DC" if role == "mechanical" else "P150_PHASE_DC"
        check_exist = run_guarded_ssh("test -f %s/%s.dat && echo 'EXISTS' || echo 'MISSING'" % (REMOTE_RUN_DIR, job_name))
        if "EXISTS" in check_exist:
            print("  Datacheck output for %s already exists; preserving authentic evidence." % role)
            continue
        print("  Running datacheck for role: %s" % role)
        dc_res = run_guarded_ssh("bash %s/run_datacheck.sh %s" % (REMOTE_RUN_DIR, role), timeout=180)
        print("    Output: %s" % dc_res.strip())
        if "AUTHENTIC_DATACHECK_PASS" not in dc_res:
            raise RuntimeError("Datacheck failed for %s: %s" % (role, dc_res))

    print("Step 7: Validating datacheck outputs...")
    check_dc_script = """
import hashlib, json, sys
from pathlib import Path

run_dir = Path(%r)
results = {}
for name in ["P150_MECHANICAL_DC", "P150_PHASE_DC"]:
    dat_path = run_dir / (name + ".dat")
    if not dat_path.exists():
        print("DAT_MISSING: " + name)
        sys.exit(1)
    dat = dat_path.read_text()
    if "***ERROR" in dat or "***FATAL" in dat:
        print("DAT_ERROR: " + name)
        sys.exit(2)
    if "ANALYSIS DATACHECK COMPLETE" not in dat:
        print("DAT_INCOMPLETE: " + name)
        sys.exit(3)
    results[name + ".dat"] = hashlib.sha256(dat_path.read_bytes()).hexdigest()

print(json.dumps({"status": "PASS", "datachecks": results}))
""" % REMOTE_RUN_DIR

    encoded = check_dc_script.encode().hex()
    res = run_guarded_ssh("python3 -c exec\\(bytes.fromhex\\(\\'" + encoded + "\\'\\)\\)")
    print("Datacheck verification result:", res.strip())
    proof = json.loads(res.strip())
    assert proof["status"] == "PASS"

    # Save local proof
    proof_path = REPO_ROOT / "results/validation/package150_c1_2_datachecks.json"
    proof_path.write_text(json.dumps(proof, indent=2) + "\n")
    print("Datacheck proof recorded at:", proof_path)
    return proof


if __name__ == "__main__":
    stage_package()
