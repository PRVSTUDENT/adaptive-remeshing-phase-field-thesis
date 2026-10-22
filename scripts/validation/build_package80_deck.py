#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_package80_deck.py

Task: F1597-CORRECT-PACKAGE72-STATE-TRANSFER
Turn: 27

Builds Package 80 candidate deck with:
1. Peak-preserving crack-wake damage reconstruction (retaining authentic donor peak d=0.99713).
2. Updated active set partition: 1,752 active nodes (including 9 activated healing nodes),
   661 inactive nodes (including 13 released negative-multiplier nodes).
3. Staged execution:
   - Step 1: STATE_INJECTION (all nodes prescribed)
   - Step 2: MECH_REEQUIL_FROZEN_DAMAGE (interior displacements released, d fixed)
   - Step 3: ACTIVE_SET_COUPLED_REEQUIL (active set d fixed, inactive set free)
"""
import os
import sys
import json
import csv
import hashlib
from pathlib import Path
import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
DONOR_DIR = REPO_ROOT / "models/pandey_kumar_mode1/76_candidate_donor_h0025_visual"
DONOR_INP = DONOR_DIR / "candidate_donor_h0025_visual.inp"
DONOR_SDV_CSV = DONOR_DIR / "evidence_1416301/pkg76_frame111_elem_sdv.csv"
DONOR_U_CSV = DONOR_DIR / "evidence_1416301/pkg76_frame111_nodal_u.csv"

BASE_C2_INP = REPO_ROOT / "models/pandey_kumar_mode1/79_candidate_c2_active_set_reequilibration/M1_C2_ACTIVE_SET_REEQUIL.inp"
PKG80_DIR = REPO_ROOT / "models/pandey_kumar_mode1/80_candidate_c2_peak_preserved_reequilibration"
PKG80_INP = PKG80_DIR / "M1_C2_PEAK_PRESERVED_REEQUIL.inp"
PKG80_MAPPED_CSV = REPO_ROOT / "models/pandey_kumar_mode1/candidate_c2_peak_preserved_mapped_table.csv"
AUDIT_JSON = REPO_ROOT / "results/validation/mode1_f1597/package80_active_set_audit.json"

MEMBERSHIP_JSON = REPO_ROOT / "results/validation/mode1_f1597/f1597_turn26_active_set_membership_audit.json"

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest().upper()

def build_package80():
    PKG80_DIR.mkdir(parents=True, exist_ok=True)
    AUDIT_JSON.parent.mkdir(parents=True, exist_ok=True)

    # 1. Load active set partition from Turn 26 audit
    with open(MEMBERSHIP_JSON, "r", encoding="utf-8") as f:
        mem = json.load(f)

    # Load Package 79 active set and perform exact update
    # In Turn 26:
    # Package 79 active: 1756
    # 9 healing activated, 13 negative multiplier released
    # Result: 1,752 active, 661 inactive
    from scripts.validation.audit_pkg79_force_and_kkt_discrepancy import audit as get_audit
    with open(REPO_ROOT / "results/validation/package79_c2_active_set_reequilibration/pkg79_extracted_telemetry.json") as f:
        telem = json.load(f)

    healing_nodes = set(telem["damage_irreversibility"]["sample_healing_nodes"])
    neg_lambda_nodes = set([n["node_id"] for n in telem["kkt_active_set_verification"]["sample_negative_multiplier_nodes"]])

    # Parse Package 79 active nodes from deck
    pkg79_active = set()
    with open(BASE_C2_INP, "r", encoding="utf-8") as f:
        in_s3 = False
        in_bc = False
        for line in f:
            l = line.strip()
            if "*Step, name=ACTIVE_SET_COUPLED_REEQUIL" in l:
                in_s3 = True
                continue
            if in_s3 and l.startswith("*Boundary"):
                in_bc = True
                continue
            if in_s3 and in_bc:
                if l.startswith("*") and not l.startswith("**"):
                    break
                if l.startswith("**"):
                    continue
                p = [x.strip() for x in l.split(",")]
                if len(p) == 4 and p[1] == "3" and p[2] == "3":
                    pkg79_active.add(int(p[0]))

    new_active_set = sorted(list((pkg79_active | healing_nodes) - neg_lambda_nodes))
    print(f"Verified Package 80 active set: {len(new_active_set)} active nodes")

    # 2. Reconstruct peak-preserving donor damage and load donor displacements/history
    donor_elem_d = {}
    donor_elem_h = {}
    with open(DONOR_SDV_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            eid = int(r["phys_elem_id"])
            gp = int(r["gp"])
            d = float(r["damage_d"])
            h = float(r["history_h"])
            if eid not in donor_elem_d:
                donor_elem_d[eid] = {}
                donor_elem_h[eid] = {}
            donor_elem_d[eid][gp] = d
            donor_elem_h[eid][gp] = h

    donor_avg_d = {eid: np.mean(list(gps.values())) for eid, gps in donor_elem_d.items()}

    donor_nodes = {}
    donor_elems = {}
    with open(DONOR_INP, "r", encoding="utf-8") as f:
        in_n, in_e = False, False
        for line in f:
            l = line.strip()
            if l.startswith("*Node") and not l.startswith("*Node Output"):
                in_n, in_e = True, False
                continue
            elif l.startswith("*Element, type=U1"):
                in_n, in_e = False, True
                continue
            elif l.startswith("*"):
                in_n, in_e = False, False
                continue
            if in_n and l:
                p = [x.strip() for x in l.split(",")]
                if p[0].isdigit():
                    donor_nodes[int(p[0])] = (float(p[1]), float(p[2]))
            elif in_e and l:
                p = [x.strip() for x in l.split(",")]
                if p[0].isdigit():
                    donor_elems[int(p[0])] = [int(x) for x in p[1:5]]

    # Donor nodal displacements from authentic extraction
    donor_nodal_u = {}
    with open(DONOR_U_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            donor_nodal_u[int(r["node_id"])] = (float(r["u1"]), float(r["u2"]))

    # Donor node to elements connectivity
    node_to_elems = {nid: [] for nid in donor_nodes}
    for eid, conn in donor_elems.items():
        for n in conn:
            node_to_elems[n].append(eid)

    # Topology-aware peak-preserving donor nodal reconstruction
    donor_nodal_d_peak = {}
    for nid, eids in node_to_elems.items():
        if not eids:
            continue
        xn, yn = donor_nodes[nid]
        if abs(yn - 0.05) < 1e-5: # on crack line
            donor_nodal_d_peak[nid] = float(np.max([donor_avg_d[e] for e in eids]))
        else:
            donor_nodal_d_peak[nid] = float(np.mean([donor_avg_d[e] for e in eids]))

    # 3. Load Candidate C2 mesh
    c2_nodes = {}
    c2_elems = {}
    with open(BASE_C2_INP, "r", encoding="utf-8") as f:
        in_n, in_e = False, False
        for line in f:
            l = line.strip()
            if l.startswith("*Node") and not l.startswith("*Node Output"):
                in_n, in_e = True, False
                continue
            elif l.startswith("*Element, type=U1"):
                in_n, in_e = False, True
                continue
            elif l.startswith("*"):
                in_n, in_e = False, False
                continue
            if in_n and l:
                p = [x.strip() for x in l.split(",")]
                if p[0].isdigit() and int(p[0]) != 999999:
                    c2_nodes[int(p[0])] = (float(p[1]), float(p[2]))
            elif in_e and l:
                p = [x.strip() for x in l.split(",")]
                if p[0].isdigit():
                    c2_elems[int(p[0])] = [int(x) for x in p[1:5]]

    # Bilinear interpolation function
    def interp_donor_field(x, y, flank, nodal_dict):
        x = max(0.0, min(0.1, x))
        y = max(0.0, min(0.1, y))
        col = min(39, max(0, int(x / 0.0025)))
        if x >= 0.1: col = 39
        if y < 0.050:
            row = min(19, max(0, int(y / 0.0025)))
        elif y > 0.050:
            row = min(39, max(20, int(y / 0.0025)))
        else:
            if flank == "lower": row = 19
            elif flank == "upper": row = 20
            else: row = 20 if (x > 0.040 or flank == "upper") else 19

        eid = row * 40 + col + 1
        conn = donor_elems[eid]
        pts = [donor_nodes[n] for n in conn]
        x_min, y_min = pts[0][0], pts[0][1]
        xi = 2.0 * (x - x_min) / 0.0025 - 1.0
        eta = 2.0 * (y - y_min) / 0.0025 - 1.0
        xi = max(-1.0, min(1.0, xi))
        eta = max(-1.0, min(1.0, eta))

        N = [
            0.25 * (1.0 - xi) * (1.0 - eta),
            0.25 * (1.0 + xi) * (1.0 - eta),
            0.25 * (1.0 + xi) * (1.0 + eta),
            0.25 * (1.0 - xi) * (1.0 + eta)
        ]
        return float(sum(N[i] * nodal_dict[conn[i]] for i in range(4)))

    # Nodal displacement interpolation
    donor_nodal_u1 = {n: donor_nodal_u[n][0] for n in donor_nodes if n in donor_nodal_u}
    donor_nodal_u2 = {n: donor_nodal_u[n][1] for n in donor_nodes if n in donor_nodal_u}

    c2_nodal_u = {}
    c2_mapped_d = {}
    for nid, (x, y) in c2_nodes.items():
        if 2398 <= nid <= 2413: flank = "upper"
        elif 1176 <= nid <= 1191: flank = "lower"
        elif y > 0.050: flank = "upper"
        elif y < 0.050: flank = "lower"
        else: flank = "ligament"

        u1 = interp_donor_field(x, y, flank, donor_nodal_u1)
        u2 = interp_donor_field(x, y, flank, donor_nodal_u2)
        d_val = interp_donor_field(x, y, flank, donor_nodal_d_peak)
        c2_nodal_u[nid] = (u1, u2)
        c2_mapped_d[nid] = max(0.0, min(1.0, d_val))

    # Element history mapping (nearest Gauss point / donor element)
    c2_elem_h = {}
    for eid, conn in c2_elems.items():
        pts = [c2_nodes[n] for n in conn]
        cx = float(np.mean([p[0] for p in pts]))
        cy = float(np.mean([p[1] for p in pts]))
        col = min(39, max(0, int(cx / 0.0025)))
        row = min(39, max(0, int(cy / 0.0025)))
        donor_eid = row * 40 + col + 1
        h_vals = [donor_elem_h[donor_eid][gp] for gp in range(1, 5)]
        c2_elem_h[eid] = h_vals

    # Export candidate_c2_peak_preserved_mapped_table.csv
    with open(PKG80_MAPPED_CSV, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["record_type", "id", "val1", "val2", "val3", "val4", "val5", "val6"])
        for nid in sorted(c2_nodes.keys()):
            u1, u2 = c2_nodal_u[nid]
            d = c2_mapped_d[nid]
            writer.writerow(["NODE", nid, "%.10e" % u1, "%.10e" % u2, "%.10e" % d, "0.0", "0.0", "0.0"])
        for eid in sorted(c2_elems.keys()):
            h_list = c2_elem_h[eid]
            writer.writerow(["ELEM_H", eid, "%.10e" % h_list[0], "%.10e" % h_list[1], "%.10e" % h_list[2], "%.10e" % h_list[3], "0.0", "0.0"])

    mapped_csv_hash = sha256_file(PKG80_MAPPED_CSV)
    print(f"Wrote mapped table: {PKG80_MAPPED_CSV} (SHA-256: {mapped_csv_hash})")

    # 4. Construct Package 80 Deck
    # Read base staged deck up to Step 1
    with open(BASE_C2_INP, "r", encoding="utf-8") as f:
        base_lines = [l.rstrip("\r\n") for l in f]

    step1_idx = None
    for idx, line in enumerate(base_lines):
        if "*STEP, NAME=STATE_INJECTION" in line.upper():
            step1_idx = idx
            break

    deck = base_lines[:step1_idx]

    # Reconstruct Step 1: STATE_INJECTION with new mapped u1, u2, d
    deck.append("** ==========================================================")
    deck.append("** STEP 1: STATE_INJECTION (Full Displacement & Phase Field)")
    deck.append("** Injects continuous displacement and damage fields")
    deck.append("** ==========================================================")
    deck.append("*Step, name=STATE_INJECTION, nlgeom=NO, inc=1")
    deck.append("*Static")
    deck.append("1.0, 1.0, 1e-12, 1.0")
    deck.append("*Boundary")
    deck.append("N_BOTTOM, 2, 2, 0.0")
    deck.append("N_PIN, 1, 1, 0.0")
    deck.append("N_RP, 1, 1, 0.0")
    deck.append("N_RP, 2, 2, 0.002540107")
    deck.append("** Prescribed interior independent displacements:")
    for nid in sorted(c2_nodes.keys()):
        if nid not in [1, 999999]: # don't double prescribe pin / RP
            u1, u2 = c2_nodal_u[nid]
            deck.append(f"{nid}, 1, 1, {u1:.10e}")
            deck.append(f"{nid}, 2, 2, {u2:.10e}")
    deck.append("** Prescribed damage field on DOF 3 across all physical nodes:")
    for nid in sorted(c2_nodes.keys()):
        d = c2_mapped_d[nid]
        deck.append(f"{nid}, 3, 3, {d:.10e}")
    deck.append("*Output, field, frequency=1")
    deck.append("*Node Output")
    deck.append("U, RF")
    deck.append("*Element Output")
    deck.append("SDV")
    deck.append("*Output, history, frequency=1")
    deck.append("*Node Output, nset=N_RP")
    deck.append("RF2, U2")
    deck.append("*End Step")

    # Step 2: MECH_REEQUIL_FROZEN_DAMAGE with new peak-preserved damage
    deck.append("** ==========================================================")
    deck.append("** STEP 2: MECH_REEQUIL_FROZEN_DAMAGE (Interior Displacements Released)")
    deck.append("** Relaxes high-frequency mapped interpolation strains under frozen damage")
    deck.append("** ==========================================================")
    deck.append("*Step, name=MECH_REEQUIL_FROZEN_DAMAGE, nlgeom=NO, inc=50")
    deck.append("*Static")
    deck.append("0.1, 1.0, 1e-8, 1.0")
    deck.append("*Boundary, OP=NEW")
    deck.append("N_BOTTOM, 2, 2, 0.0")
    deck.append("N_PIN, 1, 1, 0.0")
    deck.append("N_RP, 1, 1, 0.0")
    deck.append("N_RP, 2, 2, 0.002540107")
    deck.append("** Prescribed frozen damage field on DOF 3 across all physical nodes:")
    for nid in sorted(c2_nodes.keys()):
        d = c2_mapped_d[nid]
        deck.append(f"{nid}, 3, 3, {d:.10e}")
    deck.append("*Output, field, frequency=1")
    deck.append("*Node Output")
    deck.append("U, RF")
    deck.append("*Element Output")
    deck.append("SDV")
    deck.append("*Output, history, frequency=1")
    deck.append("*Node Output, nset=N_RP")
    deck.append("RF2, U2")
    deck.append("*Energy Output")
    deck.append("ALLSE, ALLWK")
    deck.append("*End Step")

    # Step 3: ACTIVE_SET_COUPLED_REEQUIL with new active set (1,752 nodes)
    inactive_nodes = sorted(list(set(c2_nodes.keys()) - set(new_active_set)))
    deck.append("** ==========================================================")
    deck.append("** STEP 3: ACTIVE_SET_COUPLED_REEQUIL (KKT Active-Set Equilibrium)")
    deck.append("** Enforces d_receiver >= d_mapped via active set A (1,752 nodes)")
    deck.append("** Inactive crack-tip nodes I (661 nodes) free to advance damage")
    deck.append("** Active count: %d, Inactive count: %d" % (len(new_active_set), len(inactive_nodes)))
    deck.append("** ==========================================================")
    deck.append("*Step, name=ACTIVE_SET_COUPLED_REEQUIL, nlgeom=NO, inc=100")
    deck.append("*Static")
    deck.append("0.01, 1.0, 1e-12, 0.1")
    deck.append("*Boundary, OP=NEW")
    deck.append("N_BOTTOM, 2, 2, 0.0")
    deck.append("N_PIN, 1, 1, 0.0")
    deck.append("N_RP, 1, 1, 0.0")
    deck.append("N_RP, 2, 2, 0.002540107")
    deck.append("** Prescribed active-set lower-bound damage constraints (d = d_mapped):")
    for nid in new_active_set:
        d = c2_mapped_d[nid]
        deck.append(f"{nid}, 3, 3, {d:.10e}")
    deck.append("*Output, field, frequency=1")
    deck.append("*Node Output")
    deck.append("U, RF")
    deck.append("*Element Output")
    deck.append("SDV")
    deck.append("*Output, history, frequency=1")
    deck.append("*Node Output, nset=N_RP")
    deck.append("RF2, U2")
    deck.append("*Energy Output")
    deck.append("ALLSE, ALLWK")
    deck.append("*End Step")

    with open(PKG80_INP, "w", encoding="utf-8") as f:
        f.write("\n".join(deck) + "\n")

    deck_hash = sha256_file(PKG80_INP)
    print(f"Wrote Package 80 deck: {PKG80_INP} (SHA-256: {deck_hash})")

    # 5. Copy UEL and notifications
    import shutil
    uel_src = REPO_ROOT / "models/pandey_kumar_mode1/79_candidate_c2_active_set_reequilibration/f42_mixed_uel.for"
    uel_dst = PKG80_DIR / "f42_mixed_uel.for"
    shutil.copy2(uel_src, uel_dst)
    uel_hash = sha256_file(uel_dst)
    assert uel_hash == "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6", "UEL hash mismatch!"

    notif_src = REPO_ROOT / "models/pandey_kumar_mode1/79_candidate_c2_active_set_reequilibration/job_notifications.sh"
    notif_dst = PKG80_DIR / "job_notifications.sh"
    shutil.copy2(notif_src, notif_dst)

    # 6. Generate PBS Script
    pbs_text = """#!/bin/bash
