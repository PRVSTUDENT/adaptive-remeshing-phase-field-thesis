# -*- coding: utf-8 -*-
"""
build_package150_c1_2_continuation.py
Mode-I Method C: Stage C1-2 Forward-Loading Continuation Package Builder.
Task: F1597-CORRECT-PACKAGE72-STATE-TRANSFER
Protocol Version: 2

Generates Package 150 forward continuation files initialized from authentic
accepted Package 148 Revision 8 equilibrium checkpoint:
  Checkpoint: results/validation/package148/r8_equilibrium_checkpoint.json
  SHA-256: 5D627B0340ADB3099D5C8980F733160FFA134787704DEAEBC93D67AB55B8D81C
"""
from __future__ import print_function, division
import os
import sys
import json
import hashlib
import shutil
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.state_transfer.c3_int_to_c4_spatial_mapping import Mesh2D

EXPECTED_CHECKPOINT_SHA256 = "5D627B0340ADB3099D5C8980F733160FFA134787704DEAEBC93D67AB55B8D81C"
FROZEN_UEL_SHA256 = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"
RECEIVER_TEMPLATE_INP = REPO_ROOT / "models/pandey_kumar_mode1/147_c4_corrected_reference/M1_C4_CORRECTED_PACKAGE147_REF.inp"
FROZEN_UEL_SOURCE = REPO_ROOT / "models/pandey_kumar_mode1/148_c4_package148_state_transfer_r8/f42_mixed_uel.for"
NOTIFICATIONS_SOURCE = REPO_ROOT / "models/pandey_kumar_mode1/148_c4_package148_state_transfer_r8/job_notifications.sh"

U_START_MM = 0.0018003125442191958
U_TARGET_MM = 0.0020000000000000000
LOADING_STEPS = [
    {"step": 1, "target_uy": 0.0018503125442191958, "delta_uy": 0.000050000000},
    {"step": 2, "target_uy": 0.0019003125442191958, "delta_uy": 0.000050000000},
    {"step": 3, "target_uy": 0.0019503125442191958, "delta_uy": 0.000050000000},
    {"step": 4, "target_uy": 0.0020000000000000000, "delta_uy": 0.0000496874557808042}
]


def sha256_file(p):
    h = hashlib.sha256()
    with open(str(p), "rb") as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest().upper()


