from __future__ import print_function
import os
import sys
import json

file_var_key = '__' + 'file' + '__'

runtime_dir_env = os.environ.get('F40_RUNTIME_DIR', os.environ.get('F38_RUNTIME_DIR', '')).strip()

if not runtime_dir_env:
    raise RuntimeError(
        'F40_RUNTIME_DIR or F38_RUNTIME_DIR is required because Abaqus/CAE noGUI may execute '
        'the script without defining ' + file_var_key + '.'
    )

runtime_dir = os.path.abspath(runtime_dir_env)

if not os.path.isdir(runtime_dir):
    raise RuntimeError(
        'Runtime dir does not exist: {0}'.format(runtime_dir)
    )

if runtime_dir not in sys.path:
    sys.path.insert(0, runtime_dir)

audit_data = {
    'protocol_version': 1,
    'entrypoint': 'run_f38_cae_diagnostic.py',
    'file_global_defined': file_var_key in globals(),
    'name_global': globals().get('__name__'),
    'runtime_dir': runtime_dir,
    'runtime_dir_source': 'F40_RUNTIME_DIR',
    'runtime_dir_exists': os.path.isdir(runtime_dir),
    'runtime_dir_on_sys_path': runtime_dir in sys.path,
    'bootstrap_passed': True
}

audit_path = os.environ.get('F40_INVOCATION_AUDIT', os.environ.get('F38_INVOCATION_AUDIT', 'CAE_INVOCATION_CONTEXT_AUDIT.json')).strip()
try:
    with open(audit_path, 'w') as f:
        json.dump(audit_data, f, indent=2)
except Exception:
    pass

from f38_cae_diagnostic_matrix import main

main()
