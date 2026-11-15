"""
Detailed probe of Case 2 candidate ODBs to check geometry, element type,
boundary conditions, and physical state.
"""

import sys
import json
import odbAccess

candidates = [
    "models/pandey_kumar_mode1/176_method_a_plate_with_hole/PK_HOLE_METHOD_A_PREANALYSIS.odb",
    "PK_HOLE_COUPLED_RECOVERY.odb",
    "PK_HOLE_F1656_RECOVERY.odb",
    "PK_HOLE_F1659_RECOVERY.odb",
    "PK_HOLE_F1661_RECOVERY.odb",
    "runs/f1683_recovery_candidate_b/PK_HOLE_RECOVERY_B.odb",
    "runs/f1683_recovery_candidate_c/PK_HOLE_RECOVERY_C.odb",
    "runs/f1683_recovery_candidate_d/PK_HOLE_RECOVERY_D.odb",
    "runs/f1684_multistep_recovery/PK_HOLE_MULTISTEP_RECOVERY.odb"
]

results = {}

for path in candidates:
    try:
        odb = odbAccess.openOdb(path=path, readOnly=True)
        # Check root assembly nodes to get bounding box
        assembly = odb.rootAssembly
        xs, ys = [], []
        num_nodes = 0
        num_elements = 0
        element_types = set()
        for instance_name, inst in assembly.instances.items():
            num_nodes += len(inst.nodes)
            num_elements += len(inst.elements)
            for n in inst.nodes:
                c = n.coordinates
                xs.append(float(c[0]))
                ys.append(float(c[1]))
            for el in inst.elements:
                element_types.add(str(el.type))

        bbox = {
            "x_min": min(xs) if xs else None,
            "x_max": max(xs) if xs else None,
            "y_min": min(ys) if ys else None,
            "y_max": max(ys) if ys else None,
        }

        # Check steps and frames
        steps_info = {}
        for sname, step in odb.steps.items():
            s_dict = {
                "procedure": getattr(step, "procedure", "unknown"),
                "num_frames": len(step.frames),
                "frames": []
            }
            for f in step.frames:
                f_info = {
                    "frame_id": f.frameId,
                    "frame_value": f.frameValue,
                    "field_keys": list(f.fieldOutputs.keys())
                }
                if "MISESERI" in f.fieldOutputs:
                    vals = [v.data for v in f.fieldOutputs["MISESERI"].values if hasattr(v, "data") and v.data is not None]
                    f_info["miseseri_min"] = float(min(vals)) if vals else None
                    f_info["miseseri_max"] = float(max(vals)) if vals else None
                    f_info["miseseri_mean"] = float(sum(vals)/len(vals)) if vals else None
                s_dict["frames"].append(f_info)
            steps_info[sname] = s_dict

        results[path] = {
            "num_nodes": num_nodes,
            "num_elements": num_elements,
            "element_types": list(element_types),
            "bbox": bbox,
            "steps": steps_info,
            "error": None
        }
        odb.close()
    except Exception as e:
        results[path] = {"error": str(e)}

print("__DETAILED_JSON_START__")
print(json.dumps(results, indent=2))
print("__DETAILED_JSON_END__")
