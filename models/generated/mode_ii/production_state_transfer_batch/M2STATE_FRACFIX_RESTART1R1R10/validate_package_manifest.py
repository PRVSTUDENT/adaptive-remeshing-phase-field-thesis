#!/usr/bin/env python3
import json
import hashlib
from pathlib import Path

def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()

def main():
    pkg_dir = Path(__file__).resolve().parent
    manifest_path = pkg_dir / "PACKAGE_MANIFEST.json"
    with open(manifest_path, "r") as f:
        manifest = json.load(f)
        
    for item in manifest["files"]:
        fname = item["filename"]
        expected_hash = item["sha256"]
        fpath = pkg_dir / fname
        if not fpath.exists():
            print("FAIL: Missing file %s" % fname)
            exit(1)
        actual_hash = sha256_file(fpath)
        if actual_hash != expected_hash:
            print("FAIL: Hash mismatch for %s: expected %s, got %s" % (fname, expected_hash, actual_hash))
            exit(1)
        print("PASS: %s -> %s" % (fname, actual_hash))
    print("ALL MANIFEST FILES VERIFIED PASS")

if __name__ == "__main__":
    main()
