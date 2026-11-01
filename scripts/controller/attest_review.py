"""Trusted ChatGPT Review Attestation Worker.

Extracts independent review decisions, verifies binding to the immutable request packet,
and generates cryptographic Ed25519 receipts when the external bridge signing key is configured.
The signing private key must reside outside the repository in the user's protected profile.
"""
import argparse
import base64
import json
import os
from pathlib import Path
import re
import sys
import uuid

REVIEWER = 'ChatGPT-independent-review'
DEFAULT_KEY_PATH = Path.home() / '.config' / 'adaptive-remeshing' / 'review_bridge_ed25519.key'


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode('utf-8')


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def atomic_write_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + '.' + uuid.uuid4().hex + '.tmp')
    with tmp.open('w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def extract_decision(raw_text):
    """Extract JSON decision from raw markdown, code block, or json text."""
    if not raw_text or not raw_text.strip():
        raise ValueError('EMPTY_REVIEW_REPLY')
    text = raw_text.strip()

    # If wrapped in code block
    match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', text)
    candidate_texts = [match.group(1).strip()] if match else []
    candidate_texts.append(text)

    # Search for { ... } object
    for candidate in candidate_texts:
        try:
            parsed = json.loads(candidate)
            if isinstance(parsed, dict):
                # If wrapped in { "decision": ..., "signature": ... }
                if 'decision' in parsed and isinstance(parsed['decision'], dict):
                    return parsed['decision'], parsed.get('signature')
                return parsed, None
        except json.JSONDecodeError:
            pass

    # Fallback regex search for JSON object with reviewer field
    json_match = re.search(r'(\{[\s\S]*"reviewer"[\s\S]*\})', text)
    if json_match:
        try:
            parsed = json.loads(json_match.group(1))
            if isinstance(parsed, dict):
                if 'decision' in parsed and isinstance(parsed['decision'], dict):
                    return parsed['decision'], parsed.get('signature')
                return parsed, None
        except json.JSONDecodeError:
            pass

    raise ValueError('UNPARSEABLE_DECISION_JSON')


def validate_decision(decision, request):
    """Verify all fields match the immutable request packet."""
    expected_author = request.get('definition', {}).get('author')
    valid_authors = [expected_author] if expected_author else ['', 'gemini-antigravity']

    errors = []
    if decision.get('reviewer') != REVIEWER:
        errors.append(f"Invalid reviewer: expected '{REVIEWER}', got '{decision.get('reviewer')}'")
    if decision.get('author') not in valid_authors:
        errors.append(f"Invalid author: expected one of {valid_authors}, got '{decision.get('author')}'")
    if decision.get('author') == decision.get('reviewer'):
        errors.append("Author cannot be reviewer; self-approval strictly prohibited")
    if decision.get('correlation_id') != request.get('correlation_id'):
        errors.append(f"Correlation ID mismatch: expected '{request.get('correlation_id')}', got '{decision.get('correlation_id')}'")
    if decision.get('operation_id') != request.get('operation_id'):
        errors.append(f"Operation ID mismatch: expected '{request.get('operation_id')}', got '{decision.get('operation_id')}'")
    if decision.get('fingerprint') != request.get('fingerprint'):
        errors.append(f"Fingerprint mismatch: expected '{request.get('fingerprint')}', got '{decision.get('fingerprint')}'")
    if decision.get('reviewed_hashes') != request.get('hashes'):
        errors.append("Reviewed hashes do not match request hashes")
    if decision.get('decision') not in request.get('required_decisions', ['APPROVE', 'REJECT', 'INSUFFICIENT_EVIDENCE']):
        errors.append(f"Invalid decision value: '{decision.get('decision')}'")
    if not decision.get('rationale'):
        errors.append("Missing rationale")
    if not decision.get('assistant_message_id'):
        errors.append("Missing assistant_message_id")
    conv_url = decision.get('conversation_url', '')
    if not re.fullmatch(r'https://chatgpt\.com/c/[A-Za-z0-9-]+', conv_url):
        errors.append(f"Invalid conversation_url: '{conv_url}'")

    if errors:
        raise ValueError('VALIDATION_FAILED: ' + '; '.join(errors))


def sign_decision(decision, key_path):
    """Sign the canonical JSON of decision using Ed25519 private key."""
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    from cryptography.hazmat.primitives.serialization import load_pem_private_key

    key_bytes = Path(key_path).read_bytes()
    key = load_pem_private_key(key_bytes, password=None)
    if not isinstance(key, Ed25519PrivateKey):
        raise ValueError('NOT_AN_ED25519_PRIVATE_KEY')

    sig = key.sign(canonical(decision))
    return base64.b64encode(sig).decode('ascii')


def attest(request_path, response_path, raw_reply, key_path=None, bridge_archive=None):
    request = read_json(request_path)
    if bridge_archive:
        arch_data = read_json(bridge_archive)
        if arch_data.get('bridge_handoff_id') != request.get('correlation_id'):
            raise ValueError(f"BRIDGE_HANDOFF_ID_MISMATCH: expected {request.get('correlation_id')}, got {arch_data.get('bridge_handoff_id')}")
        if arch_data.get('status') != 'OK':
            raise ValueError(f"BRIDGE_STATUS_NOT_OK: {arch_data.get('status')}")
        if not arch_data.get('response'):
            raise ValueError("EMPTY_BRIDGE_RESPONSE_IN_ARCHIVE")
        raw_reply = arch_data['response']

    decision, existing_sig = extract_decision(raw_reply)
    validate_decision(decision, request)

    if existing_sig:
        receipt = dict(decision=decision, signature=existing_sig)
    else:
        key_file = Path(key_path) if key_path else DEFAULT_KEY_PATH
        if not key_file.is_file():
            # Save raw decision for audit/recovery
            raw_path = Path(response_path).with_suffix('.unauthenticated.json')
            atomic_write_json(raw_path, dict(decision=decision))
            raise ValueError(
                f"REVIEW_BRIDGE_KEY_NOT_CONFIGURED: Missing Ed25519 private key at {key_file}. "
                "Configure key outside repo using Initialize-ReviewBridgeKeys.ps1."
            )
        signature = sign_decision(decision, key_file)
        receipt = dict(decision=decision, signature=signature)

    atomic_write_json(response_path, receipt)
    return receipt


def main():
    parser = argparse.ArgumentParser(description='Attest and sign ChatGPT review decision')
    parser.add_argument('--request-path', required=True, help='Path to request JSON')
    parser.add_argument('--response-path', required=True, help='Path to output receipt JSON')
    parser.add_argument('--bridge-archive', help='Path to authentic bridge archive JSON (response_*_<correlation_id>.json)')
    parser.add_argument('--reply-text', help='Raw reply text from ChatGPT')
    parser.add_argument('--reply-file', help='Path to raw reply file')
    parser.add_argument('--key-path', default=str(DEFAULT_KEY_PATH), help='Path to Ed25519 private key')
    args = parser.parse_args()

    raw_text = ''
    if args.bridge_archive:
        pass  # Handled inside attest() via bridge_archive parameter
    elif args.reply_file:
        raw_text = Path(args.reply_file).read_text(encoding='utf-8')
    elif args.reply_text:
        raw_text = args.reply_text
    else:
        raw_text = sys.stdin.read()

    try:
        attest(args.request_path, args.response_path, raw_text, args.key_path, bridge_archive=args.bridge_archive)
        print('ATTESTED_RECEIPT_PRODUCED')
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()

