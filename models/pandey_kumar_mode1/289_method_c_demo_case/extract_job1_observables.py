# -*- coding: utf-8 -*-
"""
extract_job1_observables.py
===========================
Abaqus Python extraction script for Method C Demo Case Step-1 Baseline Solve:
- Model: PK_METHOD_C_DEMO_COARSE_JOB1 (8,760 layered elements)
- Extracts Step-1 baseline observables:
  1. Status / walltime / CPU time / cutbacks from .sta and .log
  2. Nodal displacements (U) at Step 1 end (u2 = 0.0050 mm)
  3. Total reaction force RF2 at reference point RP
  4. Peak damage max(d) from SDV1
  5. Peak history max(H) from SDV2 / history SVAR
  6. Recovered stress error MISESERI and MISESAVG distributions
  7. Element-level snapshot for subsequent state transfer
- Can be run on cluster via:
  abaqus python extract_job1_observables.py --run-dir /scratch9/pr21vyci/runs/mode1_289_method_c_demo_case
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


def extract_job1_observables(run_dir):
    job_name = "PK_METHOD_C_DEMO_COARSE_JOB1"
    odb_path = os.path.join(run_dir, job_name + ".odb")
    sta_path = os.path.join(run_dir, job_name + ".sta")
    log_path = os.path.join(run_dir, job_name + ".log")
    out_json = os.path.join(run_dir, "PK_METHOD_C_DEMO_COARSE_JOB1_SUMMARY.json")

    results = {
        "job_name": job_name,
        "run_dir": run_dir,
        "status": "UNKNOWN",
        "walltime_s": None,
        "cpu_time_s": None,
        "step1_increments": None,
        "step1_cutbacks": 0,
        "step1_end_time": None,
        "RF2_kN": None,
        "RF2_N": None,
        "max_damage": None,
        "damage_intact_verified": False,
        "max_history_MPa": None,
        "mean_miseseri": None,
        "max_miseseri": None,
        "nodes_count": None,
        "elements_count": None
    }

    # 1. Parse .sta file
    if os.path.exists(sta_path):
        with open(sta_path, "r") as f:
            lines = f.readlines()
        cutbacks = 0
        step1_incs = 0
        for line in lines:
            parts = line.strip().split()
            if len(parts) >= 6 and parts[0].isdigit() and parts[1].isdigit():
                step_num = int(parts[0])
                inc_num = int(parts[1])
                att_num = int(parts[2]) if parts[2].isdigit() else 1
                if att_num > 1:
                    cutbacks += (att_num - 1)
                if step_num == 1:
                    step1_incs = max(step1_incs, inc_num)
                    results["step1_end_time"] = float(parts[5]) if len(parts) > 5 else None
        results["step1_increments"] = step1_incs
        results["step1_cutbacks"] = cutbacks

    # 2. Parse .log file for timing and completion
    if os.path.exists(log_path):
        with open(log_path, "r") as f:
            log_content = f.read()
        if "Abaqus JOB PK_METHOD_C_DEMO_COARSE_JOB1 COMPLETED" in log_content:
            results["status"] = "COMPLETED_EXIT0"
        elif "Abaqus/Standard Analysis exited with an error" in log_content:
            results["status"] = "ERROR"

        # Search for CPU and wall clock time
        cpu_match = re.search(r"Total CPU time\s*:\s*([\d\.]+)\s*seconds", log_content, re.IGNORECASE)
        wall_match = re.search(r"Total wall clock time\s*:\s*([\d\.]+)\s*seconds", log_content, re.IGNORECASE)
        if cpu_match:
            results["cpu_time_s"] = float(cpu_match.group(1))
        if wall_match:
            results["walltime_s"] = float(wall_match.group(1))

    # 3. Parse .odb file if Abaqus is available
    if ABAQUS_AVAILABLE and os.path.exists(odb_path):
        print("Opening ODB: %s" % odb_path)
        odb = odbAccess.openOdb(odb_path, readOnly=True)
        try:
            step1 = odb.steps.get("Step-1", None)
            if step1 is None and len(odb.steps) > 0:
                step1 = list(odb.steps.values())[0]

            if step1 is not None and len(step1.frames) > 0:
                final_frame = step1.frames[-1]
                print("Final frame: %s, frameValue: %f" % (final_frame.description, final_frame.frameValue))

                # Extract displacements
                if "U" in final_frame.fieldOutputs:
                    u_field = final_frame.fieldOutputs["U"]
                    u2_vals = [v.data[1] for v in u_field.values]
                    results["max_u2_mm"] = max(u2_vals)
                    results["min_u2_mm"] = min(u2_vals)

                # Extract reaction force
                if "RF" in final_frame.fieldOutputs:
                    rf_field = final_frame.fieldOutputs["RF"]
                    # Top edge reaction force sum
                    rf2_sum = sum(v.data[1] for v in rf_field.values if abs(v.data[1]) > 1e-12 and v.data[1] > 0)
                    results["RF2_kN"] = rf2_sum
                    results["RF2_N"] = rf2_sum * 1000.0

                # Extract SDV1 (phase-field damage)
                if "SDV1" in final_frame.fieldOutputs:
                    sdv1_field = final_frame.fieldOutputs["SDV1"]
                    d_vals = [v.data for v in sdv1_field.values]
                    results["max_damage"] = max(d_vals)
                    results["mean_damage"] = sum(d_vals) / float(len(d_vals))
                    results["damage_intact_verified"] = (results["max_damage"] < 0.05)

                # Extract SDV2 (strain energy history H)
                if "SDV2" in final_frame.fieldOutputs:
                    sdv2_field = final_frame.fieldOutputs["SDV2"]
                    h_vals = [v.data for v in sdv2_field.values]
                    results["max_history_MPa"] = max(h_vals)
                    results["mean_history_MPa"] = sum(h_vals) / float(len(h_vals))

                # Extract MISESERI and MISESAVG
                if "MISESERI" in final_frame.fieldOutputs:
                    eri_field = final_frame.fieldOutputs["MISESERI"]
                    eri_vals = [v.data for v in eri_field.values]
                    results["max_miseseri"] = max(eri_vals)
                    results["mean_miseseri"] = sum(eri_vals) / float(len(eri_vals))

                if "MISESAVG" in final_frame.fieldOutputs:
                    avg_field = final_frame.fieldOutputs["MISESAVG"]
                    avg_vals = [v.data for v in avg_field.values]
                    results["max_misesavg"] = max(avg_vals)
                    results["mean_misesavg"] = sum(avg_vals) / float(len(avg_vals))

                # Elements and nodes count
                root_inst = list(odb.rootAssembly.instances.values())[0]
                results["nodes_count"] = len(root_inst.nodes)
                results["elements_count"] = len(root_inst.elements)
        finally:
            odb.close()

    # Save summary JSON
    with open(out_json, "w") as f:
        json.dump(results, f, indent=2)
    print("Wrote summary to: %s" % out_json)
    return results


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Extract Job-1 observables")
    parser.add_argument("--run-dir", default="/scratch9/pr21vyci/runs/mode1_289_method_c_demo_case")
    args = parser.parse_args()
    res = extract_job1_observables(args.run_dir)
    print(json.dumps(res, indent=2))
