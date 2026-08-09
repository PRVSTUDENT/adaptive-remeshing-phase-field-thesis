#!/usr/bin/env python3
import subprocess
import sys

remote_cmd = """
cd /home/pr21vyci/projects/adaptive-remeshing
PYTHONPATH=.:tests/unit python3 -c "
from tests.unit.test_stage_f43rem3_native import TestStageF43REM3Native
t = TestStageF43REM3Native()
t.setUp()
try:
    t.test_T_working_directory_fallback_and_file_discovery_logic()
    print('test_T passed')
except Exception as e:
    print('test_T failed:', e)

try:
    t.test_Y_step_name_fail_closed_assertions()
    print('test_Y passed')
except Exception as e:
    print('test_Y failed:', e)

try:
    t.test_Z1_assembly_remesh_forbidden_and_model_adaptiveremesh_required()
    print('test_Z1 passed')
except Exception as e:
    print('test_Z1 failed:', e)
"
"""

p = subprocess.run(["ssh", "-F", r"C:\Users\pruth\.ssh\codex_config", "tu_freiberg", remote_cmd], capture_output=True, text=True)
print("STDOUT:")
print(p.stdout)
print("STDERR:")
print(p.stderr)
sys.exit(p.returncode)
