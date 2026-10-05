#!/usr/bin/env python3
import json
import hashlib
from pathlib import Path

def sha256_file(filepath):
    h = hashlib.sha256()
    with open(filepath, 'rb') as f:
        while True:
            chunk = f.read(8192)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()

def main():
    root = Path(__file__).resolve().parent
    manifest = json.loads((root / "PACKAGE_MANIFEST.json").read_text(encoding="utf-8"))
    for rel_fn, exp_hash in manifest["file_hashes"].items():
        fp = root / rel_fn
        if not fp.exists():
            print(f"FAIL: Missing file {rel_fn}")
            return 1
        act_hash = sha256_file(fp)
        if act_hash.lower() != exp_hash.lower():
            print(f"FAIL: Hash mismatch for {rel_fn}: expected {exp_hash}, got {act_hash}")
            return 1
    print("ALL FILES MATCH MANIFEST SHA256: PASS")
    return 0

if __name__ == '__main__':
    exit(main())
