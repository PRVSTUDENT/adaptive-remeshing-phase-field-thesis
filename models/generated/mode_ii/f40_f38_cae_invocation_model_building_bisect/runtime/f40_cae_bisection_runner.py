from __future__ import print_function
import json
import os
import sys
import traceback
import datetime

def write_phase_audit(phase_id, phase_name, started, completed, return_code, exc_type, exc_msg, tb_str, dep_status, metrics=None):
    audit_data = {
        "phase_id": phase_id,
        "phase_name": phase_name,
        "started": started,
        "completed": completed,
        "return_code": return_code,
        "exception_type": exc_type,
        "exception_message": exc_msg,
        "traceback": tb_str,
        "dependency_status": dep_status,
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "process_executable": sys.executable,
        "working_directory": os.getcwd(),
        "metrics": metrics or {}
    }
    filename = "{}_AUDIT.json".format(phase_name)
    out_dir = os.environ.get("F40_EVIDENCE_DIR", os.getcwd())
    filepath = os.path.join(out_dir, filename)
    with open(filepath, "w") as f:
        json.dump(audit_data, f, indent=2)

    # Also write in current working directory if different
    if os.getcwd() != out_dir:
        with open(filename, "w") as f:
            json.dump(audit_data, f, indent=2)

    print("PHASE_AUDIT_RECORDED: {} (rc={})".format(phase_name, return_code))

