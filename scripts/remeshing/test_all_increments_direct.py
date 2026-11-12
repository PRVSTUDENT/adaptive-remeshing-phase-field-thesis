from abaqus import *
from abaqusConstants import *
import regionToolset
import mesh
import os
import math
import numpy as np

REPO_ROOT = r"D:\Master thesis\Adaptive remeshing"
COUPLED_ODB = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "213_f1720_coarse_coupled", "PK_F1720_COARSE_COUPLED.odb")

out_log = os.path.join(REPO_ROOT, "scripts", "remeshing", "all_increments_experiment_results.txt")
log_f = open(out_log, "w")

def log(msg):
    log_f.write(str(msg) + "\n")
    log_f.flush()
    print(msg)

def build_cad_model(m, seed_size):
    s = m.ConstrainedSketch(name='__profile__', sheetSize=2.0)
    s.Line(point1=(0.0, 0.0), point2=(1.0, 0.0))
    s.Line(point1=(1.0, 0.0), point2=(1.0, 0.375))
    s.Arc3Points(point1=(1.0, 0.375), point2=(1.0, 0.525), point3=(0.925, 0.450))
    s.Line(point1=(1.0, 0.525), point2=(1.0, 1.0))
    s.Line(point1=(1.0, 1.0), point2=(0.0, 1.0))
    s.Line(point1=(0.0, 1.0), point2=(0.0, 0.60))
    s.Arc3Points(point1=(0.0, 0.600), point2=(0.0, 0.400), point3=(0.100, 0.500))
    s.Line(point1=(0.0, 0.400), point2=(0.0, 0.0))

    s.CircleByCenterPerimeter(center=(0.35, 0.45), point1=(0.45, 0.45))
    s.CircleByCenterPerimeter(center=(0.60, 0.55), point1=(0.65, 0.55))
    s.CircleByCenterPerimeter(center=(0.75, 0.50), point1=(0.825, 0.50))

    p = m.Part(name='FiveHolePlate', dimensionality=TWO_D_PLANAR, type=DEFORMABLE_BODY)
    p.BaseShell(sketch=s)
    del m.sketches['__profile__']

    mat = m.Material(name='Steel')
    mat.Elastic(table=((210000.0, 0.3), ))
    m.HomogeneousSolidSection(name='SolidSec', material='Steel', thickness=1.0)
    p.SectionAssignment(region=regionToolset.Region(faces=p.faces), sectionName='SolidSec')

    p.seedPart(size=seed_size, deviationFactor=0.1, minSizeFactor=0.1)
    p.setMeshControls(regions=p.faces, elemShape=QUAD_DOMINATED, technique=FREE)
    elem_cpe4 = mesh.ElemType(elemCode=CPE4, elemLibrary=STANDARD)
    elem_cpe3 = mesh.ElemType(elemCode=CPE3, elemLibrary=STANDARD)
    p.setElementType(regions=(p.faces,), elemTypes=(elem_cpe4, elem_cpe3))
    p.generateMesh()

    p.Set(name='ALL_ELEM', faces=p.faces)
    a = m.rootAssembly
    inst = a.Instance(name='PART-1-1', part=p, dependent=ON)
    a.Set(name='ALL_ELEM', faces=inst.faces)

    m.StaticStep(name='Step-1', previous='Initial', timePeriod=1.0)
    m.StaticStep(name='Step-2', previous='Step-1', timePeriod=1.0)
    return p, a, inst

