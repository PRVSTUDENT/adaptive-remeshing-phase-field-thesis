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


def _field_data(v):
    """Safely extracts data tuple/array honoring DOUBLE_PRECISION when present."""
    try:
        from abaqusConstants import DOUBLE_PRECISION
        if getattr(v, 'precision', None) == DOUBLE_PRECISION:
            return v.dataDouble
    except Exception:
        pass
    return v.data


def parse_dat_nodal_u(dat_path):
    """Parses nodal U table from Abaqus .dat file if present."""
    if not os.path.isfile(dat_path):
        return {}
    results = {}
    with open(dat_path, 'r') as f:
        in_table = False
        for line in f:
            if 'NODE FOOT-' in line:
                in_table = True
                continue
            if in_table:
                line_s = line.strip()
                if not line_s or 'NOTE' in line_s or line_s.startswith('-'):
                    continue
                if line_s.startswith('MAXIMUM') or line_s.startswith('MINIMUM'):
                    in_table = False
                    continue
                parts = line_s.split()
                if parts and parts[0].isdigit():
                    nid = int(parts[0])
                    vals = [float(x) for x in parts[1:]]
                    results[nid] = vals
    return results


def export(odb_path, output, physical_nodes, physical_elements, expected_step=None):
    from odbAccess import openOdb
    if os.path.exists(output):
        raise RuntimeError('Refusing to overwrite endpoint evidence')
    before = sha(odb_path)
    odb = openOdb(path=odb_path, readOnly=True)
    try:
        step_keys = list(odb.steps.keys())
        if expected_step:
            if expected_step not in odb.steps:
                raise RuntimeError('Specified step not found in ODB: %s (available: %s)' % (expected_step, str(step_keys)))
            step_name = expected_step
        else:
            if len(step_keys) != 1:
                raise RuntimeError('Expected exactly one step in subproblem iteration ODB, found: %s' % str(step_keys))
            step_name = step_keys[0]
            if not (step_name == 'C1-1-ReEquil' or step_name.startswith('C1_2_Step') or step_name.startswith('C1-2-Step')):
                raise RuntimeError('Unexpected step identity: %s (expected C1-1-ReEquil or C1_2_Step*)' % step_name)

        frame = odb.steps[step_name].frames[-1]
        if frame.incrementNumber != 1 or abs(frame.frameValue - 1.0) > 1e-12:
            raise RuntimeError('Incomplete/wrong endpoint in step %s: inc %d, time %g' % (step_name, frame.incrementNumber, frame.frameValue))

        # Check for .dat companion table for U3 (phase field damage) if present
        dat_path = os.path.splitext(odb_path)[0] + '.dat'
        dat_u = parse_dat_nodal_u(dat_path) if os.path.isfile(dat_path) else {}

        nodes, rp, instances = {}, {}, set()
        for v in frame.fieldOutputs['U'].values:
            if v.nodeLabel == 999999:
                rp['rp_u2'] = float(_field_data(v)[1])
            else:
                if v.nodeLabel in nodes:
                    raise RuntimeError('Duplicate node in fieldOutputs[U]')
                u_data = [float(x) for x in _field_data(v)]
                if len(u_data) == 2:
                    # 2D planar mechanical displacement
                    # If dat file has U3 for this node, append it
                    if v.nodeLabel in dat_u and len(dat_u[v.nodeLabel]) >= 3:
                        u_data.append(float(dat_u[v.nodeLabel][2]))
                elif len(u_data) == 3:
                    pass
                else:
                    raise RuntimeError('Invalid U dimension: %d' % len(u_data))

                nodes[v.nodeLabel] = [int(v.nodeLabel)] + u_data
                instances.add(v.instance.name)

        if len(nodes) != physical_nodes or len(instances) != 1:
            raise RuntimeError('Incomplete/ambiguous physical node coverage')

        for v in frame.fieldOutputs['RF'].values:
            if v.nodeLabel == 999999:
                if 'rf2_kN' in rp:
                    raise RuntimeError('Duplicate reference reaction')
                rp['rf2_kN'] = float(_field_data(v)[1])

        totals = {}
        expected = set((e, g) for e in range(2 * physical_elements + 1, 3 * physical_elements + 1)
                       for g in range(1, 5))
        for field, key in [('SDV17', 'fracture_kNmm'), ('SDV18', 'elastic_kNmm')]:
            values = {}
            if field in frame.fieldOutputs:
                for v in frame.fieldOutputs[field].values:
                    index = (int(v.elementLabel), int(v.integrationPoint))
                    if index in values or v.instance.name not in instances:
                        raise RuntimeError('Duplicate/ambiguous energy output')
                    raw_e = _field_data(v)
                    try:
                        value = float(raw_e)
                    except (TypeError, ValueError):
                        value = float(raw_e[0])
                    if math.isnan(value) or math.isinf(value) or value < 0:
                        raise RuntimeError('Invalid endpoint energy')
                    values[index] = value
            if set(values) != expected:
                raise RuntimeError('Incomplete energy IP coverage')
            total = 0.
            for e in range(2 * physical_elements + 1, 3 * physical_elements + 1):
                reference = values[e, 1]
                if any(abs(values[e, g] - reference) > max(1e-14, abs(reference) * 1e-6)
                       for g in range(2, 5)):
                    raise RuntimeError('Repeated element energy IP values disagree')
                total += reference  # Element totals: count each exactly once.
            totals[key] = total

        precision_u = str(getattr(frame.fieldOutputs['U'].values[0], 'precision', 'UNKNOWN')) if frame.fieldOutputs['U'].values else 'UNKNOWN'
        result = dict(schema=1, step_name=str(step_name), increment=int(frame.incrementNumber),
                      step_time=float(frame.frameValue), precision=precision_u,
                      nodes=[nodes[n] for n in sorted(nodes)],
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
    p.add_argument('--step', default=None, help='Optional explicit step name')
    a = p.parse_args()
    export(a.odb, a.output, a.physical_nodes, a.physical_elements, expected_step=a.step)
