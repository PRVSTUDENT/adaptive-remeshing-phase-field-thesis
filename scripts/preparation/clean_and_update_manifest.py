#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Enforce Unix LF and update batch_e2_transfers_manifest.json
"""
import os
import json
import hashlib

def sha256_file(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while True:
            chunk = f.read(8192)
            if not chunk: break
            h.update(chunk)
    return h.hexdigest()

def clean_lf(filepath):
    with open(filepath, "rb") as f:
        content = f.read()
    content_lf = content.replace(b"\r\n", b"\n")
    with open(filepath, "wb") as f:
        f.write(content_lf)

def main():
    base_dir = "models/generated/mode_ii/stage_e_refinement_coarsening_batch"
    manifest_path = os.path.join(base_dir, "batch_e2_transfers_manifest.json")
    
    with open(manifest_path, "r") as f:
        manifest = json.load(f)
        
    for key, prov in manifest["packages"].items():
        pkg_dir = prov["package_dir"]
        for fname in ["submit_job.pbs", "f44_mixed_uel_restart_stateinit.for", "MODE_STAGED.flag",
                      "STAGE_E_PRIMARY_STATE_BOUNDARY.inp", "STAGE_E_U3_ONLY_BOUNDARY.inp"]:
            fpath = os.path.join(pkg_dir, fname)
            if os.path.exists(fpath):
                clean_lf(fpath)
                
        inp_path = os.path.join(pkg_dir, prov["package_name"] + ".inp")
        clean_lf(inp_path)
        
        prov["inp_sha256"] = sha256_file(inp_path)
        prov["bin_sha256"] = sha256_file(os.path.join(pkg_dir, "STAGE_D_COMMITTED_STATE.bin"))
        prov["for_sha256"] = sha256_file(os.path.join(pkg_dir, "f44_mixed_uel_restart_stateinit.for"))
        prov["pbs_sha256"] = sha256_file(os.path.join(pkg_dir, "submit_job.pbs"))
        
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)
        
    print("Manifest updated successfully.")

if __name__ == "__main__":
    main()
