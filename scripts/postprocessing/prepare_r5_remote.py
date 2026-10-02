import os
import shutil
import hashlib
import json

base_dir = os.path.expanduser('~/projects/adaptive-remeshing/models/generated/mode_ii/production_control_batch')
r5_dir = os.path.join(base_dir, 'M2CORR_PK10R1_SAMEMESH_RESTART_VALIDATION_R5')

if not os.path.exists(r5_dir):
    os.makedirs(r5_dir)

bin_src = os.path.join(base_dir, 'M2CORR_PK10R1_SAMEMESH_RESTART_VALIDATION', 'PK10R1_INC29_SOURCE_STATE.bin')
if not os.path.exists(bin_src):
    bin_src = os.path.join(base_dir, 'PK10R1_INC29_SOURCE_STATE.bin')

shutil.copy2(bin_src, os.path.join(r5_dir, 'PK10R1_INC29_SOURCE_STATE.bin'))
shutil.copy2(os.path.join(base_dir, 'f44_mixed_uel_restart_stateinit.for'), os.path.join(r5_dir, 'f44_mixed_uel_restart_stateinit.for'))

from odbAccess import openOdb
odb_path = os.path.expanduser('~/projects/adaptive-remeshing/models/generated/mode_ii/production_control_batch/M2CORR_PK10R1_NATIVE_RESTART_CONTROL_INC29_R1/M2CORR_PK10R1_CONTINUOUS_U050_STATECAPTURE_R1.odb')
odb = openOdb(odb_path, readOnly=True)
step = odb.steps['ShearStep']
frame29 = step.frames[29]
u_field = frame29.fieldOutputs['U']

full_bnd_path = os.path.join(r5_dir, 'PK10R1_INC29_PRIMARY_STATE_BOUNDARY.inp')
u3_bnd_path   = os.path.join(r5_dir, 'PK10R1_INC29_U3_ONLY_BOUNDARY.inp')

u3_count = 0
full_count = 0

with open(full_bnd_path, 'w') as f_full:
    with open(u3_bnd_path, 'w') as f_u3:
        for val in u_field.values:
            nid = val.nodeLabel
            u1 = float(val.data[0]) if len(val.data) >= 1 and val.data[0] is not None else 0.0
            u2 = float(val.data[1]) if len(val.data) >= 2 and val.data[1] is not None else 0.0
            u3 = float(val.data[2]) if len(val.data) >= 3 and val.data[2] is not None else 0.0
            
            f_full.write('%d, 1, 1, %.16e\n' % (nid, u1))
            f_full.write('%d, 2, 2, %.16e\n' % (nid, u2))
            f_full.write('%d, 3, 3, %.16e\n' % (nid, u3))
            full_count += 3
            
            f_u3.write('%d, 3, 3, %.16e\n' % (nid, u3))
            u3_count += 1

print('Generated full boundary file with %d lines.' % full_count)
print('Generated U3-only boundary file with %d lines.' % u3_count)
odb.close()

ref_inp_path = os.path.join(base_dir, 'M2CORR_PK10R1_SAMEMESH_RESTART_VALIDATION/M2CORR_PK10R1_SAMEMESH_RESTART_VALIDATION.inp')
with open(ref_inp_path) as f:
    text = f.read()

mesh_part = text.split('*STEP, NAME=STATE_INIT')[0]

