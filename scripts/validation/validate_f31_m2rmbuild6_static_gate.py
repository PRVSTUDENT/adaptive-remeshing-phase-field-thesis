#!/usr/bin/env python3
"""Fail-closed static validator for Stage F31 M2RMBUILD6 qualification."""

from __future__ import annotations
import os
import sys
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

def validate_f31_static_gate():
    failures = []

    # 1. Builder API check: writeInput(exactAssignment=True) prohibited, writeInput(consistencyChecking=ON) required
    builder_path = ROOT / "models/generated/mode_ii/f31_cae_runtime_gate_repair/runtime/build_f31_geometry_backed_model.py"
    if not builder_path.exists():
        failures.append("F31 builder script build_f31_geometry_backed_model.py missing")
    else:
        content = builder_path.read_text(encoding="utf-8")
        if "exactAssignment" in content:
            failures.append("Prohibited exactAssignment argument found in writeInput call")
        if "writeInput(consistencyChecking=ON)" not in content:
            failures.append("Required writeInput(consistencyChecking=ON) signature missing")
        if "from abaqusConstants import" not in content or "ON" not in content:
            failures.append("Explicit ON import from abaqusConstants missing")

    # 2. Check no '-- arguments' route in PBS script
    pbs_path = ROOT / "models/generated/mode_ii/f31_cae_runtime_gate_repair/M2RMBUILD6.pbs"
    if not pbs_path.exists():
        failures.append("M2RMBUILD6.pbs script missing")
    else:
        pbs_content = pbs_path.read_text(encoding="utf-8")
        if "abaqus cae noGUI=" in pbs_content and " -- " in pbs_content:
            failures.append("Prohibited '-- arguments' transport found in M2RMBUILD6.pbs")
        if "F31_SOURCE_DECK" not in pbs_content or "F31_OUTPUT_INPUT" not in pbs_content or "F31_GEOMETRY_AUDIT" not in pbs_content:
            failures.append("Required environment variables F31_SOURCE_DECK, F31_OUTPUT_INPUT, F31_GEOMETRY_AUDIT missing in PBS")
        if any("curl" in line and "|| echo" in line for line in pbs_content.splitlines()):
            failures.append("Prohibited curl || echo fallback found in PBS script")

    # 3. Check EXIT trap covers early failures & captures curl return code
    if pbs_path.exists():
        pbs_content = pbs_path.read_text(encoding="utf-8")
        if "on_exit" not in pbs_content or "trap on_exit EXIT" not in pbs_content:
            failures.append("Mandatory on_exit EXIT trap missing in M2RMBUILD6.pbs")
        if "term_curl_rc=$?" not in pbs_content:
            failures.append("Explicit curl return code capture term_curl_rc=$? missing")

    # 4. Check runtime STATUS classifications (only cae_geometry_build_contract_passed / failed allowed)
    if pbs_path.exists():
        pbs_content = pbs_path.read_text(encoding="utf-8")
        if "f31_m2rmbuild6_" in pbs_content and "STATUS.json" in pbs_content:
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
    orch_path = ROOT / "scripts/hpc/stage_f/submit_stage_f31_cae_build_qualification.sh"
    if not orch_path.exists():
        failures.append("Guarded orchestrator submit_stage_f31_cae_build_qualification.sh missing")
    else:
        orch_content = orch_path.read_text(encoding="utf-8")
        if "F31_ALLOW_SUBMISSION" not in orch_content or "F31_AUTHORIZE_M2RMBUILD6" not in orch_content:
            failures.append("Orchestrator missing activation or authorization gates")

    # 7. Check decision JSON classification
    dec_path = ROOT / "runs/hpc/stage_f/f31_m2rmbuild6_static_gate/F31_DECISION.json"
    if dec_path.exists():
        dec_data = json.loads(dec_path.read_text(encoding="utf-8"))
        cls_name = dec_data.get("classification", "")
        if cls_name == "f31_m2rmbuild6_static_clean_linux_qualified_not_authorized":
            failures.append("f31_m2rmbuild6_static_clean_linux_qualified_not_authorized claimed without clean Linux qualification")

    res = {
        "classification": "pass" if len(failures) == 0 else "fail",
        "failures": failures
    }
    print(json.dumps(res, indent=2))
    return len(failures) == 0

if __name__ == "__main__":
    success = validate_f31_static_gate()
    sys.exit(0 if success else 1)
