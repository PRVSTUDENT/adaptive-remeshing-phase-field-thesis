"""Read-only donor diagnostic. Run with Abaqus Python; never changes an ODB.

E/A below is a diagnostic proxy, NOT Abaqus' documented sizing formula.
"""
from __future__ import print_function
import hashlib
import json
import os
from odbAccess import openOdb

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def digest(path):
    h = hashlib.sha256()
    with open(path, 'rb') as stream:
        for block in iter(lambda: stream.read(1048576), b''):
            h.update(block)
    return h.hexdigest()

def read_fields(relative):
    path = os.path.join(ROOT, relative)
    if not os.path.isfile(path):
        raise IOError(path)
    odb = openOdb(path, readOnly=True)
    try:
        frame = odb.steps['RECOVERY_STEP'].frames[-1]
        fields = {}
        for name in ('MISESERI', 'MISESAVG'):
            values = {}
            for v in frame.fieldOutputs[name].values:
                key = (v.instance.name, v.elementLabel)
                if key in values:
                    raise ValueError('Multiple field values per element: %s %s' % (relative, name))
                values[key] = float(v.data)
            fields[name] = values
        return fields, {'path': relative.replace('\\', '/'), 'sha256': digest(path),
                        'frame_description': frame.description,
                        'elements': len(fields['MISESERI'])}
    finally:
        odb.close()

def quantiles(values):
    values = sorted(values)
    if not values:
        return None
    return dict((str(p), values[int((len(values)-1)*p/100.0)]) for p in (0, 25, 50, 75, 95, 100))

def main():
    base = 'models/pandey_kumar_mode1/259_f1809_multistate_recovery/'
    cases = {
        '2': ('case2/', ['PK_C2_STATE1_PREANALYSIS', 'PK_C2_STATE2_HOLE_ARREST',
                        'PK_C2_STATE3_DISTAL_NUCLEATION', 'PK_C2_STATE4_OUTER_PROPAGATION'],
              'PK_HOLE_MULTISTATE_RECOVERY'),
        '3': ('case3/', ['SEC43_C3_STATE1_INITIATION', 'SEC43_C3_STATE2_HOLE_ARREST',
                        'SEC43_C3_STATE3_PROPAGATION'], 'SEC43_MULTISTATE_RECOVERY')}
    result = {'scope': 'Read-only existing Cases 2/3 recovery donors; no solver or remeshing',
              'warning': 'E/A is a diagnostic proxy, not the Abaqus sizing formula or a candidate indicator.',
              'cases': {}}
    for case, (folder, names, envelope) in sorted(cases.items()):
        states = [read_fields(base+folder+n+'.odb') for n in names]
        env, provenance = read_fields(base+folder+envelope+'.odb')
        keys = set(env['MISESERI'])
        if not keys or set(env['MISESAVG']) != keys:
            raise ValueError('Empty or inconsistent envelope support')
        for state, _ in states:
            if set(state['MISESERI']) != keys or set(state['MISESAVG']) != keys:
                raise ValueError('Inconsistent element support')
        errors, averages, factors = [], [], []
        for key in keys:
            es = [s['MISESERI'][key] for s, _ in states]
            av = [s['MISESAVG'][key] for s, _ in states]
            errors.append(abs(env['MISESERI'][key]-max(es)))
            averages.append(abs(env['MISESAVG'][key]-sum(av)/len(av)))
            if min(av) > 1e-12 and env['MISESAVG'][key] > 1e-12:
                reference = max(e/a for e, a in zip(es, av))
                if reference > 1e-12:
                    factors.append((env['MISESERI'][key]/env['MISESAVG'][key])/reference)
        if max(errors) > 1e-6*max(1.0, max(env['MISESERI'].values())):
            raise ValueError('Stored error envelope does not match maximum')
        if max(averages) > 1e-6*max(1.0, max(env['MISESAVG'].values())):
            raise ValueError('Stored stress envelope does not match mean')
        if not factors:
            raise ValueError('No valid diagnostic ratios')
        result['cases'][case] = {
            'envelope': provenance, 'states': [p for _, p in states],
            'max_absolute_max_error_residual': max(errors),
            'max_absolute_mean_stress_residual': max(averages),
            'proxy_ratio_envelope_over_max_state_ratio_quantiles': quantiles(factors),
            'proxy_valid_elements': len(factors),
            'proxy_fraction_above_1_01': sum(x > 1.01 for x in factors)/float(len(factors)),
            'state_stress_field_ranges': [dict(path=p['path'], minimum=min(s['MISESAVG'].values()),
                                             maximum=max(s['MISESAVG'].values())) for s, p in states]}
    out = os.path.join(ROOT, 'results/validation/native_miseseri_envelope_efficiency.json')
    with open(out, 'w') as stream:
        json.dump(result, stream, indent=2, sort_keys=True)
        stream.write('\n')
    print(out)

if __name__ == '__main__':
    main()
