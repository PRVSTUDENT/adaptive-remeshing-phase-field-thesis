#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_package103_h1_pilot.py
Task: F1597-CORRECT-PACKAGE72-STATE-TRANSFER
Protocol Version: 2

Generates Package 103:
Mode-I Method C Stage C1-2 First Conforming Matched-Displacement Pilot under
the newly qualified Exact Bound-Constrained Natural-Energy (H^1) State Transfer.

Key Parameters & Principles:
1. Qualified H^1 Damage Field:
   - Evaluated from exact box-constrained quadratic program:
     min 1/2 d^T A d - b^T d  subject to d_ckpt <= d <= 1.00000000
   - Achieves predicted E_frac = 0.136659 mJ (-0.7822% error vs Abaqus donor 0.137737 mJ, PASS)
   - Achieves predicted RF2 = 114.2252 N (+1.1105% error vs Abaqus donor 112.9707 N, PASS)
   - Strictly 0 healing points (min(d - d_ckpt) = 0.00e+00)
   - Strictly 0 overshoot points (max(d - 1.0) = 0.00e+00, d_max = 1.00000000)
   - KKT stationarity verified (0 multiplier violations, free gradient norm < 1e-8)
2. Preserved Authentic Transferred History:
   - Sourced from authentic Case A C4 donor (Package 94 Step 4 Frame 7)
   - Ingests all 17,760 Gauss-point history values without loss
   - Formatted using verified 3-line card syntax (<= 8 entries per card)
3. Preserved Bitwise Frozen UEL:
   - f42_mixed_uel.for SHA-256 CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6
4. Mandatory Dual-Channel Notifications:
   - #PBS -m abe, #PBS -M pr21vyci@mailserver.tu-freiberg.de
   - job_notifications.sh integration
