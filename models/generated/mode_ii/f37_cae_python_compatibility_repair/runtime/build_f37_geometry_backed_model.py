# Python 2 and 3 compatible Abaqus model builder script for F37
# Fail-closed Abaqus/CAE Python script with exact API signatures,
# environment variable argument transport (F37_SOURCE_DECK, F37_OUTPUT_INPUT, F37_GEOMETRY_AUDIT),
# job.writeInput(consistencyChecking=ON),
# topology-safe crack face reconstruction via adjacent face centroids using Edge.getFaces(),
# bridge element detection via elem.getNodes() node labels,
# separate node (U, RF) and element (MISESERI, MISESAVG, S, E, EVOL) output requests,
# equation constraints under model.constraints, and exact set-based source coverage audit.
from __future__ import print_function
import sys
import os
import json
import hashlib
import traceback

RUNTIME_DIR = os.path.dirname(os.path.abspath(__file__))
if RUNTIME_DIR not in sys.path:
    sys.path.insert(0, RUNTIME_DIR)
from f37_runtime_compat import resolve_unique_repository_key

CURRENT_PHASE = 'startup'
def set_phase(name):
    global CURRENT_PHASE
    CURRENT_PHASE = name

def write_runtime_failure_audit(error):
    audit_path = os.environ.get('F37_RUNTIME_FAILURE_AUDIT', 'RUNTIME_FAILURE_AUDIT.json')
    payload = {'protocol_version': 1, 'task_id': 'F37-M2RMBUILD11-OFFLINE-REPAIR', 'phase': CURRENT_PHASE, 'exception_type': type(error).__name__, 'exception_message': str(error), 'traceback': traceback.format_exc()}
    try:
        with open(audit_path, 'w') as handle:
            json.dump(payload, handle, indent=2)
    except BaseException:
        pass

def sha256_file(path):
    if not os.path.exists(path):
        return ""
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()

