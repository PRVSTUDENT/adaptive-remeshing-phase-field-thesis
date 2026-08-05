#!/usr/bin/env python3
"""Fail-closed static validator for Stage F37 M2RMBUILD11 qualification."""

from __future__ import annotations
import os
import sys
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

def validate_f37_static_gate():
    failures = []

    # 1. Builder API check: writeInput(exactAssignment=True) prohibited, writeInput(consistencyChecking=ON) required
    builder_path = ROOT / "models/generated/mode_ii/f37_cae_python_compatibility_repair/runtime/build_f37_geometry_backed_model.py"
    if not builder_path.exists():
        failures.append("F37 builder script build_f37_geometry_backed_model.py missing")
    else:
        content = builder_path.read_text(encoding="utf-8")
        if "exactAssignment" in content:
            failures.append("Prohibited exactAssignment argument found in writeInput call")
        if "writeInput(consistencyChecking=ON)" not in content:
            failures.append("Required writeInput(consistencyChecking=ON) signature missing")
        if "from abaqusConstants import" not in content or "ON" not in content:
            failures.append("Explicit ON import from abaqusConstants missing")
        if "UNPLANNED" in content:
            failures.append("Invalid Abaqus 2023 constant UNPLANNED remains in builder")
        if "from abaqusConstants import ON, CPE4, STANDARD, STRUCTURED" not in content:
            failures.append("Builder constants are not the verified minimal Abaqus 2023 set")
        for token in (".casefold(", "pathlib", "dataclasses", "subprocess.run", "exist_ok="):
            if token in content:
                failures.append("Abaqus builder contains unsupported construct: " + token)
        for lookup in ("m.parts['Part-1']", 'm.parts["Part-1"]', "a.instances['Part-1-1']", 'a.instances["Part-1-1"]'):
            if lookup in content:
                failures.append("Builder contains direct imported repository lookup: " + lookup)
        if "from f37_runtime_compat import resolve_unique_repository_key" not in content:
            failures.append("Builder does not import the shared repository resolver")

    # 2. Check complete manifest-listed workdir staging & no '-- arguments' route in PBS script
    pbs_path = ROOT / "models/generated/mode_ii/f37_cae_python_compatibility_repair/M2RMBUILD11.pbs"
    if not pbs_path.exists():
        failures.append("M2RMBUILD11.pbs script missing")
    else:
        pbs_content = pbs_path.read_text(encoding="utf-8")
        if "M2RMBUILD11.pbs" not in pbs_content or 'cp "$F37_PACKAGE_DIR/M2RMBUILD11.pbs" .' not in pbs_content:
            failures.append("PBS script missing self-staging into WORK_DIR before SHA verification")
        if "abaqus cae noGUI=" in pbs_content and " -- " in pbs_content:
            failures.append("Prohibited '-- arguments' transport found in M2RMBUILD11.pbs")
        if "F37_SOURCE_DECK" not in pbs_content or "F37_OUTPUT_INPUT" not in pbs_content or "F37_GEOMETRY_AUDIT" not in pbs_content:
            failures.append("Required environment variables F37_SOURCE_DECK, F37_OUTPUT_INPUT, F37_GEOMETRY_AUDIT missing in PBS")
        if any("curl" in line and "|| echo" in line for line in pbs_content.splitlines()):
            failures.append("Prohibited curl || echo fallback found in PBS script")

    # 3. Check EXIT trap, verified python3, and fail-fast return-code capture.
    if pbs_path.exists():
        pbs_content = pbs_path.read_text(encoding="utf-8")
        if "on_exit" not in pbs_content or "trap on_exit EXIT" not in pbs_content:
            failures.append("Mandatory on_exit EXIT trap missing in M2RMBUILD11.pbs")
        if "term_curl_rc=$?" not in pbs_content:
            failures.append("Explicit curl return code capture term_curl_rc=$? missing")
        if "module load" not in pbs_content:
            failures.append("Module loading missing in PBS script")
        if "command -v python3" not in pbs_content or "python3 --version" not in pbs_content:
            failures.append("Standalone python3 is not explicitly resolved and version-checked")
        if re.search(r"(?m)^\s*python\s+", pbs_content):
            failures.append("Unverified standalone python invocation remains in PBS script")
        if 'cae_builder_rc="skipped"' not in pbs_content:
            failures.append("Unexecuted CAE builder is not initialized as skipped")
        if "set +e\nabaqus cae" not in pbs_content or "cae_builder_rc=$?\nset -e" not in pbs_content:
            failures.append("Actual Abaqus CAE return code is not captured outside fail-fast mode")

    # 4. Check runtime STATUS classifications (only cae_geometry_build_contract_passed / failed allowed)
    if pbs_path.exists():
        pbs_content = pbs_path.read_text(encoding="utf-8")
        if "f37_m2rmbuild11_" in pbs_content and "STATUS.json" in pbs_content:
            failures.append("Preparation/authorization classification wrongfully written to runtime STATUS.json in PBS")

    # 5. Check no Abaqus/Standard or adaptiveRemesh calls in builder or PBS
    for p in [builder_path, pbs_path]:
        if p and p.exists():
            c = p.read_text(encoding="utf-8")
            if "abaqus job=" in c.lower() or "abaqus standard" in c.lower():
                failures.append(f"Prohibited Abaqus/Standard solver invocation in {p.name}")
            if "adaptiveremesh" in c.lower():
                failures.append(f"Prohibited adaptiveRemesh call in {p.name}")

    # 6. Check Orchestrator
    orch_path = ROOT / "scripts/hpc/stage_f/submit_stage_f37_cae_build_qualification.sh"
    if not orch_path.exists():
        failures.append("Guarded orchestrator submit_stage_f37_cae_build_qualification.sh missing")
    else:
        orch_content = orch_path.read_text(encoding="utf-8")
        if "F37_ALLOW_SUBMISSION" not in orch_content or "F37_AUTHORIZE_M2RMBUILD11" not in orch_content:
            failures.append("Orchestrator missing activation or authorization gates")
        if len(re.findall(r"(?m)^JOB_ID=\$\(qsub\s", orch_content)) != 1:
            failures.append("Orchestrator must contain exactly one qsub command")

    res = {
        "classification": "pass" if len(failures) == 0 else "fail",
        "failures": failures
    }
    print(json.dumps(res, indent=2))
    return len(failures) == 0

if __name__ == "__main__":
    success = validate_f37_static_gate()
    sys.exit(0 if success else 1)
