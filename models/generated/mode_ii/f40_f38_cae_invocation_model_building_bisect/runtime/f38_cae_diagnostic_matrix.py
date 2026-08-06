from __future__ import print_function
import os
import sys
import json
import datetime
import traceback
import hashlib

PHASE_DEPENDENCIES = {
    'repository_inventory': ['model_import'],
    'repository_resolution': ['model_import'],
    'element_type_assignment': ['geometry_conversion'],
    'mesh_control_assignment': ['geometry_conversion'],
    'instance_replacement': ['assembly_feature_inventory'],
    'crack_edge_detection': ['crack_edge_method_inventory'],
    'crack_mesh_topology': ['crack_edge_method_inventory'],
    'output_request_rebinding': ['output_variable_probe'],
    'generated_input_presence': ['input_write']
}

def get_hash(filepath):
    if not os.path.exists(filepath):
        return None
    h = hashlib.sha256()
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(65536), b''):
            h.update(chunk)
    return h.hexdigest()

def write_matrix(matrix, matrix_path=None):
    if matrix_path is None:
        matrix_path = os.environ.get('F38_DIAGNOSTIC_MATRIX', 'CAE_PHASE_DIAGNOSTIC_MATRIX.json').strip()
    try:
        with open(matrix_path, 'w') as f:
            json.dump(matrix, f, indent=2)
    except Exception as e:
        print("Error writing diagnostic matrix:", str(e))

def run_phase(matrix, phase_name, function, context, passed_phases, matrix_path=None):
    prereqs = PHASE_DEPENDENCIES.get(phase_name, [])
    blocked_by = [p for p in prereqs if not passed_phases.get(p, False)]

    if blocked_by:
        record = {
            'phase': phase_name,
            'attempted': False,
            'passed': False,
            'dependency_blocked': True,
            'blocked_by': blocked_by,
            'exception_type': None,
            'exception_message': None,
            'traceback': None,
            'started_at': datetime.datetime.now().isoformat(),
            'finished_at': datetime.datetime.now().isoformat(),
            'observations': {},
            'artifacts_written': []
        }
        matrix['phases'].append(record)
        write_matrix(matrix, matrix_path)
        return False

    record = {
        'phase': phase_name,
        'attempted': True,
        'passed': False,
        'dependency_blocked': False,
        'blocked_by': [],
        'exception_type': None,
        'exception_message': None,
        'traceback': None,
        'started_at': datetime.datetime.now().isoformat(),
        'finished_at': None,
        'observations': {},
        'artifacts_written': []
    }

    try:
        observations = function(context)
        record['observations'] = observations or {}
        record['passed'] = True
    except BaseException as error:
        record['exception_type'] = type(error).__name__
        record['exception_message'] = str(error)
        record['traceback'] = traceback.format_exc()

    record['finished_at'] = datetime.datetime.now().isoformat()
    matrix['phases'].append(record)
    write_matrix(matrix, matrix_path)
    return record['passed']

def import_fresh_model(mdb, source_deck, model_name):
    if model_name in mdb.models:
        del mdb.models[model_name]
    return mdb.ModelFromInputFile(
        name=model_name,
        inputFileName=source_deck
    )

def get_first_analysis_step(model):
    step_names = [
        str(name) for name in model.steps.keys()
        if str(name).lower() != "initial"
    ]
    if not step_names:
        raise RuntimeError("No non-Initial analysis step exists")
    return model.steps[step_names[0]]

# Phase 1
def phase_bootstrap(ctx):
    runtime_dir = os.environ.get('F38_RUNTIME_DIR', '').strip()
    return {
        'runtime_dir': runtime_dir,
        'sys_path': sys.path[:5],
        'python_version': sys.version
    }

# Phase 2
def phase_abaqus_module_import(ctx):
    try:
        from abaqus import mdb
    except ImportError:
        import mdb as mdb_module
        mdb = mdb_module.mdb

    import abaqusConstants as ac
    import part
    import mesh
    import assembly
    import step
    import load
    ctx['mdb'] = mdb
    ctx['ac'] = ac
    ctx['mesh'] = mesh
    return {
        'mdb_available': True,
        'mesh_imported': True,
        'constants_imported': ['ON', 'CPE4', 'STANDARD', 'STRUCTURED']
    }

