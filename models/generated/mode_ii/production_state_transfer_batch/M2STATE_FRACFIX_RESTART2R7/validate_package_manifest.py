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
    root = Path(__file__).resolve().parent
    man_path = root / 'PACKAGE_MANIFEST.json'
    if not man_path.exists():
        print('ERROR: PACKAGE_MANIFEST.json missing')
        sys.exit(1)
        
    with open(man_path, 'r') as f:
        manifest = json.load(f)
        
    hashes = manifest.get('file_hashes', {})
    mismatches = []
    for fname, exp_hash in hashes.items():
        fpath = root / fname
        if not fpath.exists():
            mismatches.append(f"{fname}: FILE_NOT_FOUND")
            continue
        act_hash = sha256_file(fpath)
        if act_hash != exp_hash:
            mismatches.append(f"{fname}: HASH_MISMATCH (exp {exp_hash[:8]} vs act {act_hash[:8]})")
            
    if mismatches:
        print('MANIFEST VALIDATION FAILED:')
        for m in mismatches:
            print('  -', m)
        sys.exit(1)
        
    print('ALL_MANIFEST_FILES_VERIFIED_PASS')

if __name__ == '__main__':
    main()
