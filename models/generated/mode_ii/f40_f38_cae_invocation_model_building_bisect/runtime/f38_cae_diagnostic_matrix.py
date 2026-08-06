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
    'usable_geometry_validation': ['geometry_conversion_observation'],
    'element_type_assignment': ['usable_geometry_validation'],
    'mesh_control_assignment': ['usable_geometry_validation'],
    'mesh_generation': ['usable_geometry_validation'],
    'assembly_feature_inventory': ['model_import'],
    'instance_replacement': ['usable_geometry_validation', 'assembly_feature_inventory'],
    'crack_edge_method_inventory': ['usable_geometry_validation'],
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

# Helper to execute a single conversion probe in a fresh model safely
def run_single_conversion_probe(mdb, source_deck, model_name, part_key, feature_angle, merge_crack_nodes=False):
    probe_record = {
        'model_name': model_name,
        'feature_angle': feature_angle,
        'merge_crack_nodes_requested': merge_crack_nodes,
        'attempted': True,
        'completed': False,
        'face_count': 0,
        'vertex_count': 0,
        'edge_count': 0,
        'coincident_pairs_before': 0,
        'coincident_pairs_after': 0,
        'node_reduction': 0,
        'exception_type': None,
        'exception_message': None
    }
    try:
        model = import_fresh_model(mdb, source_deck, model_name)
        source_part = model.parts[list(model.parts.keys())[0]]

        if merge_crack_nodes:
            # 1. Detect coincident coordinate groups along crack y=0 (x in [0.0, 0.5])
            crack_nodes = [n for n in source_part.nodes if abs(n.coordinates[1]) < 1e-5 and n.coordinates[0] <= 0.5 + 1e-5]
            coord_groups = {}
            for n in crack_nodes:
                pt_key = (round(n.coordinates[0], 5), round(n.coordinates[1], 5))
                coord_groups.setdefault(pt_key, []).append(n)

            duplicate_pairs = {k: v for k, v in coord_groups.items() if len(v) > 1}
            probe_record['coincident_pairs_before'] = len(duplicate_pairs)

            if len(duplicate_pairs) != 15:
                raise RuntimeError("Control A fail-closed check failed: expected exactly 15 coincident node pairs along crack, found {0}".format(len(duplicate_pairs)))

            if not hasattr(source_part, 'mergeNodes'):
                raise RuntimeError("Control A fail-closed check failed: source_part lacks mergeNodes method")

            nodes_before = len(source_part.nodes)
            source_part.mergeNodes(nodes=crack_nodes, tolerance=1e-4)
            nodes_after = len(source_part.nodes)
            probe_record['node_reduction'] = nodes_before - nodes_after

            if (nodes_before - nodes_after) != 15:
                raise RuntimeError("Control A fail-closed check failed: node count reduction expected 15, actual {0}".format(nodes_before - nodes_after))

            rem_nodes = [n for n in source_part.nodes if abs(n.coordinates[1]) < 1e-5 and n.coordinates[0] <= 0.5 + 1e-5]
            rem_groups = {}
            for n in rem_nodes:
                pt_key = (round(n.coordinates[0], 5), round(n.coordinates[1], 5))
                rem_groups.setdefault(pt_key, []).append(n)
            rem_pairs = {k: v for k, v in rem_groups.items() if len(v) > 1}
            probe_record['coincident_pairs_after'] = len(rem_pairs)

            if len(rem_pairs) != 0:
                raise RuntimeError("Control A fail-closed check failed: remaining coincident pairs expected 0, actual {0}".format(len(rem_pairs)))

        model.Part2DGeomFrom2DMesh(name=part_key, part=source_part, featureAngle=feature_angle)
        geom_part = model.parts[part_key]

        probe_record['face_count'] = len(geom_part.faces) if hasattr(geom_part, 'faces') else 0
        probe_record['vertex_count'] = len(geom_part.vertices) if hasattr(geom_part, 'vertices') else 0
        probe_record['edge_count'] = len(geom_part.edges) if hasattr(geom_part, 'edges') else 0
        probe_record['completed'] = True
    except Exception as e:
        probe_record['exception_type'] = type(e).__name__
        probe_record['exception_message'] = str(e)

    return probe_record

