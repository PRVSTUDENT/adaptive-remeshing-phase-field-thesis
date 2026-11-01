#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_package165_c5_contract_a.py
Mode-I Method C Cycle 2: Candidate Package 165 Builder & Offline Qualifier.
Task: F1597-TRUSTED-REVIEW-BOUNDARY-AND-PACKAGE160
Protocol Version: 2

Constructs Candidate Package 165 for Stage C2-0 Coupled Re-Equilibration
on the C5 Receiver Mesh (12,996 elements, 13,278 nodes, 51,984 integration points)
implementing Contract A (Frozen Transferred History H = H0):
1. Pure spatial bilinear transfer of C4 Checkpoint 01 history, eliminating the artificial
   pre-relaxation strain energy gradient spike (27,631.37 MPa -> 6,488.35 MPa at slit tip).
2. Sets H0 = min(H_trans, H_donor_max) at all 51,984 integration points.
3. Preserves separate immutable H0 baseline in d_lower_bounds.csv and initial_conditions_solution.inc.
4. Generates input decks directing execution to driver_package165_c5_contract_a.py.
5. Verifies frozen production UEL (CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6).
6. Generates complete PACKAGE_MANIFEST.json and EXECUTION_MANIFEST.json with SHA-256 digests.
"""

from __future__ import print_function, division
import os
import sys
import math
import json
import shutil
import hashlib
from pathlib import Path

REPO_ROOT = Path("D:/Master thesis/Adaptive remeshing")
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.state_transfer.c4_to_c5_spatial_mapping import (
    Mesh2D,
    C4ToC5TransferMapper,
    C4_INP_DEFAULT,
    C5_INP_DEFAULT,
)
from scripts.generation.build_package160_c5_re_equilibration import assemble_discrete_phase_residuals

SOURCE_CKPT_PATH = REPO_ROOT / "models/pandey_kumar_mode1/157_c4_package157_c1_2_continuation_r5/converged_checkpoint_01.json"
SOURCE_PKG162 = REPO_ROOT / "models/pandey_kumar_mode1/162_c5_package162_c2_0_re_equilibration"
TARGET_PKG165 = REPO_ROOT / "models/pandey_kumar_mode1/165_c5_package165_c2_0_contract_a"
PROD_UEL_PATH = REPO_ROOT / "models/pandey_kumar_mode1/15_energy_qualification_small/f42_mixed_uel.for"
FROZEN_UEL_SHA256 = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"

REMOTE_RUN_DIR = "/scratch9/pr21vyci/runs/mode1_c5_package165_c2_0_contract_a"
JOB_NAME = "M1_C5_P165_C2_0"
PBS_NAME = "submit_M1_C5_P165_C2_0.pbs"

# Hintermuller-Ito-Kunisch PDAS parameters
C_PDAS = 1000.0      # (kN*mm)^-1
EPS_PDAS = 1.0e-6    # dimensionless damage tolerance
TAU_PDAS = EPS_PDAS / C_PDAS  # 1.0e-9 kN*mm residual threshold

def compute_sha256(filepath):
    h = hashlib.sha256()
    with open(str(filepath), "rb") as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest().upper()

def build_package165():
    print("=" * 80)
    print("BUILDING PACKAGE 165: C5 FIXED-LOAD RE-EQUILIBRATION (CONTRACT A)")
    print("=" * 80)

    TARGET_PKG165.mkdir(parents=True, exist_ok=True)

    # 1. Parse meshes
    print("\n1. Parsing meshes...")
    c4 = Mesh2D.from_inp(C4_INP_DEFAULT, name="C4_Donor", max_physical_node=7265)
    c5 = Mesh2D.from_inp(C5_INP_DEFAULT, name="C5_Receiver", max_physical_node=13278)

    # 2. Load authentic Checkpoint 01 donor
    print("\n2. Loading authentic converged Checkpoint 01 donor...")
    ckpt = json.loads(SOURCE_CKPT_PATH.read_text(encoding="utf-8"))
    donor_u = {int(item[0]): (float(item[1]), float(item[2])) for item in ckpt["displacement"]}
    donor_d = {int(item[0]): float(item[1]) for item in ckpt["damage"]}
    donor_h = {(int(item[0]), int(item[1])): float(item[2]) for item in ckpt["history"]}
    target_uy = float(ckpt["target_uy_mm"])

    c4_max_h = max(donor_h.values()) # in kN/mm^2
    print(f"  Donor target_uy = {target_uy:.10g} mm")
    print(f"  Donor max history = {c4_max_h * 1000.0:.4f} MPa ({c4_max_h:.6e} kN/mm^2)")

    # 3. Spatial transfer mapping
    print("\n3. Executing spatial transfer mapping (pure bilinear)...")
    mapper = C4ToC5TransferMapper(c4, c5)
    res_bil = mapper.transfer_fields(donor_u, donor_d, donor_h, history_method="bilinear")

    # 4. Pure spatial history baseline without artificial strain spiking
    # Bound by donor maximum to eliminate any extrapolation overshoot
    print("\n4. Establishing Contract A immutable baseline H0...")
    h0_clean = {k: min(c4_max_h, res_bil["h"][k]) for k in res_bil["h"]}
    max_h0_MPa = max(h0_clean.values()) * 1000.0
    print(f"  Contract A H0 maximum: {max_h0_MPa:.4f} MPa (bounded by C4 max {c4_max_h*1000.0:.4f} MPa)")
    print(f"  Elem 6552 GP 1 (spiked point in P160): {h0_clean[(6552, 1)]*1000.0:.4f} MPa")
    assert max_h0_MPa <= (c4_max_h * 1000.0 + 1e-4), "H0 exceeds donor maximum!"

    # 5. Evaluate discrete phase residuals for initial PDAS active set
    print("\n5. Assembling discrete phase residuals for initial PDAS active set...")
    R_d_clean = assemble_discrete_phase_residuals(c5, res_bil["d"], h0_clean)
    active_nodes = [n for n, r in R_d_clean.items() if r >= -TAU_PDAS]
    free_nodes = [n for n, r in R_d_clean.items() if r < -TAU_PDAS]
    peak_defect_node = min(R_d_clean, key=R_d_clean.get)
    peak_defect_val = R_d_clean[peak_defect_node]

    print(f"  Initial Active Nodes (clamped): {len(active_nodes)} / {len(c5.nodes)} ({len(active_nodes)/len(c5.nodes)*100:.2f}%)")
    print(f"  Initial Free Nodes   (released): {len(free_nodes)} / {len(c5.nodes)} ({len(free_nodes)/len(c5.nodes)*100:.2f}%)")
    print(f"  Peak Dual Defect: {peak_defect_val:.6e} kN*mm at Node {peak_defect_node}")

    # 6. Write initial CSVs
    print("\n6. Writing initial condition CSVs...")
    u_csv = TARGET_PKG165 / "nodal_displacements_initial.csv"
    with u_csv.open("w", encoding="utf-8") as f:
        f.write("node_id,u1,u2\n")
        for nid in sorted(c5.nodes):
            u1, u2 = res_bil["u"][nid]
            f.write(f"{nid},{u1:.16e},{u2:.16e}\n")

    d_csv = TARGET_PKG165 / "nodal_phase_field_initial.csv"
    with d_csv.open("w", encoding="utf-8") as f:
        f.write("node_id,d\n")
        for nid in sorted(c5.nodes):
            f.write(f"{nid},{res_bil['d'][nid]:.16e}\n")

    bounds_csv = TARGET_PKG165 / "d_lower_bounds.csv"
    with bounds_csv.open("w", encoding="utf-8") as f:
        f.write("element_id,d0_1,d0_2,d0_3,d0_4,h0_1,h0_2,h0_3,h0_4\n")
        for eid in sorted(c5.elements):
            conn = c5.elements[eid]
            d0_vals = [res_bil["d"][n] for n in conn]
            h0_vals = [h0_clean[(eid, k)] for k in range(1, 5)]
            f.write(f"{eid}," + ",".join(f"{v:.16e}" for v in d0_vals) + "," + ",".join(f"{v:.16e}" for v in h0_vals) + "\n")

    # 7. Write initial_conditions_solution.inc
    print("\n7. Writing initial_conditions_solution.inc...")
    sol_inc = TARGET_PKG165 / "initial_conditions_solution.inc"
    with sol_inc.open("w", encoding="utf-8") as f:
        f.write("*Initial Conditions, type=SOLUTION\n")
        for eid in sorted(c5.elements):
            h_vals = [h0_clean[(eid, k)] for k in range(1, 5)]
            f.write(f"{eid}, 0, 0, 0, 0, 0, 0, 0\n")
            f.write("0, " + ", ".join(f"{h:.16e}" for h in h_vals) + ", 0, 0, 0\n")
            f.write("0, 0, 0\n")

    # 8. Write active_set_boundary_cards.inc
    print("\n8. Writing active_set_boundary_cards.inc...")
    active_inc = TARGET_PKG165 / "active_set_boundary_cards.inc"
    with active_inc.open("w", encoding="utf-8") as f:
        for nid in sorted(active_nodes):
            f.write(f"{nid}, 3, 3, {res_bil['d'][nid]:.16e}\n")

    # 9. Copy frozen production UEL
    uel_dst = TARGET_PKG165 / "f42_mixed_uel.for"
    shutil.copy2(str(PROD_UEL_PATH), str(uel_dst))
    uel_sha = compute_sha256(uel_dst)
    assert uel_sha == FROZEN_UEL_SHA256, f"UEL hash mismatch: {uel_sha}"
    print(f"\n9. Copied frozen production UEL: {uel_sha}")

    # 10. Assemble main re-equilibration deck
    print("\n10. Assembling M1_C5_PACKAGE165_C2_0_REEQUILIBRATION.inp...")
    c5_mesh_lines = C5_INP_DEFAULT.read_text(encoding="utf-8").splitlines()
    split_idx = None
    for i, line in enumerate(c5_mesh_lines):
        if line.strip().upper() == "*BOUNDARY":
            split_idx = i
            break
    assert split_idx is not None, "Could not find *BOUNDARY in C5 mesh deck!"
    mesh_header_part = c5_mesh_lines[:split_idx]

    main_inp = TARGET_PKG165 / "M1_C5_PACKAGE165_C2_0_REEQUILIBRATION.inp"
    with main_inp.open("w", encoding="utf-8") as f:
        for line in mesh_header_part:
            f.write(line + "\n")
        f.write("*Boundary\n")
        f.write("N_BOTTOM, 2, 2, 0.0\n")
        f.write("N_PIN, 1, 1, 0.0\n")
        f.write("N_TOP, 1, 1, 0.0\n")
        f.write("N_RP, 2, 2, 0.0\n")
        f.write("*INCLUDE, INPUT=initial_conditions_solution.inc\n")
        f.write("*Step, name=C2_0_REEQUILIBRATION, nlgeom=NO, inc=100\n")
        f.write("*Static\n")
        f.write("1.0, 1.0, 1e-05, 1.0\n")
        f.write("*Boundary\n")
        f.write("N_BOTTOM, 2, 2, 0.0\n")
        f.write("N_PIN, 1, 1, 0.0\n")
        f.write("N_TOP, 1, 1, 0.0\n")
        f.write("N_RP, 1, 1, 0.0\n")
        f.write(f"N_RP, 2, 2, {target_uy:.16e}\n")
        f.write("*INCLUDE, INPUT=active_set_boundary_cards.inc\n")
        f.write("*Output, field, frequency=1\n")
        f.write("*Node Output\n")
        f.write("U, RF\n")
        f.write("*Element Output, elset=MECH_QUADS\n")
        f.write("SDV\n")
        f.write("*Node Print, frequency=1\n")
        f.write("U\n")
        f.write("*End Step\n")

    # 11. Assemble datacheck decks
    print("\n11. Assembling datacheck decks...")
    mech_dc = TARGET_PKG165 / "P165_MECHANICAL_DC.inp"
    with mech_dc.open("w", encoding="utf-8") as f:
        for line in mesh_header_part:
            f.write(line + "\n")
        f.write("*Boundary\n")
        f.write("N_BOTTOM, 2, 2, 0.0\n")
        f.write("N_PIN, 1, 1, 0.0\n")
        f.write("N_TOP, 1, 1, 0.0\n")
        f.write("N_RP, 2, 2, 0.0\n")
        f.write("*INCLUDE, INPUT=initial_conditions_solution.inc\n")
        f.write("*Step, name=DC_MECH, nlgeom=NO, inc=1\n")
        f.write("*Static\n")
        f.write("1.0, 1.0, 1e-05, 1.0\n")
        f.write("*Boundary\n")
        f.write("N_BOTTOM, 2, 2, 0.0\n")
        f.write("N_PIN, 1, 1, 0.0\n")
        f.write("N_TOP, 1, 1, 0.0\n")
        f.write("N_RP, 1, 1, 0.0\n")
        f.write(f"N_RP, 2, 2, {target_uy:.16e}\n")
        # Clamp all nodes to d0 for mechanical datacheck
        for nid in sorted(c5.nodes):
            f.write(f"{nid}, 3, 3, {res_bil['d'][nid]:.16e}\n")
        f.write("*Output, field, frequency=1\n")
        f.write("*Node Output\nU, RF\n")
        f.write("*End Step\n")

    phase_dc = TARGET_PKG165 / "P165_PHASE_DC.inp"
    with phase_dc.open("w", encoding="utf-8") as f:
        f.write("*Heading\n")
        f.write("** Package 165 C5 Phase Datacheck Discretization\n")
        f.write("*Preprint, echo=NO, model=NO, history=NO, contact=NO\n")
        f.write("*USER ELEMENT, TYPE=U1, NODES=4, COORDINATES=2, PROPERTIES=6, VARIABLES=18, UNSYMM\n")
        f.write("3\n")
        f.write("*Node\n")
        for nid, (x, y) in sorted(c5.nodes.items()):
            f.write(f"{nid}, {x:.10f}, {y:.10f}\n")
        f.write("*Element, type=U1, elset=PHASE_QUADS\n")
        for eid in range(1, 12997):
            conn = c5.elements[eid]
            f.write(f"{eid}, {conn[0]}, {conn[1]}, {conn[2]}, {conn[3]}\n")
        f.write("*UEL PROPERTY, ELSET=PHASE_QUADS\n")
        f.write("0.0075, 0.0027, 210.0, 0.3, 1.0e-7, 12996\n")
        f.write("*INCLUDE, INPUT=initial_conditions_solution.inc\n")
        f.write("*Step, name=DC_PHASE, nlgeom=NO, inc=1\n")
        f.write("*Static\n")
        f.write("1.0, 1.0, 1.0, 1.0\n")
        f.write("*Boundary\n")
        f.write("*INCLUDE, INPUT=active_set_boundary_cards.inc\n")
        f.write("*Output, field, frequency=1\n")
        f.write("*Node Output\n")
        f.write("U\n")
        f.write("*End Step\n")

    # 12. Copy notification and runner scripts
    for script_name in ["job_notifications.sh"]:
        src = SOURCE_PKG162 / script_name
        dst = TARGET_PKG165 / script_name
        if src.is_file():
            shutil.copy2(str(src), str(dst))

    datacheck_sh = f"""#!/bin/bash
