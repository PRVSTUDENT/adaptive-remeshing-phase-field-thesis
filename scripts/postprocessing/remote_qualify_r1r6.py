#!/usr/bin/env python3
"""
Remote qualification helper for candidate M2STATE_FRACFIX_RESTART1R1R6 on mlogin01.
"""

import sys
import os
import json
import hashlib

def qualify_remote_r1r6():
    manifest_path = "PACKAGE_MANIFEST.json"
    if not os.path.exists(manifest_path):
        print("ERROR: PACKAGE_MANIFEST.json not found")
        sys.exit(1)
        
    manifest = json.load(open(manifest_path))
    mismatches = 0
    
    for fname, exp_hash in manifest["files"].items():
        if not os.path.exists(fname):
            print("FAIL: File missing: {}".format(fname))
            mismatches += 1
            continue
        actual_hash = hashlib.sha256(open(fname, "rb").read()).hexdigest()
        if actual_hash != exp_hash:
            print("FAIL: Hash mismatch for {}: expected {}, got {}".format(fname, exp_hash, actual_hash))
            mismatches += 1
        else:
            print("PASS: {} ({})".format(fname, actual_hash[:16]))
            
    if mismatches > 0:
        print("REMOTE QUALIFICATION FAIL: {} mismatches".format(mismatches))
        sys.exit(1)
        
    print("ALL REMOTE HASHES MATCH 100%.")

if __name__ == "__main__":
    qualify_remote_r1r6()
