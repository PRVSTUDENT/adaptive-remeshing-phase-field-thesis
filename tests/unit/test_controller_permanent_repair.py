"""Unit and integration test suite for permanent controller repair.

Tests:
1. Controller-Registration routing state machine.
2. Attestation worker cryptographic provenance and fail-closed validation.
3. Dispatcher event synchronization and recovery.
"""
import base64
import json
import os
from pathlib import Path
import subprocess
import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding, PrivateFormat, PublicFormat, NoEncryption

from scripts.controller.attest_review import (
    attest, canonical, extract_decision, sign_decision, validate_decision, REVIEWER
)
from scripts.controller.review_dispatcher import (
    Dispatcher, LiveHooks, approved_review, atomic, packet, read, sha, verify_receipt
)


@pytest.fixture
def keys(tmp_path):
    priv = Ed25519PrivateKey.generate()
    priv_file = tmp_path / 'test_private.key'
    pub_file = tmp_path / 'test_public.pem'
    priv_file.write_bytes(priv.private_bytes(Encoding.PEM, PrivateFormat.PKCS8, NoEncryption()))
    pub_file.write_bytes(priv.public_key().public_bytes(Encoding.PEM, PublicFormat.SubjectPublicKeyInfo))
    return priv_file, pub_file


@pytest.fixture
def mock_operation(tmp_path):
    op = 'execute_test_operation_c4'
    op_dir = tmp_path / 'project_coordination/operation_definitions'
    op_dir.mkdir(parents=True)
    model_dir = tmp_path / 'models/pandey_kumar_mode1/test_c4'
    model_dir.mkdir(parents=True)

    source = model_dir / 'source.inp'
    source.write_text('dummy source')
    manifest_file = model_dir / 'manifest.json'
    manifest_data = dict(
        files={'source.inp': sha(source)},
        jobs=[{'id': 'TEST_JOB', 'cpus': 1, 'memory_gb': 16, 'walltime_hours': 8}],
        adapter='mode1-qualified-batch-v2'
    )
    manifest_file.write_text(json.dumps(manifest_data))

    definition = dict(
        schema=1,
        operation_id=op,
        manifest='models/pandey_kumar_mode1/test_c4/manifest.json',
        registration_status='PREPARED_FOR_INDEPENDENT_REGISTRATION_REVIEW',
        author='gemini-antigravity',
        reviewed_by='ChatGPT-independent-review',
        execution_script='scripts/validation/execute_test.py',
        preparation_script='scripts/validation/prepare_test.sh',
        scientific_hypothesis='Valid reference test',
        evidence_sources={}
    )
    atomic(op_dir / (op + '.json'), definition)
    return tmp_path, op, definition, manifest_data


# ==============================================================================
# Part 1: Attestation Worker Unit Tests
# ==============================================================================

def test_extract_decision_from_markdown():
    reply = """
Here is my review:
```json
{
  "reviewer": "ChatGPT-independent-review",
  "author": "gemini-antigravity",
  "correlation_id": "HND-1234",
  "operation_id": "op_test",
  "fingerprint": "FP123",
  "reviewed_hashes": {},
  "decision": "APPROVE",
  "rationale": "Evidence passes",
  "assistant_message_id": "msg-001",
  "conversation_url": "https://chatgpt.com/c/test-uuid"
}
```
Done.
"""
    dec, sig = extract_decision(reply)
    assert dec['decision'] == 'APPROVE'
    assert dec['assistant_message_id'] == 'msg-001'
    assert sig is None


def test_extract_decision_from_envelope():
    reply = json.dumps({
        "decision": {
            "reviewer": "ChatGPT-independent-review",
            "decision": "APPROVE"
        },
        "signature": "mock_sig_base64"
    })
    dec, sig = extract_decision(reply)
    assert dec['decision'] == 'APPROVE'
    assert sig == 'mock_sig_base64'


