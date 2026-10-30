"""Read-only Package 49 qualification; never issues permits or invokes qsub."""
import hashlib
import json
import os
import re
from pathlib import Path
import shutil
import subprocess
import tempfile
from datetime import datetime, timezone

RUN = Path('/scratch9/pr21vyci/runs/mode1_stage_c1_1_nonmatching_transfer')


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def run_shell(body, expected_status=0):
    with tempfile.TemporaryDirectory(prefix='p49-preflight-') as directory:
        script = Path(directory) / 'check.sh'
        script.write_text('set -euo pipefail\n' + body)
        result = subprocess.run(['bash', str(script)], stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, universal_newlines=True, timeout=75)
        require(result.returncode == expected_status, 'Notification transport/lifecycle check failed')
        return result.stdout.strip()


def check(payload):
    global RUN
    if payload.get('batch', {}).get('adapter') in ('mode1-qualified-batch-v2', 'mode1-experimental-offset-v1', 'mode1-continuum-preanalysis-v1', 'mode1-pdas-iterative-v1', 'mode1-experimental-irrev-v1', 'mode1-experimental-12dof-v1'):
        target=payload['batch'].get('remote_run_dir','')
        require(re.fullmatch(r'/scratch9/pr21vyci/runs/mode1_[a-z0-9_/]+',target) and '..' not in target, 'Unsafe Mode-I scratch path')
        RUN=Path(target)
    # Live scheduler capacity is a technical resource check, not an approval.
    active=subprocess.run(['qstat','-f','-u','pr21vyci'],stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True,timeout=20)
    require(active.returncode==0,'Cannot verify live scheduler capacity')
    active_count=len(re.findall(r'\bjob_state\s*=\s*[Q R H T W E S B]\b',active.stdout))
    require(active_count < 4,'Four-job project resource limit reached; preserve running jobs')
    facts = {}
    queue = payload.get('submission_queue', 'entry_imfdfkmq')
    require(queue in ('normal_imfdfkmq', 'entry_imfdfkmq'), 'Unapproved queue')
    query = subprocess.run(['qstat', '-Qf', queue], stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE, universal_newlines=True, timeout=20)
    require(query.returncode == 0, 'Queue query failed')
    require('from_route_only = True' not in query.stdout,
            'Direct submission prohibited: use authorized entry_imfdfkmq routing queue')
    for key in ('enabled', 'started'):
        require(re.search(r'\b' + key + r'\s*=\s*True', query.stdout), 'Queue not ' + key)
    if queue == 'entry_imfdfkmq':
        require('queue_type = Route' in query.stdout and
                'normal_imfdfkmq' in query.stdout, 'Routing destination mismatch')
    for name, digest in payload['files'].items():
        require(Path(name).name == name, 'Invalid package filename')
        path = RUN / name
        require(path.is_file(), 'Missing staged file: ' + name)
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        require(actual == digest.lower(), 'Staged hash mismatch: ' + name)
        facts[name] = actual

    batch = payload.get('batch')
    require(batch is not None, 'Batch specification required')
    if batch.get('runtime_source_hashes'):
        require(batch.get('runtime_root') == str(RUN / 'runtime'), 'Runtime must be isolated within exact package')
        for name, expected in batch['runtime_source_hashes'].items():
            require(not Path(name).is_absolute() and '..' not in Path(name).parts, 'Unsafe runtime dependency')
            source = RUN / 'runtime' / name
            require(source.is_file() and hashlib.sha256(source.read_bytes()).hexdigest().upper() == expected.upper(), 'Staged runtime dependency changed: '+name)
    require(batch['batch_name'].startswith('MODE1_') and batch.get('scientific_scope') == 'MODE1', 'Outside Mode-I scope')
    require(1 <= len(batch['jobs']) == batch['max_submissions'] <= 2, 'Invalid batch size')

    for job in batch['jobs']:
        pbs_path = RUN / job['pbs']
        require(pbs_path.is_file(), 'Missing PBS script: ' + job['pbs'])
        text = pbs_path.read_text()
        for directive in ['#PBS -q entry_imfdfkmq', '#PBS -m abe',
                          '#PBS -M pr21vyci@mailserver.tu-freiberg.de',
                          '#PBS -l select=1:ncpus=1:mem='+str(job['memory_gb'])+'gb',
                          '#PBS -l walltime='+str(job['walltime_hours']).zfill(2)+':00:00',
                          '#PBS -r n', 'cd "${RUN_DIR}"', 'notification_load_config', 'command -v ifort',
                          'module load gcc/11.4.0 intel/2024.2.0 abaqus/2023',
                          'notification_install_terminal_trap', 'notify_start']:
            require(directive in text, 'Batch PBS contract missing: ' + job['pbs'])
        require(subprocess.call(['bash', '-n', str(pbs_path)]) == 0,
                'Batch PBS syntax failure: ' + job['pbs'])

    helper = RUN / 'job_notifications.sh'
    require(helper.is_file(), 'Missing staged notification helper')
    cfg = Path.home() / '.config/adaptive-remeshing/notifications.env'
    require(cfg.is_file() and cfg.stat().st_mode & 0o777 == 0o600,
            'Notification configuration must exist with mode 600')
    require(shutil.which('sendmail'), 'sendmail unavailable; email acceptance unverified')

    prefix = 'export NOTIFICATION_CONFIG=' + str(cfg) + '\nsource ' + str(helper) + '\n'
    run_shell('''if ! type module >/dev/null 2>&1; then
    source /etc/profile.d/lmod.sh 2>/dev/null || source /usr/share/Modules/init/bash 2>/dev/null || true
fi
module purge
module load gcc/11.4.0 intel/2024.2.0 abaqus/2023
command -v ifort
''')

    lifecycle = prefix + '''
notification_send_telegram() { printf '%s\\n' "$1" >> "$CAPTURE"; }
notification_send_email() { :; }
export PBS_JOBID=PREFLIGHT_TEST PBS_JOBNAME=P49_PREFLIGHT_TEST
notify_submitted PREFLIGHT_TEST P49_PREFLIGHT_TEST Synthetic
notify_start
notify_completed P49_PREFLIGHT_TEST PREFLIGHT_TEST 0
notify_failed P49_PREFLIGHT_TEST PREFLIGHT_TEST 1 0
notify_terminated P49_PREFLIGHT_TEST PREFLIGHT_TEST TERM 0
NOTIFICATION_TERMINAL_SENT=0
notification_terminal_trap 0
notification_terminal_trap 0
'''
    with tempfile.TemporaryDirectory(prefix='p49-events-') as directory:
        capture = Path(directory) / 'events'
        run_shell('export CAPTURE=' + str(capture) + '\n' + lifecycle)
        text = capture.read_text()
        for event, count in [('SUBMITTED', 1), ('STARTED', 1), ('COMPLETED', 2),
                             ('FAILED', 1), ('TERMINATED', 1)]:
            require(text.count(' - ' + event + ']') == count,
                    'Lifecycle/exactly-once contract failed: ' + event)
        for ending, rc, event in [('exit 0', 0, 'COMPLETED'),
                                 ('exit 1', 1, 'FAILED'),
                                 ('kill -TERM $$', 143, 'TERMINATED')]:
            capture.write_text('')
            run_shell('export CAPTURE=' + str(capture) + '\n' + prefix + '''
notification_send_telegram() { printf '%s\\n' "$1" >> "$CAPTURE"; }
notification_send_email() { :; }
export PBS_JOBID=PREFLIGHT_TEST PBS_JOBNAME=P49_PREFLIGHT_TEST
notification_install_terminal_trap
''' + ending + '\n', expected_status=rc)
            require(capture.read_text().count(' - ' + event + ']') == 1,
                    'Installed terminal trap failed: ' + event)

    # Real transport tests: helper requires Telegram HTTP 200 and JSON ok=true.
    run_shell(prefix + '''
unset NOTIFICATION_MOCK_TELEGRAM NOTIFICATION_MOCK_FAIL
notification_load_config
notification_send_telegram_once 'Package 49 authorization PREFLIGHT TEST; no PBS job submitted.'
notification_send_email_once 'Package 49 authorization PREFLIGHT TEST' 'No PBS job submitted. Mail transport verification.'
''')

    # Bind actual checked datacheck artifacts to the unchanged candidate inputs.
    datachecks={}
    for job in batch['jobs']:
        require(Path(job['datacheck']).name == job['datacheck'], 'Unsafe datacheck filename')
        dat_file=RUN/job['datacheck']
        require(dat_file.is_file(), 'Datacheck output missing: '+job['datacheck'])
        data=dat_file.read_bytes()
        text=data.decode(errors='replace')
        require('ANALYSIS DATACHECK COMPLETE' in text and '***ERROR' not in text, 'Datacheck failed')
        require(job['input'] in facts,'Unbound datacheck input')
        datachecks[job['id']]={'status':'PASS','input_sha256':facts[job['input']], 'dat_sha256':hashlib.sha256(data).hexdigest()}
        for extra in job.get('additional_datachecks', []):
            require(Path(extra).name == extra, 'Unsafe additional datacheck')
            require(extra.endswith('.dat'), 'Additional datacheck must be a DAT file')
            inp = extra[:-4] + '.inp'
            require(inp in facts, 'Unbound additional datacheck input')
            extra_path = RUN / extra
            require(extra_path.is_file(), 'Additional datacheck missing: '+extra)
            extra_data = extra_path.read_bytes()
            extra_text = extra_data.decode(errors='replace')
            require('ANALYSIS DATACHECK COMPLETE' in extra_text and '***ERROR' not in extra_text, 'Additional datacheck failed')
            datachecks[job['id']].setdefault('additional', {})[extra] = {'status':'PASS', 'input_sha256':facts[inp], 'dat_sha256':hashlib.sha256(extra_data).hexdigest()}

    adapter_name = payload.get('batch', {}).get('adapter', 'mode1-qualified-batch-v2')
    return dict(active_job_count=active_count, adapter_contract=adapter_name, datachecks=datachecks,
                batch_spec_sha256=hashlib.sha256(json.dumps(batch,sort_keys=True,separators=(",",":")).encode()).hexdigest(), passed=True, pbs_email_verified=True, telegram_verified=True,
                submission_queue=queue, queue_access_preflight='PASS',
                compiler_environment='PASS_LOGIN_NODE',
                datacheck_verified='PASS_BOTH',
                candidate_manifest_sha256=payload['manifest_sha256'],
                authorized_command_sha256=payload['command_sha256'],
                checked_at=datetime.now(timezone.utc).isoformat(),
                config_path=str(cfg), config_mode='600', file_hashes=facts,
                helper_sha256=hashlib.sha256(helper.read_bytes()).hexdigest(),
                email_evidence='sendmail accepted test message; PBS abe directives verified',
                telegram_notification_contract='PASS_LOGIN_NODE',
                compute_node_delivery='UNRESOLVED', lifecycle_tests='PASS')


if __name__ == '__main__':
    import base64
    import gzip
    import sys
    try:
        data = base64.b64decode(sys.argv[1], validate=True)
        payload = json.loads(gzip.decompress(data) if data.startswith(b'\x1f\x8b') else data)
        print(json.dumps(check(payload)))
    except Exception as error:
        print(json.dumps({'passed': False, 'reason': str(error)}))
        sys.exit(1)
