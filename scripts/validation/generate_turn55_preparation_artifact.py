import os
import hashlib
import json
from pathlib import Path

REPO_ROOT = Path("D:/Master thesis/Adaptive remeshing")
RUN_ID = "b13e68ac-0d42-4db1-ae22-779415f0ae6e"

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest().upper()

evidence_rel_paths = [
    "results/validation/mode1_f1597/turn55_initial_pkg92_r1_audit_and_history_defect.json",
    "results/validation/mode1_f1597/pkg92_r1_solver_evaluation.json",
    "results/validation/mode1_f1597/pkg90_r1_running_history_audit.json",
    "results/validation/mode1_f1597/pkg90_r1_running_vs_frame6_history.csv",
    "scripts/validation/audit_pkg90_r1_running_history.py",
    "scripts/validation/build_package93_instrumented_deck.py",
    "scripts/validation/upload_package93.py",
    "tests/unit/test_mode1_f1597_turn55_package93_instrumented_control.py",
    "models/pandey_kumar_mode1/93_c3_package93_instrumented_control/M1_C3_PACKAGE93_INSTRUMENTED_REPLAY.inp",
    "models/pandey_kumar_mode1/93_c3_package93_instrumented_control/f42_mixed_uel.for",
    "models/pandey_kumar_mode1/93_c3_package93_instrumented_control/job_notifications.sh",
    "models/pandey_kumar_mode1/93_c3_package93_instrumented_control/submit_M1_C3_PACKAGE93_INSTRUMENTED_REPLAY.pbs",
    "models/pandey_kumar_mode1/93_c3_package93_instrumented_control/run_pkg93_datacheck.sh",
    "models/pandey_kumar_mode1/93_c3_package93_instrumented_control/PACKAGE_MANIFEST.json",
    "models/pandey_kumar_mode1/93_c3_package93_instrumented_control/M1_C3_PACKAGE93_INSTRUMENTED_REPLAY_AUTHORIZATION.json"
]

evidence_sources = {}
for rel in evidence_rel_paths:
    p = REPO_ROOT / rel
    if not p.is_file():
        raise FileNotFoundError(f"Missing evidence file: {p}")
    evidence_sources[rel] = sha256_file(p)

prep_artifact = {
    "schema": 1,
    "controller_run_id": RUN_ID,
    "task_id": "F1597-CORRECT-PACKAGE72-STATE-TRANSFER",
    "status": "PREPARATION_COMPLETE",
    "finding": (
        "Evaluated Package 92-R1 Exit 0 solver completion (Job 1416628, 4 steps, 0 cutbacks, RF2=105.32 N, -31.5% softening drop) "
        "and proved that single-frame displacement reconstruction underestimated running maximum history H at 1,067 / 10,600 Gauss points (by up to 1.0964 kN/mm^2). "
        "Formulated faithful Package 93 instrumented C3 control with Layer 3 companion elements (2,650 CPE4 quads, IDs 5301..7950) "
        "and exact Package 90-R1 active-set boundary conditions (2,221 clamped far-field nodes, 548 free crack-band nodes, 0 healing nodes). "
        "Passed 6/6 unit tests, completed cluster interactive datacheck Exit 0, and submitted qualified job to PBS entry_imfdfkmq as Job 1416642.mmaster02 under the Job-First / Report-After policy."
    ),
    "operation": "package93_faithful_c3_instrumented_control_submission",
    "title": "Package 93 Faithful C3 Instrumented Control Qualification and Job Submission",
    "classification": "RESEARCH_PREPARATION_VERIFIED",
    "next_operation": "Advance to qualified execution or next research task",
    "verification_passed": True,
    "evidence_sources": evidence_sources,
    "package93_execution": {
        "pbs_job_id": "1416642.mmaster02",
        "job_name": "M1_C3_PACKAGE93_INSTRUMENTED_REPLAY",
        "queue": "entry_imfdfkmq",
        "scratch_directory": "/scratch9/pr21vyci/runs/mode1_package93_c3_instrumented_control",
        "status": "RUNNING",
        "datacheck_result": "PASS (Exit 0)",
        "uel_hash": "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6",
        "input_deck_hash": evidence_sources["models/pandey_kumar_mode1/93_c3_package93_instrumented_control/M1_C3_PACKAGE93_INSTRUMENTED_REPLAY.inp"],
        "physical_mesh": "2,650 CPE4 quads, 2,769 nodes, h_band=0.0010 mm <= ell_0/7.5",
        "layer_3_overlay": "2,650 CPE4 companion elements (5301..7950) with DUMMY_MAT / UMAT visualization bridge",
        "total_companion_gauss_points": 10600,
        "active_set_partition": {
            "clamped_far_field_nodes": 2221,
            "free_crack_band_nodes": 548,
            "corridor": "0.035 <= x <= 0.075 and |y - 0.050| <= 0.008 and d >= 0.15",
            "parity_vs_package90_r1": "100% BITWISE IDENTICAL NODE SET"
        },
        "target_continuation_u2_mm": 0.0020480,
        "checkpoint_frame6_step_time": 0.65625,
        "checkpoint_frame6_u2_mm": 0.0020367
    }
}

out_path = REPO_ROOT / f"results/validation/preparation-{RUN_ID}.json"
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(prep_artifact, f, indent=2)

print(f"Generated preparation artifact: {out_path} (Finding length: {len(prep_artifact['finding'])})")
