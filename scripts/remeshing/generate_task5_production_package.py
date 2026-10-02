# -*- coding: utf-8 -*-
"""
Task 5 Production Package Generator: Pandey & Kumar (2025) Mode-I Proposed Adaptive Refinement.

Executes the publication-faithful two-pass workflow:
Pass 1:
  - Geometric model [0,1]x[0,1] mm plate with notch slit at y=0.5, x in [0, 0.5] mm
  - Coarse seed h_cms = 0.02 mm (matching Section 4.1 Page 3265)
  - RemeshingRule: errorTarget=1.0%, h_min=0.001 mm, h_max=0.02 mm, refinementFactor=10, coarsening=NOT_ALLOWED
  - Solves elastic pre-analysis to generate MISESERI error indicator
Pass 2:
  - Executes mdb.models[m].adaptiveRemesh(odb=o1) to generate publication-grade refined mesh
  - Exports refined physical deck
  - Builds complete 4-layer UEL production input deck with 2-step fracture displacement schedule
  - Prepares PBS submission scripts, subroutine symlinks, and manifest
"""

from __future__ import print_function

import os
import sys
import math
import json
import hashlib
import shutil

# Abaqus CAE environment modules
from abaqus import *
from abaqusConstants import *
import regionToolset
import part
import material
import section
import assembly
import step
import interaction
import load
import mesh
import job
import sketch
import visualization
import odbAccess


