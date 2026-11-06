"""Read authentic Abaqus 2023 hole preanalysis; never run a solver or modify ODB.

Usage: abaqus python extract_method_a_hole_indicator.py PATH_TO_ODB
JSON is written to stdout; run through the repository guarded SSH wrapper.
"""
from __future__ import print_function
import hashlib
import json
import math
import os
import sys


def digest(path):
    h = hashlib.sha256()
    with open(path, 'rb') as stream:
        for block in iter(lambda: stream.read(1048576), b''):
            h.update(block)
    return h.hexdigest().upper()


def extract(path):
    if not os.path.isfile(path):
        raise ValueError('Exact source ODB does not exist')
    from odbAccess import openOdb
    odb = openOdb(path=os.path.abspath(path), readOnly=True)
    try:
        step_name = list(odb.steps.keys())[-1]
        step = odb.steps[step_name]
        frame = step.frames[-1]
        if 'MISESERI' not in frame.fieldOutputs:
            raise ValueError('Authentic MISESERI field missing')
        by_key = {}
        positions = set()
        sections = set()
        for value in frame.fieldOutputs['MISESERI'].values:
            data = value.data
            if hasattr(data, '__len__'):
                if len(data) != 1:
                    raise ValueError('Expected scalar MISESERI')
                data = data[0]
            data = float(data)
            if math.isnan(data) or math.isinf(data) or data < 0:
                raise ValueError('Nonfinite or negative MISESERI')
            key = (value.instance.name, value.elementLabel)
            positions.add(str(value.position))
            sections.add(str(value.sectionPoint))
            by_key.setdefault(key, []).append(data)
        rows = []
        for name in odb.rootAssembly.instances.keys():
            inst = odb.rootAssembly.instances[name]
            nodes = dict((n.label, [float(x) for x in n.coordinates]) for n in inst.nodes)
            for elem in inst.elements:
                key = (name, elem.label)
                if key not in by_key:
                    raise ValueError('Missing MISESERI coverage: %s' % (key,))
                xy = [nodes[n] for n in elem.connectivity]
                centroid = [sum(p[i] for p in xy) / len(xy) for i in (0, 1)]
                edges = [math.sqrt(sum((xy[i][j]-xy[(i+1)%len(xy)][j])**2
                                      for j in (0, 1))) for i in range(len(xy))]
                values = by_key[key]
                if min(values) != max(values):
                    raise ValueError('Ambiguous unequal whole-element samples: %s' % (key,))
                rows.append(dict(instance=name, element=elem.label, type=elem.type,
                                 centroid_mm=centroid, coordinates_mm=xy,
                                 edge_min_mm=min(edges), edge_max_mm=max(edges),
                                 miseseri_max=max(values), miseseri_min=min(values),
                                 samples=len(values)))
        if not rows:
            raise ValueError('Empty source mesh')
        if len(rows) != len(by_key):
            raise ValueError('Indicator/mesh identity coverage mismatch')
        displacement = frame.fieldOutputs['U'] if 'U' in frame.fieldOutputs else None
        displacement_summary = None
        if displacement is not None:
            uy = [float(v.data[1]) for v in displacement.values]
            displacement_summary = dict(min_u2_mm=min(uy), max_u2_mm=max(uy))
        return dict(schema=1, source_odb=os.path.abspath(path),
                    source_sha256=digest(path), source_bytes=os.path.getsize(path),
                    step=step_name, frame_value=frame.frameValue,
                    frame_count=len(step.frames), fields=list(frame.fieldOutputs.keys()),
                    element_count=len(rows), indicator='MISESERI',
                    output_positions=sorted(positions), displacement=displacement_summary,
                    section_points=sorted(sections),
                    indicator_sample_count=sum(r['samples'] for r in rows),
                    interpretation='native scalar field; raw units retained, not a normalized percentage',
                    records=rows, solver_runs=0, odb_modified=False)
    finally:
        odb.close()


if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise SystemExit('Provide exactly one existing ODB path')
    print(json.dumps(extract(sys.argv[1]), sort_keys=True, allow_nan=False))
