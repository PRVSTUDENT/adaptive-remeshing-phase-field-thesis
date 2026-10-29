"""Abaqus Python, read-only ODB export. No solver or scheduler invocation."""
from __future__ import print_function
import argparse
import gzip
import hashlib
import json
import os


def sha(path):
    h = hashlib.sha256()
    with open(path, 'rb') as stream:
        for block in iter(lambda: stream.read(1048576), b''):
            h.update(block)
    return h.hexdigest()


def export(odb_path, output, inspect=False):
    from odbAccess import openOdb
    before = sha(odb_path)
    odb = openOdb(path=odb_path, readOnly=True)
    try:
        step = odb.steps['Step-1']
        frame = step.frames[-1]
        if inspect:
            print(json.dumps({'steps': list(odb.steps.keys()), 'frames': len(step.frames),
                              'fields': list(frame.fieldOutputs.keys()),
                              'instances': list(odb.rootAssembly.instances.keys()),
                              'last_increment': frame.incrementNumber,
                              'last_step_time': frame.frameValue,
                              'sample_u': [float(x) for x in frame.fieldOutputs['U'].values[0].data]}))
            return
        frames = []
        history_keys = None
        for index, frame in enumerate(step.frames):
            nodes = []
            rp = {}
            for value in frame.fieldOutputs['U'].values:
                key = value.instance.name + ':' + str(value.nodeLabel)
                data = list(value.data)
                if value.nodeLabel == 999999:
                    rp['u2'] = float(data[1])
                elif index == len(step.frames)-1:
                    nodes.append([key] + [float(x) for x in data])
            for value in frame.fieldOutputs['RF'].values:
                if value.nodeLabel == 999999:
                    rp['rf2'] = float(value.data[1])
            history = []
            energies = []
            fields = frame.fieldOutputs
            # Abaqus emits separate SDVn fields for this companion UMAT.
            for name, target in [('SDV2', history), ('SDV17', energies), ('SDV18', energies)]:
                if name != 'SDV2' and index != len(step.frames)-1:
                    continue
                if name not in fields:
                    continue
                for value in fields[name].values:
                    key = value.instance.name + ':' + str(value.elementLabel) + ':' + str(value.integrationPoint)
                    datum = value.data
                    try:
                        datum = datum[0]
                    except (TypeError, IndexError):
                        pass
                    target.append([name, key, float(datum)])
            history.sort()
            keys = [row[1] for row in history]
            if history_keys is None:
                history_keys = keys
            if keys != history_keys:
                raise RuntimeError('GP history coverage changes across accepted frames')
            frames.append({'frame_index': index, 'increment': int(frame.incrementNumber),
                           'step_time': float(frame.frameValue), 'rp': rp,
                           'history_values': [row[2] for row in history]})
        result = {'schema': 1, 'step': 'Step-1', 'step_number': 1, 'frames': frames,
                  'nodes': sorted(nodes), 'history_keys': history_keys, 'energies': sorted(energies),
                  'odb_path': os.path.abspath(odb_path), 'odb_sha256': before,
                  'history_semantics': 'UMAT SDV2 = SV_H_TRIAL at accepted output frames; committed-array equivalence unverified',
                  'energy_semantics': 'UMAT SDV17 fracture, SDV18 elastic: element totals repeated at each integration point',
                  'extractor_sha256': sha(os.path.abspath(__file__))}
    finally:
        odb.close()
    if sha(odb_path) != before:
        raise RuntimeError('ODB changed during read-only extraction')
    with gzip.open(output, 'wb') as stream:
        stream.write(json.dumps(result, allow_nan=False, separators=(',', ':')).encode('utf-8'))
    print('EXPORTED ' + output)


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--odb', required=True)
    p.add_argument('--output', default='snapshot.json.gz')
    p.add_argument('--inspect', action='store_true')
    a = p.parse_args()
    export(a.odb, a.output, a.inspect)
