# -*- coding: utf-8 -*-
"""
stage_package150_r1.py
Stages Package 150 R1 to cluster scratch directory, executes authentic Abaqus 2023 datachecks,
verifies remote SHA-256 hashes, and records local datacheck proof.
"""

import os
import sys
import json
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PKG_DIR = REPO_ROOT / "models/pandey_kumar_mode1/151_c4_package150_c1_2_continuation_r1"
SSH_CONFIG = Path.home() / ".ssh/codex_config"
REMOTE_RUN_DIR = "/scratch9/pr21vyci/runs/mode1_c4_package150_c1_2_continuation_r1"
REMOTE_P150_DIR = "/scratch9/pr21vyci/runs/mode1_c4_package150_c1_2_continuation"
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
    cmd = (
        "mkdir -p %s/runtime/scripts/state_transfer "
        "%s/runtime/scripts/validation "
        "%s/runtime/models/pandey_kumar_mode1/147_c4_corrected_reference "
        "%s/runtime/results/validation/package148"
    ) % ((REMOTE_RUN_DIR,) * 4)
    run_guarded_ssh(cmd)

    print("Step 2: Copying reusable files from Package 150 / R8 directory...")
    copy_cmd = (
        "cp -p %s/f42_mixed_uel.for %s/ && "
        "cp -p %s/nodal_displacements_initial.csv %s/ && "
        "cp -p %s/nodal_phase_field_initial.csv %s/ && "
        "cp -p %s/d_lower_bounds.csv %s/ && "
        "cp -p %s/active_set_boundary_cards.inc %s/ && "
        "cp -p %s/initial_conditions_solution.inc %s/ && "
        "cp -p %s/M1_C4_PACKAGE150_C1_2_CONTINUATION.inp %s/ && "
        "cp -p %s/P150_MECHANICAL_DC.inp %s/ && "
        "cp -p %s/P150_PHASE_DC.inp %s/ && "
        "cp -p %s/job_notifications.sh %s/ && "
        "cp -rp %s/runtime/* %s/runtime/ 2>/dev/null || true"
    ) % (
        REMOTE_P150_DIR, REMOTE_RUN_DIR,
        REMOTE_P150_DIR, REMOTE_RUN_DIR,
        REMOTE_P150_DIR, REMOTE_RUN_DIR,
        REMOTE_P150_DIR, REMOTE_RUN_DIR,
        REMOTE_P150_DIR, REMOTE_RUN_DIR,
        REMOTE_P150_DIR, REMOTE_RUN_DIR,
        REMOTE_P150_DIR, REMOTE_RUN_DIR,
        REMOTE_P150_DIR, REMOTE_RUN_DIR,
        REMOTE_P150_DIR, REMOTE_RUN_DIR,
        REMOTE_P150_DIR, REMOTE_RUN_DIR,
        REMOTE_P150_DIR, REMOTE_RUN_DIR
    )
    run_guarded_ssh(copy_cmd)

    print("Step 3: Uploading unique/updated Package 150 R1 files via SCP...")
    upload_files = [
        ("run_datacheck.sh", "%s/run_datacheck.sh" % REMOTE_RUN_DIR),
        ("submit_M1_C4_P150_C1_2_R1.pbs", "%s/submit_M1_C4_P150_C1_2_R1.pbs" % REMOTE_RUN_DIR),
        ("EXECUTION_MANIFEST.json", "%s/EXECUTION_MANIFEST.json" % REMOTE_RUN_DIR),
        ("PACKAGE_MANIFEST.json", "%s/PACKAGE_MANIFEST.json" % REMOTE_RUN_DIR),
    ]
    for local_name, remote_dest in upload_files:
        print("  Uploading %s -> %s" % (local_name, remote_dest))
        scp_file(PKG_DIR / local_name, remote_dest)

    # Upload repaired extractor to runtime
    repaired_extractor = REPO_ROOT / "scripts/validation/extract_package148_iteration.py"
    print("  Uploading repaired extractor -> %s/runtime/scripts/validation/extract_package148_iteration.py" % REMOTE_RUN_DIR)
    scp_file(repaired_extractor, "%s/runtime/scripts/validation/extract_package148_iteration.py" % REMOTE_RUN_DIR)

    # Upload driver to runtime
    driver_path = REPO_ROOT / "scripts/state_transfer/driver_package150_c1_2_continuation.py"
    scp_file(driver_path, "%s/runtime/scripts/state_transfer/driver_package150_c1_2_continuation.py" % REMOTE_RUN_DIR)

    # Upload predecessor checkpoint to runtime
    ckpt_path = REPO_ROOT / "results/validation/package148/r8_equilibrium_checkpoint.json"
    scp_file(ckpt_path, "%s/runtime/results/validation/package148/r8_equilibrium_checkpoint.json" % REMOTE_RUN_DIR)

    print("Step 4: Setting permissions...")
    perm_cmd = "chmod 755 %s/*.sh %s/*.pbs" % (REMOTE_RUN_DIR, REMOTE_RUN_DIR)
    run_guarded_ssh(perm_cmd)

    print("Step 5: Verifying remote SHA-256 hashes against EXECUTION_MANIFEST.json...")
    manifest = json.loads((PKG_DIR / "EXECUTION_MANIFEST.json").read_text())
    verify_script = """
import hashlib, json, sys
from pathlib import Path

run_dir = Path(%r)
manifest = json.loads((run_dir / "EXECUTION_MANIFEST.json").read_text())
failures = []

for name, expected in manifest["files"].items():
    p = run_dir / name
    if not p.is_file():
        failures.append("MISSING_FILE: " + name)
        continue
    h = hashlib.sha256(p.read_bytes()).hexdigest().lower()
    if h != expected.lower():
        failures.append("HASH_MISMATCH: " + name + " (got " + h + ", expected " + expected + ")")

for name, expected in manifest.get("runtime_source_hashes", {}).items():
    p = run_dir / "runtime" / name
    if not p.is_file():
        failures.append("MISSING_RUNTIME: " + name)
        continue
    h = hashlib.sha256(p.read_bytes()).hexdigest().upper()
    if h != expected.upper():
        failures.append("RUNTIME_HASH_MISMATCH: " + name + " (got " + h + ", expected " + expected + ")")

if failures:
    print("VERIFICATION_FAIL: " + "; ".join(failures))
    sys.exit(1)
else:
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
    proof = json.loads([l for l in res.splitlines() if not l.startswith("**") and l.strip().startswith("{")][0])
    assert proof["status"] == "PASS"

    # Save local proof
    proof_path = REPO_ROOT / "results/validation/package150_r1_datachecks.json"
    proof_path.write_text(json.dumps(proof, indent=2) + "\n")
    print("Datacheck proof recorded at:", proof_path)
    return proof


if __name__ == "__main__":
    stage_package()