def build_package150(target_dir=None):
    if target_dir is None:
        target_dir = REPO_ROOT / "models" / "pandey_kumar_mode1" / "150_c4_package150_c1_2_continuation"
    target_dir = Path(target_dir)
    target_dir.mkdir(parents=True, exist_ok=True)

    checkpoint_file = REPO_ROOT / "results" / "validation" / "package148" / "r8_equilibrium_checkpoint.json"
    if not checkpoint_file.is_file():
        raise FileNotFoundError("Missing checkpoint file: %s" % checkpoint_file)

    actual_hash = sha256_file(checkpoint_file)
    if actual_hash != EXPECTED_CHECKPOINT_SHA256:
        raise ValueError("Checkpoint hash mismatch: expected %s, got %s" % (EXPECTED_CHECKPOINT_SHA256, actual_hash))

    with open(str(checkpoint_file), "r") as f:
        cp = json.load(f)

    # 1. Parse mesh template
    mesh = Mesh2D.from_inp(str(RECEIVER_TEMPLATE_INP), max_physical_node=7265)
    if len(mesh.nodes) != 7265 or len(mesh.elements) != 7056:
        raise ValueError("Unexpected receiver mesh topology: %d nodes, %d elements" % (len(mesh.nodes), len(mesh.elements)))

    # 2. Extract state arrays
    disp_rows = cp["displacement"]  # [[nid, u1, u2], ...]
    damage_rows = cp["damage"]      # [[nid, d], ...]
    history_rows = cp["history"]    # [[eid, gp, H], ...]
    active_nodes = set(cp.get("active_nodes", []))

    if len(disp_rows) != 7265 or len(damage_rows) != 7265 or len(history_rows) != 28224:
        raise ValueError("Incomplete checkpoint state: disp=%d, damage=%d, history=%d" % (len(disp_rows), len(damage_rows), len(history_rows)))

    disp_map = {r[0]: (r[1], r[2]) for r in disp_rows}
    damage_map = {r[0]: r[1] for r in damage_rows}
    history_map = {(r[0], r[1]): r[2] for r in history_rows}

    # 3. Write nodal_displacements_initial.csv
    disp_csv = target_dir / "nodal_displacements_initial.csv"
    with open(str(disp_csv), "w") as f:
        f.write("node_id,u1,u2\n")
        for nid in sorted(mesh.nodes):
            u1, u2 = disp_map[nid]
            f.write("%d,%.17g,%.17g\n" % (nid, u1, u2))

    # 4. Write nodal_phase_field_initial.csv
    damage_csv = target_dir / "nodal_phase_field_initial.csv"
    with open(str(damage_csv), "w") as f:
        f.write("node_id,d\n")
        for nid in sorted(mesh.nodes):
            d = damage_map[nid]
            f.write("%d,%.17g\n" % (nid, d))

    # 5. Write d_lower_bounds.csv
    # Note: frozen UEL perimeter order is [1, 2, 4, 3] relative to row order [1, 2, 3, 4]
    bounds_csv = target_dir / "d_lower_bounds.csv"
    with open(str(bounds_csv), "w") as f:
        f.write("element_id,d0_1,d0_2,d0_3,d0_4,h0_1,h0_2,h0_3,h0_4\n")
        for eid in sorted(mesh.elements):
            conn = mesh.elements[eid]
            d_nodal = [damage_map[n] for n in conn]
            # Average nodal damage to 4 GPs
            d_gp = [sum(d_nodal)/4.0]*4
            # Map UEL perimeter GP (1, 2, 3, 4) to spatial mapper order (1, 2, 4, 3)
            # GP1: (1,1), GP2: (2,2), GP3: (4,3), GP4: (3,4)
            h_uel = [history_map[eid, g] for g in (1, 2, 3, 4)]
            # Spatial mapper columns: h0_1, h0_2, h0_3 (uel4), h0_4 (uel3)
            f.write("%d,%.17g,%.17g,%.17g,%.17g,%.17g,%.17g,%.17g,%.17g\n" % (
                eid, d_gp[0], d_gp[1], d_gp[2], d_gp[3],
                h_uel[0], h_uel[1], h_uel[3], h_uel[2]
            ))

    # 6. Write initial_conditions_solution.inc (7+8+3 card serialization)
    inc_file = target_dir / "initial_conditions_solution.inc"
    with open(str(inc_file), "w") as f:
        f.write("*Initial Conditions, type=SOLUTION\n")
        for eid in sorted(mesh.elements):
            h1 = history_map[eid, 1]
            h2 = history_map[eid, 2]
            h3 = history_map[eid, 3]
            h4 = history_map[eid, 4]
            f.write("%d, 0, 0, 0, 0, 0, 0, 0\n" % eid)
            f.write("0, %.17g, %.17g, %.17g, %.17g, 0, 0, 0\n" % (h1, h2, h3, h4))
            f.write("0, 0, 0\n")

    # 7. Write active_set_boundary_cards.inc
    active_inc = target_dir / "active_set_boundary_cards.inc"
    with open(str(active_inc), "w") as f:
        for nid in sorted(active_nodes):
            f.write("%d, 3, 3, %.17g\n" % (nid, damage_map[nid]))

    # 8. Copy f42_mixed_uel.for and verify frozen hash
    uel_dest = target_dir / "f42_mixed_uel.for"
    shutil.copyfile(str(FROZEN_UEL_SOURCE), str(uel_dest))
    uel_hash = sha256_file(uel_dest)
    if uel_hash != FROZEN_UEL_SHA256:
        raise ValueError("Frozen UEL SHA256 corrupted")

    # 9. Copy job_notifications.sh
    notif_dest = target_dir / "job_notifications.sh"
    shutil.copyfile(str(NOTIFICATIONS_SOURCE), str(notif_dest))

    # 10. Write Master Deck: M1_C4_PACKAGE150_C1_2_CONTINUATION.inp
    master_inp = target_dir / "M1_C4_PACKAGE150_C1_2_CONTINUATION.inp"
    with open(str(RECEIVER_TEMPLATE_INP), "r") as f:
        template_content = f.read()

    # Split template at *Step to insert initial state includes
    step_idx = template_content.find("*Step")
    if step_idx == -1:
        raise ValueError("Could not find *Step in receiver template")

    header_part = template_content[:step_idx]
    # Replace initial conditions include if present, or append
    inp_content = header_part.rstrip() + "\n*INCLUDE, INPUT=initial_conditions_solution.inc\n"
    inp_content += """*Amplitude, name=RAMP_C1_2
0.0, 0.0, 1.0, 1.0
*Step, name=C1_2_CONTINUATION, nlgeom=NO, inc=100
*Static
0.25, 1.0, 1e-05, 0.25
*Boundary, amplitude=RAMP_C1_2
N_BOTTOM, 2, 2, 0.0
N_PIN, 1, 1, 0.0
N_TOP, 1, 1, 0.0
N_RP, 1, 1, 0.0
N_RP, 2, 2, 0.0020000000000000000
*INCLUDE, INPUT=active_set_boundary_cards.inc
*Output, field, frequency=1
*Node Output
U, RF
*Element Output, elset=umatelem
SDV
*Node Print, frequency=1
U
*End Step
"""
    with open(str(master_inp), "w") as f:
        f.write(inp_content)

    # 11. Write Datacheck decks
    dc_mech = target_dir / "P150_MECHANICAL_DC.inp"
    dc_mech_content = header_part.rstrip() + "\n*INCLUDE, INPUT=initial_conditions_solution.inc\n"
    dc_mech_content += """*Step, name=P150_DC_MECH, nlgeom=NO, inc=1
*Static
1.0, 1.0, 1.0, 1.0
*Boundary
N_BOTTOM, 2, 2, 0.0
N_PIN, 1, 1, 0.0
N_TOP, 1, 1, 0.0
N_RP, 1, 1, 0.0
N_RP, 2, 2, 0.0018503125442191958
*INCLUDE, INPUT=active_set_boundary_cards.inc
*Output, field, frequency=1
*Node Output
U, RF
*Element Output, elset=umatelem
SDV
*End Step
"""
    with open(str(dc_mech), "w") as f:
        f.write(dc_mech_content)

    dc_phase = target_dir / "P150_PHASE_DC.inp"
    # Phase solve removes *EQUATION cards and prescribes all displacements
    lines = header_part.splitlines()
    clean_lines = []
    skip_eq = False
    for line in lines:
        if line.strip().upper().startswith("*EQUATION"):
            skip_eq = True
            continue
        if skip_eq:
            if line.strip().startswith("*") and not line.strip().startswith("**"):
                skip_eq = False
                clean_lines.append(line)
            continue
        clean_lines.append(line)
    dc_phase_content = "\n".join(clean_lines).rstrip() + "\n*INCLUDE, INPUT=initial_conditions_solution.inc\n"
    dc_phase_content += """*Step, name=P150_DC_PHASE, nlgeom=NO, inc=1
*Static
1.0, 1.0, 1.0, 1.0
*Boundary
N_BOTTOM, 1, 2, 0.0
N_TOP, 1, 2, 0.0
N_RP, 1, 2, 0.0
*INCLUDE, INPUT=active_set_boundary_cards.inc
*Output, field, frequency=1
*Node Output
U, RF
*Element Output, elset=umatelem
SDV
*End Step
"""
    with open(str(dc_phase), "w") as f:
        f.write(dc_phase_content)

    # 12. Write submit_M1_C4_P150_C1_2.pbs
    pbs_file = target_dir / "submit_M1_C4_P150_C1_2.pbs"
    pbs_content = """#!/bin/bash
#PBS -N M1_C4_P150_C1_2
#PBS -l select=1:ncpus=1:mem=16gb
#PBS -l walltime=08:00:00
#PBS -q entry_imfdfkmq
#PBS -j oe
#PBS -r n
#PBS -o /scratch9/pr21vyci/runs/mode1_c4_package150_c1_2_continuation/pbs_execution.log
#PBS -m abe
#PBS -M pr21vyci@mailserver.tu-freiberg.de

set -euo pipefail
RUN_DIR="/scratch9/pr21vyci/runs/mode1_c4_package150_c1_2_continuation"
cd "${RUN_DIR}"

export JOB_NAME="M1_C4_P150_C1_2"
export NOTIFICATION_CONFIG="${NOTIFICATION_CONFIG:-${HOME}/.config/adaptive-remeshing/notifications.env}"
source "${RUN_DIR}/job_notifications.sh"
notification_load_config
notification_install_terminal_trap
notify_start

if ! type module >/dev/null 2>&1; then
    source /etc/profile.d/lmod.sh 2>/dev/null || source /usr/share/Modules/init/bash 2>/dev/null || true
fi
module purge
module load gcc/11.4.0 intel/2024.2.0 abaqus/2023
command -v ifort

repo="${RUN_DIR}/runtime"
python3 "${repo}/scripts/state_transfer/driver_package150_c1_2_continuation.py" \\
    --package "${RUN_DIR}" \\
    --output "${RUN_DIR}/continuation_${PBS_JOBID}" \\
    --extractor "${repo}/scripts/validation/extract_package148_iteration.py" \\
    --memory-gb 16 \\
    --timeout 25200 \\
    --max-outer 30
EXIT_CODE=$?

echo "Stage C1-2 Continuation finished with exit code: ${EXIT_CODE}"
exit ${EXIT_CODE}
"""
    with open(str(pbs_file), "w") as f:
        f.write(pbs_content)

    # 13. Write run_datacheck.sh
    dc_sh = target_dir / "run_datacheck.sh"
    dc_sh_content = """#!/bin/bash
set -euo pipefail
module load abaqus/2023 intel/2024.2.0 gcc/11.4.0 2>/dev/null || true
abaqus datacheck job=P150_MECHANICAL_DC input=P150_MECHANICAL_DC.inp user=f42_mixed_uel.for interactive
abaqus datacheck job=P150_PHASE_DC input=P150_PHASE_DC.inp user=f42_mixed_uel.for interactive
grep -q "THE ANALYSIS HAS COMPLETED SUCCESSFULLY" P150_MECHANICAL_DC.sta || exit 1
grep -q "THE ANALYSIS HAS COMPLETED SUCCESSFULLY" P150_PHASE_DC.sta || exit 2
echo "DATACHECKS_PASSED"
"""
    with open(str(dc_sh), "w") as f:
        f.write(dc_sh_content)

    # 14. Compute hashes and write manifests
    manifest_files = {}
    for p in sorted(target_dir.glob("*")):
        if p.is_file() and not p.name.endswith("MANIFEST.json"):
            manifest_files[p.name] = sha256_file(p).lower()

    package_manifest = {
        "package_id": "PACKAGE_150_C1_2_CONTINUATION",
        "stage": "STAGE_C1_2",
        "predecessor_checkpoint": "results/validation/package148/r8_equilibrium_checkpoint.json",
        "predecessor_checkpoint_sha256": EXPECTED_CHECKPOINT_SHA256,
        "loading_schedule": {
            "initial_uy_mm": U_START_MM,
            "target_uy_mm": U_TARGET_MM,
            "steps": LOADING_STEPS
        },
        "discretization": {
            "physical_nodes": 7265,
            "reference_nodes": 1,
            "total_nodes": 7266,
            "elements": 7056,
            "integration_points": 28224
        },
        "files": manifest_files
    }
    with open(str(target_dir / "PACKAGE_MANIFEST.json"), "w") as f:
        json.dump(package_manifest, f, indent=2)

    exec_manifest = {
        "batch_name": "MODE1_PACKAGE150_STAGE_C1_2_CONTINUATION",
        "adapter": "mode1-qualified-batch-v2",
        "scientific_scope": "MODE1",
        "technical_stage": "C1-2",
        "configuration": "MODE1_BASELINE",
        "max_submissions": 1,
        "automatic_retry": False,
        "remote_run_dir": "/scratch9/pr21vyci/runs/mode1_c4_package150_c1_2_continuation",
        "files": manifest_files,
        "jobs": [
            {
                "id": "M1_C4_P150_C1_2",
                "purpose": "Executes Stage C1-2 forward-loading continuation from accepted R8 equilibrium checkpoint (uy=0.0018003125 to 0.002000 mm in 4 steps <= 0.00005 mm); preserves 7+8+3 state, frozen UEL, and irreversibility.",
                "input": "P150_MECHANICAL_DC.inp",
                "datacheck": "P150_MECHANICAL_DC.dat",
                "additional_datachecks": [
                    "P150_PHASE_DC.dat"
                ],
                "pbs": "submit_M1_C4_P150_C1_2.pbs",
                "queue": "entry_imfdfkmq",
                "cpus": 1,
                "memory_gb": 16,
                "walltime_hours": 8,
                "execution": "single-rank serial",
                "max_submissions": 1,
                "depends_on": [],
                "command": 'powershell -NoProfile -ExecutionPolicy Bypass -File .\\.agents\\scripts\\Invoke-GuardedSsh.ps1 -RemoteCommand "qsub -q entry_imfdfkmq /scratch9/pr21vyci/runs/mode1_c4_package150_c1_2_continuation/submit_M1_C4_P150_C1_2.pbs"',
                "command_sha256": "4c8f01b63efeb9265f72cf93f18e95c1c8a16709841c30598687b3be6d649987"
            }
        ],
        "acceptance": {
            "M1_C4_P150_C1_2": "Coupled convergence at all 4 loading states; signed KKT; damage in [0,1], no healing beyond 1e-6; monotonic H at all 28,224 GPs; finite physical RF2 and total energy."
        },
        "scientific_predecessor_review": "results/validation/package148/r8_terminal_evaluation.json",
        "runtime_root": "/scratch9/pr21vyci/runs/mode1_c4_package150_c1_2_continuation/runtime",
        "runtime_source_hashes": {
            "models/pandey_kumar_mode1/147_c4_corrected_reference/M1_C4_CORRECTED_PACKAGE147_REF.inp": "FFFE51D5348F6E4B5E9B4742D783CA1645B480B229189168493AEDA10C91722A",
            "results/validation/package148/r8_equilibrium_checkpoint.json": EXPECTED_CHECKPOINT_SHA256,
            "scripts/validation/extract_package148_iteration.py": "1C0D1A33729E1EE746C3C5B9EA10694BD7059D19FA47B8F8B3C639BC8F6D2D98"
        }
    }
    with open(str(target_dir / "EXECUTION_MANIFEST.json"), "w") as f:
        json.dump(exec_manifest, f, indent=2)

    return package_manifest


if __name__ == "__main__":
    rep = build_package150()
    print("Package 150 built successfully: %d files generated" % len(rep["files"]))
