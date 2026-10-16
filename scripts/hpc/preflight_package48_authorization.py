"""Read-only Package 48 qualification; never issues permits or invokes qsub."""
import hashlib
import json
import os
import re
from pathlib import Path
import shutil
import subprocess
import tempfile
from datetime import datetime, timezone

RUN = Path('/scratch9/pr21vyci/runs/mode1_package48_restart_control')


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def run_shell(body, expected_status=0):
    with tempfile.TemporaryDirectory(prefix='p48-preflight-') as directory:
        script = Path(directory) / 'check.sh'
        script.write_text('set -euo pipefail\n' + body)
        result = subprocess.run(['bash', str(script)], stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, universal_newlines=True, timeout=75)
        # Never echo shell output/errors: configuration may contain credentials.
        require(result.returncode == expected_status, 'Notification transport/lifecycle check failed')
        return result.stdout.strip()


def check(payload):
    facts = {}
    queue = payload.get('submission_queue', 'normal_imfdfkmq')
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
    pbs = (RUN / 'submit_M1_MB_DONOR.pbs').read_text()
    for directive in ['#PBS -m abe', '#PBS -M pr21vyci@mailserver.tu-freiberg.de',
                      '#PBS -l nodes=1:ppn=1', '#PBS -l mem=16gb',
                      '#PBS -l walltime=04:00:00', '#PBS -q entry_imfdfkmq',
                      'module load gcc/11.4.0 intel/2024.2.0 abaqus/2023',
                      'command -v ifort',
                      'notification_install_terminal_trap', 'notify_start']:
        require(directive in pbs, 'Missing PBS contract: ' + directive)
    if payload.get('batch'):
        batch = payload['batch']
        require((batch['max_submissions'] == 3 and len(batch['jobs']) == 3) or
                (batch.get('adapter') == 'package48-native-restart-technical-recovery-v1' and batch['max_submissions'] == 2 and len(batch['jobs']) == 2),
                'Invalid batch budget')
        for job in batch['jobs']:
            text = (RUN / job['pbs']).read_text()
            for directive in ['#PBS -q entry_imfdfkmq', '#PBS -m abe', '#PBS -r n',
                              '#PBS -M pr21vyci@mailserver.tu-freiberg.de',
                              '#PBS -l nodes=1:ppn=1', '#PBS -l mem=16gb',
                              'module load gcc/11.4.0 intel/2024.2.0 abaqus/2023',
                              'command -v ifort', 'notification_install_terminal_trap', 'notify_start']:
                require(directive in text, 'Batch PBS contract missing: ' + job['pbs'])
            require(subprocess.call(['bash', '-n', str(RUN / job['pbs'])]) == 0,
                    'Batch PBS syntax failure')
            if job['id'] != 'donor':
                require('oldjob=M1_MB_DONOR_WITH_RESTART' in text and
                        'test -s M1_MB_DONOR_WITH_RESTART.res' in text,
                        'Missing restart/checkpoint contract')
    helper = RUN / 'job_notifications.sh'
    require(helper.is_file(), 'Missing staged notification helper')
    cfg = Path.home() / '.config/adaptive-remeshing/notifications.env'
    require(cfg.is_file() and cfg.stat().st_mode & 0o777 == 0o600,
            'Notification configuration must exist with mode 600')
    require(shutil.which('sendmail'), 'sendmail unavailable; email acceptance unverified')
    # Lifecycle tests use the real helper with local transport capture, not messages
    # pretending that an actual PBS experiment started or finished.
    prefix = 'export NOTIFICATION_CONFIG=' + str(cfg) + '\nsource ' + str(helper) + '\n'
    run_shell('''if ! type module >/dev/null 2>&1; then
    source /etc/profile.d/lmod.sh
fi
module purge
module load gcc/11.4.0 intel/2024.2.0 abaqus/2023
command -v ifort
ifort --version
''')
    lifecycle = prefix + '''
notification_send_telegram() { printf '%s\\n' "$1" >> "$CAPTURE"; }
notification_send_email() { :; }
export PBS_JOBID=PREFLIGHT_TEST PBS_JOBNAME=P48_PREFLIGHT_TEST
notify_submitted PREFLIGHT_TEST P48_PREFLIGHT_TEST Synthetic
notify_start
notify_completed P48_PREFLIGHT_TEST PREFLIGHT_TEST 0
notify_failed P48_PREFLIGHT_TEST PREFLIGHT_TEST 1 0
notify_terminated P48_PREFLIGHT_TEST PREFLIGHT_TEST TERM 0
NOTIFICATION_TERMINAL_SENT=0
notification_terminal_trap 0
notification_terminal_trap 0
'''
    with tempfile.TemporaryDirectory(prefix='p48-events-') as directory:
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
export PBS_JOBID=PREFLIGHT_TEST PBS_JOBNAME=P48_PREFLIGHT_TEST
notification_install_terminal_trap
''' + ending + '\n', expected_status=rc)
            require(capture.read_text().count(' - ' + event + ']') == 1,
                    'Installed terminal trap failed: ' + event)
    # Real transport tests: helper requires Telegram HTTP 200 and JSON ok=true.
    run_shell(prefix + '''