set -euo pipefail
cd "${{1:-{REMOTE_RUN_DIR}}}"
if ! type module >/dev/null 2>&1; then
 source /etc/profile.d/lmod.sh 2>/dev/null || source /usr/share/Modules/init/bash 2>/dev/null || true
fi
module purge
module load gcc/11.4.0 intel/2024.2.0 abaqus/2023
for role in MECHANICAL PHASE; do
 job="P165_${{role}}_DC"
 test ! -e "${{job}}.dat" || rm -f "${{job}}.dat"
 abaqus job="${{job}}" input="${{job}}.inp" user=f42_mixed_uel.for cpus=1 memory="16 gb" datacheck interactive > "${{job}}.stdout.txt" 2>&1
 test -f "${{job}}.dat"
 grep -q 'ANALYSIS DATACHECK COMPLETE' "${{job}}.dat"
 if grep -q '\\*\\*\\*ERROR' "${{job}}.dat"; then exit 66; fi
done
echo AUTHENTIC_DATACHECK_PASS_BOTH
"""
    (TARGET_PKG165 / "run_datacheck.sh").write_text(datacheck_sh, encoding="utf-8")

    # 13. Generate submit PBS script
    pbs_content = f"""#!/bin/bash
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
python3 "${{repo}}/scripts/state_transfer/driver_package165_c5_contract_a.py" \\
    --package "${{RUN_DIR}}" \\
    --output "${{RUN_DIR}}/equilibration_${{PBS_JOBID}}" \\
    --extractor "${{repo}}/scripts/validation/extract_package148_iteration.py" \\
    --memory-gb 16 \\
    --timeout 25200 \\
    --max-outer 100
