"""Read one profile from stdin; never access or modify the global login."""
import base64
import json
import os
import sys
from ai_limit_checker import antigravity
from ai_limit_checker.antigravity import check_antigravity
from ai_limit_checker.credentials import parse_windows_blob


def refresh_with_candidates(grant, client_id, candidates, expected_identity, http_form, http_json):
    """Try only embedded client pairs; a rejected user grant never triggers fallback."""
    for secret in candidates:
        status, data = http_form(antigravity.TOKEN_URL, {
            'client_id': client_id, 'client_secret': secret,
            'refresh_token': grant, 'grant_type': 'refresh_token'})
        if data.get('error') == 'invalid_client':
            continue
        if status != 200 or not data.get('access_token'):
            category = 'AUTHENTICATION_FAILED' if data.get('error') == 'invalid_grant' else 'TOKEN_REFRESH_FAILED'
            raise RuntimeError(category + ' HTTP ' + str(status))
        access = data['access_token']
        verify_provider_identity(access, expected_identity, http_json)
        return access
    raise RuntimeError('OAUTH_CLIENT_REJECTED')


def verify_provider_identity(access, expected, http_json):
    status, identity = http_json('GET', 'https://openidconnect.googleapis.com/v1/userinfo',
                                 headers={'Authorization': 'Bearer '+access})
    if status != 200:
        raise RuntimeError('PROVIDER_IDENTITY_UNAVAILABLE HTTP '+str(status))
    if canonical_identity(identity.get('sub')) != expected:
        raise RuntimeError('PROVIDER_IDENTITY_MISMATCH')


def install_oauth_client_fix(expected_identity=None):
    """Bound GOCSPX secrets before adjacent Go binary text; never persist tokens."""
    import re
    original = antigravity._resolve_oauth_client

    def resolve():
        client_id, secret = original()
        # Installed checker greedily captures 70 characters from this Go binary.
        # Google's GOCSPX credential is prefix + 28 characters (35 total).
        # Preserve explicit configured overrides without modification.
        import os
        if not os.environ.get('AGY_CLIENT_SECRET') and secret.startswith('GOCSPX-'):
            match = re.match(r'GOCSPX-[A-Za-z0-9_-]{28}', secret)
            if match:
                secret = match.group(0)
        return client_id, secret

    antigravity._resolve_oauth_client = resolve
    if expected_identity is None:
        return
    # The binary embeds several OAuth clients. Its first secret does not
    # necessarily belong to the selected client ID. Bound discovery to those
    # explicit embedded secrets; only invalid_client permits another pair.
    original_get = antigravity.get_access_token
    def refresh(grant):
        client_id, first = resolve()
        candidates = [first]
        if not os.environ.get('AGY_CLIENT_SECRET'):
            binary = antigravity._find_agy_binary()
            if binary:
                candidates += [m.decode('ascii') for m in re.findall(
                    rb'GOCSPX-[A-Za-z0-9_-]{28}', binary.read_bytes())]
        candidates = list(dict.fromkeys(candidates))
        if not 1 <= len(candidates) <= 8:
            raise RuntimeError('OAUTH_CLIENT_DISCOVERY_INVALID')
        return refresh_with_candidates(grant, client_id, candidates, expected_identity,
                                       antigravity.utils.http_form, antigravity.utils.http_json)
    def get_verified(creds, now=None):
        access = original_get(creds, now)
        if access:
            try:
                verify_provider_identity(access, expected_identity, antigravity.utils.http_json)
            except RuntimeError as exc:
                if str(exc) != 'PROVIDER_IDENTITY_UNAVAILABLE HTTP 401' or not creds.get('refresh_token'):
                    raise
                access = refresh(creds['refresh_token'])
        return access
    antigravity.refresh_access_token = refresh
    antigravity.get_access_token = get_verified


# Authentic Antigravity CLI User-Agent ensures Google's backend serves complete quota groups.
AUTHENTIC_USER_AGENT = "antigravity/cli/1.4.0 (aidev_client; os_type=windows; arch=amd64)"
antigravity.USER_AGENT = AUTHENTIC_USER_AGENT