def test_attest_produces_verifiable_receipt(keys, tmp_path):
    priv_file, pub_file = keys
    req_file = tmp_path / 'req.json'
    resp_file = tmp_path / 'resp.json'

    request = dict(
        operation_id='op_test',
        correlation_id='HND-abc123',
        fingerprint='FP_VALID_123',
        hashes={'source.py': 'AAAABBBB'},
        required_decisions=['APPROVE', 'REJECT', 'INSUFFICIENT_EVIDENCE'],
        definition=dict(author='gemini-antigravity')
    )
    req_file.write_text(json.dumps(request))

    raw_reply = json.dumps({
        "reviewer": "ChatGPT-independent-review",
        "author": "gemini-antigravity",
        "correlation_id": "HND-abc123",
        "operation_id": "op_test",
        "fingerprint": "FP_VALID_123",
        "reviewed_hashes": {'source.py': 'AAAABBBB'},
        "decision": "APPROVE",
        "rationale": "All checks verified",
        "assistant_message_id": "msg-999",
        "conversation_url": "https://chatgpt.com/c/chat-1234"
    })

    receipt = attest(req_file, resp_file, raw_reply, priv_file)
    assert resp_file.is_file()
    assert 'signature' in receipt
    # Verify with dispatcher verify_receipt
    verified = verify_receipt(receipt, request, pub_file)
    assert verified['decision'] == 'APPROVE'


def test_attest_fails_closed_on_forged_hashes(keys, tmp_path):
    priv_file, pub_file = keys
    req_file = tmp_path / 'req.json'
    resp_file = tmp_path / 'resp.json'

    request = dict(
        operation_id='op_test',
        correlation_id='HND-abc123',
        fingerprint='FP_VALID_123',
        hashes={'source.py': 'CORRECT_HASH'},
        required_decisions=['APPROVE', 'REJECT', 'INSUFFICIENT_EVIDENCE'],
        definition=dict(author='gemini-antigravity')
    )
    req_file.write_text(json.dumps(request))

    raw_reply = json.dumps({
        "reviewer": "ChatGPT-independent-review",
        "author": "gemini-antigravity",
        "correlation_id": "HND-abc123",
        "operation_id": "op_test",
        "fingerprint": "FP_VALID_123",
        "reviewed_hashes": {'source.py': 'WRONG_HASH'},
        "decision": "APPROVE",
        "rationale": "All checks verified",
        "assistant_message_id": "msg-999",
        "conversation_url": "https://chatgpt.com/c/chat-1234"
    })

    with pytest.raises(ValueError, match="VALIDATION_FAILED: Reviewed hashes do not match"):
        attest(req_file, resp_file, raw_reply, priv_file)


def test_attest_fails_closed_on_self_approval(keys, tmp_path):
    priv_file, _ = keys
    req_file = tmp_path / 'req.json'
    resp_file = tmp_path / 'resp.json'

    request = dict(
        operation_id='op_test',
        correlation_id='HND-abc123',
        fingerprint='FP_VALID_123',
        hashes={'source.py': 'CORRECT_HASH'},
        required_decisions=['APPROVE'],
        definition=dict(author='gemini-antigravity')
    )
    req_file.write_text(json.dumps(request))

    raw_reply = json.dumps({
        "reviewer": "gemini-antigravity",
        "author": "gemini-antigravity",
        "correlation_id": "HND-abc123",
        "operation_id": "op_test",
        "fingerprint": "FP_VALID_123",
        "reviewed_hashes": {'source.py': 'CORRECT_HASH'},
        "decision": "APPROVE",
        "rationale": "Self-certifying",
        "assistant_message_id": "msg-999",
        "conversation_url": "https://chatgpt.com/c/chat-1234"
    })

    with pytest.raises(ValueError, match="VALIDATION_FAILED: Invalid reviewer.*Author cannot be reviewer"):
        attest(req_file, resp_file, raw_reply, priv_file)


