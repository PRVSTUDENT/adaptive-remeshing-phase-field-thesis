#!/usr/bin/env python3
"""
F43GEO1 Abaqus/CAE Native Parametric Geometry Builder for Pandey-Kumar Mode-II Benchmark.

Constructs a CAD geometry-backed model part from native sketch and partition operations:
- 1.0 mm x 1.0 mm square domain [-0.5, 0.5] x [-0.5, 0.5]
- Native sketch partition for single-edge horizontal notch y=0.0, x in [-0.5, 0.0] mm
- Seam edge assignment along notch line
- Adaptivity-compatible FREE quadrilateral mesh controls (CPE4 elements)
- Real physical material elasticity (E = 210000.0 MPa, v = 0.3, plane strain)
- Fixed bottom boundary (u1=u2=0), top vertical restraint (u2=0), RP horizontal shear displacement (u1=0.001 mm)
- Output requests for S, MISESERI, MISESAVG, EVOL, U, RF
- Saves ModeII_Geometry_Source.cae and writes F43PRE2_GEOM.inp
"""

import sys
import os
import json
import hashlib

BUILDER_SPEC_VERSION = "1.0-geo1"

CANONICAL_BENCHMARK_SPEC = {
    "name": "pandey_kumar_2025_mode_ii_asymmetric_shear",
    "width_mm": 1.0,
    "height_mm": 1.0,
    "thickness_mm": 1.0,
    "notch_length_mm": 0.5,
    "notch_start_mm": [-0.5, 0.0],
    "notch_tip_mm": [0.0, 0.0],
    "material": {
        "youngs_modulus_MPa": 210000.0,
        "poissons_ratio": 0.3,
        "gc_N_per_mm": 2.7,
        "l0_mm": 0.015
    },
    "mesh": {
        "element_family": "CPE4",
        "elem_shape": "QUAD",
        "technique": "FREE",
        "algorithm": "ADVANCING_FRONT",
        "target_h_mm": 0.018,
        "planned_coarse_element_count_range": [3500, 4300]
    },
    "deterministic_names": {
        "model_name": "ModeII_Geometry_Model",
        "part_name": "PlatePart",
        "instance_name": "PlateInstance",
        "step_name": "Step-1",
        "material_name": "Steel",
        "section_name": "SolidSection",
        "set_bottom": "bottom_nodes",
        "set_top": "top_nodes",
        "set_rp": "RP",
        "rule_name": "MISESERI_Adaptive_Rule"
    }
}