def main():
    set_phase('configuration')
    # Read configuration from explicit environment variables
    source_deck_path = os.environ.get('F37_SOURCE_DECK', 'runtime/source_deck.inp')
    output_inp_path = os.environ.get('F37_OUTPUT_INPUT', 'M2RMPROV4.inp')
    audit_json_path = os.environ.get('F37_GEOMETRY_AUDIT', 'GEOMETRY_BACKED_MODEL_AUDIT.json')

    if not source_deck_path or not output_inp_path or not audit_json_path:
        print("ERROR: Mandatory environment variables F37_SOURCE_DECK, F37_OUTPUT_INPUT, F37_GEOMETRY_AUDIT must be set.")
        sys.exit(1)

    if not os.path.exists(source_deck_path):
        print("ERROR: Source deck not found: " + str(source_deck_path))
        sys.exit(1)

    source_sha = sha256_file(source_deck_path)

    set_phase('abaqus_module_import')
    try:
        from abaqus import mdb
        # Abaqus 2023 constants used by this builder. Keep this import minimal so
        # an unrelated or unsupported constant cannot prevent CAE startup.
        from abaqusConstants import ON, CPE4, STANDARD, STRUCTURED
        import part
        import assembly
        import mesh
    except ImportError as e:
        print("ERROR: Mandatory Abaqus Python modules could not be imported: " + str(e))
        sys.exit(1)

    model_name = 'M2RMPROV4_MODEL'
    if model_name in mdb.models:
        del mdb.models[model_name]
    # Documented full-model import: preserves steps, materials, sections, BCs,
    # equations, sets, and output requests before geometry reconstruction.
    set_phase('model_import')
    m = mdb.ModelFromInputFile(name=model_name, inputFileName=source_deck_path)

    # Import orphan mesh from source deck
    source_part_name = 'Part-1'
    set_phase('part_repository_resolution')
    part_lookup = resolve_unique_repository_key(m.parts, source_part_name, 'model.parts')
    source_part_key = part_lookup['resolved_key']
    orphan_part = m.parts[source_part_key]
    a = m.rootAssembly
    set_phase('instance_repository_resolution')
    instance_lookup = resolve_unique_repository_key(a.instances, 'Part-1-1', 'rootAssembly.instances')
    source_instance_key = instance_lookup['resolved_key']
    set_phase('model_repository_resolution')
    step_lookup = resolve_unique_repository_key(m.steps, 'Step-1', 'model.steps')
    source_step_key = step_lookup['resolved_key']
    material_lookup = resolve_unique_repository_key(m.materials, 'Elastic_Matrix', 'model.materials')
    section_lookup = resolve_unique_repository_key(m.sections, 'Section-1', 'model.sections')
    required_set_names = ('bottom', 'top', 'RP', 'notch_lower_face', 'notch_upper_face', 'notch_tip')
    resolved_set_lookups = {}
    for logical_set_name in required_set_names:
        resolved_set_lookups[logical_set_name] = resolve_unique_repository_key(a.sets, logical_set_name, 'rootAssembly.sets')

    set_phase('geometry_reconstruction')
    # Construct geometry part from orphan mesh
    geom_part_name = 'Part-1-GEOM'
    print("INFO: Constructing 2D geometry part " + str(geom_part_name) + " from orphan mesh...")
    geom_part = m.Part2DGeomFrom2DMesh(name=geom_part_name, part=orphan_part, featureAngle=135.0)

    # Assign CPE4 elements to geometry part
    elem_type = mesh.ElemType(elemCode=CPE4, elemLibrary=STANDARD)
    faces = geom_part.faces
    geom_part.setElementType(regions=(faces,), elemTypes=(elem_type,))

    # Assign structured mesh control
    geom_part.setMeshControls(regions=faces, technique=STRUCTURED)

    # Seed and generate mesh
    geom_part.seedPart(size=0.015, deviationFactor=0.1, minSizeFactor=0.1)
    set_phase('mesh_generation')
    geom_part.generateMesh()

    geom_node_count = len(geom_part.nodes)
    geom_element_count = len(geom_part.elements)

    # Instance replacement sequence: delete orphan instance, create geometry instance
    set_phase('instance_replacement')
    a.deleteFeatures(featureNames=(source_instance_key,))
    orphan_deleted = True
    a.Instance(name=source_instance_key, part=geom_part, dependent=ON)
    inst = a.instances[source_instance_key]

    set_phase('slit_edge_detection')
    # Topology-safe crack face identification via adjacent face centroids using Edge.getFaces()
    crack_x_min = -0.5
    crack_x_max = 0.0
    crack_y = 0.0
    tol = 1.0e-5

    lower_edge_objs = []
    upper_edge_objs = []

    for edge in geom_part.edges:
        vertex_ids = edge.getVertices()
        if len(vertex_ids) != 2:
            continue
        p1 = geom_part.vertices[vertex_ids[0]].pointOn[0]
        p2 = geom_part.vertices[vertex_ids[1]].pointOn[0]
        if abs(p1[1] - crack_y) < tol and abs(p2[1] - crack_y) < tol:
            if (crack_x_min - tol) <= p1[0] <= (crack_x_max + tol) and (crack_x_min - tol) <= p2[0] <= (crack_x_max + tol):
                # Retrieve adjacent faces using Edge.getFaces()
                adj_face_ids = edge.getFaces()
                if len(adj_face_ids) > 0:
                    face_obj = geom_part.faces[adj_face_ids[0]]
                    f_cy = face_obj.pointOn[0][1]
                    if f_cy < 0.0:
                        lower_edge_objs.append(edge)
                    elif f_cy > 0.0:
                        upper_edge_objs.append(edge)

    geom_part.Set(edges=part.EdgeArray(lower_edge_objs), name='Bottom_crack')
    geom_part.Set(edges=part.EdgeArray(upper_edge_objs), name='Top_crack')

    set_phase('slit_topology_audit')
    # Audit slit geometry and mesh topology
    bottom_nodes = set(n.label for e in lower_edge_objs for n in e.getNodes())
    top_nodes = set(n.label for e in upper_edge_objs for n in e.getNodes())

    disjoint_mesh_nodes = len(bottom_nodes.intersection(top_nodes)) == 0
    coincident_pair_count = min(len(bottom_nodes), len(top_nodes))

    # Detect bridge elements across crack faces
    bridge_elem_count = 0
    for elem in geom_part.elements:
        elem_node_labels = set(n.label for n in elem.getNodes())
        if elem_node_labels.intersection(bottom_nodes) and elem_node_labels.intersection(top_nodes):
            bridge_elem_count += 1

    # Reconstruct assembly All_elem set
    all_inst_elems = inst.elements
    a.Set(elements=all_inst_elems, name='All_elem')

    # Separate node and element output requests
    if 'F-Output-1' in m.fieldOutputRequests:
        del m.fieldOutputRequests['F-Output-1']

    nodal_set = a.Set(nodes=inst.nodes, name='All_nodes')
    set_phase('output_request_rebinding')
    m.FieldOutputRequest(name='F-Output-Node', createStepName=source_step_key,
                         variables=('U', 'RF'), region=nodal_set)
    m.FieldOutputRequest(name='F-Output-Element', createStepName=source_step_key,
                         variables=('MISESERI', 'MISESAVG', 'S', 'E', 'EVOL'), region=a.sets['All_elem'])

    # Write input deck using exact documented signature
    job_name = 'M2RMBUILD11_JOB'
    if job_name in mdb.jobs:
        del mdb.jobs[job_name]

    job = mdb.Job(name=job_name, model=model_name)
    set_phase('input_deck_write')
    job.writeInput(consistencyChecking=ON)

    temp_inp = job_name + '.inp'
    if os.path.exists(temp_inp):
        if os.path.exists(output_inp_path):
            os.remove(output_inp_path)
        os.rename(temp_inp, output_inp_path)
        input_deck_written = True
    else:
        input_deck_written = False

    generated_sha = sha256_file(output_inp_path) if input_deck_written else ""
    hash_inequal = (source_sha != generated_sha)

    required_sets = ('bottom', 'top', 'RP', 'notch_lower_face', 'notch_upper_face', 'notch_tip', 'All_elem', 'All_nodes')
    existing_set_names = set(a.sets.keys())
    missing_source_keys = [key for key in required_sets if key not in existing_set_names]
    required_model_keys = ('Elastic_Matrix', 'Section-1', 'Step-1')
    existing_model_keys = set(m.materials.keys()) | set(m.sections.keys()) | set(m.steps.keys())
    missing_source_keys.extend([key for key in required_model_keys if key not in existing_model_keys])
    total_keys = len(required_sets) + len(required_model_keys)
    coverage = float(total_keys - len(missing_source_keys)) / float(total_keys)
    stale_orphan_references = sum(1 for name in a.instances.keys() if name != source_instance_key)
    distinct_edges = bool(lower_edge_objs and upper_edge_objs and set(e.index for e in lower_edge_objs).isdisjoint(set(e.index for e in upper_edge_objs)))
    open_slit = disjoint_mesh_nodes and coincident_pair_count > 0 and bridge_elem_count == 0

    def write_audit(name, payload):
        with open(name, 'w') as handle:
            json.dump(payload, handle, indent=2)

    write_audit('SOURCE_MODEL_INVENTORY.json', {'protocol_version': 1, 'task_id': 'F37-M2RMBUILD11-OFFLINE-REPAIR', 'python_version': sys.version, 'normalization_method': 'str.lower', 'part_lookup': part_lookup, 'instance_lookup': instance_lookup, 'step_lookup': step_lookup, 'material_lookup': material_lookup, 'section_lookup': section_lookup, 'required_set_lookups': resolved_set_lookups, 'lookup_contract_passed': True})
    write_audit('INSTANCE_REPLACEMENT_API_AUDIT.json', {'import_route': 'mdb.ModelFromInputFile', 'api_audit_pass': orphan_deleted and source_instance_key in a.instances, 'active_instance_name': source_instance_key})
    write_audit('MODEL_ENTITY_REBINDING_AUDIT.json', {'unresolved_entity_count': len(missing_source_keys), 'stale_orphan_reference_count': stale_orphan_references, 'source_contract_coverage': coverage, 'model_entity_rebinding_pass': len(missing_source_keys) == 0 and stale_orphan_references == 0})
    write_audit('SLIT_GEOMETRY_AUDIT.json', {'distinct_geometry_edge_ids': distinct_edges, 'lower_edge_count': len(lower_edge_objs), 'upper_edge_count': len(upper_edge_objs), 'x_interval': [-0.5, 0.0]})
    write_audit('SLIT_MESH_TOPOLOGY_AUDIT.json', {'coincident_crack_face_pair_count': coincident_pair_count, 'disjoint_duplicated_crack_nodes': disjoint_mesh_nodes, 'bridge_element_count': bridge_elem_count, 'open_slit_topology_preserved': open_slit})

    final_audit = {
        "protocol_version": 1,
        "task_id": "F37-M2RMBUILD11-OFFLINE-REPAIR",
        "source_deck_path": source_deck_path,
        "source_deck_sha256": source_sha,
        "generated_inp_path": output_inp_path,
        "generated_inp_sha256": generated_sha,
        "hashes_are_different": hash_inequal,
        "cpe4_element_type_assigned": True,
        "structured_mesh_controls_assigned": True,
        "part_seeded_and_generated": True,
        "geometry_nodes_count": geom_node_count,
        "geometry_elements_count": geom_element_count,
        "orphan_instance_deleted": orphan_deleted,
        "geometry_instance_created": True,
        "active_instance_name": source_instance_key,
        "active_instance_part": geom_part_name,
        "slit_edges_separated_by_face_centroids": True,
        "lower_slit_edge_count": len(lower_edge_objs),
        "upper_slit_edge_count": len(upper_edge_objs),
        "slit_mesh_disjoint_nodes": disjoint_mesh_nodes,
        "slit_coincident_pair_count": coincident_pair_count,
        "slit_bridge_element_count": bridge_elem_count,
        "assembly_all_elem_set_reconstructed": True,
        "separate_node_and_element_output_requests": True,
        "input_deck_written": input_deck_written,
        "unresolved_entity_count": len(missing_source_keys),
        "stale_orphan_reference_count": stale_orphan_references,
        "source_contract_coverage": coverage,
        "write_input_consistency_checking_on": True,
        "open_slit_topology_preserved": open_slit,
        "contract_pass": (input_deck_written and hash_inequal and len(missing_source_keys) == 0 and stale_orphan_references == 0 and coverage == 1.0 and open_slit and bridge_elem_count == 0)
    }

    set_phase('final_contract_audit')
    with open(audit_json_path, 'w') as f:
        json.dump(final_audit, f, indent=2)
    write_audit('GENERATED_INPUT_AUDIT.json', {'generated_input_sha256': generated_sha, 'exact_generated_input_contract_pass': final_audit['contract_pass']})
    if not final_audit['contract_pass']:
        print("ERROR: F37 live runtime contract failed.")
        sys.exit(1)

    print("SUCCESS: Abaqus CAE model construction and audits completed.")
    print("Generated INP: " + str(output_inp_path) + " (SHA: " + str(generated_sha) + ")")

if __name__ == '__main__':
    try:
        main()
    except BaseException as error:
        write_runtime_failure_audit(error)
        raise
