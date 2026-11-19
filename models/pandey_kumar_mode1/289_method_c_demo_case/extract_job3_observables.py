# -*- coding: utf-8 -*-
"""
extract_job3_observables.py
===========================
Abaqus Python extraction script for Method C Demo Case Step-2 Forward Crack Propagation Solve:
- Model: PK_METHOD_C_DEMO_PROPAGATION_JOB3 (10,299 physical / 30,897 layered elements)
- Extracts two-step sequential observables:
  1. Status / exit code / walltime / CPU time / cutbacks / iterations from .sta, .log, .msg
  2. Step 1 (Re-Equilibration at u2=0.0050 mm):
     - End RF2, U2, damage, history, verifying continuity
  3. Step 2 (Forward Crack Propagation u2=0.0050 -> 0.0100 mm):
     - Frame-by-frame history of (u2, RF2, max_damage, crack_tip_x, crack_extension_Delta_a)
     - Peak reaction force F_max and corresponding displacement u2_at_Fmax
     - Softening behavior and post-peak load drop
     - Crack extension trajectory along y=0.50 mm toward hole at (0.75, 0.50) mm
     - Verification of hole capture (whether crack reached x=0.65 mm)
  4. Energy components from uel_energy_balance.csv (E_elastic, E_fracture, E_total)
  5. Outputs PK_METHOD_C_DEMO_PROPAGATION_JOB3_SUMMARY.json and RECEIPT.json
"""
from __future__ import print_function
import os
import sys
import json
import re

try:
    import odbAccess
    from abaqusConstants import *
    ABAQUS_AVAILABLE = True
except ImportError:
    ABAQUS_AVAILABLE = False