def test_attest_with_authentic_bridge_archive(keys, tmp_path):
    priv_file, pub_file = keys
    req_file = tmp_path / 'req.json'
    resp_file = tmp_path / 'resp.json'
    arch_file = tmp_path / 'bridge_archive.json'

    request = dict(
        operation_id='op_test',
        correlation_id='HND-abc123',
        fingerprint='FP_VALID_123',
        hashes={'source.py': 'AAAABBBB'},
        required_decisions=['APPROVE', 'REJECT', 'INSUFFICIENT_EVIDENCE'],
        definition=dict(author='gemini-antigravity')
    )
    req_file.write_text(json.dumps(request))

    reply_json = json.dumps({
        "reviewer": "ChatGPT-independent-review",
        "author": "gemini-antigravity",
        "correlation_id": "HND-abc123",
        "operation_id": "op_test",
        "fingerprint": "FP_VALID_123",
        "reviewed_hashes": {'source.py': 'AAAABBBB'},
        "decision": "APPROVE",
        "rationale": "Verified from authentic bridge archive",
        "assistant_message_id": "msg-999",
        "conversation_url": "https://chatgpt.com/c/chat-1234"
    })

    archive_data = {
        "bridge_handoff_id": "HND-abc123",
        "status": "OK",
        "copied_at": "2026-11-01T11:00:00.000Z",
        "response_chars": len(reply_json),
        "response": f"```json\n{reply_json}\n```"
    }
    arch_file.write_text(json.dumps(archive_data))

    receipt = attest(req_file, resp_file, None, priv_file, bridge_archive=str(arch_file))
    assert resp_file.is_file()
    assert 'signature' in receipt
    verified = verify_receipt(receipt, request, pub_file)
    assert verified['decision'] == 'APPROVE'


def test_attest_fails_closed_when_key_missing(tmp_path):
    req_file = tmp_path / 'req.json'
    resp_file = tmp_path / 'resp.json'
    missing_key = tmp_path / 'nonexistent.key'

    request = dict(
        operation_id='op_test',
        correlation_id='HND-abc123',
        fingerprint='FP_VALID_123',
        hashes={'source.py': 'CORRECT_HASH'},
        required_decisions=['APPROVE'],
        definition=dict(author='gemini-antigravity')
    )
    req_file.write_text(json.dumps(request))

    raw_reply = json.dumps({
        "reviewer": "ChatGPT-independent-review",
        "author": "gemini-antigravity",
        "correlation_id": "HND-abc123",
        "operation_id": "op_test",
        "fingerprint": "FP_VALID_123",
        "reviewed_hashes": {'source.py': 'CORRECT_HASH'},
        "decision": "APPROVE",
        "rationale": "All checks verified",
        "assistant_message_id": "msg-999",
        "conversation_url": "https://chatgpt.com/c/chat-1234"
    })

    with pytest.raises(ValueError, match="REVIEW_BRIDGE_KEY_NOT_CONFIGURED"):
        attest(req_file, resp_file, raw_reply, missing_key)
    # Ensure unauthenticated payload was saved for recovery/audit
    assert resp_file.with_suffix('.unauthenticated.json').is_file()


# ==============================================================================
# Part 2: Controller-Registration State Machine Tests (PowerShell)
# ==============================================================================

def test_controller_registration_unreviewed_routes_to_dispatch(mock_operation):
    root, op, _, _ = mock_operation
    ps_cmd = f"""
    . '{Path('scripts/controller/Controller-Registration.ps1').resolve()}'
    $task = [pscustomobject]@{{ requested_operation_id = '{op}'; operation_transition = $null }}
    $plan = Get-ControllerRegistrationPlan -Workspace '{root}' -Instruction 'OPERATION_ID: {op}' -Task $task
    $plan | ConvertTo-Json
    """
    res = subprocess.run(
        ['powershell', '-NoProfile', '-Command', ps_cmd],
        capture_output=True, text=True, check=True, stdin=subprocess.DEVNULL
    )
    plan = json.loads(res.stdout)
    assert plan['status'] == 'DEFINITION_REVIEW_REQUIRED'
    assert plan['dispatch_ready'] is False
    assert plan['task_type'] == 'EXTERNAL_REVIEW_DISPATCH'


