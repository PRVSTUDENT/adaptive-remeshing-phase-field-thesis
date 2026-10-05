#!/usr/bin/env python3
import json
import hashlib
import sys
from pathlib import Path

def main():
    pkg_dir = Path(__file__).resolve().parent
    manifest_file = pkg_dir / "PACKAGE_MANIFEST.json"
    if not manifest_file.exists():
        print(f"[ERROR] Manifest not found: {manifest_file}")
        sys.exit(1)

    manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
    file_hashes = manifest.get("file_hashes", {})

    all_pass = True
    for rel_path, expected_sha in file_hashes.items():
        fp = pkg_dir / rel_path
        if not fp.exists():
            print(f"[FAIL] Missing file: {rel_path}")
            all_pass = False
            continue
        actual_sha = hashlib.sha256(fp.read_bytes()).hexdigest()
        if actual_sha != expected_sha:
            print(f"[FAIL] SHA mismatch for {rel_path}: actual={actual_sha} expected={expected_sha}")
            all_pass = False

    if all_pass:
        print("[PREFLIGHT] package_manifest_verification = PASS")
        sys.exit(0)
    else:
        print("[PREFLIGHT] package_manifest_verification = FAIL")
        sys.exit(1)

if __name__ == "__main__":
    main()
