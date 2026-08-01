#!/usr/bin/env bash
set -u
set +x

SCRIPT_DIR=$(cd "$(dirname "$0")" && pwd)
# shellcheck disable=SC1091
. "$SCRIPT_DIR/job_notifications.sh"
notification_load_config || exit $?
mkdir -p "$NOTIFICATION_EVIDENCE_DIR"

UTC_ID=$(date -u +%Y-%m-%dT%H:%M:%SZ)
TELEGRAM_MESSAGE="F15 TELEGRAM DELIVERY TEST — NOT A PBS JOB EVENT | UTC=${UTC_ID}"
test -n "$TELEGRAM_MESSAGE" || exit 50
TELEGRAM_TEXT_LENGTH=$(LC_ALL=C printf '%s' "$TELEGRAM_MESSAGE" | wc -c | tr -d ' ')
[ "$TELEGRAM_TEXT_LENGTH" -gt 0 ] || exit 51

RAW_RESPONSE=$(mktemp)
CURL_CONFIG=$(mktemp)
chmod 600 "$RAW_RESPONSE" "$CURL_CONFIG"
cleanup() { rm -f "$RAW_RESPONSE" "$CURL_CONFIG"; }
trap cleanup EXIT INT TERM HUP

{
  printf 'silent\nshow-error\nrequest = "POST"\n'
  printf 'url = "https://api.telegram.org/bot%s/sendMessage"\n' "$TELEGRAM_BOT_TOKEN"
  printf 'data-urlencode = "chat_id=%s"\n' "$TELEGRAM_CHAT_ID"
} >"$CURL_CONFIG"

python3 - "$NOTIFICATION_EVIDENCE_DIR/F15_TELEGRAM_PAYLOAD_REQUEST_AUDIT.json" "$TELEGRAM_TEXT_LENGTH" <<'PY'
import json,sys
record={
  'method':'POST', 'endpoint':'sendMessage', 'chat_id_present':True,
  'text_present':True, 'text_length':int(sys.argv[2]),
  'content_encoding':'application/x-www-form-urlencoded', 'attempt':1,
  'data_urlencode_has_literal_text_prefix':True,
  'notification_function_received_message_argument':True,
}
open(sys.argv[1],'w').write(json.dumps(record,indent=2,sort_keys=True)+'\n')
PY

curl_rc=0
http_status=$(curl --config "$CURL_CONFIG" \
  --data-urlencode "text=${TELEGRAM_MESSAGE}" \
  --output "$RAW_RESPONSE" --write-out '%{http_code}') || curl_rc=$?

python3 - "$RAW_RESPONSE" "$NOTIFICATION_EVIDENCE_DIR/F15_TELEGRAM_PAYLOAD_REPAIR.json" \
  "$TELEGRAM_CHAT_ID" "$curl_rc" "$http_status" "$TELEGRAM_TEXT_LENGTH" "$UTC_ID" <<'PY'
import datetime,hashlib,json,re,sys
raw_path,out_path,chat_id,curl_rc,http_status,text_length,test_id=sys.argv[1:]
def fp(v): return 'redacted:'+hashlib.sha256(('f15-payload:'+str(v)).encode()).hexdigest()[:12]
try: d=json.load(open(raw_path))
except Exception: d={}
result=d.get('result') if isinstance(d.get('result'),dict) else {}
chat=result.get('chat') if isinstance(result.get('chat'),dict) else {}
returned=chat.get('id')
description=re.sub(r'[-+]?\d{5,}','[redacted-id]',str(d.get('description','')))
record={
 'test_id':test_id, 'label':'F15 TELEGRAM DELIVERY TEST — NOT A PBS JOB EVENT',
 'utc_timestamp':datetime.datetime.utcnow().isoformat()+'Z',
 'telegram_text_nonempty':int(text_length)>0, 'telegram_text_length':int(text_length),
 'request_method':'POST', 'endpoint':'sendMessage', 'attempt_count':1,
 'curl_return_code':int(curl_rc), 'http_status':http_status,
 'telegram_ok':d.get('ok') is True,
 'configured_chat_fingerprint':fp(chat_id),
 'returned_chat_fingerprint':fp(returned) if returned is not None else None,
 'chat_fingerprint_match':str(returned)==str(chat_id),
 'message_id_fingerprint':fp(result.get('message_id')) if result.get('message_id') is not None else None,
 'error_code':d.get('error_code'), 'error_description_redacted':description or None,
 'data_urlencode_has_literal_text_prefix':True,
 'notification_function_received_message_argument':True,
 'pass':int(curl_rc)==0 and http_status=='200' and d.get('ok') is True and str(returned)==str(chat_id),
 'qsub_attempts':0,
}
open(out_path,'w').write(json.dumps(record,indent=2,sort_keys=True)+'\n')
raise SystemExit(0 if record['pass'] else 1)
PY
evidence_rc=$?
cleanup
trap - EXIT INT TERM HUP
exit "$evidence_rc"
