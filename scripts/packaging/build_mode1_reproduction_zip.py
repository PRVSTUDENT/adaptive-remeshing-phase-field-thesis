#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Builds deterministic ZIP archive for ModeI_Supervisor_Report_Reproduction_Package.
Root entry: ModeI_Supervisor_Report_Reproduction_Package/
Excludes: __pycache__, *.pyc, *.tmp, *.bak
"""

import os
import zipfile
import hashlib

def build_zip(source_dir, output_zip_path):
    source_dir = os.path.abspath(source_dir)
    parent_dir = os.path.dirname(source_dir)
    base_name = os.path.basename(source_dir)
    
    file_entries = []
    for root, dirs, files in os.walk(source_dir):
        dirs.sort()
        for f in sorted(files):
            if f.endswith(('.pyc', '.tmp', '.bak')) or f == '__pycache__':
                continue
            full_path = os.path.join(root, f)
            rel_path = os.path.relpath(full_path, parent_dir).replace('\\', '/')
            file_entries.append((full_path, rel_path))
            
    file_entries.sort(key=lambda x: x[1])
    
    # Remove existing zip if present
    if os.path.exists(output_zip_path):
        os.remove(output_zip_path)
        
    with zipfile.ZipFile(output_zip_path, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for full_path, arcname in file_entries:
            zf.write(full_path, arcname)
            
    # Compute size and SHA-256
    size = os.path.getsize(output_zip_path)
    h = hashlib.sha256()
    with open(output_zip_path, 'rb') as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
    sha256 = h.hexdigest()
    
    print("Successfully built: {}".format(output_zip_path))
    print("File count: {}".format(len(file_entries)))
    print("Byte size: {}".format(size))
    print("SHA-256: {}".format(sha256))
    return size, sha256, len(file_entries)

if __name__ == '__main__':
    source = 'ModeI_Supervisor_Report_Reproduction_Package'
    dest = 'ModeI_Supervisor_Report_Reproduction_Package.zip'
    build_zip(source, dest)
