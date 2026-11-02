#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_package_c2_2_continuation.py
Builder and Preflight for Mode-I Method C Stage C2-2 (+5 nm Continuation on C5 Mesh, Package 167).
Task: F1598-PACKAGE166-CONVERGENCE-ACCEPTANCE
Protocol Version: 2

Prepares candidate Package 167 (Stage C2-2 Forward Continuation):
- Mesh: C5 (12,996 elements, 13,278 nodes, 51,984 integration points)
- Load increment: Advancing uy from 0.0018653125442191958 mm to 0.0018703125442191958 mm (+5.0 nm)
- Enforces strict authentic Checkpoint 02 binding from Package 163-R3 (Job 1419499.mmaster02)
- Rejects all disqualified Package 163-R2 artifacts (Job 1419489.mmaster02)
- Validated reference comparator: Package 169 Reference B (Job 1419543.mmaster02)
"""

from __future__ import print_function, division
import json
import hashlib
import shutil
import sys
import csv
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.state_transfer.stage_c2_2_specification import (
    get_c2_2_specification,
    evaluate_c2_2_submission_eligibility,
    BASELINE_UY_MM, TARGET_UY_MM, INCREMENT_UY_MM,
    FROZEN_UEL_SHA256, TOTAL_C5_NODES, TOTAL_C5_ELEMENTS,
    R3_RUN_DIR, ACTIVE_PREDECESSOR_JOB_ID, DISQUALIFIED_PREDECESSOR_JOB_IDS
)

PKG_167_DIR = REPO_ROOT / "models/pandey_kumar_mode1/167_c5_package167_c2_2_continuation"
REMOTE_RUN_DIR = "/scratch9/pr21vyci/runs/mode1_c5_package167_c2_2_continuation"
CHECKPOINT_02_SRC = R3_RUN_DIR / "evidence/1419499.mmaster02/converged_checkpoint_02.json"
CHECKPOINT_02_CANONICAL_HASH = "8201D8200A12C8A493ABA8550DA7D66DB9301C2389A9EA1409BCB5B9E57B4FEA"


def sha256_file(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest().upper()


def canonical(cmd):
    return " ".join(cmd.strip().split())


def parse_c5_connectivity(inp_path):
    conn = {}
    with open(inp_path, "r", encoding="utf-8") as f:
        in_elem = False
        for line in f:
            line_str = line.strip()
            if line_str.startswith("*Element, type=U1"):
                in_elem = True
                continue
            elif in_elem and line_str.startswith("*"):
                break
            elif in_elem and line_str:
                parts = [int(p.strip()) for p in line_str.split(",")]
                eid, n1, n2, n3, n4 = parts[0], parts[1], parts[2], parts[3], parts[4]
                conn[eid] = (n1, n2, n3, n4)
    return conn


def build_c2_2_package(dry_run=False, checkpoint_override=None, r3_report_override=None, r8_report_override=None):
    """
    Build candidate Package 167.
    """
    eligibility = evaluate_c2_2_submission_eligibility(
        checkpoint_override=checkpoint_override,
        r3_report_override=r3_report_override,
        r8_report_override=r8_report_override
    )
    if not eligibility["eligible_for_submission"]:
        return {
            "success": False,
            "status": "NO_SUBMISSION_FALLBACK",
            "reason": eligibility["block_reason"],
            "explanation": eligibility["explanation"],
            "package_path": str(PKG_167_DIR)
        }

    PKG_167_DIR.mkdir(parents=True, exist_ok=True)
    chkpt_path = Path(eligibility["checkpoint_02_path"])
    chkpt_hash = sha256_file(chkpt_path)
    if chkpt_hash != CHECKPOINT_02_CANONICAL_HASH:
        raise ValueError(f"Checkpoint 02 hash mismatch: {chkpt_hash} != {CHECKPOINT_02_CANONICAL_HASH}")

    chkpt_data = json.loads(chkpt_path.read_text(encoding="utf-8"))

    # 1. Copy Checkpoint 02 to package
    shutil.copyfile(chkpt_path, PKG_167_DIR / "initial_checkpoint_02.json")

    # 2. Copy f42_mixed_uel.for and verify hash
    uel_src = R3_RUN_DIR / "f42_mixed_uel.for"
    uel_dst = PKG_167_DIR / "f42_mixed_uel.for"
    shutil.copyfile(uel_src, uel_dst)
    uel_hash = sha256_file(uel_dst)
    if uel_hash != FROZEN_UEL_SHA256:
        raise ValueError("UEL SHA-256 mismatch in C2-2 builder: " + uel_hash)

    # 3. Copy job_notifications.sh
    notif_src = R3_RUN_DIR / "job_notifications.sh"
    notif_dst = PKG_167_DIR / "job_notifications.sh"
    shutil.copyfile(notif_src, notif_dst)

    # 4. Extract state maps
    u_map = {int(r[0]): (float(r[1]), float(r[2])) for r in chkpt_data["displacement"]}
    d_map = {int(r[0]): float(r[1]) for r in chkpt_data["damage"]}
    h_map = {(int(r[0]), int(r[1])): float(r[2]) for r in chkpt_data["history"]}

    # Load previous lower bounds if available
    prev_h_bounds = {}
    if (R3_RUN_DIR / "d_lower_bounds.csv").is_file():
        with open(R3_RUN_DIR / "d_lower_bounds.csv", "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            next(reader)
            for r in reader:
                eid = int(r[0])
                for k in range(1, 5):
                    prev_h_bounds[(eid, k)] = float(r[4 + k])

    # 5. Write nodal_displacements_initial.csv
    with open(PKG_167_DIR / "nodal_displacements_initial.csv", "w", encoding="utf-8", newline="\n") as f:
        writer = csv.writer(f)
        writer.writerow(["node_id", "u1_mm", "u2_mm"])
        for nid in sorted(u_map):
            writer.writerow([nid, f"{u_map[nid][0]:.17g}", f"{u_map[nid][1]:.17g}"])

    # 6. Write nodal_phase_field_initial.csv
    with open(PKG_167_DIR / "nodal_phase_field_initial.csv", "w", encoding="utf-8", newline="\n") as f:
        writer = csv.writer(f)
        writer.writerow(["node_id", "damage"])
        for nid in sorted(d_map):
            writer.writerow([nid, f"{d_map[nid]:.17g}"])

    # 7. Write d_lower_bounds.csv (monotonic bound update: H_0 = max(H_CP02, H_prev))
    mesh_deck = R3_RUN_DIR / "M1_C5_PACKAGE163_R3_C2_1_CONTINUATION.inp"
    elements = parse_c5_connectivity(mesh_deck)
    with open(PKG_167_DIR / "d_lower_bounds.csv", "w", encoding="utf-8", newline="\n") as f:
        writer = csv.writer(f)
        writer.writerow(["element_id", "d_node1", "d_node2", "d_node3", "d_node4", "h_gp1", "h_gp2", "h_gp3", "h_gp4"])
        for eid in sorted(elements):
            conn = elements[eid]
            d_nodal_vals = [f"{d_map[n]:.17g}" for n in conn]
            h_vals = []
            for g in range(1, 5):
                cur_h = h_map.get((eid, g), 0.0)
                old_h = prev_h_bounds.get((eid, g), 0.0)
                h_vals.append(f"{max(cur_h, old_h):.17g}")
            writer.writerow([eid] + d_nodal_vals + h_vals)

    # 8. Write initial_conditions_solution.inc
    with open(PKG_167_DIR / "initial_conditions_solution.inc", "w", encoding="utf-8", newline="\n") as f:
        for eid in sorted(elements):
            f.write(f"{eid}, 0, 0, 0, 0, 0, 0, 0\n")
            h_str = ", ".join(f"{max(h_map.get((eid, g), 0.0), prev_h_bounds.get((eid, g), 0.0)):.17g}" for g in range(1, 5))
            f.write(f"0, {h_str}, 0, 0, 0\n0, 0, 0\n")

    # 9. Write active_set_boundary_cards.inc
    with open(PKG_167_DIR / "active_set_boundary_cards.inc", "w", encoding="utf-8", newline="\n") as f:
        f.write("** Active Set Dirichlet cards for C5 Stage C2-2 Continuation\n")
        f.write("** Format: node_id, 3, 3, d_value\n")
        for nid in sorted(d_map):
            f.write(f"{nid}, 3, 3, {d_map[nid]:.17g}\n")

    # 10. Assemble Master Input Deck M1_C5_PACKAGE167_C2_2_CONTINUATION.inp
    base_deck_text = mesh_deck.read_text(encoding="utf-8")
    new_deck_text = base_deck_text.replace(
        "N_RP, 2, 2, 0.0018653125442191958",
        f"N_RP, 2, 2, {TARGET_UY_MM:.17g}"
    ).replace(
        "*Step, name=C2_1_Step1",
        "*Step, name=C2_2_Step1"
    )
    master_inp_path = PKG_167_DIR / "M1_C5_PACKAGE167_C2_2_CONTINUATION.inp"
    master_inp_path.write_text(new_deck_text, encoding="utf-8")

    # 11. Datacheck decks
    mech_dc_path = PKG_167_DIR / "P167_MECHANICAL_DC.inp"
    mech_dc_path.write_text(new_deck_text, encoding="utf-8")

    # Phase DC deck: prescribes u from Checkpoint 02 without conflicting set boundaries
    phase_dc_lines = []
    blocks = new_deck_text.split("*Step")
    phase_prefix = blocks[0]
    phase_dc_lines.append(phase_prefix)
    phase_dc_lines.append("*Step, name=C2_2_Step1, nlgeom=NO, inc=1\n*Static\n1., 1., 1., 1.\n*Boundary, amplitude=FIXED\n")
    for nid in sorted(u_map):
        u1, u2 = u_map[nid]
        phase_dc_lines.append(f"{nid}, 1, 1, {u1:.17g}\n")
        phase_dc_lines.append(f"{nid}, 2, 2, {u2:.17g}\n")
    phase_dc_lines.append('*INCLUDE, INPUT="active_set_boundary_cards.inc"\n*Output, field, frequency=1\n*Node Output\nU, RF\n*Element Output, elset=MECH_QUADS\nSDV\n*Node Print, frequency=1\nU\n*End Step\n')
    phase_dc_path = PKG_167_DIR / "P167_PHASE_DC.inp"
    phase_dc_path.write_text("".join(phase_dc_lines), encoding="utf-8")

    # 12. run_datacheck.sh
    run_dc_script = f"""#!/bin/bash