# Phase 3
def phase_source_deck_access(ctx):
    source_deck = os.environ.get('F38_SOURCE_DECK', '').strip()
    if not source_deck:
        source_deck = os.path.join(os.environ.get('F38_RUNTIME_DIR', ''), 'source_deck.inp')
    source_deck = os.path.abspath(source_deck)
    exists = os.path.isfile(source_deck)
    size = os.path.getsize(source_deck) if exists else 0
    sha256 = get_hash(source_deck) if exists else None
    ctx['source_deck'] = source_deck
    if not exists:
        raise RuntimeError('Source deck file does not exist: {0}'.format(source_deck))
    return {
        'source_deck_path': source_deck,
        'exists': exists,
        'size_bytes': size,
        'sha256': sha256
    }

# Phase 4
def phase_model_import(ctx):
    mdb = ctx['mdb']
    source_deck = ctx['source_deck']
    model = import_fresh_model(mdb, source_deck, 'F38_IMPORT_PROBE')
    ctx['import_model'] = model
    return {
        'imported_model_name': model.name,
        'models_in_mdb': list(mdb.models.keys())
    }

# Phase 5
def phase_repository_inventory(ctx):
    model = ctx['import_model']
    assembly = model.rootAssembly
    return {
        'parts': [str(k) for k in model.parts.keys()],
        'steps': [str(k) for k in model.steps.keys()],
        'materials': [str(k) for k in model.materials.keys()],
        'sections': [str(k) for k in model.sections.keys()],
        'instances': [str(k) for k in assembly.instances.keys()],
        'features': [str(k) for k in assembly.features.keys()],
        'sets': [str(k) for k in assembly.sets.keys()]
    }

# Phase 6
def phase_repository_resolution(ctx):
    model = ctx['import_model']
    assembly = model.rootAssembly
    part_keys = list(model.parts.keys())
    instance_keys = list(assembly.instances.keys())
    feature_keys = list(assembly.features.keys())

    part_name = str(part_keys[0]) if part_keys else None
    instance_name = str(instance_keys[0]) if instance_keys else None

    mapping = {}
    for fk in feature_keys:
        mapping[str(fk)] = (str(fk) in [str(ik) for ik in instance_keys])

    return {
        'resolved_part_name': part_name,
        'resolved_instance_name': instance_name,
        'feature_to_instance_match': mapping
    }

# Phase 7
def phase_geometry_conversion(ctx):
    mdb = ctx['mdb']
    source_deck = ctx['source_deck']
    model = import_fresh_model(mdb, source_deck, 'F38_GEOMETRY_PROBE')
    ctx['geom_model'] = model
    part_keys = list(model.parts.keys())
    source_part = model.parts[part_keys[0]]

    geom_part = None
    model_api_passed = False
    part_api_passed = False
    model_api_error = None
    part_api_error = None

    # Model-level conversion API probe (Primary)
    try:
        if hasattr(model, 'Part2DGeomFrom2DMesh'):
            geom_part = model.Part2DGeomFrom2DMesh(name='GeomPartModelApi', part=source_part, featureAngle=45.0)
            model_api_passed = True
        else:
            model_api_error = "model has no Part2DGeomFrom2DMesh attribute"
    except Exception as e:
        model_api_error = str(e)

    # Part-level conversion API probe (Alternative)
    try:
        if hasattr(source_part, 'Part2DGeomFrom2DMesh'):
            p_geom = source_part.Part2DGeomFrom2DMesh(name='GeomPartPartApi', featureAngle=45.0)
            part_api_passed = True
            if geom_part is None:
                geom_part = p_geom
        else:
            part_api_error = "source_part has no Part2DGeomFrom2DMesh attribute"
    except Exception as e:
        part_api_error = str(e)

    if geom_part is None:
        raise RuntimeError("Both model-level and part-level Part2DGeomFrom2DMesh probes failed. Model error: {0}; Part error: {1}".format(model_api_error, part_api_error))

    ctx['geom_part'] = geom_part

    face_count = len(geom_part.faces) if hasattr(geom_part, 'faces') else 0
    vertex_count = len(geom_part.vertices) if hasattr(geom_part, 'vertices') else 0

    if face_count == 0 or vertex_count == 0:
        raise RuntimeError("geometry_conversion produced zero faces ({0}) or zero vertices ({1})".format(face_count, vertex_count))

    capabilities = {
        'object_type': str(type(geom_part)),
        'has_getVertices': hasattr(geom_part, 'getVertices'),
        'has_getFaces': hasattr(geom_part, 'getFaces'),
        'has_getNodes': hasattr(geom_part, 'getNodes'),
        'has_pointOn': hasattr(geom_part, 'pointOn')
    }

    return {
        'model_api_passed': model_api_passed,
        'model_api_error': model_api_error,
        'part_api_passed': part_api_passed,
        'part_api_error': part_api_error,
        'geom_part_name': str(geom_part.name),
        'face_count': face_count,
        'vertex_count': vertex_count,
        'capabilities': capabilities
    }

