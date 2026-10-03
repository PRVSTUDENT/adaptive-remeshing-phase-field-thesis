# -*- coding: utf-8 -*-
from __future__ import print_function
import sys
import os
import json
import math

import odbAccess
from abaqus import mdb
from abaqusConstants import (
    TWO_D_PLANAR, DEFORMABLE_BODY, STANDARD, CPE4, CPE3, ON, OFF,
    MODEL, UNIFORM_ERROR, NOT_ALLOWED, ALL_INCREMENTS, ADVANCING_FRONT, QUAD_DOMINATED, FREE
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

def execute_stage11_diagnostic(odb_path, out_dir="."):
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)
        
    print("="*70)
    print("STAGE 11: CONTROLLED MESH-CONTROL DIAGNOSTIC (minTransition=OFF)")
    print("="*70)
    print("Opening ODB: %s" % odb_path)
    
    o = odbAccess.openOdb(path=odb_path, readOnly=True)
    step1 = o.steps['Step-1']
    frame_last = step1.frames[-1]
    print("Step-1 total frames: %d, final frameValue: %.6f" % (len(step1.frames), frame_last.frameValue))
    
    model_name = "PK_M1_STAGE11_MINTRANS_OFF_CAD"
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
    
    p.Set(name='ALL_ELEM', faces=p.faces)
    
    mat = m.Material(name='Steel')
    mat.Elastic(table=((210000.0, 0.3), ))
    m.HomogeneousSolidSection(name='SolidSec', material='Steel', thickness=1.0)
    p.SectionAssignment(region=p.sets['ALL_ELEM'], sectionName='SolidSec')
    
    # Apply single intended change: minTransition = OFF
    p.setMeshControls(regions=p.faces, elemShape=QUAD_DOMINATED, technique=FREE, algorithm=ADVANCING_FRONT, minTransition=OFF)
    
    p.seedPart(size=0.02, deviationFactor=0.1, minSizeFactor=0.1)
    elemTypeQuad = mesh.ElemType(elemCode=CPE4, elemLibrary=STANDARD)
    elemTypeTri = mesh.ElemType(elemCode=CPE3, elemLibrary=STANDARD)
    p.setElementType(regions=p.sets['ALL_ELEM'], elemTypes=(elemTypeQuad, elemTypeTri))
    p.generateMesh()
    
    coarse_nodes = len(p.nodes)
    coarse_elems = len(p.elements)
    print("Geometry-backed Part Coarse Mesh generated: %d elements, %d nodes" % (coarse_elems, coarse_nodes))
    
    a = m.rootAssembly
    inst = a.Instance(name='PART-1-1', part=p, dependent=ON)
    m.StaticStep(name='Step-1', previous='Initial', timePeriod=1.0, nlgeom=OFF)
    reg = inst.sets['ALL_ELEM']
    
    m.RemeshingRule(
        name='PK_M1_STAGE11_RR',
        stepName='Step-1',
        region=reg,
        description='Stage 11 Native 1% Remeshing Rule with minTransition=OFF (errorTarget=1.0%)',
        outputFrequency=ALL_INCREMENTS,
        variables=('MISESERI', ),
        sizingMethod=UNIFORM_ERROR,
        errorTarget=1.0,
        specifyMinSize=True,
        specifyMaxSize=True,
        minElementSize=0.001,
        maxElementSize=0.020,
        elementCountLimit=None,
        coarseningFactor=NOT_ALLOWED,
        refinementFactor=10
    )
    
    print("Calling m.adaptiveRemesh(odb=o)...")
    m.adaptiveRemesh(odb=o)
    o.close()
    print("adaptiveRemesh call completed successfully!")
    
    p_refined = m.parts['PART-1']
    refined_nodes_count = len(p_refined.nodes)
    refined_elems_count = len(p_refined.elements)
    print("Adapted Mesh Generated: %d elements, %d nodes" % (refined_elems_count, refined_nodes_count))
    
    nodes_seq = p_refined.nodes
    elem_records = []
    
    corridor_count = 0
    upper_far_count = 0
    lower_far_count = 0
    wake_count = 0
    ligament_count = 0
    h_corridor = []
    h_far = []
    all_h = []
    
    for e in p_refined.elements:
        conn = e.connectivity
        coords = []
        for idx in conn:
            c = nodes_seq[idx].coordinates
            coords.append((c[0], c[1]))
        num_n = len(coords)
        
        area, h_eq, cx, cy, ar = compute_polygon_area_and_centroid(coords)
        all_h.append(h_eq)
        
        if 0.45 <= cy <= 0.55:
            corridor_count += 1
            h_corridor.append(h_eq)
            if cx <= 0.5:
                wake_count += 1
            else:
                ligament_count += 1
        elif cy > 0.55:
            upper_far_count += 1
            h_far.append(h_eq)
        else:
            lower_far_count += 1
            h_far.append(h_eq)
            
        elem_records.append({
            'label': e.label,
            'type': 'CPE4' if num_n == 4 else 'CPE3',
            'cx': cx,
            'cy': cy,
            'area': area,
            'h_eq': h_eq,
            'aspect_ratio': ar
        })
        
    far_field_total = upper_far_count + lower_far_count
    corridor_fraction = float(corridor_count) / float(refined_elems_count)
    far_field_fraction = float(far_field_total) / float(refined_elems_count)
    
    x_slices = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
    band_widths = {}
    for xs in x_slices:
        slice_elems = [er for er in elem_records if abs(er['cx'] - xs) <= 0.03 and er['h_eq'] <= 0.005]
        if slice_elems:
            y_min = min([er['cy'] for er in slice_elems])
            y_max = max([er['cy'] for er in slice_elems])
            band_widths[str(xs)] = {
                'count': len(slice_elems),
                'y_min': y_min,
                'y_max': y_max,
                'width_mm': y_max - y_min
            }
        else:
            band_widths[str(xs)] = {'count': 0, 'width_mm': 0.0}
            
    fine_elems = [er for er in elem_records if er['h_eq'] <= 0.003]
    if fine_elems:
        bbox_fine = {
            'count': len(fine_elems),
            'x_min': min([er['cx'] for er in fine_elems]),
            'x_max': max([er['cx'] for er in fine_elems]),
            'y_min': min([er['cy'] for er in fine_elems]),
            'y_max': max([er['cy'] for er in fine_elems])
        }
    else:
        bbox_fine = {'count': 0}
        
    coarse_remaining = [er for er in elem_records if er['h_eq'] >= 0.015]
    
    deck_name = "PK_M1_STAGE11_MINTRANS_OFF_1PCT"
    j_raw = mdb.Job(name=deck_name, model=model_name, description='Stage 11 Native 1% Refined Model with minTransition=OFF')
    j_raw.writeInput(consistencyChecking=OFF)
    
    src_deck = deck_name + ".inp"
    dst_deck = os.path.join(out_dir, src_deck)
    if os.path.exists(src_deck) and os.path.abspath(src_deck) != os.path.abspath(dst_deck):
        import shutil
        shutil.move(src_deck, dst_deck)
        
    csv_path = os.path.join(out_dir, "stage11_mintrans_off_elements.csv")
    with open(csv_path, "w") as f:
        f.write("label,type,cx,cy,area,h_eq,aspect_ratio\n")
        for er in elem_records:
            f.write("%d,%s,%.6f,%.6f,%.8e,%.6f,%.4f\n" % (
                er['label'], er['type'], er['cx'], er['cy'], er['area'], er['h_eq'], er['aspect_ratio']
            ))
            
    sorted_h = sorted(all_h)
    n_h = len(sorted_h)
    
    summary = {
        'audit_id': 'GATE6B-STAGE11-MINTRANS-OFF-DIAGNOSTIC-20261003',
        'preanalysis_odb': odb_path,
        'caller_frame': 'Step-1 frame_last (u=0.005 mm)',
        'mesh_controls': {
            'minTransition': 'OFF',
            'algorithm': 'ADVANCING_FRONT',
            'technique': 'FREE',
            'elemShape': 'QUAD_DOMINATED'
        },
        'sizing_contract': {
            'error_target_pct': 1.0,
            'sizing_method': 'UNIFORM_ERROR',
            'refinement_factor': 10,
            'coarsening_factor': 'NOT_ALLOWED',
            'min_element_size_mm': 0.001,
            'max_element_size_mm': 0.020,
            'region': 'ALL_ELEM'
        },
        'adapted_mesh': {
            'total_elements': refined_elems_count,
            'total_nodes': refined_nodes_count,
            'h_eq_stats': {
                'min': min(all_h),
                'p10': sorted_h[int(0.10*n_h)],
                'p25': sorted_h[int(0.25*n_h)],
                'median': sorted_h[int(0.50*n_h)],
                'mean': sum(all_h)/float(n_h),
                'p75': sorted_h[int(0.75*n_h)],
                'p90': sorted_h[int(0.90*n_h)],
                'max': max(all_h)
            }
        },
        'spatial_morphology': {
            'crack_corridor_count': corridor_count,
            'crack_corridor_fraction': corridor_fraction,
            'wake_count': wake_count,
            'ligament_count': ligament_count,
            'upper_far_field_count': upper_far_count,
            'lower_far_field_count': lower_far_count,
            'far_field_total_count': far_field_total,
            'far_field_fraction': far_field_fraction,
            'h_corridor_median_mm': sorted(h_corridor)[int(0.50*len(h_corridor))] if h_corridor else 0.0,
            'h_corridor_min_mm': min(h_corridor) if h_corridor else 0.0,
            'h_far_median_mm': sorted(h_far)[int(0.50*len(h_far))] if h_far else 0.0,
            'h_far_min_mm': min(h_far) if h_far else 0.0,
            'elements_near_nominal_h002_count': len(coarse_remaining),
            'refined_bbox_h003': bbox_fine,
            'refined_band_widths_by_x': band_widths
        },
        'comparison_vs_baseline_stage10': {
            'baseline_stage10_elements': 57929,
            'mintrans_off_elements': refined_elems_count,
            'element_difference': refined_elems_count - 57929,
            'far_field_fraction_stage10': 0.854391,
            'far_field_fraction_mintrans_off': far_field_fraction
        },
        'classification': 'MESH_CONTROL_NO_MEANINGFUL_IMPROVEMENT' if abs(corridor_fraction - 0.1456) < 0.05 else ('MESH_CONTROL_TOWARD_TARGET_LOCALIZATION' if corridor_fraction > 0.30 else 'MESH_CONTROL_AWAY_FROM_TARGET_LOCALIZATION')
    }
    
    json_path = os.path.join(out_dir, "STAGE11_MINTRANS_OFF_SUMMARY.json")
    with open(json_path, "w") as f:
        json.dump(summary, f, indent=2)
        
    print("="*70)
    print("STAGE 11 SUMMARY (minTransition=OFF):")
    print("  Adapted Element Count: %d (Nodes: %d)" % (refined_elems_count, refined_nodes_count))
    print("  Corridor Elements: %d (%.2f%%)" % (corridor_count, corridor_fraction*100.0))
    print("  Far Field Elements: %d (%.2f%%)" % (far_field_total, far_field_fraction*100.0))
    print("  Classification: %s" % summary['classification'])
    print("="*70)
    return summary

if __name__ == "__main__":
    odb_p = "/home/pr21vyci/projects/adaptive-remeshing/models/pandey_kumar_mode1/93_mode1_preanalysis_inf_companion_2906/PK_M1_JOB1_INF_COMPANION_2906.odb"
    out_d = "/home/pr21vyci/projects/adaptive-remeshing/models/pandey_kumar_mode1/97_mode1_stage11_min_transition_diagnostic"
    execute_stage11_diagnostic(odb_p, out_d)
