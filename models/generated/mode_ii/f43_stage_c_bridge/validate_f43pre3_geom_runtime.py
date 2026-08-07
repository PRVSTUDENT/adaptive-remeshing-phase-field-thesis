#!/bin/bash
#!/usr/bin/env python3
"""Static validator for F43PRE3_GEOM preanalysis execution package."""

import os
import sys
import json
import hashlib
from pathlib import Path

def validate_f43pre3_geom(pkg_dir):
    pkg_path = Path(pkg_dir)
    manifest_path = pkg_path / "F43PRE3_SOURCE_MANIFEST.json"
    inp_path = pkg_path / "F43PRE3_GEOM.inp"
    pbs_path = pkg_path / "F43PRE3_GEOM.pbs"
    wrapper_path = pkg_path / "submit_f43pre3_geom.sh"
    collector_path = pkg_path / "collect_f43pre3_geom_evidence.sh"
    criteria_path = pkg_path / "F43PRE3_ACCEPTANCE_CRITERIA.json"

    res = {
        "manifest_exists": manifest_path.exists(),
        "inp_exists": inp_path.exists(),
        "pbs_exists": pbs_path.exists(),
        "wrapper_exists": wrapper_path.exists(),
        "collector_exists": collector_path.exists(),
        "criteria_exists": criteria_path.exists(),
        "failures": []
    }

    if not res["manifest_exists"]:
        res["failures"].append("F43PRE3_SOURCE_MANIFEST.json missing")
        res["overall_passed"] = False
        return res

    with open(manifest_path, "r") as f:
        m = json.load(f)

    if m.get("task_id") != "F43PRE3_GEOM":
        res["failures"].append("Manifest task_id must be F43PRE3_GEOM")

    if m.get("cae_source_sha256") != "0d5b32fe48b70ed0817e8b9c439bfdb39165dee5e8d157fcb6d0b3075efe1baa":
        res["failures"].append("Manifest cae_source_sha256 must match Abaqus 2023 0d5b32... SHA")

    if res["inp_exists"]:
        with open(inp_path, "rb") as f:
            actual_inp_sha = hashlib.sha256(f.read()).hexdigest()
        if actual_inp_sha != m.get("inp_sha256"):
            res["failures"].append("INP file SHA mismatch with manifest inp_sha256")

    # Reject PRE2 889c CAE as active source
    pre2_cae = m.get("pre2_provenance", {}).get("cae_sha256")
    if m.get("cae_source_sha256") == "889c15ba6621ae8435324473bb385cb0da6a62866dd8c996865806b876c051ff":
        res["failures"].append("PRE2 889c15 CAE cannot be used as active PRE3 source")

    # Reject PRE2 ODB as native remesh predecessor in PRE3
    if m.get("predecessor_job_id") == "1385392.mmaster02" and m.get("task_id") == "F43REM2_NATIVE":
        res["failures"].append("PRE2 ODB cannot be used as remesh predecessor")

    res["overall_passed"] = len(res["failures"]) == 0
    return res

if __name__ == "__main__":
    pkg_dir = sys.argv[1] if len(sys.argv) > 1 else "."
    res = validate_f43pre3_geom(pkg_dir)
    print(json.dumps(res, indent=2))
    sys.exit(0 if res["overall_passed"] else 1)