# Phase 8
def phase_element_type_assignment(ctx):
    geom_part = ctx.get('geom_part')
    ac = ctx['ac']
    mesh_module = ctx.get('mesh')
    if mesh_module is None:
        import mesh as mesh_module
    if not geom_part:
        raise RuntimeError('geom_part unavailable for element type assignment')

    elem_type = mesh_module.ElemType(elemCode=ac.CPE4, elemLibrary=ac.STANDARD)
    geom_part.setElementType(regions=(geom_part.faces,), elemTypes=(elem_type,))
    return {
        'element_type_assigned': True,
        'elem_code': 'CPE4',
        'elem_library': 'STANDARD'
    }

# Phase 9
def phase_mesh_control_assignment(ctx):
    geom_part = ctx.get('geom_part')
    ac = ctx['ac']
    if not geom_part:
        raise RuntimeError('geom_part unavailable for mesh control assignment')

    geom_part.setMeshControls(regions=geom_part.faces, technique=ac.STRUCTURED)
    return {
        'mesh_controls_assigned': True,
        'technique': 'STRUCTURED'
    }

# Phase 10
def phase_mesh_generation(ctx):
    mdb = ctx['mdb']
    source_deck = ctx['source_deck']
    ac = ctx['ac']
    mesh_module = ctx.get('mesh')
    if mesh_module is None:
        import mesh as mesh_module
    model = import_fresh_model(mdb, source_deck, 'F38_MESH_PROBE')
    source_part = model.parts[list(model.parts.keys())[0]]
    if hasattr(model, 'Part2DGeomFrom2DMesh'):
        geom_part = model.Part2DGeomFrom2DMesh(name='GeomPartMesh', part=source_part, featureAngle=45.0)
    else:
        geom_part = source_part.Part2DGeomFrom2DMesh(name='GeomPartMesh', featureAngle=45.0)
    geom_part.setElementType(regions=(geom_part.faces,), elemTypes=(mesh_module.ElemType(elemCode=ac.CPE4, elemLibrary=ac.STANDARD),))
    geom_part.setMeshControls(regions=geom_part.faces, technique=ac.STRUCTURED)
    geom_part.seedPart(size=0.01)
    geom_part.generateMesh()
    ctx['mesh_geom_part'] = geom_part

    nodes_count = len(geom_part.nodes) if hasattr(geom_part, 'nodes') else 0
    elements_count = len(geom_part.elements) if hasattr(geom_part, 'elements') else 0

    if nodes_count == 0 or elements_count == 0:
        raise RuntimeError("mesh_generation produced zero nodes ({0}) or zero elements ({1})".format(nodes_count, elements_count))

    return {
        'mesh_nodes_count': nodes_count,
        'mesh_elements_count': elements_count
    }

# Phase 11
def phase_assembly_feature_inventory(ctx):
    mdb = ctx['mdb']
    source_deck = ctx['source_deck']
    model = import_fresh_model(mdb, source_deck, 'F38_INSTANCE_PROBE')
    ctx['inst_model'] = model
    assembly = model.rootAssembly
    features = [str(f) for f in assembly.features.keys()]
    instances = [str(i) for i in assembly.instances.keys()]
    return {
        'features_list': features,
        'instances_list': instances,
        'feature_instance_diff': list(set(features) - set(instances))
    }

