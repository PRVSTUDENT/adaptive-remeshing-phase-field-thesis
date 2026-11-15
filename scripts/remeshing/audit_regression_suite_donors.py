# -*- coding: utf-8 -*-
"""
scripts/remeshing/audit_regression_suite_donors.py
=================================================
Targeted read-only Abaqus Python audit script for Unified Method A regression suite donors:
- Case 2: PK_HOLE_COMPANION_RECOVERY.odb (RECOVERY_STEP, LAST_INCREMENT)
- Case 3: PK_SEC43_PRESCRIBED_STATE2.odb and PK_SEC43_PRESCRIBED_STATE4.odb
- Case 5: PK_F1726_SEVEN_HOLE_COARSE.odb (Step-2, ALL_INCREMENTS / LAST_INCREMENT)

Executes under Abaqus CAE/Python environment, checks instances, steps, frames,
and presence/extrema of MISESERI, MISESAVG, EVOL, and outputs a JSON report.
"""

from __future__ import print_function
import os
import sys
import json

try:
    from odbAccess import openOdb
except ImportError:
    print("ERROR: odbAccess module not available. Must be run with abaqus python.")
    sys.exit(1)


def audit_odb(odb_path, target_step_name=None, target_frame_idx=-1):
    print("Auditing ODB: %s" % odb_path)
    if not os.path.isfile(odb_path):
        return {
            "status": "FILE_NOT_FOUND",
            "path": odb_path
        }

    file_size_bytes = os.path.getsize(odb_path)
    odb = openOdb(odb_path, readOnly=True)

    root_assembly = odb.rootAssembly
    instances_info = {}
    total_elements = 0
    total_nodes = 0
    for name, inst in root_assembly.instances.items():
        n_elem = len(inst.elements)
        n_nodes = len(inst.nodes)
        instances_info[name] = {
            "num_elements": n_elem,
            "num_nodes": n_nodes
        }
        total_elements += n_elem
        total_nodes += n_nodes

    steps_info = {}
    for sname, step in odb.steps.items():
        n_frames = len(step.frames)
        total_time = step.timePeriod if hasattr(step, 'timePeriod') else 0.0
        steps_info[sname] = {
            "num_frames": n_frames,
            "time_period": float(total_time)
        }

    # If target step not specified, use last step
    if target_step_name is None:
        target_step_name = list(odb.steps.keys())[-1]

    if target_step_name not in odb.steps:
        odb.close()
        return {
            "status": "STEP_NOT_FOUND",
            "path": odb_path,
            "size_bytes": file_size_bytes,
            "instances": instances_info,
            "available_steps": steps_info,
            "requested_step": target_step_name
        }

    step = odb.steps[target_step_name]
    num_frames = len(step.frames)

    # Resolve frame index
    if target_frame_idx < 0:
        actual_frame_idx = num_frames + target_frame_idx
    else:
        actual_frame_idx = target_frame_idx

    if actual_frame_idx < 0 or actual_frame_idx >= num_frames:
        odb.close()
        return {
            "status": "FRAME_INDEX_OUT_OF_RANGE",
            "path": odb_path,
            "size_bytes": file_size_bytes,
            "requested_frame": target_frame_idx,
            "num_frames": num_frames
        }

    frame = step.frames[actual_frame_idx]
    frame_val = float(frame.frameValue)
    frame_desc = str(frame.description)

    available_fields = list(frame.fieldOutputs.keys())

    # Check target fields
    field_summaries = {}
    for fld_name in ['MISESERI', 'MISESAVG', 'EVOL', 'SDV1', 'SDV_D', 'S']:
        if fld_name in frame.fieldOutputs:
            fld = frame.fieldOutputs[fld_name]
            vals = []
            for v in fld.values:
                if v.data is not None:
                    try:
                        # scalar or tensor
                        if hasattr(v.data, '__iter__'):
                            vals.append(float(v.data[0]))
                        else:
                            vals.append(float(v.data))
                    except Exception:
                        pass
            if vals:
                field_summaries[fld_name] = {
                    "present": True,
                    "num_values": len(vals),
                    "min": min(vals),
                    "max": max(vals),
                    "mean": sum(vals) / float(len(vals))
                }
            else:
                field_summaries[fld_name] = {
                    "present": True,
                    "num_values": 0
                }
        else:
            field_summaries[fld_name] = {
                "present": False
            }

    odb.close()

    return {
        "status": "QUALIFIED",
        "path": odb_path,
        "size_bytes": file_size_bytes,
        "total_elements": total_elements,
        "total_nodes": total_nodes,
        "instances": instances_info,
        "steps": steps_info,
        "audited_step": target_step_name,
        "audited_frame_index": actual_frame_idx,
        "audited_frame_value": frame_val,
        "audited_frame_description": frame_desc,
        "available_fields": available_fields,
        "field_summaries": field_summaries
    }


