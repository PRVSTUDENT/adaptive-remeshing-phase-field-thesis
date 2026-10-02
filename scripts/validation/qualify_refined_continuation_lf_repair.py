#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Technical Requalification of LF-Repaired Refined Continuation Package:
Package: M2CORR_STAGE_E_REFINED_TARGET_MINIMAL_CONTINUATION_VAL
Targeting replacement of failed predecessor 1390829.mmaster02
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
    pkg_dir = "models/generated/mode_ii/stage_e_refinement_coarsening_batch/M2CORR_STAGE_E_REFINED_TARGET_MINIMAL_CONTINUATION_VAL"
    inp_path = os.path.join(pkg_dir, "M2CORR_STAGE_E_REFINED_TARGET_MINIMAL_CONTINUATION_VAL.inp")
    for_path = os.path.join(pkg_dir, "f44_mixed_uel_restart_stateinit.for")
    pbs_path = os.path.join(pkg_dir, "submit_job.pbs")
    
    # 1. Inspect PBS bytes
    with open(pbs_path, "rb") as fp:
        pbs_bytes = fp.read()
        
    has_crlf = b"\r\n" in pbs_bytes
    has_cr = b"\r" in pbs_bytes
    has_bom = pbs_bytes.startswith(b"\xef\xbb\xbf")
    lines = pbs_bytes.split(b"\n")
    shebang_exact = (lines[0] == b"#!/bin/bash")
    
    pbs_sha256 = get_file_sha256(pbs_path)
    inp_sha256 = get_file_sha256(inp_path)
    for_sha256 = get_file_sha256(for_path)
    
    ref_for_sha = "62e35f74bbeccd3f5b1ac67312b79211f4ccb75648ae20dbb8985cb577fe1aab"
    ref_inp_sha = "d1731bebabf80560ae6150c3a7288bb186975d36fcb738ae1b42ec86a50f6028"
    
    scientific_identical = (for_sha256 == ref_for_sha and inp_sha256 == ref_inp_sha)
    lf_clean = (not has_cr and not has_bom and shebang_exact)
    
    results = {
        "package_name": "M2CORR_STAGE_E_REFINED_TARGET_MINIMAL_CONTINUATION_VAL",
        "pbs_file": pbs_path,
        "pbs_size_bytes": len(pbs_bytes),
        "pbs_sha256": pbs_sha256,
        "has_crlf": has_crlf,
        "has_cr": has_cr,
        "has_utf8_bom": has_bom,
        "shebang_exact_match": shebang_exact,
        "lf_clean": lf_clean,
        "inp_sha256": inp_sha256,
        "for_sha256": for_sha256,
        "scientific_files_byte_identical": scientific_identical,
        "technical_requalification_passed": (lf_clean and scientific_identical)
    }
    
    out_json = os.path.join(pkg_dir, "technical_lf_requalification.json")
    with open(out_json, "w") as fp:
        json.dump(results, fp, indent=2)
        
    print("================================================================================")
    print("REFINED CONTINUATION PACKAGE LF TECHNICAL REQUALIFICATION:")
    print("================================================================================")
    print("PBS Size (Bytes)       : %d" % len(pbs_bytes))
    print("PBS SHA-256            : %s" % pbs_sha256)
    print("Shebang Line           : %s (Exact match = %s)" % (lines[0].decode('utf-8', errors='ignore'), shebang_exact))
    print("Contains CR / CRLF     : %s" % has_cr)
    print("Contains UTF-8 BOM     : %s" % has_bom)
    print("INP SHA-256            : %s (Valid = %s)" % (inp_sha256, inp_sha256 == ref_inp_sha))
    print("FOR SHA-256            : %s (Valid = %s)" % (for_sha256, for_sha256 == ref_for_sha))
    print("Scientific Invariance  : %s" % ("100% BYTE IDENTICAL" if scientific_identical else "CHANGED"))
    print("Technical Requal Status: %s" % ("PASSED" if results["technical_requalification_passed"] else "FAILED"))

if __name__ == "__main__":
    main()
