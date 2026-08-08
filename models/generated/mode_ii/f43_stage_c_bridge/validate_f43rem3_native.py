import os
import sys
import json

def validate_f43rem3_native(package_dir):
    results = {
        "manifest_exists": False,
        "pbs_exists": False,
        "wrapper_exists": False,
        "cae_script_exists": False,
        "collector_exists": False,
        "criteria_exists": False,
        "failures": [],
        "overall_passed": False
    }

    manifest_path = os.path.join(package_dir, "F43REM3_NATIVE_MANIFEST.json")
    pbs_path = os.path.join(package_dir, "F43REM3_NATIVE.pbs")
    wrapper_path = os.path.join(package_dir, "submit_f43rem3_native.sh")
    cae_script_path = os.path.join(package_dir, "remesh_mode_ii_native_cae.py")
    collector_path = os.path.join(package_dir, "collect_f43rem3_native_evidence.sh")
    criteria_path = os.path.join(package_dir, "F43REM3_ACCEPTANCE_CRITERIA.json")

    results["manifest_exists"] = os.path.exists(manifest_path)
    results["pbs_exists"] = os.path.exists(pbs_path)
    results["wrapper_exists"] = os.path.exists(wrapper_path)
    results["cae_script_exists"] = os.path.exists(cae_script_path)
    results["collector_exists"] = os.path.exists(collector_path)
    results["criteria_exists"] = os.path.exists(criteria_path)

    for k in ["manifest_exists", "pbs_exists", "wrapper_exists", "cae_script_exists", "collector_exists", "criteria_exists"]:
        if not results[k]:
            results["failures"].append("Missing required file for check: {}".format(k))

    if results["pbs_exists"]:
        with open(pbs_path, "r") as f:
            content = f.read()
            if "#PBS -m abe" not in content:
                results["failures"].append("F43REM3_NATIVE.pbs missing #PBS -m abe")
            if "#PBS -M pr21vyci@mailserver.tu-freiberg.de,Pruthviraja.Reddy-Vandavagali@student.tu-freiberg.de" not in content:
                results["failures"].append("F43REM3_NATIVE.pbs missing #PBS -M with both recipients")

    if results["wrapper_exists"]:
        with open(wrapper_path, "r") as f:
            content = f.read()
            if "qsub -m abe -M" not in content:
                results["failures"].append("submit_f43rem3_native.sh missing qsub -m abe -M")
            if "qstat -f" not in content:
                results["failures"].append("submit_f43rem3_native.sh missing qstat -f verification")

    results["overall_passed"] = (len(results["failures"]) == 0)
    return results

if __name__ == "__main__":
    pkg = sys.argv[1] if len(sys.argv) > 1 else "."
    res = validate_f43rem3_native(pkg)
    print(json.dumps(res, indent=2))
    if not res["overall_passed"]:
        sys.exit(1)
