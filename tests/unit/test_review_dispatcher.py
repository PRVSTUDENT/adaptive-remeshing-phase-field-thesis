import base64
import json
from pathlib import Path

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat

from scripts.controller.review_dispatcher import (
    Dispatcher, LiveHooks, REVIEWER, approved_review, atomic, canonical, packet,
    read, sha, verify_receipt,
)


class Hooks:
    def __init__(self, root):
        self.root = root
        self.private = Ed25519PrivateKey.generate()
        self.key = root / 'test-public.pem'
        self.key.write_bytes(self.private.public_key().public_bytes(Encoding.PEM, PublicFormat.SubjectPublicKeyInfo))
        self.reviews = self.submissions = self.qualifications = 0
        self.accounting = {'status': 'NOT_SUBMITTED'}
        self.decision = 'APPROVE'
        self.available = True
        self.crash = None

    def reconcile(self, key, definition):
        return self.accounting

    def review(self, request, path, resume):
        self.reviews += 1
        if not self.available:
            raise ValueError('unavailable')
        decision = dict(reviewer=REVIEWER, author='gemini-antigravity',
                        correlation_id=request['correlation_id'], operation_id=request['operation_id'],
                        fingerprint=request['fingerprint'], reviewed_hashes=request['hashes'],
                        decision=self.decision, rationale='Full source and numerical evidence reviewed',
                        assistant_message_id='test-assistant-message', conversation_url='https://chatgpt.com/c/test')
        return dict(decision=decision, signature=base64.b64encode(self.private.sign(canonical(decision))).decode())

    def verify(self, receipt, request):
        return verify_receipt(receipt, request, self.key)

    def qualify(self, definition, state, path):
        self.qualifications += 1
        if self.crash == 'before':
            raise KeyboardInterrupt('simulated process crash before submit intent')
        return True

    def submit(self, definition):
        self.submissions += 1
        if self.crash == 'lost':
            raise KeyboardInterrupt('submitted but receipts lost')
        self.accounting = dict(status='SUBMITTED', pbs_job_id='999999.mmaster02')
        if self.crash == 'after':
            raise KeyboardInterrupt('scheduler accepted before dispatcher saved')


@pytest.fixture
def fixture(tmp_path):
    op = 'execute_test_review'
    directory = tmp_path / 'project_coordination/operation_definitions'
    directory.mkdir(parents=True)
    model = tmp_path / 'models/pandey_kumar_mode1/test'
    model.mkdir(parents=True)
    (model / 'source.py').write_text('immutable source')
    (model / 'manifest.json').write_text(json.dumps(dict(files={'source.py': sha(model / 'source.py')}, jobs=[{'id': 'TEST'}])))
    atomic(directory / (op + '.json'), dict(operation_id=op, manifest='models/pandey_kumar_mode1/test/manifest.json',
           registration_status='REVIEW_REQUIRED', scientific_hypothesis='test', evidence_sources={}))
    hooks = Hooks(tmp_path)
    return tmp_path, op, hooks, Dispatcher(tmp_path, hooks)


def test_approve_qualify_submit_recover_once(fixture):
    root, op, hooks, dispatcher = fixture
    state = dispatcher.run(op)
    assert state['status'] == 'SUBMITTED'
    assert state['transitions'] == ['PREPARED', 'REVIEW_PENDING', 'REVIEWED', 'TECH_QUALIFIED', 'SUBMITTING', 'SUBMITTED']
    approved_review(root, op, hooks.key)
    assert dispatcher.run(op)['status'] == 'SUBMITTED'
    assert (hooks.reviews, hooks.submissions) == (1, 1)
    hooks.accounting['status'] = 'RUNNING'
    assert dispatcher.run(op)['status'] == 'RUNNING'
    hooks.accounting.update(status='TERMINAL', exit_status=0)
    assert dispatcher.run(op)['status'] == 'TERMINAL'  # No EVALUATED on Exit0.


@pytest.mark.parametrize('decision,status', [('REJECT', 'REJECTED'), ('INSUFFICIENT_EVIDENCE', 'BLOCKED')])
def test_negative_decisions(fixture, decision, status):
    _, op, hooks, dispatcher = fixture
    hooks.decision = decision
    assert dispatcher.run(op)['status'] == status
    dispatcher.run(op)
    assert hooks.submissions == 0 and hooks.reviews == 1


def test_unavailable_halts_without_gemini_or_redispatch(fixture):
    _, op, hooks, dispatcher = fixture
    hooks.available = False
    a = dispatcher.run(op)
    b = dispatcher.run(op)
    assert a == b and a['reason'] == 'REVIEW_DISPATCH_UNAVAILABLE'
    assert hooks.reviews == 1 and hooks.submissions == 0


