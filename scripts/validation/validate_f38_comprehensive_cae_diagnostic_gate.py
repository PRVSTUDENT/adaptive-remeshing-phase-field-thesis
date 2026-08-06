#!/usr/bin/env python3
"""Fail-closed static validator for Stage F38 M2RMDIAG1 comprehensive CAE phase diagnostic."""

from __future__ import annotations
import os
import sys
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

def validate_f38_static_gate():
    failures = []

    # 1. Entrypoint checks
    entry_path = ROOT / "models/generated/mode_ii/f38_comprehensive_cae_diagnostic_matrix/runtime/run_f38_cae_diagnostic.py"
    if not entry_path.exists():
        failures.append("F38 entrypoint run_f38_cae_diagnostic.py missing")
    else:
        content = entry_path.read_text(encoding="utf-8")
        if "__file__" in content:
            failures.append("Prohibited __file__ token found in run_f38_cae_diagnostic.py")
        if "F38_RUNTIME_DIR" not in content:
            failures.append("Mandatory F38_RUNTIME_DIR requirement missing in entrypoint")
        if "f38_cae_diagnostic_matrix" not in content:
            failures.append("Import of f38_cae_diagnostic_matrix missing in entrypoint")

    # 2. Diagnostic matrix module checks
    matrix_path = ROOT / "models/generated/mode_ii/f38_comprehensive_cae_diagnostic_matrix/runtime/f38_cae_diagnostic_matrix.py"
    if not matrix_path.exists():
        failures.append("F38 diagnostic matrix module f38_cae_diagnostic_matrix.py missing")
    else:
        m_content = matrix_path.read_text(encoding="utf-8")
        if "write_matrix(matrix" not in m_content:
            failures.append("Matrix must be written after every phase in f38_cae_diagnostic_matrix.py")
        if "import_fresh_model" not in m_content:
            failures.append("Fresh model import helper missing in f38_cae_diagnostic_matrix.py")
        if "assembly.features" not in m_content or "assembly.instances" not in m_content:
            failures.append("Assembly features and instances must be inventoried separately")
        if "accepted_variables" not in m_content:
            failures.append("Output variables must be probed individually")
        for probe in ("F38_IMPORT_PROBE", "F38_GEOMETRY_PROBE", "F38_MESH_PROBE", "F38_INSTANCE_PROBE", "F38_CRACK_PROBE", "F38_OUTPUT_PROBE", "F38_WRITE_INPUT_PROBE"):
            if probe not in m_content:
                failures.append(f"Independent model probe {probe} missing in diagnostic matrix")

    # 3. PBS Script checks
    pbs_path = ROOT / "models/generated/mode_ii/f38_comprehensive_cae_diagnostic_matrix/M2RMDIAG1.pbs"
    if not pbs_path.exists():
        failures.append("M2RMDIAG1.pbs script missing")
    else:
        pbs_content = pbs_path.read_text(encoding="utf-8")
        if "M2RMDIAG1.pbs" not in pbs_content or 'cp "$F38_PACKAGE_DIR/M2RMDIAG1.pbs" .' not in pbs_content:
            failures.append("PBS script missing self-staging into WORK_DIR")
        if "abaqus cae noGUI=" in pbs_content and " -- " in pbs_content:
            failures.append("Prohibited '-- arguments' transport found in M2RMDIAG1.pbs")
        if "F38_RUNTIME_DIR" not in pbs_content or "F38_SOURCE_DECK" not in pbs_content:
            failures.append("Required environment variables F38_RUNTIME_DIR or F38_SOURCE_DECK missing in PBS")

    # 4. Prohibited solver / remesh / execution calls
    for p in [entry_path, matrix_path, pbs_path]:
        if p and p.exists():
            c = p.read_text(encoding="utf-8")
            if "abaqus job=" in c.lower() or "abaqus standard" in c.lower():
                failures.append(f"Prohibited Abaqus/Standard solver invocation in {p.name}")
            if "adaptiveremesh" in c.lower():
                failures.append(f"Prohibited adaptiveRemesh call in {p.name}")

    # 5. Orchestrator checks
    orch_path = ROOT / "scripts/hpc/stage_f/submit_stage_f38_cae_diagnostic.sh"
    if not orch_path.exists():
        failures.append("Guarded orchestrator submit_stage_f38_cae_diagnostic.sh missing")
    else:
        orch_content = orch_path.read_text(encoding="utf-8")
        if "F38_ALLOW_SUBMISSION" not in orch_content or "F38_AUTHORIZE_M2RMDIAG1" not in orch_content:
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
    success = validate_f38_static_gate()
    sys.exit(0 if success else 1)
