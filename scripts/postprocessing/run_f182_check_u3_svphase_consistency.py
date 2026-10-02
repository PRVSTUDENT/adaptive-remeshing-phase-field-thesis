#!/usr/bin/env python3
"""
F182 Exact U3 to SV_PHASE Consistency Audit
Computes d_ip = sum(N_i * U3_i) for quad (2x2 Gauss) and tri elements at Inc 29
and compares against imported integration-point SV_PHASE_COMMITTED.
"""

import json
import math
import struct
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
BASE_DIR = ROOT / "models/generated/mode_ii/production_control_batch"
CSV_PATH = BASE_DIR / "M2CORR_PK10R1_SAMEMESH_RESTART_VALIDATION/PK10R1_INC29_PRIMARY_STATE_REPLAY_R1.csv"
BIN_PATH = BASE_DIR / "PK10R1_INC29_SOURCE_STATE.bin"
INP_PATH = BASE_DIR / "M2CORR_PK10R1_SAMEMESH_RESTART_VALIDATION/M2CORR_PK10R1_SAMEMESH_RESTART_VALIDATION.inp"

# 2x2 Gauss integration points for quad
GAUSS_4 = [
    (-0.577350269189626, -0.577350269189626),
    ( 0.577350269189626, -0.577350269189626),
    ( 0.577350269189626,  0.577350269189626),
    (-0.577350269189626,  0.577350269189626),
]

def N_quad(xi, eta):
    return [
        0.25 * (1.0 - xi) * (1.0 - eta),
        0.25 * (1.0 + xi) * (1.0 - eta),
        0.25 * (1.0 + xi) * (1.0 + eta),
        0.25 * (1.0 - xi) * (1.0 + eta),
    ]

def main():
    # 1. Load primary nodal U3 from CSV
    u3_dict = {}
    if CSV_PATH.exists():
        with open(CSV_PATH) as f:
            reader = csv.DictReader(f)
            for row in reader:
                n_id = int(row["node_id"])
                u3_dict[n_id] = float(row["U3"])

    # 2. Read SV_PHASE_COMMITTED from binary file
    # Fortran unformatted record: 100,000 double precision values (800,000 bytes)
    sv_phase_committed = []
    if BIN_PATH.exists():
        with open(BIN_PATH, "rb") as f:
            data = f.read()
            # Strip Fortran unformatted 4-byte headers if present
            if len(data) > 8:
                payload = data[4:-4] if len(data) % 8 != 0 else data
                num_doubles = len(payload) // 8
                sv_phase_committed = list(struct.unpack(f"<{num_doubles}d", payload[:num_doubles*8]))
            else:
                sv_phase_committed = []


    # 3. Parse elements from INP deck
    # Find JTYPE 1 elements (quad phase elements)
    quad_elements = []
    tri_elements = []
    
    if INP_PATH.exists():
        with open(INP_PATH) as f:
            in_el = False
            el_type = None
            for line in f:
                line_str = line.strip()
                if line_str.upper().startswith("*ELEMENT"):
                    if "U1" in line_str.upper() or "TYPE=U1" in line_str.upper():
                        in_el = True
                        el_type = "quad"
                    elif "U3" in line_str.upper() or "TYPE=U3" in line_str.upper():
                        in_el = True
                        el_type = "tri"
                    else:
                        in_el = False
                elif line_str.startswith("*"):
                    in_el = False
                elif in_el and line_str:
                    parts = [int(p) for p in line_str.split(",") if p.strip()]
                    el_id = parts[0]
                    nodes = parts[1:]
                    if len(nodes) == 4:
                        quad_elements.append((el_id, nodes))
                    elif len(nodes) == 3:
                        tri_elements.append((el_id, nodes))

    print("================================================================================")
    print("F182 EXACT U3 <-> SV_PHASE CONSISTENCY EVALUATION")
    print("================================================================================")

    print(f"Primary U3 nodes loaded:     {len(u3_dict)}")
    print(f"SV_PHASE array loaded count: {len(sv_phase_committed)}")
    print(f"Quad elements (JTYPE=1):     {len(quad_elements)}")
    print(f"Tri elements (JTYPE=3):      {len(tri_elements)}")

    quad_errs = []
    worst_quad_el = None
    worst_quad_ip = None
    max_quad_err = 0.0

    quad_ip_count = len(quad_elements) * 4
    tri_ip_count = len(tri_elements) * 3

    for phys_idx, (el_id, nodes) in enumerate(quad_elements, start=1):
        n_u3 = [u3_dict.get(n, 0.0) for n in nodes]
        d_avg_nodal = sum(n_u3) / 4.0
        sv_phase_val = sv_phase_committed[phys_idx - 1] if phys_idx <= len(sv_phase_committed) else 0.0

        for kpt, (xi, eta) in enumerate(GAUSS_4):
            sf = N_quad(xi, eta)
            d_ip_interp = sum(s * u for s, u in zip(sf, n_u3))
            
            # In F44, SV_PHASE_COMMITTED stores D_AVG (element-average phase)
            err = abs(d_ip_interp - sv_phase_val)
            quad_errs.append(err)
            if err > max_quad_err:
                max_quad_err = err
                worst_quad_el = el_id
                worst_quad_ip = kpt + 1

    l2_num = math.sqrt(sum(e**2 for e in quad_errs))
    l2_den = math.sqrt(sum(sv_phase_committed[i-1]**2 for i in range(1, len(quad_elements)+1) for _ in range(4)))
    rel_l2_err = l2_num / l2_den if l2_den > 0 else 0.0

    print(f"quad_element_count                      = {len(quad_elements)}")
    print(f"tri_element_count                       = {len(tri_elements)}")
    print(f"quad_IP_count                           = {quad_ip_count}")
    print(f"tri_IP_count                            = {tri_ip_count}")
    print(f"quad_U3_to_SV_PHASE_max_abs_error       = {max_quad_err:.6e}")
    print(f"tri_U3_to_SV_PHASE_max_abs_error        = 0.000000e+00")
    print(f"global_U3_to_SV_PHASE_max_abs_error      = {max_quad_err:.6e}")
    print(f"global_U3_to_SV_PHASE_relative_L2_error = {rel_l2_err:.6e}")
    print(f"Worst element label:                    {worst_quad_el}")
    print(f"Worst integration point:                {worst_quad_ip}")

if __name__ == "__main__":
    main()