def test_controller_registration_unverified_review_fails_closed(mock_operation):
    root, op, definition, _ = mock_operation
    manifest_key = sha(root / definition['manifest']).lower()
    dispatch_dir = root / 'project_coordination/review_dispatch'
    dispatch_dir.mkdir(parents=True, exist_ok=True)

    # State with review approval text but NO cryptographic signature
    state = {
        "operation_id": op,
        "status": "REVIEWED",
        "review": {
            "decision": {
                "decision": "APPROVE",
                "rationale": "Unsigned fake approval"
            }
        }
    }
    (dispatch_dir / f"{op}-{manifest_key}.json").write_text(json.dumps(state))

    ps_cmd = f"""
    . '{Path('scripts/controller/Controller-Registration.ps1').resolve()}'
    $task = [pscustomobject]@{{ requested_operation_id = '{op}'; operation_transition = $null }}
    $plan = Get-ControllerRegistrationPlan -Workspace '{root}' -Instruction 'OPERATION_ID: {op}' -Task $task
    $plan | ConvertTo-Json
    """
    res = subprocess.run(
        ['powershell', '-NoProfile', '-Command', ps_cmd],
        capture_output=True, text=True, check=True, stdin=subprocess.DEVNULL
    )
    plan = json.loads(res.stdout)
    # MUST fail closed to DEFINITION_REVIEW_REQUIRED because cryptographic signature check failed
    assert plan['status'] == 'DEFINITION_REVIEW_REQUIRED'
    assert plan['dispatch_ready'] is False


def test_controller_registration_approved_review_advances_to_qualification(mock_operation, keys):
    root, op, definition, manifest = mock_operation
    priv_file, pub_file = keys

    # Copy public key to expected repo location
    pub_dest = root / 'configs/controller/review_bridge_public.pem'
    pub_dest.parent.mkdir(parents=True, exist_ok=True)
    pub_dest.write_bytes(pub_file.read_bytes())

    req = packet(root, op)
    correlation_id = 'HND-test-corr-123'
    decision = {
        "reviewer": "ChatGPT-independent-review",
        "author": "gemini-antigravity",
        "correlation_id": correlation_id,
        "operation_id": op,
        "fingerprint": req['fingerprint'],
        "reviewed_hashes": req['hashes'],
        "decision": "APPROVE",
        "rationale": "Scientifically verified and cryptographically signed",
        "assistant_message_id": "msg-888",
        "conversation_url": "https://chatgpt.com/c/chat-5678"
    }
    signature = sign_decision(decision, priv_file)

    manifest_key = sha(root / definition['manifest']).lower()
    dispatch_dir = root / 'project_coordination/review_dispatch'
    dispatch_dir.mkdir(parents=True, exist_ok=True)

    state = {
        "operation_id": op,
        "status": "REVIEWED",
        "fingerprint": req['fingerprint'],
        "correlation_id": correlation_id,
        "review": {
            "decision": decision,
            "signature": signature
        }
    }
    (dispatch_dir / f"{op}-{manifest_key}.json").write_text(json.dumps(state))

    ps_cmd = f"""
    . '{Path('scripts/controller/Controller-Registration.ps1').resolve()}'
    $task = [pscustomobject]@{{ requested_operation_id = '{op}'; operation_transition = $null }}
    $plan = Get-ControllerRegistrationPlan -Workspace '{root}' -Instruction 'OPERATION_ID: {op}' -Task $task
    $plan | ConvertTo-Json
    """
    res = subprocess.run(
        ['powershell', '-NoProfile', '-Command', ps_cmd],
        capture_output=True, text=True, check=True, stdin=subprocess.DEVNULL
    )
    plan = json.loads(res.stdout)
    # Cryptographically verified: must advance to REGISTERED_TECHNICAL_QUALIFICATION_REQUIRED or READY
    assert plan['status'] in ('REGISTERED_TECHNICAL_QUALIFICATION_REQUIRED', 'READY')
    assert plan['dispatch_ready'] is True


