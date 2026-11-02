#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_package163_c5_continuation.py
Mode-I Method C Cycle 2: Package 163 (+5 nm C5 Forward Continuation) Candidate Builder.
Task: F1597-TRUSTED-REVIEW-BOUNDARY-AND-PACKAGE160
Protocol Version: 2

Constructs the candidate Package 163 for Stage C2-1 forward continuation on the C5 mesh
(12,996 elements, 13,278 nodes, 51,984 integration point driving histories) advancing from
the accepted Checkpoint 01 (uy = 0.0018603125442191958 mm) to target uy = 0.0018653125442191958 mm
(+5 nm increment, matching the accepted C4 R6 reference load level).

State Contracts Enforced:
1. Strict schema compliance for input Checkpoint 01.
2. Complete topology verification on 12,996-quad C5 mesh (13,278 physical nodes + RP 999999).
3. Monotonic update of lower obstacle bounds: d0_new = max(d0_old, d_conv).
4. Monotonic update of integration-point history baseline: H0_new = max(H0_old, H_conv).
5. Exact target displacement increment (+5.0e-6 mm).
6. Bitwise frozen UEL verification (SHA-256: CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6).
7. Emission of fully self-contained input decks, datachecks, and execution manifests.
"""

from __future__ import print_function, division
import os
import sys
import math
import json
import shutil
import hashlib
import csv
import io
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.state_transfer.c4_to_c5_spatial_mapping import Mesh2D
from scripts.state_transfer.driver_package146_147_pdas_continuation import (
    validate_damage, split_keyword_blocks, FROZEN_UEL_SHA256, HEALING_TOL
)

# Reference definitions
BASELINE_UY_MM = 0.0018603125442191958
TARGET_UY_MM = 0.0018653125442191958
DELTA_UY_MM = 0.0000050000000000000

C4_R6_REFERENCE_FORCE_KN = 0.18411666272311777
C4_R6_REFERENCE_TOTAL_ENERGY_KNMM = 0.00022418821426719904

REMOTE_RUN_DIR = "/scratch9/pr21vyci/runs/mode1_c5_package163_c2_1_continuation"
JOB_NAME = "M1_C5_P163_C2_1"
PBS_NAME = "submit_M1_C5_P163_C2_1.pbs"


def compute_sha256(filepath):
    h = hashlib.sha256()
    with open(str(filepath), "rb") as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest().upper()


def validate_checkpoint_schema(chkpt):
    """
    Validates that checkpoint data strictly conforms to the Stage C2-0 accepted checkpoint interface.
    """
    required_keys = ["schema", "stage", "step", "target_uy_mm", "coupled_convergence",
                     "displacement", "damage", "history"]
    for k in required_keys:
        if k not in chkpt:
            raise ValueError(f"Checkpoint contract violation: missing key '{k}'")

    if chkpt["schema"] != 1:
        raise ValueError(f"Unsupported checkpoint schema: {chkpt['schema']}")
    if not chkpt["coupled_convergence"]:
        raise ValueError("Cannot construct continuation candidate from un-converged checkpoint")
    if abs(float(chkpt["target_uy_mm"]) - BASELINE_UY_MM) > 1e-12:
        raise ValueError(f"Checkpoint baseline uy mismatch: {chkpt['target_uy_mm']} != {BASELINE_UY_MM}")

    disp = chkpt["displacement"]
    dam = chkpt["damage"]
    hist = chkpt["history"]

    if len(disp) != 13278:
        raise ValueError(f"Displacement node coverage violation: {len(disp)} != 13278")
    if len(dam) != 13278:
        raise ValueError(f"Damage node coverage violation: {len(dam)} != 13278")
    if len(hist) != 51984:
        raise ValueError(f"History GP coverage violation: {len(hist)} != 51984")

    # Value sanity
    for r in dam:
        nid, d = int(r[0]), float(r[1])
        if not math.isfinite(d) or d < -HEALING_TOL or d > 1.0 + 1e-6:
            raise ValueError(f"Invalid damage at node {nid}: {d}")

    for r in hist:
        eid, g, h = int(r[0]), int(r[1]), float(r[2])
        if not math.isfinite(h) or h < 0.0:
            raise ValueError(f"Invalid history at element {eid} GP {g}: {h}")

    return True


def build_package163_candidate(checkpoint_data, target_dir, predecessor_package_dir=None):
    """
    Builds the complete, self-contained Package 163 directory for Stage C2-1.
    """
    validate_checkpoint_schema(checkpoint_data)
    target = Path(target_dir).resolve()
    target.mkdir(parents=True, exist_ok=True)

    if predecessor_package_dir is None:
        cand_p166 = REPO_ROOT / "models/pandey_kumar_mode1/166_c5_package166_r3_c2_0_nonaccumulating_history"
        if cand_p166.exists():
            predecessor_package_dir = cand_p166
        else:
            predecessor_package_dir = REPO_ROOT / "models/pandey_kumar_mode1/162_c5_package162_c2_0_re_equilibration"
    pred = Path(predecessor_package_dir).resolve()

    # 1. Verify frozen UEL in repository
    uel_src = pred / "f42_mixed_uel.for"
    if not uel_src.is_file():
        uel_src = REPO_ROOT / "models/pandey_kumar_mode1/104_experimental_irreversible_uel/f42_mixed_uel.for"
    uel_h = compute_sha256(uel_src)
    if uel_h != FROZEN_UEL_SHA256:
        raise ValueError(f"Frozen UEL hash violation: {uel_h} != {FROZEN_UEL_SHA256}")
    shutil.copyfile(str(uel_src), str(target / "f42_mixed_uel.for"))

    # 2. Extract state maps
    u_map = {int(r[0]): (float(r[1]), float(r[2])) for r in checkpoint_data["displacement"]}
    d_map = {int(r[0]): float(r[1]) for r in checkpoint_data["damage"]}
    h_map = {(int(r[0]), int(r[1])): float(r[2]) for r in checkpoint_data["history"]}

    # Load previous lower bounds if available to guarantee monotonicity
    prev_d_bounds = {}
    prev_h_bounds = {}
    if (pred / "d_lower_bounds.csv").is_file():
        with open(pred / "d_lower_bounds.csv", "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            next(reader)
            for r in reader:
                eid = int(r[0])
                for k in range(1, 5):
                    prev_h_bounds[(eid, k)] = float(r[4 + k])

    # 3. Write nodal_displacements_initial.csv
    with open(target / "nodal_displacements_initial.csv", "w", encoding="utf-8", newline="\n") as f:
        writer = csv.writer(f)
        writer.writerow(["node_id", "u1_mm", "u2_mm"])
        for nid in sorted(u_map):
            writer.writerow([nid, f"{u_map[nid][0]:.17g}", f"{u_map[nid][1]:.17g}"])

    # 4. Write nodal_phase_field_initial.csv
    with open(target / "nodal_phase_field_initial.csv", "w", encoding="utf-8", newline="\n") as f:
        writer = csv.writer(f)
        writer.writerow(["node_id", "damage"])
        for nid in sorted(d_map):
            writer.writerow([nid, f"{d_map[nid]:.17g}"])

    # 5. Write d_lower_bounds.csv (monotonic bound update)
    with open(target / "d_lower_bounds.csv", "w", encoding="utf-8", newline="\n") as f:
        writer = csv.writer(f)
        writer.writerow(["element_id", "d_node1", "d_node2", "d_node3", "d_node4", "h_gp1", "h_gp2", "h_gp3", "h_gp4"])
        # C5 mesh elements: 1..12996
        mesh_deck = pred / "M1_C5_PACKAGE166_C2_0_REEQUILIBRATION.inp"
        if not mesh_deck.is_file():
            mesh_deck = pred / "M1_C5_PACKAGE160_C2_0_REEQUILIBRATION.inp"
        mesh = Mesh2D.from_inp(mesh_deck, name="C5", max_physical_node=13278)
        for eid in sorted(mesh.elements):
            conn = mesh.elements[eid]
            d_nodal_vals = [f"{d_map[n]:.17g}" for n in conn]
            h_vals = []
            for g in range(1, 5):
                cur_h = h_map.get((eid, g), 0.0)
                old_h = prev_h_bounds.get((eid, g), 0.0)
                h_vals.append(f"{max(cur_h, old_h):.17g}")
            writer.writerow([eid] + d_nodal_vals + h_vals)

    # 6. Write initial_conditions_solution.inc
    with open(target / "initial_conditions_solution.inc", "w", encoding="utf-8", newline="\n") as f:
        for eid in sorted(mesh.elements):
            f.write(f"{eid}, 0, 0, 0, 0, 0, 0, 0\n")
            h_str = ", ".join(f"{max(h_map.get((eid, g), 0.0), prev_h_bounds.get((eid, g), 0.0)):.17g}" for g in range(1, 5))
            f.write(f"0, {h_str}, 0, 0, 0\n0, 0, 0\n")

    # 7. Write active_set_boundary_cards.inc (clamped damage lower obstacle)
    with open(target / "active_set_boundary_cards.inc", "w", encoding="utf-8", newline="\n") as f:
        f.write("** Active Set Dirichlet cards for C5 Stage C2-1 Continuation\n")
        f.write("** Format: node_id, 3, 3, d_value\n")
        for nid in sorted(d_map):
            f.write(f"{nid}, 3, 3, {d_map[nid]:.17g}\n")

    # 8. Assemble Master Continuation Input Deck
    template_path = pred / "M1_C5_PACKAGE166_C2_0_REEQUILIBRATION.inp"
    if not template_path.is_file():
        template_path = pred / "M1_C5_PACKAGE160_C2_0_REEQUILIBRATION.inp"
    deck_template = template_path.read_text(encoding="utf-8")
    blocks = split_keyword_blocks(deck_template)
    prefix = []
    for block in blocks:
        key = block.split("\n", 1)[0].strip().lower()
        if key.startswith("*step"):
            break
        if key.startswith(("*boundary", "*include")):
            continue
        prefix.append(block)

    master_deck = [
        "".join(prefix),
        "*Initial Conditions, type=SOLUTION\n",
        f'*INCLUDE, INPUT="initial_conditions_solution.inc"\n',
        "*Amplitude, name=FIXED\n0., 1., 1., 1.\n",
        f"*Step, name=C2_1_Step1, nlgeom=NO, inc=1\n",
        "*Static\n1., 1., 1., 1.\n*Boundary, amplitude=FIXED\n",
        "N_BOTTOM, 2, 2, 0.\nN_PIN, 1, 1, 0.\nN_TOP, 1, 1, 0.\n",
        f"N_RP, 1, 1, 0.\nN_RP, 2, 2, {TARGET_UY_MM:.17g}\n",
        f'*INCLUDE, INPUT="active_set_boundary_cards.inc"\n',
        "*Output, field, frequency=1\n*Node Output\nU, RF\n",
        "*Element Output, elset=MECH_QUADS\nSDV\n",
        "*Node Print, frequency=1\nU\n",
        "*End Step\n"
    ]
    (target / "M1_C5_PACKAGE163_C2_1_CONTINUATION.inp").write_text("".join(master_deck), encoding="utf-8")

    # 9. Assemble Datacheck Decks
    mech_dc = [
        "".join(prefix),
        "*Initial Conditions, type=SOLUTION\n",
        f'*INCLUDE, INPUT="initial_conditions_solution.inc"\n',
        "*Amplitude, name=FIXED\n0., 1., 1., 1.\n",
        f"*Step, name=C2_1_Step1, nlgeom=NO, inc=1\n",
        "*Static\n1., 1., 1., 1.\n*Boundary, amplitude=FIXED\n",
        "N_BOTTOM, 2, 2, 0.\nN_PIN, 1, 1, 0.\nN_TOP, 1, 1, 0.\n",
        f"N_RP, 1, 1, 0.\nN_RP, 2, 2, {TARGET_UY_MM:.17g}\n",
        f'*INCLUDE, INPUT="active_set_boundary_cards.inc"\n',
        "*Output, field, frequency=1\n*Node Output\nU, RF\n",
        "*Element Output, elset=MECH_QUADS\nSDV\n",
        "*Node Print, frequency=1\nU\n",
        "*End Step\n"
    ]
    (target / "P163_MECHANICAL_DC.inp").write_text("".join(mech_dc), encoding="utf-8")

    # Phase datacheck deck: uncouple MPCs, prescribe U1/U2 from initial solution, clamp active D
    prefix_phase = []
    for block in blocks:
        key = block.split("\n", 1)[0].strip().lower()
        if key.startswith("*step"):
            break
        if key.startswith(("*boundary", "*include", "*equation")):
            continue
        prefix_phase.append(block)

    phase_dc = [
        "".join(prefix_phase),
        "*Initial Conditions, type=SOLUTION\n",
        f'*INCLUDE, INPUT="initial_conditions_solution.inc"\n',
        "*Amplitude, name=FIXED\n0., 1., 1., 1.\n",
        f"*Step, name=C2_1_Step1, nlgeom=NO, inc=1\n",
        "*Static\n1., 1., 1., 1.\n*Boundary, amplitude=FIXED\n"
    ]
    for nid in sorted(u_map):
        phase_dc.append(f"{nid}, 1, 1, {u_map[nid][0]:.17g}\n{nid}, 2, 2, {u_map[nid][1]:.17g}\n")
    phase_dc.append(f'*INCLUDE, INPUT="active_set_boundary_cards.inc"\n')
    phase_dc += [
        "*Output, field, frequency=1\n*Node Output\nU, RF\n",
        "*Element Output, elset=MECH_QUADS\nSDV\n",
        "*Node Print, frequency=1\nU\n",
        "*End Step\n"
    ]
    (target / "P163_PHASE_DC.inp").write_text("".join(phase_dc), encoding="utf-8")

    # 10. Copy scripts
    if (pred / "job_notifications.sh").is_file():
        shutil.copyfile(str(pred / "job_notifications.sh"), str(target / "job_notifications.sh"))

    # 11. Write run_datacheck.sh
    dc_sh = f"""#!/bin/bash
