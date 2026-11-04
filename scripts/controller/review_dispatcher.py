"""Durable independent review routing. No model code or free-form commands run here.

Live decisions require an Ed25519 receipt from a separately controlled bridge
worker. The scientific author must not control that worker's signing key.
Unsigned legacy clipboard/localhost responses never authorize execution.
"""
import argparse
import base64
import contextlib
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import uuid

REVIEWER = 'ChatGPT-independent-review'
FROZEN = 'CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6'


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest().upper()


def read(path, default=None):
    return json.loads(Path(path).read_text(encoding='utf-8-sig')) if Path(path).is_file() else default


def atomic(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + '.' + uuid.uuid4().hex + '.tmp')
    with tmp.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, indent=2)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(tmp, path)


def inside(root, rel):
    path = (root / rel).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError('PATH_ESCAPE')
    return path


@contextlib.contextmanager
def exclusive(path):
    # OS lock automatically releases on crash; never delete another process lock.
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('a+b') as stream:
        stream.seek(0)
        stream.write(b'0')
        stream.flush()
        stream.seek(0)
        if os.name == 'nt':
            import msvcrt
            msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        try:
            yield
        finally:
            stream.seek(0)
            if os.name == 'nt':
                msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(stream, fcntl.LOCK_UN)


def packet(root, operation):
    if not re.fullmatch(r'[a-z][a-z0-9_]{5,140}', operation):
        raise ValueError('INVALID_OPERATION')
    reg_rel = 'project_coordination/operation_definitions/' + operation + '.json'
    cand_rel = 'project_coordination/candidate_definitions/' + operation + '.json'
    if (root / reg_rel).is_file():
        rel = reg_rel
    elif (root / cand_rel).is_file():
        rel = cand_rel
    else:
        raise ValueError('DEFINITION_MISSING')
    definition = read(root / rel)
    if not definition or definition.get('operation_id') != operation:
        raise ValueError('DEFINITION_MISSING')
    manifest_rel = definition.get('manifest')
    manifest = read(inside(root, manifest_rel)) if manifest_rel else {}
    sources = dict(definition.get('evidence_sources', {}))
    sources[rel] = sha(root / rel)
    if manifest_rel and manifest:
        sources[manifest_rel] = sha(root / manifest_rel)
        sources.update(manifest.get('runtime_source_hashes', {}))
        for name, digest in manifest.get('files', {}).items():
            if Path(name).name != name:
                raise ValueError('UNSAFE_FILE')
            sources[str(Path(manifest_rel).parent / name).replace('\\', '/')] = digest
    for name, digest in sources.items():
        if sha(inside(root, name)) != digest.upper():
            raise ValueError('STALE_EVIDENCE: ' + name)
    # Complete, exact text evidence, not a summary-only request. Binary outputs
    # are intentionally excluded; a candidate must supply extracted evidence.
    texts = {}
    for name in sources:
        path = inside(root, name)
        if path.stat().st_size > 5_000_000:
            raise ValueError('EVIDENCE_TOO_LARGE: provide bounded extracted evidence')
        texts[name] = path.read_text(encoding='utf-8-sig')
    body = dict(schema=1, operation_id=operation, definition=definition,
                manifest=manifest, hashes={k: v.upper() for k, v in sources.items()},
                evidence=texts, required_decisions=['APPROVE', 'REJECT', 'INSUFFICIENT_EVIDENCE'])
    body['source_differences'] = definition.get('source_differences',
        'No explicit parent diff supplied: require INSUFFICIENT_EVIDENCE if exact sources alone cannot establish the change')
    body['fingerprint'] = hashlib.sha256(canonical(body)).hexdigest().upper()
    return body


def verify_receipt(receipt, request, key_path):
    from cryptography.hazmat.primitives.serialization import load_pem_public_key
    decision = receipt['decision']
    expected_author = request['definition'].get('author')
    valid_authors = [expected_author] if expected_author else ['', 'gemini-antigravity']
    if (decision.get('reviewer') != REVIEWER or
            decision.get('author') not in valid_authors or
            decision.get('author') == decision.get('reviewer') or
            decision.get('correlation_id') != request['correlation_id'] or
            decision.get('operation_id') != request['operation_id'] or
            decision.get('fingerprint') != request['fingerprint'] or
            decision.get('reviewed_hashes') != request['hashes'] or
            decision.get('decision') not in request['required_decisions'] or
            not decision.get('rationale') or not decision.get('assistant_message_id') or
            not re.fullmatch(r'https://chatgpt\.com/c/[A-Za-z0-9-]+', decision.get('conversation_url', ''))):
        raise ValueError('INVALID_INDEPENDENT_REVIEW')
    key = load_pem_public_key(Path(key_path).read_bytes())
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
    if not isinstance(key, Ed25519PublicKey):
        raise ValueError('ED25519_BRIDGE_KEY_REQUIRED')
    key.verify(base64.b64decode(receipt['signature'], validate=True), canonical(decision))
    return decision


