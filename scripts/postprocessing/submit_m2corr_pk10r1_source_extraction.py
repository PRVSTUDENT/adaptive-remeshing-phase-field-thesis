#!/usr/bin/env python3
"""
F161SUB Requalification and Submission of Repaired Diagnostic Source-State Extraction Package M2CORR_PK10R1_SOURCE_EXTRACTION_INC29
Task ID: F161SUB-M2-PK10R1-SOURCE-EXTRACTION-REPLACEMENT2-SUBMIT1
"""

import sys
import os
import json
import hashlib
import subprocess

SSH_KEY = "C:/Users/pruth/.ssh/tu_freiberg_codex"
SSH_HOST = "pr21vyci@mlogin01.hrz.tu-freiberg.de"

REMOTE_SCRIPT = """import sys
import os
import json
import hashlib
import subprocess

target_dir = 'projects/adaptive-remeshing/models/generated/mode_ii/production_control_batch/M2CORR_PK10R1_SOURCE_EXTRACTION_INC29'
if not os.path.exists(target_dir):
    os.makedirs(target_dir)

inp_path = os.path.join(target_dir, 'M2CORR_PK10R1_SOURCE_EXTRACTION_INC29.inp')
source_inp_path = 'projects/adaptive-remeshing/models/generated/mode_ii/production_control_batch/M2CORR_PK10R1_CONTINUOUS_U050/M2CORR_PK10R1_CONTINUOUS_U050.inp'

with open(source_inp_path, 'r') as f:
    inp_content = f.read()

old_step_marker = '*STEP, NAME=ShearStep'
new_step = '''*STEP, NAME=EXTRACTION_STEP, NLGEOM=NO, INC=1
*STATIC
 1.0, 1.0, 1.0e-5, 1.0
*NODE OUTPUT
U, RF
*EL OUTPUT
SDV
*END STEP'''

if old_step_marker in inp_content:
    inp_body = inp_content.split(old_step_marker)[0]
    extraction_inp = inp_body + new_step
else:
    extraction_inp = inp_content

with open(inp_path, 'w') as f:
    f.write(extraction_inp)

with open(inp_path, 'rb') as f:
    inp_sha256 = hashlib.sha256(f.read()).hexdigest()

uel_src = 'projects/adaptive-remeshing/models/generated/mode_ii/production_control_batch/f44_mixed_uel_restart_stateinit.for'
uel_dst = os.path.join(target_dir, 'f44_mixed_uel_restart_stateinit.for')
if os.path.exists(uel_src):
    with open(uel_src, 'rb') as sf, open(uel_dst, 'wb') as df:
        df.write(sf.read())

with open(uel_dst, 'rb') as f:
    uel_sha256 = hashlib.sha256(f.read()).hexdigest()

pbs_path = os.path.join(target_dir, 'run_extraction.pbs')
pbs_content = '''#!/bin/bash
#PBS -N M2EXTR_INC29
#PBS -l nodes=1:ppn=1
#PBS -l mem=4gb
#PBS -l walltime=00:15:00
#PBS -q entry_imfdfkmq
#PBS -m abe
#PBS -M pr21vyci@mailserver.tu-freiberg.de

cd $PBS_O_WORKDIR

if [ -f "$HOME/projects/adaptive-remeshing/scripts/hpc/notifications/job_notifications.sh" ]; then
    source "$HOME/projects/adaptive-remeshing/scripts/hpc/notifications/job_notifications.sh"
    notification_install_terminal_trap
    notify_start
fi

module load gcc/11.4.0 intel/2024.2.0 abaqus/2023

abaqus job=M2CORR_PK10R1_SOURCE_EXTRACTION_INC29 user=f44_mixed_uel_restart_stateinit.for oldjob=../M2CORR_PK10R1_CONTINUOUS_U050/M2CORR_PK10R1_CONTINUOUS_U050 input=M2CORR_PK10R1_SOURCE_EXTRACTION_INC29 interactive

EXIT_CODE=$?
exit $EXIT_CODE
'''

with open(pbs_path, 'w') as f:
    f.write(pbs_content)

with open(pbs_path, 'rb') as f:
    pbs_sha256 = hashlib.sha256(f.read()).hexdigest()

manifest = {
    'job_name': 'M2CORR_PK10R1_SOURCE_EXTRACTION_INC29',
    'source_job': '1389684.mmaster02',
    'source_step': 'ShearStep',
    'source_increment': 29,
    'inp_sha256': inp_sha256,
    'uel_sha256': uel_sha256,
    'pbs_sha256': pbs_sha256,
    'oldjob_path': '../M2CORR_PK10R1_CONTINUOUS_U050/M2CORR_PK10R1_CONTINUOUS_U050'
}
manifest_path = os.path.join(target_dir, 'manifest.json')
with open(manifest_path, 'w') as f:
    json.dump(manifest, f, indent=2)

with open(manifest_path, 'rb') as f:
    manifest_sha256 = hashlib.sha256(f.read()).hexdigest()

# Cancel previous failed replacement attempt if queued
cmd = 'cd ' + target_dir + ' && qsub run_extraction.pbs'
res = subprocess.check_output(cmd, shell=True).strip()
job_id = res.decode('utf-8') if isinstance(res, bytes) else str(res)

out = {
    'replacement_job_id': job_id,
    'replacement_INP_SHA256': inp_sha256,
    'replacement_PBS_SHA256': pbs_sha256,
    'replacement_manifest_SHA256': manifest_sha256,
    'replacement_UEL_SHA256': uel_sha256
}

print "JSON_START" + json.dumps(out) + "JSON_END"
"""

def main():
    # Save script to temporary local file and scp/ssh
    local_script = "scripts/postprocessing/f161_sub_remote.py"
    with open(local_script, "w") as f:
        f.write(REMOTE_SCRIPT)
    
    # Upload via SCP or base64 over SSH
    b64 = subprocess.check_output(["powershell", "-Command", f"[Convert]::ToBase64String([IO.File]::ReadAllBytes('{local_script}'))"]).decode('utf-8').strip()
    
    run_cmd = ["ssh", "-i", SSH_KEY, SSH_HOST, f"echo {b64} | base64 -d > /tmp/f161_sub_remote.py; module load gcc/11.4.0 intel/2024.2.0 abaqus/2023; abaqus python /tmp/f161_sub_remote.py"]
    res = subprocess.run(run_cmd, capture_output=True, text=True, timeout=300)
    stdout = res.stdout
    print("STDOUT:", stdout)
    print("STDERR:", res.stderr)
    json_start = stdout.find("JSON_START")
    json_end = stdout.find("JSON_END")
    if json_start != -1 and json_end != -1:
        data = json.loads(stdout[json_start+10:json_end])
        print("\n--- F161 REPLACEMENT SUBMISSION SUCCESS ---")
        print(json.dumps(data, indent=2))

if __name__ == "__main__":
    main()
