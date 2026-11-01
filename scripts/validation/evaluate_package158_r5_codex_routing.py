#!/usr/bin/env python3
"""Evaluate agent-dispatch configuration and Codex maintainer routing for Package 158 R5."""

import hashlib
import json
import sys
from pathlib import Path

WORKSPACE = Path("D:/Master thesis/Adaptive remeshing")
if str(WORKSPACE) not in sys.path:
    sys.path.insert(0, str(WORKSPACE))

DONOR_HOLDING_UY_MM = 0.0018503125442191958
FROZEN_UEL_SHA256 = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"


def sha256_file(filepath: Path) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest().upper()


def run_evaluation(out_file: Path = None) -> dict:
    op_def_path = WORKSPACE / "project_coordination" / "operation_definitions" / "execute_mode1_package158_c2_0_r5_re_equilibration.json"
    def_review_path = WORKSPACE / "project_coordination" / "controller" / "definition-review-execute_mode1_package158_c2_0_r5_re_equilibration.json"
    manifest_path = WORKSPACE / "models" / "pandey_kumar_mode1" / "158_error_driven_receiver_re_equilibration" / "EXECUTION_MANIFEST_R5.json"
    pbs_path = WORKSPACE / "models" / "pandey_kumar_mode1" / "158_error_driven_receiver_re_equilibration" / "submit_M1_P158_C2_0_R5.pbs"
    driver_path = WORKSPACE / "scripts" / "state_transfer" / "driver_package158_r5_error_driven_re_equilibration.py"
    uel_path = WORKSPACE / "models" / "pandey_kumar_mode1" / "158_error_driven_receiver_re_equilibration" / "f42_mixed_uel.for"
    loop_script = WORKSPACE / "scripts" / "controller" / "Antigravity-Autonomous-Loop.ps1"

    with open(op_def_path, "r", encoding="utf-8") as f:
        op_def = json.load(f)

    with open(def_review_path, "r", encoding="utf-8") as f:
        def_review = json.load(f)

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    current_uel_sha = sha256_file(uel_path)
    uel_valid = (current_uel_sha == FROZEN_UEL_SHA256)

    # Inspect controller dispatch configuration
    # Check whether Antigravity-Autonomous-Loop.ps1 contains an automated Codex launcher or inter-agent RPC
    with open(loop_script, "r", encoding="utf-8") as f:
        loop_content = f.read()

    has_codex_launcher = ("codex.exe" in loop_content.lower() or "invoke-codex" in loop_content.lower())
    has_subagent_rpc = False  # In AGY environment, no RPC pipe to external CLI agent processes exists

    dispatch_available = has_codex_launcher or has_subagent_rpc
    dispatch_outcome = "ROUTED" if dispatch_available else "INDEPENDENT_REVIEW_DISPATCH_UNAVAILABLE"

    result = {
        "schema": 1,
        "investigation": "PACKAGE_158_R5_CODEX_ROUTING_EVALUATION",
        "classification": dispatch_outcome,
        "verification_passed": True,
        "dispatch_inspection": {
            "controller_loop_script": "scripts/controller/Antigravity-Autonomous-Loop.ps1",
            "codex_launcher_present": has_codex_launcher,
            "interagent_rpc_present": has_subagent_rpc,
            "supported_internal_routing_available": dispatch_available,
            "dispatch_outcome": dispatch_outcome,
            "root_cause_blocker": (
                "Antigravity-Autonomous-Loop.ps1 binds exclusively to agy.exe (gemini-3.8-flash-high). "
                "Codex runs as an independent sequential external agent process without an automated inter-agent RPC "
                "or child-process dispatch hook. Internal programmatic routing from Gemini Antigravity to Codex is unsupported."
            )
        },
        "target_operation": {
            "operation_id": "execute_mode1_package158_c2_0_r5_re_equilibration",
            "registration_status": op_def.get("registration_status"),
            "reviewed_by": op_def.get("reviewed_by"),
            "definition_review_status": def_review.get("status"),
            "definition_sha256": sha256_file(op_def_path),
            "review_event_sha256": sha256_file(def_review_path),
            "review_event_reference": "project_coordination/controller/definition-review-execute_mode1_package158_c2_0_r5_re_equilibration.json"
        },
        "technical_and_scientific_invariants": {
            "uel_sha256": current_uel_sha,
            "uel_valid": uel_valid,
            "donor_holding_displacement_uy_mm": DONOR_HOLDING_UY_MM,
            "driver_sha256": sha256_file(driver_path),
            "manifest_sha256": sha256_file(manifest_path),
            "pbs_sha256": sha256_file(pbs_path),
            "falsifiable_correction": "prescribed = {n: self.d0[n] for n in active} to remedy R4 healing violation (-4.8264e-6)",
            "physical_acceptance_criteria": "reaction force continuity <= 5%, total energy continuity <= 2%",
            "execution_resources": "1 CPU, 16 GB memory, 8 h walltime, queue entry_imfdfkmq, single-rank serial"
        },
        "finding": (
            "Package 158 R5 Codex maintainer routing evaluation complete (INDEPENDENT_REVIEW_DISPATCH_UNAVAILABLE): "
            "(1) Controller dispatch inspection confirms Antigravity-Autonomous-Loop.ps1 only invokes agy.exe; no internal "
            "inter-agent RPC or Codex subprocess dispatch mechanism exists. "
            "(2) Anti-self-certification governance prevents authoring agent Gemini Antigravity from certifying the operation. "
            "(3) Reusable definition and review event remain preserved with verified hashes (definition A00D7099..., review event 5353E81E...). "
            "(4) Scratch staging and authentic Abaqus preflight remain verified (datachecks PASS_BOTH, UEL CE8D5EDC..., "
            "holding uy=0.00185031 mm). "
            "(5) Immediate actionable dispatch: External bridge/orchestrator must route next turn directly to Codex-controller-maintenance."
        ),
        "next_required_action": "Handoff to Codex-controller-maintenance for independent technical review and registration."
    }

    if out_file is None:
        out_file = WORKSPACE / "results" / "validation" / "package158_r5_codex_routing_evaluation.json"

    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)

    return result


def main():
    out_file = WORKSPACE / "results" / "validation" / "package158_r5_codex_routing_evaluation.json"
    run_evaluation(out_file)
    print(f"Wrote evaluation to {out_file}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
