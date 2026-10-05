#!/usr/bin/env python3
import json, hashlib, sys
from pathlib import Path

def sha256_file(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for chunk in iter(lambda: f.read(65536), b''):
            h.update(chunk)
    return h.hexdigest()

def main():
    mpath = Path("PACKAGE_MANIFEST.json")
    if not mpath.exists():
        print("ERROR: PACKAGE_MANIFEST.json missing")
        sys.exit(1)
    with open(mpath) as f:
        m = json.load(f)
    for fname, expected_hash in m.get("files", {}).items():
        p = Path(fname)
        if not p.exists():
            print(f"ERROR: missing file {fname}")
            sys.exit(1)
        actual = sha256_file(p)
        if actual != expected_hash:
            print(f"ERROR: hash mismatch for {fname}: expected {expected_hash}, got {actual}")
            sys.exit(1)
    print("ALL_MANIFEST_FILES_VERIFIED_PASS")

if __name__ == '__main__':
    main()
