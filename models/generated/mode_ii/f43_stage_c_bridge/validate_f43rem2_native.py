#!/usr/bin/env python3
"""
Offline Static Validator for F43REM2_NATIVE Package and Fail-Closed Runtime.
"""

import sys
import os
import hashlib
import json

def get_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, 'rb') as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()

def validate_f43rem2_native(pkg_dir="."):
    manifest_path = os.path.join(pkg_dir, "F43REM2_NATIVE_MANIFEST.json")
    driver_path = os.path.join(pkg_dir, "remesh_mode_ii_native_cae.py")
    pbs_path = os.path.join(pkg_dir, "F43REM2_NATIVE.pbs")
    wrapper_path = os.path.join(pkg_dir, "submit_f43rem2_native.sh")
    collector_path = os.path.join(pkg_dir, "collect_f43rem2_native_evidence.sh")
    cae_local_path = os.path.join(pkg_dir, "ModeII_Geometry_Source.cae")
    
    results = {
        "manifest_exists": False,
        "driver_exists": False,
        "pbs_script_exists": False,
        "submit_wrapper_exists": False,
        "collector_exists": False,
        "cae_local_binary_absent": False,
        "cae_external_contract_valid": False,
        "predecessor_odb_sha_contract_valid": False,
        "source_open_in_place_forbidden": False,
        "execution_authorized_false": False,
        "submission_approved_false": False,
        "maximum_jobs_now_zero": False,
        "overall_passed": False,
        "failures": []
    }

    # 1. Manifest Audit
    if os.path.exists(manifest_path):
        results["manifest_exists"] = True
        try:
            with open(manifest_path, "r") as f:
                m = json.load(f)
                
            if m.get("predecessor_odb_sha256") == "85339f45937cf5d2c57f169fa71b3e55f066082e6525aa3c20a370f058c4cf72":
                results["predecessor_odb_sha_contract_valid"] = True
            else:
                results["failures"].append("Manifest predecessor ODB SHA256 contract invalid")
                
            if m.get("source_cae_sha256") == "889c15ba6621ae8435324473bb385cb0da6a62866dd8c996865806b876c051ff":
                results["cae_external_contract_valid"] = True
            else:
                results["failures"].append("External CAE SHA256 contract invalid")
                
            if m.get("cae_source_open_in_place") is False:
                results["source_open_in_place_forbidden"] = True
            else:
                results["failures"].append("Source CAE open in place not false")
                
            if m.get("execution_authorized") is False:
                results["execution_authorized_false"] = True
            else:
                results["failures"].append("execution_authorized must be false")
                
            if m.get("submission_approved") is False:
                results["submission_approved_false"] = True
            else:
                results["failures"].append("submission_approved must be false")
                
            if m.get("maximum_jobs_now") == 0:
                results["maximum_jobs_now_zero"] = True
            else:
                results["failures"].append("maximum_jobs_now must be 0")
        except Exception as e:
            results["failures"].append(f"Failed to parse manifest: {e}")
    else:
        results["failures"].append("F43REM2_NATIVE_MANIFEST.json missing")

    # 2. Package Execution Files Audit
    if os.path.exists(driver_path):
        results["driver_exists"] = True
    else:
        results["failures"].append("remesh_mode_ii_native_cae.py missing")

    if os.path.exists(pbs_path):
        results["pbs_script_exists"] = True
    else:
        results["failures"].append("F43REM2_NATIVE.pbs missing")

    if os.path.exists(wrapper_path):
        results["submit_wrapper_exists"] = True
    else:
        results["failures"].append("submit_f43rem2_native.sh missing")

    if os.path.exists(collector_path):
        results["collector_exists"] = True
    else:
        results["failures"].append("collect_f43rem2_native_evidence.sh missing")

    # 3. External CAE Policy Audit (Local CAE binary must NOT be tracked)
    if not os.path.exists(cae_local_path):
        results["cae_local_binary_absent"] = True
    else:
        results["failures"].append("ModeII_Geometry_Source.cae binary present in local tracked tree")

    results["overall_passed"] = (
        results["manifest_exists"] and
        results["driver_exists"] and
        results["pbs_script_exists"] and
        results["submit_wrapper_exists"] and
        results["collector_exists"] and
        results["cae_local_binary_absent"] and
        results["cae_external_contract_valid"] and
        results["predecessor_odb_sha_contract_valid"] and
        results["source_open_in_place_forbidden"] and
        results["execution_authorized_false"] and
        results["submission_approved_false"] and
        results["maximum_jobs_now_zero"]
    )

    out_status_path = os.path.join(pkg_dir, "F43REM2_NATIVE_VALIDATION_STATUS.json")
    with open(out_status_path, "w") as f:
        json.dump(results, f, indent=2)

    return results

if __name__ == "__main__":
    pkg_dir = sys.argv[1] if len(sys.argv) > 1 else "."
    res = validate_f43rem2_native(pkg_dir)
    print(json.dumps(res, indent=2))
    sys.exit(0 if res["overall_passed"] else 1)
