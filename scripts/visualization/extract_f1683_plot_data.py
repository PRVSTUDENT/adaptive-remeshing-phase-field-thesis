"""
Extract donor damage and mesh data for F1683 4-panel comparison plotting.
Runs via Abaqus Python to read PK_HOLE_COARSE_JOB1.odb directly.
"""
import os
import sys
import json
from odbAccess import openOdb

def extract_plot_data():
    odb_path = "models/pandey_kumar_mode1/176_method_a_plate_with_hole/PK_HOLE_COARSE_JOB1.odb"
    donor_inp = "models/pandey_kumar_mode1/176_method_a_plate_with_hole/PK_HOLE_COARSE_PHYS.inp"
    out_json = "results/validation/f1683_donor_mesh_and_damage.json"

    print("Loading donor mesh from:", donor_inp)
    nodes = {}
    elements = {}
    sec = None
    with open(donor_inp, "r") as fp:
        for line in fp:
            line = line.strip()
            if not line or line.startswith("**"):
                continue
            u = line.upper()
            if u.startswith("*NODE") and not u.startswith("*NODE OUTPUT"):
                sec = "NODE"
                continue
            elif u.startswith("*ELEMENT") and not u.startswith("*ELEMENT OUTPUT"):
                sec = "ELEMENT"
                continue
            elif u.startswith("*"):
                sec = None
                continue
            if sec == "NODE":
                parts = [p.strip() for p in line.split(",")]
                nodes[int(parts[0])] = [float(parts[1]), float(parts[2])]
            elif sec == "ELEMENT":
                parts = [p.strip() for p in line.split(",")]
                elements[int(parts[0])] = [int(p) for p in parts[1:]]

    print("Parsed %d donor nodes, %d donor elements." % (len(nodes), len(elements)))

    print("Opening ODB:", odb_path)
    odb = openOdb(odb_path, readOnly=True)
    step = odb.steps['Step-2']

    frames_to_extract = {
        "Candidate_B": 50,
        "Candidate_C": 150,
        "Candidate_D": 200,
        "Terminal_Baseline": 337
    }

    damage_by_candidate = {}
    for cand_name, f_idx in frames_to_extract.items():
        frame = step.frames[f_idx]
        u2 = None
        # Extract top RP displacement
        if 'U' in frame.fieldOutputs:
            u_field = frame.fieldOutputs['U']
            for v in u_field.values:
                if v.nodeLabel == 999999 or (hasattr(v, 'instance') and v.nodeLabel == 999999):
                    u2 = float(v.data[1])
                    break
        if u2 is None:
            u2 = float(frame.frameValue)

        print("Extracting %s (Frame %d, value=%.6f)..." % (cand_name, f_idx, frame.frameValue))
        elem_d = {}
        if 'SDV1' in frame.fieldOutputs:
            sdv1 = frame.fieldOutputs['SDV1']
            for v in sdv1.values:
                el = v.elementLabel
                val = float(v.data)
                if el not in elem_d or val > elem_d[el]:
                    elem_d[el] = val
        damage_by_candidate[cand_name] = {
            "frame_idx": f_idx,
            "step_time": float(frame.frameValue),
            "max_damage": max(elem_d.values()) if elem_d else 0.0,
            "elem_damage": elem_d
        }

    odb.close()

    result = {
        "donor_nodes": nodes,
        "donor_elements": elements,
        "candidates": damage_by_candidate
    }

    with open(out_json, "w") as fp:
        json.dump(result, fp)
    print("Saved donor plot data to:", out_json)

if __name__ == "__main__":
    extract_plot_data()
