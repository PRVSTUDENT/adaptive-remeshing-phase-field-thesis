# -*- coding: utf-8 -*-
import os

files = [
    'tests/unit/test_f1740_case3_multistate_design.py',
    'tests/unit/test_f1741_case3_multistate_remeshing.py',
    'tests/unit/test_f1742_transient_donor_recovery.py',
    'tests/unit/test_f1743_case3_transient_companion.py',
    'tests/unit/test_f1744_case3_5state_remesh.py',
    'tests/unit/test_f1745_case3_envelope_qualification.py',
    'tests/unit/test_f1746_case3_envelope_execution_readiness.py',
    'tests/unit/test_f1747_contrast_prototype.py',
    'tests/unit/test_f1748_damage_field_availability.py',
    'tests/unit/test_f1749_time_causal_indicator.py'
]

f1750_str = '"F1750-LOCAL-NATIVE-DAMAGE-SIZING-PROBE"'
f1751_str = '"F1751-CASE2-METHOD-A-DAMAGE-RESOLUTION-AND-CONTINUATION-READINESS"'

for path in files:
    if not os.path.exists(path):
        continue
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    if f1750_str in content and f1751_str not in content:
        content = content.replace(f1750_str, f'{f1750_str},\n            {f1751_str}')
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f'Updated {path}')

# Also check test_f1743 scope_boundary
if os.path.exists('tests/unit/test_f1743_case3_transient_companion.py'):
    with open('tests/unit/test_f1743_case3_transient_companion.py', 'r', encoding='utf-8') as f:
        c = f.read()
    if '"ZERO_PBS_CASE2_READINESS_DIAGNOSIS"' not in c:
        c = c.replace('"ZERO_PBS_LOCAL_NATIVE_SIZING_PROBE"', '"ZERO_PBS_LOCAL_NATIVE_SIZING_PROBE", "ZERO_PBS_CASE2_READINESS_DIAGNOSIS"')
        with open('tests/unit/test_f1743_case3_transient_companion.py', 'w', encoding='utf-8') as f:
            f.write(c)
        print('Updated test_f1743 scope list for F1751')

print('All test task assertions updated successfully for F1751!')
