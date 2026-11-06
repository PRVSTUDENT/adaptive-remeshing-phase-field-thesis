"""One offline local-sizing hypothesis; no mesh generation or solver calls.

Predeclared parameters: bulk fraction0.90, cap0.0015mm, far cap0.020mm,
Lipschitz grading slope0.25. Regions are independent diagnostics only.
MISESERI is treated as a raw stress-error proxy, not a percentage or certified norm.
"""
import hashlib
import json
import math
from pathlib import Path

import numpy as np
from scipy.spatial import cKDTree
from scripts.validation.validate_f1641_native_mesh import read_mesh

ROOT = Path(__file__).resolve().parents[2]
THETA, CAP, FAR, SLOPE = .90, .0015, .020, .25


def polygon_area(points):
    p = np.asarray(points)
    return abs(float(np.sum(p[:,0]*np.roll(p[:,1],-1)-p[:,1]*np.roll(p[:,0],-1)))/2)


def bulk_support(areas, errors, theta=THETA):
    areas, errors = np.asarray(areas), np.asarray(errors)
    if not 0 < theta < 1 or np.any(areas <= 0) or np.any(errors < 0):
        raise ValueError('Invalid support inputs')
    weights = areas*errors**2
    if not np.all(np.isfinite(weights)) or weights.sum() <= 0:
        raise ValueError('Invalid total indicator mass')
    order = np.argsort(-weights, kind='stable')
    stop = np.searchsorted(np.cumsum(weights[order]), theta*weights.sum())
    cutoff = weights[order[stop]]
    # Include all exact cutoff ties, preserving invariance to input ordering.
    selected = weights >= cutoff
    return selected, weights/weights.sum(), float(cutoff)


def inside(point, polygon):
    x, y = point
    result = False
    for a, b in zip(polygon, polygon[1:]+polygon[:1]):
        cross = (x-a[0])*(b[1]-a[1])-(y-a[1])*(b[0]-a[0])
        if abs(cross) < 1e-13 and min(a[0],b[0])-1e-12 <= x <= max(a[0],b[0])+1e-12 and min(a[1],b[1])-1e-12 <= y <= max(a[1],b[1])+1e-12:
            return True
        if (a[1] > y) != (b[1] > y) and x < (b[0]-a[0])*(y-a[1])/(b[1]-a[1])+a[0]:
            result = not result
    return result


def support_distance(points, polygons, selected):
    segments = [(a,b) for k,p in enumerate(polygons) if selected[k]
                for a,b in zip(p,p[1:]+p[:1])]
    start = np.array([x[0][:2] for x in segments])
    delta = np.array([x[1][:2] for x in segments])-start
    denom = np.sum(delta**2,axis=1)
    answer = []
    for point, is_selected in zip(points, selected):
        if is_selected:
            answer.append(0.)
            continue
        offset = point-start
        t = np.clip(np.sum(offset*delta,axis=1)/denom,0,1)
        answer.append(float(np.min(np.linalg.norm(offset-t[:,None]*delta,axis=1))))
    return np.array(answer)