def build_native_mode_ii_cae_model(output_dir="."):
    output_dir = os.path.abspath(output_dir)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    spec = CANONICAL_BENCHMARK_SPEC
    names = spec["deterministic_names"]

    try:
        from abaqus import mdb, session
        from abaqusConstants import (
            TWO_D_PLANAR, DEFORMABLE_BODY, STANDARD, PLANE_STRAIN,
            QUAD, FREE, ADVANCING_FRONT, CPE4, ON, OFF, SET, COPLANAR_EDGES
        )
    except ImportError:
        print("[F43GEO1 Builder] Standalone inspection environment (Abaqus Python API absent).")
        manifest_path = os.path.join(output_dir, "F43PRE2_SOURCE_MANIFEST.json")
        with open(manifest_path, "w") as fp:
            json.dump({
                "spec_version": BUILDER_SPEC_VERSION,
                "builder_ready": True,
                "cae_generated": False,
                "geometry_backed": True,
                "orphan_mesh": False,
                "model_name": names["model_name"],
                "part_name": names["part_name"],
                "instance_name": names["instance_name"],
                "step_name": names["step_name"],
                "benchmark_spec": spec
            }, fp, indent=2)
        return manifest_path

    print("[F43GEO1 Builder] Creating CAD geometry-backed model: " + str(names["model_name"]))
    if names["model_name"] in mdb.models:
        del mdb.models[names["model_name"]]

    model = mdb.Model(name=names["model_name"])

    # 1. Sketch & Base Shell Part
    sketch = model.ConstrainedSketch(name='__profile__', sheetSize=2.0)
    sketch.rectangle(point1=(-0.5, -0.5), point2=(0.5, 0.5))
    part = model.Part(name=names["part_name"], dimensionality=TWO_D_PLANAR, type=DEFORMABLE_BODY)
    part.BaseShell(sketch=sketch)
    del model.sketches['__profile__']

    # 2. Native Sketch Partition for Notch
    notch_sketch = model.ConstrainedSketch(name='__notch__', sheetSize=2.0, transform=part.getSketchTransform(sketchPlane=part.faces[0]))
    part.projectReferencesOntoSketch(sketch=notch_sketch, filter=COPLANAR_EDGES)
    notch_sketch.Line(point1=(-0.5, 0.0), point2=(0.0, 0.0))
    part.PartitionFaceBySketch(faces=part.faces[0], sketch=notch_sketch)
    del model.sketches['__notch__']

    # 3. Assign Seam to Notch Line Edge
    notch_edges = part.edges.findAt(((-0.25, 0.0, 0.0),))
    part.engineeringFeatures.assignSeam(regions=notch_edges)

    # 4. Material & Homogeneous Plane Strain Section
    material = model.Material(name=names["material_name"])
    material.Elastic(table=((spec["material"]["youngs_modulus_MPa"], spec["material"]["poissons_ratio"]),))
    model.HomogeneousSolidSection(name=names["section_name"], material=names["material_name"], thickness=spec["thickness_mm"])
    part.SectionAssignment(region=(part.faces,), sectionName=names["section_name"])

    # 5. Assembly Instance & Sets
    assembly = model.rootAssembly
    instance = assembly.Instance(name=names["instance_name"], part=part, dependent=ON)

    bottom_edges = instance.edges.findAt(((-0.25, -0.5, 0.0),), ((0.25, -0.5, 0.0),))
    top_edges = instance.edges.findAt(((-0.25, 0.5, 0.0),), ((0.25, 0.5, 0.0),))
    
    assembly.Set(name=names["set_bottom"], edges=bottom_edges)
    assembly.Set(name=names["set_top"], edges=top_edges)

    # Reference Point & Kinematic Coupling Equation
    rp = assembly.ReferencePoint(point=(0.0, 0.6, 0.0))
    assembly.Set(name=names["set_rp"], referencePoints=(assembly.referencePoints[rp.id],))
    model.Equation(name='shear_coupling', terms=((1.0, names["set_top"], 1), (-1.0, names["set_rp"], 1)))

    # 6. Step & Boundary Conditions
    model.StaticStep(name=names["step_name"], previous='Initial', timePeriod=1.0, initialInc=0.001, maxInc=1.0)
    model.fieldOutputRequests['F-Output-1'].setValues(variables=('S', 'MISESERI', 'MISESAVG', 'EVOL', 'U', 'RF'))

    model.DisplacementBC(name='bottom_fix', createStepName='Initial', region=assembly.sets[names["set_bottom"]], u1=0.0, u2=0.0)
    model.DisplacementBC(name='top_vertical_fix', createStepName='Initial', region=assembly.sets[names["set_top"]], u2=0.0)
    model.DisplacementBC(name='prescribed_shear', createStepName=names["step_name"], region=assembly.sets[names["set_rp"]], u1=0.001)

    # 7. Adaptivity-Compatible Mesh Controls & CPE4 Elements
    import mesh
    part.setMeshControls(regions=part.faces, elemShape=QUAD, technique=FREE, algorithm=ADVANCING_FRONT)
    part.setElementType(regions=(part.faces,), elemTypes=(mesh.ElemType(elemCode=CPE4, elemLibrary=STANDARD),))
    part.seedPart(size=spec["mesh"]["target_h_mm"], deviationFactor=0.1, minSizeFactor=0.1)
    part.generateMesh()

    # Save CAE database & Write INP Deck
    cae_path = os.path.join(output_dir, "ModeII_Geometry_Source.cae")
    inp_path = os.path.join(output_dir, "F43PRE2_GEOM.inp")
    
    mdb.saveAs(pathName=cae_path)
    job = mdb.Job(name="F43PRE2_GEOM", model=names["model_name"])
    job.writeInput(consistencyChecking=OFF)

    with open(cae_path, "rb") as fp:
        cae_sha256 = hashlib.sha256(fp.read()).hexdigest()
    with open(inp_path, "rb") as fp:
        inp_sha256 = hashlib.sha256(fp.read()).hexdigest()

    manifest = {
        "spec_version": BUILDER_SPEC_VERSION,
        "builder_ready": True,
        "cae_generated": True,
        "cae_path": cae_path,
        "cae_sha256": cae_sha256,
        "inp_path": inp_path,
        "inp_sha256": inp_sha256,
        "model_name": names["model_name"],
        "part_name": names["part_name"],
        "instance_name": names["instance_name"],
        "step_name": names["step_name"],
        "mesh_element_count": len(part.elements),
        "mesh_node_count": len(part.nodes),
        "geometry_backed": True,
        "orphan_mesh": False
    }

    manifest_path = os.path.join(output_dir, "F43PRE2_SOURCE_MANIFEST.json")
    with open(manifest_path, "w") as fp:
        json.dump(manifest, fp, indent=2)

    print("[F43GEO1 Builder] CAD Geometry-Backed CAE source created cleanly: " + str(cae_path))
    return manifest_path

if __name__ == "__main__":
    out_dir = sys.argv[1] if len(sys.argv) > 1 else "."
    build_native_mode_ii_cae_model(out_dir)
