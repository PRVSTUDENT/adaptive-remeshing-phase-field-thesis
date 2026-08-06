from __future__ import print_function
import json
import os
import sys
import traceback
import datetime
import hashlib

EXPECTED_ENTRYPOINT_SHA256 = "5d6b4b0f2f016ce1ac4e62cfd1044427c971fdb0db476e85919d72cbcabe096d"
EXPECTED_HELPER_SHA256 = "86fe1c864e021709775b84e26dd32f268573b161c82578146b801f99801a411a"

def load_expected_sha256(runtime_dir):
    manifest_paths = [
        os.path.join(runtime_dir, "..", "PACKAGE_MANIFEST.json"),
        os.path.join(runtime_dir, "PACKAGE_MANIFEST.json"),
        os.path.join(os.getcwd(), "PACKAGE_MANIFEST.json")
    ]
    expected_entry = EXPECTED_ENTRYPOINT_SHA256
    expected_help = EXPECTED_HELPER_SHA256
    for mp in manifest_paths:
        if os.path.exists(mp):
            try:
                with open(mp, "r") as f:
                    data = json.load(f)
                    for item in data.get("files", []):
                        path = item.get("path", "")
                        if path.endswith("run_f38_cae_diagnostic.py"):
                            expected_entry = item.get("sha256", expected_entry)
                        elif path.endswith("f38_cae_diagnostic_matrix.py"):
                            expected_help = item.get("sha256", expected_help)
            except Exception:
                pass
    return expected_entry, expected_help

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

    if os.getcwd() != out_dir:
        with open(filename, "w") as f:
            json.dump(audit_data, f, indent=2)

    print("PHASE_AUDIT_RECORDED: {} (rc={})".format(phase_name, return_code))

def get_file_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()

def verify_script_hashes(runtime_dir):
    entrypoint_script = os.path.join(runtime_dir, "run_f38_cae_diagnostic.py")
    helper_script = os.path.join(runtime_dir, "f38_cae_diagnostic_matrix.py")

    entrypoint_exists = os.path.exists(entrypoint_script)
    helper_exists = os.path.exists(helper_script)

    if not entrypoint_exists or not helper_exists:
        return False, "missing_script_files", {
            "entrypoint_exists": entrypoint_exists,
            "helper_exists": helper_exists
        }

    entrypoint_sha256 = get_file_sha256(entrypoint_script)
    helper_sha256 = get_file_sha256(helper_script)
    exp_entry, exp_help = load_expected_sha256(runtime_dir)

    entry_matched = True
    if entrypoint_sha256 != EXPECTED_ENTRYPOINT_SHA256 or entrypoint_sha256 != exp_entry:
        entry_matched = False

    helper_matched = True
    if helper_sha256 != EXPECTED_HELPER_SHA256 or helper_sha256 != exp_help:
        helper_matched = False

    metrics = {
        "runtime_dir": runtime_dir,
        "entrypoint_script": entrypoint_script,
        "entrypoint_exists": True,
        "helper_script": helper_script,
        "helper_exists": True,
        "entrypoint_sha256": entrypoint_sha256,
        "expected_entrypoint_sha256": EXPECTED_ENTRYPOINT_SHA256,
        "entrypoint_hash_matched": entry_matched,
        "helper_sha256": helper_sha256,
        "expected_helper_sha256": EXPECTED_HELPER_SHA256,
        "helper_hash_matched": helper_matched
    }

    if not entry_matched:
        return False, "entrypoint_hash_mismatch", metrics
    if not helper_matched:
        return False, "helper_hash_mismatch", metrics

    return True, "ok", metrics

def run_bisection_matrix():
    print("=== F40 Abaqus CAE Bisection Matrix Runner ===")
    runtime_dir = os.environ.get("F40_RUNTIME_DIR", os.getcwd())
    inp_path = os.path.join(runtime_dir, "source_deck.inp")

    # Phase 00: Kernel Startup
    p00_id, p00_name = "P00", "P00_KERNEL_STARTUP"
    try:
        metrics = {
            "sys_version": sys.version,
            "executable": sys.executable,
            "platform": sys.platform
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

    # Phase 02: F38 Entrypoint and Module Probing (No duplicate main() execution)
    p02_id, p02_name = "P02", "P02_MODULE_LOADING"
    try:
        if runtime_dir not in sys.path:
            sys.path.insert(0, runtime_dir)

        file_var_key = '__' + 'file' + '__'
        file_defined = file_var_key in globals()

        valid_hashes, status_msg, hash_metrics = verify_script_hashes(runtime_dir)
        if not valid_hashes:
            raise ValueError("Script hash verification failed in P02: status={}".format(status_msg))

        import f38_cae_diagnostic_matrix
        main_callable = hasattr(f38_cae_diagnostic_matrix, "main") and callable(f38_cae_diagnostic_matrix.main)
        if not main_callable:
            raise AttributeError("f38_cae_diagnostic_matrix does not expose a callable main()")

        metrics = dict(hash_metrics)
        metrics.update({
            "file_global_defined": file_defined,
            "module_imported": True,
            "main_callable": True,
            "main_executed_in_p02": False,
            "sys_path_0": sys.path[0]
        })
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
        metrics = {
            "probe_model_created": "F40_PROBE_OWNERSHIP" in mdb.models,
            "total_models": len(mdb.models)
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
        assy = model.rootAssembly
        assy.regenerate()
        metrics = {
            "assembly_regenerated": True,
            "instances_in_assembly": len(assy.instances)
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

    # Phase 10: Sets/Surfaces Inventory
    p10_id, p10_name = "P10", "P10_SETS_SURFACES_INVENTORY"
    try:
        from abaqus import mdb
        model = mdb.models["F40_MODEL"]
        assy = model.rootAssembly
        sets_count = len(assy.sets)
        surfaces_count = len(assy.surfaces)

        metrics = {
            "assembly_sets": sets_count,
            "assembly_surfaces": surfaces_count
        }
        write_phase_audit(p10_id, p10_name, True, True, 0, None, None, None, "ok", metrics=metrics)
    except Exception as exc:
        write_phase_audit(p10_id, p10_name, True, False, 1, type(exc).__name__, str(exc), traceback.format_exc(), "failed")
        return 1

    # Phase 11: Step Output Probing
    p11_id, p11_name = "P11", "P11_STEP_OUTPUT_PROBING"
    try:
        from abaqus import mdb
        model = mdb.models["F40_MODEL"]
        steps_count = len(model.steps)
        output_requests = len(model.fieldOutputRequests)

        metrics = {
            "steps_count": steps_count,
            "field_output_requests": output_requests
        }
        write_phase_audit(p11_id, p11_name, True, True, 0, None, None, None, "ok", metrics=metrics)
    except Exception as exc:
        write_phase_audit(p11_id, p11_name, True, False, 1, type(exc).__name__, str(exc), traceback.format_exc(), "failed")
        return 1

    print("=== All F40 Bisection Probes Passed Successfully ===")
    return 0

if __name__ == "__main__":
    rc = run_bisection_matrix()
    sys.exit(rc)
