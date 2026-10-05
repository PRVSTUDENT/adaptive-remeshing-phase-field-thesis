#!/usr/bin/env python3
import sys, json, hashlib
from pathlib import Path

def main():
    pkg_dir = Path(__file__).resolve().parent
    manifest_path = pkg_dir / "PACKAGE_MANIFEST.json"
    if not manifest_path.exists():
        print("FAIL: PACKAGE_MANIFEST.json not found")
        sys.exit(1)
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)
    all_ok = True
    for rel_path, expected_hash in manifest.get("file_hashes", {}).items():
        file_path = pkg_dir / rel_path
        if not file_path.exists():
            print(f"FAIL: Missing file {rel_path}")
            all_ok = False
            continue
        actual_hash = hashlib.sha256(file_path.read_bytes()).hexdigest()
        if actual_hash != expected_hash:
            print(f"FAIL: Hash mismatch for {rel_path}")
            all_ok = False
    if all_ok:
        print("MANIFEST_VALIDATION_PASS")
        sys.exit(0)
    else:
        print("MANIFEST_VALIDATION_FAIL")
        sys.exit(1)

if __name__ == "__main__":
    main()
