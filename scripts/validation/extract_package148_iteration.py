"""Abaqus Python 2/3 read-only endpoint extraction for Package 148 iterations."""
from __future__ import print_function
import argparse
import hashlib
import json
import math
import os


def sha(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1048576), b''):
            h.update(chunk)
    return h.hexdigest()


def export(odb_path, output, physical_nodes, physical_elements):
    from odbAccess import openOdb
    if os.path.exists(output):
        raise RuntimeError('Refusing to overwrite endpoint evidence')
    before = sha(odb_path)
    odb = openOdb(path=odb_path, readOnly=True)
    try:
        if list(odb.steps.keys()) != ['C1-1-ReEquil']:
            raise RuntimeError('Unexpected step identity')
        frame = odb.steps['C1-1-ReEquil'].frames[-1]
        if frame.incrementNumber != 1 or abs(frame.frameValue-1.0) > 1e-12:
            raise RuntimeError('Incomplete/wrong endpoint')
        nodes, rp, instances = {}, {}, set()
        for v in frame.fieldOutputs['U'].values:
            if v.nodeLabel == 999999:
                rp['rp_u2'] = float(v.data[1])
            else:
                if v.nodeLabel in nodes or len(v.data) != 3:
                    raise RuntimeError('Duplicate node or missing U3 damage')
                nodes[v.nodeLabel] = [int(v.nodeLabel)]+[float(x) for x in v.data]
                instances.add(v.instance.name)
        if len(nodes) != physical_nodes or len(instances) != 1:
            raise RuntimeError('Incomplete/ambiguous physical node coverage')
        for v in frame.fieldOutputs['RF'].values:
            if v.nodeLabel == 999999:
                if 'rf2_kN' in rp:
                    raise RuntimeError('Duplicate reference reaction')
                rp['rf2_kN'] = float(v.data[1])
        totals = {}
        expected = set((e, g) for e in range(2*physical_elements+1, 3*physical_elements+1)
                       for g in range(1, 5))
        for field, key in [('SDV17', 'fracture_kNmm'), ('SDV18', 'elastic_kNmm')]:
            values = {}
            for v in frame.fieldOutputs[field].values:
                index = (int(v.elementLabel), int(v.integrationPoint))
                if index in values or v.instance.name not in instances:
                    raise RuntimeError('Duplicate/ambiguous energy output')
                try:
                    value = float(v.data)
                except (TypeError, ValueError):
                    value = float(v.data[0])
                if math.isnan(value) or math.isinf(value) or value < 0:
                    raise RuntimeError('Invalid endpoint energy')
                values[index] = value
            if set(values) != expected:
                raise RuntimeError('Incomplete energy IP coverage')
            total = 0.
            for e in range(2*physical_elements+1, 3*physical_elements+1):
                reference = values[e, 1]
                if any(abs(values[e, g]-reference) > max(1e-14, abs(reference)*1e-6)
                       for g in range(2, 5)):
                    raise RuntimeError('Repeated element energy IP values disagree')
                total += reference  # Element totals: count each exactly once.
            totals[key] = total
        result = dict(schema=1, increment=int(frame.incrementNumber),
                      step_time=float(frame.frameValue), nodes=[nodes[n] for n in sorted(nodes)],
                      odb_sha256=before, extractor_sha256=sha(__file__), **totals)
        result.update(rp)
    finally:
        odb.close()
    if sha(odb_path) != before:
        raise RuntimeError('ODB changed during extraction')
    with open(output, 'w') as f:
        json.dump(result, f, allow_nan=False)


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--odb', required=True)
    p.add_argument('--output', required=True)
    p.add_argument('--physical-nodes', type=int, required=True)
    p.add_argument('--physical-elements', type=int, required=True)
    a = p.parse_args()
    export(a.odb, a.output, a.physical_nodes, a.physical_elements)