# Phase 12
def phase_instance_replacement(ctx):
    mdb = ctx['mdb']
    source_deck = ctx['source_deck']
    ac = ctx['ac']
    model = ctx.get('inst_model')
    if not model:
        model = import_fresh_model(mdb, source_deck, 'F38_INSTANCE_PROBE')
        ctx['inst_model'] = model

    source_part = model.parts[list(model.parts.keys())[0]]
    if hasattr(model, 'Part2DGeomFrom2DMesh'):
        geom_part = model.Part2DGeomFrom2DMesh(name='GeomPartInst', part=source_part, featureAngle=45.0)
    else:
        geom_part = source_part.Part2DGeomFrom2DMesh(name='GeomPartInst', featureAngle=45.0)

    assembly = model.rootAssembly
    feature_names = tuple(assembly.features.keys())
    if feature_names:
        assembly.deleteFeatures(featureNames=feature_names)

    new_inst = assembly.Instance(name='Part-1-1', part=geom_part, dependent=ac.ON)
    assembly.regenerate()
    ctx['inst_geom_part'] = geom_part
    return {
        'instance_replaced': True,
        'new_instance_name': str(new_inst.name),
        'instances_in_assembly': [str(k) for k in assembly.instances.keys()]
    }

# Phase 13
def phase_crack_edge_method_inventory(ctx):
    mdb = ctx['mdb']
    source_deck = ctx['source_deck']
    model = import_fresh_model(mdb, source_deck, 'F38_CRACK_PROBE')
    ctx['crack_model'] = model
    source_part = model.parts[list(model.parts.keys())[0]]
    if hasattr(model, 'Part2DGeomFrom2DMesh'):
        geom_part = model.Part2DGeomFrom2DMesh(name='GeomPartCrack', part=source_part, featureAngle=45.0)
    else:
        geom_part = source_part.Part2DGeomFrom2DMesh(name='GeomPartCrack', featureAngle=45.0)
    ctx['crack_geom_part'] = geom_part

    edges = geom_part.edges
    faces = geom_part.faces
    sample_edge = edges[0] if edges else None

    capabilities = {
        'edge_has_getFaces': hasattr(sample_edge, 'getFaces') if sample_edge else False,
        'edge_has_getVertices': hasattr(sample_edge, 'getVertices') if sample_edge else False,
        'edge_has_pointOn': hasattr(sample_edge, 'pointOn') if sample_edge else False,
        'face_count': len(faces)
    }
    return capabilities

# Phase 14
def phase_crack_edge_detection(ctx):
    geom_part = ctx.get('crack_geom_part')
    if not geom_part:
        raise RuntimeError('crack_geom_part unavailable')

    top_faces = 0
    bottom_faces = 0
    total_faces = len(geom_part.faces)
    if total_faces == 0:
        raise RuntimeError('crack_edge_detection found zero faces')

    for face in geom_part.faces:
        if hasattr(face, 'pointOn'):
            pt = face.pointOn[0]
            if pt[1] >= 0:
                top_faces += 1
            else:
                bottom_faces += 1

    return {
        'top_faces_count': top_faces,
        'bottom_faces_count': bottom_faces,
        'total_faces': total_faces
    }