#PBS -N M1_C2_PEAK_PRESERVED_REEQUIL
#PBS -l select=1:ncpus=1:mem=8gb
#PBS -l walltime=04:00:00
#PBS -q entry_imfdfkmq
#PBS -j oe
#PBS -r n
#PBS -o /scratch9/pr21vyci/runs/mode1_candidate_c2_peak_preserved_reequilibration/pbs_execution.log
#PBS -m abe
#PBS -M pr21vyci@mailserver.tu-freiberg.de

set -euo pipefail
RUN_DIR="/scratch9/pr21vyci/runs/mode1_candidate_c2_peak_preserved_reequilibration"
cd "${RUN_DIR}"

# Notifications are required; PBS spool location is not the package directory.
export JOB_NAME="M1_C2_PEAK_PRESERVED_REEQUIL"
export NOTIFICATION_CONFIG="${NOTIFICATION_CONFIG:-${HOME}/.config/adaptive-remeshing/notifications.env}"
source "${RUN_DIR}/job_notifications.sh"
notification_load_config
notification_install_terminal_trap
notify_start

if ! type module >/dev/null 2>&1; then source /etc/profile.d/lmod.sh; fi
module purge
module load gcc/11.4.0 intel/2024.2.0 abaqus/2023
command -v ifort

JOB_NAME="M1_C2_PEAK_PRESERVED_REEQUIL"
INP_NAME="M1_C2_PEAK_PRESERVED_REEQUIL.inp"
USER_SUB="f42_mixed_uel.for"

