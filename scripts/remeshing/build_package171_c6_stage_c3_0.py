#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_package171_c6_stage_c3_0.py
=================================
Assembles Package 171: C6 Stage C3-0 Coupled PDAS Re-Equilibration.
Task: F1598-PACKAGE166-CONVERGENCE-ACCEPTANCE
Protocol Version: 2

Deliverables assembled:
- Non-coarsened C6 mesh (15,252 CPE4 quads, 15,559 physical nodes + RP 999999, 59 slit pairs)
- Dual UEL layers: 15,252 phase U1 (DOF 3) + 15,252 mechanical U2 (DOF 1, 2)
- Transferred initial state from accepted Checkpoint 03 (Job 1419566.mmaster02)
- Initial CSV state tables:
  * nodal_displacements_initial.csv (15,559 nodes)
  * nodal_phase_field_initial.csv (15,559 nodes)
  * d_lower_bounds.csv (15,252 elements, 61,008 GPs)
- Solution state initialization: initial_conditions_solution.inc
- Phase obstacle boundary cards: active_set_boundary_cards.inc
- Master template: M1_C6_PACKAGE171_C3_0_REEQUILIBRATION.inp
- Representative compute-node datacheck decks:
  * P171_MECHANICAL_DC.inp
  * P171_PHASE_DC.inp