def approved_review(root, operation, key=None):
    """Recompute immutable packet and verify archived provenance on every use."""
    if not key:
        key = Path(root) / 'configs/controller/review_bridge_public.pem'
    request = packet(root, operation)
    manifest_rel = request['definition'].get('manifest')
    manifest_path = inside(root, manifest_rel) if manifest_rel else None
    manifest_key = sha(manifest_path).lower() if manifest_path and manifest_path.is_file() else 'no-manifest'
    path = root / 'project_coordination/review_dispatch' / (operation + '-' + manifest_key + '.json')
    state = read(path, {})
    request['correlation_id'] = state.get('correlation_id')
    if state.get('fingerprint') != request['fingerprint'] or not state.get('review'):
        response_path = root / 'project_coordination/review_dispatch' / (operation + '-' + request['fingerprint'] + '.response.json')
        if response_path.is_file():
            receipt = read(response_path)
            state['review'] = receipt
            state['fingerprint'] = request['fingerprint']
            state['correlation_id'] = receipt.get('decision', {}).get('correlation_id')
            request['correlation_id'] = state['correlation_id']
            state['status'] = 'REVIEWED'
            atomic(path, state)
        else:
            raise ValueError('INDEPENDENT_REVIEW_MISSING_OR_STALE')
    decision = verify_receipt(state['review'], request, key)
    if decision['decision'] != 'APPROVE':
        raise ValueError('INDEPENDENT_REVIEW_NOT_APPROVED')
    return state