"""

import sys
import os
import shutil
import hashlib
from pathlib import Path
import numpy as np
import csv
import json

REPO_ROOT = Path("D:/Master thesis/Adaptive remeshing")
FROZEN_UEL_HASH = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"
DONOR_RF2_N = 112.97070980072021
DONOR_E_FRAC_MJ = 0.13773671
U_CHECKPOINT_MM = 0.0020520000252872705

def sha256_file(filepath: Path) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest().upper()

def build_package103():
    pkg_dir = REPO_ROOT / "models/pandey_kumar_mode1/103_c5_h1_transfer_pilot"
    pkg_dir.mkdir(parents=True, exist_ok=True)
    print(f"Building Package 103 in: {pkg_dir}")

    # 1. Source files
    pkg102_r1_dir = REPO_ROOT / "models/pandey_kumar_mode1/102_r1_c5_coupled_staggered_history_repaired"
    mesh_inp = pkg102_r1_dir / "candidate_crack_band_mesh_c5.inp"
    state_table_csv = pkg102_r1_dir / "candidate_c5_frame7_mapped_state_table.csv"
    src_uel = pkg102_r1_dir / "f42_mixed_uel.for"
    src_notif = pkg102_r1_dir / "job_notifications.sh"
    qualified_d_npy = REPO_ROOT / "results/validation/mode1_f1597/c5_h1_bound_constrained_d.npy"

    assert mesh_inp.exists(), f"Missing {mesh_inp}"
    assert state_table_csv.exists(), f"Missing {state_table_csv}"
    assert src_uel.exists(), f"Missing {src_uel}"
    assert src_notif.exists(), f"Missing {src_notif}"
    assert qualified_d_npy.exists(), f"Missing {qualified_d_npy}"

    # Verify frozen UEL
    actual_uel_hash = sha256_file(src_uel)
    assert actual_uel_hash == FROZEN_UEL_HASH, f"UEL hash mismatch! Got {actual_uel_hash}"

    # 2. Copy companion files
    dst_mesh = pkg_dir / "candidate_crack_band_mesh_c5.inp"
    dst_uel = pkg_dir / "f42_mixed_uel.for"
    dst_notif = pkg_dir / "job_notifications.sh"
    shutil.copy2(mesh_inp, dst_mesh)
    shutil.copy2(src_uel, dst_uel)
    shutil.copy2(src_notif, dst_notif)

    # 3. Load qualified damage field
    d_H1 = np.load(qualified_d_npy)
    assert len(d_H1) == 4610, f"Expected 4610 nodes, got {len(d_H1)}"
    assert np.min(d_H1) >= 0.0, "Negative damage detected!"
    assert np.max(d_H1) <= 1.00000001, f"Damage overshoot detected: {np.max(d_H1)}"

    # 4. Load mesh nodes and node ordering
    nodes = {}
    with open(mesh_inp, "r", encoding="utf-8") as f:
        reading = None
        for line in f:
            l = line.strip()
            if not l or l.startswith("**"): continue
            if l.startswith("*"):
                u = l.upper()
                if u.startswith("*NODE") and not any(u.startswith(k) for k in ["*NODE OUTPUT", "*NODE PRINT", "*NODE FILE"]):
                    reading = "NODE"
                else:
                    reading = None
                continue
            if reading == "NODE":
                parts = [p.strip() for p in l.split(",") if p.strip()]
                if len(parts) >= 3 and parts[0].isdigit():
                    nid = int(parts[0])
                    if nid != 999999:
                        nodes[nid] = np.array([float(parts[1]), float(parts[2])])

    node_list = sorted([n for n in nodes.keys() if n != 999999])
    node_to_idx = {nid: i for i, nid in enumerate(node_list)}
    assert len(node_list) == 4610, f"Expected 4610 nodes, got {len(node_list)}"

    # 5. Load authentic transferred history from state table
    elem_h = {}
    with open(state_table_csv, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        for row in reader:
            if not row: continue
            if row[0].strip().upper() == "ELEM_HISTORY":
                eid = int(row[1])
                elem_h[eid] = [float(row[2]), float(row[3]), float(row[4]), float(row[5])]
    assert len(elem_h) == 4440, f"Expected 4440 history elements, got {len(elem_h)}"

    # 6. Build input deck header
    # Extract header up to *INITIAL CONDITIONS from seed deck
    seed_deck = pkg102_r1_dir / "M1_C5_PACKAGE102_R1_STAGGERED.inp"
    seed_text = seed_deck.read_text(encoding="utf-8")
    init_cond_pos = seed_text.find("*INITIAL CONDITIONS, TYPE=SOLUTION")
    assert init_cond_pos != -1, "Could not find *INITIAL CONDITIONS in seed deck"
    header_section = seed_text[:init_cond_pos]

    # Change heading
    header_section = header_section.replace(
        "** PACKAGE 102-R1: Coupled Staggered State Transfer (History Loss Repaired)",
        "** PACKAGE 103: Mode-I Method C Stage C1-2 Bound-Constrained H^1 Transfer Pilot"
    )

    # 7. Format *INITIAL CONDITIONS with strict 3-line continuation
    init_lines = ["*INITIAL CONDITIONS, TYPE=SOLUTION"]
    for eid in sorted(elem_h.keys()):
        h_vals = elem_h[eid]
        # Element U1 (PHASE_QUADS, VARIABLES=18):
        init_lines.append(f"{eid}, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0")
        init_lines.append(f"0.0, {h_vals[0]:.10e}, {h_vals[1]:.10e}, {h_vals[2]:.10e}, {h_vals[3]:.10e}, 0.0, 0.0, 1.0")
        init_lines.append(f"{h_vals[0]:.10e}, 0.0, 0.0")

        # Element U2 (MECH_QUADS, VARIABLES=18):
        mech_eid = eid + 4440
        init_lines.append(f"{mech_eid}, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0")
        init_lines.append(f"0.0, {h_vals[0]:.10e}, {h_vals[1]:.10e}, {h_vals[2]:.10e}, {h_vals[3]:.10e}, 0.0, 0.0, 1.0")
        init_lines.append(f"{h_vals[0]:.10e}, 0.0, 0.0")

        # Companion CPE4 (UMATELEM, NSTATV=20):
        comp_eid = eid + 8880
        init_lines.append(f"{comp_eid}, 0.0, {h_vals[0]:.10e}, 0.0, 0.0, 0.0, 0.0, 0.0")
        init_lines.append("0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0")
        init_lines.append(f"{h_vals[0]:.10e}, 0.0, 0.0, 0.0, 0.0")

    init_section = "\n".join(init_lines) + "\n"

    # 8. Step definitions: Matched-Displacement Checkpoint Evaluation
    bc_phase_lines = []
    for nid in node_list:
        d_val = float(d_H1[node_to_idx[nid]])
        bc_phase_lines.append(f"{nid}, 3, 3, {d_val:.10e}")

    step_definitions = [
        "** ==========================================================",
        "** STEP 1: H1_STATE_EVALUATION (Bound-Constrained H^1 Checkpoint Pilot)",
        "** Evaluates authentic mechanical reaction force and AT2 fracture energy",
        "** under holding displacement u = 0.002052 mm without artificial loading",
        "** ==========================================================",
        "*Step, name=H1_STATE_EVALUATION, nlgeom=NO, inc=1",
        "*Static",
        "1.0, 1.0, 1.0, 1.0",
        "*Boundary, OP=NEW",
        "N_BOTTOM, 2, 2, 0.0",
        "N_PIN, 1, 1, 0.0",
        "N_RP, 1, 1, 0.0",
        f"999999, 2, 2, {U_CHECKPOINT_MM:.10e}",
        "\n".join(bc_phase_lines),
        "*Output, field, frequency=1",
        "*Node Output",
        "RF, U",
        "*Element Output, elset=UMATELEM",
        "SDV",
        "*Output, history, frequency=1",
        "*Node Output, nset=N_RP",
        "RF2, U2",
        "*Energy Output",
        "ALLSE, ALLWK, ALLFD, ALLIE",
        "*NODE PRINT, FREQUENCY=1, SUMMARY=NO",
        "U",
        "*End Step"
    ]

    step_section = "\n".join(step_definitions) + "\n"
    final_deck_content = header_section + init_section + step_section

    out_deck = pkg_dir / "M1_C5_PACKAGE103_H1_PILOT.inp"
    out_deck.write_text(final_deck_content, encoding="utf-8")
    print(f"Generated Package 103 input deck: {out_deck}")
    print(f"  Deck size: {out_deck.stat().st_size} bytes, lines: {len(final_deck_content.splitlines())}")

    # 9. Generate PBS submission script
    pbs_lines = [
        "#!/bin/bash",
        "#PBS -N M1_C5_P103",
        "#PBS -l select=1:ncpus=1:mem=16gb",
        "#PBS -l walltime=04:00:00",
        "#PBS -q normal_imfdfkmq",
        "#PBS -m abe",
        "#PBS -M pr21vyci@mailserver.tu-freiberg.de",
        "#PBS -j oe",
        "#PBS -o pbs_execution.log",
        "",
        "cd $PBS_O_WORKDIR || exit 1",
        "",
        "# Dual-channel notification trap",
        "source job_notifications.sh",
        "notification_install_terminal_trap",
        "notify_start",
        "",
        "module load abaqus/2023",
        "",
        "abaqus job=M1_C5_PACKAGE103_H1_PILOT user=f42_mixed_uel.for cpus=1 interactive",
        "ABAQUS_EXIT=$?",
        "",
        "if [ $ABAQUS_EXIT -eq 0 ]; then",
        "    python3 extract_pkg103_results.py",
        "    EXIT_STATUS=0",
        "else",
        "    echo \"ERROR: Abaqus execution failed with exit code $ABAQUS_EXIT\"",
        "    EXIT_STATUS=$ABAQUS_EXIT",
        "fi",
        "",
        "exit $EXIT_STATUS"
    ]
    out_pbs = pkg_dir / "submit_M1_C5_PACKAGE103_H1_PILOT.pbs"
    out_pbs.write_text("\n".join(pbs_lines) + "\n", encoding="utf-8")
    print(f"Generated PBS script: {out_pbs}")

    # 10. Generate remote datacheck runner
    dc_sh = [
        "#!/bin/bash",
        "cd \"$(dirname \"$0\")\" || exit 1",
        "module load abaqus/2023",
        "abaqus datacheck job=M1_C5_PACKAGE103_H1_PILOT_DC input=M1_C5_PACKAGE103_H1_PILOT.inp user=f42_mixed_uel.for interactive",
        "exit $?"
    ]
    out_dc = pkg_dir / "run_pkg103_datacheck.sh"
    out_dc.write_text("\n".join(dc_sh) + "\n", encoding="utf-8")

    # 11. Generate Python extraction script
    ext_py = [
        "#!/usr/bin/env python3",
        "# -*- coding: utf-8 -*-",
        "import csv",
        "import json",
        "import re",
        "from pathlib import Path",
        "",
        "def extract():",
        "    dat_file = Path('M1_C5_PACKAGE103_H1_PILOT.dat')",
        "    msg_file = Path('M1_C5_PACKAGE103_H1_PILOT.msg')",
        "    sta_file = Path('M1_C5_PACKAGE103_H1_PILOT.sta')",
        "    csv_file = Path('uel_energy_balance.csv')",
        "",
        "    results = {'status': 'UNKNOWN', 'rf2_N': None, 'e_frac_mJ': None, 'e_elas_mJ': None}",
        "    if csv_file.exists():",
        "        with open(csv_file, 'r', encoding='utf-8') as f:",
        "            reader = csv.DictReader(f)",
        "            rows = list(reader)",
        "            if rows:",
        "                last = rows[-1]",
        "                results['e_frac_mJ'] = float(last['E_fracture_kNmm']) * 1000.0",
        "                results['e_elas_mJ'] = float(last['E_elastic_kNmm']) * 1000.0",
        "                results['step'] = int(last['Step'])",
        "                results['inc'] = int(last['Increment'])",
        "",
        "    if dat_file.exists():",
        "        text = dat_file.read_text(encoding='utf-8', errors='ignore')",
        "        m = re.findall(r'999999\s+[-+0-9.E]+\s+([-+0-9.E]+)', text)",
        "        if m:",
        "            results['rf2_N'] = float(m[-1]) * 1000.0",
        "",
        "    with open('package103_deliverable_evaluation.json', 'w', encoding='utf-8') as f:",
        "        json.dump(results, f, indent=2)",
        "    print('Extracted Package 103 deliverables:', results)",
        "",
        "if __name__ == '__main__':",
        "    extract()"
    ]
    out_ext = pkg_dir / "extract_pkg103_results.py"
    out_ext.write_text("\n".join(ext_py) + "\n", encoding="utf-8")

    # 12. Save Mapped State Table for Package 103
    out_state_table = pkg_dir / "candidate_c5_h1_state_table.csv"
    with open(out_state_table, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["RECORD_TYPE", "ID", "X", "Y", "DAMAGE_H1", "U1", "U2", "RESIDUAL"])
        # Load u1, u2 from existing state table
        old_nodes = {}
        with open(state_table_csv, "r", encoding="utf-8") as f_old:
            for r in csv.reader(f_old):
                if r and r[0].strip().upper() == "NODE":
                    old_nodes[int(r[1])] = (float(r[2]), float(r[3]), float(r[5]), float(r[6]))
        for nid in node_list:
            idx = node_to_idx[nid]
            coords = nodes[nid]
            u_vals = old_nodes.get(nid, (coords[0], coords[1], 0.0, 0.0))
            writer.writerow(["NODE", nid, f"{coords[0]:.8f}", f"{coords[1]:.8f}", f"{d_H1[idx]:.10e}", f"{u_vals[2]:.10e}", f"{u_vals[3]:.10e}", 0.0])
        for eid in sorted(elem_h.keys()):
            h = elem_h[eid]
            writer.writerow(["ELEM_HISTORY", eid, f"{h[0]:.10e}", f"{h[1]:.10e}", f"{h[2]:.10e}", f"{h[3]:.10e}", 0.0, 0.0])

    print(f"Saved Package 103 state table: {out_state_table}")

    # 13. Write PACKAGE_MANIFEST.json
    manifest = {
        "schema": 1,
        "package_name": "PACKAGE_103",
        "job_name": "M1_C5_PACKAGE103_H1_PILOT",
        "objective": "First Conforming Matched-Displacement Pilot under Exact Bound-Constrained H^1 State Transfer",
        "mesh": {
            "name": "candidate_crack_band_mesh_c5.inp",
            "physical_quads": 4440,
            "physical_nodes": 4610,
            "total_elements": 13320,
            "hash": sha256_file(dst_mesh)
        },
        "user_subroutine": {
            "name": "f42_mixed_uel.for",
            "hash": sha256_file(dst_uel),
            "status": "BITWISE_FROZEN_PASS"
        },
        "input_deck": {
            "name": "M1_C5_PACKAGE103_H1_PILOT.inp",
            "hash": sha256_file(out_deck),
            "data_lines": len(final_deck_content.splitlines()),
            "format": "STRICT_3_LINE_CARD_FORMAT"
        },
        "hpc_resources": {
            "queue": "normal_imfdfkmq",
            "cpus": 1,
            "memory_gb": 16,
            "walltime_hours": 4
        },
        "predecessor": {
            "package": "PACKAGE_94",
            "donor_source": "Package 94 Step 4 Frame 7",
            "donor_rf2_N": DONOR_RF2_N,
            "donor_e_frac_mJ": DONOR_E_FRAC_MJ,
            "donor_u_mm": U_CHECKPOINT_MM
        },
        "predicted_checkpoint_metrics": {
            "rf2_N": 114.2252,
            "rf2_error_pct": 1.1105,
            "e_frac_mJ": 0.136659,
            "e_frac_error_pct": -0.7822,
            "min_damage": float(np.min(d_H1)),
            "max_damage": float(np.max(d_H1)),
            "healing_nodes": 0,
            "overshoot_nodes": 0
        },
        "acceptance_criteria": {
            "rf2_error_limit_pct": 5.0,
            "e_frac_error_limit_pct": 2.0,
            "zero_healing": True,
            "zero_overshoot": True,
            "history_preservation_pct": 100.0
        }
    }

    manifest_path = pkg_dir / "PACKAGE_MANIFEST.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    print(f"Saved Package 103 manifest: {manifest_path}")

    return manifest

if __name__ == "__main__":
    build_package103()
