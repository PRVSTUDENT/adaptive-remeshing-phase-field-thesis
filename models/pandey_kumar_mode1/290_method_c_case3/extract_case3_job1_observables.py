# -*- coding: utf-8 -*-
"""
extract_case3_job1_observables.py
=================================
Abaqus Python extraction script for Method C Case 3 Job-1 Coarse Baseline Solve:
- Benchmark: Pandey & Kumar (2025) Section 4.3 Rectangular Notched Plate with Hole and Pins
- Physical mesh: 4,671 elements (4,524 quads, 147 tris)
- Layered deck: PK_METHOD_C_CASE3_COARSE_JOB1 (14,013 layered elements)
- Execution:
    Step 1: Pre-critical linear-elastic loading to u2 = 0.05 mm (50 increments)
    Step 2: Forward crack propagation to u2 = 0.4125 mm
- Extracts:
    1. Execution telemetry (exit code, status, walltime, CPU time, cutbacks, iterations) from .sta, .log, .msg
    2. Step-1 baseline observables: RF2, U2, max damage d, mean damage d, max history H, MISESERI/MISESAVG
    3. Step-2 forward propagation observables: RF2(u2) curve, peak force, post-peak softening,
       crack-tip coordinates (x_tip, y_tip), crack extension Delta a from notch tip (10.0, 70.0) mm
    4. Energy components from uel_energy_balance.csv (E_elastic, E_fracture, E_total)
    5. Outputs PK_METHOD_C_CASE3_COARSE_JOB1_SUMMARY.json and RECEIPT.json
- Usage:
    abaqus python extract_case3_job1_observables.py --run-dir /scratch9/pr21vyci/runs/mode1_290_method_c_case3
"""
from __future__ import print_function
import os
import sys
import json
import re
import math

try:
    import odbAccess
    from abaqusConstants import *
    ABAQUS_AVAILABLE = True
except ImportError:
    ABAQUS_AVAILABLE = False


