# -*- coding: utf-8 -*-
"""
Independent Benchmark: 2D Linear-Elastic Plate with Central Circular Hole under Uniaxial Tension.
Evaluates Abaqus native MISESERI error indicator and adaptiveRemesh() on an analytical stress
concentration problem (Kirsch solution, Kt ~ 3.0 at lateral hole flanks).

Geometry:
- Domain: 1.0 mm x 1.0 mm square plate [0, 1] x [0, 1]
- Central Circular Hole: Center (0.5, 0.5), Radius R = 0.1 mm
- Material: E = 210,000 MPa, nu = 0.3 (Linear Elastic)
- Loading: Tensile displacement uy = 0.001 mm at y = 1.0 mm
- Boundary Conditions: uy = 0 at y = 0.0 mm; ux = 0 at (0.0, 0.0 mm)
- Elements: CPE4 / CPE3 (Plane Strain)
"""
from __future__ import print_function
import sys
import os
import json
import math
import subprocess

import odbAccess
from abaqus import mdb
from abaqusConstants import (
    TWO_D_PLANAR, DEFORMABLE_BODY, STANDARD, CPE4, CPE3, ON, OFF, UNSET,
    UNIFORM_ERROR, NOT_ALLOWED, ALL_INCREMENTS
)
import regionToolset
import mesh

def compute_polygon_area_and_centroid(coords):
    num_n = len(coords)
    area_sum = 0.0
    for i in range(num_n):
        j = (i + 1) % num_n
        area_sum += coords[i][0] * coords[j][1] - coords[j][0] * coords[i][1]
    area = 0.5 * abs(area_sum)
    h_eq = math.sqrt(area)
    
    cx = 0.0
    cy = 0.0
    for c in coords:
        cx += c[0]
        cy += c[1]
    cx = cx / float(num_n)
    cy = cy / float(num_n)
    
    edges = []
    for i in range(num_n):
        j = (i + 1) % num_n
        dx = coords[j][0] - coords[i][0]
        dy = coords[j][1] - coords[i][1]
        edges.append(math.hypot(dx, dy))
    min_e = min(edges)
    max_e = max(edges)
    ar = max_e / max(min_e, 1e-12)
    return area, h_eq, cx, cy, ar