def run_bisection_matrix():
    print("=== F40 Abaqus CAE Bisection Matrix Runner ===")
    runtime_dir = os.environ.get("F40_RUNTIME_DIR", os.getcwd())
    inp_path = os.path.join(runtime_dir, "source_deck.inp")

    # Phase 00: Kernel Startup
    p00_id, p00_name = "P00", "P00_KERNEL_STARTUP"
    try:
        metrics = {
            "python_version": sys.version,
            "executable": sys.executable
        }
        write_phase_audit(p00_id, p00_name, True, True, 0, None, None, None, "ok", metrics=metrics)
    except Exception as exc:
        write_phase_audit(p00_id, p00_name, True, False, 1, type(exc).__name__, str(exc), traceback.format_exc(), "failed")
        return 1

    # Phase 01: Core Abaqus Imports
    p01_id, p01_name = "P01", "P01_IMPORTS"
    try:
        import abaqus
        import abaqusConstants
        from abaqus import mdb
        metrics = {
            "imported_modules": ["abaqus", "abaqusConstants", "mdb"],
            "mdb_type": str(type(mdb))
        }
        write_phase_audit(p01_id, p01_name, True, True, 0, None, None, None, "ok", metrics=metrics)
    except Exception as exc:
        write_phase_audit(p01_id, p01_name, True, False, 1, type(exc).__name__, str(exc), traceback.format_exc(), "failed")
        return 1

    # Phase 02: F38 Entrypoint and Module Execution Probing
    p02_id, p02_name = "P02", "P02_MODULE_LOADING"
    try:
        if runtime_dir not in sys.path:
            sys.path.insert(0, runtime_dir)
        
        file_var_key = '__' + 'file' + '__'
        file_defined = file_var_key in globals()
        entrypoint_script = os.path.join(runtime_dir, "run_f38_cae_diagnostic.py")
        entrypoint_exists = os.path.exists(entrypoint_script)
        
        metrics = {
            "runtime_dir": runtime_dir,
            "file_global_defined": file_defined,
            "entrypoint_script": entrypoint_script,
            "entrypoint_exists": entrypoint_exists,
            "sys_path_0": sys.path[0]
        }
        write_phase_audit(p02_id, p02_name, True, True, 0, None, None, None, "ok", metrics=metrics)
    except Exception as exc:
        write_phase_audit(p02_id, p02_name, True, False, 1, type(exc).__name__, str(exc), traceback.format_exc(), "failed")
        return 1

    # Phase 03: Source Deck Discovery
    p03_id, p03_name = "P03", "P03_SOURCE_DECK_DISCOVERY"
    try:
        if not os.path.exists(inp_path):
            raise IOError("Source input deck missing: {}".format(inp_path))
        byte_size = os.path.getsize(inp_path)
        with open(inp_path, "r") as f:
            lines = f.readlines()
            line_count = len(lines)
        if line_count == 0:
            raise ValueError("Source input deck is empty: {}".format(inp_path))
        
        metrics = {
            "deck_path": inp_path,
            "line_count": line_count,
            "byte_size": byte_size
        }
        write_phase_audit(p03_id, p03_name, True, True, 0, None, None, None, "ok", metrics=metrics)
    except Exception as exc:
        write_phase_audit(p03_id, p03_name, True, False, 1, type(exc).__name__, str(exc), traceback.format_exc(), "failed")
        return 1

    # Phase 04: ModelFromInputFile
    p04_id, p04_name = "P04", "P04_MODEL_FROM_INPUT_FILE"
    try:
        from abaqus import mdb
        model = mdb.ModelFromInputFile(name="F40_MODEL", inputFileName=inp_path)
        metrics = {
            "model_name": "F40_MODEL",
            "total_models": len(mdb.models)
        }
        write_phase_audit(p04_id, p04_name, True, True, 0, None, None, None, "ok", metrics=metrics)
    except Exception as exc:
        write_phase_audit(p04_id, p04_name, True, False, 1, type(exc).__name__, str(exc), traceback.format_exc(), "failed")
        return 1

    # Phase 05: Imported Model Inventory
    p05_id, p05_name = "P05", "P05_IMPORTED_MODEL_INVENTORY"
    try:
        from abaqus import mdb
        model = mdb.models["F40_MODEL"]
        parts_count = len(model.parts)
        instances_count = len(model.rootAssembly.instances)
        part_names = [str(k) for k in model.parts.keys()]
        instance_names = [str(k) for k in model.rootAssembly.instances.keys()]
        
        metrics = {
            "parts_count": parts_count,
            "instances_count": instances_count,
            "part_names": part_names,
            "instance_names": instance_names
        }
        write_phase_audit(p05_id, p05_name, True, True, 0, None, None, None, "ok", metrics=metrics)
    except Exception as exc:
        write_phase_audit(p05_id, p05_name, True, False, 1, type(exc).__name__, str(exc), traceback.format_exc(), "failed")
        return 1

    # Phase 06: Geometry Conversion
    p06_id, p06_name = "P06", "P06_GEOMETRY_CONVERSION"
    try:
        from abaqus import mdb
        model = mdb.models["F40_MODEL"]
        converted_parts = []
        total_faces = 0
        total_edges = 0
        for p_name, part in model.parts.items():
            geom_name = "F40_GEOM_" + str(p_name)
            g_part = model.Part2DGeomFrom2DMesh(name=geom_name, part=part, featureAngle=45.0)
            n_faces = len(g_part.faces)
            n_edges = len(g_part.edges)
            total_faces += n_faces
            total_edges += n_edges
            converted_parts.append(geom_name)

        metrics = {
            "converted_parts": converted_parts,
            "total_faces": total_faces,
            "total_edges": total_edges
        }
        write_phase_audit(p06_id, p06_name, True, True, 0, None, None, None, "ok", metrics=metrics)
    except Exception as exc:
        write_phase_audit(p06_id, p06_name, True, False, 1, type(exc).__name__, str(exc), traceback.format_exc(), "failed")
        return 1

    # Phase 07: Independent Model Ownership
    p07_id, p07_name = "P07", "P07_INDEPENDENT_MODEL_OWNERSHIP"
    try:
        from abaqus import mdb
        probe_model = mdb.Model(name="F40_PROBE_OWNERSHIP")
        all_models = [str(k) for k in mdb.models.keys()]
        metrics = {
            "created_model": "F40_PROBE_OWNERSHIP",
            "all_models": all_models,
            "model_count": len(all_models)
        }
        write_phase_audit(p07_id, p07_name, True, True, 0, None, None, None, "ok", metrics=metrics)
    except Exception as exc:
        write_phase_audit(p07_id, p07_name, True, False, 1, type(exc).__name__, str(exc), traceback.format_exc(), "failed")
        return 1

    # Phase 08: Assembly Operations
    p08_id, p08_name = "P08", "P08_ASSEMBLY_OPERATIONS"
    try:
        from abaqus import mdb
        model = mdb.models["F40_MODEL"]
        assembly = model.rootAssembly
        assembly.regenerate()
        metrics = {
            "assembly_instances": len(assembly.instances),
            "is_regenerated": True
        }
        write_phase_audit(p08_id, p08_name, True, True, 0, None, None, None, "ok", metrics=metrics)
    except Exception as exc:
        write_phase_audit(p08_id, p08_name, True, False, 1, type(exc).__name__, str(exc), traceback.format_exc(), "failed")
        return 1

    # Phase 09: Topology Measurement
    p09_id, p09_name = "P09", "P09_TOPOLOGY_MEASUREMENT"
    try:
        from abaqus import mdb
        model = mdb.models["F40_MODEL"]
        total_nodes = 0
        total_elements = 0
        for p in model.parts.values():
            total_nodes += len(p.nodes)
            total_elements += len(p.elements)
        metrics = {
            "total_nodes": total_nodes,
            "total_elements": total_elements
        }
        write_phase_audit(p09_id, p09_name, True, True, 0, None, None, None, "ok", metrics=metrics)
    except Exception as exc:
        write_phase_audit(p09_id, p09_name, True, False, 1, type(exc).__name__, str(exc), traceback.format_exc(), "failed")
        return 1

    # Phase 10: Sets and Surfaces Inventory
    p10_id, p10_name = "P10", "P10_SETS_SURFACES_INVENTORY"
    try:
        from abaqus import mdb
        model = mdb.models["F40_MODEL"]
        assembly = model.rootAssembly
        set_names = [str(k) for k in assembly.sets.keys()]
        surf_names = [str(k) for k in assembly.surfaces.keys()]
        metrics = {
            "set_count": len(set_names),
            "surface_count": len(surf_names),
            "set_names": set_names,
            "surface_names": surf_names
        }
        write_phase_audit(p10_id, p10_name, True, True, 0, None, None, None, "ok", metrics=metrics)
    except Exception as exc:
        write_phase_audit(p10_id, p10_name, True, False, 1, type(exc).__name__, str(exc), traceback.format_exc(), "failed")
        return 1

    # Phase 11: Step and Field Output Request Probing
    p11_id, p11_name = "P11", "P11_STEP_OUTPUT_PROBING"
    try:
        from abaqus import mdb
        model = mdb.models["F40_MODEL"]
        step_names = [str(k) for k in model.steps.keys()]
        fo_names = [str(k) for k in model.fieldOutputRequests.keys()]
        variables_probed = []
        for fo in model.fieldOutputRequests.values():
            if hasattr(fo, 'variables'):
                variables_probed.extend([str(v) for v in fo.variables])
        metrics = {
            "step_count": len(step_names),
            "step_names": step_names,
            "field_output_requests": fo_names,
            "variables_probed": variables_probed
        }
        write_phase_audit(p11_id, p11_name, True, True, 0, None, None, None, "ok", metrics=metrics)
    except Exception as exc:
        write_phase_audit(p11_id, p11_name, True, False, 1, type(exc).__name__, str(exc), traceback.format_exc(), "failed")
        return 1

    print("ALL_BISECTION_PHASES_COMPLETED_SUCCESSFULLY")
    return 0

if __name__ == "__main__":
    sys.exit(run_bisection_matrix())