set -euo pipefail
cd "{REMOTE_RUN_DIR}"

case "${{1:-}}" in
  mechanical) job=P167_MECHANICAL_DC ;;
  phase) job=P167_PHASE_DC ;;
  *) echo 'Exact mechanical or phase role required' >&2; exit 64 ;;
esac

if ! type module >/dev/null 2>&1; then
    source /etc/profile.d/lmod.sh 2>/dev/null || source /usr/share/Modules/init/bash 2>/dev/null || true
fi
module purge
module load gcc/11.4.0 intel/2024.2.0 abaqus/2023
command -v ifort

abaqus job="${{job}}" input="${{job}}.inp" user=f42_mixed_uel.for cpus=1 memory="16 gb" datacheck interactive > "${{job}}.stdout.txt" 2>&1
test -f "${{job}}.dat"
grep -q 'THE ANALYSIS HAS COMPLETED SUCCESSFULLY' "${{job}}.dat" || grep -q 'ANALYSIS DATACHECK COMPLETE' "${{job}}.dat"
if grep -q '\\*\\*\\*ERROR' "${{job}}.dat"; then exit 66; fi
echo "${{job}}: AUTHENTIC_DATACHECK_PASS"
"""
    (PKG_167_DIR / "run_datacheck.sh").write_bytes(run_dc_script.replace("\r\n", "\n").encode("utf-8"))

    # 13. submit_M1_C5_P167_C2_2.pbs
    pbs_content = f"""#!/bin/bash
