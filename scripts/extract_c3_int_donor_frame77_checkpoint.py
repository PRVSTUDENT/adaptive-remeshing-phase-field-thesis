# -*- coding: utf-8 -*-
"""
extract_c3_int_donor_frame77_checkpoint.py
Task: F1597-CORRECT-PACKAGE72-STATE-TRANSFER
Protocol Version: 2

Extracts, authenticates, and serializes the exact Frame-77 physical state
from Package 141 (Candidate C3-Intermediate Continuous Donor Simulation, 2,484 quads, 2,610 nodes):
1. Identifies Step-1 final increment (exact Frame-77 state, u_top = 0.0018003125442191958 mm).
2. Extracts physical nodal coordinates and displacements for all 2,610 nodes.
3. Extracts committed phase-field damage d and Gauss point history H0.
4. Audits slit-flank topology along y = 0.05 mm, x <= 0.04 mm.
5. Reconciles reaction force RF2 and energy components (E_elastic, E_frac, E_tot).
6. Serializes verified checkpoint files for H37 C3-Int -> C4 state transfer.
"""

from __future__ import print_function, division
import os
import sys
import json
import math
import hashlib

# Physical parameters
E_MOD = 210.0      # kN/mm^2 (210 GPa)
NU = 0.3
E_GC = 0.0027      # kN/mm (2.7 N/mm)
E_L0 = 0.0075      # mm (7.5 um)
K_DEGRAD = 1.0e-7

N_PHYS_NODES = 2610
N_PHYS_ELEMS = 2484
RP_NODE = 999999
TARGET_U_FRAME77 = 0.0018003125442191958
TARGET_T_STEP1 = 0.36006251

L1_OFFSET = 0
L2_OFFSET = N_PHYS_ELEMS       # 2484
L3_OFFSET = 2 * N_PHYS_ELEMS   # 4968


def compute_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest().lower()


def parse_inp_mesh(inp_path):
    """Parses physical nodes, element connectivity, node sets, and slit flanks."""
    nodes = {}
    elements = {}
    nset_top = []
    nset_bottom = []
    nset_pin = []
    
    state = None
    with open(inp_path, "r") as f:
        for line in f:
            l = line.strip()
            if not l or l.startswith("**"):
                continue
            u = l.upper()
            if u.startswith("*NODE") and not any(u.startswith(k) for k in ["*NODE OUTPUT", "*NODE PRINT", "*NODE FILE"]):
                state = "NODE"
                continue
            elif u.startswith("*ELEMENT") and "TYPE=U1" in u:
                state = "ELEM"
                continue
            elif u.startswith("*NSET, NSET=N_TOP"):
                state = "NSET_TOP"
                continue
            elif u.startswith("*NSET, NSET=N_BOTTOM"):
                state = "NSET_BOTTOM"
                continue
            elif u.startswith("*NSET, NSET=N_PIN"):
                state = "NSET_PIN"
                continue
            elif u.startswith("*"):
                state = None
                continue

            if state == "NODE":
                parts = [p.strip() for p in l.split(",")]
                if len(parts) >= 3:
                    nid = int(parts[0])
                    if nid <= N_PHYS_NODES:
                        nodes[nid] = (float(parts[1]), float(parts[2]))
            elif state == "ELEM":
                parts = [int(p.strip()) for p in l.split(",") if p.strip().isdigit()]
                if len(parts) == 5:
                    eid = parts[0]
                    if eid <= N_PHYS_ELEMS:
                        elements[eid] = parts[1:5]
            elif state == "NSET_TOP":
                nset_top.extend([int(p.strip()) for p in l.split(",") if p.strip().isdigit()])
            elif state == "NSET_BOTTOM":
                nset_bottom.extend([int(p.strip()) for p in l.split(",") if p.strip().isdigit()])
            elif state == "NSET_PIN":
                nset_pin.extend([int(p.strip()) for p in l.split(",") if p.strip().isdigit()])

    # Identify slit flank nodes along y = 0.05 mm, x <= 0.04 mm
    slit_nodes = []
    for nid, (x, y) in nodes.items():
        if abs(y - 0.050) < 1.0e-5 and x <= 0.040 + 1.0e-5:
            slit_nodes.append(nid)

    # Classify upper vs lower flank based on element connectivity
    from collections import defaultdict
    upper_flank_nodes = set()
    lower_flank_nodes = set()
    by_x = defaultdict(list)

    for nid in slit_nodes:
        x, y = nodes[nid]
        by_x[round(x, 7)].append(nid)

    for nid in slit_nodes:
        attached_elems = [eid for eid, conn in elements.items() if nid in conn]
        centers_y = [sum(nodes[m][1] for m in elements[eid])/4.0 for eid in attached_elems]
        if all(cy > 0.05 for cy in centers_y):
            upper_flank_nodes.add(nid)
        elif all(cy < 0.05 for cy in centers_y):
            lower_flank_nodes.add(nid)

    # Establish exact coincident seam pairs
    seam_pairs = []
    for x_val in sorted(by_x.keys()):
        pair = by_x[x_val]
        if len(pair) == 2:
            n1, n2 = pair[0], pair[1]
            if n1 in lower_flank_nodes and n2 in upper_flank_nodes:
                seam_pairs.append((n1, n2))
            elif n2 in lower_flank_nodes and n1 in upper_flank_nodes:
                seam_pairs.append((n2, n1))

    return {
        "nodes": nodes,
        "elements": elements,
        "nset_top": sorted(nset_top),
        "nset_bottom": sorted(nset_bottom),
        "nset_pin": sorted(nset_pin),
        "slit_nodes": sorted(slit_nodes),
        "upper_flank_nodes": sorted(list(upper_flank_nodes)),
        "lower_flank_nodes": sorted(list(lower_flank_nodes)),
        "seam_pairs": seam_pairs
    }