# Phase 7: API Invocation Observation
def phase_geometry_conversion_observation(ctx):
    mdb = ctx['mdb']
    source_deck = ctx['source_deck']
    model = import_fresh_model(mdb, source_deck, 'F38_GEOMETRY_PROBE')
    ctx['geom_model'] = model
    part_keys = list(model.parts.keys())
    source_part = model.parts[part_keys[0]]

    # Source-part topology metrics before conversion
    source_metrics = {
        'object_type': str(type(source_part)),
        'node_count': len(source_part.nodes) if hasattr(source_part, 'nodes') else 0,
        'element_count': len(source_part.elements) if hasattr(source_part, 'elements') else 0,
        'geometry_face_count': len(source_part.faces) if hasattr(source_part, 'faces') else 0,
        'geometry_edge_count': len(source_part.edges) if hasattr(source_part, 'edges') else 0,
        'geometry_vertex_count': len(source_part.vertices) if hasattr(source_part, 'vertices') else 0,
        'is_meshed': getattr(source_part, 'isMeshed', None),
        'space': str(getattr(source_part, 'space', None)),
        'part_type': str(getattr(source_part, 'type', None)),
    }

    geom_part = None
    model_api_passed = False
    model_api_error = None

    # Model-level conversion API call only (Part2DGeomFrom2DMesh is a model-level method)
    try:
        if hasattr(model, 'Part2DGeomFrom2DMesh'):
            model.Part2DGeomFrom2DMesh(name='GeomPartModelApi', part=source_part, featureAngle=45.0)
            geom_part = model.parts['GeomPartModelApi']
            model_api_passed = True
        else:
            model_api_error = "model has no Part2DGeomFrom2DMesh attribute"
    except Exception as e:
        model_api_error = str(e)

    if geom_part is None:
        raise RuntimeError("Model-level Part2DGeomFrom2DMesh probe failed: {0}".format(model_api_error))

    ctx['geom_part'] = geom_part

    face_count = len(geom_part.faces) if hasattr(geom_part, 'faces') else 0
    vertex_count = len(geom_part.vertices) if hasattr(geom_part, 'vertices') else 0
    edge_count = len(geom_part.edges) if hasattr(geom_part, 'edges') else 0
    feature_keys = [str(k) for k in geom_part.features.keys()] if hasattr(geom_part, 'features') else []
    is_meshed = getattr(geom_part, 'isMeshed', None)
    is_wire_only = (edge_count > 0 and face_count == 0)

    capabilities = {
        'object_type': str(type(geom_part)),
        'has_getVertices': hasattr(geom_part, 'getVertices'),
        'has_getFaces': hasattr(geom_part, 'getFaces'),
        'has_getNodes': hasattr(geom_part, 'getNodes'),
        'has_pointOn': hasattr(geom_part, 'pointOn')
    }

    # Controlled conversion probes executed in separate fresh models & separate try/except blocks
    control_a = run_single_conversion_probe(mdb, source_deck, 'F40_CTRL_A_UNCRACKED', 'GeomCtrlA', 45.0, merge_crack_nodes=True)
    control_b = run_single_conversion_probe(mdb, source_deck, 'F40_CTRL_B_CRACKED', 'GeomCtrlB', 45.0, merge_crack_nodes=False)

    angle_probes = {}
    for fa in [15.0, 30.0, 45.0, 60.0, 90.0]:
        fa_key = 'angle_{0}deg'.format(int(fa))
        angle_probes[fa_key] = run_single_conversion_probe(
            mdb, source_deck, 'F40_ANGLE_{0}'.format(int(fa)), 'GeomAngle_{0}'.format(int(fa)), fa, merge_crack_nodes=False
        )

    controlled_conversion_probes = {
        'control_a': control_a,
        'control_b': control_b,
        'angle_probes': angle_probes,
        'coincident_crack_nodes_confirmed_root_cause': (control_a.get('face_count', 0) > 0 and control_b.get('face_count', 0) == 0)
    }

    # API Observation Record
    api_observation = {
        'source_metrics': source_metrics,
        'model_api_passed': model_api_passed,
        'model_api_error': model_api_error,
        'part_api_passed': False,
        'part_api_error': "Part-level fallback probe cleanly removed per F40 v15R1 specification",
        'created_repository_key': 'GeomPartModelApi',
        'returned_object_type': str(type(geom_part)),
        'geom_part_name': str(geom_part.name),
        'face_count': face_count,
        'vertex_count': vertex_count,
        'edge_count': edge_count,
        'feature_keys': feature_keys,
        'is_meshed': is_meshed,
        'is_wire_only': is_wire_only,
        'capabilities': capabilities,
        'controlled_conversion_probes': controlled_conversion_probes
    }
    ctx['geometry_conversion_api_observation'] = api_observation
    return api_observation

