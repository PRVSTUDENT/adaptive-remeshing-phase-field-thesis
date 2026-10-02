#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Pre-submission Qualification Script:
Package: M2CORR_STAGE_E_DONOR_MINIMAL_DTMIN_CONTINUATION_VAL
"""

import os
import sys
import hashlib
import json

def get_file_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while True:
            chunk = f.read(8192)
            if not chunk: break
            h.update(chunk)
    return h.hexdigest()

def main():
    pkg_dir = "models/generated/mode_ii/stage_e_refinement_coarsening_batch/M2CORR_STAGE_E_DONOR_MINIMAL_DTMIN_CONTINUATION_VAL"
    inp_path = os.path.join(pkg_dir, "M2CORR_STAGE_E_DONOR_MINIMAL_DTMIN_CONTINUATION_VAL.inp")
    for_path = os.path.join(pkg_dir, "f44_mixed_uel_restart_stateinit.for")
    pbs_path = os.path.join(pkg_dir, "submit_job.pbs")
    
    with open(pbs_path, "rb") as fp:
        pbs_bytes = fp.read()
        
    has_cr = b"\r" in pbs_bytes
    has_bom = pbs_bytes.startswith(b"\xef\xbb\xbf")
    lines = pbs_bytes.split(b"\n")
    shebang_exact = (lines[0] == b"#!/bin/bash")
    
    pbs_sha = get_file_sha256(pbs_path)
    inp_sha = get_file_sha256(inp_path)
    for_sha = get_file_sha256(for_path)
    
    expected_inp_sha = "105d2cc04de25f68c0a1fbeaab8b66d355881993cf6292e8201ad210137d3db8"
    expected_for_sha = "62e35f74bbeccd3f5b1ac67312b79211f4ccb75648ae20dbb8985cb577fe1aab"
    
    inp_valid = (inp_sha == expected_inp_sha)
    for_valid = (for_sha == expected_for_sha)
    lf_clean = (not has_cr and not has_bom and shebang_exact)
    
    results = {
        "package_name": "M2CORR_STAGE_E_DONOR_MINIMAL_DTMIN_CONTINUATION_VAL",
        "pbs_file": pbs_path,
        "pbs_size_bytes": len(pbs_bytes),
        "pbs_sha256": pbs_sha,
        "has_cr": has_cr,
        "has_utf8_bom": has_bom,
        "shebang_exact_match": shebang_exact,
        "lf_clean": lf_clean,
        "inp_sha256": inp_sha,
        "for_sha256": for_sha,
        "inp_hash_valid": inp_valid,
        "for_hash_valid": for_valid,
        "pre_submission_qualification_passed": (lf_clean and inp_valid and for_valid)
    }
    
    out_json = os.path.join(pkg_dir, "donor_dtmin_qualification.json")
    with open(out_json, "w") as fp:
        json.dump(results, fp, indent=2)
        
    print("================================================================================")
    print("DONOR DTMIN PACKAGE PRE-SUBMISSION QUALIFICATION:")
    print("================================================================================")
    print("PBS Size (Bytes)       : %d" % len(pbs_bytes))
    print("PBS SHA-256            : %s" % pbs_sha)
    print("Shebang Line           : %s (Exact match = %s)" % (lines[0].decode('utf-8', errors='ignore'), shebang_exact))
    print("Contains CR / CRLF     : %s" % has_cr)
    print("Contains UTF-8 BOM     : %s" % has_bom)
    print("INP SHA-256            : %s (Matches Manifest = %s)" % (inp_sha, inp_valid))
    print("FOR SHA-256            : %s (Matches Baseline = %s)" % (for_sha, for_valid))
    print("Pre-sub Requal Status  : %s" % ("PASSED" if results["pre_submission_qualification_passed"] else "FAILED"))

if __name__ == "__main__":
    main()
