"""Build reviewed Package 157 Revision 6 candidate from authentic Checkpoint 01."""
import csv
import hashlib
import io
import json
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts.state_transfer.driver_package157_r6 import AdaptiveContinuationR6, START, TARGETS

REL = 'models/pandey_kumar_mode1/157_c4_package157_c1_2_continuation_r6'
REMOTE = '/scratch9/pr21vyci/runs/mode1_c4_package157_c1_2_continuation_r6'
JOB = 'M1_C4_P157_C1_2_R6'
DC_JOB = 'M1_C4_P157_R6_DC'

SOURCES = [
    'scripts/state_transfer/driver_package157_r6.py',
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
    command = 'powershell -NoProfile -ExecutionPolicy Bypass -File .\\.agents\\scripts\\Invoke-GuardedSsh.ps1 -RemoteCommand "qsub -q entry_imfdfkmq ' + REMOTE + '/' + pbs_name + '"'
    return dict(batch_name='MODE1_PACKAGE157_' + job, adapter='mode1-qualified-batch-v2',
        scientific_scope='MODE1', technical_stage='C1-2', configuration='MODE1_BASELINE',
        max_submissions=1, automatic_retry=False, remote_run_dir=REMOTE,
        runtime_root=REMOTE + '/runtime', runtime_source_hashes=runtime, files=files,
        scientific_predecessor_review='results/validation/package157_r6_restart_candidate_projection.json',
        jobs=[dict(id=job, purpose=purpose, input='P157_MECHANICAL_DC.inp',
            datacheck='P157_MECHANICAL_DC.dat', additional_datachecks=['P157_PHASE_DC.dat'],
            pbs=pbs_name, queue='entry_imfdfkmq', cpus=1, memory_gb=16, walltime_hours=hours,
            execution='single-rank serial', max_submissions=1, depends_on=[],
            command=command, command_sha256=hashlib.sha256(command.encode()).hexdigest())],
        acceptance={job: purpose})


def build():
    package = ROOT / REL
    if package.exists():
        shutil.rmtree(package)
    package.mkdir(parents=True, exist_ok=False)

    p157_r5 = ROOT / 'models/pandey_kumar_mode1/157_c4_package157_c1_2_continuation_r5'
    chkpt_path = p157_r5 / 'converged_checkpoint_01.json'
    chkpt = json.loads(chkpt_path.read_text())

    assert chkpt['target_uy_mm'] == START
    assert chkpt['coupled_convergence'] is True

    # Copy authentic checkpoint 01
    shutil.copyfile(chkpt_path, package / 'initial_checkpoint_01.json')

    nodes_disp = chkpt['displacement']
    nodes_damage = chkpt['damage']
    gp_history = chkpt['history']

    assert len(nodes_disp) == 7265
    assert len(nodes_damage) == 7265
    assert len(gp_history) == 28224

    u_dict = {row[0]: (row[1], row[2]) for row in nodes_disp}
    d_dict = {row[0]: row[1] for row in nodes_damage}
    h_dict = {(row[0], row[1]): row[2] for row in gp_history}

    # Initial conditions cards for solution SVARS
    cards_lines = ['*Initial Conditions, type=SOLUTION\n']
    for eid in range(1, 7057):
        h1 = h_dict[(eid, 1)]
        h2 = h_dict[(eid, 2)]
        h3 = h_dict[(eid, 3)]
        h4 = h_dict[(eid, 4)]
        cards_lines.append('%d, 0, 0, 0, 0, 0, 0, 0\n' % eid)
        cards_lines.append('0, %.17g, %.17g, %.17g, %.17g, 0, 0, 0\n' % (h1, h2, h3, h4))
        cards_lines.append('0, 0, 0\n')
    cards_text = ''.join(cards_lines)

    for name in ['f42_mixed_uel.for', 'job_notifications.sh', 'M1_C4_PACKAGE150_C1_2_CONTINUATION.inp']:
        shutil.copyfile(p157_r5 / name, package / name)
    assert sha(package / 'f42_mixed_uel.for') == 'ce8d5edcd2911dcb018bb15275271f874e7ea62b8fb48cf4a8297469a83acdd6'

    text(package / 'initial_conditions_solution.inc', cards_text)
    write_csv(package / 'nodal_displacements_initial.csv', ['node_id', 'u1', 'u2'],
              [[n, u_dict[n][0], u_dict[n][1]] for n in sorted(u_dict)])
    write_csv(package / 'nodal_phase_field_initial.csv', ['node_id', 'd'],
              [[n, d_dict[n]] for n in sorted(d_dict)])
    write_csv(package / 'd_lower_bounds.csv', ['element_id', 'h0_1', 'h0_2', 'h0_3', 'h0_4'],
              [[eid] + [h_dict[(eid, gp)] for gp in (1, 2, 4, 3)] for eid in range(1, 7057)])
    text(package / 'active_set_boundary_cards.inc',
         '*Boundary\n' + ''.join('%d, 3, 3, %.17g\n' % (n, d_dict[n]) for n in sorted(d_dict)))

    runtime = {name: sha(ROOT / name).upper() for name in SOURCES}
    initial_files = {p.name: sha(p) for p in package.iterdir()}

    pkg = dict(schema=1, package=157, revision='R6', files=initial_files,
        runtime_source_hashes=runtime, baseline_uy_mm=START, targets_mm=TARGETS,
        restart_checkpoint_source='converged_checkpoint_01.json',
        restart_checkpoint_sha256=sha(chkpt_path),
        history_gp_order='MAPPER_ROW_FROM_UEL_PERIMETER',
        max_outer=130, max_phase=20,
        substep_size_mm=5e-6,
        physical_acceptance='UNVERIFIED', force_discrepancy_pct_max=5.0, raw_energy_discrepancy_pct_max=2.0)
    text(package / 'PACKAGE_MANIFEST.json', json.dumps(pkg, indent=2) + '\n')

    controller = AdaptiveContinuationR6(package, package / 'unused', ROOT / SOURCES[-1], max_outer=130)
    controller.load()
    for role in ('mechanical', 'phase'):
        text(package / ('P157_' + role.upper() + '_DC.inp'), controller._deck(1, role, controller.d0,
            set(controller.d0), controller.u0, controller.h0, TARGETS[0]))

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
    text(package / 'run_datacheck.sh', dc)

    startup = 'python3 "${RUN_DIR}/runtime/scripts/state_transfer/driver_package157_r6.py" --package "${RUN_DIR}" --output "${RUN_DIR}/continuation_${PBS_JOBID}" --extractor "${RUN_DIR}/runtime/scripts/validation/extract_package148_iteration.py"'
    text(package / ('submit_' + JOB + '.pbs'), pbs(JOB, startup, 8))

    qualification_body = '''test ! -e compute_datacheck
mkdir compute_datacheck
cp P157_MECHANICAL_DC.inp P157_PHASE_DC.inp f42_mixed_uel.for compute_datacheck/
bash "${RUN_DIR}/run_datacheck.sh" "${RUN_DIR}/compute_datacheck"
%s --startup-only > "${RUN_DIR}/compute_startup.json"
hostname > "${RUN_DIR}/compute_datacheck_host.txt"''' % startup
    text(package / ('submit_' + DC_JOB + '.pbs'), pbs(DC_JOB, qualification_body, 1))

    pkg['files'] = {p.name: sha(p) for p in package.iterdir() if p.name != 'PACKAGE_MANIFEST.json'}
    text(package / 'PACKAGE_MANIFEST.json', json.dumps(pkg, indent=2) + '\n')
    files = {p.name: sha(p) for p in package.iterdir()}

    for filename, job_name, purpose, hours in [
        ('EXECUTION_MANIFEST.json', JOB, 'Reviewed R6 restart continuation (+5 nm increment to uy=0.00186531 mm, max_outer=130) from authentic Checkpoint 01; convergence and full state preservation required; physical PASS only after matching-load force <=5% and raw energy <=2% review. No C5 execution or automatic PBS retry.', 8),
        ('QUALIFICATION_EXECUTION_MANIFEST.json', DC_JOB, 'Required authentic COMPUTE-NODE Abaqus mechanical/phase datachecks and actual R6 runtime startup; zero numerical continuation.', 1)]:
        text(package / filename, json.dumps(manifest(files, runtime, job_name, 'submit_' + job_name + '.pbs', purpose, hours), indent=2) + '\n')

    print(json.dumps(dict(package=REL, history_values=28224,
                          baseline=START, targets=TARGETS, max_outer=130), indent=2))


if __name__ == '__main__':
    build()