class Dispatcher:
    def __init__(self, root, hooks):
        self.root = Path(root).resolve()
        self.hooks = hooks
        self.directory = self.root / 'project_coordination/review_dispatch'

    def save(self, path, state, status, **extra):
        state.update(status=status, **extra)
        state.setdefault('transitions', []).append(status)
        atomic(path, state)

    def run(self, operation, dry_run=False):
        if not re.fullmatch(r'[a-z][a-z0-9_]{5,140}', operation):
            raise ValueError('INVALID_OPERATION')
        try:
            with exclusive(self.directory / 'dispatcher.lock'):
                state = self._run(operation, dry_run)
                if not dry_run:
                    self._sync_controller_event(operation, state)
                return state
        except (OSError, PermissionError) as lock_err:
            return dict(status='BLOCKED', reason='DISPATCHER_LOCKED_BY_ANOTHER_PROCESS', detail=str(lock_err))

    def _sync_controller_event(self, operation, state):
        event_path = self.root / 'project_coordination/controller' / f'definition-review-{operation}.json'
        if event_path.is_file():
            try:
                event = read(event_path, {})
                status = state.get('status')
                if status in ('REVIEWED', 'TECH_QUALIFIED', 'SUBMITTING', 'SUBMITTED', 'RUNNING', 'TERMINAL', 'EVALUATED'):
                    event['status'] = status
                    event['updated_at'] = state.get('updated_at', event.get('created_at'))
                    atomic(event_path, event)
                elif status in ('BLOCKED', 'REJECTED'):
                    event['status'] = status
                    event['reason'] = state.get('reason')
                    atomic(event_path, event)
            except Exception:
                pass

    def _run(self, operation, dry_run):
        # Always reconcile canonical accounting before review or dispatch. A
        # lost local review record must never erase a submission reservation.
        reg_rel = 'project_coordination/operation_definitions/' + operation + '.json'
        cand_rel = 'project_coordination/candidate_definitions/' + operation + '.json'
        is_candidate = False
        if (self.root / reg_rel).is_file():
            definition = read(self.root / reg_rel)
        elif (self.root / cand_rel).is_file():
            definition = read(self.root / cand_rel)
            is_candidate = True
        else:
            raise ValueError('DEFINITION_MISSING')
        if not definition:
            raise ValueError('DEFINITION_MISSING')
        manifest_rel = definition.get('manifest')
        manifest_path = inside(self.root, manifest_rel) if manifest_rel else None
        manifest_key = sha(manifest_path).lower() if manifest_path and manifest_path.is_file() else 'no-manifest'
        path = self.directory / (operation + '-' + manifest_key + '.json')
        state = read(path, dict(operation_id=operation, status='PREPARED', transitions=['PREPARED']))
        accounting = self.hooks.reconcile(manifest_key, definition) if manifest_path else dict(status='NOT_SUBMITTED')
        is_read_only = (is_candidate or
                        definition.get('operation_mode') == 'READ_ONLY_SCIENTIFIC_EVALUATION' or
                        definition.get('registration_status') == 'PROPOSED_FOR_INDEPENDENT_REVIEW')
        if not is_read_only and accounting['status'] != 'NOT_SUBMITTED':
            status = accounting['status']
            if dry_run:
                return dict(status='DRY_RUN_NO_DISPATCH', operation_id=operation, accounting=accounting)
            self.save(path, state, status, accounting=accounting)
            # Exit 0 is terminal evidence, never scientific acceptance.
            return state
        if state['status'] in ('SUBMITTING', 'SUBMITTED', 'RUNNING', 'TERMINAL', 'EVALUATED'):
            self.save(path, state, 'BLOCKED', reason='LOST_ACCOUNTING_OR_AMBIGUOUS_SUBMISSION')
            return state
        if state.get('reason') == 'LOST_ACCOUNTING_OR_AMBIGUOUS_SUBMISSION':
            return state
        try:
            request = packet(self.root, operation)
        except (ValueError, OSError, UnicodeError) as error:
            self.save(path, state, 'BLOCKED', reason=str(error))
            return state
        if state.get('fingerprint') and state['fingerprint'] != request['fingerprint']:
            if dry_run:
                return dict(status='DRY_RUN_NEW_EVIDENCE_REVIEW_REQUIRED', fingerprint=request['fingerprint'])
            atomic(path.with_name(path.stem + '-' + state['fingerprint'] + '.history.json'), state)
            state = dict(operation_id=operation, status='PREPARED', transitions=['PREPARED'], fingerprint=request['fingerprint'])
        elif not state.get('fingerprint'):
            state['fingerprint'] = request['fingerprint']
        if state['status'] in ('REJECTED', 'SCIENTIFIC_FAILED'):
            return state
        if state.get('reason') in ('TECHNICAL_QUALIFICATION_REQUIRED', 'TECHNICAL_GATE_FAILED'):
            return state  # Unchanged failed qualification is not a polling job.
        if dry_run:
            return dict(status='DRY_RUN_NO_DISPATCH', operation_id=operation,
                        fingerprint=request['fingerprint'], accounting=accounting)
        request_path = self.directory / (operation + '-' + request['fingerprint'] + '.request.json')
        if (state.get('reason') == 'REVIEW_DISPATCH_UNAVAILABLE' and
                not request_path.with_suffix('.response.json').is_file()):
            return state  # One durable alert, no repeated bridge or Gemini turn.
        if not state.get('correlation_id'):
            response_file = request_path.with_suffix('.response.json')
            if response_file.is_file():
                try:
                    resp_data = read(response_file)
                    state['correlation_id'] = resp_data.get('decision', {}).get('correlation_id')
                except Exception:
                    pass
            if not state.get('correlation_id'):
                state.update(correlation_id='HND-' + uuid.uuid4().hex)
            state['fingerprint'] = request['fingerprint']
        request['correlation_id'] = state['correlation_id']
        if not request_path.exists():
            atomic(request_path, request)
        if not state.get('review'):
            # Persist before transport; restart polls/resumes SAME correlation,
            # never creates another browser request after an uncertain send.
            resume = state.get('dispatch_started', False)
            self.save(path, state, 'REVIEW_PENDING', dispatch_started=True)
            try:
                receipt = self.hooks.review(request, request_path, resume)
                decision = self.hooks.verify(receipt, request)
            except Exception as error:
                self.save(path, state, 'BLOCKED', reason='REVIEW_DISPATCH_UNAVAILABLE',
                          detail=str(error), alert='Configure authenticated bridge receipt producer; resume same correlation. Gemini re-entry prohibited.')
                return state
            archive = request_path.with_suffix('.response.json')
            atomic(archive, receipt)
            if decision['decision'] != 'APPROVE':
                self.save(path, state, 'REJECTED' if decision['decision'] == 'REJECT' else 'BLOCKED',
                          reason=decision['decision'], review=receipt)
                return state
            self.save(path, state, 'REVIEWED', review=receipt)
        else:
            try:
                decision = self.hooks.verify(state['review'], request)
            except Exception as error:
                self.save(path, state, 'BLOCKED', reason='INVALID_ARCHIVED_REVIEW', detail=str(error))
                return state
            if decision['decision'] != 'APPROVE':
                return state
        # Recheck bytes after browser wait, before any executable gate.
        if packet(self.root, operation)['fingerprint'] != request['fingerprint']:
            self.save(path, state, 'BLOCKED', reason='STALE_EVIDENCE_AFTER_REVIEW')
            return state
        if is_candidate or is_read_only:
            # Staged candidates remain inactive and ineligible for scientific execution.
            return state
        try:
            if not self.hooks.qualify(definition, state, request_path):
                self.save(path, state, 'BLOCKED', reason='TECHNICAL_QUALIFICATION_REQUIRED')
                return state
            self.save(path, state, 'TECH_QUALIFIED')
            if packet(self.root, operation)['fingerprint'] != request['fingerprint']:
                self.save(path, state, 'BLOCKED', reason='STALE_EVIDENCE_AFTER_QUALIFICATION')
                return state
            accounting = self.hooks.reconcile(manifest_key, definition)
            if accounting['status'] != 'NOT_SUBMITTED':
                self.save(path, state, accounting['status'], accounting=accounting)
                return state
            # Cryptographically verify the approved review and hash integrity immediately before submitting
            approved_review(self.root, operation, getattr(self.hooks, 'key', None))
            self.save(path, state, 'SUBMITTING')
            self.hooks.submit(definition)
            accounting = self.hooks.reconcile(manifest_key, definition)
            if accounting['status'] == 'NOT_SUBMITTED':
                raise ValueError('MISSING_RECEIPT_AFTER_EXECUTION')
            self.save(path, state, accounting['status'], accounting=accounting)
        except Exception as error:
            self.save(path, state, 'BLOCKED', reason='LOST_ACCOUNTING_OR_AMBIGUOUS_SUBMISSION'
                      if state['status'] == 'SUBMITTING' else 'TECHNICAL_GATE_FAILED', detail=str(error))
        return state


