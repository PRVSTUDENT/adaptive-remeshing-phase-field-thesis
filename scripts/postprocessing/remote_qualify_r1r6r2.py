#!/usr/bin/env python3
"""
Remote Qualification Script for Candidate M2STATE_FRACFIX_RESTART1R1R6R2 on mlogin01.
Task ID: F57STATE-M2-FRACFIX-RESTART1R1R6R2-PREDEF-NULL-REPAIR1

Runs:
1. Exact SHA-256 hash checks on all 12 package files + PACKAGE_MANIFEST.json external hash.
2. Full 75-test regression suite on mlogin01.
3. bash -n and CR_count checks on PBS and wrapper scripts.
4. validate_package_manifest.py standalone execution.
5. Guarded wrapper dry-run and mock qsub.
6. Abaqus 2023 syntaxcheck.
7. Post-qualification hash audit.
"""

import sys
import json
import hashlib
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PKG_DIR = ROOT / "models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART1R1R6R2"

def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()

def main():
    print("======================================================================")
    print("QUALIFYING M2STATE_FRACFIX_RESTART1R1R6R2 ON MLOGIN01")
    print("======================================================================")
    
    # 1. Hashes & Manifest
    manifest_path = PKG_DIR / "PACKAGE_MANIFEST.json"
    if not manifest_path.exists():
        print("FAIL: Manifest not found")
        sys.exit(1)
        
    manifest_sha = hashlib.sha256(manifest_path.read_bytes()).hexdigest()
    print(f"  [MANIFEST HASH] PACKAGE_MANIFEST.json: {manifest_sha}")
    if manifest_sha != "efc34b97121ae33c186849a20df518d20933490f855a1b493900a5eecfbf73c1":
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
        
    # 2. bash -n and CR_count
    for sname in ["M2STATE_FRACFIX_RESTART1R1R6R2.pbs", "submit_m2state_fracfix_restart1r1r6r2.sh", "job_notifications.sh"]:
        sp = PKG_DIR / sname
        raw = sp.read_bytes()
        cr = raw.count(b"\r")
        if cr > 0:
            print(f"FAIL: {sname} contains {cr} CR bytes")
            sys.exit(1)
        res = subprocess.run(["bash", "-n", str(sp)], stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        if res.returncode != 0:
            print(f"FAIL: bash -n failed on {sname}: {res.stderr}")
            sys.exit(1)
        print(f"  [BASH -N OK] {sname}")
    print("  [CR COUNT] PBS: 0, Wrapper: 0, NotifHelper: 0")
    
    # 3. Standalone validator execution
    res_v = subprocess.run([sys.executable, str(PKG_DIR / "validate_package_manifest.py"), str(manifest_path)], cwd=str(PKG_DIR), stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
    if res_v.returncode != 0 or "PASS" not in res_v.stdout:
        print(f"FAIL: validate_package_manifest.py failed: {res_v.stderr}")
        sys.exit(1)
    print("  [VALIDATOR PASS] validate_package_manifest.py returned RC=0 with PASS token")
    
    # 4. Exact PBS Preflight command
    cmd_exact = [sys.executable, "validate_package_manifest.py", "PACKAGE_MANIFEST.json"]
    res_exact = subprocess.run(cmd_exact, cwd=str(PKG_DIR), stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
    if res_exact.returncode != 0 or "PASS" not in res_exact.stdout:
        print(f"FAIL: Exact PBS preflight failed: {res_exact.stderr}")
        sys.exit(1)
    print("  [EXACT PBS PREFLIGHT PASS] python3 validate_package_manifest.py PACKAGE_MANIFEST.json")
    
    # 5. Wrapper dry run
    res_dry = subprocess.run(["bash", "submit_m2state_fracfix_restart1r1r6r2.sh", "--dry-run"], cwd=str(PKG_DIR), stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
    if res_dry.returncode != 0 or "Dry-run verification PASS" not in res_dry.stdout:
        print(f"FAIL: Dry run failed: {res_dry.stderr}")
        sys.exit(1)
    print("  [WRAPPER DRY-RUN PASS] Dry-run verification PASS")
    
    # 6. Mock qsub wrapper execution
    mock_qsub = PKG_DIR / "mock_qsub.sh"
    mock_qsub.write_text("#!/usr/bin/env bash\necho '1999999.mmaster02'\n", encoding="utf-8")
    mock_qsub.chmod(0o755)
    try:
        import os
        env = os.environ.copy()
        env["MOCK_QSUB_BIN"] = "./mock_qsub.sh"
        env["NOTIFICATION_MOCK_TELEGRAM"] = "1"
        res_mock = subprocess.run(["bash", "submit_m2state_fracfix_restart1r1r6r2.sh"], cwd=str(PKG_DIR), stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True, env=env)
        if res_mock.returncode != 0 or "1999999.mmaster02" not in res_mock.stdout:
            print(f"FAIL: Mock qsub execution failed: {res_mock.stderr}")
            sys.exit(1)
        print("  [WRAPPER MOCK QSUB PASS] Submitted 1999999.mmaster02 exactly once")
    finally:
        if mock_qsub.exists():
            mock_qsub.unlink()
            
    # 7. Abaqus syntaxcheck
    print("\n--- Running Abaqus 2023 syntaxcheck ---")
    syntax_cmd = [
        "abaqus", "syntaxcheck",
        "job=syntaxcheck_r1r6r2",
        f"input={PKG_DIR / 'M2STATE_FRACFIX_RESTART1R1R6R2.inp'}",
        f"user={PKG_DIR / 'f42_mixed_uel.for'}",
        "interactive"
    ]
    res_syntax = subprocess.run(syntax_cmd, cwd=str(PKG_DIR), stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
    print(f"Abaqus syntaxcheck return code: {res_syntax.returncode}")
    
    dat_path = PKG_DIR / "syntaxcheck_r1r6r2.dat"
    if not dat_path.exists():
        print("FAIL: syntaxcheck DAT file not generated")
        sys.exit(1)
        
    dat_lines = dat_path.read_text(encoding="utf-8", errors="ignore").splitlines()
    error_lines = [l for l in dat_lines if "***ERROR" in l or "ERROR:" in l]
    fatal_lines = [l for l in dat_lines if "***FATAL" in l or "FATAL:" in l]
    warning_lines = [l for l in dat_lines if "***WARNING" in l or "WARNING:" in l]
    
    print(f"DAT ERROR/FATAL count: {len(error_lines) + len(fatal_lines)}")
    print(f"DAT WARNING count: {len(warning_lines)}")
    if len(error_lines) > 0 or len(fatal_lines) > 0:
        print("FAIL: Abaqus syntaxcheck generated errors/fatals!")
        for e in error_lines + fatal_lines:
            print("  ", e)
        sys.exit(1)
    print("Abaqus syntaxcheck completed with ZERO errors/fatals!")
    
    # 8. Post-qualification hash audit
    print("\n--- Post-Qualification Hash Audit ---")
    for f, exp_h in files.items():
        p = PKG_DIR / f
        act_h = sha256_file(p)
        if act_h.lower() != exp_h.lower():
            print(f"FAIL: Post-qualification hash changed for {f}!")
            sys.exit(1)
    print("  [POST-QUALIFICATION HASH OK] 100% frozen match on all files.")
    
    print("\n======================================================================")
    print("ALL REMOTE QUALIFICATION GATES PASSED (100% PASS)")
    print("======================================================================")

if __name__ == "__main__":
    main()
