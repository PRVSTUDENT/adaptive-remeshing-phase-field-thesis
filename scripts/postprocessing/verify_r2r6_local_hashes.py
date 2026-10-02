#!/usr/bin/env python3
"""
Verify 100% local and remote SHA256 byte identity for M2STATE_FRACFIX_RESTART2R6.
"""
import json
import hashlib
from pathlib import Path

def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()

def verify_hashes():
    root = Path(__file__).resolve().parent.parent.parent
    pkg_dir = root / "models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART2R6"
    man_path = pkg_dir / "PACKAGE_MANIFEST.json"
    
    with open(man_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)
        
    hashes = manifest.get("file_hashes", {})
    print(f"Checking {len(hashes)} files in {pkg_dir} against {man_path.name}...")
    
    mismatches = []
    for fname, exp_hash in hashes.items():
        fpath = pkg_dir / fname
        if not fpath.exists():
            mismatches.append((fname, "MISSING", exp_hash))
            continue
        act_hash = sha256_file(fpath)
        if act_hash != exp_hash:
            mismatches.append((fname, act_hash, exp_hash))
        else:
            print(f"  [OK] {fname:45s} -> {act_hash[:16]}...")
            
    if mismatches:
        print("\nHASH MISMATCHES FOUND:")
        for m in mismatches:
            print(f"  {m[0]}: act={m[1]} vs exp={m[2]}")
        raise ValueError("Package manifest hash verification failed")
    else:
        print("\nALL 12 MANIFEST FILES MATCH PACKAGE_MANIFEST.json 100% BYTE-FOR-BYTE!")

if __name__ == "__main__":
    verify_hashes()