def test_controller_registration_rejected_review_fails_closed(mock_operation):
    root, op, definition, _ = mock_operation
    manifest_key = sha(root / definition['manifest']).lower()
    dispatch_dir = root / 'project_coordination/review_dispatch'
    dispatch_dir.mkdir(parents=True, exist_ok=True)

    state = {
        "operation_id": op,
        "status": "REJECTED",
        "review": {
            "decision": {
                "decision": "REJECT",
                "rationale": "Physics law violated"
            }
        }
    }
    (dispatch_dir / f"{op}-{manifest_key}.json").write_text(json.dumps(state))

    ps_cmd = f"""
    . '{Path('scripts/controller/Controller-Registration.ps1').resolve()}'
    $task = [pscustomobject]@{{ requested_operation_id = '{op}'; operation_transition = $null }}
    $plan = Get-ControllerRegistrationPlan -Workspace '{root}' -Instruction 'OPERATION_ID: {op}' -Task $task
    $plan | ConvertTo-Json
    """
    res = subprocess.run(
        ['powershell', '-NoProfile', '-Command', ps_cmd],
        capture_output=True, text=True, check=True, stdin=subprocess.DEVNULL
    )
    plan = json.loads(res.stdout)
    assert plan['status'] == 'DEFINITION_REJECTED'
    assert plan['dispatch_ready'] is False
    assert plan['task_type'] == 'REJECTED'
    assert 'Physics law violated' in plan['blocked_on'][0]


# ==============================================================================
# Part 3: Dispatcher Synchronization & Event Handling
# ==============================================================================

def test_dispatcher_syncs_controller_event(mock_operation, keys):
    root, op, _, _ = mock_operation
    priv_file, pub_file = keys

    event_dir = root / 'project_coordination/controller'
    event_dir.mkdir(parents=True, exist_ok=True)
    event_file = event_dir / f"definition-review-{op}.json"
    event_file.write_text(json.dumps({
        "schema": 1,
        "status": "DEFINITION_REVIEW_REQUIRED",
        "operation_id": op,
        "event_fingerprint": "FP123"
    }))

    class MockHooks:
        def reconcile(self, key, definition):
            return dict(status='NOT_SUBMITTED')

        def review(self, request, path, resume):
            decision = dict(
                reviewer=REVIEWER, author='gemini-antigravity',
                correlation_id=request['correlation_id'], operation_id=request['operation_id'],
                fingerprint=request['fingerprint'], reviewed_hashes=request['hashes'],
                decision='APPROVE', rationale='Approved in test',
                assistant_message_id='msg-sync', conversation_url='https://chatgpt.com/c/test'
            )
            sig = base64.b64encode(priv_file.read_bytes()[:32]).decode()  # dummy
            # sign properly
            priv = Ed25519PrivateKey.generate()
            signature = base64.b64encode(priv.sign(canonical(decision))).decode()
            self.key = root / 'pub.pem'
            self.key.write_bytes(priv.public_key().public_bytes(Encoding.PEM, PublicFormat.SubjectPublicKeyInfo))
            return dict(decision=decision, signature=signature)

        def verify(self, receipt, request):
            return verify_receipt(receipt, request, self.key)

        def qualify(self, definition, state, path):
            return True

        def submit(self, definition):
            pass

    hooks = MockHooks()
    dispatcher = Dispatcher(root, hooks)
    state = dispatcher.run(op)

    # Event file must be synchronized with state status
    synced_event = json.loads(event_file.read_text())
    assert synced_event['status'] == state['status']
    assert synced_event['status'] in ('REVIEWED', 'TECH_QUALIFIED', 'SUBMITTED', 'BLOCKED')

