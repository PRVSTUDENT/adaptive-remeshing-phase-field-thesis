#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
transition_f1607_to_f1608.py
============================
Executes the scientific lifecycle transition from F1607 to F1608:
1. Closes F1607 in TASK_LEDGER.csv (status=completed, classification=EVALUATED_INDEPENDENT_REVIEW_APPROVED, next_task=F1608-PACKAGE171-R8-C6-ADAPTIVE-REEQUILIBRATION).
2. Appends F1608 row in TASK_LEDGER.csv (status=ready, classification=REGISTERED_NOT_EXECUTED).
3. Updates ACTIVE_TASK.json to bind F1608-PACKAGE171-R8-C6-ADAPTIVE-REEQUILIBRATION.
4. Updates CURRENT_STATE.md with the F1608 registration milestone.
"""

import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

WORKSPACE = Path(__file__).resolve().parents[2]

TASK_ID_PRED = "F1607-PACKAGE171-R8-C6-COUPLED-REEQUILIBRATION"
TASK_ID_SUCC = "F1608-PACKAGE171-R8-C6-ADAPTIVE-REEQUILIBRATION"
DEF_REL = "project_coordination/task_definitions/F1608-PACKAGE171-R8-C6-ADAPTIVE-REEQUILIBRATION.json"
RUN_ID = "50098952-dcad-4686-94e2-1ca422f14dd1"
CHECKPOINT_REL = f"results/validation/preparation-{RUN_ID}.json"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def main():
    def_path = WORKSPACE / DEF_REL
    if not def_path.exists():
        raise FileNotFoundError(f"Missing definition file: {def_path}")
    def_hash = sha256_file(def_path)
    print(f"Successor task definition hash: {def_hash}")

    cp_path = WORKSPACE / CHECKPOINT_REL
    if not cp_path.exists():
        raise FileNotFoundError(f"Missing checkpoint file: {cp_path}")
    cp_hash = sha256_file(cp_path)
    print(f"Predecessor checkpoint hash: {cp_hash}")

    now_iso = datetime.now(timezone.utc).astimezone().isoformat()

    # Get current git commit as base_commit
    import subprocess
    cmd = ["git", "-C", str(WORKSPACE), "rev-parse", "HEAD"]
    source_commit = subprocess.check_output(cmd, text=True).strip()
    print(f"Source commit: {source_commit}")

    # 1. Update TASK_LEDGER.csv
    ledger_path = WORKSPACE / "project_coordination/TASK_LEDGER.csv"
    lines = ledger_path.read_text(encoding="utf-8").splitlines()
    header = lines[0]
    reader = csv.DictReader(lines)
    fieldnames = reader.fieldnames
    rows = list(reader)

    # Find the parent task row for F1607
    f1607_parent_indices = [
        i for i, r in enumerate(rows)
        if r["task_id"] == TASK_ID_PRED and r["classification"] == "REGISTERED_NOT_EXECUTED"
    ]
    if len(f1607_parent_indices) != 1:
        raise ValueError(f"Expected 1 open parent row for F1607, found {len(f1607_parent_indices)}")

    idx = f1607_parent_indices[0]
    rows[idx]["status"] = "completed"
    rows[idx]["classification"] = "EVALUATED_INDEPENDENT_REVIEW_APPROVED"
    rows[idx]["next_task"] = TASK_ID_SUCC
    rows[idx]["updated_at"] = now_iso

    # Append new row for F1608
    f1608_row = {
        "task_id": TASK_ID_SUCC,
        "stage": "Mode-I",
        "title": "Package 171-R8 C6 Coupled PDAS Re-Equilibration Implementation and Technical Qualification",
        "status": "ready",
        "agent": "gemini-antigravity",
        "base_commit": source_commit,
        "result_commit": "",
        "write_scope": "models/pandey_kumar_mode1/171_c6_package171_r8_c3_0_adaptive_reequilibration;scripts/state_transfer;tests/unit;project_coordination",
        "job_id": "1419873.mmaster02 references only",
        "classification": "REGISTERED_NOT_EXECUTED",
        "next_task": "",
        "updated_at": now_iso
    }
    rows.append(f1608_row)

    # Write back TASK_LEDGER.csv
    import io
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=fieldnames, lineterminator="\n", extrasaction="ignore")
    writer.writeheader()
    writer.writerows(rows)
    ledger_path.write_text(output.getvalue(), encoding="utf-8")
    print("Updated TASK_LEDGER.csv successfully.")

    # 2. Update ACTIVE_TASK.json
    active_path = WORKSPACE / "project_coordination/ACTIVE_TASK.json"
    with open(active_path, "r", encoding="utf-8") as f:
        active = json.load(f)

    active["task_id"] = TASK_ID_SUCC
    active["agent"] = "gemini-antigravity"
    active["status"] = "READY_READ_ONLY_EVALUATION"
    active["phase"] = (
        "Registered successor task F1608-PACKAGE171-R8-C6-ADAPTIVE-REEQUILIBRATION following authenticated "
        "independent review APPROVE decision under correlation HND-F1607-R8-REVIEW-8D0545A3 (fingerprint "
        "8D0545A3A733B1368DBA705880C71FD8E2D797B09AF4920FDB1E76688EA52D1F). Successor scope: technical "
        "qualification, coupled driver implementation (driver_package171_r8_c6_coupled_pdas.py) with compound "
        "active-set transition criteria (|A_k|<=500, |Delta A_k|<=10, Delta A^+=0 sustained for 3 consecutive iterations), "
        "two-phase damping (omega_d=0.50 -> 0.85), 140 outer iteration budget, 5% residual growth rollback, and real Abaqus "
        "datachecks Exit 0 before PBS submission. Strictly 0 PBS submissions authorized until qualification complete."
    )
    active["gate_status"] = "REGISTERED_SUCCESSOR__NUMERICAL_EXECUTION_NOT_QUALIFIED"
    active["predecessor_task"] = {
        "run_id": RUN_ID,
        "status": "COMPLETED",
        "task_id": TASK_ID_PRED,
        "source_commit": source_commit,
        "checkpoint_sha256": cp_hash
    }
    active["registration"] = {
        "sha256": def_hash,
        "schema": 1,
        "definition": DEF_REL,
        "registered_by": "gemini-antigravity",
        "registered_at": now_iso
    }
    active["scientific_checkpoint_required"] = True
    active["scientific_operation"] = ""
    active["scientific_operation_id"] = "research_preparation"
    active["max_new_pbs_submissions"] = 0
    active["lifecycle"] = {
        "scientific_execution_started": False,
        "predecessor_replay_allowed": False,
        "state": "ACTIVE"
    }
    active["preserved_predecessor"] = {
        "task_id": TASK_ID_PRED,
        "status": "COMPLETED",
        "scientific_acceptance": "FAIL_COUPLED_NONCONVERGENCE",
        "artifact": CHECKPOINT_REL,
        "sha256": cp_hash
    }
    active["scientific_acceptance"] = "NOT_YET_EVALUATED"
    active["last_step_status"] = "PREPARATION_COMPLETE"
    active["last_updated"] = now_iso
    active["next_safe_action"] = (
        "Implement R8 coupled driver with compound active-set transition criteria (|A_k| <= 500, |Delta A_k| <= 10, "
        "Delta A^+ = 0 for 3 consecutive iterations; 140 outer iterations), run unit tests, assemble Package 171-R8, "
        "and run authentic Abaqus datachecks Exit 0."
    )
    active["scientific_checkpoint"] = {
        "kind": "PREPARATION_CHECKPOINT",
        "operation": "research_preparation",
        "exit_code": 0,
        "artifact": CHECKPOINT_REL,
        "sha256": cp_hash,
        "created_at": now_iso
    }

    with open(active_path, "w", encoding="utf-8") as f:
        json.dump(active, f, indent=4)
    print("Updated ACTIVE_TASK.json successfully.")

    # 3. Update CURRENT_STATE.md
    cs_path = WORKSPACE / "project_coordination/CURRENT_STATE.md"
    if cs_path.exists():
        cs_content = cs_path.read_text(encoding="utf-8")
        entry = (
            f"\n\n### Lifecycle Milestone: F1607 -> F1608 Transition ({now_iso[:10]})\n"
            f"- **Closed Task**: `{TASK_ID_PRED}` (classification: `EVALUATED_INDEPENDENT_REVIEW_APPROVED`)\n"
            f"- **Registered Successor**: `{TASK_ID_SUCC}`\n"
            f"- **Reviewed Operation**: `{active['scientific_operation_id']}`\n"
            f"- **Correlation**: `HND-F1607-R8-REVIEW-8D0545A3` (fingerprint `8D0545A3A733B1368DBA705880C71FD8E2D797B09AF4920FDB1E76688EA52D1F`)\n"
            f"- **Predecessor Checkpoint**: `{CHECKPOINT_REL}` (`{cp_hash}`)\n"
            f"- **Scope**: Technical qualification and driver implementation for Candidate M1_C6_P171_R8_ADAPTIVE_DAMPED on non-coarsened C6 mesh (15,252 quads);\n"
            f"  compound active-set condition (|A_k| <= 500, |Delta A_k| <= 10, Delta A^+ = 0 for 3 iterations), two-phase damping (0.50 -> 0.85), 140 outer budget, 5% residual growth rollback;\n"
            f"  strictly 0 PBS submissions until technical qualification and authentic Abaqus datachecks pass.\n"
        )
        cs_path.write_text(cs_content + entry, encoding="utf-8")
        print("Updated CURRENT_STATE.md successfully.")


if __name__ == "__main__":
    main()
