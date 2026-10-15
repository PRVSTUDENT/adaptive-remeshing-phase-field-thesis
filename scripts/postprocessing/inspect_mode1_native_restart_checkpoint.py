"""Read actual end-of-Step-1 state; compatible with Abaqus 2023 Python 2.7.

This checks donor readiness, not successful recipient restoration or Method C
validation. It never manufactures missing displacement or state variables.
"""
from __future__ import print_function
import argparse
import json
import math
import os


def finite(value):
    value = float(value)
    if math.isnan(value) or math.isinf(value):
        raise ValueError('Nonfinite donor state')
    return value


def inspect(odb):
    if 'Step-1' not in odb.steps:
        raise ValueError('Donor Step-1 absent')
    frame = odb.steps['Step-1'].frames[-1]
    if abs(finite(frame.frameValue)-1.0) > 1.e-8:
        raise ValueError('Donor has not reached end of Step-1')
    fields = frame.fieldOutputs
    state = {'step_time': float(frame.frameValue), 'increment': int(frame.incrementNumber)}
    for name in ('U', 'RF'):
        if name not in fields:
            raise ValueError('Missing donor field ' + name)
        values = [v for v in fields[name].values if v.nodeLabel == 999999]
        if len(values) != 1:
            raise ValueError('Missing or ambiguous reference point ' + name)
        state[name+'_rp'] = [finite(v) for v in values[0].data]
    if abs(state['U_rp'][1]-0.005) > 1.e-9:
        raise ValueError('Donor handoff displacement differs from 0.005 mm')
    for name in ('SDV2', 'SDV14', 'SDV17', 'SDV18'):
        if name not in fields:
            raise ValueError('Missing donor state output ' + name)
        values = [finite(v.data) for v in fields[name].values]
        if not values:
            raise ValueError('Empty donor state output ' + name)
        state[name] = dict(count=len(values), minimum=min(values), maximum=max(values))
    if state['SDV2']['minimum'] < -1.e-9:
        raise ValueError('Negative donor history output')
    if state['SDV14']['minimum'] < -1.e-6 or state['SDV14']['maximum'] > 1.000001:
        raise ValueError('Donor damage outside admissible range')
    state['rp_reaction_N'] = state['RF_rp'][1]*1000.0
    state['checkpoint_readiness'] = 'END_STATE_OUTPUT_VERIFIED'
    state['recipient_restoration'] = 'NOT_YET_TESTED'
    return state


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--odb', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    if not os.path.isfile(args.odb):
        raise ValueError('Exact donor ODB missing')
    from odbAccess import openOdb
    odb = openOdb(args.odb, readOnly=True)
    try:
        result = inspect(odb)
    finally:
        odb.close()
    with open(args.output, 'w') as stream:
        json.dump(result, stream, indent=2)
    print(json.dumps(result))


if __name__ == '__main__':
    main()