def main():
    source_path = ROOT/'results/validation/f1641_hole_indicator_provenance.json'
    source = json.loads(source_path.read_text())
    records = source['records']
    polygons = [r['coordinates_mm'] for r in records]
    centers = np.array([r['centroid_mm'] for r in records])
    areas = np.array([polygon_area(p) for p in polygons])
    errors = np.array([r['miseseri_max'] for r in records])
    marked, weights, cutoff = bulk_support(areas, errors)
    distances = support_distance(centers, polygons, marked)
    caps = np.minimum(FAR, CAP+SLOPE*distances)
    tree = cKDTree(centers)
    mesh_path = ROOT/'models/pandey_kumar_mode1/176_method_a_plate_with_hole/f1641_native_1pct/PK_HOLE_F1641_1PCT_PROD_PHYS.inp'
    nodes, elems = read_mesh(mesh_path)
    regions = {k:dict(elements=0,mapped=0,selected=0,area=0.,selected_area=0.,unmapped=0,
                      uncovered_examples=[]) for k in ('notch_tip','ligament','hole_boundary')}
    for label,conn in elems.items():
        p = [nodes[n] for n in conn]
        x,y = np.mean(p,axis=0)
        hole = math.hypot(x-.65,y-.65)
        name = ('notch_tip' if math.hypot(x-.5,y-.5) <= .025 else 'hole_boundary' if abs(hole-.1) <= .015
                else 'ligament' if .5 <= x <= .65 and .48 <= y <= .70 and hole > .1 else None)
        if name is None:
            continue
        r = regions[name]
        r['elements'] += 1
        area = polygon_area(p)
        r['area'] += area
        _,near = tree.query([x,y],k=min(24,len(records)))
        found = next((int(i) for i in near if inside((x,y),polygons[int(i)])),None)
        if found is None:
            # No nearest-neighbor substitution across coarse hole chords/seam.
            r['unmapped'] += 1
            continue
        r['mapped'] += 1
        if marked[found]:
            r['selected'] += 1
            r['selected_area'] += area
        elif len(r['uncovered_examples']) < 5:
            r['uncovered_examples'].append(dict(candidate_element=label,centroid_mm=[float(x),float(y)],
                                                 source_element=records[found]['element']))
    for r in regions.values():
        r['selected_count_fraction'] = r['selected']/r['elements']
        r['selected_area_fraction'] = r['selected_area']/r['area']
        r['full_coverage_demonstrated'] = r['selected'] == r['elements'] and r['unmapped'] == 0
    report = dict(schema=1,hypothesis='90 percent bulk stress-error-proxy support with graded local maximum-size cap',
                  source_sha256=hashlib.sha256(source_path.read_bytes()).hexdigest().upper(),
                  source_odb_sha256=source['source_sha256'],
                  parameters=dict(theta=THETA,h_cap_mm=CAP,h_far_mm=FAR,slope=SLOPE,transition_width_mm=(FAR-CAP)/SLOPE),
                  formulas=dict(weight='w_K = A_K * MISESERI_K^2 / sum_J(A_J * MISESERI_J^2)',
                                marking='Descending unnormalized contributions; shortest prefix reaching theta, include all cutoff ties',
                                cap='h_resolution(x)=min(h_far,h_cap+slope*distance(x,union(marked polygons)))',
                                final='h_target(x)=min(h_native_MISESERI(x),h_resolution(x)); proposed, not implemented'),
                  parameter_provenance='One predeclared theta0.90 captures90% of a normalized proxy mass; not a percent error, qualified threshold, or fracture convergence theorem. No fitting to diagnostic zones.',
                  support=dict(cells=int(marked.sum()),total_cells=len(marked),area_mm2=float(areas[marked].sum()),
                               source_polygon_area_mm2=float(areas.sum()),area_fraction=float(areas[marked].sum()/areas.sum()),
                               mass_fraction=float(weights[marked].sum()),raw_contribution_cutoff=cutoff),
                  cost_proxy=dict(marked_area_over_cap_squared=float(areas[marked].sum()/CAP**2),
                                  centroid_quadrature_integral_area_over_graded_cap_squared=float(np.sum(areas/caps**2)),
                                  interpretation='Approximate square-cell counts; triangles/geometric transitions change counts; not rigorous bounds, actual mesh counts, or runtime estimates'),
                  diagnostic_region_coverage=regions,
                  source_cell_map=[dict(element=r['element'],area_mm2=float(a),weight=float(w),selected=bool(s),
                                        distance_to_support_mm=float(d),resolution_cap_at_centroid_mm=float(h))
                                   for r,a,w,s,d,h in zip(records,areas,weights,marked,distances,caps)],
                  result='SUPPORT_REJECTED' if not all(r['full_coverage_demonstrated'] for r in regions.values()) else 'SUPPORT_ONLY_PASS_BACKEND_REVIEW_REQUIRED',
                  falsification='Any independently required diagnostic region contains mapped centers outside selected support, or coverage unproven; no geometric corridor may be added to force a pass',
                  new_meshes=0,solver_runs=0,pbs_submissions=0)
    out = ROOT/'results/validation/f1641_local_size_support.json'
    if out.exists():
        raise ValueError('Preserve existing hypothesis result')
    out.write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:report[k] for k in ('support','cost_proxy','diagnostic_region_coverage','result')},indent=2))


if __name__ == '__main__':
    main()
