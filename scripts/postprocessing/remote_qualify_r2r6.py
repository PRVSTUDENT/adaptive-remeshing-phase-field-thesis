#!/usr/bin/env python3
"""
Remote qualification driver for M2STATE_FRACFIX_RESTART2R6 on tu_freiberg.
"""
import subprocess
import sys
from pathlib import Path

def run_cmd(cmd, cwd=None):
    print(f"--- RUNNING: {cmd} (cwd={cwd}) ---")
    res = subprocess.run(cmd, shell=True, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
    print(res.stdout)
    if res.returncode != 0:
        print(f"FAILED with returncode {res.returncode}")
        sys.exit(res.returncode)
    return res.stdout

def qualify_r2r6():
    pkg_dir = Path("/home/pr21vyci/projects/adaptive-remeshing/models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART2R6")
    
    # 1. Manifest Validation
    print("=== STEP 1: MANIFEST VALIDATION ===")
    run_cmd("python3 validate_package_manifest.py", cwd=pkg_dir)
    
    # 2. Guarded Wrapper Dry-Run
    print("\n=== STEP 2: GUARDED WRAPPER DRY RUN ===")
    run_cmd("./submit_m2state_fracfix_restart2r6.sh --dry-run", cwd=pkg_dir)
    
    # 3. Unit Tests
    print("\n=== STEP 3: UNIT TESTS ===")
    run_cmd("python3 -m unittest /home/pr21vyci/projects/adaptive-remeshing/tests/unit/test_m2state_fracfix_restart2r6.py")
    
    # 4. Abaqus Syntaxcheck / Datacheck with Subroutine
    print("\n=== STEP 4: ABAQUS DATACHECK AND COMPILATION ===")
    abaqus_cmd = (
        "source /etc/profile.d/modules.sh 2>/dev/null || source /etc/profile 2>/dev/null || true; "
        "module purge; "
        "module load gcc/11.4.0 intel/2024.2.0 abaqus/2023 python/gcc/11.4.0/3.11.7; "
        "rm -f M2STATE_FRACFIX_RESTART2R6.odb M2STATE_FRACFIX_RESTART2R6.dat M2STATE_FRACFIX_RESTART2R6.msg M2STATE_FRACFIX_RESTART2R6.sta M2STATE_FRACFIX_RESTART2R6.com M2STATE_FRACFIX_RESTART2R6.prt; "
        "abaqus job=M2STATE_FRACFIX_RESTART2R6 user=f42_mixed_uel.for datacheck interactive"
    )
    run_cmd(abaqus_cmd, cwd=pkg_dir)
    
    # 5. Check .dat and .msg for errors
    print("\n=== STEP 5: VERIFY DATACHECK OUTPUT LOGS ===")
    dat_path = pkg_dir / "M2STATE_FRACFIX_RESTART2R6.dat"
    with open(dat_path, "r", errors="ignore") as f:
        dat_text = f.read()
    if "FATAL" in dat_text or "***ERROR" in dat_text:
        print("ERROR: Datacheck reported FATAL or ERROR messages:")
        for line in dat_text.splitlines():
            if "FATAL" in line or "***ERROR" in line:
                print("  ", line)
        sys.exit(1)
    else:
        print("Abaqus datacheck passed with ZERO ERRORS and ZERO FATALS!")

if __name__ == "__main__":
    qualify_r2r6()