def audit_ligaments(p):
    nodes = p.nodes
    lig1_elems = []
    lig2_elems = []
    lig3_elems = []
    lig4_elems = []
    bulk_elems = []
    
    for el in p.elements:
        pts = [nodes[i].coordinates for i in el.connectivity]
        px = [pt[0] for pt in pts]
        py = [pt[1] for pt in pts]
        n_pts = len(pts)
        
        area = 0.5 * abs(sum([px[i]*py[(i+1)%n_pts] - py[i]*px[(i+1)%n_pts] for i in range(n_pts)]))
        h_eq = math.sqrt(area) * 1000.0 # in um
        
        cx = sum(px) / float(n_pts)
        cy = sum(py) / float(n_pts)
        
        if 0.08 <= cx <= 0.27 and 0.40 <= cy <= 0.56:
            lig1_elems.append(h_eq)
        elif 0.42 <= cx <= 0.57 and 0.42 <= cy <= 0.58:
            lig2_elems.append(h_eq)
        elif 0.63 <= cx <= 0.69 and 0.48 <= cy <= 0.56:
            lig3_elems.append(h_eq)
        elif 0.81 <= cx <= 0.94 and 0.40 <= cy <= 0.55:
            lig4_elems.append(h_eq)
        elif cy > 0.70 or cy < 0.30:
            bulk_elems.append(h_eq)
            
    return {
        "n_elems": len(p.elements),
        "lig1_count": len(lig1_elems),
        "lig1_mean_h": sum(lig1_elems)/float(len(lig1_elems)) if lig1_elems else 0.0,
        "lig1_min_h": min(lig1_elems) if lig1_elems else 0.0,
        "lig2_count": len(lig2_elems),
        "lig2_mean_h": sum(lig2_elems)/float(len(lig2_elems)) if lig2_elems else 0.0,
        "lig2_min_h": min(lig2_elems) if lig2_elems else 0.0,
        "lig3_count": len(lig3_elems),
        "lig3_mean_h": sum(lig3_elems)/float(len(lig3_elems)) if lig3_elems else 0.0,
        "bulk_count": len(bulk_elems),
        "bulk_mean_h": sum(bulk_elems)/float(len(bulk_elems)) if bulk_elems else 0.0
    }

test_configs = [
    # (name, step_name, out_freq, err_tgt, seed)
    ("S1_LAST_340", "Step-1", LAST_INCREMENT, 3.40, 0.020),
    ("S1_ALL_340",  "Step-1", ALL_INCREMENTS, 3.40, 0.020),
    ("S2_LAST_340", "Step-2", LAST_INCREMENT, 3.40, 0.020),
    ("S2_ALL_340",  "Step-2", ALL_INCREMENTS, 3.40, 0.020),
    ("S2_ALL_300",  "Step-2", ALL_INCREMENTS, 3.00, 0.020),
    ("S2_ALL_250",  "Step-2", ALL_INCREMENTS, 2.50, 0.020),
]

log("Starting direct comparison of LAST_INCREMENT vs ALL_INCREMENTS...")
odb_donor = session.openOdb(name=COUPLED_ODB)

for name, step_name, out_freq, err_tgt, seed in test_configs:
    model_name = "M_" + name
    if model_name in mdb.models:
        del mdb.models[model_name]
    m = mdb.Model(name=model_name)
    p, a, inst = build_cad_model(m, seed)
    reg_all = inst.sets['ALL_ELEM']
    
    m.RemeshingRule(
        name="RR_" + name,
        stepName=step_name,
        region=reg_all,
        variables=('MISESERI',),
        sizingMethod=UNIFORM_ERROR,
        errorTarget=err_tgt,
        specifyMinSize=True,
        minElementSize=0.001,
        specifyMaxSize=True,
        maxElementSize=0.020,
        coarseningFactor=NOT_ALLOWED,
        refinementFactor=10,
        outputFrequency=out_freq
    )
    
    m.adaptiveRemesh(odb=odb_donor)
    metrics = audit_ligaments(p)
    log("--------------------------------------------------")
    log("Case %s (%s, out_freq=%s, err_tgt=%.2f):" % (name, step_name, str(out_freq), err_tgt))
    log("  Total elems: %d" % metrics['n_elems'])
    log("  Lig 1 (h1-h2): count=%d, mean_h=%.2fum, min_h=%.2fum" % (metrics['lig1_count'], metrics['lig1_mean_h'], metrics['lig1_min_h']))
    log("  Lig 2 (h2-h3): count=%d, mean_h=%.2fum, min_h=%.2fum" % (metrics['lig2_count'], metrics['lig2_mean_h'], metrics['lig2_min_h']))
    log("  Lig 3 (h3-h4): count=%d, mean_h=%.2fum" % (metrics['lig3_count'], metrics['lig3_mean_h']))
    log("  Bulk: count=%d, mean_h=%.2fum" % (metrics['bulk_count'], metrics['bulk_mean_h']))

odb_donor.close()
log("==================================================")
log("All test configs complete!")
log_f.close()
