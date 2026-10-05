#!/bin/bash
import json, hashlib, sys
from pathlib import Path

dir_path = Path(__file__).parent
manifest_file = dir_path / "PACKAGE_MANIFEST.json"
manifest = json.loads(manifest_file.read_text(encoding="utf-8"))

failed = False
for rel_fn, exp_sha in manifest["file_hashes"].items():
    fp = dir_path / rel_fn
    if not fp.exists():
        print(f"FAIL: Missing file {rel_fn}")
        failed = True
        continue
    h = hashlib.sha256()
    with open(fp, "rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
    act_sha = h.hexdigest()
    if act_sha.lower() != exp_sha.lower():
        print(f"FAIL: Mismatch for {rel_fn}: expected {exp_sha}, got {act_sha}")
        failed = True

if failed:
    print("Package Manifest Validation: FAILED")
    sys.exit(1)
else:
    print("Package Manifest Validation: 100% PASS")
