#!/usr/bin/env python3
"""
Remote Qualification Runner for Mode-II Control Batch:
- PK10R1_CONTINUOUS_U050
- PK10R1_IDENTITY_RESTART_U050
"""

import os
import sys
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
SSH_KEY = "C:/Users/pruth/.ssh/tu_freiberg_codex"
SSH_HOST = "pr21vyci@mlogin01.hrz.tu-freiberg.de"
REMOTE_BASE = "projects/adaptive-remeshing/models/generated/mode_ii/production_control_batch"
LOCAL_BASE = ROOT / "models/generated/mode_ii/production_control_batch"

JOBS = [
    "PK10R1_CONTINUOUS_U050",
    "PK10R1_IDENTITY_RESTART_U050"
]

def run_ssh(cmd, timeout=300):
    full_cmd = ["ssh", "-i", SSH_KEY, SSH_HOST, cmd]
    return subprocess.run(full_cmd, stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=timeout)

def upload_package(job_name):
    local_pkg = LOCAL_BASE / job_name
    remote_pkg = f"{REMOTE_BASE}/{job_name}"
    print(f"\nUploading {job_name} to cluster...")
    run_ssh(f"mkdir -p {remote_pkg}", timeout=30)
    
    for f in local_pkg.glob("*"):
        if f.is_file():
            scp_cmd = ["scp", "-i", SSH_KEY, str(f), f"{SSH_HOST}:{remote_pkg}/{f.name}"]
            res = subprocess.run(scp_cmd, stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=60)
            if res.returncode != 0:
                print(f"Failed to upload {f.name}: {res.stderr}")
                return False
    # Make executable
    wrapper_name = f"submit_{job_name.lower()}.sh"
    run_ssh(f"chmod +x {remote_pkg}/{wrapper_name} {remote_pkg}/validate_package_manifest.py", timeout=30)
    return True



def qualify_package(job_name):
    remote_pkg = f"{REMOTE_BASE}/{job_name}"
    print(f"\n--- Qualifying {job_name} on cluster ---")

    # 1. Validate manifest
    print("1. Validating package manifest...")
    res = run_ssh(f"cd {remote_pkg} && python3 validate_package_manifest.py")
    print(res.stdout.strip())
    if "MANIFEST_VALIDATION_PASS" not in res.stdout:
        print(f"Manifest validation failed: {res.stderr}")
        return False

    # 2. Dry run wrapper
    print("2. Testing guarded wrapper in dry-run mode...")
    wrapper_name = f"submit_{job_name.lower()}.sh"
    res = run_ssh(f"cd {remote_pkg} && ./{wrapper_name} --dry-run")
    print(res.stdout.strip())
    if "DRY_RUN_PASS" not in res.stdout:
        print(f"Dry run failed: {res.stderr}")
        return False

    # 3. Run Abaqus Datacheck
    print("3. Executing Abaqus 2023 Datacheck...")
    datacheck_job = f"{job_name}_DATACHECK"
    dc_cmd = (
        "export PATH=/cluster/stages/2024.0/software/intel/2024.2/compiler/2024.2/bin:/cluster/stages/2024.0/software/gcc/11.4.0/bin:/cluster/application/abaqus/2023/Commands:$PATH; "
        f"cd {remote_pkg} && "
        f"rm -f {datacheck_job}.* || true && "
        f"abaqus job={datacheck_job} input={job_name}.inp user=f42_mixed_uel.for datacheck double=both interactive cpus=1"
    )
    res = run_ssh(dc_cmd, timeout=300)




    print(f"Datacheck RC: {res.returncode}")
    print(f"Datacheck output:\n{res.stdout[-400:] if len(res.stdout) > 400 else res.stdout}")
    print(f"Datacheck stderr:\n{res.stderr[-400:] if len(res.stderr) > 400 else res.stderr}")

    # 4. Check Datacheck status / log
    res_tail = run_ssh(f"cd {remote_pkg} && tail -n 25 {datacheck_job}.dat {datacheck_job}.msg 2>/dev/null || true")
    print(f"Datacheck tail:\n{res_tail.stdout}")
    if res.returncode == 0 or "COMPLETED" in res.stdout or "THE ANALYSIS HAS COMPLETED SUCCESSFULLY" in res_tail.stdout or "CHECKPOINT: DATA CHECK COMPLETE" in res_tail.stdout:
        print(f"DATACHECK_PASS for {job_name}")
        return True

    else:
        print(f"Datacheck failed for {job_name}")
        return False


def main():
    print("================================================================================")
    print("REMOTE QUALIFICATION FOR MODE-II CONTROL BATCH")
    print("================================================================================")

    for job in JOBS:
        if not upload_package(job):
            print(f"ABORT: Upload failed for {job}")
            sys.exit(1)
        if not qualify_package(job):
            print(f"ABORT: Qualification failed for {job}")
            sys.exit(1)

    print("\n================================================================================")
    print("ALL 2 CONTROL BATCH PACKAGES FULLY QUALIFIED AND READY FOR AUTHORIZED SUBMISSION")
    print("================================================================================")

if __name__ == '__main__':
    main()
