"""Build reviewed R4 from the authentic accepted R3 Step1 state, once."""
import csv
import hashlib
import io
import json
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts.state_transfer.driver_package157_r4 import AdaptiveContinuation, START, TARGETS

REL = 'models/pandey_kumar_mode1/157_c4_package157_c1_2_continuation_r4'
REMOTE = '/scratch9/pr21vyci/runs/mode1_c4_package157_c1_2_continuation_r4'
JOB = 'M1_C4_P157_C1_2_R4'
SOURCES = [
    'scripts/state_transfer/driver_package157_r4.py',
    'scripts/state_transfer/driver_package150_c1_2_continuation.py',
    'scripts/state_transfer/driver_package146_147_pdas_continuation.py',
    'scripts/state_transfer/c3_int_to_c4_spatial_mapping.py',
    'scripts/validation/extract_package148_iteration.py',
]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def text(path, value):
    path.write_bytes(value.replace('\r\n', '\n').encode('utf-8'))


def write_csv(path, fields, rows):
    stream = io.StringIO(newline='')
    writer = csv.writer(stream, lineterminator='\n')
    writer.writerow(fields)
    writer.writerows(rows)
    text(path, stream.getvalue())


def pbs(job, body, hours=8):
    return '''#!/bin/bash
#PBS -N %s
#PBS -l select=1:ncpus=1:mem=16gb
#PBS -l walltime=%02d:00:00
#PBS -q entry_imfdfkmq
#PBS -j oe
#PBS -r n
#PBS -o %s/%s.pbs_execution.log
#PBS -m abe
#PBS -M pr21vyci@mailserver.tu-freiberg.de
set -euo pipefail
RUN_DIR="%s"
cd "${RUN_DIR}"
export JOB_NAME="%s"
export NOTIFICATION_CONFIG="${NOTIFICATION_CONFIG:-${HOME}/.config/adaptive-remeshing/notifications.env}"
source "${RUN_DIR}/job_notifications.sh"
notification_load_config
notification_install_terminal_trap
notify_start
if ! type module >/dev/null 2>&1; then
 source /etc/profile.d/lmod.sh 2>/dev/null || source /usr/share/Modules/init/bash
fi
module purge
module load gcc/11.4.0 intel/2024.2.0 abaqus/2023
command -v ifort
%s
''' % (job, hours, REMOTE, job, REMOTE, job, body)


def manifest(files, runtime, job, pbs_name, purpose, hours):
    command = 'powershell -NoProfile -ExecutionPolicy Bypass -File .\\.agents\\scripts\\Invoke-GuardedSsh.ps1 -RemoteCommand "qsub -q entry_imfdfkmq '+REMOTE+'/'+pbs_name+'"'
    return dict(batch_name='MODE1_PACKAGE157_'+job, adapter='mode1-qualified-batch-v2',
        scientific_scope='MODE1', technical_stage='C1-2', configuration='MODE1_BASELINE',
        max_submissions=1, automatic_retry=False, remote_run_dir=REMOTE,
        runtime_root=REMOTE+'/runtime', runtime_source_hashes=runtime, files=files,
        scientific_predecessor_review='results/validation/package157_r4_scientific_review_and_registration_handoff.json',
        jobs=[dict(id=job, purpose=purpose, input='P157_MECHANICAL_DC.inp',
            datacheck='P157_MECHANICAL_DC.dat', additional_datachecks=['P157_PHASE_DC.dat'],
            pbs=pbs_name, queue='entry_imfdfkmq', cpus=1, memory_gb=16, walltime_hours=hours,
            execution='single-rank serial', max_submissions=1, depends_on=[],
            command=command, command_sha256=hashlib.sha256(command.encode()).hexdigest())],
        acceptance={job:purpose})


