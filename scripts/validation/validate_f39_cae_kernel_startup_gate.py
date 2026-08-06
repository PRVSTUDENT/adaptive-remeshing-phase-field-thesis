#!/usr/bin/env python3
import json
import os
import re
import sys

def main():
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    pkg_dir = os.path.join(repo_root, "models", "generated", "mode_ii", "f39_abaqus_cae_kernel_startup_diagnostic")
    wrapper_path = os.path.join(repo_root, "scripts", "hpc", "stage_f", "submit_stage_f39_cae_kernel_diagnostic.sh")

    failures = []

    # Check 1: minimal_cae_kernel_probe.py has no __file__ and no model import
    probe_path = os.path.join(pkg_dir, "runtime", "minimal_cae_kernel_probe.py")
    if os.path.exists(probe_path):
        with open(probe_path, "r") as f:
            content = f.read()
            if "__file__" in content:
                failures.append("minimal_cae_kernel_probe.py contains prohibited __file__")
            prohibited_imports = ["import mdb", "from abaqus import", "import part", "import assembly", "import mesh"]
            for imp in prohibited_imports:
                if imp in content:
                    failures.append("minimal_cae_kernel_probe.py contains prohibited model import: " + imp)
    else:
        failures.append("minimal_cae_kernel_probe.py missing")

    # Check 2: No solver, datacheck, remeshing, state transfer in package
    prohibited_keywords = ["abaqus datacheck", "abaqus job", "submit()", "remesh", "state_transfer"]
    for root, _, files in os.walk(pkg_dir):
        for fname in files:
            fpath = os.path.join(root, fname)
            if fname in ["SHA256SUMS", "F39_SHA256SUMS", "PACKAGE_MANIFEST.json"]:
                continue
            try:
                with open(fpath, "r") as f:
                    txt = f.read()
                    for kw in prohibited_keywords:
                        if kw in txt:
                            failures.append("File {} contains prohibited keyword '{}'".format(fname, kw))
            except Exception:
                pass

    # Check 3: M2RMKERN1.pbs trap preserves first_failure and exits with it
    pbs_path = os.path.join(pkg_dir, "M2RMKERN1.pbs")
    if os.path.exists(pbs_path):
        with open(pbs_path, "r") as f:
            pbs_txt = f.read()
            if "trap - EXIT" not in pbs_txt or 'exit "$first_failure"' not in pbs_txt:
                failures.append("M2RMKERN1.pbs does not correctly unbind trap and exit with $first_failure")
            if "STATUS.json" not in pbs_txt or "generate_missing_evidence_report.py" not in pbs_txt:
                failures.append("M2RMKERN1.pbs missing STATUS.json or missing evidence report invocation")
            if "validate_f39_runtime_audits.py" not in pbs_txt:
                failures.append("M2RMKERN1.pbs does not invoke validate_f39_runtime_audits.py")
    else:
        failures.append("M2RMKERN1.pbs missing")

    # Check 4: Missing vs existing evidence disjoint check in generate_missing_evidence_report.py
    gen_rep_path = os.path.join(pkg_dir, "runtime", "generate_missing_evidence_report.py")
    if os.path.exists(gen_rep_path):
        with open(gen_rep_path, "r") as f:
            gen_txt = f.read()
            if "existing_files" not in gen_txt or "missing_files" not in gen_txt:
                failures.append("generate_missing_evidence_report.py missing existing/missing sets logic")
    else:
        failures.append("generate_missing_evidence_report.py missing")

    # Check 5: Environment collector redaction logic
    collector_path = os.path.join(pkg_dir, "runtime", "collect_launcher_environment.py")
    if os.path.exists(collector_path):
        with open(collector_path, "r") as f:
            col_txt = f.read()
            if "[REDACTED]" not in col_txt or "WHITELISTED_VARS" not in col_txt:
                failures.append("collect_launcher_environment.py missing environment variable redaction logic")
    else:
        failures.append("collect_launcher_environment.py missing")

    # Check 6: PACKAGE_MANIFEST.json matches all runtime files
    man_path = os.path.join(pkg_dir, "PACKAGE_MANIFEST.json")
    if os.path.exists(man_path):
        with open(man_path, "r") as f:
            manifest = json.load(f)
            pkg_files = manifest.get("package_files", {})
            required_files = [
                "M2RMKERN1.pbs",
                "runtime/collect_launcher_environment.py",
                "runtime/generate_missing_evidence_report.py",
                "runtime/minimal_cae_kernel_probe.py",
                "runtime/validate_f39_runtime_audits.py"
            ]
            for rf in required_files:
                if rf not in pkg_files:
                    failures.append("PACKAGE_MANIFEST.json missing entry for " + rf)
    else:
        failures.append("PACKAGE_MANIFEST.json missing")

    # Check 7: Submission wrapper contains exactly one qsub and closed gates
    if os.path.exists(wrapper_path):
        with open(wrapper_path, "r") as f:
            wrap_txt = f.read()
            qsub_matches = re.findall(r"\bqsub\b", wrap_txt)
            if len(qsub_matches) != 1:
                failures.append("Submission wrapper must contain exactly 1 qsub call, found " + str(len(qsub_matches)))
            if 'F39_ALLOW_SUBMISSION:-false' not in wrap_txt or 'F39_AUTHORIZE_M2RMKERN1:-false' not in wrap_txt:
                failures.append("Submission wrapper gates not properly defaulted to false")
    else:
        failures.append("Submission wrapper missing")

    # Check 8: F38 package preservation check
    f38_dir = os.path.join(repo_root, "models", "generated", "mode_ii", "f38_comprehensive_cae_diagnostic_matrix")
    if not os.path.exists(f38_dir) or not os.path.exists(os.path.join(f38_dir, "M2RMDIAG1.pbs")):
        failures.append("F38 package modified or missing")

    result = {
        "classification": "pass" if len(failures) == 0 else "fail",
        "failures": failures
    }

    print(json.dumps(result, indent=2))
    return 0 if result["classification"] == "pass" else 1

if __name__ == "__main__":
    sys.exit(main())