class LiveHooks:
    def __init__(self, root, key):
        self.root, self.key = Path(root), key

    def ps(self, args, timeout=180):
        return subprocess.run(['powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass'] + args,
                              cwd=self.root, check=True, stdin=subprocess.DEVNULL,
                              capture_output=True, text=True, timeout=timeout).stdout

    def reconcile(self, key, definition):
        receipts = read(self.root / 'project_coordination/MODE1_BATCH_SUBMISSIONS.json', {}).get(key, {})
        record = read(self.root / 'project_coordination/MODE1_EXECUTION_LEDGER.json', {}).get('batches', {}).get(key, {})
        batch = read(self.root / definition['manifest'])
        jobs = [j['id'] for j in batch['jobs']]
        if len(jobs) != 1:
            return dict(status='BLOCKED', reason='ONE_OPERATION_ONE_JOB_REQUIRED')
        receipt = receipts.get(jobs[0])
        if receipt:
            job = receipt.get('pbs_job_id', '')
            if not re.fullmatch(r'\d+\.mmaster02', job):
                return dict(status='BLOCKED', reason='AMBIGUOUS_RECEIPT')
            try:
                output = self.ps(['-File', '.agents/scripts/Invoke-GuardedSsh.ps1',
                                  '-RemoteCommand', 'qstat -xf ' + job])
                match = re.search(r'job_state\s*=\s*([A-Z])', output)
                status = 'RUNNING' if match and match[1] == 'R' else 'TERMINAL' if match and match[1] in ('F', 'C', 'E') else 'SUBMITTED'
            except Exception:
                status = 'SUBMITTED'  # Receipt survives scheduler history expiry.
            return dict(status=status, pbs_job_id=job, physical_acceptance='UNVERIFIED')
        if any(record.get('attempts', {}).get(j, 0) for j in jobs):
            return dict(status='BLOCKED', reason='RESERVED_WITHOUT_RECEIPT_RECONCILE_REQUIRED')
        # Live exact-name scheduler query catches an orphan even if local state
        # was lost. Any unavailable/ambiguous query fails closed.
        try:
            output = self.ps(['-File', '.agents/scripts/Invoke-GuardedSsh.ps1',
                              '-RemoteCommand', 'qstat -x -u pr21vyci -f'])
        except Exception:
            return dict(status='BLOCKED', reason='SCHEDULER_RECONCILIATION_UNAVAILABLE')
        if any(re.search(r'Job_Name\s*=\s*' + re.escape(j) + r'\s', output) for j in jobs):
            return dict(status='BLOCKED', reason='ORPHAN_SCHEDULER_JOB')
        return dict(status='NOT_SUBMITTED')

    def review(self, request, request_path, resume):
        response = request_path.with_suffix('.response.json')
        if response.is_file():
            return read(response)
        if resume:
            # Check if bridge already produced an archive for this correlation_id
            archive_dir = Path.home() / 'OpenClawPAD' / 'ChatGPTBridge' / 'archive'
            if archive_dir.is_dir():
                matches = list(archive_dir.glob(f"*{request['correlation_id']}*.json"))
                if matches:
                    self.ps(['-File', 'scripts/controller/Invoke-IndependentReviewBridge.ps1',
                             '-RequestPath', str(request_path), '-ResponsePath', str(response)], timeout=360)
                    if response.is_file():
                        return read(response)
            raise ValueError('Uncertain prior bridge dispatch: recover signed archived response for same correlation; no automatic resend')
        if not self.key or not Path(self.key).is_file():
            raise ValueError('Authenticated bridge public key unavailable; unsigned legacy bridge is insufficient')
        self.ps(['-File', 'scripts/controller/Invoke-IndependentReviewBridge.ps1',
                 '-RequestPath', str(request_path), '-ResponsePath', str(response)], timeout=360)
        return read(response)

    def verify(self, receipt, request):
        return verify_receipt(receipt, request, self.key)

    def qualify(self, definition, state, request_path):
        # Scientific approval does not make arbitrary definition scripts runnable.
        # Existing dynamic qualification must bind and validate the executable.
        operation = definition['operation_id']
        out = self.ps(['-File', 'scripts/controller/Test-IndependentReviewQualification.ps1',
                       '-OperationId', operation])
        return out.strip().endswith('TECH_QUALIFIED')

    def submit(self, definition):
        if read(self.root / 'project_coordination/ACTIVE_SESSION.json', {}).get('active'):
            raise ValueError('Repository session claimed during bridge wait; no submission')
        self.ps(['-File', 'scripts/hpc/Invoke-Mode1Execution.ps1', '-ManifestPath',
                 str(self.root / definition['manifest'])], timeout=600)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--workspace', default=str(Path(__file__).resolve().parents[2]))
    parser.add_argument('--operation-id', required=True)
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--bridge-public-key', default=os.environ.get('PRV_REVIEW_BRIDGE_PUBLIC_KEY'))
    parser.add_argument('--check-review', action='store_true')
    parser.add_argument('--check-package', action='store_true')
    args = parser.parse_args()
    root = Path(args.workspace).resolve()
    bridge_key = args.bridge_public_key
    if not bridge_key:
        default_pub = root / 'configs/controller/review_bridge_public.pem'
        if default_pub.is_file():
            bridge_key = str(default_pub)
    if args.check_review:
        approved_review(root, args.operation_id, bridge_key)
        print('AUTHENTICATED_INDEPENDENT_REVIEW')
        return
    if args.check_package:
        sys.path.insert(0, str(root))
        from scripts.hpc.mode1_execution_gate import validate_manifest
        definition = read(root / ('project_coordination/operation_definitions/' + args.operation_id + '.json'))
        batch, _, _ = validate_manifest(root / definition['manifest'], root)
        if (batch['adapter'] != 'mode1-qualified-batch-v2' or len(batch['jobs']) != 1 or
                batch['files'].get('f42_mixed_uel.for', '').upper() != FROZEN or
                any(j['cpus'] != 1 or j['memory_gb'] > 16 or j['walltime_hours'] > 8 for j in batch['jobs'])):
            raise ValueError('UNCHANGED_FROZEN_SERIAL_MODE1_ENVELOPE_REQUIRED')
        print('PACKAGE_INTEGRITY_PASS_LIVE_PREFLIGHT_STILL_REQUIRED')
        return
    session = read(root / 'project_coordination/ACTIVE_SESSION.json', {})
    if session.get('active') and not args.dry_run:
        raise SystemExit('BLOCKED_ACTIVE_REPOSITORY_SESSION')
    print(json.dumps(Dispatcher(root, LiveHooks(root, bridge_key)).run(args.operation_id, args.dry_run), indent=2))


if __name__ == '__main__':
    main()