def main():
    print("================================================================================")
    print("TARGETED READ-ONLY ABAQUS ODB AUDIT: REGRESSION SUITE DONORS (CASES 2, 3, 5)")
    print("================================================================================")

    out_file = "donor_preflight_audit.json"
    if len(sys.argv) > 1:
        out_file = sys.argv[1]

    # Pre-defined donor configurations on cluster
    donors_to_audit = [
        {
            "case_id": "case_2",
            "name": "Case 2 Off-Axis Hole Companion Recovery",
            "path": "/scratch9/pr21vyci/runs/f1730_case2_recovery_solve/PK_HOLE_COMPANION_RECOVERY.odb",
            "step": "RECOVERY_STEP",
            "frame": -1
        },
        {
            "case_id": "case_3_state2",
            "name": "Case 3 Notched Plate with Pins State 2",
            "path": "/scratch9/pr21vyci/runs/mode1_pk_f1741_case3_remesh/PK_SEC43_PRESCRIBED_STATE2.odb",
            "step": "RECOVERY_STEP",
            "frame": -1
        },
        {
            "case_id": "case_3_state4",
            "name": "Case 3 Notched Plate with Pins State 4",
            "path": "/scratch9/pr21vyci/runs/mode1_pk_f1741_case3_remesh/PK_SEC43_PRESCRIBED_STATE4.odb",
            "step": "RECOVERY_STEP",
            "frame": -1
        },
        {
            "case_id": "case_3_parent",
            "name": "Case 3 Parent Staggered Solve Frame 30",
            "path": "/scratch9/pr21vyci/runs/mode1_pk_sec43_staggered_job1/PK_SEC43_STAGGERED_JOB1.odb",
            "step": "Step-1",
            "frame": 30
        },
        {
            "case_id": "case_3_parent_frame55",
            "name": "Case 3 Parent Staggered Solve Frame 55",
            "path": "/scratch9/pr21vyci/runs/mode1_pk_sec43_staggered_job1/PK_SEC43_STAGGERED_JOB1.odb",
            "step": "Step-1",
            "frame": 55
        },
        {
            "case_id": "case_5",
            "name": "Case 5 Seven-Hole Plate Coarse Step-2",
            "path": "/scratch9/pr21vyci/runs/mode1_pk_f1765_case5_pilot/PK_F1726_SEVEN_HOLE_COARSE.odb",
            "step": "Step-2",
            "frame": -1
        }
    ]

    results = {}
    all_passed = True

    for d in donors_to_audit:
        print("\n--- Auditing %s ---" % d["name"])
        res = audit_odb(d["path"], d.get("step"), d.get("frame", -1))
        results[d["case_id"]] = {
            "name": d["name"],
            "config": d,
            "audit": res
        }
        if res.get("status") != "QUALIFIED":
            print("  Result: FAILED (%s)" % res.get("status"))
            all_passed = False
        else:
            print("  Result: QUALIFIED")
            flds = res.get("field_summaries", {})
            if "MISESERI" in flds and flds["MISESERI"]["present"]:
                print("  MISESERI: Present (min=%g, max=%g, mean=%g)" % (
                    flds["MISESERI"]["min"], flds["MISESERI"]["max"], flds["MISESERI"]["mean"]
                ))
            else:
                print("  MISESERI: NOT PRESENT or NO VALUES")

    report = {
        "audit_version": "1.0.0",
        "task_id": "F1773-EXECUTION-READINESS-PREFLIGHT",
        "all_donors_qualified": all_passed,
        "donors": results
    }

    with open(out_file, "w") as f:
        json.dump(report, f, indent=2)

    print("\nAudit written to %s" % out_file)
    print("All donors qualified: %s" % all_passed)


if __name__ == "__main__":
    main()