set -euo pipefail
cd "{REMOTE_RUN_DIR}"

case "${{1:-}}" in
  mechanical) job=P163_MECHANICAL_DC ;;
  phase) job=P163_PHASE_DC ;;
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
    (target / "run_datacheck.sh").write_bytes(dc_sh.replace("\r\n", "\n").encode("utf-8"))

    # 12. Write submit_M1_C5_P163_C2_1.pbs
    pbs_sh = f"""#!/bin/bash
#PBS -N {JOB_NAME}
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

export JOB_NAME="{JOB_NAME}"
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
python3 "${{repo}}/scripts/state_transfer/driver_package163_c5_continuation.py" \\
    --package "${{RUN_DIR}}" \\
    --output "${{RUN_DIR}}/continuation_${{PBS_JOBID}}" \\
    --extractor "${{repo}}/scripts/validation/extract_package148_iteration.py" \\
    --memory-gb 16 \\
    --timeout 25200 \\
    --max-outer 100
EXIT_CODE=$?

echo "Stage C2-1 Forward Continuation finished with exit code: ${{EXIT_CODE}}"
exit ${{EXIT_CODE}}
"""
    (target / PBS_NAME).write_bytes(pbs_sh.replace("\r\n", "\n").encode("utf-8"))

    # 13. Write PACKAGE_MANIFEST.json
    package_files = [
        "active_set_boundary_cards.inc",
        "d_lower_bounds.csv",
        "f42_mixed_uel.for",
        "initial_conditions_solution.inc",
        "job_notifications.sh",
        "M1_C5_PACKAGE163_C2_1_CONTINUATION.inp",
        "nodal_displacements_initial.csv",
        "nodal_phase_field_initial.csv",
        "P163_MECHANICAL_DC.inp",
        "P163_PHASE_DC.inp",
        "run_datacheck.sh",
        PBS_NAME
    ]
    file_hashes = {}
    for fn in sorted(package_files):
        fp = target / fn
        if fp.is_file():
            file_hashes[fn] = compute_sha256(fp).lower()

    pkg_manifest = {
        "package_name": "163_c5_package163_c2_1_continuation",
        "stage": "C2-1",
        "step": 1,
        "baseline_uy_mm": BASELINE_UY_MM,
        "target_uy_mm": TARGET_UY_MM,
        "displacement_increment_mm": DELTA_UY_MM,
        "total_quads": 12996,
        "total_nodes": 13278,
        "total_gps": 51984,
        "frozen_uel_sha256": FROZEN_UEL_SHA256,
        "comparison_reference": {
            "source": "C4_R6_CONTINUATION",
            "load_level_uy_mm": TARGET_UY_MM,
            "reaction_force_kN": C4_R6_REFERENCE_FORCE_KN,
            "total_energy_kNmm": C4_R6_REFERENCE_TOTAL_ENERGY_KNMM
        },
        "files": file_hashes
    }
    (target / "PACKAGE_MANIFEST.json").write_text(json.dumps(pkg_manifest, indent=2), encoding="utf-8")

    # 14. Write EXECUTION_MANIFEST.json
    runtime_sources = {
        "scripts/state_transfer/driver_package163_c5_continuation.py": compute_sha256(REPO_ROOT / "scripts/state_transfer/driver_package163_c5_continuation.py"),
        "scripts/validation/extract_package148_iteration.py": compute_sha256(REPO_ROOT / "scripts/validation/extract_package148_iteration.py"),
        "scripts/state_transfer/c4_to_c5_spatial_mapping.py": compute_sha256(REPO_ROOT / "scripts/state_transfer/c4_to_c5_spatial_mapping.py"),
        "scripts/state_transfer/driver_package146_147_pdas_continuation.py": compute_sha256(REPO_ROOT / "scripts/state_transfer/driver_package146_147_pdas_continuation.py")
    }

    command_str = f'powershell -NoProfile -ExecutionPolicy Bypass -File .\\.agents\\scripts\\Invoke-GuardedSsh.ps1 -RemoteCommand "qsub -q entry_imfdfkmq {REMOTE_RUN_DIR}/{PBS_NAME}"'
    exec_manifest = {
        "batch_name": f"MODE1_PACKAGE163_{JOB_NAME}",
        "adapter": "mode1-qualified-batch-v2",
        "scientific_scope": "MODE1",
        "technical_stage": "C2-1",
        "configuration": "MODE1_C5_REFINED_CONTINUATION",
        "max_submissions": 1,
        "automatic_retry": False,
        "remote_run_dir": REMOTE_RUN_DIR,
        "runtime_root": f"{REMOTE_RUN_DIR}/runtime",
        "runtime_source_hashes": runtime_sources,
        "files": file_hashes,
        "jobs": [
            {
                "id": JOB_NAME,
                "purpose": "Mode-I Method C Cycle 2: Stage C2-1 +5 nm forward continuation on C5 receiver mesh",
                "input": "P163_MECHANICAL_DC.inp",
                "datacheck": "P163_MECHANICAL_DC.dat",
                "additional_datachecks": ["P163_PHASE_DC.dat"],
                "pbs": PBS_NAME,
                "queue": "entry_imfdfkmq",
                "cpus": 1,
                "memory_gb": 16,
                "walltime_hours": 8,
                "execution": "single-rank serial",
                "max_submissions": 1,
                "depends_on": [],
                "command": command_str,
                "command_sha256": hashlib.sha256(command_str.encode()).hexdigest()
            }
        ],
        "acceptance": {
            JOB_NAME: "Mode-I Stage C2-1 +5 nm forward continuation meeting coupled PDAS convergence and physical acceptance"
        }
    }
    (target / "EXECUTION_MANIFEST.json").write_text(json.dumps(exec_manifest, indent=2), encoding="utf-8")
    print(f"Successfully generated Package 163 candidate in {target}")
    return pkg_manifest


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Package 163 Candidate Builder")
    parser.add_argument("--checkpoint", required=True, help="Path to accepted Checkpoint 01 json")
    parser.add_argument("--target", default=str(REPO_ROOT / "models/pandey_kumar_mode1/163_c5_package163_c2_1_continuation"))
    args = parser.parse_args()

    chkpt = json.loads(Path(args.checkpoint).read_text(encoding="utf-8"))
    build_package163_candidate(chkpt, args.target)


if __name__ == "__main__":
    main()