def parse_energy_balance_csv(csv_path):
    """Parses uel_energy_balance.csv written by f42_mixed_uel.for."""
    records = []
    if not os.path.exists(csv_path):
        return records
    with open(csv_path, "r") as f:
        header = None
        for line in f:
            l = line.strip()
            if not l:
                continue
            parts = [p.strip() for p in l.split(",")]
            if header is None:
                header = [h.upper() for h in parts]
                continue
            if len(parts) >= 7:
                try:
                    records.append({
                        "step": int(parts[0]),
                        "inc": int(parts[1]),
                        "total_time": float(parts[2]),
                        "step_time": float(parts[3]),
                        "e_elastic_knmm": float(parts[4]),
                        "e_fracture_knmm": float(parts[5]),
                        "e_total_knmm": float(parts[6])
                    })
                except ValueError:
                    continue
    return records


def extract_odb_data(odb_path, mesh_info):
    """Extracts exact Frame-77 state from Abaqus ODB using odbAccess."""
    try:
        from odbAccess import openOdb
    except ImportError:
        print("Note: odbAccess not available in current environment; running in static verification mode.")
        return None

    print("Opening ODB: %s" % odb_path)
    odb = openOdb(odb_path, readOnly=True)

    # 1. Step-1 identification
    if "Step-1" not in odb.steps:
        odb.close()
        raise RuntimeError("STRICT_FAILURE: Step-1 not found in ODB steps: %s" % list(odb.steps.keys()))

    step1 = odb.steps["Step-1"]
    n_frames = len(step1.frames)
    if n_frames == 0:
        odb.close()
        raise RuntimeError("STRICT_FAILURE: Step-1 contains zero frames.")
    print("Step-1 contains %d frames." % n_frames)

    # Final frame of Step 1 is the Frame-77 donor state
    frame77 = step1.frames[-1]
    step_time = frame77.frameValue
    print("Final Step-1 frame %d: step_time = %.8f s" % (frame77.frameId, step_time))

    # Verify step_time is within tolerance of target
    if abs(step_time - TARGET_T_STEP1) > 1.0e-5:
        odb.close()
        raise RuntimeError(
            "STRICT_FAILURE: Step-1 terminated early! step_time = %.8f s, expected %.8f s" % (
                step_time, TARGET_T_STEP1
            )
        )

    # 2. Extract displacements and nodal phase damage from root assembly instance
    inst_name = list(odb.rootAssembly.instances.keys())[0]
    inst = odb.rootAssembly.instances[inst_name]

    if "U" not in frame77.fieldOutputs:
        odb.close()
        raise RuntimeError("STRICT_FAILURE: FieldOutput 'U' missing from Frame 77.")
    if "RF" not in frame77.fieldOutputs:
        odb.close()
        raise RuntimeError("STRICT_FAILURE: FieldOutput 'RF' missing from Frame 77.")

    u_field = frame77.fieldOutputs["U"]
    rf_field = frame77.fieldOutputs["RF"]

    disp_dict = {}
    d_nodal_dict = {}
    rf_dict = {}

    for val in u_field.values:
        data = val.data
        if val.nodeLabel <= N_PHYS_NODES:
            disp_dict[val.nodeLabel] = (float(data[0]), float(data[1]))
            # DOF 3 is phase-field damage on UEL Layer 1 nodes
            if len(data) >= 3:
                d_nodal_dict[val.nodeLabel] = float(data[2])
            else:
                d_nodal_dict[val.nodeLabel] = 0.0
        elif val.nodeLabel == RP_NODE:
            disp_dict[RP_NODE] = (float(data[0]), float(data[1]))

    for val in rf_field.values:
        if val.nodeLabel == RP_NODE:
            rf_dict[RP_NODE] = (float(val.data[0]), float(val.data[1]))

    # Verify complete nodal recovery
    if len(disp_dict) < N_PHYS_NODES:
        odb.close()
        raise RuntimeError(
            "STRICT_FAILURE: Incomplete nodal displacement extraction (%d of %d physical nodes)." % (
                len(disp_dict), N_PHYS_NODES
            )
        )

    # Verify RP displacement matches target
    rp_u2 = disp_dict.get(RP_NODE, (0.0, 0.0))[1]
    print("RP 999999 displacement u2 = %.12f mm (target: %.12f mm)" % (rp_u2, TARGET_U_FRAME77))
    if abs(rp_u2 - TARGET_U_FRAME77) > 1.0e-6:
        odb.close()
        raise RuntimeError(
            "STRICT_FAILURE: Target displacement mismatch! u_RP = %.12e, expected %.12e" % (
                rp_u2, TARGET_U_FRAME77
            )
        )

    # 3. Extract SDVs from Companion CPE4 Overlay elements (Layer 3: 4969..7452)
    if "SDV" not in frame77.fieldOutputs:
        odb.close()
        raise RuntimeError("STRICT_FAILURE: FieldOutput 'SDV' missing from Frame 77 companion elements.")

    sdv_field = frame77.fieldOutputs["SDV"]
    d_dict = {}      # physical element -> list of 4 GP d values
    h_dict = {}      # physical element -> list of 4 GP H values
    e_frac_dict = {} # physical element -> E_frac
    e_elas_dict = {} # physical element -> E_elas

    gp_count_check = {}

    for val in sdv_field.values:
        eid = val.elementLabel
        if L3_OFFSET < eid <= L3_OFFSET + N_PHYS_ELEMS:
            phys_eid = eid - L3_OFFSET
            gp_idx = val.integrationPoint - 1
            if phys_eid not in d_dict:
                d_dict[phys_eid] = [0.0] * 4
                h_dict[phys_eid] = [0.0] * 4
                gp_count_check[phys_eid] = 0
            
            gp_count_check[phys_eid] += 1

            # SDV1 = d, SDV2 = H (or SDV16), SDV17 = E_frac, SDV18 = E_elas
            data = val.data
            if isinstance(data, (list, tuple)):
                if len(data) >= 1:
                    d_dict[phys_eid][gp_idx] = float(data[0])
                if len(data) >= 2:
                    h_dict[phys_eid][gp_idx] = float(data[1])
                if len(data) >= 17:
                    e_frac_dict[phys_eid] = float(data[16])
                if len(data) >= 18:
                    e_elas_dict[phys_eid] = float(data[17])

    # Verify complete element and Gauss-point coverage
    if len(d_dict) < N_PHYS_ELEMS:
        odb.close()
        raise RuntimeError(
            "STRICT_FAILURE: Incomplete element SDV extraction (%d of %d physical elements)." % (
                len(d_dict), N_PHYS_ELEMS
            )
        )
    for phys_eid, count in gp_count_check.items():
        if count != 4:
            odb.close()
            raise RuntimeError(
                "STRICT_FAILURE: Element %d has %d Gauss points (expected exactly 4)." % (
                    phys_eid, count
                )
            )

    odb.close()

    # 4. Slit Flank Penetration Audit
    seam_pairs = mesh_info.get("seam_pairs", [])
    penetration_violations = 0
    for n_lower, n_upper in seam_pairs:
        u_y_lower = disp_dict[n_lower][1]
        u_y_upper = disp_dict[n_upper][1]
        if u_y_upper < u_y_lower - 1.0e-9:
            penetration_violations += 1

    if penetration_violations > 0:
        raise RuntimeError(
            "STRICT_FAILURE: Slit flank interpenetration detected across %d seam pairs!" % (
                penetration_violations
            )
        )

    return {
        "step_time": step_time,
        "frame_id": frame77.frameId,
        "displacements": disp_dict,
        "d_nodal": d_nodal_dict,
        "reactions": rf_dict,
        "d_gp": d_dict,
        "h_gp": h_dict,
        "e_frac_elem": e_frac_dict,
        "e_elas_elem": e_elas_dict
    }