# Phase 15
def phase_crack_mesh_topology(ctx):
    geom_part = ctx.get('crack_geom_part')
    if not geom_part:
        raise RuntimeError('crack_geom_part unavailable')

    nodes = geom_part.nodes if hasattr(geom_part, 'nodes') and geom_part.nodes else []
    elements = geom_part.elements if hasattr(geom_part, 'elements') and geom_part.elements else []

    lower_node_labels = []
    upper_node_labels = []
    lower_coords = {}
    upper_coords = {}

    if hasattr(geom_part, 'sets') and 'notch_lower_face' in geom_part.sets and 'notch_upper_face' in geom_part.sets:
        lower_nodes = geom_part.sets['notch_lower_face'].nodes
        upper_nodes = geom_part.sets['notch_upper_face'].nodes
        lower_node_labels = [n.label for n in lower_nodes]
        upper_node_labels = [n.label for n in upper_nodes]
        lower_coords = {n.label: n.coordinates for n in lower_nodes}
        upper_coords = {n.label: n.coordinates for n in upper_nodes}
    else:
        for n in nodes:
            x, y, z = n.coordinates
            if x <= 0.001:
                if y <= 0 and y >= -0.05:
                    lower_node_labels.append(n.label)
                    lower_coords[n.label] = (x, y, z)
                elif y >= 0 and y <= 0.05:
                    upper_node_labels.append(n.label)
                    upper_coords[n.label] = (x, y, z)

    if len(lower_node_labels) == 0 or len(upper_node_labels) == 0:
        raise RuntimeError("crack_mesh_topology upper/lower node sets are empty (lower: {0}, upper: {1})".format(len(lower_node_labels), len(upper_node_labels)))

    lower_set = set(lower_node_labels)
    upper_set = set(upper_node_labels)
    intersection_count = len(lower_set.intersection(upper_set))
    disjoint_node_sets = (intersection_count == 0)

    if not disjoint_node_sets:
        raise RuntimeError("crack_mesh_topology node sets are not disjoint (intersection count: {0})".format(intersection_count))

    coincident_pair_count = 0
    for l_label, l_c in lower_coords.items():
        for u_label, u_c in upper_coords.items():
            if abs(l_c[0] - u_c[0]) < 1e-5 and abs(l_c[1] - u_c[1]) < 1e-5:
                coincident_pair_count += 1
                break

    if coincident_pair_count == 0:
        raise RuntimeError("crack_mesh_topology coincident pair count is zero")

    bridge_elem_count = 0
    for elem in elements:
        n_labels = set()
        if hasattr(elem, 'getNodes'):
            n_labels = set(n.label for n in elem.getNodes())
        elif hasattr(elem, 'connectivity'):
            n_labels = set(elem.connectivity)
        if len(n_labels.intersection(lower_set)) > 0 and len(n_labels.intersection(upper_set)) > 0:
            bridge_elem_count += 1

    if bridge_elem_count != 0:
        raise RuntimeError("crack_mesh_topology bridge element count is non-zero ({0})".format(bridge_elem_count))

    return {
        'lower_node_labels_count': len(lower_node_labels),
        'upper_node_labels_count': len(upper_node_labels),
        'intersection_count': intersection_count,
        'disjoint_node_sets': disjoint_node_sets,
        'coincident_node_pairs_count': coincident_pair_count,
        'bridge_element_count': bridge_elem_count
    }

# Phase 16
def phase_assembly_set_inventory(ctx):
    model = ctx.get('crack_model')
    if not model:
        raise RuntimeError('crack_model unavailable')

    assembly = model.rootAssembly
    sets_data = {}
    for name, s in assembly.sets.items():
        sets_data[str(name)] = {
            'exists': True,
            'node_count': len(s.nodes) if hasattr(s, 'nodes') and s.nodes else 0,
            'element_count': len(s.elements) if hasattr(s, 'elements') and s.elements else 0,
            'edge_count': len(s.edges) if hasattr(s, 'edges') and s.edges else 0,
            'face_count': len(s.faces) if hasattr(s, 'faces') and s.faces else 0
        }

    return {
        'inventoried_sets_count': len(sets_data),
        'set_details': sets_data,
        'is_observation_only_probe': True
    }

# Phase 17
def phase_output_variable_probe(ctx):
    mdb = ctx['mdb']
    source_deck = ctx['source_deck']
    model = import_fresh_model(mdb, source_deck, 'F38_OUTPUT_PROBE')
    ctx['output_model'] = model

    step = get_first_analysis_step(model)
    candidate_vars = ['U', 'RF', 'S', 'E', 'EVOL', 'MISESERI', 'MISESAVG']

    accepted = []
    rejected = []

    for var in candidate_vars:
        req_name = 'PROBE_' + var
        try:
            if req_name in model.fieldOutputRequests:
                del model.fieldOutputRequests[req_name]
            model.FieldOutputRequest(name=req_name, createStepName=step.name, variables=(var,))
            accepted.append(var)
        except Exception as e:
            rejected.append({'variable': var, 'error': str(e)})

    return {
        'accepted_variables': accepted,
        'rejected_variables': rejected,
        'probe_step_name': step.name
    }

# Phase 18
def phase_output_request_rebinding(ctx):
    model = ctx.get('output_model')
    if not model:
        raise RuntimeError('output_model unavailable')

    step = get_first_analysis_step(model)
    model.FieldOutputRequest(
        name='F38_REBOUND_OUTPUT',
        createStepName=step.name,
        variables=('U', 'RF')
    )
    return {
        'output_request_rebound': True,
        'create_step_name': step.name
    }