r5_steps = """*STEP, NAME=STATE_INSTALL, NLGEOM=NO, INC=10
*STATIC
1.0, 1.0, 1.0e-5, 1.0
*BOUNDARY, OP=NEW
*INCLUDE, INPUT=PK10R1_INC29_PRIMARY_STATE_BOUNDARY.inp
*OUTPUT, FIELD, FREQ=1
*NODE OUTPUT, NSET=N_RP
U, RF
*END STEP

*STEP, NAME=MECH_EQUILIBRATION, NLGEOM=NO, INC=100
*STATIC
1.0, 1.0, 1.0e-5, 1.0
*BOUNDARY, OP=NEW
N_BOTTOM, 1, 2, 0.0
N_TOP, 2, 2, 0.0
N_RP, 1, 1, 0.010143300518393517
N_RP, 2, 2, 0.0
*INCLUDE, INPUT=PK10R1_INC29_U3_ONLY_BOUNDARY.inp
*OUTPUT, FIELD, FREQ=1
*NODE OUTPUT, NSET=N_RP
U, RF
*END STEP

*STEP, NAME=PHASE_RELEASE, NLGEOM=NO, INC=100
*STATIC
1.0, 1.0, 1.0e-5, 1.0
*BOUNDARY, OP=NEW
N_BOTTOM, 1, 2, 0.0
N_TOP, 2, 2, 0.0
N_RP, 1, 1, 0.010143300518393517
N_RP, 2, 2, 0.0
*OUTPUT, FIELD, FREQ=1
*NODE OUTPUT, NSET=N_RP
U, RF
*END STEP

*STEP, NAME=CONTINUATION, NLGEOM=NO, INC=10000
*STATIC
0.001, 1.0, 1.0e-9, 0.02
*BOUNDARY, OP=MOD
N_RP, 1, 1, 0.050000
N_RP, 2, 2, 0.0
*OUTPUT, FIELD, FREQ=1
*NODE OUTPUT, NSET=N_TOP
U, RF
*NODE OUTPUT, NSET=N_BOTTOM
U, RF
*NODE OUTPUT, NSET=N_RP
U, RF
*NODE PRINT, FREQ=1
U, RF
*EL PRINT, FREQ=1, ELSET=E_QUAD_MECH
SDV14, SDV15, SDV16
*END STEP
"""


inp_r5_path = os.path.join(r5_dir, 'M2CORR_PK10R1_SAMEMESH_RESTART_VALIDATION_R5.inp')
with open(inp_r5_path, 'w') as f:
    f.write(mesh_part + r5_steps)

pbs_r5_path = os.path.join(r5_dir, 'submit_job.pbs')
pbs_content = """#PBS -N M2R5_SAMEMESH
#PBS -l select=1:ncpus=1:mem=16gb
#PBS -l walltime=24:00:00
#PBS -q normal_imfdfkmq
#PBS -m abe
#PBS -M pr21vyci@mailserver.tu-freiberg.de

cd $PBS_O_WORKDIR
source $HOME/projects/adaptive-remeshing/scripts/hpc/notifications/job_notifications.sh
notification_install_terminal_trap

module load abaqus/2023

abaqus job=M2CORR_PK10R1_SAMEMESH_RESTART_VALIDATION_R5 user=f44_mixed_uel_restart_stateinit.for interactive
"""
with open(pbs_r5_path, 'w') as f:
    f.write(pbs_content)

def sha256_file(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        while True:
            chunk = f.read(8192)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()

inp_hash = sha256_file(inp_r5_path)
uel_hash = sha256_file(os.path.join(r5_dir, 'f44_mixed_uel_restart_stateinit.for'))
pbs_hash = sha256_file(pbs_r5_path)
bin_hash = sha256_file(os.path.join(r5_dir, 'PK10R1_INC29_SOURCE_STATE.bin'))

manifest = {
    'job_name': 'M2CORR_PK10R1_SAMEMESH_RESTART_VALIDATION_R5',
    'inp_sha256': inp_hash,
    'uel_sha256': uel_hash,
    'pbs_sha256': pbs_hash,
    'bin_sha256': bin_hash,
    'resources': '1 CPU / 16 GB / 24:00:00 / entry_imfdfkmq / Abaqus 2023'
}

manifest_path = os.path.join(r5_dir, 'manifest.json')
with open(manifest_path, 'w') as f:
    json.dump(manifest, f, indent=2)

manifest_hash = sha256_file(manifest_path)

print('================================================================================')
print('M2CORR_PK10R1_SAMEMESH_RESTART_VALIDATION_R5 PACKAGE PREPARED')
print('================================================================================')
print('Directory:       ' + r5_dir)
print('INP SHA256:      ' + inp_hash)
print('UEL SHA256:      ' + uel_hash)
print('PBS SHA256:      ' + pbs_hash)
print('BIN SHA256:      ' + bin_hash)
print('Manifest SHA256: ' + manifest_hash)
