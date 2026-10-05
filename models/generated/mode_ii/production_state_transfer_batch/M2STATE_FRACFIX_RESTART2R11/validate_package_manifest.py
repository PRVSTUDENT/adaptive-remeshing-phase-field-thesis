#!/bin/env python3
import json, hashlib, sys
from pathlib import Path

manifest_path = Path('PACKAGE_MANIFEST.json')
if not manifest_path.exists():
    print("ERROR: PACKAGE_MANIFEST.json missing")
    sys.exit(1)

manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
for item in manifest['files']:
    fn = item['filename']
    expected = item['sha256']
    p = Path(fn)
    if not p.exists():
        print(f"ERROR: {fn} missing")
        sys.exit(1)
    actual = hashlib.sha256(p.read_bytes()).hexdigest()
    if actual.lower() != expected.lower():
        print(f"ERROR: Hash mismatch for {fn}: actual={actual} expected={expected}")
        sys.exit(1)

print("Package Manifest Validation: 100% PASS")