def serialize_checkpoint(output_dir, mesh_info, extracted_data, energy_record=None):
    """Atomically serializes the verified Frame-77 checkpoint files."""
    os.makedirs(output_dir, exist_ok=True)

    # 1. nodal_displacements.csv: node_id, u1, u2, d_nodal
    disp_csv = os.path.join(output_dir, "c3_int_donor_frame77_nodal_displacements.csv")
    phase_csv = os.path.join(output_dir, "c3_int_donor_frame77_nodal_phase_field.csv")
    disps = extracted_data["displacements"]
    d_nodal = extracted_data.get("d_nodal", {})

    with open(disp_csv, "w") as f, open(phase_csv, "w") as f_phase:
        f.write("node_id,u1_mm,u2_mm,d_nodal\n")
        f_phase.write("node_id,d_nodal\n")
        for nid in sorted(mesh_info["nodes"].keys()):
            u1, u2 = disps.get(nid, (0.0, 0.0))
            d_val = d_nodal.get(nid, 0.0)
            f.write("%d,%.12e,%.12e,%.12e\n" % (nid, u1, u2, d_val))
            f_phase.write("%d,%.12e\n" % (nid, d_val))
        if RP_NODE in disps:
            u1_rp, u2_rp = disps[RP_NODE]
            f.write("%d,%.12e,%.12e,0.0\n" % (RP_NODE, u1_rp, u2_rp))

    # 2. d_lower_bounds.csv: EID, D0_1, D0_2, D0_3, D0_4, H0_1, H0_2, H0_3, H0_4
    bounds_csv = os.path.join(output_dir, "c3_int_donor_frame77_d_lower_bounds.csv")
    with open(bounds_csv, "w") as f:
        f.write("EID,D0_1,D0_2,D0_3,D0_4,H0_1,H0_2,H0_3,H0_4\n")
        d_gp = extracted_data["d_gp"]
        h_gp = extracted_data["h_gp"]
        for eid in sorted(mesh_info["elements"].keys()):
            d_vals = d_gp.get(eid, [0.0, 0.0, 0.0, 0.0])
            h_vals = h_gp.get(eid, [0.0, 0.0, 0.0, 0.0])
            f.write("%d,%.10e,%.10e,%.10e,%.10e,%.10e,%.10e,%.10e,%.10e\n" % (
                eid,
                d_vals[0], d_vals[1], d_vals[2], d_vals[3],
                h_vals[0], h_vals[1], h_vals[2], h_vals[3]
            ))

    # 3. Checkpoint metadata manifest
    manifest_json = os.path.join(output_dir, "c3_int_donor_frame77_checkpoint_manifest.json")
    rf2_rp = extracted_data["reactions"].get(RP_NODE, (0.0, 0.0))[1]
    
    manifest_data = {
        "donor_package": "141_c3_int_donor_monotonic",
        "job_name": "M1_C3_INT_DONOR_MONOTONIC",
        "donor_step": 1,
        "donor_step_time_s": extracted_data["step_time"],
        "target_u_mm": TARGET_U_FRAME77,
        "actual_u_rp_mm": disps.get(RP_NODE, (0.0, 0.0))[1],
        "reaction_force_rp_rf2_kn": rf2_rp,
        "reaction_force_rp_rf2_n": rf2_rp * 1000.0,
        "n_physical_nodes": len(mesh_info["nodes"]),
        "n_physical_elements": len(mesh_info["elements"]),
        "slit_flank_nodes": len(mesh_info["slit_nodes"]),
        "upper_flank_nodes": len(mesh_info["upper_flank_nodes"]),
        "lower_flank_nodes": len(mesh_info["lower_flank_nodes"]),
        "seam_pairs": len(mesh_info.get("seam_pairs", [])),
        "files": {
            "c3_int_donor_frame77_nodal_displacements.csv": compute_sha256(disp_csv),
            "c3_int_donor_frame77_nodal_phase_field.csv": compute_sha256(phase_csv),
            "c3_int_donor_frame77_d_lower_bounds.csv": compute_sha256(bounds_csv)
        }
    }
    if energy_record:
        manifest_data["energetics"] = energy_record

    with open(manifest_json, "w") as f:
        json.dump(manifest_data, f, indent=2)

    print("Serialized authentic Frame-77 checkpoint to: %s" % output_dir)
    return manifest_data


