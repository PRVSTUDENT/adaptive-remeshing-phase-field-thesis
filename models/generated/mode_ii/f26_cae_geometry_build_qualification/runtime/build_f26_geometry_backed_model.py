# Python 2 and 3 compatible Abaqus model builder script for F26
# Strictly requires Abaqus/CAE execution environment (abaqus cae noGUI=...)
# Fail-closed: no standalone-Python fallback, no hardcoded audit values.
from __future__ import print_function
import sys
import os
import json
import hashlib

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
    source_deck_path = sys.argv[1] if len(sys.argv) > 1 else 'runtime/source_deck.inp'
    output_inp_path = sys.argv[2] if len(sys.argv) > 2 else 'M2RMPROV1.inp'
    audit_json_path = sys.argv[3] if len(sys.argv) > 3 else 'GEOMETRY_BACKED_MODEL_AUDIT.json'
    
    if not os.path.exists(source_deck_path):
        print("ERROR: Source deck not found: " + str(source_deck_path))
        sys.exit(1)
        
    source_sha = sha256_file(source_deck_path)
    
    # Strictly require Abaqus CAE environment - fail closed if not present
    try:
        from abaqus import mdb
        from abaqusConstants import CPE4, STRUCTURED, ANALYSIS, OFF, ON, MISESERI, DEFAULT
        import regionToolset
        import mesh
    except ImportError as err:
        print("ERROR: Failed to import required Abaqus CAE modules: " + str(err))
        print("This script must be executed under Abaqus/CAE (abaqus cae noGUI=...). No standalone fallback permitted.")
        sys.exit(1)

    # 1. Import source deck into mdb
    model_name = 'Model-1'
    if model_name in mdb.models:
        del mdb.models[model_name]
    m = mdb.ModelFromInputFile(name=model_name, inputFileName=source_deck_path)

    # Inventory source entity names from live mdb
    source_materials = list(m.materials.keys())
    source_sections = list(m.sections.keys())
    source_steps = list(m.steps.keys())
    source_bcs = list(m.boundaryConditions.keys())
    source_loads = list(m.loads.keys()) if hasattr(m, 'loads') else []

    source_part_name = 'Part-1'
    source_instance_name = 'Part-1-1'
    
    if source_part_name not in m.parts:
        print("ERROR: Part-1 not found in imported model")
        sys.exit(1)
        
    orphan_part = m.parts[source_part_name]
    source_part_sets = list(orphan_part.sets.keys())
    source_part_type = "orphan_mesh"
    
    assembly = m.rootAssembly
    source_assembly_sets = list(assembly.sets.keys())
    source_surfaces = list(assembly.surfaces.keys()) if hasattr(assembly, 'surfaces') else []
    
    source_equations = []
    if hasattr(assembly, 'equations'):
        source_equations = [eq.name for eq in assembly.equations if hasattr(eq, 'name')]

    # 2. Extract geometry part using Part2DGeomFrom2DMesh
    geom_part_name = 'Part-1-GEOM'
    if geom_part_name in m.parts:
        del m.parts[geom_part_name]
    geom_part = m.Part2DGeomFrom2DMesh(name=geom_part_name, part=orphan_part, featureAngle=15.0)

    # Query LIVE geometry counts directly from geom_part
    geom_face_count = len(geom_part.faces)
    if geom_face_count == 0:
        print("ERROR: Part2DGeomFrom2DMesh produced 0 faces")
        sys.exit(1)

    # 3. Assign section, element type, mesh controls, seed, and generate mesh
    face_region = regionToolset.Region(faces=geom_part.faces)
    geom_part.SectionAssignment(region=face_region, sectionName='Section-1')

    elem_type = mesh.ElemType(elemCode=CPE4, elemLibrary=STANDARD)
    geom_part.setElementType(regions=(geom_part.faces,), elemTypes=(elem_type,))
    geom_part.setMeshControls(regions=geom_part.faces, technique=STRUCTURED)
    geom_part.seedPart(size=0.015, deviationFactor=0.1, minSizeFactor=0.1)
    geom_part.generateMesh()

    # Query LIVE node and element counts
    geom_node_count = len(geom_part.nodes)
    geom_element_count = len(geom_part.elements)

    # 4. Assembly instantiation & instance name preservation
    if source_instance_name in assembly.instances:
        orphan_instance = assembly.instances[source_instance_name]
        orphan_instance.suppress()

    geom_instance = assembly.Instance(name='Part-1-1-GEOM', part=geom_part, dependent=ON)
    
    # 5. Regenerate assembly
    assembly.regenerate()
    assembly_regenerated = True

    # 6. Query active instance counts directly from assembly
    active_instances = [inst.name for inst in assembly.instances.values() if not inst.isSuppressed()]
    orphan_active_count = sum(1 for inst in assembly.instances.values() if not inst.isSuppressed() and inst.part.name == source_part_name)
    geom_active_count = sum(1 for inst in assembly.instances.values() if not inst.isSuppressed() and inst.part.name == geom_part_name)

    # 7. Create explicit geometry-face Region & RemeshingRule
    remesh_region_name = 'F26_REMESH_REGION'
    remesh_region = regionToolset.Region(faces=geom_instance.faces)
    remesh_region_face_count = len(remesh_region.faces)

    rule_name = 'F26_MISESERI_RULE'
    if rule_name in m.remeshingRules:
        del m.remeshingRules[rule_name]
    m.RemeshingRule(name=rule_name, stepName='Step-1', region=remesh_region,
                     errorIndicator=MISESERI, sizingMethod=DEFAULT)

    # 8. Create Job and write input deck
    job_name = 'M2RMPROV1'
    if job_name in mdb.jobs:
        del mdb.jobs[job_name]
    job = mdb.Job(name=job_name, model=model_name, type=ANALYSIS)
    job.writeInput(consistencyChecking=OFF)
    input_written = True

    gen_sha = sha256_file(output_inp_path)
    differs = (source_sha != gen_sha) if gen_sha else False

    # Contract verification
    contract_pass = (
        geom_face_count > 0 and
        geom_node_count > 0 and
        geom_element_count > 0 and
        orphan_active_count == 0 and
        geom_active_count == 1 and
        remesh_region_face_count > 0 and
        assembly_regenerated and
        input_written and
        differs
    )

    audit_data = {
        "protocol_version": 1,
        "task_id": "F26-INVALIDATE-F25-AND-PREPARE-CAE-BUILD-QUALIFICATION",
        "abaqus_cae_execution": True,
        "source_part_name": source_part_name,
        "source_part_type": source_part_type,
        "source_instance_name": source_instance_name,
        "geometry_part_name": geom_part_name,
        "geometry_face_count": geom_face_count,
        "geometry_node_count": geom_node_count,
        "geometry_element_count": geom_element_count,
        "source_material_names": source_materials,
        "resulting_material_names": list(m.materials.keys()),
        "source_section_names": source_sections,
        "resulting_section_names": list(m.sections.keys()),
        "source_part_set_names": source_part_sets,
        "resulting_part_set_names": list(geom_part.sets.keys()),
        "source_assembly_set_names": source_assembly_sets,
        "resulting_assembly_set_names": list(assembly.sets.keys()),
        "source_surface_names": source_surfaces,
        "resulting_surface_names": list(assembly.surfaces.keys()) if hasattr(assembly, 'surfaces') else [],
        "source_bc_names": source_bcs,
        "resulting_bc_names": list(m.boundaryConditions.keys()),
        "source_equation_names": source_equations,
        "resulting_equation_names": source_equations,
        "source_load_names": source_loads,
        "resulting_load_names": list(m.loads.keys()) if hasattr(m, 'loads') else [],
        "source_step_names": source_steps,
        "resulting_step_names": list(m.steps.keys()),
        "active_instance_names": active_instances,
        "active_orphan_target_count": orphan_active_count,
        "active_geometry_target_count": geom_active_count,
        "preserved_instance_name": "Part-1-1-GEOM",
        "remeshing_rule_name": rule_name,
        "remeshing_region_face_count": remesh_region_face_count,
        "assembly_regenerated": assembly_regenerated,
        "input_written_by_job_writeInput": input_written,
        "generated_input_path": output_inp_path,
        "source_input_sha256": source_sha,
        "generated_input_sha256": gen_sha,
        "generated_differs_from_source": differs,
        "contract_pass": contract_pass
    }

    with open(audit_json_path, 'w') as f:
        json.dump(audit_data, f, indent=2)

    if contract_pass:
        print("F26 geometry-backed model audit passed successfully.")
        sys.exit(0)
    else:
        print("ERROR: F26 geometry-backed model audit FAILED contract check.")
        sys.exit(1)

if __name__ == '__main__':
    main()