unset NOTIFICATION_MOCK_TELEGRAM NOTIFICATION_MOCK_FAIL
notification_load_config
notification_send_telegram_once 'Package 48 authorization PREFLIGHT TEST; no PBS job submitted.'
notification_send_email_once 'Package 48 authorization PREFLIGHT TEST' 'No PBS job submitted. Mail transport verification.'
''')
    restart_facts = {}
    if payload.get('batch', {}).get('adapter') == 'package48-native-restart-technical-recovery-v1':
        for name, expected in payload['batch']['checkpoint_hashes'].items():
            checkpoint = Path(name)
            require(checkpoint.parent == RUN and checkpoint.name.startswith('M1_MB_DONOR_WITH_RESTART.'), 'Unsafe checkpoint path')
            require(checkpoint.is_file(), 'Checkpoint missing')
            digest = hashlib.sha256()
            with checkpoint.open('rb') as stream:
                for block in iter(lambda: stream.read(8 * 1024 * 1024), b''):
                    digest.update(block)
            require(digest.hexdigest() == expected, 'Checkpoint digest mismatch')
        # Datacheck actual corrected deck against authentic donor; distinct output names.
        deck = (RUN / 'M1_MB_NATIVE_RESTART.inp').read_text()
        require('MISESERI' not in deck and 'MISESAVG' not in deck, 'Restart error-indicator request remains')
        for lane, source in [('PROD', 'f42_mixed_uel.for'), ('DIAG', 'f42_mixed_uel_restart_diagnostic.for')]:
            result = RUN / ('M1_MB_RECOVERY_DC_' + lane + '.dat')
            require(result.is_file(), 'Actual restart datacheck missing: ' + lane)
            content = result.read_text(errors='replace')
            require('ANALYSIS DATACHECK COMPLETE' in content and '***ERROR' not in content,
                    'Actual restart datacheck not successful: ' + lane)
            meta = json.loads((RUN / ('M1_MB_RECOVERY_DC_' + lane + '.json')).read_text())
            require(meta.get('exit_status') == 0 and meta.get('input_sha256') == facts['M1_MB_NATIVE_RESTART.inp'] and
                    meta.get('source_sha256') == facts[source] and meta.get('dat_sha256') == hashlib.sha256(result.read_bytes()).hexdigest(),
                    'Datacheck evidence hashes mismatch')
        restart_facts = dict(restart_datacheck='PASS_BOTH', checkpoint_hashes=payload['batch']['checkpoint_hashes'])
    return dict(**restart_facts, passed=True, pbs_email_verified=True, telegram_verified=True,
                submission_queue=queue, queue_access_preflight='PASS',
                compiler_environment='PASS_LOGIN_NODE',
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