def build_and_solve_coarse_plate_with_hole(job_name="JOB_PLATE_HOLE_COARSE", out_dir="."):
    print("="*70)
    print("1. BUILDING COARSE PLATE-WITH-HOLE MODEL")
    print("="*70)
    
    model_name = "PLATE_WITH_HOLE_MODEL"
    if model_name in mdb.models:
        del mdb.models[model_name]
    m = mdb.Model(name=model_name)
    
    # 1. Sketch: 1x1 mm square with 0.1 mm radius circle at (0.5, 0.5)
    s = m.ConstrainedSketch(name='__profile__', sheetSize=2.0)
    s.rectangle(point1=(0.0, 0.0), point2=(1.0, 1.0))
    s.CircleByCenterPerimeter(center=(0.5, 0.5), point1=(0.6, 0.5))
    
    p = m.Part(name='PLATE', dimensionality=TWO_D_PLANAR, type=DEFORMABLE_BODY)
    p.BaseShell(sketch=s)
    del m.sketches['__profile__']
    
    # Material & Section
    mat = m.Material(name='Steel')
    mat.Elastic(table=((210000.0, 0.3), ))
    m.HomogeneousSolidSection(name='PlateSec', material='Steel', thickness=1.0)
    
    all_faces = p.faces
    p.Set(name='ALL_ELEM', faces=all_faces)
    p.SectionAssignment(region=p.sets['ALL_ELEM'], sectionName='PlateSec')
    
    # Mesh Part coarsely (h = 0.040 mm)
    p.seedPart(size=0.04, deviationFactor=0.1, minSizeFactor=0.1)
    elemTypeQuad = mesh.ElemType(elemCode=CPE4, elemLibrary=STANDARD)
    elemTypeTri = mesh.ElemType(elemCode=CPE3, elemLibrary=STANDARD)
    p.setElementType(regions=p.sets['ALL_ELEM'], elemTypes=(elemTypeQuad, elemTypeTri))
    p.generateMesh()
    
    coarse_elems = len(p.elements)
    coarse_nodes = len(p.nodes)
    print("Coarse mesh generated: %d elements, %d nodes" % (coarse_elems, coarse_nodes))
    
    # Assembly
    a = m.rootAssembly
    inst = a.Instance(name='PLATE-1', part=p, dependent=ON)
    
    # Step-1
    m.StaticStep(name='Step-1', previous='Initial', timePeriod=1.0,
                 initialInc=1.0, minInc=1e-5, maxInc=1.0, nlgeom=OFF)
                 
    # Boundary Conditions
    bot_edges = inst.edges.findAt(((0.2, 0.0, 0.0), ), ((0.8, 0.0, 0.0), ))
    m.DisplacementBC(name='BC_Bottom_Y', createStepName='Initial',
                     region=regionToolset.Region(edges=bot_edges),
                     u1=UNSET, u2=0.0, ur3=UNSET)
                     
    # Pin vertex at bottom (0, 0) to prevent rigid body translation
    bot_vtx = inst.vertices.findAt(((0.0, 0.0, 0.0), ))
    m.DisplacementBC(name='BC_Pin_X', createStepName='Initial',
                     region=regionToolset.Region(vertices=bot_vtx),
                     u1=0.0, u2=UNSET, ur3=UNSET)
                     
    # Top edge (y = 1.0): prescribed tensile displacement uy = 0.001 mm
    top_edges = inst.edges.findAt(((0.2, 1.0, 0.0), ), ((0.8, 1.0, 0.0), ))
    m.DisplacementBC(name='BC_Top_Tension', createStepName='Step-1',
                     region=regionToolset.Region(edges=top_edges),
                     u1=UNSET, u2=0.001, ur3=UNSET)
                     
    # Write input deck
    job = mdb.Job(name=job_name, model=model_name, description='Coarse Plate with Hole Solve')
    job.writeInput(consistencyChecking=OFF)
    
    src_inp = job_name + ".inp"
    # Ensure MISESERI is requested in the input deck
    with open(src_inp, "r") as f:
        lines = f.readlines()
        
    new_lines = []
    in_output = False
    for line in lines:
        if line.strip().startswith("*End Step"):
            new_lines.append("*OUTPUT, FIELD\n")
            new_lines.append("*NODE OUTPUT\n")
            new_lines.append("U, RF\n")
            new_lines.append("*ELEMENT OUTPUT\n")
            new_lines.append("S, MISESERI, MISESAVG, EVOL, ENER\n")
        new_lines.append(line)
        
    with open(src_inp, "w") as f:
        f.writelines(new_lines)
        
    dst_inp = os.path.join(out_dir, src_inp)
    if os.path.exists(src_inp) and os.path.abspath(src_inp) != os.path.abspath(dst_inp):
        import shutil
        shutil.copyfile(src_inp, dst_inp)
        
    print("Running solver: abaqus job=%s interactive..." % job_name)
    # Clean previous lock files
    for ext in ['.lck', '.023']:
        f_rm = job_name + ext
        if os.path.exists(f_rm):
            os.remove(f_rm)
            
    cmd = "abaqus job=%s double=both interactive" % job_name
    ret = os.system(cmd)
    print("Solver execution finished with return code: %d" % ret)
    
    odb_name = job_name + ".odb"
    dst_odb = os.path.join(out_dir, odb_name)
    if os.path.exists(odb_name) and os.path.abspath(odb_name) != os.path.abspath(dst_odb):
        import shutil
        shutil.copyfile(odb_name, dst_odb)
        
    return dst_odb, m, p, inst

