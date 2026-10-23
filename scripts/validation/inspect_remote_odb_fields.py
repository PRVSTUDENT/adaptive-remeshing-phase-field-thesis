#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
inspect_remote_odb_fields.py
Inspects available fieldOutputs in Package 96-R4 ODB on HPC cluster,
specifically checking if RF contains degree of freedom 3 (phase field reaction force).
"""

import subprocess
import os
from pathlib import Path

REMOTE_DIR = "/scratch9/pr21vyci/runs/mode1_package96_r4_c5_transfer"
SSH_CONFIG = Path(os.environ["USERPROFILE"]) / ".ssh/codex_config"

REMOTE_PY = """
from odbAccess import openOdb
import sys

odb_path = '/scratch9/pr21vyci/runs/mode1_package96_r4_c5_transfer/M1_C5_PACKAGE96_R4_TRANSFER.odb'
odb = openOdb(odb_path, readOnly=True)

step1 = odb.steps['STATE_INJECTION']
fr1 = step1.frames[-1]

print('Step 1 FieldOutputs keys:')
for k in sorted(fr1.fieldOutputs.keys()):
    fo = fr1.fieldOutputs[k]
    comp = getattr(fo, 'componentLabels', None)
    print('  Field: %s, type: %s, components: %s' % (k, fo.type, str(comp)))

if 'RF' in fr1.fieldOutputs:
    rf = fr1.fieldOutputs['RF']
    print('\\nRF details:')
    print('  componentLabels: %s' % str(rf.componentLabels))
    # Sample nodes: node 1 (pinned), node 100 (diffuse flank), node 2000 (interior)
    sample_nodes = [1, 2, 50, 100, 500, 1000]
    for val in rf.values:
        if val.nodeLabel in sample_nodes:
            print('  Node %d RF: data=%s, mag=%s' % (val.nodeLabel, str(val.data), str(val.magnitude)))

if 'U' in fr1.fieldOutputs:
    u = fr1.fieldOutputs['U']
    print('\\nU details:')
    print('  componentLabels: %s' % str(u.componentLabels))
    for val in u.values:
        if val.nodeLabel in [1, 2, 100]:
            print('  Node %d U: data=%s' % (val.nodeLabel, str(val.data)))

odb.close()
print('\\nODB inspection complete.')
"""

RUNNER_SH = f"""#!/bin/bash
set -euo pipefail
cd "{REMOTE_DIR}"
if ! type module >/dev/null 2>&1; then source /etc/profile.d/lmod.sh; fi
module purge
module load gcc/11.4.0 intel/2024.2.0 abaqus/2023
abaqus python inspect_odb.py
"""

def main():
    py_path = Path("temp_inspect.py")
    sh_path = Path("temp_run.sh")
    py_path.write_text(REMOTE_PY, encoding="utf-8")
    with open(sh_path, "wb") as f:
        f.write(RUNNER_SH.replace("\r\n", "\n").encode("utf-8"))

    # scp
    subprocess.run(["scp", "-F", str(SSH_CONFIG), str(py_path), f"tu_freiberg:{REMOTE_DIR}/inspect_odb.py"], check=True)
    subprocess.run(["scp", "-F", str(SSH_CONFIG), str(sh_path), f"tu_freiberg:{REMOTE_DIR}/run_inspect.sh"], check=True)

    # run remote
    res = subprocess.run([
        "powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
        r".\.agents\scripts\Invoke-GuardedSsh.ps1",
        "-RemoteCommand", f"bash {REMOTE_DIR}/run_inspect.sh"
    ], capture_output=True, text=True)

    print("STDOUT:")
    print(res.stdout)
    if res.stderr:
        print("STDERR:")
        print(res.stderr)

    py_path.unlink(missing_ok=True)
    sh_path.unlink(missing_ok=True)

if __name__ == "__main__":
    main()