#PBS -N M1_C5_P167_C2_2
#PBS -l select=1:ncpus=1:mem=16gb
#PBS -l walltime=08:00:00
#PBS -q entry_imfdfkmq
#PBS -j oe
#PBS -r n
#PBS -o {REMOTE_RUN_DIR}/pbs_execution.log
#PBS -m abe
#PBS -M pr21vyci@mailserver.tu-freiberg.de

set -euo pipefail
RUN_DIR="{REMOTE_RUN_DIR}"
cd "${{RUN_DIR}}"

export JOB_NAME="M1_C5_P167_C2_2"
export NOTIFICATION_CONFIG="${{NOTIFICATION_CONFIG:-${{HOME}}/.config/adaptive-remeshing/notifications.env}}"
source "${{RUN_DIR}}/job_notifications.sh"
notification_load_config
notification_install_terminal_trap
notify_start

if ! type module >/dev/null 2>&1; then
    source /etc/profile.d/lmod.sh 2>/dev/null || source /usr/share/Modules/init/bash 2>/dev/null || true
fi
module purge
module load gcc/11.4.0 intel/2024.2.0 abaqus/2023
command -v ifort

repo="${{RUN_DIR}}/runtime"
python3 "${{repo}}/scripts/state_transfer/driver_package167_c5_continuation.py" \\
    --package "${{RUN_DIR}}" \\
    --output "${{RUN_DIR}}/continuation_${{PBS_JOBID}}" \\
    --extractor "${{repo}}/scripts/validation/extract_package148_iteration.py" \\
    --memory-gb 16 \\
    --timeout 25200 \\
    --max-outer 300
