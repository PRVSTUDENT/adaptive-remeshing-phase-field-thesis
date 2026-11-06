"""Quantify the single native Method A candidate against both existing meshes.

Regions are diagnostic measurements only; no region is used to prescribe a crack.
No solver invocation. Positive quad Jacobians are evaluated at all 2x2 Gauss points.
"""
import hashlib
import json
import math
from collections import defaultdict
from pathlib import Path

import numpy as np
from scipy.spatial import cKDTree
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT / 'models/pandey_kumar_mode1/176_method_a_plate_with_hole'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def read_mesh(path):
    nodes, elems = {}, {}
    mode = None
    for raw in path.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith('**'):
            continue
        if line.startswith('*'):
            keyword = line.split(',')[0].upper()
            mode = 'node' if keyword == '*NODE' else 'elem' if keyword == '*ELEMENT' else None
            continue
        values = [x.strip() for x in line.split(',') if x.strip()]
        if mode == 'node':
            nodes[int(values[0])] = tuple(float(x) for x in values[1:3])
        elif mode == 'elem':
            conn = tuple(int(x) for x in values[1:])
            if len(conn) not in (3, 4):
                raise ValueError('Only linear triangles/quads accepted')
            elems[int(values[0])] = conn
    if not nodes or not elems:
        raise ValueError('Empty physical mesh')
    return nodes, elems


def stats(values):
    v = np.asarray(values, dtype=float)
    if not len(v):
        return None
    return dict(zip(('min', 'p10', 'median', 'p90', 'max'),
                    [float(x) for x in np.percentile(v, [0, 10, 50, 90, 100])]))


def element_metrics(points):
    p = np.asarray(points, dtype=float)
    edge_vectors = np.roll(p, -1, axis=0) - p
    lengths = np.linalg.norm(edge_vectors, axis=1)
    area = 0.5 * float(np.sum(p[:, 0]*np.roll(p[:, 1], -1)-p[:, 1]*np.roll(p[:, 0], -1)))
    angles = []
    for i in range(len(p)):
        a, b = p[i-1]-p[i], p[(i+1) % len(p)]-p[i]
        angles.append(math.degrees(math.acos(float(np.clip(np.dot(a, b)/(np.linalg.norm(a)*np.linalg.norm(b)), -1, 1)))))
    if len(p) == 3:
        jac = [2*area]
        quality = 4*math.sqrt(3)*area/float(np.sum(lengths**2))
    else:
        jac = []
        for xi in (-1/math.sqrt(3), 1/math.sqrt(3)):
            for eta in (-1/math.sqrt(3), 1/math.sqrt(3)):
                derivative = np.array([[-(1-eta), -(1-xi)],
                                       [(1-eta), -(1+xi)],
                                       [(1+eta), (1+xi)],
                                       [-(1+eta), (1-xi)]]) / 4
                jac.append(float(np.linalg.det(derivative.T @ p)))
        # Minimum signed corner scaled Jacobian: 1 for square, <=0 for inversion.
        quality = min(float(np.cross(edge_vectors[i], -edge_vectors[i-1])) /
                      (lengths[i]*lengths[i-1]) for i in range(4))
    return dict(area=area, hmax=float(max(lengths)), harea=math.sqrt(abs(area)),
                aspect=float(max(lengths)/min(lengths)), min_angle=min(angles),
                min_jac=min(jac), quality=quality, centroid=np.mean(p, axis=0))


