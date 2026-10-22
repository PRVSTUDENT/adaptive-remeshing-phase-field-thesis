#!/usr/bin/env python3
import json
import hashlib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PKG80_DIR = REPO_ROOT / "models/pandey_kumar_mode1/80_candidate_c2_peak_preserved_reequilibration"

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest().lower()

def main():
    inp_file = PKG80_DIR / "M1_C2_PEAK_PRESERVED_REEQUIL.inp"
    uel_file = PKG80_DIR / "f42_mixed_uel.for"
    notif_file = PKG80_DIR / "job_notifications.sh"
    pbs_file = PKG80_DIR / "submit_M1_C2_PEAK_PRESERVED_REEQUIL.pbs"
    dat_file = PKG80_DIR / "M1_C2_PEAK_PRESERVED_REEQUIL_DC.dat"
    table_file = REPO_ROOT / "models/pandey_kumar_mode1/candidate_c2_peak_preserved_mapped_table.csv"

    inp_hash = sha256_file(inp_file)
    uel_hash = sha256_file(uel_file)
    notif_hash = sha256_file(notif_file)
    pbs_hash = sha256_file(pbs_file)
    dat_hash = sha256_file(dat_file)
    table_hash = sha256_file(table_file)

    manifest = {
        "schema": 1,
        "task_id": "F1597-CORRECT-PACKAGE72-STATE-TRANSFER",
        "package": "Package 80",
        "model": "M1_C2_PEAK_PRESERVED_REEQUIL",
        "created_at": "2026-10-22T16:20:00+02:00",
        "job_name": "M1_C2_PEAK_PRESERVED_REEQUIL",
        "pbs_script": "submit_M1_C2_PEAK_PRESERVED_REEQUIL.pbs",
        "pbs_script_sha256": pbs_hash.upper(),
        "input_deck": "M1_C2_PEAK_PRESERVED_REEQUIL.inp",
        "input_deck_sha256": inp_hash.upper(),
        "user_subroutine": "f42_mixed_uel.for",
        "user_subroutine_sha256": uel_hash.upper(),
        "mapped_table": "candidate_c2_peak_preserved_mapped_table.csv",
        "mapped_table_sha256": table_hash.upper(),
        "resources": {
            "cpus": 1,
            "memory_gb": 8,
            "walltime_hours": 4,
            "queue": "entry_imfdfkmq",
            "execution_mode": "serial"
        },
        "predecessor": {
            "package": "Package 79",
            "job_id": "1416328.mmaster02",
            "finding": "Wake stiffness integral inflated by 1.98x due to unweighted averaging; Package 80 restores peak-preserving wake damage."
        },
        "active_set_partition": {
            "active_nodes_count": 1752,
            "inactive_nodes_count": 661,
            "total_nodes": 2413
        },
        "acceptance_criteria": {
            "reaction_force_continuity": "<= 5.0% error vs donor 3.266150 N",
            "fracture_energy_continuity": "<= 2.0% error vs donor 293.92 microJ",
            "damage_irreversibility": "zero healing violations",
            "equilibrium_completion": "100% completion of coupled re-equilibration step"
        }
    }
    manifest_file = PKG80_DIR / "PACKAGE_MANIFEST.json"
    with open(manifest_file, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    manifest_hash = sha256_file(manifest_file)

    cmd_str = r'powershell -NoProfile -ExecutionPolicy Bypass -File .\.agents\scripts\Invoke-GuardedSsh.ps1 -RemoteCommand "qsub -q entry_imfdfkmq /scratch9/pr21vyci/runs/mode1_candidate_c2_peak_preserved_reequilibration/submit_M1_C2_PEAK_PRESERVED_REEQUIL.pbs"'
    cmd_hash = hashlib.sha256(cmd_str.encode("utf-8")).hexdigest().lower()

    auth = {
        "batch_name": "MODE1_C2_PEAK_PRESERVED_REEQUIL",
        "adapter": "mode1-qualified-batch-v2",
        "scientific_scope": "MODE1",
        "technical_stage": "MODE1_BASELINE",
        "configuration": "MODE1_BASELINE",
        "max_submissions": 1,
        "hours_valid": 24,
        "automatic_retry": False,
        "remote_run_dir": "/scratch9/pr21vyci/runs/mode1_candidate_c2_peak_preserved_reequilibration",
        "files": {
            "M1_C2_PEAK_PRESERVED_REEQUIL.inp": inp_hash,
            "f42_mixed_uel.for": uel_hash,
            "job_notifications.sh": notif_hash,
            "submit_M1_C2_PEAK_PRESERVED_REEQUIL.pbs": pbs_hash,
            "PACKAGE_MANIFEST.json": manifest_hash,
            "M1_C2_PEAK_PRESERVED_REEQUIL_DC.dat": dat_hash
        },
        "jobs": [
            {
                "id": "M1_C2_PEAK_PRESERVED_REEQUIL",
                "pbs": "submit_M1_C2_PEAK_PRESERVED_REEQUIL.pbs",
                "command": cmd_str,
                "command_sha256": cmd_hash,
                "max_submissions": 1,
                "depends_on": [],
                "purpose": "Candidate C2 peak-preserved active-set re-equilibration diagnostic (2300 quads, h=1.0 um, u_top=0.002540107 mm, frozen UEL) restoring authentic donor crack-wake damage peak",
                "cpus": 1,
                "memory_gb": 8,
                "walltime_hours": 4,
                "queue": "entry_imfdfkmq",
                "execution": "single-rank serial",
                "input": "M1_C2_PEAK_PRESERVED_REEQUIL.inp",
                "datacheck": "M1_C2_PEAK_PRESERVED_REEQUIL_DC.dat"
            }
        ],
        "acceptance": {
            "M1_C2_PEAK_PRESERVED_REEQUIL": "Exit code 0; Step 1 injects state; Step 2 achieves mechanical equilibrium under frozen damage; Step 3 achieves coupled Newton-Raphson equilibrium with active set holding d >= d_mapped; zero damage healing within tolerance; force continuity within 5% and fracture energy continuity within 2%."
        }
    }
    auth_file = PKG80_DIR / "C2_PEAK_PRESERVED_REEQUIL_AUTHORIZATION.json"
    with open(auth_file, "w", encoding="utf-8") as f:
        json.dump(auth, f, indent=2)

    print(f"Generated {manifest_file.name} (SHA256: {manifest_hash})")
    print(f"Generated {auth_file.name} (SHA256: {sha256_file(auth_file)})")

if __name__ == "__main__":
    main()