- Frozen production UEL f42_mixed_uel.for (SHA-256: CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6)
- PBS batch submission script: submit_M1_C6_P171_C3_0.pbs
- Dual notifications helper: job_notifications.sh
- Datacheck execution script: run_datacheck.sh
- Package manifests and batch authorization files
"""

import sys
import json
import math
import shutil
import hashlib
import csv
from pathlib import Path
from typing import Dict, Any, List

REPO_ROOT = Path("D:/Master thesis/Adaptive remeshing")
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.remeshing.c5_to_c6_adaptive_integration import (
    load_c5_mesh,
    validate_c5_indicator_distribution,
    compute_c5_to_c6_sizing,
    generate_noncoarsened_c6_coords,
    build_c6_conformal_quad_mesh,
    verify_non_coarsening_acceptance,
    transfer_c5_to_c6_solution,
    evaluate_transfer_acceptance,
    sha256_file
)

FROZEN_UEL_HASH = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"
PRODUCTION_UEL_PATH = REPO_ROOT / "models/pandey_kumar_mode1/15_energy_qualification_small/f42_mixed_uel.for"
PACKAGE_DIR = REPO_ROOT / "models/pandey_kumar_mode1/171_c6_package171_c3_0_reequilibration"
CP03_PATH = REPO_ROOT / "models/pandey_kumar_mode1/167_c5_package167_r3_c2_2_continuation/evidence/1419566.mmaster02/converged_checkpoint_03.json"
INDICATOR_CSV = REPO_ROOT / "models/pandey_kumar_mode1/168_c5_companion_miseseri/c5_companion_miseseri_distribution.csv"
REMOTE_RUN_DIR = "/scratch9/pr21vyci/runs/mode1_c6_package171_c3_0_reequilibration"


def canonical(cmd: str) -> str:
    return " ".join(cmd.strip().split())


def main():
    print("=" * 80)
    print("ASSEMBLING PACKAGE 171: C6 STAGE C3-0 COUPLED PDAS RE-EQUILIBRATION")
    print("=" * 80)

    PACKAGE_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Verify frozen UEL
    uel_hash = sha256_file(PRODUCTION_UEL_PATH)
    assert uel_hash == FROZEN_UEL_HASH, f"UEL hash mismatch! Expected {FROZEN_UEL_HASH}, got {uel_hash}"
    target_uel = PACKAGE_DIR / "f42_mixed_uel.for"
    shutil.copyfile(PRODUCTION_UEL_PATH, target_uel)
    print(f"1. Verified frozen production UEL: f42_mixed_uel.for ({uel_hash})")

    # 2. Load C5 & Indicators
    c5_mesh = load_c5_mesh()
    val = validate_c5_indicator_distribution(INDICATOR_CSV)
    sizing = compute_c5_to_c6_sizing(val["element_map"])
    marked = sizing["marked_elements"]
    print(f"2. Validated 12,996 C5 elements; {len(marked)} marked elements (eta_g >= 0.15).")

    # 3. Build Non-Coarsened C6 Mesh
    x_c6, y_c6 = generate_noncoarsened_c6_coords(c5_mesh, marked, buffer_mm=0.00025)
    c6_mesh = build_c6_conformal_quad_mesh(x_c6, y_c6, slit_y=0.050, slit_a0=0.040)
    num_elems = c6_mesh["num_elements"]
    num_nodes = c6_mesh["num_nodes"]
    min_det = c6_mesh["min_det_jac"]
    num_slit = len(c6_mesh["coincident_slit_pairs"])
    print(f"3. Non-coarsened C6 mesh: {num_elems} quads, {num_nodes} nodes, min det(J)={min_det:.4e}, {num_slit} slit pairs.")
    assert num_elems == 15252, f"Expected 15,252 elements, got {num_elems}"
    assert num_nodes == 15559, f"Expected 15,559 nodes, got {num_nodes}"
    assert num_slit == 59, f"Expected 59 slit pairs, got {num_slit}"

    # 4. Non-coarsening Acceptance Audit
    audit = verify_non_coarsening_acceptance(c5_mesh, c6_mesh, marked)
    assert audit["pass"] is True, f"Non-coarsening audit failed: {audit}"
    print(f"4. Non-coarsening acceptance audit: PASS (coarsened area fraction: {audit['coarser_area_fraction']*100:.2f}%)")

    # 5. Nonmatching State Transfer from Checkpoint 03
    with open(CP03_PATH, "r", encoding="utf-8") as f:
        cp03 = json.load(f)
    transfer_res = transfer_c5_to_c6_solution(c5_mesh, cp03, c6_mesh)
    print(f"5. Nonmatching transfer: status={transfer_res['status']}, healing={transfer_res['healing_violations']}, bounds={transfer_res['bounds_violations']}")

    # 6. Quantitative Acceptance Evaluation (Elastic & Fracture Energy)
    acc = evaluate_transfer_acceptance(cp03, c6_mesh, transfer_res)
    assert acc["acceptance_passed"] is True, f"Transfer acceptance failed: {acc}"
    el_gate = acc["tests"]["elastic_continuity_gate"]
    frac_gate = acc["tests"]["fracture_continuity_gate"]
    tot_gate = acc["tests"]["total_energy_continuity_gate"]
    print(f"6. Transfer acceptance gates: ALL PASS")
    print(f"   - Elastic discrepancy: {el_gate['elastic_discrepancy_pct']:.4f}% (< 2.0%)")
    print(f"   - Fracture discrepancy: {frac_gate['fracture_discrepancy_pct']:.4f}% (< 2.0%)")
    print(f"   - Total energy discrepancy: {tot_gate['total_energy_discrepancy_pct']:.4f}% (< 2.0%)")

    disp = transfer_res["transferred_disp"]
    dmg = transfer_res["transferred_damage"]
    hist = transfer_res["transferred_history"]
    target_uy = float(cp03["target_uy_mm"])

    # Verify transferred non-zero fields
    min_d = min(dmg.values())
    max_d = max(dmg.values())
    min_h = min(min(h_list) for h_list in hist.values())
    print(f"   - Damage range: [{min_d:.6f}, {max_d:.6f}] (non-zero confirmed)")
    print(f"   - Min history: {min_h:.4e} (strictly positive confirmed)")
    assert min_d > 0.0 and max_d > 0.5, "Damage field must be authentically non-zero"
    assert min_h > 0.0, "History field must be authentically positive"

    # 7. Write nodal_displacements_initial.csv
    u_csv_path = PACKAGE_DIR / "nodal_displacements_initial.csv"
    with u_csv_path.open("w", encoding="utf-8", newline="\n") as f:
        writer = csv.writer(f)
        writer.writerow(["node_id", "u1", "u2"])
        for nid in sorted(disp.keys()):
            u = disp[nid]
            writer.writerow([nid, f"{u[0]:.17e}", f"{u[1]:.17e}"])
    print(f"7. Wrote {u_csv_path.name} ({len(disp)} nodes)")

    # 8. Write nodal_phase_field_initial.csv
    d_csv_path = PACKAGE_DIR / "nodal_phase_field_initial.csv"
    with d_csv_path.open("w", encoding="utf-8", newline="\n") as f:
        writer = csv.writer(f)
        writer.writerow(["node_id", "d"])
        for nid in sorted(dmg.keys()):
            writer.writerow([nid, f"{dmg[nid]:.17e}"])
    print(f"8. Wrote {d_csv_path.name} ({len(dmg)} nodes)")

    # 9. Write d_lower_bounds.csv
    bounds_csv_path = PACKAGE_DIR / "d_lower_bounds.csv"
    elements = c6_mesh["elements"]
    with bounds_csv_path.open("w", encoding="utf-8", newline="\n") as f:
        writer = csv.writer(f)
        writer.writerow(["element_id", "d0_1", "d0_2", "d0_3", "d0_4", "h0_1", "h0_2", "h0_3", "h0_4"])
        for eid in sorted(elements.keys()):
            conn = elements[eid]
            d_vals = [dmg[n] for n in conn]
            h_vals = hist[eid]
            writer.writerow([eid] + [f"{x:.17e}" for x in (d_vals + h_vals)])
    print(f"9. Wrote {bounds_csv_path.name} ({len(elements)} elements, {len(elements)*4} GPs)")

    # 10. Write initial_conditions_solution.inc
    inc_path = PACKAGE_DIR / "initial_conditions_solution.inc"
    with inc_path.open("w", encoding="utf-8", newline="\n") as f:
        f.write("*Initial Conditions, type=SOLUTION\n")
        for eid in sorted(elements.keys()):
            f.write(f"{eid}, 0, 0, 0, 0, 0, 0, 0\n")
            h_line = ", ".join(f"{h_val:.17g}" for h_val in hist[eid])
            f.write(f"0, {h_line}, 0, 0, 0\n0, 0, 0\n")
    print(f"10. Wrote {inc_path.name} ({len(elements)} elements solution cards)")

    # 11. Write active_set_boundary_cards.inc (clamped to d0)
    active_path = PACKAGE_DIR / "active_set_boundary_cards.inc"
    with active_path.open("w", encoding="utf-8", newline="\n") as f:
        for nid in sorted(dmg.keys()):
            f.write(f"{nid}, 3, 3, {dmg[nid]:.17g}\n")
    print(f"11. Wrote {active_path.name} ({len(dmg)} nodes phase cards)")

    # 12. Write Master Re-Equilibration Input Deck
    master_inp_path = PACKAGE_DIR / "M1_C6_PACKAGE171_C3_0_REEQUILIBRATION.inp"
    nodes = c6_mesh["nodes"]
    rp_nid = c6_mesh["rp_nid"]
    top_nodes = c6_mesh["top_nodes"]
    bottom_nodes = c6_mesh["bottom_nodes"]
    pin_nodes = c6_mesh["pin_nodes"]
    n_elems = len(elements)

    with master_inp_path.open("w", encoding="utf-8", newline="\n") as f:
        f.write("*Heading\n")
        f.write(f"** Mode-I Method C Stage C3-0 Re-Equilibration on Candidate C6 Mesh\n")
        f.write(f"** Discretization: {n_elems} Quads, {len(nodes)-1} Nodes + RP {rp_nid}\n")
        f.write(f"** Prescribed Fixed Target: uy = {target_uy:.10f} mm\n")
        f.write(f"** Task: F1598 (Adaptive Remeshing)\n")
        f.write("*Preprint, echo=NO, model=NO, history=NO, contact=NO\n")
        f.write("** ----------------------------------------------------------\n")
        f.write("** NODES\n")
        f.write("** ----------------------------------------------------------\n")
        f.write("*Node\n")
        for nid in sorted(nodes.keys()):
            p = nodes[nid]
            f.write(f"{nid:8d}, {p[0]:15.8e}, {p[1]:15.8e}\n")

        f.write("** ----------------------------------------------------------\n")
        f.write("** ELEMENTS (LAYER 1 PHASE UEL U1, LAYER 2 MECH UEL U2)\n")
        f.write("** ----------------------------------------------------------\n")
        f.write("*User Element, nodes=4, type=U1, properties=6, coordinates=2, variables=18\n3\n")
        f.write("*User Element, nodes=4, type=U2, properties=6, coordinates=2, variables=18\n1, 2\n")

        # Layer 1: Phase quads
        f.write("*Element, type=U1, elset=PHASE_QUADS\n")
        for eid in sorted(elements.keys()):
            conn = elements[eid]
            f.write(f"{eid:8d}, {conn[0]:8d}, {conn[1]:8d}, {conn[2]:8d}, {conn[3]:8d}\n")

        # Layer 2: Mechanical quads
        f.write("*Element, type=U2, elset=MECH_QUADS\n")
        for eid in sorted(elements.keys()):
            conn = elements[eid]
            f.write(f"{eid + n_elems:8d}, {conn[0]:8d}, {conn[1]:8d}, {conn[2]:8d}, {conn[3]:8d}\n")

        # Node sets
        f.write("** ----------------------------------------------------------\n")
        f.write("** NODE SETS\n")
        f.write("** ----------------------------------------------------------\n")
        f.write("*Nset, nset=N_BOTTOM\n")
        for i in range(0, len(bottom_nodes), 16):
            f.write(", ".join(str(n) for n in bottom_nodes[i:i+16]) + "\n")

        f.write("*Nset, nset=N_PIN\n")
        f.write(f"{pin_nodes[0]}\n")

        f.write("*Nset, nset=N_TOP\n")
        for i in range(0, len(top_nodes), 16):
            f.write(", ".join(str(n) for n in top_nodes[i:i+16]) + "\n")

        f.write("*Nset, nset=N_RP\n")
        f.write(f"{rp_nid}\n")

        # Kinematic ties
        f.write("** ----------------------------------------------------------\n")
        f.write("** KINEMATIC TIE EQUATIONS IN DOF 2\n")
        f.write("** ----------------------------------------------------------\n")
        for tn in top_nodes:
            f.write("*Equation\n2\n")
            f.write(f"{tn}, 2, 1.0, {rp_nid}, 2, -1.0\n")

        # UEL Properties
        f.write("** ----------------------------------------------------------\n")
        f.write("** UEL PROPERTIES (l0=0.0075, Gc=0.0027, E=210.0, nu=0.3)\n")
        f.write("** ----------------------------------------------------------\n")
        f.write("*Uel Property, elset=PHASE_QUADS\n")
        f.write(f"0.0075, 0.0027, 210.0, 0.3, 1.0e-7, {n_elems}\n")
        f.write("*Uel Property, elset=MECH_QUADS\n")
        f.write(f"0.0075, 0.0027, 210.0, 0.3, 1.0e-7, {n_elems}\n")

        # Initial Boundary Conditions
        f.write("** ----------------------------------------------------------\n")
        f.write("** BOUNDARY CONDITIONS (INITIAL MODEL DEFINITION)\n")
        f.write("** ----------------------------------------------------------\n")
        f.write("*Boundary\n")
        f.write("N_PIN, 1, 1, 0.0\n")
        f.write("N_BOTTOM, 2, 2, 0.0\n")
        f.write("N_RP, 2, 2, 0.0\n")
        f.write("*INCLUDE, INPUT=initial_conditions_solution.inc\n")

        # Step 1: Re-equilibration solve
        f.write("** ----------------------------------------------------------\n")
        f.write("** STEP 1: C3-0 RE-EQUILIBRATION SOLVE\n")
        f.write("** ----------------------------------------------------------\n")
        f.write("*Step, name=C3_0_REEQUILIBRATION, nlgeom=NO, inc=100\n")
        f.write("*Static\n1.0, 1.0, 1e-05, 1.0\n")
        f.write("*Boundary\n")
        f.write("N_BOTTOM, 2, 2, 0.0\n")
        f.write("N_PIN, 1, 1, 0.0\n")
        f.write("N_TOP, 1, 1, 0.0\n")
        f.write("N_RP, 1, 1, 0.0\n")
        f.write(f"N_RP, 2, 2, {target_uy:.17g}\n")
        f.write("*INCLUDE, INPUT=active_set_boundary_cards.inc\n")
        f.write("*Output, field, frequency=1\n*Node Output\nU, RF\n")
        f.write("*Element Output, elset=MECH_QUADS\nSDV\n")
        f.write("*End Step\n")

    print(f"12. Assembled master deck: {master_inp_path.name} (SHA-256: {sha256_file(master_inp_path)})")

    # 13. Write Representative Datacheck Decks
    from scripts.state_transfer.driver_package146_147_pdas_continuation import split_keyword_blocks

    master_content = master_inp_path.read_text(encoding="utf-8")
    blocks = split_keyword_blocks(master_content)

    # 13a. Mechanical Datacheck Deck (DC_MECH)
    mech_dc_path = PACKAGE_DIR / "P171_MECHANICAL_DC.inp"
    prefix_mech = []
    for b in blocks:
        k = b.split("\n", 1)[0].strip().lower()
        if k.startswith("*step"):
            break
        if k.startswith(("*boundary", "*include")):
            continue
        prefix_mech.append(b)

    cards_mech = ["".join(prefix_mech), "*INCLUDE, INPUT=initial_conditions_solution.inc\n"]
    cards_mech += [
        "*Step, name=DC_MECH, nlgeom=NO, inc=1\n",
        "*Static\n1.0, 1.0, 1e-05, 1.0\n",
        "*Boundary\n",
        "N_BOTTOM, 2, 2, 0.0\nN_PIN, 1, 1, 0.0\nN_TOP, 1, 1, 0.0\n",
        "N_RP, 1, 1, 0.0\n",
        f"N_RP, 2, 2, {target_uy:.17g}\n",
        "*INCLUDE, INPUT=active_set_boundary_cards.inc\n",
        "*Output, field, frequency=1\n*Node Output\nU, RF\n",
        "*End Step\n"
    ]
    with open(mech_dc_path, "w", encoding="utf-8", newline="\n") as f:
        f.write("".join(cards_mech))
    print(f"13a. Wrote {mech_dc_path.name}")

    # 13b. Phase Datacheck Deck (DC_PHASE)
    phase_dc_path = PACKAGE_DIR / "P171_PHASE_DC.inp"
    prefix_phase = []
    for b in blocks:
        k = b.split("\n", 1)[0].strip().lower()
        if k.startswith("*step"):
            break
        if k.startswith(("*boundary", "*include", "*equation")):
            continue
        prefix_phase.append(b)

    cards_phase = ["".join(prefix_phase), "*INCLUDE, INPUT=initial_conditions_solution.inc\n"]
    cards_phase += [
        "*Step, name=DC_PHASE, nlgeom=NO, inc=1\n",
        "*Static\n1.0, 1.0, 1.0, 1.0\n",
        "*Boundary\n"
    ]
    for nid in sorted(disp.keys()):
        u = disp[nid]
        cards_phase.append(f"{nid}, 1, 1, {u[0]:.17g}\n{nid}, 2, 2, {u[1]:.17g}\n")
    cards_phase.append("*INCLUDE, INPUT=active_set_boundary_cards.inc\n")
    cards_phase += [
        "*Output, field, frequency=1\n*Node Output\nU\n",
        "*End Step\n"
    ]
    with open(phase_dc_path, "w", encoding="utf-8", newline="\n") as f:
        f.write("".join(cards_phase))
    print(f"13b. Wrote {phase_dc_path.name}")

    # 14. Write PBS Submission Script
    pbs_path = PACKAGE_DIR / "submit_M1_C6_P171_C3_0.pbs"
    pbs_content = f"""#!/bin/bash
