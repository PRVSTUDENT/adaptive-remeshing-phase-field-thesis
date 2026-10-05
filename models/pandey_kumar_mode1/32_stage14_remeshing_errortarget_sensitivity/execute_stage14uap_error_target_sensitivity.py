# -*- coding: utf-8 -*-
"""
Gate-6B Stage 14U-AP: Native Remeshing ErrorTarget Spatial Sensitivity Analysis (1, 2, 3, 5%).
Runs native Abaqus mdb.models[model].adaptiveRemesh(odb) on the final Stage-14 pre-analysis ODB
(PK_M1_JOB1_INF_COMPANION_2906.odb) for errorTarget in [1.0, 2.0, 3.0, 5.0]%.

Parameters kept identical across all 4 runs:
- Sizing method: UNIFORM_ERROR
- Refinement factor: 10
- Coarsening factor: NOT_ALLOWED
- Min element size: 0.001 mm (specifyMinSize=True)
- Max element size: 0.020 mm (specifyMaxSize=True)
- Region: ALL_ELEM
- Frame: Step-1 final frame (u = 0.005 mm)
- Element Code: CPE4 / CPE3
"""
from __future__ import print_function
import sys
import os
import json
import math

import odbAccess
from abaqus import mdb
from abaqusConstants import (
    TWO_D_PLANAR, DEFORMABLE_BODY, STANDARD, CPE4, CPE3, ON, OFF,
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

def run_single_errortarget_remesh(odb_path, error_target_pct, out_dir):
    print("\n" + "="*70)
    print("RUNNING NATIVE REMESH: errorTarget = %.1f%%" % error_target_pct)
    print("="*70)
    
    # 1. Open ODB
    o = odbAccess.openOdb(path=odb_path, readOnly=True)
    step1 = o.steps['Step-1']
    frame_last = step1.frames[-1]
    
    # 2. Build CAD Geometry Model in CAE
    model_name = "PK_M1_CAD_ERR_%02d" % int(error_target_pct * 10)
    if model_name in mdb.models:
        del mdb.models[model_name]
    m = mdb.Model(name=model_name)
    
    s = m.ConstrainedSketch(name='__profile__', sheetSize=2.0)
    s.rectangle(point1=(0.0, 0.0), point2=(1.0, 1.0))
    p = m.Part(name='PART-1', dimensionality=TWO_D_PLANAR, type=DEFORMABLE_BODY)
    p.BaseShell(sketch=s)
    del m.sketches['__profile__']
    
    # Partition crack seam y=0.5, 0 <= x <= 0.5
    p.PartitionFaceByShortestPath(faces=p.faces, point1=(0.0, 0.5, 0.0), point2=(0.5, 0.5, 0.0))
    seam_edge = p.edges.findAt(((0.25, 0.5, 0.0), ))
    p.engineeringFeatures.assignSeam(regions=regionToolset.Region(edges=seam_edge))
    
    # Element Sets
    p.Set(name='ALL_ELEM', faces=p.faces)
    p.Set(name='UMATELEM', faces=p.faces)
    
    # Material & Section Assignment
    mat = m.Material(name='Steel')
    mat.Elastic(table=((210000.0, 0.3), ))
    m.HomogeneousSolidSection(name='SolidSec', material='Steel', thickness=1.0)
    p.SectionAssignment(region=p.sets['ALL_ELEM'], sectionName='SolidSec')
    
    # Coarse Mesh Generation (nominal h = 0.020 mm)
    p.seedPart(size=0.02, deviationFactor=0.1, minSizeFactor=0.1)
    elemTypeQuad = mesh.ElemType(elemCode=CPE4, elemLibrary=STANDARD)
    elemTypeTri = mesh.ElemType(elemCode=CPE3, elemLibrary=STANDARD)
    p.setElementType(regions=p.sets['ALL_ELEM'], elemTypes=(elemTypeQuad, elemTypeTri))
    p.generateMesh()
    
    coarse_nodes = len(p.nodes)
    coarse_elems = len(p.elements)
    print("Coarse mesh generated: %d elements, %d nodes" % (coarse_elems, coarse_nodes))
    
    # Assembly instance
    a = m.rootAssembly
    inst = a.Instance(name='PART-1-1', part=p, dependent=ON)
    
    # Step-1 matching ODB
    m.StaticStep(name='Step-1', previous='Initial', timePeriod=1.0,
                 initialInc=0.002, minInc=1e-9, maxInc=0.002, nlgeom=OFF)
                 
    reg = inst.sets['ALL_ELEM']
    
    # Remeshing Rule with exact Abaqus keywords
    rule_name = "RR_ERR_%02d" % int(error_target_pct * 10)
    m.RemeshingRule(
        name=rule_name,
        stepName='Step-1',
        region=reg,
        description='Native Remeshing Rule errorTarget=%.1f%%' % error_target_pct,
        outputFrequency=ALL_INCREMENTS,
        variables=('MISESERI', ),
        sizingMethod=UNIFORM_ERROR,
        errorTarget=float(error_target_pct),
        specifyMinSize=True,
        specifyMaxSize=True,
        minElementSize=0.001,
        maxElementSize=0.020,
        elementCountLimit=None,
        coarseningFactor=NOT_ALLOWED,
        refinementFactor=10
    )
    
    # Execute native adaptive remesh
    print("Executing native m.adaptiveRemesh(odb=o)... for errorTarget=%.1f%%" % error_target_pct)
    m.adaptiveRemesh(odb=o)
    o.close()
    
    p_refined = m.parts['PART-1']
    refined_nodes_count = len(p_refined.nodes)
    refined_elems_count = len(p_refined.elements)
    print("Native remesh complete: %d elements, %d nodes" % (refined_elems_count, refined_nodes_count))
    
    # Write native adapted input deck via mdb.Job
    deck_name = "PK_M1_STAGE14UAP_ERR_%02dPCT" % int(error_target_pct * 10)
    job = mdb.Job(name=deck_name, model=model_name, description='Adapted Deck errorTarget=%.1f%%' % error_target_pct)
    job.writeInput(consistencyChecking=OFF)
    
    src_deck = deck_name + ".inp"
    dst_deck = os.path.join(out_dir, src_deck)
    if os.path.exists(src_deck) and os.path.abspath(src_deck) != os.path.abspath(dst_deck):
        import shutil
        shutil.move(src_deck, dst_deck)
        
    # Analyze spatial morphology of the adapted mesh
    nodes_seq = p_refined.nodes
    elem_records = []
    all_h = []
    corridor_count = 0
    wake_count = 0
    ligament_count = 0
    upper_far_count = 0
    lower_far_count = 0
    
    h_corridor = []
    h_far = []
    
    fine_x = []
    fine_y = []
    
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
        
        # Spatial classification
        in_corridor = (0.45 <= cy <= 0.55)
        if in_corridor:
            corridor_count += 1
            h_corridor.append(h_eq)
            if cx < 0.50:
                wake_count += 1
            else:
                ligament_count += 1
        else:
            h_far.append(h_eq)
            if cy > 0.55:
                upper_far_count += 1
            else:
                lower_far_count += 1
                
        # Fine elements footprint (h_eq <= 0.0075 mm, i.e. <= l_0)
        if h_eq <= 0.0075:
            fine_x.append(cx)
            fine_y.append(cy)

    far_field_total = upper_far_count + lower_far_count
    corridor_fraction = float(corridor_count) / float(refined_elems_count)
    far_field_fraction = float(far_field_total) / float(refined_elems_count)
    
    centroid_fine_x = sum(fine_x) / float(len(fine_x)) if fine_x else 0.5
    centroid_fine_y = sum(fine_y) / float(len(fine_y)) if fine_y else 0.5
    
    sorted_h = sorted(all_h)
    n_h = len(sorted_h)
    
    # Save CSV
    csv_path = os.path.join(out_dir, "elements_err_%02dpct.csv" % int(error_target_pct * 10))
    with open(csv_path, "w") as f:
        f.write("label,type,cx,cy,area,h_eq,aspect_ratio\n")
        for er in elem_records:
            f.write("%d,%s,%.6f,%.6f,%.8e,%.6f,%.4f\n" % (
                er['label'], er['type'], er['cx'], er['cy'], er['area'], er['h_eq'], er['aspect_ratio']
            ))
            
    summary_case = {
        'error_target_pct': error_target_pct,
        'deck_file': dst_deck,
        'csv_file': csv_path,
        'total_elements': refined_elems_count,
        'total_nodes': refined_nodes_count,
        'corridor_elements': corridor_count,
        'corridor_fraction': corridor_fraction,
        'ligament_elements': ligament_count,
        'wake_elements': wake_count,
        'far_field_elements': far_field_total,
        'far_field_fraction': far_field_fraction,
        'fine_elements_l0_count': len(fine_x),
        'fine_centroid_x': centroid_fine_x,
        'fine_centroid_y': centroid_fine_y,
        'h_eq_stats': {
            'min_mm': min(all_h),
            'p10_mm': sorted_h[int(0.10 * n_h)],
            'p25_mm': sorted_h[int(0.25 * n_h)],
            'median_mm': sorted_h[int(0.50 * n_h)],
            'mean_mm': sum(all_h) / float(n_h),
            'p75_mm': sorted_h[int(0.75 * n_h)],
            'p90_mm': sorted_h[int(0.90 * n_h)],
            'max_mm': max(all_h)
        },
        'corridor_h_stats': {
            'min_mm': min(h_corridor) if h_corridor else 0.0,
            'median_mm': sorted(h_corridor)[int(0.50 * len(h_corridor))] if h_corridor else 0.0,
            'mean_mm': sum(h_corridor) / float(len(h_corridor)) if h_corridor else 0.0
        },
        'far_h_stats': {
            'min_mm': min(h_far) if h_far else 0.0,
            'median_mm': sorted(h_far)[int(0.50 * len(h_far))] if h_far else 0.0,
            'mean_mm': sum(h_far) / float(len(h_far)) if h_far else 0.0
        }
    }
    
    print("Summary for errorTarget = %.1f%%:" % error_target_pct)
    print("  Total elements: %d (Nodes: %d)" % (refined_elems_count, refined_nodes_count))
    print("  Corridor elements: %d (%.2f%%)" % (corridor_count, corridor_fraction * 100.0))
    print("  Far field elements: %d (%.2f%%)" % (far_field_total, far_field_fraction * 100.0))
    print("  Fine centroid: (cx=%.4f, cy=%.4f)" % (centroid_fine_x, centroid_fine_y))
    print("  h_min = %.6f mm, h_median = %.6f mm, h_max = %.6f mm" % (min(all_h), sorted_h[int(0.50 * n_h)], max(all_h)))
    return summary_case

def execute_all_sensitivities(odb_path, out_dir="."):
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)
        
    error_targets = [1.0, 2.0, 3.0, 5.0]
    all_results = {}
    
    for et in error_targets:
        res = run_single_errortarget_remesh(odb_path, et, out_dir)
        all_results[str(et)] = res
        
    summary_master = {
        'audit_id': 'GATE6B-STAGE14UAP-ERRORTARGET-SENSITIVITY-20261005',
        'preanalysis_odb': odb_path,
        'error_targets_tested': error_targets,
        'results_by_error_target': all_results,
        'status': 'STAGE14UAP_ERRORTARGET_SENSITIVITY_COMPLETED'
    }
    
    json_path = os.path.join(out_dir, "MODE1_STAGE14UAP_ERRORTARGET_SENSITIVITY_SUMMARY.json")
    with open(json_path, "w") as f:
        json.dump(summary_master, f, indent=2)
        
    print("\n" + "="*70)
    print("MASTER SENSITIVITY SUMMARY SAVED: %s" % json_path)
    print("="*70)
    return summary_master

if __name__ == "__main__":
    if '--' in sys.argv:
        idx = sys.argv.index('--')
        user_args = sys.argv[idx+1:]
        odb_p = user_args[0] if len(user_args) >= 1 else "PK_M1_JOB1_INF_COMPANION_2906.odb"
        out_d = user_args[1] if len(user_args) >= 2 else "."
    else:
        odb_p = sys.argv[-2] if len(sys.argv) >= 3 else "PK_M1_JOB1_INF_COMPANION_2906.odb"
        out_d = sys.argv[-1] if len(sys.argv) >= 3 else "."
    execute_all_sensitivities(odb_p, out_d)