def build():
    package = ROOT/REL
    package.mkdir(exist_ok=False)
    previous = ROOT/'models/pandey_kumar_mode1/154_c4_package150_c1_2_continuation_r3'
    registration = json.loads((ROOT/'results/validation/package157_r4_registration_status_receipt.json').read_text())
    for name, expected in registration['verified_hashes'].items():
        assert sha(ROOT/name).upper() == expected
    endpoint = json.loads((ROOT/'results/validation/step1_equilibrium_checkpoint_1419113_endpoint.json').read_text())
    history = json.loads((ROOT/'results/validation/step1_equilibrium_checkpoint_1419113_full_history.json').read_text())
    nodes = endpoint['nodes']
    assert len(nodes) == len({r[0] for r in nodes}) == 7265 and endpoint['rp_u2'] == START
    h = {(r['element_id'],r['gp']): r['h_MPa'] for r in history['history_gp_records']}
    assert len(h) == 28224
    cards = (ROOT/'results/validation/step1_committed_solution_initial.inc').read_text()
    rows = [[float(v) for v in line.split(',')] for line in cards.splitlines() if line.strip() and not line.startswith('*')]
    assert len(rows) == 7056*3
    error = 0.
    for i in range(0,len(rows),3):
        assert [len(r) for r in rows[i:i+3]] == [8,8,3]
        eid = int(rows[i][0]); values = rows[i][1:]+rows[i+1]+rows[i+2]
        for gp in range(1,5):
            error = max(error,abs(values[7+gp]-h[eid,gp]))
    assert error < 1e-12
    for name in ['f42_mixed_uel.for','job_notifications.sh','M1_C4_PACKAGE150_C1_2_CONTINUATION.inp']:
        shutil.copyfile(previous/name,package/name)
    assert sha(package/'f42_mixed_uel.for') == 'ce8d5edcd2911dcb018bb15275271f874e7ea62b8fb48cf4a8297469a83acdd6'
    text(package/'initial_conditions_solution.inc',cards)
    write_csv(package/'nodal_displacements_initial.csv',['node_id','u1','u2'],[r[:3] for r in nodes])
    write_csv(package/'nodal_phase_field_initial.csv',['node_id','d'],[[r[0],r[3]] for r in nodes])
    write_csv(package/'d_lower_bounds.csv',['element_id','h0_1','h0_2','h0_3','h0_4'],
              [[eid]+[h[eid,gp] for gp in (1,2,4,3)] for eid in range(1,7057)])
    text(package/'active_set_boundary_cards.inc','*Boundary\n'+''.join('%d, 3, 3, %.17g\n'%(r[0],r[3]) for r in nodes))
    runtime = {name:sha(ROOT/name).upper() for name in SOURCES}
    initial_files = {p.name:sha(p) for p in package.iterdir()}
    pkg = dict(schema=1, package=157, revision='R4', files=initial_files,
        runtime_source_hashes=runtime, baseline_uy_mm=START, targets_mm=TARGETS,
        history_gp_order='MAPPER_ROW_FROM_UEL_PERIMETER', history_card_max_difference_MPa=error,
        restart_provenance=registration['verified_hashes'], max_outer=50, max_phase=20,
        minimum_increment_mm=5e-6, maximum_subdivision_level=2,
        physical_acceptance='UNVERIFIED', force_discrepancy_pct_max=5., raw_energy_discrepancy_pct_max=2.)
    text(package/'PACKAGE_MANIFEST.json',json.dumps(pkg,indent=2)+'\n')
    controller = AdaptiveContinuation(package, package/'unused', ROOT/SOURCES[-1], max_outer=50)
    controller.load()
    for role in ('mechanical','phase'):
        text(package/('P157_'+role.upper()+'_DC.inp'),controller._deck(1,role,controller.d0,
            set(controller.d0),controller.u0,controller.h0,TARGETS[0]))
    dc = '''#!/bin/bash
set -euo pipefail
cd "${1:?exact run directory required}"
for role in MECHANICAL PHASE; do
 job="P157_${role}_DC"
 test ! -e "${job}.dat"
 abaqus job="${job}" input="${job}.inp" user=f42_mixed_uel.for cpus=1 memory="16 gb" datacheck interactive > "${job}.stdout.txt" 2>&1
 test -f "${job}.dat"
 grep -q 'ANALYSIS DATACHECK COMPLETE' "${job}.dat"
 if grep -q '\\*\\*\\*ERROR' "${job}.dat"; then exit 66; fi
done
echo AUTHENTIC_DATACHECK_PASS_BOTH
'''
    text(package/'run_datacheck.sh',dc)
    startup = 'python3 "${RUN_DIR}/runtime/scripts/state_transfer/driver_package157_r4.py" --package "${RUN_DIR}" --output "${RUN_DIR}/continuation_${PBS_JOBID}" --extractor "${RUN_DIR}/runtime/scripts/validation/extract_package148_iteration.py"'
    text(package/('submit_'+JOB+'.pbs'),pbs(JOB,startup))
    qualification_body = '''test ! -e compute_datacheck
mkdir compute_datacheck
cp P157_MECHANICAL_DC.inp P157_PHASE_DC.inp f42_mixed_uel.for compute_datacheck/
bash "${RUN_DIR}/run_datacheck.sh" "${RUN_DIR}/compute_datacheck"
%s --startup-only > "${RUN_DIR}/compute_startup.json"
hostname > "${RUN_DIR}/compute_datacheck_host.txt"''' % startup
    dc_job='M1_C4_P157_R4_DC'
    text(package/('submit_'+dc_job+'.pbs'),pbs(dc_job,qualification_body,1))
    pkg['files'] = {p.name:sha(p) for p in package.iterdir() if p.name!='PACKAGE_MANIFEST.json'}
    text(package/'PACKAGE_MANIFEST.json',json.dumps(pkg,indent=2)+'\n')
    files={p.name:sha(p) for p in package.iterdir()}
    for filename, job, purpose, hours in [
        ('EXECUTION_MANIFEST.json',JOB,'Reviewed R4 forward subdivision from authentic Step1; convergence and full state preservation required; physical PASS only after matching-load force <=5% and raw energy <=2% review. No C5 execution or automatic PBS retry.',8),
        ('QUALIFICATION_EXECUTION_MANIFEST.json',dc_job,'Required authentic COMPUTE-NODE Abaqus mechanical/phase datachecks and actual R4 runtime startup; zero numerical continuation.',1)]:
        text(package/filename,json.dumps(manifest(files,runtime,job,'submit_'+job+'.pbs',purpose,hours),indent=2)+'\n')
    print(json.dumps(dict(package=REL,history_values=28224,max_difference_MPa=error,
                         baseline=START,targets=TARGETS),indent=2))


if __name__=='__main__':
    build()
