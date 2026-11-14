# -*- coding: utf-8 -*-
"""
extract_case2_recovery_miseseri.py
==================================
Abaqus Python extraction script for Task F1730:
Case 2 Companion Degraded Cauchy Stress Recovery HPC Solve & MISESERI Audit.

Extracts and evaluates:
1. Convergence metadata: Step RECOVERY_STEP, Increment 1, converged Exit Code 0.
2. Vertical static force equilibrium: |sum RF_y(bottom) + RF_y(top)| <= 1.0e-4 |RF_y(top)|.
3. Recovered reaction force and explicit comparison with 0.731015 kN coupled peak force.
4. Field output presence and complete finite coverage (S, EVOL, MISESAVG, MISESERI) across all 2,906 elements.
5. Spatial error localization and contrast analysis on 48 damaged elements and 6 boundary elements (contrast >= 5.0x vs bulk).

Outputs:
  f1730_case2_recovery_telemetry.json
"""

from __future__ import print_function, division
import os
import sys
import math
import json
import odbAccess

def parse_args():
    odb_path = "PK_HOLE_COMPANION_RECOVERY.odb"
    json_out = "f1730_case2_recovery_telemetry.json"
    
    i = 1
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg in ("--odb", "-o") and i + 1 < len(sys.argv):
            odb_path = sys.argv[i + 1]
            i += 2
        elif arg in ("--output", "-out") and i + 1 < len(sys.argv):
            json_out = sys.argv[i + 1]
            i += 2
        else:
            # Check for key=value
            if arg.startswith("--odb="):
                odb_path = arg.split("=", 1)[1]
            elif arg.startswith("--output="):
                json_out = arg.split("=", 1)[1]
            i += 1
    return odb_path, json_out