# Phase 8: Usable Geometry Gate Validation
def phase_usable_geometry_validation(ctx):
    geom_part = ctx.get('geom_part')
    if not geom_part:
        raise RuntimeError("geom_part unavailable for usable_geometry_validation")

    obs = ctx.get('geometry_conversion_api_observation', {})
    face_count = obs.get('face_count', len(geom_part.faces) if hasattr(geom_part, 'faces') else 0)
    vertex_count = obs.get('vertex_count', len(geom_part.vertices) if hasattr(geom_part, 'vertices') else 0)
    is_wire_only = obs.get('is_wire_only', False)

    if face_count == 0 or vertex_count == 0 or is_wire_only:
        raise RuntimeError("usable_geometry_validation failed: geometry conversion produced zero usable faces ({0}), zero vertices ({1}), or wire-only geometry".format(face_count, vertex_count))

    return {
        'usable_geometry_valid': True,
        'face_count': face_count,
        'vertex_count': vertex_count,
        'is_wire_only': False
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
    model.Part2DGeomFrom2DMesh(name='GeomPartMesh', part=source_part, featureAngle=45.0)
    geom_part = model.parts['GeomPartMesh']

    if len(geom_part.faces) == 0:
        raise RuntimeError("mesh_generation blocked: Part2DGeomFrom2DMesh returned a repository part with zero geometric faces")
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
    model.Part2DGeomFrom2DMesh(name='GeomPartInst', part=source_part, featureAngle=45.0)
    geom_part = model.parts['GeomPartInst']
    if len(geom_part.faces) == 0:
        raise RuntimeError("instance_replacement blocked: Part2DGeomFrom2DMesh returned zero geometric faces")

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
    model.Part2DGeomFrom2DMesh(name='GeomPartCrack', part=source_part, featureAngle=45.0)
    geom_part = model.parts['GeomPartCrack']
    if len(geom_part.faces) == 0:
        raise RuntimeError("crack_edge_method_inventory blocked: Part2DGeomFrom2DMesh returned zero geometric faces")
    ctx['crack_geom_part'] = geom_part

    edges = geom_part.edges if hasattr(geom_part, 'edges') else []
    faces = geom_part.faces if hasattr(geom_part, 'faces') else []
    sample_edge = edges[0] if len(edges) > 0 else None

    capabilities = {
        'edge_has_getFaces': hasattr(sample_edge, 'getFaces') if sample_edge else False,
        'edge_has_getVertices': hasattr(sample_edge, 'getVertices') if sample_edge else False,
        'edge_has_pointOn': hasattr(sample_edge, 'pointOn') if sample_edge else False,
        'face_count': len(faces),
        'edge_count': len(edges)
    }
    return capabilities

# Phase 14: 2D Edge-based Crack Edge Detection
def phase_crack_edge_detection(ctx):
    geom_part = ctx.get('crack_geom_part')
    if not geom_part:
        raise RuntimeError('crack_geom_part unavailable')

    edges = geom_part.edges if hasattr(geom_part, 'edges') else []
    top_edges = 0
    bottom_edges = 0
    total_edges = len(edges)

    for edge in edges:
        if hasattr(edge, 'pointOn'):
            pt = edge.pointOn[0]
            if pt[1] >= 0:
                top_edges += 1
            else:
                bottom_edges += 1

    if total_edges == 0 or top_edges == 0 or bottom_edges == 0:
        raise RuntimeError("crack_edge_detection found no usable crack edges (total={0}, top={1}, bottom={2})".format(total_edges, top_edges, bottom_edges))

    return {
        'top_edges_count': top_edges,
        'bottom_edges_count': bottom_edges,
        'total_edges': total_edges,
        'is_observation_only_probe': False
    }

# Phase 15: Crack Mesh Topology Probe (Using original mesh source_part or meshed part)
def phase_crack_mesh_topology(ctx):
    model = ctx.get('crack_model')
    geom_part = ctx.get('crack_geom_part')

    source_part = model.parts[list(model.parts.keys())[0]] if model and hasattr(model, 'parts') else None
    target_part = geom_part if (geom_part and hasattr(geom_part, 'nodes') and len(geom_part.nodes) > 0) else source_part

    if not target_part:
        raise RuntimeError('Neither geom_part nor source_part available for topology inspection')

    nodes = target_part.nodes if hasattr(target_part, 'nodes') and target_part.nodes else []
    elements = target_part.elements if hasattr(target_part, 'elements') and target_part.elements else []

    crack_y_tol = 0.001
    coord_tol = 0.0001
    min_x = -0.5 - crack_y_tol
    max_x = 0.0 + crack_y_tol

    lower_node_labels = []
    upper_node_labels = []
    lower_coords = {}
    upper_coords = {}

    single_label_coords = []
    double_label_coords = []
    multi_label_coords = []

    if hasattr(target_part, 'sets') and 'notch_lower_face' in target_part.sets and 'notch_upper_face' in target_part.sets:
        lower_nodes = target_part.sets['notch_lower_face'].nodes
        upper_nodes = target_part.sets['notch_upper_face'].nodes
        lower_node_labels = [n.label for n in lower_nodes if min_x <= n.coordinates[0] <= max_x]
        upper_node_labels = [n.label for n in upper_nodes if min_x <= n.coordinates[0] <= max_x]
        lower_coords = {n.label: n.coordinates for n in lower_nodes if min_x <= n.coordinates[0] <= max_x}
        upper_coords = {n.label: n.coordinates for n in upper_nodes if min_x <= n.coordinates[0] <= max_x}
    else:
        # Empirical coordinate grouping for crack segment [-0.5, 0.0]
        coord_groups = {}
        for n in nodes:
            coords = n.coordinates
            x, y = coords[0], coords[1]
            if min_x <= x <= max_x and abs(y) <= crack_y_tol:
                key = (round(x / coord_tol), round(y / coord_tol))
                coord_groups.setdefault(key, []).append((n.label, coords))

        for key, item_list in sorted(coord_groups.items()):
            labels = [lbl for lbl, c in item_list]
            if len(labels) == 1:
                single_label_coords.append(key)
            elif len(labels) == 2:
                double_label_coords.append(key)
                upper_node_labels.append(item_list[0][0])
                upper_coords[item_list[0][0]] = item_list[0][1]
                lower_node_labels.append(item_list[1][0])
                lower_coords[item_list[1][0]] = item_list[1][1]
            else:
                multi_label_coords.append(key)

    classification = "inconclusive"
    if len(double_label_coords) == 15 or (len(lower_node_labels) == 15 and len(upper_node_labels) == 15):
        classification = "duplicated_crack_face_nodes"
    elif len(single_label_coords) >= 15 and len(double_label_coords) == 0:
        classification = "continuous_centerline_mesh"

    if classification not in ("duplicated_crack_face_nodes", "continuous_centerline_mesh"):
        raise RuntimeError("crack_mesh_topology invalid mesh classification '{0}' (single_coords={1}, double_coords={2})".format(
            classification, len(single_label_coords), len(double_label_coords)
        ))

    if classification == "duplicated_crack_face_nodes" and (len(lower_node_labels) == 0 or len(upper_node_labels) == 0):
        raise RuntimeError("crack_mesh_topology upper and lower node sets are empty")
    elif classification == "continuous_centerline_mesh" and len(single_label_coords) == 0:
        raise RuntimeError("crack_mesh_topology centerline node set is empty")

    lower_set = set(lower_node_labels)
    upper_set = set(upper_node_labels)
    intersection_count = len(lower_set.intersection(upper_set))
    disjoint_node_sets = (intersection_count == 0)

    if classification == "duplicated_crack_face_nodes" and not disjoint_node_sets:
        raise RuntimeError("crack_mesh_topology node sets are not disjoint (intersection count: {0})".format(intersection_count))

    coincident_pair_count = 0
    for l_label, l_c in lower_coords.items():
        for u_label, u_c in upper_coords.items():
            if abs(l_c[0] - u_c[0]) < 1e-5 and abs(l_c[1] - u_c[1]) < 1e-5:
                coincident_pair_count += 1
                break

    expected_coincident_pair_count = 15 if classification == "duplicated_crack_face_nodes" else 0
    if classification == "duplicated_crack_face_nodes" and coincident_pair_count != expected_coincident_pair_count:
        raise RuntimeError("crack_mesh_topology coincident pair count is {0}, expected {1}".format(coincident_pair_count, expected_coincident_pair_count))

    bridge_elem_count = 0
    for elem in elements:
        n_labels = set()
        if hasattr(elem, 'getNodes'):
            n_labels = set(n.label for n in elem.getNodes())
        elif hasattr(elem, 'connectivity'):
            n_labels = set(elem.connectivity)
        if len(n_labels.intersection(lower_set)) > 0 and len(n_labels.intersection(upper_set)) > 0:
            bridge_elem_count += 1

    if classification == "duplicated_crack_face_nodes" and bridge_elem_count != 0:
        raise RuntimeError("crack_mesh_topology bridge element count is non-zero ({0})".format(bridge_elem_count))

    bounds_satisfied = True
    for c in list(lower_coords.values()) + list(upper_coords.values()):
        if not (min_x <= c[0] <= max_x):
            bounds_satisfied = False
            break

    if not bounds_satisfied:
        raise RuntimeError("crack_mesh_topology selected nodes outside coordinate bounds [-0.5, 0.0]")

    return {
        'lower_node_labels_count': len(lower_node_labels),
        'upper_node_labels_count': len(upper_node_labels),
        'intersection_count': intersection_count,
        'disjoint_node_sets': disjoint_node_sets,
        'coincident_node_pairs_count': coincident_pair_count,
        'expected_coincident_pair_count': expected_coincident_pair_count,
        'bridge_element_count': bridge_elem_count,
        'coordinate_bounds_satisfied': bounds_satisfied,
        'crack_mesh_classification': classification
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
        ('geometry_conversion_observation', phase_geometry_conversion_observation),
        ('usable_geometry_validation', phase_usable_geometry_validation),
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
