from __future__ import print_function
import json
import math
import os
import sys
import traceback

def count_finite_values(values):
    count = 0
    for value in values:
        datum = float(value.data)
        if not math.isnan(datum) and not math.isinf(datum):
            count += 1
    return count

def compatibility_self_test():
    class Value(object):
        def __init__(self, data):
            self.data = data
    values = [Value(1.0), Value(float('nan')), Value(float('inf')), Value(-2.0)]
    return count_finite_values(values) == 2

def write_result(payload):
    output_dir = os.environ['F19_OUTPUT_DIR']
    path = os.path.join(output_dir, 'ABAQUS_PYTHON_COMPATIBILITY.json')
    with open(path, 'wb') as handle:
        handle.write((json.dumps(payload, indent=2, sort_keys=True) + '\n').encode('utf-8'))

if __name__ == '__main__':
    try:
        passed = compatibility_self_test()
        write_result({'compatible': bool(passed), 'python_version': sys.version, 'return_code': 0 if passed else 1})
        raise SystemExit(0 if passed else 1)
    except Exception:
        try:
            write_result({'compatible': False, 'return_code': 2, 'traceback': traceback.format_exc()})
        except Exception:
            pass
        raise SystemExit(2)
