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
import math

def main():
    model_name = "MODE2_UNIFORM_COARSE_MODEL"
    if model_name in mdb.models:
        del mdb.models[model_name]
    m = mdb.Model(name=model_name)
    
    # 1. Sketch: 1x1 mm square [0, 1] x [0, 1]
    s = m.ConstrainedSketch(name='__profile__', sheetSize=2.0)
    s.rectangle(point1=(0.0, 0.0), point2=(1.0, 1.0))
    
    p = m.Part(name='PLATE', dimensionality=TWO_D_PLANAR, type=DEFORMABLE_BODY)
    p.BaseShell(sketch=s)
    del m.sketches['__profile__']
    
    # 2. Partition for Crack Seam: from (0.0, 0.5) to (0.5, 0.5)
    p.PartitionFaceByShortestPath(faces=p.faces, point1=(0.0, 0.5, 0.0), point2=(0.5, 0.5, 0.0))
    
    # Crack seam on Part
    crack_edge = p.edges.findAt(((0.25, 0.5, 0.0), ))
    p.Set(name='SEAM_SET', edges=crack_edge)
    p.engineeringFeatures.assignSeam(regions=p.sets['SEAM_SET'])
    print("Assigned crack seam on Part along y = 0.5 mm, x in [0.0, 0.5] mm")
    
    # Material & Section
    mat = m.Material(name='Steel')
    mat.Elastic(table=((210000.0, 0.3), ))
    m.HomogeneousSolidSection(name='PlateSec', material='Steel', thickness=1.0)
    
    p.Set(name='ALL_ELEM', faces=p.faces)
    p.SectionAssignment(region=p.sets['ALL_ELEM'], sectionName='PlateSec')
    
    # Seed Part uniformly with h = 0.02 mm (matching Pandey & Kumar 2025)
    p.seedPart(size=0.02, deviationFactor=0.1, minSizeFactor=0.1)
    elemTypeQuad = mesh.ElemType(elemCode=CPE4, elemLibrary=STANDARD)
    elemTypeTri = mesh.ElemType(elemCode=CPE3, elemLibrary=STANDARD)
    p.setElementType(regions=p.sets['ALL_ELEM'], elemTypes=(elemTypeQuad, elemTypeTri))
    p.generateMesh()
    
    coarse_elems = len(p.elements)
    coarse_nodes = len(p.nodes)
    print("Uniform Coarse Mesh: %d elements, %d nodes" % (coarse_elems, coarse_nodes))
    
    # Assembly
    a = m.rootAssembly
    inst = a.Instance(name='PLATE-1', part=p, dependent=ON)
    
    # Step-1: Static General
    m.StaticStep(name='Step-1', previous='Initial', timePeriod=1.0, initialInc=1.0, minInc=1e-5, maxInc=1.0, nlgeom=OFF)
    reg = inst.sets['ALL_ELEM']
    m.fieldOutputRequests['F-Output-1'].setValues(
        variables=('S', 'U', 'RF', 'MISESERI', 'MISESAVG', 'EVOL'),
        region=reg
    )
    
    # Boundary Conditions
    bot_edges = inst.edges.findAt(((0.5, 0.0, 0.0), ))
    top_edges = inst.edges.findAt(((0.5, 1.0, 0.0), ))
    a.Set(name='BOTTOM', edges=bot_edges)
    a.Set(name='TOP', edges=top_edges)
    m.DisplacementBC(name='FIX_BOTTOM', createStepName='Step-1', region=a.sets['BOTTOM'], u1=0.0, u2=0.0)
    m.DisplacementBC(name='SHEAR_TOP', createStepName='Step-1', region=a.sets['TOP'], u1=0.001, u2=0.0)
    
    odb_path = "JOB_MODE2_UNIFORM_COARSE.odb"
    odb = odbAccess.openOdb(odb_path, readOnly=True)

    
    # We want errorTarget = 2.0 (which gave 21,550 elements, close to paper's 19,963)
    # and also test errorTarget = 5.0 (4,881 elements)
    for et in [2.0, 5.0]:
        tag = "et%d" % int(et)
        rr_name = "RR_ET_%d" % int(et)
        if rr_name in m.remeshingRules:
            del m.remeshingRules[rr_name]
        m.RemeshingRule(
            name=rr_name,
            stepName='Step-1',
            region=reg,
            description='Mode-II Native Remeshing Rule errorTarget=%.1f' % et,
            outputFrequency=ALL_INCREMENTS,
            variables=('MISESERI', ),
            sizingMethod=UNIFORM_ERROR,
            errorTarget=et,
            specifyMinSize=True,
            specifyMaxSize=True,
            minElementSize=0.001,
            maxElementSize=0.020,
            elementCountLimit=None,
            coarseningFactor=NOT_ALLOWED,
            refinementFactor=10
        )
        print("Calling m.adaptiveRemesh with %s..." % rr_name)
        m.adaptiveRemesh(odb=odb)
        p_ref = m.parts['PLATE']
        print("  --> [%s] Refined mesh: %d elements, %d nodes" % (tag, len(p_ref.elements), len(p_ref.nodes)))
        
        # Write inp
        job_name = "JOB_MODE2_ADAPTIVE_%s" % tag.upper()
        j = mdb.Job(name=job_name, model=model_name, description='Refined mesh %s' % tag)
        j.writeInput(consistencyChecking=OFF)
        print("Wrote input deck: %s.inp" % job_name)
        
        # Dump element centroid and approximate size
        out_csv = "C:/Users/pruth/.gemini/antigravity-cli/brain/b01cba38-646b-4f8c-8de2-b03dcba99e01/mesh_elements_%s.csv" % tag
        with open(out_csv, "w") as f:
            f.write("elem_id,cx,cy,area,h_approx,type\n")
            for elem in p_ref.elements:
                coords = [p_ref.nodes[i].coordinates for i in elem.connectivity]
                cx = sum([c[0] for c in coords]) / float(len(coords))
                cy = sum([c[1] for c in coords]) / float(len(coords))
                # Compute polygon area (shoelace formula)
                area = 0.0
                n_pts = len(coords)
                for i in range(n_pts):
                    j_idx = (i + 1) % n_pts
                    area += coords[i][0] * coords[j_idx][1] - coords[j_idx][0] * coords[i][1]
                area = abs(area) * 0.5
                h_approx = math.sqrt(area) if area > 0 else 0.0
                f.write("%d,%.6f,%.6f,%.6e,%.6e,%s\n" % (elem.label, cx, cy, area, h_approx, elem.type))
        print("Wrote %s with %d elements" % (out_csv, len(p_ref.elements)))

    odb.close()

if __name__ == "__main__":
    main()
