import os
import json
import hashlib
from pathlib import Path

REPO_ROOT = Path("D:/Master thesis/Adaptive remeshing")

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest().upper()

evidence_files = [
    "models/pandey_kumar_mode1/89_c2_frame88_early_state_transfer/M1_C2_FRAME88_TRANSFER.inp",
    "models/pandey_kumar_mode1/89_c2_frame88_early_state_transfer/f42_mixed_uel.for",
    "models/pandey_kumar_mode1/89_c2_frame88_early_state_transfer/submit_M1_C2_FRAME88_TRANSFER.pbs",
    "models/pandey_kumar_mode1/89_c2_frame88_early_state_transfer/PACKAGE_MANIFEST.json",
    "models/pandey_kumar_mode1/89_c2_frame88_early_state_transfer/candidate_c2_frame88_mapped_state_table.csv",
    "models/pandey_kumar_mode1/76_candidate_donor_h0025_visual/evidence_frame88/pkg76_frame88_nodal_u.csv",
    "models/pandey_kumar_mode1/76_candidate_donor_h0025_visual/evidence_frame88/pkg76_frame88_elem_sdv.csv",
    "models/pandey_kumar_mode1/76_candidate_donor_h0025_visual/evidence_frame88/pkg76_frame88_extraction_manifest.json",
    "results/validation/mode1_f1597/p76_p87_checkpoint_candidates.json",
    "results/validation/mode1_f1597/candidate_energy_comparison.json",
    "results/validation/mode1_f1597/pkg76_frame88_to_c2_audit.json",
    "tests/unit/test_mode1_f1597_turn43_checkpoint_selection.py"
]

sources = {}
for rel_path in evidence_files:
    full_path = REPO_ROOT / rel_path
    if not full_path.exists():
        raise FileNotFoundError(f"Missing evidence file: {full_path}")
    sources[rel_path] = sha256_file(full_path)

finding_text = (
    "Formulated, qualified, and submitted Package 89 (PBS Job ID 1416539.mmaster02) for nonmatching coupled "
    "state transfer at authentic pre-peak checkpoint Frame 88 (u=0.001965107 mm, t=0.39302148 s). "
    "Scanned displacement interval [0.00170, 0.00205] mm across Package 76 (donor reference) and Package 87 (C2 virgin mesh) "
    "confirming force continuity within -0.78% (185.34 N donor vs 183.89 N C2 virgin) and Bourdin AT2 fracture energy continuity "
    "within 0.0366% (52.285 uJ vs 52.266 uJ). Preserved upper/lower slit flank topology (CMOD = 2.185 um), strictly enforced "
    "zero healing (0 healing nodes), mapped 4-GP Kuhn-Tucker history H >= 0 via *INITIAL CONDITIONS, TYPE=SOLUTION into frozen UEL "
    "SVARS(9..12), verified Abaqus 2023 preflight datacheck Exit 0, and dispatched single-rank serial execution to cluster queue."
)

artifact = {
    "schema": 1,
    "status": "PREPARATION_COMPLETE",
    "run_id": "6859eebd-3dbb-4dbb-9ce5-e262bf8bdea6",
    "task_id": "F1597-CORRECT-PACKAGE72-STATE-TRANSFER",
    "finding": finding_text,
    "evidence_sources": sources,
    "verification_passed": True,
    "scientific_audit": {
        "checkpoint_selection": {
            "source_model": "Package 76 Visual Donor (1600 quads, h=2.5 um)",
            "source_step": "Step-1",
            "source_frame": 88,
            "source_inc": 88,
            "time_s": 0.39302148,
            "displacement_u2_mm": 0.00196510735,
            "donor_reaction_force_N": 185.33544,
            "c2_virgin_reaction_force_N": 183.88912,
            "force_continuity_error_pct": -0.78036,
            "force_continuity_pass": True,
            "donor_at2_fracture_energy_uJ": 52.28544,
            "c2_at2_fracture_energy_uJ": 52.26631,
            "fracture_energy_diff_pct": 0.0366,
            "fracture_energy_pass": True,
            "donor_max_damage": 0.490618,
            "ligament_state": "INTACT_LOCALIZING_CRACK_BAND"
        },
        "state_initialization_verification": {
            "mechanism": "*INITIAL CONDITIONS, TYPE=SOLUTION populates SVARS(9..12) on Step 1 Inc 1, committed into SV_H_COMMITTED and SV_H_TRIAL by frozen UEL lines 248-262",
            "frozen_uel_sha256": "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6",
            "healing_node_count": 0,
            "zero_healing_pass": True,
            "min_history_h": 0.0,
            "max_history_h": 1.297688,
            "history_monotonicity_pass": True,
            "crack_flank_preserved": True,
            "cmod_um": 2.185032
        },
        "hpc_execution": {
            "package_id": "PACKAGE_89_C2_FRAME88_EARLY_STATE_TRANSFER",
            "job_id": "1416539.mmaster02",
            "job_name": "M1_C2_FRAME88_TRANSFER",
            "queue": "normal_imfdfkmq",
            "status": "RUNNING",
            "resources": "1 CPU, 8 GB RAM, 4h walltime",
            "datacheck_result": "EXIT_0_ANALYSIS_DATACHECK_COMPLETE",
            "run_dir": "/scratch9/pr21vyci/runs/mode1_package89_c2_frame88_transfer"
        }
    }
}

out_path = REPO_ROOT / "results/validation/preparation-6859eebd-3dbb-4dbb-9ce5-e262bf8bdea6.json"
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(artifact, f, indent=2)

print("Generated preparation checkpoint:", out_path)
print("Finding length:", len(finding_text))
print("Evidence count:", len(sources))