#PBS -N M1_C6_P171_C3_0
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

export JOB_NAME="M1_C6_P171_C3_0"
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
python3 "${{repo}}/scripts/state_transfer/driver_package171_c6_coupled_pdas.py" \\
    --package "${{RUN_DIR}}" \\
    --output "${{RUN_DIR}}/equilibration_${{PBS_JOBID}}" \\
    --extractor "${{repo}}/scripts/validation/extract_package148_iteration.py" \\
    --memory-gb 16 \\
    --timeout 25200 \\
    --max-outer 100
EXIT_CODE=$?

echo "Stage C3-0 Re-equilibration (Package 171 C6 Coupled PDAS) finished with exit code: ${{EXIT_CODE}}"
exit ${{EXIT_CODE}}
"""
    with open(pbs_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(pbs_content)
    print(f"14. Wrote {pbs_path.name}")

    # Copy job_notifications.sh
    shutil.copyfile(REPO_ROOT / "models/pandey_kumar_mode1/168_c5_companion_miseseri/job_notifications.sh", PACKAGE_DIR / "job_notifications.sh")

    # 15. Write Datacheck execution script for cluster
    dc_sh_path = PACKAGE_DIR / "run_datacheck.sh"
    dc_sh_content = f"""#!/bin/bash
set -euo pipefail
cd "{REMOTE_RUN_DIR}"