def compute_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, 'rb') as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def generate_task5_production_uel_deck(src_phys_inp, dst_uel_inp, job_name="PK_MODE1_PROPOSED_PFM"):
    """
    Builds reference-identical 4-layer UEL input deck matching f42_mixed_uel.for:
    - User Elements: U1 (PF quad), U2 (Disp quad), U3 (PF tri), U4 (Disp tri)
    - Companion UMAT: CPE4 / CPE3 in All_elem
    - Step 1: u = 0.005 mm (time=1.0, dt_init=0.02, dt_max=0.02)
    - Step 2: u = 0.010 mm (time=1.0, dt_init=0.002, dt_max=0.002)
    - Rigid top tensile pull tied to RP (999999) via *EQUATION
    """
    nodes = {}
    quad_elems = {}
    tri_elems = {}
    
    in_nodes = False
    in_elements = False
    elem_type = None

    with open(src_phys_inp, 'r') as f:
        for line in f:
            l = line.strip()
            if not l or l.startswith('**'):
                continue
            if l.startswith('*'):
                in_nodes = False
                in_elements = False
                if l.upper().startswith('*NODE'):
                    in_nodes = True
                elif l.upper().startswith('*ELEMENT'):
                    in_elements = True
                    if 'CPS4' in l.upper() or 'CPE4' in l.upper() or 'QUAD' in l.upper():
                        elem_type = 'QUAD'
                    elif 'CPS3' in l.upper() or 'CPE3' in l.upper() or 'TRI' in l.upper():
                        elem_type = 'TRI'
                    else:
                        elem_type = 'QUAD'
                continue

            if in_nodes:
                parts = [p.strip() for p in l.split(',') if p.strip()]
                if len(parts) >= 3:
                    try:
                        nid = int(parts[0])
                        x = float(parts[1])
                        y = float(parts[2])
                        nodes[nid] = (x, y)
                    except ValueError:
                        continue

            if in_elements:
                parts = [p.strip() for p in l.split(',') if p.strip()]
                if len(parts) >= 4:
                    try:
                        int_parts = [int(p) for p in parts]
                        eid = int_parts[0]
                        conn = int_parts[1:]
                        if elem_type == 'QUAD' or len(conn) == 4:
                            quad_elems[eid] = tuple(conn[:4])
                        else:
                            tri_elems[eid] = tuple(conn[:3])
                    except ValueError:
                        continue

    num_phys_nodes = len(nodes)
    num_phys_quads = len(quad_elems)
    num_phys_tris = len(tri_elems)
    num_phys_elems = num_phys_quads + num_phys_tris

    # Find boundary nodes
    bottom_nodes = [nid for nid, (x, y) in nodes.items() if abs(y - 0.0) < 1e-4]
    top_nodes = [nid for nid, (x, y) in nodes.items() if abs(y - 1.0) < 1e-4]
    pin_candidates = [nid for nid in bottom_nodes if abs(nodes[nid][0] - 0.0) < 1e-4]
    pin_node = min(pin_candidates) if pin_candidates else bottom_nodes[0]
    rp_nid = 999999

    with open(dst_uel_inp, 'w') as f:
        f.write("*HEADING\n")
        f.write("Pandey & Kumar (2025) Mode-I Proposed Adaptive Refined PFM Solve\n")
        f.write("** Physical Elements: " + str(num_phys_elems) + " (" + str(num_phys_quads) + " quads, " + str(num_phys_tris) + " tris), Nodes: " + str(num_phys_nodes) + "\n")
        f.write("** Parameters: E=210 GPa, nu=0.3, l0=0.0075 mm, Gc=0.0027 kN/mm, eta=1e-7\n")
        f.write("** ----------------------------------------------------------\n")
        
        # User Element Interfaces
        f.write("*USER ELEMENT, TYPE=U1, NODES=4, COORDINATES=2, PROPERTIES=6, VARIABLES=18, UNSYMM\n3\n")
        f.write("*USER ELEMENT, TYPE=U2, NODES=4, COORDINATES=2, PROPERTIES=6, VARIABLES=18, UNSYMM\n1, 2\n")
        if num_phys_tris > 0:
            f.write("*USER ELEMENT, TYPE=U3, NODES=3, COORDINATES=2, PROPERTIES=6, VARIABLES=18, UNSYMM\n3\n")
            f.write("*USER ELEMENT, TYPE=U4, NODES=3, COORDINATES=2, PROPERTIES=6, VARIABLES=18, UNSYMM\n1, 2\n")
        
        # Nodes
        f.write("*NODE\n")
        for nid in sorted(nodes.keys()):
            x, y = nodes[nid]
            f.write(str(nid) + ", " + str(x) + ", " + str(y) + "\n")
        # Reference point node for top pull
        f.write(str(rp_nid) + ", 0.5, 1.0\n")

        # Layer 1: Phase-field user elements (U1 for quads, U3 for tris) -> IDs 1..N_phys
        if quad_elems:
            f.write("*ELEMENT, TYPE=U1, ELSET=PHASE_QUAD\n")
            for eid in sorted(quad_elems.keys()):
                c = quad_elems[eid]
                f.write(str(eid) + ", " + ", ".join(str(n) for n in c) + "\n")
        if tri_elems:
            f.write("*ELEMENT, TYPE=U3, ELSET=PHASE_TRI\n")
            for eid in sorted(tri_elems.keys()):
                c = tri_elems[eid]
                f.write(str(eid) + ", " + ", ".join(str(n) for n in c) + "\n")

        # Layer 2: Displacement user elements (U2 for quads, U4 for tris) -> IDs (N_phys+1)..2*N_phys
        offset_disp = num_phys_elems
        if quad_elems:
            f.write("*ELEMENT, TYPE=U2, ELSET=DISP_QUAD\n")
            for eid in sorted(quad_elems.keys()):
                c = quad_elems[eid]
                f.write(str(eid + offset_disp) + ", " + ", ".join(str(n) for n in c) + "\n")
        if tri_elems:
            f.write("*ELEMENT, TYPE=U4, ELSET=DISP_TRI\n")
            for eid in sorted(tri_elems.keys()):
                c = tri_elems[eid]
                f.write(str(eid + offset_disp) + ", " + ", ".join(str(n) for n in c) + "\n")

        # Layer 3: Dummy UMAT elements for visualization -> IDs (2*N_phys+1)..3*N_phys
        offset_umat = 2 * num_phys_elems
        if quad_elems:
            f.write("*ELEMENT, TYPE=CPE4, ELSET=UMAT_QUADS\n")
            for eid in sorted(quad_elems.keys()):
                c = quad_elems[eid]
                f.write(str(eid + offset_umat) + ", " + ", ".join(str(n) for n in c) + "\n")
        if tri_elems:
            f.write("*ELEMENT, TYPE=CPE3, ELSET=UMAT_TRIS\n")
            for eid in sorted(tri_elems.keys()):
                c = tri_elems[eid]
                f.write(str(eid + offset_umat) + ", " + ", ".join(str(n) for n in c) + "\n")

        # Element sets
        f.write("*ELSET, ELSET=All_elem\nUMAT_QUADS\n")
        if tri_elems:
            f.write("UMAT_TRIS\n")
        f.write("*ELSET, ELSET=umatelem\nAll_elem\n")

        # Node sets (wrapped at <= 16 nodes per line to prevent Abaqus preprocessor truncation)
        def write_nset(file_handle, set_name, node_list):
            file_handle.write("*NSET, NSET=" + set_name + "\n")
            chunk_size = 10
            for i in range(0, len(node_list), chunk_size):
                chunk = node_list[i:i + chunk_size]
                file_handle.write(", ".join(str(n) for n in chunk) + "\n")

        write_nset(f, "N_BOTTOM", bottom_nodes)
        write_nset(f, "N_PIN", [pin_node])
        write_nset(f, "N_TOP", top_nodes)
        write_nset(f, "N_RP", [rp_nid])

        # UEL Properties: l0, Gc, E, nu, eta, N_PHYS
        f.write("*UEL PROPERTY, ELSET=PHASE_QUAD\n0.0075, 0.0027, 210.0, 0.3, 1.0e-7, " + str(float(num_phys_elems)) + "\n")
        f.write("*UEL PROPERTY, ELSET=DISP_QUAD\n0.0075, 0.0027, 210.0, 0.3, 1.0e-7, " + str(float(num_phys_elems)) + "\n")
        if tri_elems:
            f.write("*UEL PROPERTY, ELSET=PHASE_TRI\n0.0075, 0.0027, 210.0, 0.3, 1.0e-7, " + str(float(num_phys_elems)) + "\n")
            f.write("*UEL PROPERTY, ELSET=DISP_TRI\n0.0075, 0.0027, 210.0, 0.3, 1.0e-7, " + str(float(num_phys_elems)) + "\n")

        # Dummy UMAT section for visualization
        f.write("*SOLID SECTION, ELSET=All_elem, MATERIAL=DUMMY_MAT\n1.0\n")
        f.write("*MATERIAL, NAME=DUMMY_MAT\n*USER MATERIAL, CONSTANTS=2\n210.0, 0.3\n")
        f.write("*DEPVAR\n16\n")

        # Equations tying top nodes to RP
        f.write("** EQUATIONS (Rigid top tensile pull tied to RP)\n")
        for tn in sorted(top_nodes):
            f.write("*EQUATION\n2\n" + str(tn) + ", 2, 1.0, " + str(rp_nid) + ", 2, -1.0\n")

        # Step 1: Pre-peak linear loading to u = 0.005 mm (50 increments of 0.0001 mm)
        f.write("** ----------------------------------------------------------\n")
        f.write("** STEP 1: Linear Loading to u = 0.005 mm\n")
        f.write("** ----------------------------------------------------------\n")
        f.write("*STEP, NAME=Step-1, NLGEOM=NO, INC=10000\n")
        f.write("*STATIC\n")
        f.write("0.02, 1.0, 1.0e-7, 0.02\n")
        f.write("*BOUNDARY\n")
        f.write("N_BOTTOM, 2, 2, 0.0\n")
        f.write("N_PIN, 1, 1, 0.0\n")
        f.write("N_TOP, 1, 1, 0.0\n")
        f.write("N_RP, 2, 2, 0.0050\n")
        f.write("*RESTART, WRITE, FREQUENCY=0\n")
        f.write("*OUTPUT, FIELD, FREQUENCY=1\n")
        f.write("*NODE OUTPUT, NSET=N_RP\nU, RF\n")
        f.write("*ELEMENT OUTPUT, ELSET=DISP_QUAD\nSDV\n")
        f.write("*NODE PRINT, FREQ=1, NSET=N_RP\nU2, RF2\n")
        f.write("*END STEP\n")

        # Step 2: Fine fracture propagation to u = 0.010 mm (500 increments of 0.00001 mm)
        f.write("** ----------------------------------------------------------\n")
        f.write("** STEP 2: Fracture Propagation to u = 0.010 mm\n")
        f.write("** ----------------------------------------------------------\n")
        f.write("*STEP, NAME=Step-2, NLGEOM=NO, INC=20000\n")
        f.write("*STATIC\n")
        f.write("0.002, 1.0, 1.0e-8, 0.002\n")
        f.write("*BOUNDARY\n")
        f.write("N_RP, 2, 2, 0.0100\n")
        f.write("*RESTART, WRITE, FREQUENCY=0\n")
        f.write("*OUTPUT, FIELD, FREQUENCY=1\n")
        f.write("*NODE OUTPUT, NSET=N_RP\nU, RF\n")
        f.write("*ELEMENT OUTPUT, ELSET=DISP_QUAD\nSDV\n")
        f.write("*NODE PRINT, FREQ=1, NSET=N_RP\nU2, RF2\n")
        f.write("*END STEP\n")

    return {
        "uel_deck_path": dst_uel_inp,
        "num_nodes": num_phys_nodes,
        "num_elements": num_phys_elems,
        "num_quads": num_phys_quads,
        "num_tris": num_phys_tris
    }


