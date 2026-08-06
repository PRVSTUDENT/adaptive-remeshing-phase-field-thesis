#!/usr/bin/env python3
import json
import os
import re
import sys

def main():
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    pkg_dir = os.path.join(repo_root, "models", "generated", "mode_ii", "f40_f38_cae_invocation_model_building_bisect")
    wrapper_path = os.path.join(repo_root, "scripts", "hpc", "stage_f", "submit_stage_f40_cae_bisect.sh")

    failures = []

    # Check 1: bisection runner has no __file__ dependency
    runner_path = os.path.join(pkg_dir, "runtime", "f40_cae_bisection_runner.py")
    if os.path.exists(runner_path):
        with open(runner_path, "r") as f:
            content = f.read()
            if "__file__" in content:
                failures.append("f40_cae_bisection_runner.py contains prohibited __file__")
    else:
        failures.append("f40_cae_bisection_runner.py missing")

    # Check 2: No solver, datacheck, remeshing, state transfer, or nested qsub
    prohibited_keywords = ["abaqus datacheck", "abaqus job", "submit()", "remesh", "state_transfer", "qsub "]
    for root, _, files in os.walk(pkg_dir):
        for fname in files:
            fpath = os.path.join(root, fname)
            if fname in ["SHA256SUMS", "F40_SHA256SUMS", "PACKAGE_MANIFEST.json"]:
                continue
            try:
                with open(fpath, "r") as f:
                    txt = f.read()
                    for kw in prohibited_keywords:
                        if kw in txt:
                            failures.append("File {} contains prohibited keyword '{}'".format(fname, kw))
            except Exception:
                pass

    # Check 3: M2RMBISECT1.pbs trap unbinds and preserves first_failure
    pbs_path = os.path.join(pkg_dir, "M2RMBISECT1.pbs")
    if os.path.exists(pbs_path):
        with open(pbs_path, "r") as f:
            pbs_txt = f.read()
            if "trap - EXIT" not in pbs_txt or 'exit "$first_failure"' not in pbs_txt:
                failures.append("M2RMBISECT1.pbs does not correctly unbind trap and exit with $first_failure")
            if "entry_imfdfkmq" not in pbs_txt or "select=1:ncpus=1:mpiprocs=1:ompthreads=1:mem=8gb" not in pbs_txt:
                failures.append("M2RMBISECT1.pbs missing entry_imfdfkmq or select resource directive")
            if "runtime_validator_rc" not in pbs_txt or "first_failure=" not in pbs_txt:
                failures.append("M2RMBISECT1.pbs does not compute first_failure from runtime_validator_rc")
    else:
        failures.append("M2RMBISECT1.pbs missing")

    # Check 4: Contract delta auditor presence
    delta_path = os.path.join(pkg_dir, "runtime", "f40_invocation_contract_delta.py")
    if not os.path.exists(delta_path):
        failures.append("f40_invocation_contract_delta.py missing")

    # Check 5: PACKAGE_MANIFEST.json completeness
    man_path = os.path.join(pkg_dir, "PACKAGE_MANIFEST.json")
    if os.path.exists(man_path):
        with open(man_path, "r") as f:
            manifest = json.load(f)
            file_entries = manifest.get("files", [])
            pkg_files = [item["path"] for item in file_entries] if isinstance(file_entries, list) else list(manifest.get("package_files", {}).keys())
            required_files = [
                "M2RMBISECT1.pbs",
                "runtime/f40_cae_bisection_runner.py",
                "runtime/run_f38_cae_diagnostic.py",
                "runtime/f38_cae_diagnostic_matrix.py",
                "runtime/f40_invocation_contract_delta.py",
                "runtime/generate_missing_evidence_report.py",
                "runtime/source_deck.inp",
                "runtime/validate_f40_runtime_audits.py"
            ]
            for rf in required_files:
                if rf not in pkg_files:
                    failures.append("PACKAGE_MANIFEST.json missing entry for " + rf)
    else:
        failures.append("PACKAGE_MANIFEST.json missing")

    # Check 6: Submission wrapper gate defaults
    if os.path.exists(wrapper_path):
        with open(wrapper_path, "r") as f:
            wrap_txt = f.read()
            qsub_matches = re.findall(r"^\s*JOB_ID=\$\(qsub\b", wrap_txt, re.MULTILINE)
            if len(qsub_matches) != 1:
                failures.append("Submission wrapper must contain exactly 1 qsub invocation line, found " + str(len(qsub_matches)))
            if 'F40_ALLOW_SUBMISSION:-false' not in wrap_txt or 'F40_AUTHORIZE_M2RMBISECT1:-false' not in wrap_txt:
                failures.append("Submission wrapper gates not properly defaulted to false")
    else:
        failures.append("Submission wrapper missing")

    # Check 7: F38/F39 preservation checks
    f38_dir = os.path.join(repo_root, "models", "generated", "mode_ii", "f38_comprehensive_cae_diagnostic_matrix")
    f39_dir = os.path.join(repo_root, "models", "generated", "mode_ii", "f39_abaqus_cae_kernel_startup_diagnostic")
    if not os.path.exists(os.path.join(f38_dir, "M2RMDIAG1.pbs")) or not os.path.exists(os.path.join(f39_dir, "M2RMKERN1.pbs")):
        failures.append("F38/F39 frozen packages modified or missing")

    result = {
        "classification": "pass" if len(failures) == 0 else "fail",
        "failures": failures
    }

    print(json.dumps(result, indent=2))
    return 0 if result["classification"] == "pass" else 1

if __name__ == "__main__":
    sys.exit(main())