def test_stale_manifest_blocks(fixture):
    root, op, hooks, dispatcher = fixture
    hooks.crash = 'before'
    with pytest.raises(KeyboardInterrupt):
        dispatcher.run(op)
    (root / 'models/pandey_kumar_mode1/test/source.py').write_text('altered')
    assert dispatcher.run(op)['status'] == 'BLOCKED'
    assert hooks.submissions == 0


def test_crash_before_submission_resumes_review(fixture):
    _, op, hooks, dispatcher = fixture
    hooks.crash = 'before'
    with pytest.raises(KeyboardInterrupt):
        dispatcher.run(op)
    hooks.crash = None
    assert dispatcher.run(op)['status'] == 'SUBMITTED'
    assert hooks.reviews == 1 and hooks.submissions == 1


@pytest.mark.parametrize('kind,expected', [('after', 'SUBMITTED'), ('lost', 'BLOCKED')])
def test_crash_after_submission_never_resubmits(fixture, kind, expected):
    _, op, hooks, dispatcher = fixture
    hooks.crash = kind
    with pytest.raises(KeyboardInterrupt):
        dispatcher.run(op)
    hooks.crash = None
    assert dispatcher.run(op)['status'] == expected
    dispatcher.run(op)
    assert hooks.submissions == 1


def test_preserve_running_r5_before_any_review(fixture):
    _, op, hooks, dispatcher = fixture
    hooks.accounting = dict(status='RUNNING', pbs_job_id='1419269.mmaster02')
    assert dispatcher.run(op)['accounting']['pbs_job_id'] == '1419269.mmaster02'
    assert hooks.reviews == hooks.submissions == 0


@pytest.mark.parametrize('change', ['signature', 'reviewer', 'author', 'correlation_id', 'reviewed_hashes'])
def test_forged_provenance_rejected(fixture, change):
    root, op, hooks, _ = fixture
    request = packet(root, op)
    request['correlation_id'] = 'test-correlation'
    receipt = hooks.review(request, None, False)
    if change == 'signature':
        receipt['signature'] = base64.b64encode(b'0' * 64).decode()
    else:
        receipt['decision'][change] = 'forged'
    with pytest.raises(Exception):
        hooks.verify(receipt, request)


def test_dryrun_no_bridge_no_submission(fixture):
    _, op, hooks, dispatcher = fixture
    assert dispatcher.run(op, True)['status'] == 'DRY_RUN_NO_DISPATCH'
    assert hooks.reviews == hooks.submissions == 0


def test_live_reserved_without_receipt_fails_closed(fixture):
    root, op, _, _ = fixture
    atomic(root / 'project_coordination/MODE1_EXECUTION_LEDGER.json', dict(batches={'key': dict(attempts={'TEST': 1})}))
    definition = read(root / ('project_coordination/operation_definitions/' + op + '.json'))
    result = LiveHooks(root, None).reconcile('key', definition)
    assert result['status'] == 'BLOCKED' and 'RESERVED' in result['reason']


def test_unsigned_legacy_receipt_rejected(fixture):
    root, op, hooks, _ = fixture
    request = packet(root, op)
    request['correlation_id'] = 'test'
    with pytest.raises(Exception):
        hooks.verify({'response': 'APPROVE'}, request)


def test_valid_changed_evidence_requires_fresh_review(fixture):
    root, op, hooks, dispatcher = fixture
    hooks.decision = 'REJECT'
    assert dispatcher.run(op)['status'] == 'REJECTED'
    definition_path = root / ('project_coordination/operation_definitions/' + op + '.json')
    definition = read(definition_path)
    definition['scientific_hypothesis'] = 'Distinct reviewed correction'
    atomic(definition_path, definition)
    hooks.decision = 'APPROVE'
    assert dispatcher.run(op)['status'] == 'SUBMITTED'
    assert hooks.reviews == 2 and hooks.submissions == 1


def test_evidence_changed_during_qualification_blocks_submit(fixture):
    root, op, hooks, dispatcher = fixture
    def qualify(*args):
        path = root / ('project_coordination/operation_definitions/' + op + '.json')
        definition = read(path)
        definition['scientific_hypothesis'] = 'Unreviewed change'
        atomic(path, definition)
        return True
    hooks.qualify = qualify
    assert dispatcher.run(op)['reason'] == 'STALE_EVIDENCE_AFTER_QUALIFICATION'
    assert hooks.submissions == 0


def test_archived_signed_response_resumes_same_correlation(fixture):
    root, op, hooks, dispatcher = fixture
    hooks.available = False
    state = dispatcher.run(op)
    request_path = next((root / 'project_coordination/review_dispatch').glob('*.request.json'))
    request = read(request_path)
    hooks.available = True
    receipt = hooks.review(request, request_path, True)
    atomic(request_path.with_suffix('.response.json'), receipt)
    hooks.review = lambda *args: read(request_path.with_suffix('.response.json'))
    recovered = dispatcher.run(op)
    assert recovered['status'] == 'SUBMITTED'
    assert recovered['correlation_id'] == state['correlation_id']