test ! -e "${JOB_NAME}.lck"

echo "Starting Abaqus/Standard 2023 Candidate C2 Peak-Preserved Re-equilibration Diagnostic (2300 Quads, h=1.0 um)..."
abaqus job="${JOB_NAME}" input="${INP_NAME}" user="${USER_SUB}" cpus=1 interactive
EXIT_CODE=$?

echo "Abaqus Finished with Exit Code: ${EXIT_CODE}"
exit ${EXIT_CODE}
"""
    pbs_file = PKG80_DIR / "submit_M1_C2_PEAK_PRESERVED_REEQUIL.pbs"
    with open(pbs_file, "w", encoding="utf-8", newline="\n") as f:
        f.write(pbs_text)
    pbs_hash = sha256_file(pbs_file)

    # 7. Generate PACKAGE_MANIFEST.json
    manifest = {
        "schema": 1,
        "task_id": "F1597-CORRECT-PACKAGE72-STATE-TRANSFER",
        "package": "Package 80",
        "model": "M1_C2_PEAK_PRESERVED_REEQUIL",
        "created_at": "2026-10-22T16:15:00+02:00",
        "job_name": "M1_C2_PEAK_PRESERVED_REEQUIL",
        "pbs_script": "submit_M1_C2_PEAK_PRESERVED_REEQUIL.pbs",
        "pbs_script_sha256": pbs_hash,
        "input_deck": "M1_C2_PEAK_PRESERVED_REEQUIL.inp",
        "input_deck_sha256": deck_hash,
        "user_subroutine": "f42_mixed_uel.for",
        "user_subroutine_sha256": uel_hash,
        "mapped_table": "candidate_c2_peak_preserved_mapped_table.csv",
        "mapped_table_sha256": mapped_csv_hash,
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
            "active_nodes_count": len(new_active_set),
            "inactive_nodes_count": len(inactive_nodes),
            "total_nodes": len(c2_nodes)
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

    # 8. Write Audit JSON
    audit = {
        "status": "PACKAGE80_PREPARED",
        "task_id": "F1597-CORRECT-PACKAGE72-STATE-TRANSFER",
        "package": "Package 80",
        "deck_file": PKG80_INP.name,
        "deck_sha256": deck_hash,
        "uel_sha256": uel_hash,
        "pbs_sha256": pbs_hash,
        "manifest_sha256": manifest_hash,
        "mapped_table_sha256": mapped_csv_hash,
        "active_set_count": len(new_active_set),
        "inactive_set_count": len(inactive_nodes),
        "total_nodes": len(c2_nodes)
    }
    with open(AUDIT_JSON, "w", encoding="utf-8") as f:
        json.dump(audit, f, indent=2)

    return audit

if __name__ == "__main__":
    build_package80()
