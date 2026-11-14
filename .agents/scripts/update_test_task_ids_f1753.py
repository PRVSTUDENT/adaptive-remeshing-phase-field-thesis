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
    'tests/unit/test_f1749_time_causal_indicator.py',
    'tests/unit/test_f1750_local_sizing_probe.py',
    'tests/unit/test_f1751_case2_readiness.py',
    'tests/unit/test_f1752_case2_continuation_preflight.py'
]

f1752_str = '"F1752-CASE2-CONTROL-ONLY-CONTINUATION-EXECUTION-PREFLIGHT"'
f1753_str = '"F1753-CASE2-CONTROL-ONLY-CONTINUATION-EXECUTION"'

for path in files:
    if not os.path.exists(path):
        continue
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    if f1752_str in content and f1753_str not in content:
        content = content.replace(f1752_str, f'{f1752_str},\n            {f1753_str}')
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f'Updated {path}')

# Update test_f1749 line 140
if os.path.exists('tests/unit/test_f1749_time_causal_indicator.py'):
    with open('tests/unit/test_f1749_time_causal_indicator.py', 'r', encoding='utf-8') as f:
        c = f.read()
    if 'assert task["max_new_pbs_submissions"] == 0' in c:
        c = c.replace('assert task["max_new_pbs_submissions"] == 0', 'assert task["max_new_pbs_submissions"] in [0, 1]')
        with open('tests/unit/test_f1749_time_causal_indicator.py', 'w', encoding='utf-8') as f:
            f.write(c)
        print('Updated test_f1749 max_new_pbs_submissions')

# Update test_f1743 scope list
if os.path.exists('tests/unit/test_f1743_case3_transient_companion.py'):
    with open('tests/unit/test_f1743_case3_transient_companion.py', 'r', encoding='utf-8') as f:
        c = f.read()
    if '"ONE_BOUNDED_PBS_CASE2_CONTINUATION_EXECUTION"' not in c:
        c = c.replace('"ZERO_PBS_CASE2_PREFLIGHT_AND_DATACHECK"', '"ZERO_PBS_CASE2_PREFLIGHT_AND_DATACHECK", "ONE_BOUNDED_PBS_CASE2_CONTINUATION_EXECUTION"')
        with open('tests/unit/test_f1743_case3_transient_companion.py', 'w', encoding='utf-8') as f:
            f.write(c)
        print('Updated test_f1743 scope list for F1753')

print('All test task assertions updated successfully for F1753!')
