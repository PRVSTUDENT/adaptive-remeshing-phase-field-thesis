# -*- coding: utf-8 -*-
import re

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

f1749_str = '"F1749-TIME-CAUSAL-DAMAGE-INDICATOR-IMPLEMENTATION-AND-VALIDATION"'
f1750_str = '"F1750-LOCAL-NATIVE-DAMAGE-SIZING-PROBE"'

for path in files:
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    if f1749_str in content and f1750_str not in content:
        content = content.replace(f1749_str, f'{f1749_str},\n            {f1750_str}')
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f'Updated {path}')

# Also check test_f1743 scope_boundary
with open('tests/unit/test_f1743_case3_transient_companion.py', 'r', encoding='utf-8') as f:
    c = f.read()
if '"ZERO_PBS_LOCAL_NATIVE_SIZING_PROBE"' not in c:
    c = c.replace('"ZERO_PBS_TIME_CAUSAL_DAMAGE_INDICATOR"', '"ZERO_PBS_TIME_CAUSAL_DAMAGE_INDICATOR", "ZERO_PBS_LOCAL_NATIVE_SIZING_PROBE"')
    with open('tests/unit/test_f1743_case3_transient_companion.py', 'w', encoding='utf-8') as f:
        f.write(c)
    print('Updated test_f1743 scope list')

print('All test task assertions updated successfully for F1750!')
