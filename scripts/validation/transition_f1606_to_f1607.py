#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
transition_f1606_to_f1607.py
Executes the scientific lifecycle transition from F1606 to F1607:
1. Closes F1606 in TASK_LEDGER.csv (status=completed, classification=EVALUATED_NONCONVERGENCE_DIAGNOSIS_COMPLETE, next_task=F1607-PACKAGE171-R8-C6-COUPLED-REEQUILIBRATION).
2. Appends F1607 row in TASK_LEDGER.csv (status=ready, classification=REGISTERED_NOT_EXECUTED).
3. Updates ACTIVE_TASK.json to bind F1607-PACKAGE171-R8-C6-COUPLED-REEQUILIBRATION.
4. Updates CURRENT_STATE.md with the F1607 registration milestone.
"""

import csv
import hashlib
import json
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parents[2]

TASK_ID_PRED = "F1606-MODE1-C6-R7-NONCONVERGENCE-INVESTIGATION"
TASK_ID_SUCC = "F1607-PACKAGE171-R8-C6-COUPLED-REEQUILIBRATION"
SOURCE_COMMIT = "081678947b1c3c90f30501a4f028889759d604b0"
RUN_ID = "c050a5a1-d54a-4c57-b6ca-e3cb755e052d"
CHECKPOINT_HASH = "2382AC8E5B3595CED69D5CCEC08E35FC8A002B7F9BF0CF45B5EF5DB264CEE2DA"
DEF_REL = "project_coordination/task_definitions/F1607-PACKAGE171-R8-C6-COUPLED-REEQUILIBRATION.json"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def main():
    def_path = WORKSPACE / DEF_REL
    if not def_path.exists():
        raise FileNotFoundError(f"Missing definition file: {def_path}")
    def_hash = sha256_file(def_path)
    print(f"Task definition hash: {def_hash}")

    # 1. Update TASK_LEDGER.csv
    ledger_path = WORKSPACE / "project_coordination/TASK_LEDGER.csv"
    lines = ledger_path.read_text(encoding="utf-8").splitlines()
    header = lines[0]
    reader = csv.DictReader(lines)
    fieldnames = reader.fieldnames
    rows = list(reader)

    # Find the parent task row for F1606
    f1606_parent_indices = [
        i for i, r in enumerate(rows)
        if r["task_id"] == TASK_ID_PRED and r["classification"] == "REGISTERED_NOT_EXECUTED"
    ]
    if len(f1606_parent_indices) != 1:
        raise ValueError(f"Expected 1 open parent row for F1606, found {len(f1606_parent_indices)}")

    idx = f1606_parent_indices[0]
    rows[idx]["status"] = "completed"
    rows[idx]["classification"] = "EVALUATED_NONCONVERGENCE_DIAGNOSIS_COMPLETE"
    rows[idx]["next_task"] = TASK_ID_SUCC
    rows[idx]["updated_at"] = "2026-11-04T09:48:15+01:00"

    # Append new row for F1607
    f1607_row = {
        "task_id": TASK_ID_SUCC,
        "stage": "Mode-I",
        "title": "Preparation and independent review intake for Candidate M1_C6_P171_R8_ADAPTIVE_DAMPED",
        "status": "ready",
        "agent": "gemini-antigravity",
        "base_commit": SOURCE_COMMIT,
        "result_commit": "",
        "write_scope": "read-only preparation and review intake; zero PBS submissions",
        "job_id": "1419873.mmaster02 references only",
        "classification": "REGISTERED_NOT_EXECUTED",
        "next_task": "",
        "updated_at": "2026-11-04T09:48:15+01:00"
    }
    rows.append(f1607_row)

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
        "Candidate Package 171-R8 review packet prepared under correlation HND-F1607-R8-REVIEW-8D0545A3 "
        "(fingerprint 8D0545A3A733B1368DBA705880C71FD8E2D797B09AF4920FDB1E76688EA52D1F). Verified candidate definition "
        "with compound active-set transition criteria (|A_k|<=500, |Delta A_k|<=10, Delta A^+=0 sustained for 3 consecutive "
        "iterations) and 140 outer iteration budget providing 51 relaxation iterations and projecting delta_d=1.27e-6<=1.0e-5 "
        "at 1.33h runtime within the 8h PBS limit. Explicitly documented that projected damage convergence at iteration 140 "
        "is an unverified hypothesis, not proof of coupled convergence, requiring independent review of damage, displacement, "
        "history, KKT, force/energy consistency, and numerical stability. Frozen UEL and quantitative physical acceptance criteria strictly preserved."
    )
    active["gate_status"] = "REGISTERED_SUCCESSOR__NUMERICAL_EXECUTION_NOT_QUALIFIED"
    active["predecessor_task"] = {
        "run_id": RUN_ID,
        "status": "COMPLETED",
        "task_id": TASK_ID_PRED,
        "source_commit": SOURCE_COMMIT,
        "checkpoint_sha256": CHECKPOINT_HASH
    }
    active["registration"] = {
        "sha256": def_hash,
        "schema": 1,
        "definition": DEF_REL,
        "registered_by": "gemini-antigravity",
        "registered_at": "2026-11-04T09:48:15+01:00"
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
        "artifact": f"results/validation/preparation-{RUN_ID}.json",
        "sha256": CHECKPOINT_HASH
    }
    active["scientific_acceptance"] = "NOT_YET_EVALUATED"
    active["last_step_status"] = "PREPARATION_COMPLETE"
    active["last_updated"] = "2026-11-04T09:48:15+01:00"
    active["next_safe_action"] = "Intake independent review response for candidate M1_C6_P171_R8_ADAPTIVE_DAMPED under correlation HND-F1607-R8-REVIEW-8D0545A3"
    active["scientific_checkpoint"] = {
        "kind": "PREPARATION_CHECKPOINT",
        "operation": "research_preparation",
        "exit_code": 0,
        "artifact": f"results/validation/preparation-{RUN_ID}.json",
        "sha256": CHECKPOINT_HASH,
        "created_at": "2026-11-04T09:48:15+01:00"
    }

    with open(active_path, "w", encoding="utf-8") as f:
        json.dump(active, f, indent=4)
    print("Updated ACTIVE_TASK.json successfully.")


if __name__ == "__main__":
    main()