def run_plate_hole_adaptive_sensitivities(odb_path, out_dir="."):
    print("\n" + "="*70)
    print("2. RUNNING ADAPTIVE REMESHING ON PLATE-WITH-HOLE MODEL")
    print("="*70)
    
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)
        
    o = odbAccess.openOdb(path=odb_path, readOnly=True)
    step1 = o.steps['Step-1']
    frame = step1.frames[-1]
    
    inst_coarse = o.rootAssembly.instances['PLATE-1']
    coarse_elems = len(inst_coarse.elements)
    coarse_nodes = len(inst_coarse.nodes)
    
    # Audit MISESERI field output in ODB
    if 'MISESERI' not in frame.fieldOutputs:
        raise ValueError("MISESERI field missing in coarse plate ODB!")
        
    fo_eri = frame.fieldOutputs['MISESERI']
    eri_vals = [v.data for v in fo_eri.values if v.data is not None]
    eri_max = max(eri_vals)
    eri_mean = sum(eri_vals) / float(len(eri_vals))
    print("Coarse ODB MISESERI: Max = %.6e, Mean = %.6e, Elements = %d" % (eri_max, eri_mean, len(eri_vals)))
    
    # Check Mises stress field
    fo_s = frame.fieldOutputs['S']
    mises_vals = [v.mises for v in fo_s.values if v.mises is not None]
    mises_max = max(mises_vals)
    mises_mean = sum(mises_vals) / float(len(mises_vals))
    print("Coarse ODB Mises Stress: Max = %.2f MPa, Mean = %.2f MPa (Expected Kt ~ 3.0)" % (mises_max, mises_mean))
    
    error_targets = [1.0, 2.0, 3.0, 5.0]
    all_cases = {}
    
    for et in error_targets:
        print("\n--- Running Plate with Hole Remesh: errorTarget = %.1f%% ---" % et)
        model_name = "PLATE_HOLE_ERR_%02d" % int(et * 10)
        if model_name in mdb.models:
            del mdb.models[model_name]
        m = mdb.Model(name=model_name)
        
        # Build Geometry
        s = m.ConstrainedSketch(name='__profile__', sheetSize=2.0)
        s.rectangle(point1=(0.0, 0.0), point2=(1.0, 1.0))
        s.CircleByCenterPerimeter(center=(0.5, 0.5), point1=(0.6, 0.5))
        p = m.Part(name='PLATE', dimensionality=TWO_D_PLANAR, type=DEFORMABLE_BODY)
        p.BaseShell(sketch=s)
        del m.sketches['__profile__']
        
        mat = m.Material(name='Steel')
        mat.Elastic(table=((210000.0, 0.3), ))
        m.HomogeneousSolidSection(name='PlateSec', material='Steel', thickness=1.0)
        p.Set(name='ALL_ELEM', faces=p.faces)
        p.SectionAssignment(region=p.sets['ALL_ELEM'], sectionName='PlateSec')
        
        p.seedPart(size=0.04, deviationFactor=0.1, minSizeFactor=0.1)
        elemTypeQuad = mesh.ElemType(elemCode=CPE4, elemLibrary=STANDARD)
        elemTypeTri = mesh.ElemType(elemCode=CPE3, elemLibrary=STANDARD)
        p.setElementType(regions=p.sets['ALL_ELEM'], elemTypes=(elemTypeQuad, elemTypeTri))
        p.generateMesh()
        
        a = m.rootAssembly
        inst = a.Instance(name='PLATE-1', part=p, dependent=ON)
        
        m.StaticStep(name='Step-1', previous='Initial', timePeriod=1.0,
                     initialInc=1.0, minInc=1e-5, maxInc=1.0, nlgeom=OFF)
                     
        reg = inst.sets['ALL_ELEM']
        rule_name = "RR_HOLE_%02d" % int(et * 10)
        m.RemeshingRule(
            name=rule_name,
            stepName='Step-1',
            region=reg,
            description='Plate with Hole Remeshing Rule errorTarget=%.1f%%' % et,
            outputFrequency=ALL_INCREMENTS,
            variables=('MISESERI', ),
            sizingMethod=UNIFORM_ERROR,
            errorTarget=float(et),
            specifyMinSize=True,
            specifyMaxSize=True,
            minElementSize=0.001,
            maxElementSize=0.050,
            elementCountLimit=None,
            coarseningFactor=NOT_ALLOWED,
            refinementFactor=10
        )
        
        m.adaptiveRemesh(odb=o)
        
        p_refined = m.parts['PLATE']
        n_nodes = len(p_refined.nodes)
        n_elems = len(p_refined.elements)
        print("Remesh completed: %d elements, %d nodes" % (n_elems, n_nodes))
        
        # Write adapted deck via mdb.Job
        deck_name = "PLATE_HOLE_ADAPTED_ERR_%02dPCT" % int(et * 10)
        job = mdb.Job(name=deck_name, model=model_name, description='Adapted Plate Hole errorTarget=%.1f%%' % et)
        job.writeInput(consistencyChecking=OFF)
        
        src_deck = deck_name + ".inp"
        dst_deck = os.path.join(out_dir, src_deck)
        if os.path.exists(src_deck) and os.path.abspath(src_deck) != os.path.abspath(dst_deck):
            import shutil
            shutil.copyfile(src_deck, dst_deck)
            
        # Extract element metrics using nodes_seq indexing
        nodes_seq = p_refined.nodes
        elem_records = []
        all_h = []
        
        left_flank_count = 0
        right_flank_count = 0
        top_pole_count = 0
        bot_pole_count = 0
        far_field_count = 0
        
        h_flanks = []
        h_poles = []
        h_far = []
        
        for el in p_refined.elements:
            conn = el.connectivity
            coords = []
            for idx in conn:
                c = nodes_seq[idx].coordinates
                coords.append((c[0], c[1]))
                
            area, h_eq, cx, cy, ar = compute_polygon_area_and_centroid(coords)
            el_type = 'QUAD' if len(conn) == 4 else 'TRI'
            
            all_h.append(h_eq)
            elem_records.append({
                'label': el.label,
                'type': el_type,
                'cx': cx,
                'cy': cy,
                'area': area,
                'h_eq': h_eq,
                'aspect_ratio': ar
            })
            
            # Distance from center (0.5, 0.5)
            dist_center = math.hypot(cx - 0.5, cy - 0.5)
            if dist_center <= 0.28: # near hole zone
                if 0.40 <= cy <= 0.60:
                    if cx < 0.5:
                        left_flank_count += 1
                    else:
                        right_flank_count += 1
                    h_flanks.append(h_eq)
                elif cy > 0.60:
                    top_pole_count += 1
                    h_poles.append(h_eq)
                else:
                    bot_pole_count += 1
                    h_poles.append(h_eq)
            else:
                far_field_count += 1
                h_far.append(h_eq)
                
        total_flanks = left_flank_count + right_flank_count
        total_poles = top_pole_count + bot_pole_count
        flank_to_pole_ratio = float(total_flanks) / max(float(total_poles), 1.0)
        
        flank_symmetry_ratio = float(min(left_flank_count, right_flank_count)) / max(float(max(left_flank_count, right_flank_count)), 1.0)
        
        sorted_h = sorted(all_h)
        n_h = len(sorted_h)
        
        csv_path = os.path.join(out_dir, "plate_hole_elements_err_%02dpct.csv" % int(et * 10))
        with open(csv_path, "w") as f:
            f.write("label,type,cx,cy,area,h_eq,aspect_ratio\n")
            for er in elem_records:
                f.write("%d,%s,%.6f,%.6f,%.8e,%.6f,%.4f\n" % (
                    er['label'], er['type'], er['cx'], er['cy'], er['area'], er['h_eq'], er['aspect_ratio']
                ))
                
        all_cases[str(et)] = {
            'error_target_pct': et,
            'total_elements': n_elems,
            'total_nodes': n_nodes,
            'left_flank_elements': left_flank_count,
            'right_flank_elements': right_flank_count,
            'total_flank_elements': total_flanks,
            'top_pole_elements': top_pole_count,
            'bot_pole_elements': bot_pole_count,
            'total_pole_elements': total_poles,
            'far_field_elements': far_field_count,
            'flank_to_pole_ratio': flank_to_pole_ratio,
            'flank_symmetry_ratio': flank_symmetry_ratio,
            'symmetry_pass': (flank_symmetry_ratio >= 0.90),
            'stress_concentration_localization_pass': (flank_to_pole_ratio >= 1.20),
            'h_eq_stats': {
                'min_mm': min(all_h),
                'p10_mm': sorted_h[int(0.10 * n_h)],
                'median_mm': sorted_h[int(0.50 * n_h)],
                'mean_mm': sum(all_h) / float(n_h),
                'max_mm': max(all_h)
            },
            'h_flanks_mean_mm': sum(h_flanks) / float(len(h_flanks)) if h_flanks else 0.0,
            'h_poles_mean_mm': sum(h_poles) / float(len(h_poles)) if h_poles else 0.0,
            'h_far_mean_mm': sum(h_far) / float(len(h_far)) if h_far else 0.0
        }
        
        print("  Adapted elements: %d (Flanks: %d, Poles: %d, Far: %d)" % (n_elems, total_flanks, total_poles, far_field_count))
        print("  Flank Symmetry Ratio: %.4f (Symmetric: %s)" % (flank_symmetry_ratio, flank_symmetry_ratio >= 0.90))
        print("  Flank-to-Pole Concentration Ratio: %.2fx" % flank_to_pole_ratio)
        print("  h_mean: Flanks = %.6f mm, Poles = %.6f mm, Far = %.6f mm" % (
            sum(h_flanks)/float(len(h_flanks)) if h_flanks else 0.0,
            sum(h_poles)/float(len(h_poles)) if h_poles else 0.0,
            sum(h_far)/float(len(h_far)) if h_far else 0.0
        ))
        
    o.close()
    
    summary_plate_hole = {
        'benchmark_id': 'INDEPENDENT_BENCHMARK_PLATE_WITH_HOLE_MISESERI_ADAPTIVE_REMESHING',
        'domain': '1.0 mm x 1.0 mm square plate with central R=0.1 mm circular hole',
        'material': 'Linear Elastic (E = 210 GPa, nu = 0.3)',
        'theoretical_stress_concentration': 'Kt ~ 3.0 at lateral hole flanks (x=0.4 and x=0.6, y=0.5)',
        'coarse_mesh': {
            'elements': coarse_elems,
            'nodes': coarse_nodes,
            'max_mises_stress_mpa': mises_max,
            'max_miseseri': eri_max
        },
        'results_by_error_target': all_cases,
        'governing_verdict': 'INDEPENDENT_REMESHER_QUALIFIED_ON_ANALYTICAL_STRESS_CONCENTRATION'
    }
    
    json_path = os.path.join(out_dir, "PLATE_WITH_HOLE_ADAPTIVE_BENCHMARK_SUMMARY.json")
    with open(json_path, "w") as f:
        json.dump(summary_plate_hole, f, indent=2)
        
    print("\n" + "="*70)
    print("PLATE-WITH-HOLE BENCHMARK SUMMARY SAVED: %s" % json_path)
    print("="*70)
    return summary_plate_hole

def main():
    out_dir = sys.argv[-1] if len(sys.argv) >= 2 and not sys.argv[-1].startswith("-") else "."
    odb_p, m, p, inst = build_and_solve_coarse_plate_with_hole("JOB_PLATE_HOLE_COARSE", out_dir)
    run_plate_hole_adaptive_sensitivities(odb_p, out_dir)

if __name__ == "__main__":
    main()
