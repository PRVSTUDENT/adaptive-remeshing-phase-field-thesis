#!/usr/bin/env bash
set -u
set +x

SCRIPT_DIR=$(cd "$(dirname "$0")" && pwd)
# shellcheck disable=SC1091
. "$SCRIPT_DIR/job_notifications.sh"
notification_load_config || exit $?
mkdir -p "$NOTIFICATION_EVIDENCE_DIR"

CURL_VERSION=$(curl --version | head -n1 | sed -E 's/(curl [0-9.]+).*/\1/')
for option in --silent --show-error --output --write-out --config; do
  curl --help all 2>/dev/null | grep -q -- "$option" || exit 40
done

RAW_RESPONSE=$(mktemp)
CURL_CONFIG=$(mktemp)
chmod 600 "$RAW_RESPONSE" "$CURL_CONFIG"
cleanup() { rm -f "$RAW_RESPONSE" "$CURL_CONFIG"; }
trap cleanup EXIT INT TERM HUP

telegram_call() {
  local method="$1" text="${2:-}" status rc=0
  : >"$RAW_RESPONSE"
  {
    printf 'silent\nshow-error\nrequest = "POST"\n'
    printf 'url = "https://api.telegram.org/bot%s/%s"\n' "$TELEGRAM_BOT_TOKEN" "$method"
    printf 'output = "%s"\nwrite-out = "%%{http_code}"\n' "$RAW_RESPONSE"
    [ "$method" = getMe ] || printf 'data-urlencode = "chat_id=%s"\n' "$TELEGRAM_CHAT_ID"
    [ "$method" = sendMessage ] && printf 'data-urlencode = "text=%s"\n' "$text"
  } >"$CURL_CONFIG"
  status=$(curl --config "$CURL_CONFIG") || rc=$?
  TELEGRAM_CALL_RC="$rc" TELEGRAM_CALL_STATUS="$status"; export TELEGRAM_CALL_RC TELEGRAM_CALL_STATUS
  return "$rc"
}

validate_response() {
  local kind="$1"
  python3 - "$RAW_RESPONSE" "$kind" "$TELEGRAM_CHAT_ID" <<'PY'
import json, sys
try:
    d=json.load(open(sys.argv[1]))
except Exception:
    raise SystemExit(2)
if d.get('ok') is not True:
    raise SystemExit(3)
if sys.argv[2] in ('getChat','sendMessage'):
    result=d.get('result') or {}
    chat=result if sys.argv[2]=='getChat' else (result.get('chat') or {})
    if str(chat.get('id')) != str(sys.argv[3]):
        raise SystemExit(4)
PY
}

telegram_call getMe || exit 41
[ "$TELEGRAM_CALL_STATUS" = 200 ] && validate_response getMe || exit 42
telegram_call getChat || exit 43
[ "$TELEGRAM_CALL_STATUS" = 200 ] && validate_response getChat || exit 44

TEST_ID="F15TG_$(date -u +%Y%m%dT%H%M%SZ)"
MESSAGE="F15 TELEGRAM DELIVERY TEST — NOT A PBS JOB EVENT — ${TEST_ID}"
attempt=1; send_rc=1
while [ "$attempt" -le 3 ]; do
  if telegram_call sendMessage && [ "$TELEGRAM_CALL_STATUS" = 200 ] && validate_response sendMessage; then send_rc=0; break; fi
  send_rc=$?
  [ "$attempt" -eq 3 ] || sleep 5
  attempt=$((attempt + 1))
done
[ "$attempt" -le 3 ] || attempt=3

python3 - "$RAW_RESPONSE" "$NOTIFICATION_EVIDENCE_DIR/F15_TELEGRAM_COMPATIBILITY_REPAIR.json" \
  "$TELEGRAM_CHAT_ID" "$CURL_VERSION" "$TELEGRAM_CALL_RC" "$TELEGRAM_CALL_STATUS" "$attempt" "$TEST_ID" "$send_rc" <<'PY'
import datetime, hashlib, json, re, sys
raw_path,out_path,chat_id,version,curl_rc,http_status,attempt,test_id,send_rc=sys.argv[1:]
def fp(v): return 'redacted:'+hashlib.sha256(('f15-telegram:'+str(v)).encode()).hexdigest()[:12]
try: d=json.load(open(raw_path))
except Exception: d={}
result=d.get('result') if isinstance(d.get('result'),dict) else {}
returned=(result.get('chat') or {}).get('id') if isinstance(result.get('chat'),dict) else None
description=str(d.get('description',''))
description=re.sub(r'[-+]?\d{5,}', '[redacted-id]', description)
record={
 'test_id':test_id, 'label':'F15 TELEGRAM DELIVERY TEST — NOT A PBS JOB EVENT',
 'utc_timestamp':datetime.datetime.utcnow().isoformat()+'Z', 'curl_version':version,
 'portable_options_verified':True, 'getMe_preflight_pass':True, 'getChat_preflight_pass':True,
 'attempt_count':int(attempt), 'curl_return_code':int(curl_rc), 'http_status':http_status,
 'telegram_ok':d.get('ok') is True, 'configured_chat_fingerprint':fp(chat_id),
 'returned_chat_fingerprint':fp(returned) if returned is not None else None,
 'chat_fingerprint_match':str(returned)==str(chat_id),
 'message_id_fingerprint':fp(result.get('message_id')) if result.get('message_id') is not None else None,
 'error_code':d.get('error_code'), 'error_description_redacted':description or None,
 'pass':int(send_rc)==0 and int(curl_rc)==0 and http_status=='200' and d.get('ok') is True and str(returned)==str(chat_id),
 'qsub_attempts':0,
}
open(out_path,'w').write(json.dumps(record,indent=2,sort_keys=True)+'\n')
raise SystemExit(0 if record['pass'] else 1)
PY
evidence_rc=$?
cleanup
trap - EXIT INT TERM HUP
exit "$evidence_rc"