EXIT_CODE=$?

echo "Stage C2-2 Forward Continuation finished with exit code: ${{EXIT_CODE}}"
exit ${{EXIT_CODE}}
"""
    (PKG_167_DIR / "submit_M1_C5_P167_C2_2.pbs").write_bytes(pbs_content.replace("\r\n", "\n").encode("utf-8"))

    # 14. Compute file hashes for PACKAGE_MANIFEST.json
    all_package_files = [
        "active_set_boundary_cards.inc",
        "d_lower_bounds.csv",
        "f42_mixed_uel.for",
        "initial_checkpoint_02.json",
        "initial_conditions_solution.inc",
        "job_notifications.sh",
        "M1_C5_PACKAGE167_C2_2_CONTINUATION.inp",
        "nodal_displacements_initial.csv",
        "nodal_phase_field_initial.csv",
        "P167_MECHANICAL_DC.inp",
        "P167_PHASE_DC.inp",
        "run_datacheck.sh",
        "submit_M1_C5_P167_C2_2.pbs"
    ]
    if (PKG_167_DIR / "P167_MECHANICAL_DC.dat").is_file():
        all_package_files.append("P167_MECHANICAL_DC.dat")
    if (PKG_167_DIR / "P167_PHASE_DC.dat").is_file():
        all_package_files.append("P167_PHASE_DC.dat")

    pkg_manifest_files = {}
    for name in sorted(all_package_files):
        p = PKG_167_DIR / name
        assert p.is_file(), f"Missing file {name}"
        pkg_manifest_files[name] = sha256_file(p).lower()

    pkg_manifest = {
        "schema": 1,
        "package": "Package 167 Stage C2-2 +5 nm Forward Continuation",
        "mesh": "Candidate C5 Mesh (12,996 quads, 13,278 nodes, 51,984 GPs)",
        "baseline_uy_mm": BASELINE_UY_MM,
        "target_uy_mm": TARGET_UY_MM,
        "increment_nm": 5.0,
        "max_outer": 300,
        "predecessor_checkpoint_02_sha256": chkpt_hash,
        "reference_b_comparator_job_id": "1419543.mmaster02",
        "files": pkg_manifest_files
    }
    (PKG_167_DIR / "PACKAGE_MANIFEST.json").write_text(json.dumps(pkg_manifest, indent=2), encoding="utf-8")

    # Add PACKAGE_MANIFEST.json to files for EXECUTION_MANIFEST.json
    exec_manifest_files = dict(pkg_manifest_files)
    exec_manifest_files["PACKAGE_MANIFEST.json"] = sha256_file(PKG_167_DIR / "PACKAGE_MANIFEST.json").lower()

    # Runtime sources
    runtime_sources = {
        "scripts/state_transfer/driver_package167_c5_continuation.py": sha256_file(REPO_ROOT / "scripts/state_transfer/driver_package167_c5_continuation.py"),
        "scripts/validation/extract_package148_iteration.py": sha256_file(REPO_ROOT / "scripts/validation/extract_package148_iteration.py"),
        "scripts/state_transfer/c4_to_c5_spatial_mapping.py": sha256_file(REPO_ROOT / "scripts/state_transfer/c4_to_c5_spatial_mapping.py"),
        "scripts/state_transfer/driver_package146_147_pdas_continuation.py": sha256_file(REPO_ROOT / "scripts/state_transfer/driver_package146_147_pdas_continuation.py")
    }

    cmd = f'powershell -NoProfile -ExecutionPolicy Bypass -File .\\.agents\\scripts\\Invoke-GuardedSsh.ps1 -RemoteCommand "qsub -q entry_imfdfkmq {REMOTE_RUN_DIR}/submit_M1_C5_P167_C2_2.pbs"'
    cmd_sha256 = hashlib.sha256(canonical(cmd).encode()).hexdigest()

    jobs = [
        {
            "id": "M1_C5_P167_C2_2",
            "purpose": "Mode-I Stage C2-2 +5 nm forward continuation on C5 receiver mesh advancing from Checkpoint 02 to target uy=0.001870312544 mm with max_outer=300",
            "input": "P167_MECHANICAL_DC.inp",
            "datacheck": "P167_MECHANICAL_DC.dat",
            "additional_datachecks": [
                "P167_PHASE_DC.dat"
            ],
            "pbs": "submit_M1_C5_P167_C2_2.pbs",
            "queue": "entry_imfdfkmq",
            "cpus": 1,
            "memory_gb": 16,
            "walltime_hours": 8,
            "execution": "single-rank serial",
            "max_submissions": 1,
            "depends_on": [],
            "command": cmd,
            "command_sha256": cmd_sha256
        }
    ]

    exec_manifest = {
        "batch_name": "MODE1_PACKAGE167_M1_C5_P167_C2_2",
        "adapter": "mode1-qualified-batch-v2",
        "scientific_scope": "MODE1",
        "technical_stage": "MODE1_BASELINE",
        "configuration": "MODE1_BASELINE",
        "max_submissions": 1,
        "automatic_retry": False,
        "remote_run_dir": REMOTE_RUN_DIR,
        "runtime_root": f"{REMOTE_RUN_DIR}/runtime",
        "runtime_source_hashes": runtime_sources,
        "files": exec_manifest_files,
        "scientific_predecessor_review": "results/validation/mode1_f1597/package169_reference_evaluation.json",
        "jobs": jobs,
        "acceptance": {
            "M1_C5_P167_C2_2": "Mode-I Stage C2-2 +5 nm forward continuation meeting coupled PDAS convergence (delta_d <= 1e-5, delta_u <= 1e-9 mm, delta_h <= 1e-4 MPa, force <= 2%, energy <= 2% against Package 169 Reference B) and physical acceptance with max_outer=300"
        }
    }
    (PKG_167_DIR / "EXECUTION_MANIFEST.json").write_text(json.dumps(exec_manifest, indent=2), encoding="utf-8")

    return {
        "success": True,
        "status": "PACKAGE_ASSEMBLED_READY_FOR_PREFLIGHT",
        "package_path": str(PKG_167_DIR),
        "predecessor_checkpoint": str(chkpt_path),
        "predecessor_checkpoint_sha256": chkpt_hash,
        "predecessor_job_id": ACTIVE_PREDECESSOR_JOB_ID,
        "reference_b_job_id": "1419543.mmaster02",
        "uel_sha256": uel_hash
    }


if __name__ == "__main__":
    res = build_c2_2_package()
    print(json.dumps(res, indent=2))