def extract_case3_job1_observables(run_dir):
    job_name = "PK_METHOD_C_CASE3_COARSE_JOB1"
    odb_path = os.path.join(run_dir, job_name + ".odb")
    sta_path = os.path.join(run_dir, job_name + ".sta")
    log_path = os.path.join(run_dir, job_name + ".log")
    pbs_log_path = os.path.join(run_dir, "pbs_execution.log")
    msg_path = os.path.join(run_dir, job_name + ".msg")
    dat_path = os.path.join(run_dir, job_name + ".dat")
    energy_csv_path = os.path.join(run_dir, "uel_energy_balance.csv")
    out_json = os.path.join(run_dir, "PK_METHOD_C_CASE3_COARSE_JOB1_SUMMARY.json")
    receipt_json = os.path.join(run_dir, "PK_METHOD_C_CASE3_COARSE_JOB1_RECEIPT.json")

    results = {
        "job_id": "1424711.mmaster02",
        "job_name": job_name,
        "run_dir": run_dir,
        "benchmark": "Pandey & Kumar (2025) Section 4.3",
        "case_id": "method_c_case3",
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
        "step1_end_time": None,
        "step1_end_u2_mm": None,
        "step1_end_RF2_kN": None,
        "step1_max_damage": None,
        "step1_mean_damage": None,
        "step1_max_history_MPa": None,
        "step1_mean_history_MPa": None,
        "step1_max_miseseri": None,
        "step1_mean_miseseri": None,
        "step1_max_misesavg": None,
        "step1_mean_misesavg": None,
        "step2_increments": 0,
        "step2_cutbacks": 0,
        "step2_equilibrium_iterations": 0,
        "step2_end_time": None,
        "step2_end_u2_mm": None,
        "step2_end_RF2_kN": None,
        "total_increments": 0,
        "total_cutbacks": 0,
        "total_equilibrium_iterations": 0,
        "peak_RF2_kN": None,
        "u2_at_peak_RF2_mm": None,
        "post_peak_softening_demonstrated": False,
        "max_damage": None,
        "mean_damage": None,
        "max_history_MPa": None,
        "mean_history_MPa": None,
        "initial_notch_tip_x_mm": 10.0,
        "initial_notch_tip_y_mm": 70.0,
        "central_hole_center_x_mm": 36.5,
        "central_hole_center_y_mm": 51.0,
        "central_hole_radius_mm": 10.0,
        "final_crack_tip_x_mm": 10.0,
        "final_crack_tip_y_mm": 70.0,
        "final_crack_extension_mm": 0.0,
        "forward_crack_growth_demonstrated": False,
        "E_elastic_kNmm": None,
        "E_fracture_kNmm": None,
        "E_total_kNmm": None,
        "physical_elements_count": 4671,
        "layered_elements_count": 14013,
        "nodes_count": 4813,
        "propagation_history": []
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
                step_time = float(parts[5]) if len(parts) > 5 else 0.0
                if step_num == 1:
                    s1_incs = max(s1_incs, inc_num)
                    s1_iters += equil_iters
                    results["step1_end_time"] = step_time
                    if att_num > 1:
                        s1_cutbacks += (att_num - 1)
                elif step_num == 2:
                    s2_incs = max(s2_incs, inc_num)
                    s2_iters += equil_iters
                    results["step2_end_time"] = step_time
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
            elif "Abaqus JOB PK_METHOD_C_CASE3_COARSE_JOB1 COMPLETED" in log_content:
                results["status"] = "COMPLETED_EXIT0"
                if results["exit_code"] is None:
                    results["exit_code"] = 0
            elif "Abaqus/Standard Analysis exited with an error" in log_content:
                results["status"] = "ERROR"
                results["exit_code"] = 1

            cpu_match = re.search(r"Total CPU time\s*:\s*([\d\.]+)\s*seconds", log_content, re.IGNORECASE)
            wall_match = re.search(r"Total wall clock time\s*:\s*([\d\.]+)\s*seconds", log_content, re.IGNORECASE)
            if cpu_match and results["cpu_time_s"] is None:
                results["cpu_time_s"] = float(cpu_match.group(1))
            if wall_match and results["walltime_s"] is None:
                results["walltime_s"] = float(wall_match.group(1))

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
            results["status"] = "PHYSICAL_CUTBACK_TERMINATION"
            results["exit_code"] = 1
            results["termination_reason"] = "TIME_INCREMENT_LESS_THAN_MINIMUM"

        m_sum = re.search(r"JOB TIME SUMMARY\s+USER TIME \(SEC\)\s*=\s*([-\d\.E\+]+)\s+SYSTEM TIME \(SEC\)\s*=\s*([-\d\.E\+]+)\s+TOTAL CPU TIME \(SEC\)\s*=\s*([-\d\.E\+]+)\s+WALLCLOCK TIME \(SEC\)\s*=\s*([-\d\.E\+]+)", msg_content)
        if m_sum:
            results["user_time_s"] = float(m_sum.group(1))
            results["sys_time_s"] = float(m_sum.group(2))
            results["cpu_time_s"] = float(m_sum.group(3))
            results["walltime_s"] = float(m_sum.group(4))

    # 4. Parse .dat file for RP printouts across Step 1 and Step 2
    dat_history = []
    if os.path.exists(dat_path):
        with open(dat_path, "r") as f:
            dat_lines = f.readlines()
        in_rp = False
        current_step = 0
        for line in dat_lines:
            if "STEP 1" in line:
                current_step = 1
            elif "STEP 2" in line:
                current_step = 2
            if "NODE SET N_RP" in line:
                in_rp = True
            elif in_rp and "999999" in line:
                parts = line.strip().split()
                if len(parts) >= 3 and parts[0] == "999999":
                    try:
                        u2_val = float(parts[1])
                        rf2_val = float(parts[2])
                        dat_history.append({"step": current_step, "u2_mm": u2_val, "rf2_kN": rf2_val})
                        if current_step == 1:
                            results["step1_end_u2_mm"] = u2_val
                            results["step1_end_RF2_kN"] = rf2_val
                        elif current_step == 2:
                            results["step2_end_u2_mm"] = u2_val
                            results["step2_end_RF2_kN"] = rf2_val
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

    # 6. Parse ODB for detailed fields
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

            # Element centroids map for companion elements (labels 2*4671+1 to 3*4671)
            # physical elements are 1..4671
            elem_centroids = {}
            for el in root_inst.elements:
                if el.label <= 4671:
                    try:
                        xs = [node_coords[nl][0] for nl in el.connectivity]
                        ys = [node_coords[nl][1] for nl in el.connectivity]
                        cx = sum(xs) / float(len(xs))
                        cy = sum(ys) / float(len(ys))
                        elem_centroids[el.label] = (cx, cy)
                        elem_centroids[el.label + 2 * 4671] = (cx, cy)
                    except Exception:
                        pass

            # Extract Step-1 observables
            s1_key = None
            for k in odb.steps.keys():
                if "Step-1" in k:
                    s1_key = k
                    break
            if s1_key and len(odb.steps[s1_key].frames) > 0:
                s1_final = odb.steps[s1_key].frames[-1]
                if "U" in s1_final.fieldOutputs:
                    for v in s1_final.fieldOutputs["U"].values:
                        if v.nodeLabel == 999999:
                            results["step1_end_u2_mm"] = float(v.data[1])
                            break
                if "RF" in s1_final.fieldOutputs:
                    for v in s1_final.fieldOutputs["RF"].values:
                        if v.nodeLabel == 999999:
                            results["step1_end_RF2_kN"] = float(v.data[1])
                            break
                if "SDV1" in s1_final.fieldOutputs:
                    d_vals = [float(v.data) for v in s1_final.fieldOutputs["SDV1"].values]
                    results["step1_max_damage"] = max(d_vals)
                    results["step1_mean_damage"] = sum(d_vals) / float(len(d_vals))
                if "SDV2" in s1_final.fieldOutputs:
                    h_vals = [float(v.data) for v in s1_final.fieldOutputs["SDV2"].values]
                    results["step1_max_history_MPa"] = max(h_vals)
                    results["step1_mean_history_MPa"] = sum(h_vals) / float(len(h_vals))
                if "MISESERI" in s1_final.fieldOutputs:
                    eri_vals = [float(v.data) for v in s1_final.fieldOutputs["MISESERI"].values]
                    results["step1_max_miseseri"] = max(eri_vals)
                    results["step1_mean_miseseri"] = sum(eri_vals) / float(len(eri_vals))
                if "MISESAVG" in s1_final.fieldOutputs:
                    avg_vals = [float(v.data) for v in s1_final.fieldOutputs["MISESAVG"].values]
                    results["step1_max_misesavg"] = max(avg_vals)
                    results["step1_mean_misesavg"] = sum(avg_vals) / float(len(avg_vals))

            # Extract Step-2 observables & crack tracking
            s2_key = None
            for k in odb.steps.keys():
                if "Step-2" in k:
                    s2_key = k
                    break

            all_rf2 = []
            max_d_overall = results["step1_max_damage"] or 0.0
            max_h_overall = results["step1_max_history_MPa"] or 0.0
            x_tip = 10.0
            y_tip = 70.0

            step_keys_to_track = [k for k in [s1_key, s2_key] if k is not None]
            for sk in step_keys_to_track:
                st = odb.steps[sk]
                is_step2 = (sk == s2_key)
                for fi, frame in enumerate(st.frames):
                    frame_val = float(frame.frameValue)
                    frame_u2 = None
                    frame_rf2 = None
                    frame_max_d = 0.0
                    frame_max_h = 0.0

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

                    if frame_rf2 is not None and frame_u2 is not None:
                        all_rf2.append((frame_u2, frame_rf2))

                    if "SDV1" in frame.fieldOutputs:
                        for v in frame.fieldOutputs["SDV1"].values:
                            d_val = float(v.data)
                            if d_val > frame_max_d:
                                frame_max_d = d_val
                            if d_val > max_d_overall:
                                max_d_overall = d_val
                            # Track crack tip where d >= 0.90
                            if is_step2 and d_val >= 0.90:
                                centroid = elem_centroids.get(v.elementLabel)
                                if centroid:
                                    cx, cy = centroid
                                    # Measure distance from notch tip (10.0, 70.0)
                                    dist = math.sqrt((cx - 10.0)**2 + (cy - 70.0)**2)
                                    curr_dist = math.sqrt((x_tip - 10.0)**2 + (y_tip - 70.0)**2)
                                    if dist > curr_dist:
                                        x_tip = cx
                                        y_tip = cy

                    if "SDV2" in frame.fieldOutputs:
                        for v in frame.fieldOutputs["SDV2"].values:
                            h_val = float(v.data)
                            if h_val > frame_max_h:
                                frame_max_h = h_val
                            if h_val > max_h_overall:
                                max_h_overall = h_val

                    results["propagation_history"].append({
                        "step": sk,
                        "frame_index": fi,
                        "frame_value": frame_val,
                        "u2_mm": frame_u2,
                        "rf2_kN": frame_rf2,
                        "max_damage": frame_max_d,
                        "max_history_MPa": frame_max_h,
                        "crack_tip_x_mm": x_tip,
                        "crack_tip_y_mm": y_tip
                    })

            # Peak force analysis
            if all_rf2:
                peak_u2, peak_rf = max(all_rf2, key=lambda item: item[1])
                results["peak_RF2_kN"] = peak_rf
                results["u2_at_peak_RF2_mm"] = peak_u2
                final_u2, final_rf = all_rf2[-1]
                if final_rf < peak_rf - 0.05 * peak_rf:
                    results["post_peak_softening_demonstrated"] = True

            results["max_damage"] = max_d_overall
            results["max_history_MPa"] = max_h_overall
            results["final_crack_tip_x_mm"] = x_tip
            results["final_crack_tip_y_mm"] = y_tip
            results["final_crack_extension_mm"] = math.sqrt((x_tip - 10.0)**2 + (y_tip - 70.0)**2)
            if results["final_crack_extension_mm"] > 0.05:
                results["forward_crack_growth_demonstrated"] = True

        finally:
            odb.close()

    # Fallback from dat_history if ODB not available
    if results["peak_RF2_kN"] is None and dat_history:
        peak_entry = max(dat_history, key=lambda x: x["rf2_kN"])
        results["peak_RF2_kN"] = peak_entry["rf2_kN"]
        results["u2_at_peak_RF2_mm"] = peak_entry["u2_mm"]
        last_entry = dat_history[-1]
        results["step2_end_u2_mm"] = last_entry["u2_mm"]
        results["step2_end_RF2_kN"] = last_entry["rf2_kN"]
        if last_entry["rf2_kN"] < peak_entry["rf2_kN"] * 0.95:
            results["post_peak_softening_demonstrated"] = True

    # Ensure output directory exists if writing summaries
    if run_dir and not os.path.exists(run_dir):
        try:
            os.makedirs(run_dir)
        except Exception:
            pass

    # Save summary JSON
    if os.path.isdir(run_dir):
        with open(out_json, "w") as f:
            json.dump(results, f, indent=2)
        print("Wrote summary to: %s" % out_json)

    # Save receipt JSON
    receipt = {
        "job_id": results["job_id"],
        "job_name": job_name,
        "run_dir": run_dir,
        "benchmark": "Pandey & Kumar (2025) Section 4.3",
        "case_id": "method_c_case3",
        "exit_code": results["exit_code"],
        "status": results["status"],
        "solver_completed_cleanly": results["sta_completed_successfully"] and results["msg_zero_errors"],
        "walltime_s": results["walltime_s"],
        "cpu_time_s": results["cpu_time_s"],
        "user_time_s": results.get("user_time_s"),
        "sys_time_s": results.get("sys_time_s"),
        "step1_increments": results["step1_increments"],
        "step1_cutbacks": results["step1_cutbacks"],
        "step1_end_u2_mm": results["step1_end_u2_mm"],
        "step1_end_RF2_kN": results["step1_end_RF2_kN"],
        "step1_max_damage": results["step1_max_damage"],
        "step1_mean_damage": results["step1_mean_damage"],
        "step1_max_history_MPa": results["step1_max_history_MPa"],
        "step1_max_miseseri": results["step1_max_miseseri"],
        "step2_increments": results["step2_increments"],
        "step2_cutbacks": results["step2_cutbacks"],
        "step2_end_u2_mm": results["step2_end_u2_mm"],
        "step2_end_RF2_kN": results["step2_end_RF2_kN"],
        "total_increments": results["total_increments"],
        "total_cutbacks": results["total_cutbacks"],
        "peak_RF2_kN": results["peak_RF2_kN"],
        "u2_at_peak_RF2_mm": results["u2_at_peak_RF2_mm"],
        "post_peak_softening_demonstrated": results["post_peak_softening_demonstrated"],
        "max_damage": results["max_damage"],
        "max_history_MPa": results["max_history_MPa"],
        "initial_notch_tip_x_mm": results["initial_notch_tip_x_mm"],
        "initial_notch_tip_y_mm": results["initial_notch_tip_y_mm"],
        "final_crack_tip_x_mm": results["final_crack_tip_x_mm"],
        "final_crack_tip_y_mm": results["final_crack_tip_y_mm"],
        "final_crack_extension_mm": results["final_crack_extension_mm"],
        "forward_crack_growth_demonstrated": results["forward_crack_growth_demonstrated"],
        "E_elastic_kNmm": results["E_elastic_kNmm"],
        "E_fracture_kNmm": results["E_fracture_kNmm"],
        "E_total_kNmm": results["E_total_kNmm"],
        "physical_elements_count": results["physical_elements_count"],
        "layered_elements_count": results["layered_elements_count"],
        "nodes_count": results["nodes_count"]
    }
    if os.path.isdir(run_dir):
        with open(receipt_json, "w") as f:
            json.dump(receipt, f, indent=2)
        print("Wrote receipt to: %s" % receipt_json)

    return results


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Extract Case 3 Job-1 observables")
    parser.add_argument("--run-dir", default="/scratch9/pr21vyci/runs/mode1_290_method_c_case3")
    args = parser.parse_args()
    res = extract_case3_job1_observables(args.run_dir)
    print("EXTRACTED_CASE3_JOB1_OBSERVABLES_JSON:")
    print(json.dumps(res, indent=2))