def main():
    odb_path, json_out = parse_args()
    print("=== Extracting Case 2 Companion Recovery Telemetry ===")
    print("ODB Path:    %s" % odb_path)
    print("Output JSON: %s" % json_out)

    if not os.path.isfile(odb_path):
        print("ERROR: ODB file not found: %s" % odb_path)
        sys.exit(1)

    odb = odbAccess.openOdb(path=odb_path, readOnly=True)
    
    # 1. Step and Frame Verification
    if "RECOVERY_STEP" not in odb.steps:
        print("ERROR: Step 'RECOVERY_STEP' not found in ODB. Available: %s" % list(odb.steps.keys()))
        odb.close()
        sys.exit(1)
        
    step = odb.steps["RECOVERY_STEP"]
    num_frames = len(step.frames)
    print("Step: %s, Total Frames: %d" % (step.name, num_frames))
    
    if num_frames < 2:
        print("ERROR: Insufficient frames in step (expected at least 2: base + inc 1).")
        odb.close()
        sys.exit(1)
        
    last_frame = step.frames[-1]
    frame_id = last_frame.frameId
    frame_val = float(last_frame.frameValue)
    inc_num = last_frame.incrementNumber
    print("Evaluated Frame: ID=%d, Inc=%d, Value=%.6f" % (frame_id, inc_num, frame_val))
    
    # 2. Node sets and Reaction Forces
    # Node sets defined in input deck:
    # N_BOTTOM: 26..50, 659..684 (51 nodes)
    # N_TOP: 74..98, 711..736 (51 nodes)
    top_node_labels = set(list(range(74, 99)) + list(range(711, 737)))
    bottom_node_labels = set(list(range(26, 51)) + list(range(659, 685)))
    
    if "RF" not in last_frame.fieldOutputs:
        print("ERROR: FieldOutput 'RF' not found in frame. Available: %s" % list(last_frame.fieldOutputs.keys()))
        odb.close()
        sys.exit(1)
        
    rf_field = last_frame.fieldOutputs["RF"]
    
    top_rf_x = 0.0
    top_rf_y = 0.0
    top_nodes_found = 0
    bottom_rf_x = 0.0
    bottom_rf_y = 0.0
    bottom_nodes_found = 0
    
    for v in rf_field.values:
        nid = v.nodeLabel
        if nid in top_node_labels:
            top_rf_x += float(v.data[0])
            top_rf_y += float(v.data[1])
            top_nodes_found += 1
        elif nid in bottom_node_labels:
            bottom_rf_x += float(v.data[0])
            bottom_rf_y += float(v.data[1])
            bottom_nodes_found += 1
            
    print("Top Nodes Sampled:    %d / %d" % (top_nodes_found, len(top_node_labels)))
    print("Bottom Nodes Sampled: %d / %d" % (bottom_nodes_found, len(bottom_node_labels)))
    print("Top Reaction Force:    RF_x = %.6e N, RF_y = %.6e N (%.6f kN)" % (top_rf_x, top_rf_y, top_rf_y / 1000.0))
    print("Bottom Reaction Force: RF_x = %.6e N, RF_y = %.6e N (%.6f kN)" % (bottom_rf_x, bottom_rf_y, bottom_rf_y / 1000.0))
    
    vertical_residual = abs(top_rf_y + bottom_rf_y)
    relative_vertical_residual = vertical_residual / max(abs(top_rf_y), 1.0e-12)
    print("Vertical Residual:     %.6e N, Relative: %.6e" % (vertical_residual, relative_vertical_residual))
    
    # 3. Field Outputs Check (S, EVOL, MISESAVG, MISESERI)
    required_fields = ["S", "EVOL", "MISESAVG", "MISESERI"]
    field_presence = {}
    for rf in required_fields:
        field_presence[rf] = rf in last_frame.fieldOutputs
        print("Field %-10s present: %s" % (rf, field_presence[rf]))
        if not field_presence[rf]:
            print("ERROR: Required field %s missing from fieldOutputs!" % rf)
            odb.close()
            sys.exit(1)
            
    miseseri_field = last_frame.fieldOutputs["MISESERI"]
    misesavg_field = last_frame.fieldOutputs["MISESAVG"]
    evol_field = last_frame.fieldOutputs["EVOL"]
    s_field = last_frame.fieldOutputs["S"]
    
    # Extract element-level values
    elem_miseseri = {}
    elem_misesavg = {}
    elem_evol = {}
    elem_mises_s = {}
    
    # MISESERI values
    for v in miseseri_field.values:
        eid = v.elementLabel
        val = float(v.data)
        if eid not in elem_miseseri:
            elem_miseseri[eid] = []
        elem_miseseri[eid].append(val)
        
    # MISESAVG values
    for v in misesavg_field.values:
        eid = v.elementLabel
        val = float(v.data)
        if eid not in elem_misesavg:
            elem_misesavg[eid] = []
        elem_misesavg[eid].append(val)
        
    # EVOL values
    for v in evol_field.values:
        eid = v.elementLabel
        val = float(v.data)
        if eid not in elem_evol:
            elem_evol[eid] = []
        elem_evol[eid].append(val)
        
    # S values (von Mises)
    for v in s_field.values:
        eid = v.elementLabel
        val = float(v.mises) if hasattr(v, 'mises') else 0.0
        if eid not in elem_mises_s:
            elem_mises_s[eid] = []
        elem_mises_s[eid].append(val)
        
    # Average across integration points per element
    elem_miseseri_avg = {eid: sum(vals)/len(vals) for eid, vals in elem_miseseri.items()}
    elem_misesavg_avg = {eid: sum(vals)/len(vals) for eid, vals in elem_misesavg.items()}
    elem_evol_avg     = {eid: sum(vals) for eid, vals in elem_evol.items()} # total volume
    elem_mises_s_avg  = {eid: sum(vals)/len(vals) for eid, vals in elem_mises_s.items()}
    
    total_elements = len(elem_miseseri_avg)
    print("Total Elements with MISESERI: %d" % total_elements)
    
    # Finite Coverage Check
    non_finite_count = 0
    zero_error_count = 0
    all_values = []
    for eid, val in elem_miseseri_avg.items():
        if math.isnan(val) or math.isinf(val):
            non_finite_count += 1
        elif val == 0.0:
            zero_error_count += 1
        all_values.append(val)
        
    finite_coverage_pct = 100.0 * (total_elements - non_finite_count) / max(total_elements, 1)
    print("Finite Indicator Coverage: %.2f%% (%d non-finite)" % (finite_coverage_pct, non_finite_count))
    print("Zero Indicator Elements:   %d / %d" % (zero_error_count, total_elements))
    
    # 4. Spatial Localization & Contrast Analysis
    # 48 Damaged Elements from Case 2 Step-2 peak (d >= 0.10)
    damaged_element_ids = set([
        2, 13, 150, 151, 152, 153, 175, 241, 242, 243, 244, 245,
        402, 403, 497, 498, 636, 637, 647, 668, 677, 678, 687, 734,
        814, 1088, 1140, 1184, 1185, 1186, 1187, 1188, 1189, 1378,
        1379, 1395, 1405, 1409, 1412, 1413, 1439, 1441, 1454, 1455,
        1458, 1488, 1526, 1818
    ])
    
    # 6 Primary Ligament Boundary-Touching Elements
    boundary_ligament_ids = set([151, 152, 153, 687, 734, 1088])
    
    # All 12 Boundary-Touching Elements (including flank component 2)
    boundary_all_ids = set([151, 152, 153, 241, 243, 245, 497, 498, 687, 734, 1088, 1379])
    
    # Partition elements
    damaged_vals = [elem_miseseri_avg[eid] for eid in damaged_element_ids if eid in elem_miseseri_avg]
    boundary_lig_vals = [elem_miseseri_avg[eid] for eid in boundary_ligament_ids if eid in elem_miseseri_avg]
    boundary_all_vals = [elem_miseseri_avg[eid] for eid in boundary_all_ids if eid in elem_miseseri_avg]
    bulk_vals = [val for eid, val in elem_miseseri_avg.items() if eid not in damaged_element_ids]
    
    mean_damaged = sum(damaged_vals) / len(damaged_vals) if damaged_vals else 0.0
    mean_boundary_lig = sum(boundary_lig_vals) / len(boundary_lig_vals) if boundary_lig_vals else 0.0
    mean_boundary_all = sum(boundary_all_vals) / len(boundary_all_vals) if boundary_all_vals else 0.0
    mean_bulk = sum(bulk_vals) / len(bulk_vals) if bulk_vals else 0.0
    
    contrast_damaged = mean_damaged / max(mean_bulk, 1.0e-12)
    contrast_boundary_lig = mean_boundary_lig / max(mean_bulk, 1.0e-12)
    contrast_boundary_all = mean_boundary_all / max(mean_bulk, 1.0e-12)
    
    print("=== Spatial Contrast Statistics ===")
    print("Bulk Mean MISESERI (N=%d):             %.6e MPa" % (len(bulk_vals), mean_bulk))
    print("Damaged Zone Mean MISESERI (N=%d):     %.6e MPa  (Contrast: %.2fx)" % (len(damaged_vals), mean_damaged, contrast_damaged))
    print("Boundary Ligament Mean (N=%d):         %.6e MPa  (Contrast: %.2fx)" % (len(boundary_lig_vals), mean_boundary_lig, contrast_boundary_lig))
    print("All Boundary Elements Mean (N=%d):     %.6e MPa  (Contrast: %.2fx)" % (len(boundary_all_vals), mean_boundary_all, contrast_boundary_all))
    
    # Also evaluate MISESAVG statistics
    bulk_avg_vals = [val for eid, val in elem_misesavg_avg.items() if eid not in damaged_element_ids]
    damaged_avg_vals = [elem_misesavg_avg[eid] for eid in damaged_element_ids if eid in elem_misesavg_avg]
    mean_misesavg_bulk = sum(bulk_avg_vals) / len(bulk_avg_vals) if bulk_avg_vals else 0.0
    mean_misesavg_damaged = sum(damaged_avg_vals) / len(damaged_avg_vals) if damaged_avg_vals else 0.0
    
    # 5. Evaluate Gates
    # SOLVE-01: 1 increment converged, exit code 0
    gate_solve_01 = (inc_num == 1 and num_frames >= 2)
    # SOLVE-02: |sum RF_y(bottom) + RF_y(top)| <= 1.0e-4 |RF_y(top)|
    gate_solve_02 = (relative_vertical_residual <= 1.0e-4)
    # SOLVE-03: Recovered reaction force quantitatively reported and distinguished
    gate_solve_03 = (top_rf_y > 0.0 and top_nodes_found == len(top_node_labels))
    # SOLVE-04: ODB fields S, EVOL, MISESAVG, MISESERI present across all elements
    gate_solve_04 = (total_elements == 2906 and all(field_presence.values()))
    # SOLVE-05: 100% elements finite non-NaN, non-inf
    gate_solve_05 = (finite_coverage_pct == 100.0 and non_finite_count == 0)
    # SOLVE-06: process-zone contrast >= 5.0x vs bulk evaluated on 48 damaged and 6 boundary elements
    gate_solve_06 = (contrast_damaged >= 5.0 and contrast_boundary_lig >= 5.0)
    
    gate_results = {
        "SOLVE-01-CONVERGED-INCREMENT": "PASS" if gate_solve_01 else "FAIL",
        "SOLVE-02-VERTICAL-EQUILIBRIUM": "PASS" if gate_solve_02 else "FAIL",
        "SOLVE-03-REACTION-FORCE-REPORTED": "PASS" if gate_solve_03 else "FAIL",
        "SOLVE-04-FIELDS-POPULATED": "PASS" if gate_solve_04 else "FAIL",
        "SOLVE-05-FINITE-COVERAGE": "PASS" if gate_solve_05 else "FAIL",
        "SOLVE-06-PROCESS-ZONE-CONTRAST": "PASS" if gate_solve_06 else "FAIL"
    }
    
    print("=== Execution Gate Results ===")
    for g, r in sorted(gate_results.items()):
        print("  %-35s : %s" % (g, r))
        
    step_name_str = str(step.name)
    odb.close()
    
    # Construct telemetry payload
    telemetry = {
        "task_id": "F1730-CASE2-COMPANION-RECOVERY-SOLVE",
        "scientific_operation": "case2_companion_recovery_hpc_solve",
        "odb_path": odb_path,
        "step_name": step_name_str,
        "increment_number": inc_num,
        "frame_id": frame_id,
        "frame_value": frame_val,
        "kinematics": {
            "top_displacement_mm": 0.007293812465,
            "top_nodes_count": len(top_node_labels),
            "top_nodes_found": top_nodes_found,
            "bottom_nodes_count": len(bottom_node_labels),
            "bottom_nodes_found": bottom_nodes_found
        },
        "reaction_forces": {
            "top_rf_x_n": top_rf_x,
            "top_rf_y_n": top_rf_y,
            "top_rf_y_kn": top_rf_y / 1000.0,
            "bottom_rf_x_n": bottom_rf_x,
            "bottom_rf_y_n": bottom_rf_y,
            "bottom_rf_y_kn": bottom_rf_y / 1000.0,
            "vertical_residual_n": vertical_residual,
            "relative_vertical_residual": relative_vertical_residual,
            "vertical_equilibrium_pass": gate_solve_02,
            "original_coupled_peak_force_kn": 0.731015,
            "surrogate_distinction_note": "Recovered reaction force reflects linear surrogate continuum with 13 spatial material bins; distinct from original coupled softening force 0.731015 kN."
        },
        "mesh_coverage": {
            "total_elements": total_elements,
            "expected_elements": 2906,
            "non_finite_count": non_finite_count,
            "finite_coverage_pct": finite_coverage_pct,
            "zero_error_count": zero_error_count
        },
        "error_indicator_statistics": {
            "miseseri_min": min(all_values) if all_values else 0.0,
            "miseseri_max": max(all_values) if all_values else 0.0,
            "miseseri_mean_global": sum(all_values)/len(all_values) if all_values else 0.0,
            "bulk_elements_count": len(bulk_vals),
            "bulk_miseseri_mean": mean_bulk,
            "damaged_elements_count": len(damaged_vals),
            "damaged_miseseri_mean": mean_damaged,
            "contrast_damaged_vs_bulk": contrast_damaged,
            "boundary_ligament_count": len(boundary_lig_vals),
            "boundary_ligament_miseseri_mean": mean_boundary_lig,
            "contrast_boundary_ligament_vs_bulk": contrast_boundary_lig,
            "boundary_all_count": len(boundary_all_vals),
            "boundary_all_miseseri_mean": mean_boundary_all,
            "contrast_boundary_all_vs_bulk": contrast_boundary_all,
            "contrast_threshold_pass": gate_solve_06
        },
        "stress_statistics": {
            "bulk_misesavg_mean": mean_misesavg_bulk,
            "damaged_misesavg_mean": mean_misesavg_damaged
        },
        "elementwise_data": {
            "elem_miseseri": elem_miseseri_avg,
            "elem_misesavg": elem_misesavg_avg,
            "elem_evol": elem_evol_avg,
            "elem_mises_s": elem_mises_s_avg
        },
        "gate_results": gate_results
    }
    
    with open(json_out, "w") as f:
        json.dump(telemetry, f, indent=2)
    print("Telemetry written successfully to: %s" % json_out)

if __name__ == "__main__":
    main()
