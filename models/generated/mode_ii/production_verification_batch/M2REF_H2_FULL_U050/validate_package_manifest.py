import sys
import json
import hashlib
from pathlib import Path

def validate():
    manifest_path = Path("PACKAGE_MANIFEST.json")
    if not manifest_path.exists():
        print("ERROR: PACKAGE_MANIFEST.json not found!")
        sys.exit(1)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    failed = False
    for fn, exp_sha in manifest.get("files", {}).items():
        fp = Path(fn)
        if not fp.exists():
            print(f"ERROR: missing file {fn}")
            failed = True
            continue
        actual = hashlib.sha256(fp.read_bytes()).hexdigest()
        if actual != exp_sha:
            print(f"ERROR: SHA256 mismatch for {fn}: expected {exp_sha}, got {actual}")
            failed = True
    if failed:
        sys.exit(1)
    print("ALL FILES MATCH MANIFEST SHA256: PASS")

if __name__ == '__main__':
    validate()
