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
    root = Path(__file__).resolve().parent.parent.parent
    cand_dir = root / "models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART2R5"
    man_path = cand_dir / "PACKAGE_MANIFEST.json"
    
    with open(man_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)
        
    hashes = manifest.get("file_hashes", {})
    mismatches = []
    print(f"Checking {len(hashes)} files in {cand_dir.name}...")
    for fname, exp_hash in sorted(hashes.items()):
        fpath = cand_dir / fname
        if not fpath.exists():
            mismatches.append(f"{fname}: FILE_NOT_FOUND")
            continue
        act_hash = sha256_file(fpath)
        if act_hash != exp_hash:
            mismatches.append(f"{fname}: HASH_MISMATCH (exp {exp_hash[:8]} vs act {act_hash[:8]})")
        else:
            print(f"  {fname:45s} [MATCH] {act_hash}")
            
    if mismatches:
        print("FAILED with mismatches:")
        for m in mismatches:
            print(" -", m)
        sys.exit(1)
    else:
        print("ALL_MANIFEST_FILES_VERIFIED_PASS")

if __name__ == "__main__":
    main()