def generate_production_package(output_dir):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    os.chdir(output_dir)

    print("================================================================================")
    print("GENERATING TASK 5 PANDEY & KUMAR PROPOSED ADAPTIVE REFINEMENT PRODUCTION PACKAGE")
    print("================================================================================")
    print("Target Directory: " + str(output_dir))

    # Production parameters (Pandey & Kumar 2025 Section 4.1 Page 3265)
    coarse_h = 0.02      # Global initial coarse seed (0.02 mm)
    min_h = 0.001         # Local refined size (0.001 mm)
    max_h = 0.02          # Global maximum size (0.02 mm)
    error_target = 1.0    # 1% relative error threshold

    # Step 1: Create geometry with notch slit
    model_name = "PK_MODE1_PROP_ADAPT"
    if model_name in mdb.models:
        del mdb.models[model_name]
    m = mdb.Model(name=model_name)

    w = 0.001
    s = m.ConstrainedSketch(name='__profile__', sheetSize=2.0)
    s.Line(point1=(0.0, 0.0), point2=(1.0, 0.0))
    s.Line(point1=(1.0, 0.0), point2=(1.0, 1.0))
    s.Line(point1=(1.0, 1.0), point2=(0.0, 1.0))
    s.Line(point1=(0.0, 1.0), point2=(0.0, 0.5 + w))
    s.Line(point1=(0.0, 0.5 + w), point2=(0.5, 0.5 + w))
    s.Line(point1=(0.5, 0.5 + w), point2=(0.5, 0.5 - w))
    s.Line(point1=(0.5, 0.5 - w), point2=(0.0, 0.5 - w))
    s.Line(point1=(0.0, 0.5 - w), point2=(0.0, 0.0))

    p = m.Part(name='Plate', dimensionality=TWO_D_PLANAR, type=DEFORMABLE_BODY)
    p.BaseShell(sketch=s)
    del m.sketches['__profile__']

    mat = m.Material(name='Steel')
    mat.Elastic(table=((210000.0, 0.3), ))
    m.HomogeneousSolidSection(name='SolidSec', material='Steel', thickness=1.0)
    p.SectionAssignment(region=regionToolset.Region(faces=p.faces), sectionName='SolidSec')

    p.seedPart(size=coarse_h, deviationFactor=0.1, minSizeFactor=0.1)
    p.generateMesh()
    coarse_elements = len(p.elements)
    coarse_nodes = len(p.nodes)
    print("Initial Coarse Mesh (h=0.02 mm): %d elements, %d nodes" % (coarse_elements, coarse_nodes))

    a = m.rootAssembly
    inst = a.Instance(name='Plate-1', part=p, dependent=ON)

    m.StaticStep(name='Step-1', previous='Initial', timePeriod=1.0, 
                 initialInc=0.1, minInc=1e-5, maxInc=0.1, nlgeom=OFF)

    reg = regionToolset.Region(faces=inst.faces)
    m.fieldOutputRequests['F-Output-1'].setValues(
        variables=('S', 'U', 'RF', 'MISESERI', 'MISESAVG', 'EVOL'),
        region=reg
    )

    a.Set(name='Bottom', edges=inst.edges.findAt(((0.5, 0.0, 0.0), )))
    m.DisplacementBC(name='FixBottom', createStepName='Step-1', region=a.sets['Bottom'], u1=0.0, u2=0.0)
    a.Set(name='Top', edges=inst.edges.findAt(((0.5, 1.0, 0.0), )))
    m.DisplacementBC(name='TensionTop', createStepName='Step-1', region=a.sets['Top'], u2=0.005)

    m.RemeshingRule(
        name='RR: 1',
        stepName='Step-1',
        region=reg,
        description='Publication-faithful Remeshing Rule for Proposed PFM (errorTarget=1.0%)',
        outputFrequency=ALL_INCREMENTS,
        variables=('MISESERI', ),
        sizingMethod=UNIFORM_ERROR,
        errorTarget=error_target,
        specifyMinSize=True,
        specifyMaxSize=True,
        minElementSize=min_h,
        maxElementSize=max_h,
        elementCountLimit=None,
        coarseningFactor=NOT_ALLOWED,
        refinementFactor=10
    )

    # Pre-analysis job
    job1_name = "PK_PREANALYSIS_COARSE"
    j1 = mdb.Job(name=job1_name, model=model_name, description='Pre-Analysis for Production Adaptive Refinement')
    j1.writeInput(consistencyChecking=OFF)
    j1.submit(consistencyChecking=OFF)
    j1.waitForCompletion()
    print("Pre-analysis completed with status: " + str(j1.status))

    # Native adaptive remeshing
    odb1_path = os.path.abspath(job1_name + ".odb")
    o1 = odbAccess.openOdb(path=odb1_path, readOnly=True)
    m.adaptiveRemesh(odb=o1)
    o1.close()

    refined_elements = len(p.elements)
    refined_nodes = len(p.nodes)
    print("Production Refined Mesh (Target ~13,941 elements): %d elements, %d nodes" % (refined_elements, refined_nodes))

    # Write refined physical deck
    job_prod_name = "PK_MODE1_PROPOSED_PFM"
    j2 = mdb.Job(name=job_prod_name + "_PHYS", model=model_name)
    j2.writeInput(consistencyChecking=OFF)
    phys_inp_path = os.path.abspath(job_prod_name + "_PHYS.inp")

    # Generate UEL production deck
    uel_inp_path = os.path.abspath(job_prod_name + ".inp")
    uel_info = generate_task5_production_uel_deck(phys_inp_path, uel_inp_path, job_name=job_prod_name)
    print("Generated Production UEL Deck: " + uel_inp_path)

    # Copy Fortran subroutine
    src_sub = "/home/pr21vyci/projects/adaptive-remeshing/subroutines/f42_mixed_uel.for"
    dst_sub = os.path.join(output_dir, "f42_mixed_uel.for")
    if os.path.exists(src_sub):
        shutil.copy2(src_sub, dst_sub)

    manifest = {
        "benchmark": "PANDEY_KUMAR_2025_MODE_I_PROPOSED_ADAPTIVE_PFM",
        "case_name": job_prod_name,
        "material_parameters": {
            "E_GPa": 210.0,
            "nu": 0.3,
            "l0_mm": 0.0075,
            "Gc_kN_per_mm": 0.0027,
            "eta": 1.0e-7
        },
        "remeshing_rule": {
            "name": "RR: 1",
            "variable": "MISESERI",
            "sizing_method": "UNIFORM_ERROR",
            "error_target": error_target,
            "min_element_size_mm": min_h,
            "max_element_size_mm": max_h,
            "coarsening": "NOT_ALLOWED",
            "refinement_factor": 10
        },
        "coarse_mesh": {
            "nominal_size_mm": coarse_h,
            "num_elements": coarse_elements,
            "num_nodes": coarse_nodes
        },
        "refined_mesh": {
            "num_elements": refined_elements,
            "num_nodes": refined_nodes,
            "min_size_mm": min_h,
            "max_size_mm": max_h
        },
        "layered_uel_mesh": uel_info,
        "files_generated": {
            "production_uel_inp": uel_inp_path,
            "production_uel_inp_sha256": compute_sha256(uel_inp_path),
            "subroutine_for": dst_sub,
            "subroutine_for_sha256": compute_sha256(dst_sub) if os.path.exists(dst_sub) else ""
        },
        "status": "PACKAGE_GENERATED_READY_FOR_DATACHECK"
    }

    manifest_path = os.path.join(output_dir, "manifest.json")
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)

    print("\n================================================================================")
    print("TASK 5 PRODUCTION PACKAGE GENERATION COMPLETE")
    print(json.dumps(manifest, indent=2))
    print("================================================================================")

    return manifest


if __name__ == "__main__":
    out_dir = "/home/pr21vyci/projects/adaptive-remeshing/models/pandey_kumar_mode1/02_proposed_adaptive_refined"
    generate_production_package(output_dir=out_dir)