def analyze(path, source):
    nodes, elems = read_mesh(path)
    metrics = {}
    owners = defaultdict(list)
    regions = defaultdict(list)
    for label, conn in elems.items():
        m = element_metrics([nodes[n] for n in conn])
        metrics[label] = m
        x, y = m['centroid']
        tip = math.hypot(x-.5, y-.5)
        hole = math.hypot(x-.65, y-.65)
        # Same mutually exclusive diagnostic zones as the historical audit.
        region = ('notch_tip' if tip <= .025 else 'hole_boundary' if abs(hole-.1) <= .015
                  else 'ligament' if .5 <= x <= .65 and .48 <= y <= .70 and hole > .1
                  else 'far_field')
        regions[region].append(m)
        for a, b in zip(conn, conn[1:]+conn[:1]):
            owners[tuple(sorted((a, b)))].append(label)
    all_m = list(metrics.values())
    sizes = np.array([m['hmax'] for m in all_m])
    centers = np.array([m['centroid'] for m in all_m])
    tree = cKDTree([r['centroid_mm'] for r in source['records']])
    distances, idx = tree.query(centers)
    indicator = np.array([source['records'][int(i)]['miseseri_max'] for i in idx])
    # Nearest coarse centroid is a reported association diagnostic, not the sizing rule.
    correlation = spearmanr(indicator, sizes)
    bands = []
    quantiles = np.percentile(indicator, [0, 25, 50, 75, 90, 100])
    for k in range(len(quantiles)-1):
        mask = ((indicator >= quantiles[k]) &
                (indicator <= quantiles[k+1] if k == len(quantiles)-2 else indicator < quantiles[k+1]))
        bands.append(dict(indicator_interval=[float(quantiles[k]), float(quantiles[k+1])],
                          elements=int(mask.sum()), hmax_mm=stats(sizes[mask])))
    grading = [max(metrics[a]['harea'], metrics[b]['harea'])/min(metrics[a]['harea'], metrics[b]['harea'])
               for labels in owners.values() if len(labels) == 2 for a, b in [labels]]
    boundary = [edge for edge, labels in owners.items() if len(labels) == 1]
    hole_edges = [edge for edge in boundary if all(abs(math.hypot(nodes[n][0]-.65, nodes[n][1]-.65)-.1) < 1e-4 for n in edge)]
    hole_nodes = set(n for e in hole_edges for n in e)
    if not hole_edges:
        raise ValueError('No hole boundary recovered')
    radial_error = [abs(math.hypot(nodes[n][0]-.65, nodes[n][1]-.65)-.1) for n in hole_nodes]
    chord_error = [abs(math.hypot((nodes[a][0]+nodes[b][0])/2-.65,
                                 (nodes[a][1]+nodes[b][1])/2-.65)-.1) for a,b in hole_edges]
    tip_errors = [min(math.hypot(x-.5, y-t) for x,y in nodes.values()) for t in (.499,.501)]
    xyz = np.array(list(nodes.values()))
    regional = {}
    for name, ms in regions.items():
        h = [m['hmax'] for m in ms]
        regional[name] = dict(elements=len(ms), hmax_mm=stats(h),
                              h_over_l0=stats(np.array(h)/.0075),
                              h_area_mm=stats([m['harea'] for m in ms]),
                              fraction_hmax_le_l0_over5=float(np.mean(np.array(h) <= .0015)))
    nonpositive = sum(m['min_jac'] <= 0 or m['area'] <= 0 for m in all_m)
    return dict(path=str(path.relative_to(ROOT)), sha256=sha(path), nodes=len(nodes),
                elements=len(elems), triangles=sum(len(c)==3 for c in elems.values()),
                quads=sum(len(c)==4 for c in elems.values()),
                layered_elements=3*len(elems), hmax_mm=stats(sizes), regions=regional,
                quality=dict(nonpositive_jacobian_or_area=nonpositive,
                             jacobian_mm2=stats([m['min_jac'] for m in all_m]),
                             aspect_edge_ratio=stats([m['aspect'] for m in all_m]),
                             minimum_angle_degrees=stats([m['min_angle'] for m in all_m]),
                             triangle_mean_ratio_or_quad_corner_scaled_jacobian=stats([m['quality'] for m in all_m]),
                             nonmanifold_edges=sum(len(x)>2 for x in owners.values())),
                grading_adjacent_sqrt_area_ratio=stats(grading),
                geometry=dict(bbox_mm=[xyz.min(axis=0).tolist(),xyz.max(axis=0).tolist()],
                              total_area_mm2=sum(m['area'] for m in all_m),
                              exact_area_mm2=1-.5*.002-math.pi*.1**2,
                              hole_boundary_nodes=len(hole_nodes), hole_radial_error_mm=stats(radial_error),
                              hole_chord_midpoint_error_mm=stats(chord_error),
                              slit_tip_corner_position_errors_mm=tip_errors),
                indicator_association=dict(method='nearest authentic coarse-element centroid; diagnostic only',
                                           distance_mm=stats(distances),spearman_hmax_vs_miseseri=float(correlation.statistic),
                                           bands=bands),
                acceptance=dict(positive_jacobians=nonpositive == 0,
                                full_diagnostic_region_l0_over5={k: all(m['hmax'] <= .0015 for m in ms)
                                                               for k,ms in regions.items() if k != 'far_field'},
                                production_accepted=False))


def main():
    indicator_path = ROOT / 'results/validation/f1641_hole_indicator_provenance.json'
    source = json.loads(indicator_path.read_text())
    paths = [PACKAGE/'f1641_native_1pct/PK_HOLE_F1641_1PCT_PROD_PHYS.inp',
             PACKAGE/'PK_HOLE_METHOD_A_PROD_PHYS.inp',
             PACKAGE/'candidate_16k/PK_HOLE_CANDIDATE_16K_PROD_PHYS.inp']
    report = dict(schema=1, source_indicator_sha256=sha(indicator_path),
                  sizing_rule='Native Abaqus2023 UNIFORM_ERROR, errorTarget=1.0 percentage point; original coarse mesh and size bounds retained',
                  solver_runs=0, pbs_submissions=0,
                  results=[analyze(path, source) for path in paths])
    out = ROOT/'results/validation/f1641_native_mesh_metrics.json'
    if out.exists():
        raise ValueError('Metrics already exist; preserve historical output')
    out.write_text(json.dumps(report, indent=2, allow_nan=False)+'\n')
    for item in report['results']:
        print(json.dumps({k:item[k] for k in ('path','nodes','elements','quality','acceptance')}, indent=2))


if __name__ == '__main__':
    main()
