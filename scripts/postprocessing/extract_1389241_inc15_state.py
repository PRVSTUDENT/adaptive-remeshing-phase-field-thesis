#!/usr/bin/env python3
"""
Extract exact source mesh coordinates and Increment 15 phase field from Job 1389241.mmaster02.
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EVID_DIR = ROOT / "runs/hpc/mode_ii_state_transfer/evidence/1389241.mmaster02"
INP_FILE = ROOT / "models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART1R1R8/M2STATE_FRACFIX_RESTART1R1R8.inp"
DAT_FILE = EVID_DIR / "M2STATE_FRACFIX_RESTART1R1R8.dat"

def main():
    # 1. Parse node coordinates from INP
    inp_lines = INP_FILE.read_text(encoding="utf-8", errors="replace").splitlines()
    nodes = {}
    in_nodes = False
    for l in inp_lines:
        if l.startswith("*NODE"):
            in_nodes = True
            continue
        if in_nodes:
            if l.startswith("*"):
                break
            parts = l.strip().split(",")
            if len(parts) >= 3 and parts[0].strip().isdigit():
                nid = int(parts[0].strip())
                if nid <= 4998:
                    x = float(parts[1].strip())
                    y = float(parts[2].strip())
                    nodes[nid] = (x, y)

    print(f"Parsed {len(nodes)} source node coordinates.")

    # 2. Parse Increment 15 nodal phase from DAT
    dat_lines = DAT_FILE.read_text(encoding="utf-8", errors="replace").splitlines()
    table_starts = [idx for idx, l in enumerate(dat_lines) if "THE FOLLOWING TABLE IS PRINTED FOR ALL NODES" in l]
    last_start = table_starts[-1]

    phase = {}
    u1_dict = {}
    u2_dict = {}

    for l in dat_lines[last_start+5:]:
        if "MAXIMUM" in l:
            break
        parts = l.strip().split()
        if len(parts) >= 4 and parts[0].isdigit():
            nid = int(parts[0])
            if nid <= 4998:
                u1 = float(parts[1])
                u2 = float(parts[2])
                u3 = float(parts[3])
                u1_dict[nid] = u1
                u2_dict[nid] = u2
                phase[nid] = u3

    print(f"Parsed {len(phase)} nodal phase values at Increment 15.")
    print(f"Max Phase = {max(phase.values()):.6f}, Min Phase = {min(phase.values()):.6f}")

    source_data = {
        "job_id": "1389241.mmaster02",
        "candidate": "M2STATE_FRACFIX_RESTART1R1R8",
        "checkpoint_step": 2,
        "checkpoint_inc": 15,
        "u1_target_mm": 0.010000,
        "rf1_target_kN": 0.123223,
        "dmax": max(phase.values()),
        "nodes": {str(k): {"x": nodes[k][0], "y": nodes[k][1], "phase": phase[k], "u1": u1_dict[k], "u2": u2_dict[k]} for k in sorted(nodes.keys())}
    }

    out_json = EVID_DIR / "SOURCE_STATE_INCREMENT15.json"
    out_json.write_text(json.dumps(source_data, indent=2), encoding="utf-8")
    print(f"Saved source state JSON: {out_json} ({out_json.stat().st_size} bytes)")

if __name__ == "__main__":
    main()