if ! type module >/dev/null 2>&1; then
    source /etc/profile.d/lmod.sh 2>/dev/null || source /usr/share/Modules/init/bash 2>/dev/null || true
fi
module purge
module load gcc/11.4.0 intel/2024.2.0 abaqus/2023
command -v ifort

echo "=== Running Mechanical Subproblem Datacheck ==="
abaqus job=P171_MECHANICAL_DC user=f42_mixed_uel.for input=P171_MECHANICAL_DC.inp cpus=1 memory="8 gb" datacheck interactive > P171_MECHANICAL_DC.stdout.txt 2>&1
test -f "P171_MECHANICAL_DC.dat"
grep -q 'THE ANALYSIS HAS COMPLETED SUCCESSFULLY' "P171_MECHANICAL_DC.dat" || grep -q 'ANALYSIS DATACHECK COMPLETE' "P171_MECHANICAL_DC.dat"
if grep -q '\\*\\*\\*ERROR' "P171_MECHANICAL_DC.dat"; then echo "MECHANICAL DATACHECK ERROR"; exit 66; fi
echo "P171_MECHANICAL_DC: AUTHENTIC_DATACHECK_PASS"

echo "=== Running Phase Subproblem Datacheck ==="
abaqus job=P171_PHASE_DC user=f42_mixed_uel.for input=P171_PHASE_DC.inp cpus=1 memory="8 gb" datacheck interactive > P171_PHASE_DC.stdout.txt 2>&1
test -f "P171_PHASE_DC.dat"
grep -q 'THE ANALYSIS HAS COMPLETED SUCCESSFULLY' "P171_PHASE_DC.dat" || grep -q 'ANALYSIS DATACHECK COMPLETE' "P171_PHASE_DC.dat"
if grep -q '\\*\\*\\*ERROR' "P171_PHASE_DC.dat"; then echo "PHASE DATACHECK ERROR"; exit 67; fi
echo "P171_PHASE_DC: AUTHENTIC_DATACHECK_PASS"
"""
    with open(dc_sh_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(dc_sh_content)
    print(f"15. Wrote {dc_sh_path.name}")

    # 16. Package Manifest
    package_files = [
        "M1_C6_PACKAGE171_C3_0_REEQUILIBRATION.inp",
        "P171_MECHANICAL_DC.inp",
        "P171_PHASE_DC.inp",
        "nodal_displacements_initial.csv",
        "nodal_phase_field_initial.csv",
        "d_lower_bounds.csv",
        "initial_conditions_solution.inc",
        "active_set_boundary_cards.inc",
        "f42_mixed_uel.for",
        "submit_M1_C6_P171_C3_0.pbs",
        "job_notifications.sh",
        "run_datacheck.sh"
    ]
    manifest_dict = {
        "package_number": 171,
        "package_name": "MODE1_PACKAGE_171_C6_STAGE_C3_0_REEQUILIBRATION",
        "discretization": "C6_CONFORMAL_QUAD",
        "num_elements": num_elems,
        "num_nodes": num_nodes,
        "duplicate_slit_pairs": num_slit,
        "donor_source": {
            "checkpoint": "CheckPoint03_Job1419566",
            "target_uy_mm": target_uy,
            "reference_force_kN": 0.17992419004440308,
            "reference_total_energy_kNmm": 0.00022639903
        },
        "files": {fname: sha256_file(PACKAGE_DIR / fname).lower() for fname in package_files}
    }
    with open(PACKAGE_DIR / "PACKAGE_MANIFEST.json", "w", encoding="utf-8") as f:
        json.dump(manifest_dict, f, indent=2)
    print(f"16. Wrote PACKAGE_MANIFEST.json")

    # 17. Batch Authorization
    qsub_cmd = f'powershell -NoProfile -ExecutionPolicy Bypass -File .\\.agents\\scripts\\Invoke-GuardedSsh.ps1 -RemoteCommand "qsub -q entry_imfdfkmq {REMOTE_RUN_DIR}/submit_M1_C6_P171_C3_0.pbs"'
    cmd_hash = hashlib.sha256(canonical(qsub_cmd).encode("utf-8")).hexdigest()

    auth_files = {fname: sha256_file(PACKAGE_DIR / fname).lower() for fname in package_files}
    auth_files["PACKAGE_MANIFEST.json"] = sha256_file(PACKAGE_DIR / "PACKAGE_MANIFEST.json").lower()
    # Datacheck files will be populated post-datacheck
    auth_dict = {
        "batch_name": "MODE1_PACKAGE_171_C6_STAGE_C3_0_REEQUILIBRATION",
        "adapter": "mode1-qualified-batch-v2",
        "scientific_scope": "MODE1",
        "technical_stage": "MODE1_BASELINE",
        "configuration": "MODE1_BASELINE",
        "max_submissions": 1,
        "hours_valid": 24,
        "automatic_retry": False,
        "remote_run_dir": REMOTE_RUN_DIR,
        "runtime_root": f"{REMOTE_RUN_DIR}/runtime",
        "runtime_source_hashes": {
            "scripts/state_transfer/c4_to_c5_spatial_mapping.py": sha256_file(REPO_ROOT / "scripts/state_transfer/c4_to_c5_spatial_mapping.py"),
            "scripts/state_transfer/driver_package146_147_pdas_continuation.py": sha256_file(REPO_ROOT / "scripts/state_transfer/driver_package146_147_pdas_continuation.py"),
            "scripts/state_transfer/driver_package171_c6_coupled_pdas.py": sha256_file(REPO_ROOT / "scripts/state_transfer/driver_package171_c6_coupled_pdas.py"),
            "scripts/validation/extract_package148_iteration.py": sha256_file(REPO_ROOT / "scripts/validation/extract_package148_iteration.py"),
        },
        "files": auth_files,
        "scientific_predecessor_review": "results/validation/c6_stage_c3_0_solver_evaluation.json",
        "jobs": [
            {
                "id": "M1_C6_P171_C3_0",
                "pbs": "submit_M1_C6_P171_C3_0.pbs",
                "command": qsub_cmd,
                "command_sha256": cmd_hash,
                "max_submissions": 1,
                "depends_on": [],
                "purpose": "Package 171: Stage C3-0 authentic coupled PDAS re-equilibration on C6 mesh (15,252 quads) at uy = 0.0018703125 mm",
                "cpus": 1,
                "memory_gb": 16,
                "walltime_hours": 8,
                "queue": "entry_imfdfkmq",
                "execution": "single-rank serial",
                "input": "P171_MECHANICAL_DC.inp",
                "datacheck": "P171_MECHANICAL_DC.dat",
                "additional_datachecks": ["P171_PHASE_DC.dat"]
            }
        ],
        "acceptance": {
            "M1_C6_P171_C3_0": "Stage C3-0 genuine coupled re-equilibration: Delta d <= 1e-5, Delta u <= 1e-9 mm, KKT satisfied, zero healing, reaction force drift <= 2%, total energy drift <= 2% vs Checkpoint 03."
        }
    }
    with open(PACKAGE_DIR / "M1_C6_PACKAGE171_AUTHORIZATION.json", "w", encoding="utf-8") as f:
        json.dump(auth_dict, f, indent=2)
    print(f"17. Wrote M1_C6_PACKAGE171_AUTHORIZATION.json")

    # 18. Execution Manifest
    with open(PACKAGE_DIR / "EXECUTION_MANIFEST.json", "w", encoding="utf-8") as f:
        json.dump(auth_dict, f, indent=2)
    print(f"18. Wrote EXECUTION_MANIFEST.json")

    # 19. Assembly Validation Artifact
    val_artifact = {
        "schema": 1,
        "task_id": "F1598-PACKAGE166-CONVERGENCE-ACCEPTANCE",
        "evaluation_name": "PACKAGE_171_C6_STAGGERED_PDAS_ASSEMBLY_VALIDATION",
        "status": "PACKAGE_171_ASSEMBLED__AWAITING_DATACHECK",
        "mesh_stats": {
            "elements": num_elems,
            "nodes": num_nodes,
            "duplicate_slit_pairs": num_slit,
            "min_det_jac": min_det
        },
        "transferred_state": {
            "min_damage": min_d,
            "max_damage": max_d,
            "min_history": min_h,
            "elastic_continuity_pct": el_gate["elastic_discrepancy_pct"],
            "fracture_continuity_pct": frac_gate["fracture_discrepancy_pct"],
            "total_energy_continuity_pct": tot_gate["total_energy_discrepancy_pct"]
        },
        "uel_preserved": uel_hash == FROZEN_UEL_HASH,
        "verification_passed": True
    }
    val_path = REPO_ROOT / "results/validation/c6_package171_assembly_validation.json"
    with open(val_path, "w", encoding="utf-8") as f:
        json.dump(val_artifact, f, indent=2)
    print(f"19. Wrote assembly validation: {val_path.name}")
    print("=" * 80)
    print("PACKAGE 171 ASSEMBLY COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()