# Phase 19
def phase_input_write(ctx):
    mdb = ctx['mdb']
    source_deck = ctx['source_deck']
    ac = ctx['ac']
    model = import_fresh_model(mdb, source_deck, 'F38_WRITE_INPUT_PROBE')

    job_name = 'F38_TMP_JOB'
    if job_name in mdb.jobs:
        del mdb.jobs[job_name]

    job = mdb.Job(name=job_name, model=model.name)
    job.writeInput(consistencyChecking=ac.ON)

    tmp_input = job_name + '.inp'
    tmp_exists = os.path.isfile(tmp_input)

    output_input = os.environ.get('F38_OUTPUT_INPUT', 'generated_model.inp').strip()
    output_input = os.path.abspath(output_input)

    if tmp_exists:
        if os.path.exists(output_input):
            os.remove(output_input)
        os.rename(tmp_input, output_input)

    ctx['output_input'] = output_input

    return {
        'job_creation_passed': True,
        'write_input_invoked': True,
        'temporary_input_path': tmp_input,
        'temporary_input_exists': tmp_exists,
        'final_rename_passed': os.path.isfile(output_input)
    }

# Phase 20
def phase_generated_input_presence(ctx):
    output_input = ctx.get('output_input')
    if not output_input:
        output_input = os.environ.get('F38_OUTPUT_INPUT', 'generated_model.inp').strip()
    output_input = os.path.abspath(output_input)

    exists = os.path.isfile(output_input)
    size = os.path.getsize(output_input) if exists else 0
    sha256 = get_hash(output_input) if exists else None

    if not exists or size == 0:
        raise RuntimeError("generated_input_presence file missing or zero bytes")

    return {
        'generated_input_exists': exists,
        'generated_size': size,
        'generated_sha256': sha256
    }

def main():
    matrix_path = os.environ.get('F38_DIAGNOSTIC_MATRIX', 'CAE_PHASE_DIAGNOSTIC_MATRIX.json').strip()
    matrix = {
        'protocol_version': 1,
        'package': 'f38_comprehensive_cae_diagnostic_matrix',
        'job_name': 'M2RMDIAG1',
        'started_at': datetime.datetime.now().isoformat(),
        'finished_at': None,
        'overall_passed': False,
        'phases': []
    }

    ctx = {}
    phases = [
        ('bootstrap', phase_bootstrap),
        ('abaqus_module_import', phase_abaqus_module_import),
        ('source_deck_access', phase_source_deck_access),
        ('model_import', phase_model_import),
        ('repository_inventory', phase_repository_inventory),
        ('repository_resolution', phase_repository_resolution),
        ('geometry_conversion', phase_geometry_conversion),
        ('element_type_assignment', phase_element_type_assignment),
        ('mesh_control_assignment', phase_mesh_control_assignment),
        ('mesh_generation', phase_mesh_generation),
        ('assembly_feature_inventory', phase_assembly_feature_inventory),
        ('instance_replacement', phase_instance_replacement),
        ('crack_edge_method_inventory', phase_crack_edge_method_inventory),
        ('crack_edge_detection', phase_crack_edge_detection),
        ('crack_mesh_topology', phase_crack_mesh_topology),
        ('assembly_set_inventory', phase_assembly_set_inventory),
        ('output_variable_probe', phase_output_variable_probe),
        ('output_request_rebinding', phase_output_request_rebinding),
        ('input_write', phase_input_write),
        ('generated_input_presence', phase_generated_input_presence)
    ]

    passed_phases = {}
    all_passed = True

    for phase_name, func in phases:
        passed = run_phase(matrix, phase_name, func, ctx, passed_phases, matrix_path)
        passed_phases[phase_name] = passed
        if not passed:
            all_passed = False

    matrix['overall_passed'] = all_passed
    matrix['finished_at'] = datetime.datetime.now().isoformat()
    write_matrix(matrix, matrix_path)
    print("F38 CAE Diagnostic Matrix execution complete. Overall passed:", all_passed)

if __name__ == '__main__':
    main()