def install_quota_repair():
    """Install authentic quota summary and bucket parsers.

    - Fails closed on disabled / nonapplicable buckets.
    - Preserves provider group and bucket structures.
    - Uses only the primary CLI-compatible grouped quota endpoint.
    """
    original_parse_bucket = antigravity._parse_bucket
    def parse_bucket(bucket):
        if not isinstance(bucket, dict):
            return None
        if bucket.get('disabled') is True:
            return {'label': bucket.get('displayName', 'Limit'), 'window': bucket.get('window'),
                    'used_pct': None, 'remaining_pct': None, 'remaining_fraction': None,
                    'resets_at': None, 'note': bucket.get('description'), 'status': 'NONAPPLICABLE'}
        result = original_parse_bucket(bucket)
        if result is not None:
            fraction = result['remaining_fraction']
            if not 0 <= fraction <= 1:
                raise ValueError('Invalid quota fraction')
            result['remaining_pct'] = round(fraction * 100, 2)
            result['used_pct'] = round((1 - fraction) * 100, 2)
        return result
    antigravity._parse_bucket = parse_bucket
    # Only the primary CLI-compatible grouped endpoint is authoritative.
    # Missing groups stay unavailable; never mix another quota context.


def inspect(envelope):
    blob = base64.b64decode(envelope['blobB64'], validate=True)
    data = json.loads(blob.decode('utf-8-sig'))
    if not isinstance(data, dict):
        raise ValueError('invalid credential shape')
    token = data.get('token', data)
    if not isinstance(token, dict) or not token.get('refresh_token'):
        raise ValueError('missing refresh grant')
    # Local identity is a consistency marker, not proof of authentication.
    def claims(jwt):
        if not isinstance(jwt, str) or len(jwt.split('.')) != 3:
            raise ValueError('invalid identity metadata')
        encoded = jwt.split('.')[1]
        return json.loads(base64.b64decode(encoded + '=' * (-len(encoded) % 4),
                                          altchars=b'-_', validate=True).decode('utf-8'))
    nested_id, root_id = token.get('id_token'), data.get('id_token')
    selected_id = nested_id or root_id
    if not selected_id:
        raise ValueError('missing identity metadata')
    identity = claims(selected_id)
    subject = identity.get('sub')
    canonical = canonical_identity(subject)
    if nested_id and root_id and canonical_identity(claims(root_id).get('sub')) != canonical:
        raise ValueError('conflicting identity metadata')
    # The checker expects a wrapped Windows blob. Normalize only in memory;
    # support legacy root metadata and the current nested save layout alike.
    normalized = dict(token)
    normalized['id_token'] = selected_id
    wrapped = dict(data) if 'token' in data else {}
    wrapped.update(token=normalized, id_token=selected_id,
                   auth_method=data.get('auth_method', 'consumer'))
    return (json.dumps(wrapped, ensure_ascii=False).encode('utf-8'),
            canonical, identity.get('email', ''))


def canonical_identity(subject):
    # Same contract as Get-AgyCanonicalIdentity: exact UTF-8 subject, case
    # sensitive, no whitespace trimming/case folding, first 16 lowercase hex.
    if not isinstance(subject, str) or not subject.strip():
        raise ValueError('missing subject')
    import hashlib
    return hashlib.sha256(subject.encode('utf-8')).hexdigest()[:16]


def main():
    try:
        install_quota_repair()
        # Decode stdin using utf-8-sig to safely strip any PowerShell BOM
        raw_stdin = sys.stdin.buffer.read()
        request = json.loads(raw_stdin.decode('utf-8-sig'))
        blob, identity, email = inspect(request['credential'])
        result = {'identity': identity, 'email': email}
        if not request.get('audit_only'):
            install_oauth_client_fix(expected_identity=identity)
            result['antigravity'] = check_antigravity(parse_windows_blob(blob))
            if result['antigravity'].get('status') != 'ok':
                import re
                message = result['antigravity'].get('error') or ''
                categories = ('OAUTH_CLIENT_REJECTED', 'OAUTH_CLIENT_DISCOVERY_INVALID',
                              'AUTHENTICATION_FAILED', 'TOKEN_REFRESH_FAILED',
                              'PROVIDER_IDENTITY_MISMATCH', 'PROVIDER_IDENTITY_UNAVAILABLE')
                code = next((c for c in categories if c in message), 'QUOTA_API_FAILED')
                result['antigravity']['error_code'] = code
                result['antigravity']['error'] = code
        print(json.dumps(result))
    except Exception:
        # Never echo exception payloads: they can contain credential data.
        print(json.dumps({'error': 'Profile could not be inspected safely'}))
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
