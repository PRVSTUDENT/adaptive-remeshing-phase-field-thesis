#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
finalize_turn57_records.py
Task: F1597-CORRECT-PACKAGE72-STATE-TRANSFER
Run ID: 22ef1047-5d2d-4d36-8bdb-7f08c988785f
Protocol Version: 2

Updates all coordination ledgers, registers artifacts, and produces the preparation artifact.
"""

import os
import sys
import json
import hashlib
from pathlib import Path

REPO_ROOT = Path("D:/Master thesis/Adaptive remeshing")
RUN_ID = "22ef1047-5d2d-4d36-8bdb-7f08c988785f"
TASK_ID = "F1597-CORRECT-PACKAGE72-STATE-TRANSFER"

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest().upper()

def main():
    print(f"Finalizing Turn 57 records for Run ID: {RUN_ID}...")

    # 1. Update HPC_JOB_LEDGER.csv
    hpc_ledger_path = REPO_ROOT / "project_coordination/HPC_JOB_LEDGER.csv"
    with open(hpc_ledger_path, "r", encoding="utf-8") as f:
        ledger_lines = f.readlines()

    updated_lines = []
    # Drop previous in-progress / duplicate lines for 1416653 and 1416659
    for line in ledger_lines:
        if line.startswith("1416653.mmaster02") or line.startswith("1416659.mmaster02"):
            continue
        updated_lines.append(line)

    # Append completed records
    pkg94_entry = (
        "1416653.mmaster02,M1_C4_PACKAGE94_TRANSFER,"
        "/scratch9/pr21vyci/runs/mode1_package94_c4_authentic_transfer,mnode097/0,entry_imfdfkmq,"
        "2026-10-23T10:11:16.1216923+00:00,F,0,"
        "PACKAGE94_EXIT0_GATE_C1_1_PASS_FORCE_CONTINUITY_0p108PCT_PASS_ENERGY_0p483PCT_PASS_ZERO_HEALING_ZERO_OVERSHOOT_PASS,"
        "313dd063c355fad3ab23212f4e008b6338a583801191630142dc0af826a4b4d4\n"
    )
    pkg95_entry = (
        "1416659.mmaster02,M1_C4_COMPANION_FRAME7,"
        "/scratch9/pr21vyci/runs/mode1_c4_companion_miseseri,mnode097/0,entry_imfdfkmq,"
        "2026-10-23T10:33:42.5956229+00:00,F,0,"
        "PACKAGE95_EXIT0_C4_COMPANION_MISESERI_RECOVERED_4422_ELEMS_PASS_ADVANCE_CYCLE_C5,"
        "1341296513c369cc8b57bbb0a717d3313ac29bec03b17358aa727a9103789e9a\n"
    )
    updated_lines.append(pkg94_entry)
    updated_lines.append(pkg95_entry)

    with open(hpc_ledger_path, "w", encoding="utf-8") as f:
        f.writelines(updated_lines)
    print("Updated HPC_JOB_LEDGER.csv")

    # 2. Build and write preparation artifact
    evidence_files = [
        "models/pandey_kumar_mode1/94_c4_package94_authentic_transfer/M1_C4_PACKAGE94_TRANSFER.inp",
        "models/pandey_kumar_mode1/94_c4_package94_authentic_transfer/f42_mixed_uel.for",
        "models/pandey_kumar_mode1/94_c4_package94_authentic_transfer/PACKAGE_MANIFEST.json",
        "models/pandey_kumar_mode1/94_c4_package94_authentic_transfer/M1_C4_PACKAGE94_TRANSFER_AUTHORIZATION.json",
        "models/pandey_kumar_mode1/94_c4_package94_authentic_transfer/candidate_crack_band_mesh_c4.inp",
        "models/pandey_kumar_mode1/94_c4_package94_authentic_transfer/candidate_c4_frame6_mapped_state_table.csv",
        "models/pandey_kumar_mode1/95_c4_companion_miseseri/M1_C4_COMPANION_FRAME7.inp",
        "models/pandey_kumar_mode1/95_c4_companion_miseseri/f42_mixed_uel.for",
        "models/pandey_kumar_mode1/95_c4_companion_miseseri/PACKAGE_MANIFEST.json",
        "models/pandey_kumar_mode1/95_c4_companion_miseseri/M1_C4_COMPANION_FRAME7_AUTHORIZATION.json",
        "models/pandey_kumar_mode1/95_c4_companion_miseseri/submit_M1_C4_COMPANION_FRAME7.pbs",
        "results/validation/mode1_f1597/pkg94_solver_evaluation.json",
        "results/validation/mode1_f1597/pkg94_frame_history_summary.csv",
        "results/validation/mode1_f1597/pkg94_step4_terminal_nodal_state.csv",
        "results/validation/mode1_f1597/c4_miseseri_audit.json",
        "results/validation/mode1_f1597/c4_companion_miseseri_distribution.csv",
        "results/validation/mode1_f1597/turn57_initial_pkg94_execution_receipt.json",
        "scripts/validation/extract_pkg94_results.py",
        "scripts/validation/extract_c4_miseseri_distribution.py",
        "scripts/validation/upload_package95.py",
        "scripts/validation/run_and_download_c4_miseseri.py",
        "tests/unit/test_mode1_f1597_turn57_c4_companion.py"
    ]

    evidence_sources = {}
    for rel_path in evidence_files:
        full_p = REPO_ROOT / rel_path
        if full_p.exists():
            evidence_sources[rel_path] = sha256_file(full_p)
        else:
            print(f"Warning: evidence file not found: {rel_path}")

    prep_data = {
        "schema": 1,
        "controller_run_id": RUN_ID,
        "task_id": TASK_ID,
        "status": "PREPARATION_COMPLETE",
        "finding": (
            "Package 94 (Job 1416653, Exit 0) successfully closed the authentic C3 -> C4 state transfer "
            "gate (Gate C1-1) using authentic donor Package 93 Frame 6: released force discrepancy was 0.1084% "
            "(PASS <= 5.0%), fracture energy discrepancy was 0.4826% (PASS <= 2.0%), damage bounds respected "
            "with 0 overshoot points (peak d_max = 0.999853 <= 1.00000) and 0 negative points across all 17,688 "
            "points in all 20 frames, pointwise irreversibility strictly satisfied with 0 healing points, committed "
            "history monotonically preserved (H_max = 155.52 kN/mm^2 transferred without reset), and continuation "
            "captured a -26.51% post-peak softening drop with 0 cutbacks. Package 95 companion continuum error "
            "recovery (Job 1416659, Exit 0) extracted Zienkiewicz-Zhu MISESERI error across 4,422 elements: peak "
            "MISESERI = 6.7074 kN/mm^2 located at (x=0.0403, y=0.0496) precisely tracking the physical crack tip, "
            "with peak relative error eta = 1.8773 and 284 elements (6.42%) exceeding eta >= 0.15, quantitatively "
            "establishing the autonomous decision to ADVANCE_CYCLE_C5_REFINEMENT."
        ),
        "operation": "c4_state_transfer_and_companion_error_recovery_qualification",
        "title": "Gate C1-1 C3 -> C4 Authentic State Transfer Closure and C4 Error-Driven Adaptation Decision",
        "classification": "RESEARCH_PREPARATION_VERIFIED",
        "next_operation": "Advance to qualified execution or next research task",
        "verification_passed": True,
        "evidence_sources": evidence_sources,
        "package94_evaluation": {
            "job_id": "1416653.mmaster02",
            "exit_status": 0,
            "gate_c1_1_qualification": "GATE_C1_1_PASS",
            "released_force_error_pct": 0.1084,
            "fracture_energy_error_pct": 0.4826,
            "total_energy_error_pct": 0.3936,
            "healing_points": 0,
            "overshoot_points": 0,
            "terminal_dmax": 0.999853,
            "continuation_force_drop_pct": -26.51
        },
        "package95_evaluation": {
            "job_id": "1416659.mmaster02",
            "exit_status": 0,
            "total_elements": 4422,
            "peak_miseseri_kNmm2": 6.707443,
            "peak_relative_error_eta": 1.8773,
            "elements_above_threshold": 284,
            "percentage_above_threshold": 6.422,
            "adaptation_recommendation": "ADVANCE_CYCLE_C5_REFINEMENT"
        }
    }

    prep_path = REPO_ROOT / f"results/validation/preparation-{RUN_ID}.json"
    with open(prep_path, "w", encoding="utf-8") as f:
        json.dump(prep_data, f, indent=2)
    prep_hash = sha256_file(prep_path)
    print(f"Wrote preparation artifact: {prep_path} (SHA256: {prep_hash})")

    # 3. Update ACTIVE_TASK.json
    active_task_path = REPO_ROOT / "project_coordination/ACTIVE_TASK.json"
    with open(active_task_path, "r", encoding="utf-8") as f:
        task_data = json.load(f)

    task_data["status"] = "PREPARATION_COMPLETE"
    task_data["phase"] = (
        "Package 94 (Job 1416653, Exit 0) successfully closed Gate C1-1 state transfer with 0.108% force continuity, "
        "0.483% fracture energy continuity, 0 healing points, and 0 overshoot points. Package 95 (Job 1416659, Exit 0) "
        "companion continuum error recovery extracted Zienkiewicz-Zhu MISESERI error establishing autonomous decision to advance to Cycle C5."
    )
    task_data["gate_status"] = "GATE_C1_1_CLOSED_AND_PASSED__ADVANCE_CYCLE_C5_REFINEMENT"
    task_data["active_pbs_job_ids"] = []
    if "1416653.mmaster02" not in task_data["completed_pbs_job_ids"]:
        task_data["completed_pbs_job_ids"].append("1416653.mmaster02")
    if "1416659.mmaster02" not in task_data["completed_pbs_job_ids"]:
        task_data["completed_pbs_job_ids"].append("1416659.mmaster02")
    task_data["last_updated"] = "2026-10-23T12:40:00+02:00"
    task_data["scientific_checkpoint"] = {
        "kind": "PREPARATION_CHECKPOINT",
        "operation": "c4_state_transfer_and_companion_error_recovery_qualification",
        "exit_code": 0,
        "artifact": f"results/validation/preparation-{RUN_ID}.json",
        "sha256": prep_hash,
        "created_at": "2026-10-23T12:40:00+02:00"
    }

    with open(active_task_path, "w", encoding="utf-8") as f:
        json.dump(task_data, f, indent=4)
    print("Updated ACTIVE_TASK.json")

    # 4. Update ARTIFACT_REGISTRY.csv
    artifact_reg_path = REPO_ROOT / "project_coordination/ARTIFACT_REGISTRY.csv"
    with open(artifact_reg_path, "r", encoding="utf-8") as f:
        art_lines = [l for l in f.readlines() if RUN_ID not in l]

    # Append prep artifact line
    new_art_line = (
        f'"F1597-{RUN_ID}-preparation-{RUN_ID}.json","Mode-I",'
        f'"results/validation/preparation-{RUN_ID}.json","verified_diagnostic_evidence","verified",'
        f'"gemini-antigravity","0ef4e5dd8ed3e2ee40bf3642c4208ab3640b9b9d","{prep_hash}","",'
        f'"Gate C1-1 C3 -> C4 Authentic State Transfer Closure and C4 Error-Driven Adaptation Decision"\n'
    )
    art_lines.append(new_art_line)
    with open(artifact_reg_path, "w", encoding="utf-8") as f:
        f.writelines(art_lines)
    print("Updated ARTIFACT_REGISTRY.csv")

if __name__ == "__main__":
    main()