EXIT_CODE=$?

echo "Stage C2-0 Re-equilibration (Contract A) finished with exit code: ${{EXIT_CODE}}"
exit ${{EXIT_CODE}}
"""
    (TARGET_PKG165 / PBS_NAME).write_text(pbs_content, encoding="utf-8")

    # 14. Generate PACKAGE_MANIFEST.json and EXECUTION_MANIFEST.json
    pkg_files = [
        "M1_C5_PACKAGE165_C2_0_REEQUILIBRATION.inp",
        "P165_MECHANICAL_DC.inp",
        "P165_PHASE_DC.inp",
        "initial_conditions_solution.inc",
        "active_set_boundary_cards.inc",
        "nodal_displacements_initial.csv",
        "nodal_phase_field_initial.csv",
        "d_lower_bounds.csv",
        "f42_mixed_uel.for",
        PBS_NAME,
    ]
    manifest_digests = {fn: compute_sha256(TARGET_PKG165 / fn) for fn in pkg_files}

    pkg_manifest = {
        "schema": 1,
        "package": "package_165",
        "role": "c5_c2_0_re_equilibration_contract_a",
        "target_mesh": "c5_candidate_40k",
        "quad_elements": len(c5.elements),
        "physical_nodes": len(c5.nodes),
        "integration_points": len(h0_clean),
        "target_uy_mm": target_uy,
        "contract": "Contract A: Frozen Transferred History H = H0 during re-equilibration solve",
        "donor_source": {
            "checkpoint": str(SOURCE_CKPT_PATH.name),
            "donor_target_uy_mm": target_uy,
            "donor_max_history_MPa": c4_max_h * 1000.0,
            "receiver_max_history_MPa": max_h0_MPa,
            "artificial_amplification_eliminated": True
        },
        "initial_active_set": {
            "active_node_count": len(active_nodes),
            "free_node_count": len(free_nodes),
            "peak_dual_defect_kNmm": peak_defect_val,
            "peak_dual_defect_node": peak_defect_node
        },
        "file_digests": manifest_digests
    }

    with (TARGET_PKG165 / "PACKAGE_MANIFEST.json").open("w", encoding="utf-8") as f:
        json.dump(pkg_manifest, f, indent=2)

    exec_manifest = {
        "schema": 1,
        "job_name": JOB_NAME,
        "pbs_script": PBS_NAME,
        "remote_dir": REMOTE_RUN_DIR,
        "uel_sha256": uel_sha,
        "resource_request": {
            "select": 1,
            "ncpus": 1,
            "mem_gb": 16,
            "walltime_hours": 8,
            "queue": "entry_imfdfkmq"
        },
        "acceptance_criteria": {
            "max_dual_defect_kNmm": 1.0e-6,
            "max_free_error_kNmm": 1.0e-6,
            "force_discrepancy_pct": 5.0,
            "energy_discrepancy_pct": 2.0,
            "thermodynamic_consistency": "H0 >= psi+(u*) post-convergence"
        }
    }

    with (TARGET_PKG165 / "EXECUTION_MANIFEST.json").open("w", encoding="utf-8") as f:
        json.dump(exec_manifest, f, indent=2)

    print(f"\nPackage 165 successfully built at: {TARGET_PKG165}")
    return pkg_manifest

if __name__ == "__main__":
    build_package165()