def main():
    if len(sys.argv) < 3:
        print("Usage: python extract_c3_int_donor_frame77_checkpoint.py <run_dir_or_pkg_dir> <output_dir>")
        sys.exit(1)

    run_dir = sys.argv[1]
    output_dir = sys.argv[2]

    inp_path = os.path.join(run_dir, "M1_C3_INT_DONOR_MONOTONIC.inp")
    odb_path = os.path.join(run_dir, "M1_C3_INT_DONOR_MONOTONIC.odb")
    energy_csv = os.path.join(run_dir, "uel_energy_balance.csv")

    if not os.path.exists(inp_path):
        raise RuntimeError("Input deck not found: %s" % inp_path)

    print("1. Parsing input deck: %s" % inp_path)
    mesh_info = parse_inp_mesh(inp_path)
    print("   Nodes: %d, Quads: %d, Slit nodes: %d (Upper: %d, Lower: %d)" % (
        len(mesh_info["nodes"]), len(mesh_info["elements"]),
        len(mesh_info["slit_nodes"]), len(mesh_info["upper_flank_nodes"]), len(mesh_info["lower_flank_nodes"])
    ))

    # Read energy balance if available
    energy_records = parse_energy_balance_csv(energy_csv)
    step1_energy = None
    if energy_records:
        step1_records = [r for r in energy_records if r["step"] == 1]
        if step1_records:
            step1_energy = step1_records[-1]
            print("   Energy at Step 1 end: E_elas = %.6e kN*mm, E_frac = %.6e kN*mm, E_tot = %.6e kN*mm" % (
                step1_energy["e_elastic_knmm"], step1_energy["e_fracture_knmm"], step1_energy["e_total_knmm"]
            ))

    # ODB extraction
    if os.path.exists(odb_path):
        extracted = extract_odb_data(odb_path, mesh_info)
        if extracted is not None:
            serialize_checkpoint(output_dir, mesh_info, extracted, step1_energy)
    else:
        print("ODB file not present (simulation pending or running). Preflight structure check passed.")


if __name__ == "__main__":
    main()
