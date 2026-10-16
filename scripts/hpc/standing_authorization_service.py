"""Trusted standing-grant issuer. Human enrollment is separate from permit renewal.

Executed by the existing OpenClawGateway identity; never submits jobs. State is
locked and replaced atomically. The human pins this issuer's bytes at enrollment.
Only the conservative Package48 recovery adapter is currently implemented.
"""
import hashlib
import json
import os
import re
import sys
import uuid
from datetime import datetime, timedelta, timezone

PROJECT = 'PRV_ADAPTIVE_REMESHING'
ADAPTER = 'package48-native-restart-technical-recovery-v1'
STATE = '/home/openclaw/.openclaw/workspace-antigravity-controller/controller-state.json'


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def issue(state, request, issuer_hash, now=None):
    now = now or datetime.now(timezone.utc)
    if request['mode'] == 'enroll':
        require(not state.get('standing_project_authorization'),
                'Standing grant already exists; cannot reset or re-enroll')
        state['standing_project_authorization'] = dict(
            active=True, project=PROJECT, grant_id=str(uuid.uuid4()),
            enrolled_by='human_operator_Set-ControllerAuthorization',
            enrolled_at=now.isoformat(), expires_at=None, issuer_sha256=issuer_hash,
            scope='Mode-I approved research; execution restricted to qualified adapters',
            adapters=[ADAPTER], max_concurrent_jobs=4, max_replacements_per_chain=1)
        return 'STANDING_GRANT_ENROLLED'
    grant = state.get('standing_project_authorization', {})
    require(grant.get('active') is True and grant.get('project') == PROJECT,
            'One-time human standing-grant enrollment required (or grant revoked)')
    require(grant.get('issuer_sha256') == issuer_hash, 'Enrolled trusted issuer changed')
    require(ADAPTER in grant.get('adapters', []), 'Execution adapter not enrolled')
    batch = request['batch_spec']
    require(batch.get('adapter') == ADAPTER, 'Unsupported execution adapter')
    require(batch.get('max_submissions') == 2 and len(batch.get('jobs', [])) == 2,
            'Recovery batch must contain exactly two recipients')
    require(batch.get('automatic_retry') is False, 'No automatic solver retry loops')
    evidence = request['evidence']
    require(all(evidence.get(k) is True for k in ('passed', 'pbs_email_verified', 'telegram_verified')),
            'Actual notification preflight required')
    age = (now - datetime.fromisoformat(evidence['checked_at'])).total_seconds()
    require(0 <= age < 300, 'Fresh actual preflight required')
    require(evidence['candidate_manifest_sha256'] == request['manifest'], 'Manifest binding mismatch')
    require(evidence['file_hashes'] == batch['files'], 'File binding mismatch')
    require(evidence.get('restart_datacheck') == 'PASS_BOTH', 'Checkpoint-compatible datachecks required')
    require(evidence.get('checkpoint_hashes') == batch['checkpoint_hashes'], 'Checkpoint changed')
    require(batch.get('donor_pbs_job_id') == '1413814.mmaster02', 'Wrong donor')
    require(batch.get('scientific_review') == 'PASS', 'Authentic donor scientific review missing')
    require(batch.get('failure_class') == 'preprocessing' and
            batch.get('correction') == 'remove_unsupported_restart_error_indicator_output',
            'Only qualified output-only technical recovery supported')
    require(batch['files'].get('f42_mixed_uel.for') == 'ce8d5edcd2911dcb018bb15275271f874e7ea62b8fb48cf4a8297469a83acdd6', 'Frozen UEL changed')
    require(batch['files'].get('f42_mixed_uel_restart_diagnostic.for') == '8c6d873037367665c01c305d50c5b148339dc38c6e581bf4a9e19c2b5e2ac978', 'Diagnostic UEL changed')
    parents = {'restart_prod': '1413817.mmaster02', 'restart_diag': '1413818.mmaster02'}
    for job in batch['jobs']:
        require(job['id'] in parents and job.get('replaces_job') == parents[job['id']], 'Unapproved replacement chain')
        require(job['max_submissions'] == 1 and job['cpus'] == 1 and job['memory_gb'] == 16 and
                job['walltime_hours'] == 8 and job['queue'] == 'entry_imfdfkmq', 'Resource or submission limit exceeded')
        pbs = 'submit_M1_MB_RESTART_' + ('PROD' if job['id'] == 'restart_prod' else 'DIAG') + '.pbs'
        command = ('powershell -NoProfile -ExecutionPolicy Bypass -File .\\.agents\\scripts\\Invoke-GuardedSsh.ps1 '
                   '-RemoteCommand "qsub -q entry_imfdfkmq /scratch9/pr21vyci/runs/mode1_package48_restart_control/' + pbs + '"')
        require(job['pbs'] == pbs and job['command'] == command, 'Command outside guarded adapter')
        require(job['command_sha256'] == sha(' '.join(command.split()).encode()), 'Command digest mismatch')
    require(len({j['id'] for j in batch['jobs']}) == 2, 'Duplicate recipient')
    history = state.get('submission_authorization_history', [])
    old = state.get('submission_authorization', {})
    renewal = bool(old.get('standing_grant_id') == grant['grant_id'] and
                   old.get('candidate_manifest_sha256') == request['manifest'] and
                   old.get('consumed', 0) < old.get('max_submissions', 1) and
                   datetime.fromisoformat(old['expires_at']) <= now)
    if old:
        require(renewal or not old.get('active') or old.get('consumed', 0) >= old.get('max_submissions', 1),
                'Existing live permit preserved; use it instead of renewal')
    for previous in history + ([old] if old else []):
        if renewal and previous.get('standing_grant_id') == grant['grant_id'] and previous.get('candidate_manifest_sha256') == request['manifest']:
            continue  # Carry counters forward; never reset an expired partial permit.
        require(previous.get('candidate_manifest_sha256') != request['manifest'], 'This candidate already issued; counters preserved')
        require(not set(previous.get('replacement_parents', [])) & set(parents.values()), 'Replacement budget already reserved')
    if old:
        history.append(old)
    state['submission_authorization_history'] = history
    expiry = (now + timedelta(hours=24)).isoformat()
    state['daily_chatgpt_delegation'] = dict(active=True, expires_at=expiry,
        max_concurrent_jobs=grant['max_concurrent_jobs'])
    state['submission_authorization'] = dict(active=True, consumed=0, max_submissions=2,
        permit_id=str(uuid.uuid4()), batch_name=batch['batch_name'], authorized_at=now.isoformat(),
        authorized_by='trusted_standing_grant_issuer', standing_grant_id=grant['grant_id'],
        expires_at=expiry, candidate_manifest_sha256=request['manifest'], notification_preflight=evidence,
        authorized_commands=[j['command'] for j in batch['jobs']],
        authorized_command_hashes=[j['command_sha256'] for j in batch['jobs']],
        command_consumption={}, replacement_parents=list(parents.values()),
        batch_manifest_path=request['manifest_path'], batch_package_path=request['package_path'])
    if renewal:
        for field in ('consumed', 'command_consumption', 'consumption_audit'):
            if field in old:
                state['submission_authorization'][field] = old[field]
        state['submission_authorization']['renewed_from_permit_id'] = old['permit_id']
    state.setdefault('standing_authorization_audit', []).append(dict(
        at=now.isoformat(), grant_id=grant['grant_id'], manifest=request['manifest'],
        permit_id=state['submission_authorization']['permit_id'], event='ISSUED'))
    return 'STANDING_PERMIT_ISSUED'


def main():
    import base64
    import fcntl
    request = json.loads(base64.b64decode(sys.argv[1], validate=True))
    # Caller supplies exact source digest; enrollment pins it, later calls must match.
    issuer_hash = sys.argv[2]
    with open(STATE + '.lock', 'a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        with open(STATE) as stream:
            state = json.load(stream)
        result = issue(state, request, issuer_hash)
        temp = STATE + '.' + str(uuid.uuid4()) + '.tmp'
        fd = os.open(temp, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, 'w') as stream:
            json.dump(state, stream, indent=2)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp, STATE)
        print(result)


if __name__ == '__main__':
    main()
