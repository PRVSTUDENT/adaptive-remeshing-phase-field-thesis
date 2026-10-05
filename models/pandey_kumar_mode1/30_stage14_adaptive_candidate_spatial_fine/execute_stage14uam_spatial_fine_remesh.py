# -*- coding: utf-8 -*-
"""
Gate-6B Stage 14U-AM: Native Adaptive Remeshing with Controlled Spatial Sizing.
Executes native mdb.models[model].adaptiveRemesh(odb) using publication-faithful sizing parameters:
- sizingMethod = UNIFORM_ERROR
- errorTarget = 1.0% (frozen)
- refinementFactor = 10 (frozen)
- coarseningFactor = NOT_ALLOWED (frozen)
- minElementSize = 0.0005 mm (0.5 um, factor-of-2 refinement from baseline 0.001 mm)
- maxElementSize = 0.020 mm (frozen)
- region = ALL_ELEM (companion layer, frozen)
- frame = Step-1 final frame at u = 0.005 mm (PROJECT_CONTROLLED_FRAME, frozen)
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
    MODEL, UNIFORM_ERROR, NOT_ALLOWED, ALL_INCREMENTS
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

def execute_stage14uam_remesh(odb_path, out_dir="."):
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)
        
    print("="*70)
    print("STAGE 14U-AM: NATIVE ADAPTIVE REMESHING WITH MIN_ELEMENT_SIZE = 0.0005 MM")
    print("="*70)
    print("Opening ODB: %s" % odb_path)
    
    # 1. Open ODB and verify field outputs
    o = odbAccess.openOdb(path=odb_path, readOnly=True)
    
    if 'Step-1' not in o.steps:
        raise ValueError("Step-1 not found in ODB: %s" % odb_path)
        
    step1 = o.steps['Step-1']
    frame_last = step1.frames[-1]
    print("Step-1 total frames: %d, final frameValue (time/disp): %.6f" % (len(step1.frames), frame_last.frameValue))
    
    if 'MISESERI' not in frame_last.fieldOutputs:
        raise ValueError("MISESERI field output missing from Step-1 final frame in ODB!")
        
    fo_eri = frame_last.fieldOutputs['MISESERI']
    eri_values = [v.data for v in fo_eri.values if v.data is not None]
    eri_max = max(eri_values)
    eri_min = min(eri_values)
    eri_mean = sum(eri_values) / float(len(eri_values))
    total_odb_elements = len(eri_values)
    
    print("ODB Field Check (Package 93 Infinitesimal Companion):")
    print("  Total elements with MISESERI: %d" % total_odb_elements)
    print("  Peak MISESERI: %.6e" % eri_max)
    print("  Min MISESERI:  %.6e" % eri_min)
    print("  Mean MISESERI: %.6e" % eri_mean)
    
    # 2. Build CAD Geometry Model in CAE
    model_name = "PK_M1_STAGE14AM_CAD"
    if model_name in mdb.models:
        del mdb.models[model_name]
    m = mdb.Model(name=model_name)
    
    # 1.0 x 1.0 mm square sketch
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
    print("Geometry-backed Part Coarse Mesh generated: %d elements, %d nodes" % (coarse_elems, coarse_nodes))
    
    # Assembly instance
    a = m.rootAssembly
    inst = a.Instance(name='PART-1-1', part=p, dependent=ON)
    
    # Step-1 matching ODB
    m.StaticStep(name='Step-1', previous='Initial', timePeriod=1.0,
                 initialInc=0.002, minInc=1e-9, maxInc=0.002, nlgeom=OFF)
                 
    reg = inst.sets['ALL_ELEM']
    
    # Remeshing Rule: Controlled Spatial Sizing with minElementSize=0.0005 mm
    m.RemeshingRule(
        name='PK_M1_STAGE14AM_RR',
        stepName='Step-1',
        region=reg,
        description='Stage 14U-AM Controlled Spatial Sizing (minElementSize=0.0005 mm, errorTarget=1.0%)',
        outputFrequency=ALL_INCREMENTS,
        variables=('MISESERI', ),
        sizingMethod=UNIFORM_ERROR,
        errorTarget=1.0,
        specifyMinSize=True,
        specifyMaxSize=True,
        minElementSize=0.0005,
        maxElementSize=0.020,
        elementCountLimit=None,
        coarseningFactor=NOT_ALLOWED,
        refinementFactor=10
    )
    print("Created RemeshingRule on ALL_ELEM: errorTarget=1.0%, refFactor=10, h in [0.0005, 0.020] mm")
    
    # 3. Execute Native adaptiveRemesh
    print("Calling m.adaptiveRemesh(odb=o)...")
    m.adaptiveRemesh(odb=o)
    o.close()
    print("adaptiveRemesh call completed successfully!")
    
    # 4. Extract Refined Mesh Telemetry
    p_refined = m.parts['PART-1']
    refined_nodes_count = len(p_refined.nodes)
    refined_elems_count = len(p_refined.elements)
    print("Adapted Mesh Generated: %d elements, %d nodes" % (refined_elems_count, refined_nodes_count))
    
    # 5. Detailed Spatial Morphology Analysis
    nodes_seq = p_refined.nodes
    elem_records = []
    
    corridor_count = 0
    upper_far_count = 0
    lower_far_count = 0
    wake_count = 0
    ligament_count = 0
    
    quad_count = 0
    tri_count = 0
    
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
        if num_n == 4:
            quad_count += 1
            etype = 'CPE4'
        else:
            tri_count += 1
            etype = 'CPE3'
            
        area, h_eq, cx, cy, ar = compute_polygon_area_and_centroid(coords)
        all_h.append(h_eq)
        
        # Regional classification:
        # Corridor: y in [0.45, 0.55]
        # Upper far field: y > 0.55
        # Lower far field: y < 0.45
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
            'type': etype,
            'cx': cx,
            'cy': cy,
            'area': area,
            'h_eq': h_eq,
            'aspect_ratio': ar
        })
        
    far_field_total = upper_far_count + lower_far_count
    corridor_fraction = float(corridor_count) / float(refined_elems_count)
    far_field_fraction = float(far_field_total) / float(refined_elems_count)
    
    # Seam verification: find duplicate nodes along seam y=0.5, 0 <= x <= 0.5
    seam_nodes = []
    for nid, node in enumerate(nodes_seq):
        c = node.coordinates
        if abs(c[1] - 0.5) < 1e-6 and c[0] <= 0.500001:
            seam_nodes.append((nid, node.label, c[0], c[1]))
            
    # Group by x coordinate
    seam_pairs = []
    tip_nodes = []
    x_map = {}
    for sn in seam_nodes:
        x_val = round(sn[2], 6)
        if x_val not in x_map:
            x_map[x_val] = []
        x_map[x_val].append(sn)
        
    num_pairs = 0
    num_singletons = 0
    for x_val, nlist in sorted(x_map.items()):
        if len(nlist) == 2:
            num_pairs += 1
            seam_pairs.append({'x': x_val, 'node1': nlist[0][1], 'node2': nlist[1][1]})
        elif len(nlist) == 1:
            num_singletons += 1
            tip_nodes.append({'x': x_val, 'node': nlist[0][1]})
            
    print("Seam Verification:")
    print("  Duplicate pairs along seam: %d" % num_pairs)
    print("  Singletons (tip/boundary): %d" % num_singletons)
    
    # 6. Export Raw Input Deck
    deck_name = "PK_M1_STAGE14AM_RAW"
    j_raw = mdb.Job(name=deck_name, model=model_name, description='Stage 14U-AM Native Finer Sized Model from Inf-Companion ODB')
    j_raw.writeInput(consistencyChecking=OFF)
    
    src_deck = deck_name + ".inp"
    dst_deck = os.path.join(out_dir, src_deck)
    if os.path.exists(src_deck) and os.path.abspath(src_deck) != os.path.abspath(dst_deck):
        import shutil
        shutil.move(src_deck, dst_deck)
        
    # 7. Save element metrics CSV and summary JSON
    csv_path = os.path.join(out_dir, "stage14am_adapted_elements.csv")
    with open(csv_path, "w") as f:
        f.write("label,type,cx,cy,area,h_eq,aspect_ratio\n")
        for er in elem_records:
            f.write("%d,%s,%.6f,%.6f,%.8e,%.6f,%.4f\n" % (
                er['label'], er['type'], er['cx'], er['cy'], er['area'], er['h_eq'], er['aspect_ratio']
            ))
            
    sorted_h = sorted(all_h)
    n_h = len(sorted_h)
    l0 = 0.0075 # mm
    
    h_min = min(all_h)
    h_median = sorted_h[int(0.50*n_h)]
    h_mean = sum(all_h)/float(n_h)
    
    # Localization Classification
    # Baseline Stage 14 had 57.57% corridor fraction
    # With minElementSize=0.0005, elements in corridor increase significantly
    if corridor_fraction > 0.50:
        localization_class = "TOWARD_TARGET_LOCALIZATION"
    else:
        localization_class = "DIFFUSE_REFINEMENT"
        
    summary = {
        'audit_id': 'GATE6B-STAGE14UAM-CONTROLLED-SPATIAL-CONVERGENCE-20261004',
        'preanalysis_odb': odb_path,
        'caller_frame': 'Step-1 frame_last (u=0.005 mm, PROJECT_CONTROLLED_FRAME)',
        'sizing_contract': {
            'error_target_pct': 1.0,
            'sizing_method': 'UNIFORM_ERROR',
            'refinement_factor': 10,
            'coarsening_factor': 'NOT_ALLOWED',
            'min_element_size_mm': 0.0005,
            'max_element_size_mm': 0.020,
            'region': 'ALL_ELEM (companion layer)'
        },
        'coarse_mesh': {
            'total_elements': coarse_elems,
            'total_nodes': coarse_nodes
        },
        'adapted_mesh': {
            'total_elements': refined_elems_count,
            'total_nodes': refined_nodes_count,
            'quad_elements': quad_count,
            'tri_elements': tri_count,
            'h_eq_stats': {
                'min_mm': h_min,
                'p10_mm': sorted_h[int(0.10*n_h)],
                'p25_mm': sorted_h[int(0.25*n_h)],
                'median_mm': h_median,
                'mean_mm': h_mean,
                'p75_mm': sorted_h[int(0.75*n_h)],
                'p90_mm': sorted_h[int(0.90*n_h)],
                'max_mm': max(all_h)
            },
            'h_over_l0_ratios': {
                'min_h_over_l0': h_min / l0,
                'median_h_over_l0': h_median / l0,
                'mean_h_over_l0': h_mean / l0
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
            'h_far_min_mm': min(h_far) if h_far else 0.0
        },
        'seam_verification': {
            'seam_duplicate_pairs': num_pairs,
            'seam_singletons': num_singletons,
            'tip_singleton_found': (num_singletons >= 1)
        },
        'localization_classification': localization_class,
        'baseline_comparison': {
            'baseline_stage14_elements': 14483,
            'baseline_stage14_h_min_mm': 0.00076,
            'baseline_stage14_corridor_fraction': 0.5757,
            'stage14am_elements': refined_elems_count,
            'stage14am_h_min_mm': h_min,
            'stage14am_corridor_fraction': corridor_fraction
        },
        'status': 'STAGE14UAM_SPATIAL_FINE_REMESH_COMPLETED'
    }
    
    json_path = os.path.join(out_dir, "STAGE14AM_SPATIAL_FINE_REMESH_SUMMARY.json")
    with open(json_path, "w") as f:
        json.dump(summary, f, indent=2)
        
    print("="*70)
    print("STAGE 14U-AM SUMMARY:")
    print("  Adapted Element Count: %d (Quads: %d, Tris: %d, Nodes: %d)" % (
        refined_elems_count, quad_count, tri_count, refined_nodes_count))
    print("  h_min: %.6e mm (h_min/l0 = %.4f)" % (h_min, h_min / l0))
    print("  h_median: %.6e mm (h_median/l0 = %.4f)" % (h_median, h_median / l0))
    print("  Corridor Elements: %d (%.2f%%)" % (corridor_count, corridor_fraction*100.0))
    print("  Far Field Elements: %d (%.2f%%)" % (far_field_total, far_field_fraction*100.0))
    print("  Seam Duplicate Pairs: %d, Singletons: %d" % (num_pairs, num_singletons))
    print("  Localization Classification: %s" % localization_class)
    print("  Saved: %s" % json_path)
    print("  Saved: %s" % csv_path)
    print("  Saved: %s" % dst_deck)
    print("="*70)
    return summary

if __name__ == "__main__":
    if '--' in sys.argv:
        idx = sys.argv.index('--')
        user_args = sys.argv[idx+1:]
        odb_p = user_args[0] if len(user_args) >= 1 else "PK_M1_JOB1_INF_COMPANION_2906.odb"
        out_d = user_args[1] if len(user_args) >= 2 else "."
    else:
        odb_p = sys.argv[-2] if len(sys.argv) >= 3 else "PK_M1_JOB1_INF_COMPANION_2906.odb"
        out_d = sys.argv[-1] if len(sys.argv) >= 3 else "."
    execute_stage14uam_remesh(odb_p, out_d)
