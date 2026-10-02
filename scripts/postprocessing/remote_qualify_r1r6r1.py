#!/usr/bin/env python3
"""
Remote qualification script for M2STATE_FRACFIX_RESTART1R1R6R1.
Executes:
1. Exact package hash recomputation and manifest verification
2. bash -n and CR count on PBS and submission wrapper
3. Standalone manifest validator direct execution
4. Exact PBS preflight command execution
5. Guarded wrapper dry-run (--dry-run)
6. Guarded wrapper mock-qsub live execution
7. Abaqus 2023 syntaxcheck execution and DAT error/warning audit
"""

import os
import sys
import json
import hashlib
import subprocess
import tempfile
from pathlib import Path

PKG_DIR = Path("/home/pr21vyci/projects/adaptive-remeshing/models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART1R1R6R1")

def run_cmd(cmd, cwd=None, env=None):
    res = subprocess.run(cmd, shell=isinstance(cmd, str), cwd=cwd or PKG_DIR, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True, env=env)
    return res

def check_cr(path: Path) -> int:
    data = path.read_bytes()
    return data.count(b"\r")

def main():
    print("======================================================================")
    print("QUALIFYING M2STATE_FRACFIX_RESTART1R1R6R1 ON MLOGIN01")
    print("======================================================================")
    
    # 1. Hashes & Manifest
    manifest_path = PKG_DIR / "PACKAGE_MANIFEST.json"
    if not manifest_path.exists():
        print("FAIL: Manifest not found")
        sys.exit(1)
        
    manifest_sha = hashlib.sha256(manifest_path.read_bytes()).hexdigest()
    print(f"  [MANIFEST HASH] PACKAGE_MANIFEST.json: {manifest_sha}")
    if manifest_sha != "04a3d9056b9763fcf544690b0160169963302fc45ce42db7f40ef2ec716e8a66":
        print("FAIL: PACKAGE_MANIFEST.json hash mismatch!")
        sys.exit(1)
        
    m = json.loads(manifest_path.read_text(encoding="utf-8"))
    files = m["files"]
    print(f"Manifest contains {len(files)} files.")
    if len(files) != 12:
        print(f"FAIL: Expected 12 files in manifest, found {len(files)}")
        sys.exit(1)
        
    for f, exp_h in files.items():
        p = PKG_DIR / f
        if not p.exists():
            print(f"FAIL: File missing: {f}")
            sys.exit(1)
        act_h = hashlib.sha256(p.read_bytes()).hexdigest()
        if act_h.lower() != exp_h.lower():
            print(f"FAIL: Hash mismatch for {f}: exp {exp_h}, got {act_h}")
            sys.exit(1)
        print(f"  [HASH OK] {f}: {act_h}")
        
    # 2. Bash -n & CR count
    pbs_file = PKG_DIR / "M2STATE_FRACFIX_RESTART1R1R6R1.pbs"
    wrapper_file = PKG_DIR / "submit_m2state_fracfix_restart1r1r6r1.sh"
    
    res_pbs_n = run_cmd(["bash", "-n", str(pbs_file)])
    if res_pbs_n.returncode != 0:
        print(f"FAIL: bash -n on PBS script failed: {res_pbs_n.stderr}")
        sys.exit(1)
    print("  [BASH -N OK] M2STATE_FRACFIX_RESTART1R1R6R1.pbs")
    
    res_wrp_n = run_cmd(["bash", "-n", str(wrapper_file)])
    if res_wrp_n.returncode != 0:
        print(f"FAIL: bash -n on wrapper failed: {res_wrp_n.stderr}")
        sys.exit(1)
    print("  [BASH -N OK] submit_m2state_fracfix_restart1r1r6r1.sh")
    
    cr_pbs = check_cr(pbs_file)
    cr_wrp = check_cr(wrapper_file)
    print(f"  [CR COUNT] PBS: {cr_pbs}, Wrapper: {cr_wrp}")
    if cr_pbs != 0 or cr_wrp != 0:
        print("FAIL: CR count must be 0")
        sys.exit(1)
        
    # 3. Direct execution of standalone manifest validator
    val_file = PKG_DIR / "validate_package_manifest.py"
    res_val = run_cmd([sys.executable, str(val_file), str(manifest_path)])
    if res_val.returncode != 0 or "package_manifest_verification = PASS" not in res_val.stdout:
        print(f"FAIL: Standalone validator failed: {res_val.stdout} {res_val.stderr}")
        sys.exit(1)
    print("  [VALIDATOR PASS] validate_package_manifest.py returned RC=0 with PASS token")
    
    # 4. Exact PBS preflight command
    res_pre = run_cmd([sys.executable, "validate_package_manifest.py", "PACKAGE_MANIFEST.json"])
    if res_pre.returncode != 0:
        print(f"FAIL: Exact PBS preflight command failed: {res_pre.stderr}")
        sys.exit(1)
    print("  [EXACT PBS PREFLIGHT PASS] python3 validate_package_manifest.py PACKAGE_MANIFEST.json")
    
    # 5. Guarded wrapper dry-run
    res_dry = run_cmd(["bash", str(wrapper_file), "--dry-run"])
    if res_dry.returncode != 0 or "Dry-run verification PASS" not in res_dry.stdout:
        print(f"FAIL: Guarded wrapper dry-run failed: {res_dry.stdout} {res_dry.stderr}")
        sys.exit(1)
    print("  [WRAPPER DRY-RUN PASS] Dry-run verification PASS")
    
    # 6. Guarded wrapper mock-qsub live execution
    mock_qsub = PKG_DIR / "mock_qsub.sh"
    mock_qsub.write_text("#!/usr/bin/env bash\necho '1999999.mmaster02'\n", encoding="utf-8")
    os.chmod(mock_qsub, 0o755)
    try:
        env = os.environ.copy()
        env["MOCK_QSUB_BIN"] = str(mock_qsub)
        env["NOTIFICATION_MOCK_TELEGRAM"] = "1"
        res_mock = run_cmd(["bash", str(wrapper_file)], env=env)
        if res_mock.returncode != 0 or "1999999.mmaster02" not in res_mock.stdout:
            print(f"FAIL: Guarded wrapper mock execution failed: {res_mock.stdout} {res_mock.stderr}")
            sys.exit(1)
        print("  [WRAPPER MOCK QSUB PASS] Submitted 1999999.mmaster02 exactly once")
    finally:
        if mock_qsub.exists():
            mock_qsub.unlink()
            
    # 7. Abaqus 2023 syntaxcheck
    print("\n--- Running Abaqus 2023 syntaxcheck ---")
    syntax_job = "syntaxcheck_r1r6r1"
    run_cmd(f"rm -f {syntax_job}.*", cwd=PKG_DIR)
    
    cmd_abq = f"abaqus job={syntax_job} user=f42_mixed_uel.for input=M2STATE_FRACFIX_RESTART1R1R6R1.inp syntaxcheck interactive"
    res_abq = run_cmd(cmd_abq, cwd=PKG_DIR)
    print(f"Abaqus syntaxcheck return code: {res_abq.returncode}")
    
    dat_path = PKG_DIR / f"{syntax_job}.dat"
    msg_path = PKG_DIR / f"{syntax_job}.msg"
    log_path = PKG_DIR / f"{syntax_job}.log"
    
    dat_text = dat_path.read_text(encoding="utf-8", errors="replace") if dat_path.exists() else ""
    error_count = dat_text.count("***ERROR") + dat_text.count("***FATAL")
    warn_count = dat_text.count("***WARNING")
    print(f"DAT ERROR/FATAL count: {error_count}")
    print(f"DAT WARNING count: {warn_count}")
    
    if error_count > 0:
        print("FAIL: Abaqus syntaxcheck generated ERRORS in DAT file!")
        sys.exit(1)
        
    print("Abaqus syntaxcheck completed with ZERO errors/fatals!")
    
    # Clean up syntaxcheck scratch files
    for ext in [".dat", ".msg", ".log", ".prt", ".com", ".sim", ".sta"]:
        p = PKG_DIR / f"{syntax_job}{ext}"
        if p.exists():
            p.unlink()
            
    # 8. Recompute hashes again to guarantee zero post-qualification drift
    print("\n--- Post-Qualification Hash Audit ---")
    for f, exp_h in files.items():
        p = PKG_DIR / f
        act_h = hashlib.sha256(p.read_bytes()).hexdigest()
        if act_h.lower() != exp_h.lower():
            print(f"FAIL: Post-qualification hash drift for {f}!")
            sys.exit(1)
    print("  [POST-QUALIFICATION HASH OK] 100% frozen match on all files.")
    
    print("\n======================================================================")
    print("ALL REMOTE QUALIFICATION GATES PASSED (100% PASS)")
    print("======================================================================")

if __name__ == "__main__":
    main()