def extract_job3_observables(run_dir):
    job_name = "PK_METHOD_C_DEMO_PROPAGATION_JOB3"
    odb_path = os.path.join(run_dir, job_name + ".odb")
    sta_path = os.path.join(run_dir, job_name + ".sta")
    log_path = os.path.join(run_dir, job_name + ".log")
    pbs_log_path = os.path.join(run_dir, "pbs_execution_job3.log")
    msg_path = os.path.join(run_dir, job_name + ".msg")
    dat_path = os.path.join(run_dir, job_name + ".dat")
    energy_csv_path = os.path.join(run_dir, "uel_energy_balance.csv")
    out_json = os.path.join(run_dir, "PK_METHOD_C_DEMO_PROPAGATION_JOB3_SUMMARY.json")
    receipt_json = os.path.join(run_dir, "PK_METHOD_C_DEMO_PROPAGATION_JOB3_RECEIPT.json")

    results = {
        "job_id": "1424609.mmaster02",
        "job_name": job_name,
        "run_dir": run_dir,
        "status": "UNKNOWN",
        "exit_code": None,
        "sta_completed_successfully": False,
        "msg_zero_errors": False,
        "walltime_s": None,
        "cpu_time_s": None,
        "user_time_s": None,
        "sys_time_s": None,
        "step1_increments": 0,
        "step1_cutbacks": 0,
        "step1_equilibrium_iterations": 0,
        "step2_increments": 0,
        "step2_cutbacks": 0,
        "step2_equilibrium_iterations": 0,
        "total_increments": 0,
        "total_cutbacks": 0,
        "total_equilibrium_iterations": 0,
        "step1_end_RF2_kN": None,
        "step1_end_u2_mm": None,
        "step2_end_RF2_kN": None,
        "step2_end_u2_mm": None,
        "peak_RF2_kN": None,
        "u2_at_peak_RF2_mm": None,
        "post_peak_softening_demonstrated": False,
        "max_damage": None,
        "max_history_MPa": None,
        "crack_extension_history": [],
        "initial_notch_tip_x_mm": 0.50,
        "hole_center_x_mm": 0.75,
        "hole_radius_mm": 0.10,
        "hole_perimeter_x_mm": 0.65,
        "final_crack_tip_x_mm": None,
        "final_crack_extension_mm": None,
        "hole_reached": False,
        "E_elastic_kNmm": None,
        "E_fracture_kNmm": None,
        "E_total_kNmm": None,
        "physical_elements_count": 10299,
        "layered_elements_count": 30897
    }

    # 1. Parse .sta file
    if os.path.exists(sta_path):
        with open(sta_path, "r") as f:
            lines = f.readlines()
        s1_incs = 0
        s1_cutbacks = 0
        s1_iters = 0
        s2_incs = 0
        s2_cutbacks = 0
        s2_iters = 0
        for line in lines:
            if "THE ANALYSIS HAS COMPLETED SUCCESSFULLY" in line:
                results["sta_completed_successfully"] = True
            parts = line.strip().split()
            if len(parts) >= 6 and parts[0].isdigit() and parts[1].isdigit():
                step_num = int(parts[0])
                inc_num = int(parts[1])
                att_num = int(parts[2]) if parts[2].isdigit() else 1
                equil_iters = int(parts[4]) if parts[4].isdigit() else 0
                if step_num == 1:
                    s1_incs = max(s1_incs, inc_num)
                    s1_iters += equil_iters
                    if att_num > 1:
                        s1_cutbacks += (att_num - 1)
                elif step_num == 2:
                    s2_incs = max(s2_incs, inc_num)
                    s2_iters += equil_iters
                    if att_num > 1:
                        s2_cutbacks += (att_num - 1)
        results["step1_increments"] = s1_incs
        results["step1_cutbacks"] = s1_cutbacks
        results["step1_equilibrium_iterations"] = s1_iters
        results["step2_increments"] = s2_incs
        results["step2_cutbacks"] = s2_cutbacks
        results["step2_equilibrium_iterations"] = s2_iters
        results["total_increments"] = s1_incs + s2_incs
        results["total_cutbacks"] = s1_cutbacks + s2_cutbacks
        results["total_equilibrium_iterations"] = s1_iters + s2_iters

    # 2. Parse execution logs
    for lp in [log_path, pbs_log_path]:
        if os.path.exists(lp):
            with open(lp, "r") as f:
                log_content = f.read()
            if "Abaqus Finished with Exit Code: 0" in log_content:
                results["exit_code"] = 0
                results["status"] = "COMPLETED_EXIT0"
            elif "Abaqus JOB PK_METHOD_C_DEMO_PROPAGATION_JOB3 COMPLETED" in log_content:
                results["status"] = "COMPLETED_EXIT0"
                if results["exit_code"] is None:
                    results["exit_code"] = 0
            elif "Abaqus/Standard Analysis exited with an error" in log_content:
                results["status"] = "ERROR"
                results["exit_code"] = 1

    # 3. Parse .msg file for timings & errors
    if os.path.exists(msg_path):
        with open(msg_path, "r") as f:
            msg_content = f.read()
        if "0  ERROR MESSAGES" in msg_content:
            results["msg_zero_errors"] = True
            if results["status"] == "UNKNOWN":
                results["status"] = "COMPLETED_EXIT0"
                results["exit_code"] = 0
        elif "TIME INCREMENT REQUIRED IS LESS THAN THE MINIMUM SPECIFIED" in msg_content:
            results["status"] = "CUTBACK_TERMINATION_AT_HOLE_CAPTURE"
            results["exit_code"] = 1
            results["termination_reason"] = "TIME_INCREMENT_LESS_THAN_MINIMUM"

        m_sum = re.search(r"JOB TIME SUMMARY\s+USER TIME \(SEC\)\s*=\s*([-\d\.E\+]+)\s+SYSTEM TIME \(SEC\)\s*=\s*([-\d\.E\+]+)\s+TOTAL CPU TIME \(SEC\)\s*=\s*([-\d\.E\+]+)\s+WALLCLOCK TIME \(SEC\)\s*=\s*([-\d\.E\+]+)", msg_content)
        if m_sum:
            results["user_time_s"] = float(m_sum.group(1))
            results["sys_time_s"] = float(m_sum.group(2))
            results["cpu_time_s"] = float(m_sum.group(3))
            results["walltime_s"] = float(m_sum.group(4))

    # 4. Parse .dat file for RP printouts
    if os.path.exists(dat_path):
        with open(dat_path, "r") as f:
            dat_lines = f.readlines()
        in_rp = False
        dat_history = []
        for line in dat_lines:
            if "NODE SET N_RP" in line:
                in_rp = True
            elif in_rp and "999999" in line:
                parts = line.strip().split()
                if len(parts) >= 3 and parts[0] == "999999":
                    try:
                        u2_val = float(parts[1])
                        rf2_val = float(parts[2])
                        dat_history.append({"u2_mm": u2_val, "rf2_kN": rf2_val})
                    except ValueError:
                        pass
        results["dat_rp_history"] = dat_history

    # 5. Parse uel_energy_balance.csv
    if os.path.exists(energy_csv_path):
        with open(energy_csv_path, "r") as f:
            csv_lines = [l.strip() for l in f.readlines() if l.strip()]
        if len(csv_lines) > 1:
            last_line = csv_lines[-1]
            parts = [p.strip() for p in last_line.split(",")]
            if len(parts) >= 7:
                try:
                    results["E_elastic_kNmm"] = float(parts[4])
                    results["E_fracture_kNmm"] = float(parts[5])
                    results["E_total_kNmm"] = float(parts[6])
                except ValueError:
                    pass

    # 6. Parse ODB for detailed field histories
    if ABAQUS_AVAILABLE and os.path.exists(odb_path):
        print("Opening ODB: %s" % odb_path)
        odb = odbAccess.openOdb(odb_path, readOnly=True)
        try:
            root_inst = odb.rootAssembly.instances[list(odb.rootAssembly.instances.keys())[0]]
            results["nodes_count"] = len(root_inst.nodes)
            results["elements_count"] = len(root_inst.elements)

            # Node coordinates map: nodeLabel -> (x, y)
            node_coords = {}
            for n in root_inst.nodes:
                node_coords[n.label] = (float(n.coordinates[0]), float(n.coordinates[1]))

            # Precompute ligament nodes and elements along y=0.50 mm (band |y - 0.50| <= 0.020 mm)
            ligament_nodes = {}
            for nl, (nx, ny) in node_coords.items():
                if abs(ny - 0.50) <= 0.020:
                    ligament_nodes[nl] = nx

            ligament_elements = {}
            for el in root_inst.elements:
                if el.label <= 10299:
                    try:
                        xs = [node_coords[nl][0] for nl in el.connectivity]
                        ys = [node_coords[nl][1] for nl in el.connectivity]
                        cx = sum(xs) / float(len(xs))
                        cy = sum(ys) / float(len(ys))
                        if abs(cy - 0.50) <= 0.020:
                            # Map both physical label and companion label (phys + 2*10299)
                            ligament_elements[el.label] = cx
                            ligament_elements[el.label + 2 * 10299] = cx
                    except Exception:
                        pass
            print("Precomputed %d ligament nodes and %d ligament elements." % (len(ligament_nodes), len(ligament_elements)))

            # Step 1 End extraction
            if "Step-1-ReEquilibrate" in odb.steps:
                s1 = odb.steps["Step-1-ReEquilibrate"]
                if len(s1.frames) > 0:
                    f1_end = s1.frames[-1]
                    if "RF" in f1_end.fieldOutputs:
                        for v in f1_end.fieldOutputs["RF"].values:
                            if v.nodeLabel == 999999:
                                results["step1_end_RF2_kN"] = float(v.data[1])
                                break
                    if "U" in f1_end.fieldOutputs:
                        for v in f1_end.fieldOutputs["U"].values:
                            if v.nodeLabel == 999999:
                                results["step1_end_u2_mm"] = float(v.data[1])
                                break

            # Step 2 Frame-by-frame extraction
            if "Step-2-Propagate" in odb.steps:
                s2 = odb.steps["Step-2-Propagate"]
                prop_history = []
                max_d_overall = 0.0
                max_h_overall = 0.0
                peak_rf2 = -1e9
                u2_at_peak = None
                max_crack_x = 0.50

                for fi, frame in enumerate(s2.frames):
                    frame_val = float(frame.frameValue)
                    frame_desc = str(frame.description)
                    frame_u2 = None
                    frame_rf2 = None
                    frame_max_d = 0.0
                    frame_max_h = 0.0
                    frame_tip_x = 0.50

                    # Extract RP displacement and reaction force
                    if "U" in frame.fieldOutputs:
                        for v in frame.fieldOutputs["U"].values:
                            if v.nodeLabel == 999999:
                                frame_u2 = float(v.data[1])
                                break

                    if "RF" in frame.fieldOutputs:
                        for v in frame.fieldOutputs["RF"].values:
                            if v.nodeLabel == 999999:
                                frame_rf2 = float(v.data[1])
                                break

                    # Extract damage from SDV1
                    if "SDV1" in frame.fieldOutputs:
                        sdv1 = frame.fieldOutputs["SDV1"]
                        for v in sdv1.values:
                            d_val = float(v.data)
                            if d_val > frame_max_d:
                                frame_max_d = d_val
                            if d_val >= 0.90:
                                cx = ligament_elements.get(v.elementLabel)
                                if cx is not None and cx > frame_tip_x:
                                    frame_tip_x = cx

                    # Also check nodal damage from Layer 1 nodes if present in U
                    if "U" in frame.fieldOutputs:
                        u_field = frame.fieldOutputs["U"]
                        for v in u_field.values:
                            nl = v.nodeLabel
                            if nl in ligament_nodes:
                                d_node = float(v.data[0])  # DOF 1 of Layer 1
                                if d_node > frame_max_d:
                                    frame_max_d = d_node
                                if d_node >= 0.90:
                                    nx = ligament_nodes[nl]
                                    if nx > frame_tip_x:
                                        frame_tip_x = nx

                    if "SDV2" in frame.fieldOutputs:
                        for v in frame.fieldOutputs["SDV2"].values:
                            h_val = float(v.data)
                            if h_val > frame_max_h:
                                frame_max_h = h_val

                    max_d_overall = max(max_d_overall, frame_max_d)
                    max_h_overall = max(max_h_overall, frame_max_h)
                    max_crack_x = max(max_crack_x, frame_tip_x)

                    if frame_rf2 is not None:
                        if frame_rf2 > peak_rf2:
                            peak_rf2 = frame_rf2
                            u2_at_peak = frame_u2

                    delta_a = max(0.0, frame_tip_x - 0.50)
                    prop_history.append({
                        "frame": fi,
                        "frame_time": frame_val,
                        "description": frame_desc,
                        "u2_mm": frame_u2,
                        "RF2_kN": frame_rf2,
                        "max_damage": frame_max_d,
                        "max_history_MPa": frame_max_h,
                        "crack_tip_x_mm": frame_tip_x,
                        "crack_extension_Delta_a_mm": delta_a
                    })

                results["crack_extension_history"] = prop_history
                results["max_damage"] = max_d_overall
                results["peak_damage_SDV1"] = max_d_overall
                results["max_history_MPa"] = max_h_overall
                results["peak_RF2_kN"] = peak_rf2
                results["u2_at_peak_RF2_mm"] = u2_at_peak
                results["final_crack_tip_x_mm"] = max_crack_x
                results["final_crack_extension_mm"] = max(0.0, max_crack_x - 0.50)
                results["hole_reached"] = bool(max_crack_x >= 0.65)

                if len(prop_history) > 0:
                    last_entry = prop_history[-1]
                    results["step2_end_RF2_kN"] = last_entry["RF2_kN"]
                    results["step2_end_u2_mm"] = last_entry["u2_mm"]
                    if peak_rf2 > 0 and last_entry["RF2_kN"] is not None:
                        if last_entry["RF2_kN"] < peak_rf2 * 0.95:
                            results["post_peak_softening_demonstrated"] = True

        finally:
            odb.close()

    # Save summary JSON
    with open(out_json, "w") as f:
        json.dump(results, f, indent=2)
    print("Wrote summary to: %s" % out_json)

    # Save receipt JSON
    receipt = {
        "job_id": results["job_id"],
        "job_name": job_name,
        "run_dir": run_dir,
        "exit_code": results["exit_code"],
        "status": results["status"],
        "termination_reason": results.get("termination_reason", "NORMAL_COMPLETION" if results["exit_code"] == 0 else "ERROR"),
        "solver_completed_cleanly": results["sta_completed_successfully"] and results["msg_zero_errors"],
        "walltime_s": results["walltime_s"],
        "cpu_time_s": results["cpu_time_s"],
        "step1_increments": results["step1_increments"],
        "step1_end_RF2_kN": results["step1_end_RF2_kN"],
        "step2_increments": results["step2_increments"],
        "step2_end_RF2_kN": results["step2_end_RF2_kN"],
        "step2_end_u2_mm": results["step2_end_u2_mm"],
        "peak_RF2_kN": results["peak_RF2_kN"],
        "u2_at_peak_RF2_mm": results["u2_at_peak_RF2_mm"],
        "post_peak_softening_demonstrated": results["post_peak_softening_demonstrated"],
        "peak_damage_SDV1": results["max_damage"],
        "peak_history_SDV2_MPa": results["max_history_MPa"],
        "final_crack_tip_x_mm": results["final_crack_tip_x_mm"],
        "final_crack_extension_mm": results["final_crack_extension_mm"],
        "hole_reached": results["hole_reached"],
        "E_elastic_kNmm": results["E_elastic_kNmm"],
        "E_fracture_kNmm": results["E_fracture_kNmm"],
        "E_total_kNmm": results["E_total_kNmm"],
        "physical_elements_count": results["physical_elements_count"],
        "layered_elements_count": results["layered_elements_count"]
    }
    with open(receipt_json, "w") as f:
        json.dump(receipt, f, indent=2)
    print("Wrote receipt to: %s" % receipt_json)

    return results


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Extract Job-3 forward propagation observables")
    parser.add_argument("--run-dir", default="/scratch9/pr21vyci/runs/mode1_289_method_c_demo_job3")
    args = parser.parse_args()
    res = extract_job3_observables(args.run_dir)
    print("EXTRACTED_JOB3_OBSERVABLES_JSON:")
    print(json.dumps(res, indent=2))
