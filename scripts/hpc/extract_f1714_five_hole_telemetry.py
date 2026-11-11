"""
scripts/hpc/extract_f1714_five_hole_telemetry.py
================================================
Task F1714: Extract authentic five-hole adaptive simulation telemetry from
M1_PK_F1714_JOB2_ADAPTED.odb:
1. Reaction force history from bottom boundary nodes (N_BOTTOM) ensuring global static equilibrium:
   F_tensile(t) = -sum_{j in N_BOTTOM} RF_{2, j}(t).
2. Domain-integrated elastic strain energy and fracture dissipation by summing
   volume-integrated element state variables SDV18 and SDV17 from visualizer layer
   (elements 26,069 to 39,102) with strict 1-to-1 physical element mapping and deduplication.
3. Full-field damage d = SDV1 for all 13,034 physical elements across key milestone states.

Governing Review Reference: HND-F1714-FINAL-VALIDATION-002
"""

import sys
import json
import os

# Compatible with Abaqus Python (Python 2.7 / 3.10)
try:
    from odbAccess import openOdb
except ImportError:
    pass


def extract_telemetry(odb_path, out_json):
    print("Opening ODB: " + odb_path)
    odb = openOdb(odb_path, readOnly=True)

    n_phys = 13034
    
    # 52 Bottom boundary nodes (N_BOTTOM) from PK_F1714_JOB2_ADAPTED_PROD.inp
    n_bottom_nodes = set([
        49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64,
        65, 66, 67, 68, 69, 70, 71, 72, 73, 630, 631, 632, 633, 634, 635, 636,
        637, 638, 639, 640, 641, 642, 643, 644, 645, 646, 647, 648, 649, 650, 651, 652,
        653, 654, 655, 3125
    ])

    # Milestone target displacements (mm) for Pandey & Kumar (2025) Figures 23-24:
    milestone_targets = {
        "state_1_elastic_limit": 0.0050,
        "state_2_void_initiation": 0.0055,
        "state_3_ligament_propagation": 0.0065,
        "state_4_inter_hole_snapthrough": 0.0075,
        "state_5_secondary_propagation": 0.0085,
        "state_6_terminal_severance": 0.0100
    }
    milestone_frames = {}

    fu_history = []
    energy_history = []

    print("Beginning extraction across ODB steps...")
    for sname in odb.steps.keys():
        step = odb.steps[sname]
        n_frames = len(step.frames)
        print("Processing Step %s (%d frames)..." % (sname, n_frames))

        for fidx, frame in enumerate(step.frames):
            val = float(frame.frameValue)
            if sname == 'Step-1':
                current_u = val * 0.0050
            else:
                current_u = 0.0050 + val * 0.0050

            # 1. Extract bottom boundary reaction force
            rf_sum_y = 0.0
            rf_node_count = 0
            if 'RF' in frame.fieldOutputs:
                rf_field = frame.fieldOutputs['RF']
                for v in rf_field.values:
                    if v.nodeLabel in n_bottom_nodes:
                        rf_sum_y += float(v.data[1])
                        rf_node_count += 1

            # Tensile force pulling upward is equal and opposite to downward reaction on bottom
            tensile_force_kN = -rf_sum_y if rf_node_count > 0 else 0.0

            # 2. Extract domain elastic and fracture energies from visualizer layer (SDV18 and SDV17)
            # Physical elements 1..13034 map to visualizer elements:
            # Tris (1..314): visualizer NOEL = 26068 + e
            # Quads (315..13034): visualizer NOEL = 26068 + e
            total_e_elas = 0.0
            total_e_frac = 0.0
            max_damage = 0.0
            
            # Check for milestone frame selection
            for mkey, mdisp in milestone_targets.items():
                if mkey not in milestone_frames:
                    if abs(current_u - mdisp) < 1.0e-4 or current_u >= mdisp:
                        milestone_frames[mkey] = {
                            "step": sname,
                            "frame_idx": fidx,
                            "displacement_mm": current_u,
                            "force_kN": tensile_force_kN
                        }

            fu_history.append({
                "step": sname,
                "frame": fidx,
                "displacement_mm": current_u,
                "tensile_force_kN": tensile_force_kN,
                "bottom_rf_sum_kN": rf_sum_y,
                "bottom_nodes_sampled": rf_node_count
            })

            # Sample energy and full field damage at every 10th frame or milestone frames
            if fidx % 10 == 0 or fidx == n_frames - 1:
                elem_energies_extracted = False
                if 'SDV' in frame.fieldOutputs:
                    sdv_field = frame.fieldOutputs['SDV']
                    # Map element energies: exactly 1 entry per physical element
                    seen_elems = set()
                    for v in sdv_field.values:
                        noel = v.elementLabel
                        if 26069 <= noel <= 39102:
                            phys_e = noel - 26068
                            if phys_e not in seen_elems:
                                seen_elems.add(phys_e)
                                # v.data contains [SDV1, SDV2, ..., SDV20]
                                if len(v.data) >= 18:
                                    d_val = float(v.data[0])  # SDV1 = phase damage
                                    e_frac = float(v.data[16]) # SDV17 = SV_E_FRAC (volume-integrated)
                                    e_elas = float(v.data[17]) # SDV18 = SV_E_ELAS (volume-integrated)
                                    total_e_frac += e_frac
                                    total_e_elas += e_elas
                                    if d_val > max_damage:
                                        max_damage = d_val

                    elem_energies_extracted = (len(seen_elems) == n_phys)

                energy_history.append({
                    "step": sname,
                    "frame": fidx,
                    "displacement_mm": current_u,
                    "elastic_energy_kNmm": total_e_elas,
                    "fracture_energy_kNmm": total_e_frac,
                    "total_energy_kNmm": total_e_elas + total_e_frac,
                    "max_damage": max_damage,
                    "active_elements_summed": len(seen_elems) if elem_energies_extracted else 0
                })

        print("Completed Step %s. Total FU history records: %d" % (sname, len(fu_history)))

    # 3. Full-field damage extraction for milestone frames
    damage_field_data = {}
    for mkey, minfo in milestone_frames.items():
        step_name = minfo["step"]
        fidx = minfo["frame_idx"]
        frame = odb.steps[step_name].frames[fidx]
        print("Extracting full-field damage for milestone: %s (u = %.4f mm)..." % (mkey, minfo["displacement_mm"]))

        d_map = {}
        if 'SDV' in frame.fieldOutputs:
            sdv_field = frame.fieldOutputs['SDV']
            for v in sdv_field.values:
                noel = v.elementLabel
                if 26069 <= noel <= 39102:
                    phys_e = noel - 26068
                    if phys_e not in d_map:
                        d_map[phys_e] = round(float(v.data[0]), 6)

        damage_field_data[mkey] = {
            "displacement_mm": minfo["displacement_mm"],
            "force_kN": minfo["force_kN"],
            "element_damage": d_map
        }

    output_payload = {
        "benchmark": "Pandey_Kumar_2025_Section_4_5_Five_Hole",
        "odb_path": odb_path,
        "n_physical_elements": n_phys,
        "n_bottom_nodes": len(n_bottom_nodes),
        "fu_history": fu_history,
        "energy_history": energy_history,
        "milestone_damage_fields": damage_field_data
    }

    print("Writing extracted telemetry to %s..." % out_json)
    with open(out_json, "w") as f:
        json.dump(output_payload, f, indent=2)

    print("Extraction successfully completed!")
    odb.close()


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: abaqus python extract_f1714_five_hole_telemetry.py <odb_path> <out_json>")
        sys.exit(1)
    extract_telemetry(sys.argv[1], sys.argv[2])
