#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Regenerates MANIFEST.sha256 for ModeI_Supervisor_Report_Reproduction_Package.
Includes all files except:
- MANIFEST.sha256
- HPC_TEST_RESULTS.md
- HPC_QUALIFICATION_SUMMARY.json
- Temporary / cache files
Uses standard POSIX format: <sha256>  <rel_path_with_forward_slashes>\n
Sorted alphabetically by path.
"""

import os
import hashlib

def sha256_file(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()

def main():
    pkg_root = os.path.abspath('ModeI_Supervisor_Report_Reproduction_Package')
    exclude_rel = {
        'MANIFEST.sha256',
        'HPC_TEST_RESULTS.md',
        'HPC_QUALIFICATION_SUMMARY.json'
    }
    
    entries = []
    for root, dirs, files in os.walk(pkg_root):
        dirs.sort()
        for f in sorted(files):
            if f.endswith(('.pyc', '.tmp', '.bak')) or f == '__pycache__':
                continue
            full_path = os.path.join(root, f)
            rel_path = os.path.relpath(full_path, pkg_root).replace('\\', '/')
            if rel_path in exclude_rel:
                continue
            sha = sha256_file(full_path)
            entries.append((rel_path, sha))
            
    entries.sort(key=lambda x: x[0])
    
    manifest_path = os.path.join(pkg_root, 'MANIFEST.sha256')
    with open(manifest_path, 'wb') as f:
        for rel_path, sha in entries:
            line = "{}  {}\n".format(sha, rel_path)
            f.write(line.encode('utf-8'))
            
    print("Generated MANIFEST.sha256 with {} entries.".format(len(entries)))

if __name__ == '__main__':
    main()
