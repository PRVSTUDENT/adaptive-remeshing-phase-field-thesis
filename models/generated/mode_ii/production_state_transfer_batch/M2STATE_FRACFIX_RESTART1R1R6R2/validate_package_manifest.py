#!/usr/bin/env python3
"""
Standalone Package Manifest Validator for Production Candidate M2STATE_FRACFIX_RESTART1R1R6R2.
Eliminates all inline-Python shell-quoting vulnerabilities.
"""

import sys
import json
import hashlib
import re
from pathlib import Path

REQUIRED_FILES = [
    "M2STATE_FRACFIX_RESTART1R1R6R2.inp",
    "f42_mixed_uel.for",
    "STATE_TRANSFER_ARTIFACT.json",
    "TRANSFER_MANIFEST.json",
    "RESTART_ACCEPTANCE_CONTRACT.json",
    "verify_restart_trace.py",
    "extract_restart1r1r6_odb.py",
    "verify_restart1r1r6_science.py",
    "job_notifications.sh",
    "validate_package_manifest.py",
    "M2STATE_FRACFIX_RESTART1R1R6R2.pbs",
    "submit_m2state_fracfix_restart1r1r6r2.sh"
]

def validate_manifest(manifest_path_str: str = "PACKAGE_MANIFEST.json") -> bool:
    manifest_path = Path(manifest_path_str)
    if not manifest_path.exists():
        print(f"[PREFLIGHT] ERROR: Manifest not found: {manifest_path}")
        return False

    try:
        m = json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"[PREFLIGHT] ERROR: Failed to parse JSON manifest: {e}")
        return False

    if not isinstance(m, dict):
        print("[PREFLIGHT] ERROR: Manifest root is not a dictionary")
        return False

    if "files" not in m:
        print("[PREFLIGHT] ERROR: Canonical 'files' key missing from manifest")
        return False

    files_dict = m["files"]
    if not isinstance(files_dict, dict) or len(files_dict) == 0:
        print("[PREFLIGHT] ERROR: 'files' mapping is invalid or empty")
        return False

    for rf in REQUIRED_FILES:
        if rf not in files_dict:
            print(f"[PREFLIGHT] ERROR: Required execution file missing from manifest: {rf}")
            return False

    hex_re = re.compile(r"^[0-9a-fA-F]{64}$")
    for f_name, exp_hash in files_dict.items():
        if not isinstance(exp_hash, str) or not hex_re.match(exp_hash):
            print(f"[PREFLIGHT] ERROR: Invalid SHA256 format for {f_name}: {exp_hash}")
            return False
        f_path = manifest_path.parent / f_name if manifest_path.is_file() else Path(f_name)
        if not f_path.exists():
            print(f"[PREFLIGHT] ERROR: Required candidate file missing on disk: {f_name}")
            return False
        actual_hash = hashlib.sha256(f_path.read_bytes()).hexdigest()
        if actual_hash.lower() != exp_hash.lower():
            print(f"[PREFLIGHT] ERROR: Hash mismatch for {f_name}: expected {exp_hash}, got {actual_hash}")
            return False

    print("[PREFLIGHT] package_manifest_verification = PASS")
    return True

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "PACKAGE_MANIFEST.json"
    if not validate_manifest(target):
        sys.exit(1)
    sys.exit(0)
