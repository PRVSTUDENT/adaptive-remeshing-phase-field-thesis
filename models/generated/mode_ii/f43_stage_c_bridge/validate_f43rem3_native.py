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
        "config_exists": False,
        "failures": [],
        "overall_passed": False
    }

    manifest_path = os.path.join(package_dir, "F43REM3_NATIVE_MANIFEST.json")
    pbs_path = os.path.join(package_dir, "F43REM3_NATIVE.pbs")
    wrapper_path = os.path.join(package_dir, "submit_f43rem3_native.sh")
    cae_script_path = os.path.join(package_dir, "remesh_mode_ii_native_cae.py")
    collector_path = os.path.join(package_dir, "collect_f43rem3_native_evidence.sh")
    criteria_path = os.path.join(package_dir, "F43REM3_ACCEPTANCE_CRITERIA.json")
    config_path = os.path.join(package_dir, "f43_remeshing_rule_config.json")

    results["manifest_exists"] = os.path.exists(manifest_path)
    results["pbs_exists"] = os.path.exists(pbs_path)
    results["wrapper_exists"] = os.path.exists(wrapper_path)
    results["cae_script_exists"] = os.path.exists(cae_script_path)
    results["collector_exists"] = os.path.exists(collector_path)
    results["criteria_exists"] = os.path.exists(criteria_path)
    results["config_exists"] = os.path.exists(config_path)

    for k in ["manifest_exists", "pbs_exists", "wrapper_exists", "cae_script_exists", "collector_exists", "criteria_exists", "config_exists"]:
        if not results[k]:
            results["failures"].append("Missing required file for check: {}".format(k))

    if results["manifest_exists"]:
        with open(manifest_path, "r") as f:
            m = json.load(f)
        if m.get("source_cae_sha256") != "0d5b32fe48b70ed0817e8b9c439bfdb39165dee5e8d157fcb6d0b3075efe1baa":
            results["failures"].append("Invalid source CAE SHA in manifest")
        if m.get("predecessor_odb_sha256") != "9a5262931675d2780ccc8b6e6060dd20b817917df7cdf6e499a7a0a2d0d06eb1":
            results["failures"].append("Invalid predecessor ODB SHA in manifest")
        
        rp = m.get("remesh_parameters", {})
        if rp.get("min_element_size_mm") != 0.0075:
            results["failures"].append("Manifest min_element_size_mm must equal 0.0075")
        if rp.get("max_element_size_mm") != 0.03:
            results["failures"].append("Manifest max_element_size_mm must equal 0.03")
        if rp.get("refinement_factor") != 0.5:
            results["failures"].append("Manifest refinement_factor must equal 0.5")
        if rp.get("error_target") != 0.05:
            results["failures"].append("Manifest error_target must equal 0.05")
        if rp.get("coarsening_policy") != "DISALLOW_COARSENING":
            results["failures"].append("Manifest coarsening_policy must be DISALLOW_COARSENING")
        if rp.get("max_remeshing_passes") != 1:
            results["failures"].append("Manifest max_remeshing_passes must equal 1")

    if results["config_exists"]:
        with open(config_path, "r") as f:
            cfg = json.load(f)
        rc = cfg.get("remeshing_rule_configuration", {})
        if rc.get("coarsening_policy") != "DISALLOW_COARSENING":
            results["failures"].append("Config coarsening_policy must be DISALLOW_COARSENING")
        if rc.get("max_remeshing_passes") != 1:
            results["failures"].append("Config max_remeshing_passes must equal 1")

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
